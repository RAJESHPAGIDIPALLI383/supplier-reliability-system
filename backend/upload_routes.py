
import io
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse

router = APIRouter(prefix="/upload", tags=["Data Upload"])

# ================= PATHS =================

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent

UPLOAD_DIR = BACKEND_DIR / "uploads"
REPORT_DIR = UPLOAD_DIR / "reports"
DATABASE_DIR = PROJECT_DIR / "database"
DB_PATH = DATABASE_DIR / "supplier_reliability.db"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# ================= PIPELINE HISTORY DATABASE =================

def get_db_connection():
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_pipeline_history_db():
    connection = get_db_connection()
    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                filename TEXT NOT NULL,
                status TEXT NOT NULL,
                executed_at TEXT NOT NULL,
                total_records INTEGER NOT NULL,
                valid_records INTEGER NOT NULL,
                rejected_records INTEGER NOT NULL,
                missing_value_records INTEGER NOT NULL,
                duplicate_records INTEGER NOT NULL,
                quality_score REAL NOT NULL,
                valid_report TEXT,
                rejected_report TEXT,
                valid_preview TEXT,
                rejected_preview TEXT
            )
        """)
        connection.commit()
    finally:
        connection.close()


# Create the history table when this router is loaded.
initialize_pipeline_history_db()


def save_pipeline_run(result):
    connection = get_db_connection()
    try:
        connection.execute("""
            INSERT INTO pipeline_runs (
                run_id, filename, status, executed_at,
                total_records, valid_records, rejected_records,
                missing_value_records, duplicate_records,
                quality_score, valid_report, rejected_report,
                valid_preview, rejected_preview
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["run_id"],
            result["filename"],
            result["status"],
            result["executed_at"],
            result["total_records"],
            result["valid_records"],
            result["rejected_records"],
            result["missing_value_records"],
            result["duplicate_records"],
            result["quality_score"],
            result["reports"]["valid"],
            result["reports"]["rejected"],
            json.dumps(result["valid_preview"]),
            json.dumps(result["rejected_preview"])
        ))
        connection.commit()
    finally:
        connection.close()


def serialize_pipeline_run(row, include_previews=False):
    result = dict(row)

    if include_previews:
        result["valid_preview"] = json.loads(
            result.pop("valid_preview") or "[]"
        )
        result["rejected_preview"] = json.loads(
            result.pop("rejected_preview") or "[]"
        )
    else:
        result.pop("valid_preview", None)
        result.pop("rejected_preview", None)

    result["reports"] = {
        "valid": result.pop("valid_report"),
        "rejected": result.pop("rejected_report")
    }

    # Compatibility aliases for frontend components that use these names.
    result["total_rows"] = result["total_records"]
    result["valid_rows"] = result["valid_records"]
    result["rejected_rows"] = result["rejected_records"]
    result["missing_rows"] = result["missing_value_records"]
    result["duplicate_rows"] = result["duplicate_records"]

    return result


# ================= CSV UPLOAD =================

@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a CSV file."
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Maximum file size is 20 MB."
        )

    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid CSV file."
        )

    if df.empty or len(df.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail="CSV contains no data."
        )

    safe_name = Path(file.filename).name
    save_path = UPLOAD_DIR / safe_name
    df.to_csv(save_path, index=False)

    normalized_df = df.astype("string").apply(
        lambda col: col.str.strip()
    )

    return {
        "message": "CSV uploaded successfully",
        "filename": safe_name,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": df.columns.tolist(),
        "preview": df.head(10).fillna("").to_dict(orient="records"),
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(normalized_df.duplicated().sum())
    }


# ================= PIPELINE EXECUTION =================

