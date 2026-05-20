import time

from docker_client import client
from database import SessionLocal
from services.history_service import save_history
from metrics import container_memory_metric, container_status_metric
from services.container_service import calculate_memory_percent, build_alerts


def background_monitor():
    while True:
        try:
            containers = client.containers.list(all=True)

            for container in containers:
                stats = container.stats(stream=False)

                memory_percent = round(calculate_memory_percent(stats), 2)
                alerts = build_alerts(container, memory_percent)
                status = "warning" if alerts else "ok"

                container_memory_metric.labels(
                    container_name=container.name
                ).set(memory_percent)

                container_status_metric.labels(
                    container_name=container.name
                ).set(1 if container.status == "running" else 0)

                db = SessionLocal()

                try:
                    save_history(db, container.name, status, memory_percent, alerts)
                finally:
                    db.close()

            print("monitor snapshot saved")

        except Exception as e:
            print(f"monitor error: {e}")

        time.sleep(60)