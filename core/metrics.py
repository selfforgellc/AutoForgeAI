
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("http_request_duration_seconds", "HTTP request latency", ["endpoint"])

DIAGNOSIS_COUNT = Counter("diagnosis_total", "Total diagnoses executed")
CACHE_HITS = Counter("cache_hits_total", "Redis cache hits")
CACHE_MISSES = Counter("cache_misses_total", "Redis cache misses")

def metrics_response():
    return generate_latest(), CONTENT_TYPE_LATEST
