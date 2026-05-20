from fastapi import APIRouter, Depends, HTTPException
import requests
import docker
from auth import require_client_role
from docker_client import client
from config import SLACK_WEBHOOK_URL
from sqlalchemy.orm import Session
from database import get_db
from services.history_service import save_history
from services.container_service import (
    calculate_memory_percent,
    calculate_cpu_percent,
    build_alerts,
)
import httpx

router = APIRouter(prefix="/containers", tags=["Containers"])


@router.get("", dependencies=[Depends(require_client_role("container:view"))])
def list_containers():
    containers = client.containers.list(all=True)

    return [
        {
            "name": c.name,
            "id": c.short_id,
            "status": c.status,
            "image": c.image.tags,
        }
        for c in containers
    ]


@router.get("/{container_name}", dependencies=[Depends(require_client_role("container:view"))])
def get_container(container_name: str):
    try:
        container = client.containers.get(container_name)

        return {
            "name": container.name,
            "id": container.short_id,
            "status": container.status,
            "image": container.image.tags,
            "ports": container.attrs["NetworkSettings"]["Ports"],
            "created": container.attrs["Created"],
        }

    except docker.errors.NotFound:
        raise HTTPException(
            status_code=404,
            detail="Container not found"
        )


@router.get("/{container_name}/logs", dependencies=[Depends(require_client_role("container:view"))])
def get_container_logs(container_name: str, lines: int = 50):
    container = client.containers.get(container_name)
    logs = container.logs(tail=lines).decode("utf-8", errors="replace")

    return {
        "name": container.name,
        "lines": lines,
        "logs": logs,
    }


@router.get("/{container_name}/health", dependencies=[Depends(require_client_role("container:view"))])
def container_health(container_name: str):
    container = client.containers.get(container_name)

    return {
        "name": container.name,
        "status": container.status,
        "running": container.status == "running",
        "restart_count": container.attrs["RestartCount"],
    }


@router.get("/{container_name}/stats", dependencies=[Depends(require_client_role("container:view"))])
def get_container_stats(container_name: str):
    container = client.containers.get(container_name)
    stats = container.stats(stream=False)

    memory_usage = stats["memory_stats"].get("usage", 0)
    memory_limit = stats["memory_stats"].get("limit", 0)

    return {
        "name": container.name,
        "status": container.status,
        "cpu_percent": round(calculate_cpu_percent(stats), 2),
        "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
        "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
    }


@router.get("/{container_name}/alert", dependencies=[Depends(require_client_role("container:view"))])
def container_alert(container_name: str, db: Session = Depends(get_db)):
    container = client.containers.get(container_name)
    stats = container.stats(stream=False)

    memory_percent = round(calculate_memory_percent(stats), 2)
    alerts = build_alerts(container, memory_percent)
    status = "warning" if alerts else "ok"

    save_history(db, container.name, status, memory_percent, alerts)

    return {
        "name": container.name,
        "status": status,
        "memory_percent": memory_percent,
        "alerts": alerts,
    }


@router.post("/{container_name}/notify", dependencies=[Depends(require_client_role("container:notify"))])
async def notify_alert(container_name: str):
    if not SLACK_WEBHOOK_URL:
        raise HTTPException(status_code=500, detail="SLACK_WEBHOOK_URL is not set")

    container = client.containers.get(container_name)
    stats = container.stats(stream=False)

    memory_percent = round(calculate_memory_percent(stats), 2)
    alerts = build_alerts(container, memory_percent)

    if not alerts:
        return {
            "status": "ok",
            "message": "no alerts"
        }

    message = {
        "text": f"⚠️ Container Alert: {container_name}\n" + "\n".join(alerts)
    }

    async with httpx.AsyncClient() as http_client:
        response = await http_client.post(
            SLACK_WEBHOOK_URL,
            json=message
        )

    return {
        "status": "warning",
        "alerts": alerts,
        "slack_status_code": response.status_code,
        "message": "notification sent"
    }


@router.post("/{container_name}/restart", dependencies=[Depends(require_client_role("container:restart"))])
def restart_container(container_name: str):
    blocked = ["traefik", "container-api"]

    if container_name in blocked:
        raise HTTPException(
            status_code=403,
            detail=f"{container_name} darf nicht über diese API neu gestartet werden"
        )

    container = client.containers.get(container_name)
    container.restart()

    return {
        "message": f"{container_name} restarted successfully"
    }