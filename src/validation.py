
import csv
import json
from pathlib import Path

from src.config import RAW_DIR, GROUND_TRUTH_DIR


EXPECTED_ANOMALIES = {
    "Delivery date must not precede dispatch": [
        "SHP-2026-ANOM002"
    ],
    "Supplier site conflation": [
        "SITE-SUP-000001-01"
    ],
    "Risk signal source and timestamp": [
        "RSK-SUP-000001-2026-01"
    ],
    "Shipment purchase order relationship": [
        "SHP-2026-ANOM001"
    ],
    "Supplier score future data leakage": [
        "SCORE-2026-ANOM003"
    ],
}


def read_csv(filename):
    path = RAW_DIR / filename

    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def read_json(filename):
    path = GROUND_TRUTH_DIR / filename

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_primary_key(rows, key, table_name):
    values = [row[key] for row in rows]
    duplicates = len(values) - len(set(values))

    return {
        "check": f"{table_name} primary key uniqueness",
        "passed": duplicates == 0,
        "duplicate_count": duplicates,
    }


def check_foreign_keys(child_rows, parent_ids, key, table_name):
    invalid = [
        row[key]
        for row in child_rows
        if row.get(key) and row[key] not in parent_ids
    ]

    return {
        "check": f"{table_name} foreign key integrity",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_values": invalid[:10],
    }


def check_inspection_quantities(inspections):
    invalid = []

    for row in inspections:
        inspected = int(row["inspected_quantity"])
        accepted = int(row["accepted_quantity"])
        rejected = int(row["rejected_quantity"])

        if accepted + rejected != inspected:
            invalid.append(row["inspection_id"])

    return {
        "check": "Inspection quantity reconciliation",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
    }


def check_delivery_dates(shipments):
    invalid = []

    for row in shipments:
        dispatch = row.get("dispatch_date")
        delivery = row.get("actual_delivery_date")

        if dispatch and delivery and delivery < dispatch:
            invalid.append(row["shipment_id"])

    return {
        "check": "Delivery date must not precede dispatch",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid,
    }


def check_supplier_site_relationship(orders, sites):
    site_lookup = {
        row["site_id"]: row["supplier_id"]
        for row in sites
    }

    invalid = []

    for order in orders:
        site_id = order["site_id"]
        supplier_id = order["supplier_id"]

        if site_lookup.get(site_id) != supplier_id:
            invalid.append(order["po_id"])

    return {
        "check": "Supplier site relationship",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid[:10],
    }


def check_site_anomaly():
    anomaly_sites = read_csv("site_anomaly_records.csv")
    suppliers = read_csv("suppliers.csv")
    sites = read_csv("sites.csv")

    supplier_ids = {
        row["supplier_id"] for row in suppliers
    }

    site_lookup = {
        row["site_id"]: row["supplier_id"]
        for row in sites
    }

    invalid = []

    for row in anomaly_sites:
        site_id = row["site_id"]
        supplier_id = row["supplier_id"]

        if supplier_id not in supplier_ids:
            invalid.append(site_id)

        elif site_lookup.get(site_id) != supplier_id:
            invalid.append(site_id)

    return {
        "check": "Supplier site conflation",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid,
    }


def check_risk_signals(risks):
    invalid = []

    for risk in risks:
        if not risk.get("source") or not risk.get("observed_at"):
            invalid.append(risk["risk_signal_id"])

    return {
        "check": "Risk signal source and timestamp",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid,
    }


def check_shipment_relationship(shipments, orders):
    order_ids = {
        order["po_id"] for order in orders
    }

    invalid = [
        shipment["shipment_id"]
        for shipment in shipments
        if shipment["po_id"] not in order_ids
    ]

    return {
        "check": "Shipment purchase order relationship",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid,
    }


def check_future_score(scores):
    invalid = []

    for score in scores:
        if score["source_data_max_date"] > score["as_of_date"]:
            invalid.append(score["score_id"])

    return {
        "check": "Supplier score future data leakage",
        "passed": len(invalid) == 0,
        "invalid_count": len(invalid),
        "invalid_records": invalid,
    }


def classify_results(results):
    expected_detected = 0
    unexpected_failures = 0

    for result in results:
        check_name = result["check"]

        if result["passed"]:
            result["classification"] = "PASSED"
            continue

        expected_ids = EXPECTED_ANOMALIES.get(check_name, [])
        actual_ids = result.get("invalid_records", [])

        if (
            expected_ids
            and set(actual_ids) == set(expected_ids)
        ):
            result["classification"] = "EXPECTED_ANOMALY_DETECTED"
            result["expected_anomaly"] = True
            expected_detected += 1

        else:
            result["classification"] = "UNEXPECTED_FAILURE"
            result["expected_anomaly"] = False
            unexpected_failures += 1

    return expected_detected, unexpected_failures


