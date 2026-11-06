import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base

def generate_id(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:8]}"

def utc_now():
    return datetime.now(timezone.utc)

class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=False, index=True)
    email = Column(String, unique=True, index=True)
    room = Column(String, nullable=True)

    slots = relationship("Slot", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor")

class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Synthetic format: "Patient #1042"
    email = Column(String, unique=True, index=True)

    appointments = relationship("Appointment", back_populates="patient")

class Slot(Base):
    __tablename__ = "slots"

    id = Column(String, primary_key=True, index=True, default=lambda: generate_id("slot_"))
    doctor_id = Column(String, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    start_time = Column(String, nullable=False)        # HH:MM (24h)
    end_time = Column(String, nullable=False)          # HH:MM (24h)
    is_available = Column(Boolean, default=True, nullable=False)

    doctor = relationship("Doctor", back_populates="slots")
    appointment = relationship("Appointment", back_populates="slot", uselist=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "date", "start_time", name="uq_doctor_date_slot"),
        Index("idx_doctor_date_avail", "doctor_id", "date", "is_available"),
    )

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, index=True, default=lambda: generate_id("APT-"))
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False, index=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    slot_id = Column(String, ForeignKey("slots.id"), nullable=True, index=True)
    date = Column(String, nullable=False, index=True)        # YYYY-MM-DD
    start_time = Column(String, nullable=False)              # HH:MM
    end_time = Column(String, nullable=False)                # HH:MM
    status = Column(String, default="Confirmed", nullable=False) # Confirmed, Rescheduled, Cancelled
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    slot = relationship("Slot", back_populates="appointment")

    __table_args__ = (
        Index("idx_doc_date_time_status", "doctor_id", "date", "start_time", "status"),
    )

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, index=True, default=lambda: generate_id("aud_"))
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    event_type = Column(String, nullable=False, index=True) # APPOINTMENT_CREATED, APPOINTMENT_CANCELLED, etc.
    actor_role = Column(String, nullable=False)             # doctor, patient, system
    actor_id = Column(String, nullable=False)
    details = Column(String, nullable=False)                # JSON or structured message
