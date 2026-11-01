
from src.generate_data import generate_all
from src.config import RAW_DIR, DATA_SCALE
import csv


def read_csv(filename):
    with open(RAW_DIR / filename, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_required_record_counts():
    generate_all()

    suppliers = read_csv("suppliers.csv")
    orders = read_csv("purchase_orders.csv")
    shipments = read_csv("shipments.csv")
    inspections = read_csv("inspections.csv")

    assert len(suppliers) == DATA_SCALE["suppliers"]
    assert len(orders) == DATA_SCALE["purchase_orders"]
    assert len(shipments) >= DATA_SCALE["shipments"]
    assert len(inspections) == DATA_SCALE["inspections"]


def test_supplier_ids_are_unique():
    suppliers = read_csv("suppliers.csv")
    ids = [row["supplier_id"] for row in suppliers]

    assert len(ids) == len(set(ids))


def test_purchase_order_ids_are_unique():
    orders = read_csv("purchase_orders.csv")
    ids = [row["po_id"] for row in orders]

    assert len(ids) == len(set(ids))
