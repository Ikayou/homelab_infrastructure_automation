from prometheus_client import Gauge

container_memory_metric = Gauge(
    "container_memory_percent",
    "Container memory usage percent",
    ["container_name"]
)

container_status_metric = Gauge(
    "container_status",
    "Container running status",
    ["container_name"]
)