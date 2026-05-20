from models import ContainerHistory


def save_history(db, container_name: str, status: str, memory_percent: float, alerts: list):
    history = ContainerHistory(
        container_name=container_name,
        status=status,
        memory_percent=memory_percent,
        alerts=",".join(alerts),
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history