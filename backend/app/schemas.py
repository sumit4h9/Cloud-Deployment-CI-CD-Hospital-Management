from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Doctor Schemas
class DoctorBase(BaseModel):
    name: str
    specialization: str
    email: str
    room: Optional[str] = None

class DoctorOut(DoctorBase):
    id: str
    next_available_slot: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Patient Schemas
class PatientBase(BaseModel):
    name: str
    email: str

class PatientOut(PatientBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

# Slot Schemas
class SlotBase(BaseModel):
    date: str  # YYYY-MM-DD
    start_time: str # HH:MM
    end_time: str   # HH:MM

class SlotCreate(SlotBase):
    doctor_id: str

class SlotOut(SlotBase):
    id: str
    doctor_id: str
    is_available: bool
    status: str = "Available" # "Available" or "Booked"
    model_config = ConfigDict(from_attributes=True)

# Appointment Schemas
class AppointmentCreate(BaseModel):
    doctor_id: str
    patient_id: str
    slot_id: Optional[str] = None
    date: str
    start_time: str
    end_time: Optional[str] = None

class AppointmentReschedule(BaseModel):
    new_slot_id: Optional[str] = None
    new_date: str
    new_start_time: str
    new_end_time: Optional[str] = None

class AppointmentOut(BaseModel):
    id: str
    doctor_id: str
    patient_id: str
    slot_id: Optional[str] = None
    date: str
    start_time: str
    end_time: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    specialization: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# Audit Event
class AuditEventOut(BaseModel):
    id: str
    timestamp: datetime
    event_type: str
    actor_role: str
    actor_id: str
    details: str
    model_config = ConfigDict(from_attributes=True)

# System Health
class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

class ReadyResponse(BaseModel):
    status: str
    database: str
