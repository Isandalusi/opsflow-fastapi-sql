from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(40), unique=True, nullable=False, index=True)
    title = Column(String(150), nullable=False)
    area = Column(String(80), nullable=False)
    priority = Column(String(20), nullable=False, default="MEDIUM")
    status = Column(String(30), nullable=False, default="OPEN")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    audit_logs = relationship(
        "AuditLog",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="AuditLog.changed_at.asc()",
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False)
    note = Column(String(255), nullable=True)
    changed_by = Column(String(80), nullable=False, default="system")
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("WorkOrder", back_populates="audit_logs")
