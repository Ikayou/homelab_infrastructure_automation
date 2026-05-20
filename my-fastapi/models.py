from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from database import Base


class ContainerHistory(Base):
    __tablename__ = "container_history"

    id = Column(Integer, primary_key=True, index=True)
    container_name = Column(String, index=True)
    status = Column(String)
    memory_percent = Column(Float)
    alerts = Column(String)
    created_at = Column(DateTime, default=datetime.now)