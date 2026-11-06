from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .seed import seed_database
from .routes import health, doctors, appointments, slots, audit

# Ensure schema and initial seed data are populated
Base.metadata.create_all(bind=engine)
seed_database()

@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_database()
    yield

app = FastAPI(
    title="Doctor Appointment Scheduling API",
    description="A lightweight, production-grade doctor appointment scheduling service using synthetic patient data.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local dev & frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(slots.router)
app.include_router(audit.router)

@app.get("/")
def root():
    return {
        "service": "Doctor Appointment Scheduling Platform",
        "docs": "/docs",
        "health": "/health",
        "ready": "/ready"
    }
