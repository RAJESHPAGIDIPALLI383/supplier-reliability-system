from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RANDOM_SEED = 20261022

DATA_SCALE = {
    "suppliers": 1000,
    "purchase_orders": 10000,
    "shipments": 15000,
    "inspections": 20000,
}

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"

DATABASE_DIR = PROJECT_ROOT / "database"
REPORTS_DIR = PROJECT_ROOT / "reports"

SUPPLIER_ID_PREFIX = "SUP"
PO_ID_PREFIX = "PO"
SHIPMENT_ID_PREFIX = "SHP"
RISK_ID_PREFIX = "RSK"
SCORE_ID_PREFIX = "SCORE"

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

SCORING_WEIGHTS = {
    "delivery": 0.30,
    "quality": 0.25,
    "cost": 0.15,
    "capacity": 0.10,
    "compliance": 0.10,
    "disruption": 0.10,
}

assert sum(SCORING_WEIGHTS.values()) == 1.0