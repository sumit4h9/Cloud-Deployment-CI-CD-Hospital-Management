from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..models import Doctor, Patient, AuditEvent
import json

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Portals"])

class LoginRequest(BaseModel):
    portal: str  # "doctor" or "patient"
    identifier: str
    password: Optional[str] = None

class UserInfo(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    role: str
    specialization: Optional[str] = None

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user: UserInfo

@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    portal = payload.portal.lower().strip()
    identifier = payload.identifier.strip()

    if portal == "doctor":
        # Search by email or ID or name
        doctor = db.query(Doctor).filter(
            (Doctor.email.ilike(f"%{identifier}%")) |
            (Doctor.id == identifier) |
            (Doctor.name.ilike(f"%{identifier}%"))
        ).first()

        if not doctor:
            # Fallback to primary doctor if demo input is entered
            doctor = db.query(Doctor).filter(Doctor.id == "doc_1").first()

        if not doctor:
            raise HTTPException(status_code=401, detail="Doctor account not found")

        audit = AuditEvent(
            event_type="PORTAL_LOGIN",
            actor_role="doctor",
            actor_id=doctor.id,
            details=json.dumps({"portal": "doctor_portal", "doctor_name": doctor.name})
        )
        db.add(audit)
        db.commit()

        return LoginResponse(
            access_token=f"doc-{doctor.id}-token",
            role="doctor",
            user=UserInfo(
                id=doctor.id,
                name=doctor.name,
                email=doctor.email,
                role="doctor",
                specialization=doctor.specialization
            )
        )

    elif portal == "patient":
        # Search patient by ID (pat_1042 or 1042 or Patient #1042) or email
        clean_id = identifier.replace("Patient #", "").replace("Patient#", "").replace("pat_", "")
        patient = db.query(Patient).filter(
            (Patient.id == identifier) |
            (Patient.id == f"pat_{clean_id}") |
            (Patient.name.ilike(f"%{clean_id}%")) |
            (Patient.email.ilike(f"%{identifier}%"))
        ).first()

        if not patient:
            # Create synthetic patient on demand if not present
            synthetic_id = f"pat_{clean_id if clean_id else '1042'}"
            patient = Patient(
                id=synthetic_id,
                name=f"Patient #{clean_id if clean_id else '1042'}",
                email=f"patient{clean_id}@synthetic.local"
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)

        audit = AuditEvent(
            event_type="PORTAL_LOGIN",
            actor_role="patient",
            actor_id=patient.id,
            details=json.dumps({"portal": "patient_portal", "patient_id": patient.id})
        )
        db.add(audit)
        db.commit()

        return LoginResponse(
            access_token=f"pat-{patient.id}-token",
            role="patient",
            user=UserInfo(
                id=patient.id,
                name=patient.name,
                email=patient.email,
                role="patient"
            )
        )

    else:
        raise HTTPException(status_code=400, detail="Invalid portal specified. Must be 'doctor' or 'patient'.")