def run_validation():
    suppliers = read_csv("suppliers.csv")
    sites = read_csv("sites.csv")
    orders = read_csv("purchase_orders.csv")
    lines = read_csv("po_lines.csv")
    shipments = read_csv("shipments.csv")
    shipment_lines = read_csv("shipment_lines.csv")
    events = read_csv("delivery_events.csv")
    inspections = read_csv("inspections.csv")
    invoices = read_csv("invoices.csv")
    risks = read_csv("risk_signals.csv")

    future_scores = read_json("future_score_anomaly.json")

    results = []

    # Primary key checks
    results.append(
        check_primary_key(suppliers, "supplier_id", "Suppliers")
    )
    results.append(
        check_primary_key(sites, "site_id", "Sites")
    )
    results.append(
        check_primary_key(orders, "po_id", "PurchaseOrders")
    )
    results.append(
        check_primary_key(lines, "po_line_id", "POLines")
    )
    results.append(
        check_primary_key(shipments, "shipment_id", "Shipments")
    )
    results.append(
        check_primary_key(
            shipment_lines, "shipment_line_id", "ShipmentLine"
        )
    )
    results.append(
        check_primary_key(
            inspections, "inspection_id", "Inspections"
        )
    )
    results.append(
        check_primary_key(invoices, "invoice_id", "Invoices")
    )
    results.append(
        check_primary_key(
            risks, "risk_signal_id", "RiskSignals"
        )
    )

    # Foreign key checks
    supplier_ids = {
        row["supplier_id"] for row in suppliers
    }
    site_ids = {
        row["site_id"] for row in sites
    }
    order_ids = {
        row["po_id"] for row in orders
    }
    line_ids = {
        row["po_line_id"] for row in lines
    }
    shipment_ids = {
        row["shipment_id"] for row in shipments
    }

    results.append(
        check_foreign_keys(
            sites, supplier_ids, "supplier_id", "Sites"
        )
    )
    results.append(
        check_foreign_keys(
            orders, supplier_ids, "supplier_id", "PurchaseOrders"
        )
    )
    results.append(
        check_foreign_keys(
            orders, site_ids, "site_id", "PurchaseOrders"
        )
    )
    results.append(
        check_foreign_keys(
            lines, order_ids, "po_id", "POLines"
        )
    )
    results.append(
        check_foreign_keys(
            shipment_lines, shipment_ids,
            "shipment_id", "ShipmentLine"
        )
    )
    results.append(
        check_foreign_keys(
            shipment_lines, line_ids,
            "po_line_id", "ShipmentLine"
        )
    )
    results.append(
        check_foreign_keys(
            events, shipment_ids,
            "shipment_id", "DeliveryEvents"
        )
    )
    results.append(
        check_foreign_keys(
            inspections, shipment_ids,
            "shipment_id", "Inspections"
        )
    )
    results.append(
        check_foreign_keys(
            inspections, line_ids,
            "po_line_id", "Inspections"
        )
    )

    # Business validation checks
    results.append(
        check_inspection_quantities(inspections)
    )
    results.append(
        check_delivery_dates(shipments)
    )
    results.append(
        check_supplier_site_relationship(orders, sites)
    )
    results.append(
        check_site_anomaly()
    )
    results.append(
        check_risk_signals(risks)
    )
    results.append(
        check_shipment_relationship(shipments, orders)
    )
    results.append(
        check_future_score(future_scores)
    )

    expected_detected, unexpected_failures = classify_results(
        results
    )

    passed_checks = sum(
        result["passed"] for result in results
    )

    failed_checks = sum(
        not result["passed"] for result in results
    )

    report = {
        "total_checks": len(results),
        "passed_checks": passed_checks,
        "failed_checks": failed_checks,
        "expected_anomalies_detected": expected_detected,
        "unexpected_failures": unexpected_failures,
        "validation_status": (
            "PASSED"
            if unexpected_failures == 0
            and expected_detected == len(EXPECTED_ANOMALIES)
            else "REVIEW_REQUIRED"
        ),
        "results": results,
    }

    report_path = Path("reports") / "validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print(json.dumps(report, indent=4))

    return report


if __name__ == "__main__":
    run_validation()
