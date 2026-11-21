import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_create_order_and_initial_audit(client):
    payload = {
        "code": "OPS-2026-001",
        "title": "Validar conciliacion bancaria",
        "area": "Operaciones",
        "priority": "HIGH",
        "description": "Revision diaria de lote",
    }
    resp = client.post("/orders", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"
    assert len(data["audit_logs"]) == 1
    assert data["audit_logs"][0]["new_status"] == "OPEN"


def test_duplicate_code_returns_409(client):
    payload = {"code": "OPS-DUP-1", "title": "Orden A", "area": "IT", "priority": "LOW"}
    assert client.post("/orders", json=payload).status_code == 201
    assert client.post("/orders", json=payload).status_code == 409


def test_status_transition_and_audit_trail(client):
    created = client.post(
        "/orders",
        json={"code": "OPS-2026-002", "title": "Despliegue API", "area": "Backend", "priority": "CRITICAL"},
    ).json()
    oid = created["id"]

    r1 = client.patch(f"/orders/{oid}/status", json={"new_status": "IN_PROGRESS", "note": "En curso", "changed_by": "jesus"})
    assert r1.status_code == 200
    assert r1.json()["status"] == "IN_PROGRESS"

    r2 = client.patch(f"/orders/{oid}/status", json={"new_status": "DONE", "note": "Validado", "changed_by": "jesus"})
    assert r2.status_code == 200
    assert r2.json()["status"] == "DONE"

    audit = client.get(f"/orders/{oid}/audit").json()
    assert [entry["new_status"] for entry in audit] == ["OPEN", "IN_PROGRESS", "DONE"]

    invalid = client.patch(f"/orders/{oid}/status", json={"new_status": "OPEN", "changed_by": "jesus"})
    assert invalid.status_code == 422


def test_metrics_and_filters(client):
    client.post("/orders", json={"code": "OPS-10", "title": "Ticket 1", "area": "SQL", "priority": "HIGH"})
    client.post("/orders", json={"code": "OPS-11", "title": "Ticket 2", "area": "IT", "priority": "LOW"})

    high_only = client.get("/orders?priority=HIGH").json()
    assert len(high_only) == 1
    assert high_only[0]["code"] == "OPS-10"

    summary = client.get("/metrics/summary").json()
    assert summary["total_orders"] == 2
    assert summary["by_status"]["OPEN"] == 2
