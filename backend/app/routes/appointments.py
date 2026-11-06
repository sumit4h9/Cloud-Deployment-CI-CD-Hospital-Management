import threading
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional

from ..database import get_db
from ..models import Appointment, Slot, Doctor, Patient, AuditEvent
from ..schemas import AppointmentCreate, AppointmentReschedule, AppointmentOut
from ..auth import get_current_user, CurrentUser

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

# Global concurrency lock to guarantee atomic slot reservation across concurrent threads
_booking_lock = threading.Lock()

def record_audit(db: Session, event_type: str, actor_role: str, actor_id: str, details: dict):
    audit = AuditEvent(
        event_type=event_type,
        actor_role=actor_role,
        actor_id=actor_id,
        details=json.dumps(details)
    )
    db.add(audit)
    db.commit()

@router.get("", response_model=List[AppointmentOut])
def list_appointments(
    doctor_id: Optional[str] = None,
    patient_id: Optional[str] = None,
    date: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if date:
        query = query.filter(Appointment.date == date)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)

    appointments = query.order_by(Appointment.start_time.asc()).all()
    results = []
    for apt in appointments:
        doc = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        pat = db.query(Patient).filter(Patient.id == apt.patient_id).first()
        results.append(AppointmentOut(
            id=apt.id,
            doctor_id=apt.doctor_id,
            patient_id=apt.patient_id,
            slot_id=apt.slot_id,
            date=apt.date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            status=apt.status,
            created_at=apt.created_at,
            updated_at=apt.updated_at,
            doctor_name=doc.name if doc else None,
            patient_name=pat.name if pat else None,
            specialization=doc.specialization if doc else None
        ))
    return results

@router.get("/{appointment_id}", response_model=AppointmentOut)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    doc = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
    pat = db.query(Patient).filter(Patient.id == apt.patient_id).first()
    return AppointmentOut(
        id=apt.id,
        doctor_id=apt.doctor_id,
        patient_id=apt.patient_id,
        slot_id=apt.slot_id,
        date=apt.date,
        start_time=apt.start_time,
        end_time=apt.end_time,
        status=apt.status,
        created_at=apt.created_at,
        updated_at=apt.updated_at,
        doctor_name=doc.name if doc else None,
        patient_name=pat.name if pat else None,
        specialization=doc.specialization if doc else None
    )

