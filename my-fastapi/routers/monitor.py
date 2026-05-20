from fastapi import APIRouter, Depends

from auth import require_client_role
from docker_client import client
from sqlalchemy.orm import Session
from database import get_db
from services.history_service import save_history
from services.container_service import calculate_memory_percent, build_alerts

router = APIRouter(prefix="/monitor", tags=["Monitor"])


@router.post("/snapshot", dependencies=[Depends(require_client_role("container:admin"))])
def monitor_snapshot(db: Session = Depends(get_db)):
    containers = client.containers.list(all=True)

    results = []

    for container in containers:
        stats = container.stats(stream=False)

        memory_percent = round(calculate_memory_percent(stats), 2)
        alerts = build_alerts(container, memory_percent)
        status = "warning" if alerts else "ok"

        save_history(db, container.name, status, memory_percent, alerts)

        results.append({
            "name": container.name,
            "status": status,
            "memory_percent": memory_percent,
            "alerts": alerts,
        })

    return {
        "message": "snapshot saved",
        "containers_checked": len(results),
        "results": results,
    }