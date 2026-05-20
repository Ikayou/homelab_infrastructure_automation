from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import csv

from auth import require_client_role
from database import get_db
from models import ContainerHistory

router = APIRouter(prefix="/history", tags=["History"])


@router.get("/{container_name}", dependencies=[Depends(require_client_role("container:view"))])
def get_history(container_name: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ContainerHistory)
        .filter(ContainerHistory.container_name == container_name)
        .order_by(ContainerHistory.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "container_name": row.container_name,
            "status": row.status,
            "memory_percent": row.memory_percent,
            "alerts": row.alerts.split(",") if row.alerts else [],
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/{container_name}/export", dependencies=[Depends(require_client_role("container:view"))])
def export_history(container_name: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ContainerHistory)
        .filter(ContainerHistory.container_name == container_name)
        .order_by(ContainerHistory.created_at.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "container_name",
        "status",
        "memory_percent",
        "alerts",
        "created_at"
    ])

    for row in rows:
        writer.writerow([
            row.container_name,
            row.status,
            row.memory_percent,
            row.alerts,
            row.created_at,
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={container_name}_history.csv"
        }
    )