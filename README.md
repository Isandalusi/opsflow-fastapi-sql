# OpsFlow FastAPI & SQL

[![CI - FastAPI & Pytest](https://github.com/Isandalusi/opsflow-fastapi-sql/actions/workflows/ci.yml/badge.svg)](https://github.com/Isandalusi/opsflow-fastapi-sql/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)

Microservicio REST desarrollado en **Python (FastAPI + SQLAlchemy + Pydantic v2)** para la gestión de órdenes operativas con **trazabilidad automática de estados (`AuditLog`)**, validación de transiciones permitidas, métricas SQL agregadas, suite de pruebas automatizadas en **Pytest**, **Dockerfile** e integración continua con **GitHub Actions**.

---

## Arquitectura del Proyecto

```text
opsflow-fastapi-sql/
├── app/
│   ├── __init__.py
│   ├── database.py    # Engine SQLAlchemy, SessionLocal y dependencia get_db
│   ├── models.py      # Modelos relacionales WorkOrder (1:N) AuditLog
│   ├── schemas.py     # Esquemas Pydantic v2 y validación de estados/prioridades
│   └── main.py        # Endpoints FastAPI, máquina de estados y métricas SQL
├── tests/
│   └── test_orders.py # Tests de integración con SQLite en memoria + TestClient
├── .github/workflows/
│   └── ci.yml         # Pipeline automático de Pytest en GitHub Actions
├── Dockerfile
└── requirements.txt
```

## Endpoints Principales

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/health` | Health check del servicio |
| `POST` | `/orders` | Crea una orden y registra el primer evento en `audit_logs` |
| `GET` | `/orders` | Lista órdenes con filtros opcionales (`status`, `priority`, `area`) |
| `GET` | `/orders/{id}` | Obtiene detalle de una orden junto con su historial de auditoría |
| `PATCH` | `/orders/{id}/status` | Valida transición de estado y guarda log de auditoría |
| `GET` | `/orders/{id}/audit` | Devuelve la línea de tiempo de cambios de estado |
| `GET` | `/metrics/summary` | Agrupa órdenes por estado mediante `COUNT` SQL |

## Ejecución Local y Docker

```bash
# Local con Python
pip install -r requirements.txt
uvicorn app.main:app --reload
# Documentación interactiva Swagger UI en http://127.0.0.1:8000/docs

# Ejecutar pruebas automatizadas
pytest -v

# Con Docker
docker build -t opsflow-fastapi-sql .
docker run -p 8000:8000 opsflow-fastapi-sql
```
