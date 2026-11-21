from datetime import datetime, timezone
from typing import List, Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import AuditLog, WorkOrder
from app.schemas import AuditLogRead, StatusTransition, WorkOrderCreate, WorkOrderDetail, WorkOrderRead

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="OpsFlow FastAPI & SQL",
    description="API REST para gestion de ordenes operativas y trazabilidad de estados con auditoria automatica.",
    version="1.0.0",
)

ALLOWED_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "BLOCKED", "CANCELLED"},
    "IN_PROGRESS": {"BLOCKED", "DONE", "CANCELLED"},
    "BLOCKED": {"IN_PROGRESS", "CANCELLED"},
    "DONE": set(),
    "CANCELLED": set(),
}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "opsflow-fastapi-sql"}


@app.post("/orders", response_model=WorkOrderDetail, status_code=status.HTTP_201_CREATED, tags=["Work Orders"])
def create_order(payload: WorkOrderCreate, db: Session = Depends(get_db)):
    existing = db.query(WorkOrder).filter(WorkOrder.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Order code {payload.code} already exists.")

    order = WorkOrder(
        code=payload.code,
        title=payload.title,
        area=payload.area,
        priority=payload.priority,
        status="OPEN",
        description=payload.description,
    )
    db.add(order)
    db.flush()

    initial_log = AuditLog(
        order_id=order.id,
        previous_status=None,
        new_status="OPEN",
        note="Orden creada inicialmente",
        changed_by="system",
    )
    db.add(initial_log)
    db.commit()
    db.refresh(order)
    return order


@app.get("/orders", response_model=List[WorkOrderRead], tags=["Work Orders"])
def list_orders(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    priority: Optional[str] = Query(default=None),
    area: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(WorkOrder)
    if status_filter:
        query = query.filter(WorkOrder.status == status_filter)
    if priority:
        query = query.filter(WorkOrder.priority == priority)
    if area:
        query = query.filter(WorkOrder.area == area)
    return query.order_by(WorkOrder.id.desc()).all()


@app.get("/orders/{order_id}", response_model=WorkOrderDetail, tags=["Work Orders"])
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found.")
    return order


@app.patch("/orders/{order_id}/status", response_model=WorkOrderDetail, tags=["Work Orders"])
def transition_order_status(order_id: int, payload: StatusTransition, db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found.")

    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if payload.new_status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition from {order.status} to {payload.new_status}.",
        )

    prev = order.status
    order.status = payload.new_status
    order.updated_at = datetime.now(timezone.utc)

    log = AuditLog(
        order_id=order.id,
        previous_status=prev,
        new_status=payload.new_status,
        note=payload.note,
        changed_by=payload.changed_by,
    )
    db.add(log)
    db.commit()
    db.refresh(order)
    return order


@app.get("/orders/{order_id}/audit", response_model=List[AuditLogRead], tags=["Audit"])
def get_order_audit(order_id: int, db: Session = Depends(get_db)):
    order = db.query(WorkOrder).filter(WorkOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Work order not found.")
    return order.audit_logs


@app.get("/metrics/summary", tags=["Metrics"])
def metrics_summary(db: Session = Depends(get_db)):
    rows = db.query(WorkOrder.status, func.count(WorkOrder.id)).group_by(WorkOrder.status).all()
    by_status = {status_name: count for status_name, count in rows}
    total = sum(by_status.values())
    return {"total_orders": total, "by_status": by_status}
