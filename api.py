from pathlib import Path
import sqlite3

from fastapi import FastAPI, HTTPException, Query

app = FastAPI(
    title="Supplier Reliability API",
    description="Read-only REST API for the Supplier Reliability System",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "database" / "supplier_reliability.db"


def get_db_connection():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Database file not found."
        )

    connection = sqlite3.connect(
        f"file:{DB_PATH.as_posix()}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row
    return connection


def fetch_all(query, params=()):
    connection = get_db_connection()
    try:
        cursor = connection.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def fetch_one(query, params=()):
    connection = get_db_connection()
    try:
        cursor = connection.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        connection.close()


@app.get("/")
def home():
    return {
        "message": "Supplier Reliability API is running",
        "docs": "/docs"
    }


@app.get("/health")
def health():
    try:
        fetch_one("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/suppliers")
def get_suppliers(
    search: str | None = None,
    country: str | None = None,
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    query = "SELECT * FROM suppliers WHERE 1=1"
    params = []

    if search:
        query += " AND supplier_name LIKE ?"
        params.append(f"%{search}%")

    if country:
        query += " AND country = ?"
        params.append(country)

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY supplier_name LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return fetch_all(query, params)


@app.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):
    supplier = fetch_one(
        "SELECT * FROM suppliers WHERE supplier_id = ?",
        (supplier_id,)
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    return supplier


@app.get("/scores")
def get_scores(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    query = """
        SELECT
            ss.*,
            s.supplier_name
        FROM supplier_scores ss
        LEFT JOIN suppliers s
            ON ss.supplier_id = s.supplier_id
        ORDER BY ss.final_score DESC
        LIMIT ? OFFSET ?
    """

    return fetch_all(query, (limit, offset))


@app.get("/risk-signals")
def get_risk_signals(
    supplier_id: str | None = None,
    severity: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    query = """
        SELECT
            rs.*,
            s.supplier_name
        FROM risk_signals rs
        LEFT JOIN suppliers s
            ON rs.supplier_id = s.supplier_id
        WHERE 1=1
    """
    params = []

    if supplier_id:
        query += " AND rs.supplier_id = ?"
        params.append(supplier_id)

    if severity:
        query += " AND rs.severity = ?"
        params.append(severity.upper())

    query += " ORDER BY rs.observed_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    return fetch_all(query, params)


@app.get("/score-history/{supplier_id}")
def get_score_history(supplier_id: str):
    supplier = fetch_one(
        "SELECT supplier_id FROM suppliers WHERE supplier_id = ?",
        (supplier_id,)
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    query = """
        SELECT *
        FROM supplier_score_history
        WHERE supplier_id = ?
        ORDER BY scoring_period
    """

    return fetch_all(query, (supplier_id,))