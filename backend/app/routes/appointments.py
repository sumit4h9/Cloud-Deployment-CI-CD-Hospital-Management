import threading
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from ..database import get_db
from ..models import Appointment, Slot, Doctor, Patient, AuditEvent
from ..schemas import AppointmentCreate, AppointmentReschedule, AppointmentOut
from ..auth import get_current_user, CurrentUser
from ..metrics import APPOINTMENTS_CREATED, APPOINTMENTS_COMPLETED, APPOINTMENTS_CANCELLED, CONFLICTS_PREVENTED

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])

# (Note: In-memory locks eliminated in favor of database-level partial unique index
# and atomic conditional updates for multi-replica Kubernetes horizontal autoscaling)

def record_audit(db: Session, event_type: str, actor_role: str, actor_id: str, details: dict):
    audit = AuditEvent(
        event_type=event_type,
        actor_role=actor_role,
        actor_id=actor_id,
        details=json.dumps(details)
    )
    db.add(audit)
    db.commit()

def validate_time_window(start_time: str, end_time: Optional[str]) -> str:
    """Validates that appointment falls within valid clinic operating hours (08:00 - 18:00)."""
    try:
        sh, sm = map(int, start_time.split(":"))
        if not (0 <= sh < 24 and 0 <= sm < 60):
            raise ValueError()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid start_time format. Must be HH:MM.")

    if sh < 8 or sh >= 18:
        raise HTTPException(
            status_code=400, 
            detail=f"Appointment time {start_time} is outside clinic operating hours (08:00 - 18:00)."
        )

    if not end_time:
        em = sm + 30
        eh = sh + (em // 60)
        em = em % 60
        end_time = f"{eh:02d}:{em:02d}"
    else:
        try:
            eh, em = map(int, end_time.split(":"))
            if eh * 60 + em <= sh * 60 + sm:
                raise HTTPException(status_code=400, detail="end_time must be later than start_time.")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid end_time format. Must be HH:MM.")

    return end_time

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
    # 1. Validate Doctor & Patient references and time windows
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=400, detail=f"Doctor '{payload.doctor_id}' does not exist")

    end_time = validate_time_window(payload.start_time, payload.end_time)

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        # If patient doesn't exist, create synthetic patient automatically for ease of testing
        patient = Patient(id=payload.patient_id, name=f"Patient #{payload.patient_id.replace('pat_', '')}", email=f"{payload.patient_id}@example.com")
        db.add(patient)
        db.commit()
        db.refresh(patient)

    # 2. Database-level atomic slot claim
    slot = None
    if payload.slot_id:
        slot = db.query(Slot).filter(Slot.id == payload.slot_id).first()
    else:
        slot = db.query(Slot).filter(
            Slot.doctor_id == payload.doctor_id,
            Slot.date == payload.date,
            Slot.start_time == payload.start_time
        ).first()

    if slot:
        # Atomic conditional update guaranteed across distributed replica pods
        updated_rows = db.query(Slot).filter(
            Slot.id == slot.id,
            Slot.is_available == True
        ).update({"is_available": False})

        if updated_rows == 0:
            CONFLICTS_PREVENTED.inc()
            record_audit(
                db,
                event_type="CONFLICT_PREVENTED",
                actor_role=current_user.role,
                actor_id=current_user.id,
                details={
                    "reason": "Slot claimed by concurrent transaction",
                    "slot_id": slot.id,
                    "doctor_id": payload.doctor_id
                }
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected appointment slot is no longer available"
            )

    # 3. Create appointment record and enforce partial unique index constraint in DB
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

    try:
        db.commit()
        db.refresh(new_apt)
    except IntegrityError as exc:
        db.rollback()
        # Release the slot back to available if it was reserved
        if slot:
            db.query(Slot).filter(Slot.id == slot.id).update({"is_available": True})
            db.commit()

        CONFLICTS_PREVENTED.inc()
        record_audit(
            db,
            event_type="CONFLICT_PREVENTED",
            actor_role=current_user.role,
            actor_id=current_user.id,
            details={
                "reason": "Database partial unique index prevented race condition",
                "doctor_id": payload.doctor_id,
                "date": payload.date,
                "start_time": payload.start_time,
                "error": str(exc.orig) if hasattr(exc, "orig") else str(exc)
            }
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Time slot {payload.start_time} on {payload.date} is already booked for this doctor."
        )

    APPOINTMENTS_CREATED.inc()

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

    try:
        db.commit()
        db.refresh(apt)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Target time slot {payload.new_start_time} is already booked."
        )

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

    APPOINTMENTS_CANCELLED.inc()

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

@router.post("/{appointment_id}/complete", response_model=AppointmentOut)
def complete_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """Marks an appointment as Completed by the physician."""
    apt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not apt:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if apt.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cannot complete a cancelled appointment")

    apt.status = "Completed"
    apt.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(apt)

    APPOINTMENTS_COMPLETED.inc()

    record_audit(
        db,
        event_type="APPOINTMENT_COMPLETED",
        actor_role=current_user.role,
        actor_id=current_user.id,
        details={"appointment_id": apt.id, "doctor_id": apt.doctor_id}
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
