"""
Background Job Worker Service.
Runs independent scheduled operational tasks:
1. Appointment Reminder Dispatcher: Identifies upcoming appointments in the next 24 hours.
2. Slot Expiry & Cleanup: Reclaims unoccupied past slots.
3. Operational Telemetry Heartbeat: Emits periodic health checkpoints into the audit log.
"""

import time
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from .database import SessionLocal
from .models import Appointment, Slot, AuditEvent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s"
)
logger = logging.getLogger("background-worker")

def dispatch_appointment_reminders(db: Session):
    """Finds confirmed appointments for tomorrow and records reminder dispatch."""
    now = datetime.now(timezone.utc)
    target_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    
    upcoming = db.query(Appointment).filter(
        Appointment.date == target_date,
        Appointment.status == "Confirmed"
    ).all()

    if upcoming:
        logger.info(f"Dispatching reminders for {len(upcoming)} appointments on {target_date}")
        for apt in upcoming:
            # Check if reminder already logged
            existing = db.query(AuditEvent).filter(
                AuditEvent.event_type == "REMINDER_DISPATCHED",
                AuditEvent.details.contains(apt.id)
            ).first()

            if not existing:
                reminder_event = AuditEvent(
                    event_type="REMINDER_DISPATCHED",
                    actor_role="system-worker",
                    actor_id="job_reminder_dispatcher",
                    details=json.dumps({
                        "appointment_id": apt.id,
                        "patient_id": apt.patient_id,
                        "doctor_id": apt.doctor_id,
                        "date": apt.date,
                        "time": apt.start_time,
                        "dispatched_at": now.isoformat()
                    })
                )
                db.add(reminder_event)
        db.commit()

def reclaim_expired_slots(db: Session):
    """Flags past unoccupied slots as expired/reclaimed."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Identify available slots on past dates
    expired = db.query(Slot).filter(
        Slot.date < now_str,
        Slot.is_available == True
    ).all()
    if expired:
        logger.info("Reclaiming %d past unoccupied availability slots", len(expired))
        for s in expired:
            s.is_available = False
            db.add(s)
        db.commit()

def record_worker_heartbeat(db: Session):
    """Records periodic worker liveness telemetry."""
    heartbeat = AuditEvent(
        event_type="WORKER_HEARTBEAT",
        actor_role="system-worker",
        actor_id="background_scheduler",
        details=json.dumps({
            "status": "active",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tasks_executed": ["reminder_dispatcher", "slot_cleanup", "heartbeat"]
        })
    )
    db.add(heartbeat)
    db.commit()

def run_worker_loop(interval_seconds: int = 30):
    logger.info("Starting Background Job Worker loop (interval: %ds)...", interval_seconds)
    while True:
        db = SessionLocal()
        try:
            dispatch_appointment_reminders(db)
            reclaim_expired_slots(db)
            record_worker_heartbeat(db)
        except Exception as e:
            logger.error("Error executing background job cycle: %s", e)
        finally:
            db.close()
        
        time.sleep(interval_seconds)

if __name__ == "__main__":
    run_worker_loop()

