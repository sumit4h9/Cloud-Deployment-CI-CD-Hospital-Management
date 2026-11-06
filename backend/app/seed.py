from datetime import datetime
from sqlalchemy.orm import Session
from .database import engine, SessionLocal, Base
from .models import Doctor, Patient, Slot, Appointment, AuditEvent

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    # If already seeded, skip
    if db.query(Doctor).first():
        db.close()
        return

    print("Seeding synthetic healthcare appointment data...")

    # 1. Doctors
    doc1 = Doctor(
        id="doc_1",
        name="Dr. Ananya Mehta",
        specialization="Cardiology",
        email="ananya.mehta@clinic.local",
        room="Suite 4B"
    )
    doc2 = Doctor(
        id="doc_2",
        name="Dr. Marcus Vance",
        specialization="Cardiology",
        email="marcus.vance@clinic.local",
        room="Suite 2A"
    )
    doc3 = Doctor(
        id="doc_3",
        name="Dr. Sarah Lin",
        specialization="Neurology",
        email="sarah.lin@clinic.local",
        room="Suite 3C"
    )
    db.add_all([doc1, doc2, doc3])
    db.commit()

    # 2. Patients (Synthetic)
    patients = [
        Patient(id="pat_1014", name="Patient #1014", email="patient1014@synthetic.local"),
        Patient(id="pat_1029", name="Patient #1029", email="patient1029@synthetic.local"),
        Patient(id="pat_1042", name="Patient #1042", email="patient1042@synthetic.local"),
        Patient(id="pat_1055", name="Patient #1055", email="patient1055@synthetic.local"),
        Patient(id="pat_1088", name="Patient #1088", email="patient1088@synthetic.local"),
        Patient(id="pat_1102", name="Patient #1102", email="patient1102@synthetic.local"),
        Patient(id="pat_1140", name="Patient #1140", email="patient1140@synthetic.local"),
    ]
    db.add_all(patients)
    db.commit()

    # 3. Slots for Dr. Ananya on 2026-11-06 (7 Booked, 3 Available = 10 total)
    slot_configs = [
        ("09:00", "09:30", False, "pat_1014", "APT-10478"),
        ("09:30", "10:00", False, "pat_1029", "APT-10480"),
        ("10:00", "10:30", True,  None,       None),        # Bookable
        ("10:30", "11:00", False, "pat_1042", "APT-10482"),
        ("11:00", "11:30", False, "pat_1055", "APT-10485"),
        ("11:30", "12:00", True,  None,       None),        # Bookable
        ("14:00", "14:30", False, "pat_1088", "APT-10491"),
        ("14:30", "15:00", False, "pat_1102", "APT-10494"),
        ("15:00", "15:30", True,  None,       None),        # Bookable
        ("15:30", "16:00", False, "pat_1140", "APT-10499"),
    ]

    for start_t, end_t, is_avail, pat_id, apt_id in slot_configs:
        slot = Slot(
            doctor_id="doc_1",
            date="2026-11-06",
            start_time=start_t,
            end_time=end_t,
            is_available=is_avail
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)

        if not is_avail and pat_id and apt_id:
            apt = Appointment(
                id=apt_id,
                doctor_id="doc_1",
                patient_id=pat_id,
                slot_id=slot.id,
                date="2026-11-06",
                start_time=start_t,
                end_time=end_t,
                status="Confirmed",
                created_at=datetime(2026, 11, 1, 9, 0)
            )
            db.add(apt)

    # 4. Upcoming appointments for future dates (e.g. 2026-11-07, 2026-11-08)
    upcoming_data = [
        ("2026-11-07", "09:30", "10:00", "pat_1014", "APT-10510"),
        ("2026-11-07", "11:00", "11:30", "pat_1042", "APT-10515"),
        ("2026-11-09", "10:00", "10:30", "pat_1055", "APT-10522"),
        ("2026-11-10", "14:00", "14:30", "pat_1088", "APT-10530"),
    ]
    for d, st, et, pid, aid in upcoming_data:
        s = Slot(doctor_id="doc_1", date=d, start_time=st, end_time=et, is_available=False)
        db.add(s)
        db.commit()
        db.refresh(s)
        a = Appointment(
            id=aid,
            doctor_id="doc_1",
            patient_id=pid,
            slot_id=s.id,
            date=d,
            start_time=st,
            end_time=et,
            status="Confirmed"
        )
        db.add(a)

    # Seed slots for Dr. Marcus Vance
    for t in ["10:00", "11:00", "14:00"]:
        db.add(Slot(doctor_id="doc_2", date="2026-11-06", start_time=t, end_time=f"{int(t[:2])}:30", is_available=True))

    # Initial Audit event
    db.add(AuditEvent(
        event_type="SYSTEM_INITIALIZED",
        actor_role="system",
        actor_id="seed",
        details='{"message": "Synthetic appointments seed loaded successfully"}'
    ))

    db.commit()
    db.close()
    print("Database seeded successfully.")

if __name__ == "__main__":
    seed_database()

