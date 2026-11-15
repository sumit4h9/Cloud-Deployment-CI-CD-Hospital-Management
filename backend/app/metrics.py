from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

# HTTP metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests handled by the appointment service",
    ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"]
)

# Domain Appointment metrics
APPOINTMENTS_CREATED = Counter(
    "appointments_created_total",
    "Total appointments booked in the system"
)

APPOINTMENTS_COMPLETED = Counter(
    "appointments_completed_total",
    "Total appointments marked completed by doctors"
)

APPOINTMENTS_CANCELLED = Counter(
    "appointments_cancelled_total",
    "Total appointments cancelled"
)

CONFLICTS_PREVENTED = Counter(
    "concurrency_conflicts_prevented_total",
    "Total double-booking race condition conflicts prevented by mutual exclusion lock"
)

ACTIVE_SLOTS_GAUGE = Gauge(
    "active_available_slots",
    "Current count of bookable slots in the clinic"
)

def get_metrics_response() -> Response:
    """Return raw Prometheus metrics string formatted for scraper."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

