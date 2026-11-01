
import os
import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.auth.database import initialize_auth_db
from backend.upload_routes import router as upload_router


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

app = FastAPI(
    title="YottaFlex.ai - Data Quality Monitoring API",
    description="Supplier Reliability and Data Quality Monitoring Platform",
    version="1.2.0"
)


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:5176",

    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
    "http://127.0.0.1:5176",
]

# Production frontend URL
frontend_url = os.getenv("FRONTEND_URL")

if frontend_url:
    for url in frontend_url.split(","):
        url = url.strip().rstrip("/")
        if url and url not in allowed_origins:
            allowed_origins.append(url)


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = (
    BASE_DIR
    / "database"
    / "supplier_reliability.db"
)


def get_db_connection():
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Database file not found: {DB_PATH}"
        )

    try:
        connection = sqlite3.connect(
            f"file:{DB_PATH.as_posix()}?mode=ro",
            uri=True,
            timeout=30
        )

        connection.row_factory = sqlite3.Row

        return connection

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(error)}"
        )


def fetch_all(query, params=()):
    connection = get_db_connection()

    try:
        cursor = connection.execute(query, params)

        return [
            dict(row)
            for row in cursor.fetchall()
        ]

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(error)}"
        )

    finally:
        connection.close()


def fetch_one(query, params=()):
    connection = get_db_connection()

    try:
        cursor = connection.execute(query, params)

        row = cursor.fetchone()

        return dict(row) if row else None

    except sqlite3.Error as error:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(error)}"
        )

    finally:
        connection.close()


# --------------------------------------------------
# ROUTER REGISTRATION
# --------------------------------------------------

app.include_router(auth_router)
app.include_router(upload_router)


# --------------------------------------------------
# APPLICATION STARTUP
# --------------------------------------------------

@app.on_event("startup")
def startup_event():
    initialize_auth_db()

    print("====================================")
    print("YottaFlex.ai API Started")
    print(f"Database: {DB_PATH}")
    print("Authentication: Enabled")
    print("CSV Upload: Enabled")
    print("Pipeline Monitoring: Enabled")
    print("====================================")


# --------------------------------------------------
# HOME ENDPOINT
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "YottaFlex.ai API is running",
        "platform": "Data Quality Monitoring",
        "version": "1.2.0",
        "status": "online",
        "docs": "/docs"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    try:
        fetch_one("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
            "platform": "YottaFlex.ai"
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# --------------------------------------------------
# GET ALL SUPPLIERS
# --------------------------------------------------

@app.get("/suppliers")
def get_suppliers(
    search: str | None = None,
    country: str | None = None,
    category: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0)
):
    query = """
        SELECT *
        FROM suppliers
        WHERE 1=1
    """

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

    query += """
        ORDER BY supplier_name
        LIMIT ? OFFSET ?
    """

    params.extend([limit, offset])

    return fetch_all(query, params)


# --------------------------------------------------
# GET SUPPLIER BY ID
# --------------------------------------------------

@app.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: str):

    supplier = fetch_one(
        """
        SELECT *
        FROM suppliers
        WHERE supplier_id = ?
        """,
        (supplier_id,)
    )

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    return supplier


# --------------------------------------------------
# GET SUPPLIER SCORES
# --------------------------------------------------

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


# --------------------------------------------------
# GET RISK SIGNALS
# --------------------------------------------------

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

    query += """
        ORDER BY rs.observed_at DESC
        LIMIT ? OFFSET ?
    """

    params.extend([limit, offset])

    return fetch_all(query, params)


# --------------------------------------------------
# GET SUPPLIER SCORE HISTORY
# --------------------------------------------------

@app.get("/score-history/{supplier_id}")
def get_score_history(supplier_id: str):

    supplier = fetch_one(
        """
        SELECT supplier_id
        FROM suppliers
        WHERE supplier_id = ?
        """,
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
