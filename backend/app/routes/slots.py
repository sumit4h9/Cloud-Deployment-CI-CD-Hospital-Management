from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Slot, Doctor, AuditEvent
from ..schemas import SlotCreate, SlotOut
from ..auth import CurrentUser, get_current_user
import json

router = APIRouter(prefix="/api/v1/slots", tags=["Slots & Availability"])

@router.post("", response_model=SlotOut, status_code=status.HTTP_201_CREATED)
def create_slot(
    payload: SlotCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    existing = db.query(Slot).filter(
        Slot.doctor_id == payload.doctor_id,
        Slot.date == payload.date,
        Slot.start_time == payload.start_time
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Slot already exists for this time")

    slot = Slot(
        doctor_id=payload.doctor_id,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        is_available=True
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)

    audit = AuditEvent(
        event_type="SLOT_CREATED",
        actor_role=current_user.role,
        actor_id=current_user.id,
        details=json.dumps({"slot_id": slot.id, "doctor_id": slot.doctor_id, "time": f"{slot.date} {slot.start_time}"})
    )
    db.add(audit)
    db.commit()

    return SlotOut(
        id=slot.id,
        doctor_id=slot.doctor_id,
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        is_available=slot.is_available,
        status="Available"
    )

@router.patch("/{slot_id}/disable", response_model=SlotOut)
def disable_slot(
    slot_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    slot.is_available = False
    db.commit()
    db.refresh(slot)

    audit = AuditEvent(
        event_type="SLOT_DISABLED",
        actor_role=current_user.role,
        actor_id=current_user.id,
        details=json.dumps({"slot_id": slot.id, "time": f"{slot.date} {slot.start_time}"})
    )
    db.add(audit)
    db.commit()

    return SlotOut(
        id=slot.id,
        doctor_id=slot.doctor_id,
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        is_available=slot.is_available,
        status="Booked"
    )

@router.patch("/{slot_id}/enable", response_model=SlotOut)
def enable_slot(
    slot_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    slot = db.query(Slot).filter(Slot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    slot.is_available = True
    db.commit()
    db.refresh(slot)

    return SlotOut(
        id=slot.id,
        doctor_id=slot.doctor_id,
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        is_available=slot.is_available,
        status="Available"
    )