@router.post("/pipeline/run")
async def run_pipeline(filename: str = Query(...)):
    safe_name = Path(filename).name

    if safe_name != filename or not safe_name.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Invalid filename."
        )

    file_path = UPLOAD_DIR / safe_name

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please upload the CSV first."
        )

    try:
        df = pd.read_csv(file_path)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Unable to read dataset."
        )

    if df.empty:
        raise HTTPException(
            status_code=400,
            detail="Dataset is empty."
        )

    total_rows = len(df)

    # Rule 1: Detect records containing missing values.
    missing_mask = df.isna().any(axis=1)

    # Rule 2: Detect exact duplicates after trimming whitespace.
    normalized_df = df.astype("string").apply(
        lambda col: col.str.strip()
    )
    duplicate_mask = normalized_df.duplicated(keep="first")

    # Reject a record only once, even if it has multiple issues.
    rejected_mask = missing_mask | duplicate_mask

    valid_df = df.loc[~rejected_mask].copy()
    rejected_df = df.loc[rejected_mask].copy()

    # Add rejection reasons.
    reasons = []

    for index in df.index[rejected_mask]:
        row_reasons = []

        if missing_mask.loc[index]:
            row_reasons.append("Missing values")

        if duplicate_mask.loc[index]:
            row_reasons.append("Duplicate record")

        reasons.append(", ".join(row_reasons))

    rejected_df["rejection_reason"] = reasons

    valid_count = len(valid_df)
    rejected_count = len(rejected_df)

    quality_score = round(
        (valid_count / total_rows) * 100, 2
    )

    run_id = str(uuid.uuid4())

    valid_report = REPORT_DIR / f"{run_id}_valid.csv"
    rejected_report = REPORT_DIR / f"{run_id}_rejected.csv"

    valid_df.to_csv(valid_report, index=False)
    rejected_df.to_csv(rejected_report, index=False)

    result = {
        "message": "Pipeline executed successfully",
        "run_id": run_id,
        "filename": safe_name,
        "status": "Completed",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "total_records": total_rows,
        "valid_records": valid_count,
        "rejected_records": rejected_count,
        "missing_value_records": int(missing_mask.sum()),
        "duplicate_records": int(duplicate_mask.sum()),
        "quality_score": quality_score,
        "valid_preview": valid_df.head(10).fillna("").to_dict(
            orient="records"
        ),
        "rejected_preview": rejected_df.head(10).fillna("").to_dict(
            orient="records"
        ),
        "reports": {
            "valid": f"/upload/pipeline/report/{run_id}/valid",
            "rejected": f"/upload/pipeline/report/{run_id}/rejected"
        }
    }

    # Save only after the pipeline and report generation succeed.
    try:
        save_pipeline_run(result)
    except sqlite3.Error:
        # Do not silently report success if history could not be saved.
        for report_path in (valid_report, rejected_report):
            if report_path.exists():
                report_path.unlink()

        raise HTTPException(
            status_code=500,
            detail="Pipeline completed but history could not be saved."
        )

    # Keep original response fields and add frontend-compatible aliases.
    result["total_rows"] = result["total_records"]
    result["valid_rows"] = result["valid_records"]
    result["rejected_rows"] = result["rejected_records"]
    result["missing_rows"] = result["missing_value_records"]
    result["duplicate_rows"] = result["duplicate_records"]

    return result


# ================= GET ALL PIPELINE HISTORY =================

@router.get("/pipeline/history")
async def get_pipeline_history(
    limit: int = Query(default=100, ge=1, le=500)
):
    connection = get_db_connection()

    try:
        rows = connection.execute("""
            SELECT *
            FROM pipeline_runs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()

        history = [
            serialize_pipeline_run(row)
            for row in rows
        ]

        return {
            "total_runs": len(history),
            "history": history
        }
    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve pipeline history."
        )
    finally:
        connection.close()


# ================= GET INDIVIDUAL PIPELINE RUN =================

@router.get("/pipeline/history/{run_id}")
async def get_pipeline_run_details(run_id: str):
    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid pipeline run ID."
        )

    connection = get_db_connection()

    try:
        row = connection.execute("""
            SELECT *
            FROM pipeline_runs
            WHERE run_id = ?
        """, (run_id,)).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Pipeline run not found."
            )

        return serialize_pipeline_run(row, include_previews=True)

    except sqlite3.Error:
        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve pipeline run details."
        )
    finally:
        connection.close()


# ================= DOWNLOAD PIPELINE REPORTS =================

@router.get("/pipeline/report/{run_id}/{report_type}")
async def download_pipeline_report(run_id: str, report_type: str):

    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid pipeline run ID."
        )

    if report_type not in ("valid", "rejected"):
        raise HTTPException(
            status_code=400,
            detail="Invalid report type."
        )

    report_path = REPORT_DIR / f"{run_id}_{report_type}.csv"

    if not report_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Report not found."
        )

    return FileResponse(
        path=report_path,
        media_type="text/csv",
        filename=f"{report_type}_records_{run_id[:8]}.csv"
    )
