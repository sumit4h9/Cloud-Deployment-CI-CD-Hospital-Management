import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, Base
from .seed import seed_database
from .routes import health, doctors, appointments, slots, audit, auth
from .metrics import get_metrics_response

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] [API] %(message)s"
)
logger = logging.getLogger("appointment-api")

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    # Never log credentials or tokens
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)")
    return response

# Enable configurable CORS for local dev & production
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(slots.router)
app.include_router(audit.router)

@app.get("/metrics", tags=["Monitoring"], include_in_schema=True)
def prometheus_metrics():
    return get_metrics_response()

# Mount frontend build static files if present for turnkey deployment
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/")
    def serve_frontend_root():
        index_path = os.path.join(FRONTEND_DIST, "index.html")
        return FileResponse(index_path)
else:
    @app.get("/")
    def root():
        return {
            "service": "Doctor Appointment Scheduling Platform",
            "docs": "/docs",
            "health": "/health",
            "ready": "/ready"
        }