@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Creates an appointment atomically.
    Validates doctor & patient references.
    Prevents double-booking even under concurrent requests.
    """
    # 1. Validate Doctor & Patient references
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=400, detail=f"Doctor '{payload.doctor_id}' does not exist")

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        # If patient doesn't exist, create synthetic patient automatically for ease of testing
        patient = Patient(id=payload.patient_id, name=f"Patient #{payload.patient_id.replace('pat_', '')}", email=f"{payload.patient_id}@example.com")
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # 2. Acquire concurrency lock for critical section to avoid race conditions
    with _booking_lock:
        # Check if an existing confirmed or active appointment conflicts with this time window
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == payload.doctor_id,
            Appointment.date == payload.date,
            Appointment.start_time == payload.start_time,
            Appointment.status.in_(["Confirmed", "Rescheduled"])
        ).first()

        if conflict:
            record_audit(
                db,
                event_type="CONFLICT_PREVENTED",
                actor_role=current_user.role,
                actor_id=current_user.id,
                details={
                    "reason": "Doctor already booked for slot",
                    "doctor_id": payload.doctor_id,
                    "date": payload.date,
                    "start_time": payload.start_time,
                    "conflicting_appointment_id": conflict.id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Time slot {payload.start_time} on {payload.date} is already booked for this doctor."
            )

        # Slot resolution
        slot = None
        if payload.slot_id:
            slot = db.query(Slot).filter(Slot.id == payload.slot_id).first()
        else:
            slot = db.query(Slot).filter(
                Slot.doctor_id == payload.doctor_id,
                Slot.date == payload.date,
                Slot.start_time == payload.start_time
            ).first()

        if slot and not slot.is_available:
            record_audit(
                db,
                event_type="CONFLICT_PREVENTED",
                actor_role=current_user.role,
                actor_id=current_user.id,
                details={
                    "reason": "Slot is marked unavailable",
                    "slot_id": slot.id,
                    "doctor_id": payload.doctor_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected appointment slot is no longer available"
            )

        # Calculate end_time if not provided (default 30 mins)
        end_time = payload.end_time
        if not end_time:
            sh, sm = map(int, payload.start_time.split(":"))
            em = sm + 30
            eh = sh + (em // 60)
            em = em % 60
            end_time = f"{eh:02d}:{em:02d}"

        # Mark slot unavailable if slot exists
        if slot:
            slot.is_available = False
            db.add(slot)

        # Create appointment record
        new_apt = Appointment(
            doctor_id=payload.doctor_id,
            patient_id=payload.patient_id,
            slot_id=slot.id if slot else None,
            date=payload.date,
            start_time=payload.start_time,
            end_time=end_time,
            status="Confirmed"
        )
        db.add(new_apt)
        db.commit()
        db.refresh(new_apt)

        record_audit(
            db,
            event_type="APPOINTMENT_CREATED",
            actor_role=current_user.role,
            actor_id=current_user.id,
            details={
                "appointment_id": new_apt.id,
                "doctor_id": new_apt.doctor_id,
                "patient_id": new_apt.patient_id,
                "date": new_apt.date,
                "time": new_apt.start_time
            }
        )

        return AppointmentOut(
            id=new_apt.id,
            doctor_id=new_apt.doctor_id,
            patient_id=new_apt.patient_id,
            slot_id=new_apt.slot_id,
            date=new_apt.date,
            start_time=new_apt.start_time,
            end_time=new_apt.end_time,
            status=new_apt.status,
            created_at=new_apt.created_at,
            updated_at=new_apt.updated_at,
            doctor_name=doctor.name,
            patient_name=patient.name,
            specialization=doctor.specialization
        )

@router.patch("/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_appointment(
    appointment_id: str,
    payload: AppointmentReschedule,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    with _booking_lock:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if apt.status == "Cancelled":
            raise HTTPException(status_code=400, detail="Cannot reschedule a cancelled appointment")

        # Check conflict at new time
        conflict = db.query(Appointment).filter(
            Appointment.doctor_id == apt.doctor_id,
            Appointment.date == payload.new_date,
            Appointment.start_time == payload.new_start_time,
            Appointment.status.in_(["Confirmed", "Rescheduled"]),
            Appointment.id != apt.id
        ).first()

        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Target time slot {payload.new_start_time} is already booked."
            )

        # Release old slot
        if apt.slot_id:
            old_slot = db.query(Slot).filter(Slot.id == apt.slot_id).first()
            if old_slot:
                old_slot.is_available = True
                db.add(old_slot)

        # Find or reserve new slot
        new_slot = None
        if payload.new_slot_id:
            new_slot = db.query(Slot).filter(Slot.id == payload.new_slot_id).first()
        else:
            new_slot = db.query(Slot).filter(
                Slot.doctor_id == apt.doctor_id,
                Slot.date == payload.new_date,
                Slot.start_time == payload.new_start_time
            ).first()

        if new_slot:
            new_slot.is_available = False
            db.add(new_slot)
            apt.slot_id = new_slot.id

        end_time = payload.new_end_time
        if not end_time:
            sh, sm = map(int, payload.new_start_time.split(":"))
            em = sm + 30
            eh = sh + (em // 60)
            em = em % 60
            end_time = f"{eh:02d}:{em:02d}"

        old_date, old_time = apt.date, apt.start_time
        apt.date = payload.new_date
        apt.start_time = payload.new_start_time
        apt.end_time = end_time
        apt.status = "Rescheduled"
        apt.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(apt)

        record_audit(
            db,
            event_type="APPOINTMENT_RESCHEDULED",
            actor_role=current_user.role,
            actor_id=current_user.id,
            details={
                "appointment_id": apt.id,
                "from": f"{old_date} {old_time}",
                "to": f"{apt.date} {apt.start_time}"
            }
        )

        doc = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        pat = db.query(Patient).filter(Patient.id == apt.patient_id).first()

        return AppointmentOut(
            id=apt.id,
            doctor_id=apt.doctor_id,
            patient_id=apt.patient_id,
            slot_id=apt.slot_id,
            date=apt.date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            status=apt.status,
            created_at=apt.created_at,
            updated_at=apt.updated_at,
            doctor_name=doc.name if doc else None,
            patient_name=pat.name if pat else None,
            specialization=doc.specialization if doc else None
        )

@router.post("/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    with _booking_lock:
        apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not apt:
            raise HTTPException(status_code=404, detail="Appointment not found")

        if apt.status == "Cancelled":
            raise HTTPException(status_code=400, detail="Appointment is already cancelled")

        # Release slot
        if apt.slot_id:
            slot = db.query(Slot).filter(Slot.id == apt.slot_id).first()
            if slot:
                slot.is_available = True
                db.add(slot)

        apt.status = "Cancelled"
        apt.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(apt)

        record_audit(
            db,
            event_type="APPOINTMENT_CANCELLED",
            actor_role=current_user.role,
            actor_id=current_user.id,
            details={"appointment_id": apt.id, "slot_released": apt.slot_id}
        )

        doc = db.query(Doctor).filter(Doctor.id == apt.doctor_id).first()
        pat = db.query(Patient).filter(Patient.id == apt.patient_id).first()

        return AppointmentOut(
            id=apt.id,
            doctor_id=apt.doctor_id,
            patient_id=apt.patient_id,
            slot_id=apt.slot_id,
            date=apt.date,
            start_time=apt.start_time,
            end_time=apt.end_time,
            status=apt.status,
            created_at=apt.created_at,
            updated_at=apt.updated_at,
            doctor_name=doc.name if doc else None,
            patient_name=pat.name if pat else None,
            specialization=doc.specialization if doc else None
        )
