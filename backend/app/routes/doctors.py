from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Doctor, Slot
from ..schemas import DoctorOut, SlotOut

router = APIRouter(prefix="/api/v1/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorOut])
def list_doctors(
    specialization: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Doctor)
    if specialization:
        query = query.filter(Doctor.specialization.ilike(f"%{specialization}%"))
    doctors = query.all()

    result = []
    for doc in doctors:
        # Find next available slot
        next_slot = db.query(Slot).filter(
            Slot.doctor_id == doc.id,
            Slot.is_available == True
        ).order_by(Slot.date.asc(), Slot.start_time.asc()).first()

        doc_out = DoctorOut(
            id=doc.id,
            name=doc.name,
            specialization=doc.specialization,
            email=doc.email,
            room=doc.room,
            next_available_slot=f"{next_slot.start_time} ({next_slot.date})" if next_slot else "No slots available"
        )
        result.append(doc_out)
    return result

@router.get("/{doctor_id}", response_model=DoctorOut)
def get_doctor(doctor_id: str, db: Session = Depends(get_db)):
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")
    next_slot = db.query(Slot).filter(
        Slot.doctor_id == doc.id,
        Slot.is_available == True
    ).order_by(Slot.date.asc(), Slot.start_time.asc()).first()

    return DoctorOut(
        id=doc.id,
        name=doc.name,
        specialization=doc.specialization,
        email=doc.email,
        room=doc.room,
        next_available_slot=f"{next_slot.start_time} ({next_slot.date})" if next_slot else None
    )

@router.get("/{doctor_id}/slots", response_model=List[SlotOut])
def get_doctor_slots(
    doctor_id: str,
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    doc = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Doctor not found")

    query = db.query(Slot).filter(Slot.doctor_id == doctor_id)
    if date:
        query = query.filter(Slot.date == date)
    slots = query.order_by(Slot.start_time.asc()).all()

    result = []
    for slot in slots:
        result.append(SlotOut(
            id=slot.id,
            doctor_id=slot.doctor_id,
            date=slot.date,
            start_time=slot.start_time,
            end_time=slot.end_time,
            is_available=slot.is_available,
            status="Available" if slot.is_available else "Booked"
        ))
    return result
