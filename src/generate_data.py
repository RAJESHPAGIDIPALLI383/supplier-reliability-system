import csv
import json
import random
from datetime import date, datetime, timedelta

from src.config import (
    RANDOM_SEED,
    DATA_SCALE,
    RAW_DIR,
    GROUND_TRUTH_DIR,
)

rng = random.Random(RANDOM_SEED)

BASE_DATE = date(2026, 10, 22)


def random_date(start, end):
    days = (end - start).days
    return start + timedelta(days=rng.randint(0, max(days, 0)))


def write_csv(filename, rows):
    if not rows:
        return

    path = RAW_DIR / filename

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_suppliers(count):
    suppliers = []
    sites = []
    contracts = []

    for i in range(1, count + 1):
        supplier_id = f"SUP-{i:06d}"

        suppliers.append({
            "supplier_id": supplier_id,
            "supplier_name": f"Supplier {i:06d}",
            "country": rng.choice(["India", "USA", "Germany", "Japan"]),
            "category": rng.choice([
                "Electronics",
                "Raw Materials",
                "Packaging"
            ]),
            "registration_date": random_date(
                date(2018, 1, 1),
                date(2025, 12, 31)
            ).isoformat(),
            "monthly_capacity_units": rng.randint(500, 10000),
            "status": rng.choices(
                ["ACTIVE", "INACTIVE", "SUSPENDED"],
                weights=[90, 7, 3]
            )[0],
        })

        site_count = rng.randint(1, 3)

        for j in range(1, site_count + 1):
            sites.append({
                "site_id": f"SITE-{supplier_id}-{j:02d}",
                "supplier_id": supplier_id,
                "site_name": f"{supplier_id} Site {j}",
                "city": rng.choice([
                    "Hyderabad",
                    "Mumbai",
                    "Delhi",
                    "Pune"
                ]),
                "country": "India",
                "effective_from": "2020-01-01",
                "effective_to": "",
                "status": "ACTIVE",
            })

        contracts.append({
            "contract_id": f"CON-{i:06d}",
            "supplier_id": supplier_id,
            "contract_start_date": "2026-01-01",
            "contract_end_date": "2027-12-31",
            "contract_value": round(
                rng.uniform(100000, 5000000), 2
            ),
            "currency": "INR",
            "compliance_status": rng.choice([
                "COMPLIANT",
                "NON_COMPLIANT",
                "PENDING"
            ]),
            "status": "ACTIVE",
        })

    return suppliers, sites, contracts


def generate_orders(suppliers, sites, contracts, count):
    orders = []
    lines = []

    site_lookup = {}

    for site in sites:
        site_lookup.setdefault(
            site["supplier_id"], []
        ).append(site)

    contract_lookup = {
        contract["supplier_id"]: contract["contract_id"]
        for contract in contracts
    }

    for i in range(1, count + 1):
        supplier = rng.choice(suppliers)
        supplier_id = supplier["supplier_id"]

        order_date = random_date(
            date(2026, 1, 1),
            date(2026, 10, 1)
        )

        required_date = order_date + timedelta(
            days=rng.randint(7, 45)
        )

        quantity = rng.randint(50, 1000)
        price = round(rng.uniform(10, 5000), 2)

        po_id = f"PO-2026-{i:06d}"
        site = rng.choice(site_lookup[supplier_id])

        orders.append({
            "po_id": po_id,
            "supplier_id": supplier_id,
            "site_id": site["site_id"],
            "contract_id": contract_lookup[supplier_id],
            "order_date": order_date.isoformat(),
            "required_date": required_date.isoformat(),
            "currency": "INR",
            "total_amount": round(quantity * price, 2),
            "status": rng.choice([
                "APPROVED",
                "PARTIALLY_DELIVERED",
                "COMPLETED"
            ]),
        })

        lines.append({
            "po_line_id": f"POL-{i:07d}",
            "po_id": po_id,
            "item_code": f"ITEM-{rng.randint(1, 100):03d}",
            "ordered_quantity": quantity,
            "unit_price": price,
            "line_amount": round(quantity * price, 2),
        })

    return orders, lines


def generate_shipments(orders, lines, count):
    shipments = []
    shipment_lines = []
    events = []
    anomalies = []

    line_lookup = {
        line["po_id"]: line
        for line in lines
    }

    for i in range(1, count + 1):
        order = rng.choice(orders)
        po_id = order["po_id"]

        dispatch = date.fromisoformat(
            order["order_date"]
        ) + timedelta(days=rng.randint(1, 5))

        expected = date.fromisoformat(
            order["required_date"]
        )

        actual = dispatch + timedelta(
            days=rng.randint(1, 25)
        )

        shipment_id = f"SHP-2026-{i:06d}"

        shipments.append({
            "shipment_id": shipment_id,
            "supplier_id": order["supplier_id"],
            "po_id": po_id,
            "dispatch_date": dispatch.isoformat(),
            "expected_delivery_date": expected.isoformat(),
            "actual_delivery_date": actual.isoformat(),
            "carrier_name": rng.choice([
                "DHL",
                "FedEx",
                "BlueDart"
            ]),
            "status": "DELIVERED",
        })

        line = line_lookup[po_id]

        shipment_lines.append({
            "shipment_line_id": f"SL-{i:07d}",
            "shipment_id": shipment_id,
            "po_line_id": line["po_line_id"],
            "shipped_quantity": line["ordered_quantity"],
        })

        events.append({
            "delivery_event_id": f"DEV-{i:07d}",
            "shipment_id": shipment_id,
            "event_type": "DISPATCHED",
            "event_timestamp": dispatch.isoformat() + "T09:00:00",
            "location": "Origin",
            "source": "Carrier API",
        })

        events.append({
            "delivery_event_id": f"DEV-{i:07d}-2",
            "shipment_id": shipment_id,
            "event_type": "DELIVERED",
            "event_timestamp": actual.isoformat() + "T17:00:00",
            "location": "Destination",
            "source": "Carrier API",
        })

    # Anomaly 1: Shipment without a valid purchase order
    shipments.append({
        "shipment_id": "SHP-2026-ANOM001",
        "supplier_id": orders[0]["supplier_id"],
        "po_id": "PO-INVALID-999999",
        "dispatch_date": "2026-10-10",
        "expected_delivery_date": "2026-10-15",
        "actual_delivery_date": "2026-10-16",
        "carrier_name": "Unknown",
        "status": "DELIVERED",
    })

    anomalies.append({
        "anomaly_id": "ANOM-001",
        "record_id": "SHP-2026-ANOM001",
        "anomaly_type": "SHIPMENT_WITHOUT_PO",
        "expected_detection": "Shipment references a nonexistent purchase order",
    })

    # Anomaly 2: Delivery date before dispatch date
    shipments.append({
        "shipment_id": "SHP-2026-ANOM002",
        "supplier_id": orders[1]["supplier_id"],
        "po_id": orders[1]["po_id"],
        "dispatch_date": "2026-10-20",
        "expected_delivery_date": "2026-10-25",
        "actual_delivery_date": "2026-10-18",
        "carrier_name": "Unknown",
        "status": "DELIVERED",
    })

    anomalies.append({
        "anomaly_id": "ANOM-002",
        "record_id": "SHP-2026-ANOM002",
        "anomaly_type": "DELIVERY_BEFORE_DISPATCH",
        "expected_detection": "Actual delivery date is earlier than dispatch date",
    })

    return shipments, shipment_lines, events, anomalies


def generate_inspections(shipments, lines, count):
    inspections = []

    valid_shipments = [
        shipment for shipment in shipments
        if shipment["shipment_id"] not in [
            "SHP-2026-ANOM001",
            "SHP-2026-ANOM002"
        ]
    ]

    line_lookup = {
        line["po_id"]: line
        for line in lines
    }

    for i in range(1, count + 1):
        shipment = rng.choice(valid_shipments)

        inspected = rng.randint(10, 500)
        rejected = rng.randint(0, min(20, inspected))
        accepted = inspected - rejected

        line = line_lookup[shipment["po_id"]]

        inspections.append({
            "inspection_id": f"INS-{i:07d}",
            "supplier_id": shipment["supplier_id"],
            "shipment_id": shipment["shipment_id"],
            "po_line_id": line["po_line_id"],
            "inspection_date": shipment["actual_delivery_date"],
            "inspected_quantity": inspected,
            "accepted_quantity": accepted,
            "rejected_quantity": rejected,
            "defect_category": (
                "NONE" if rejected == 0 else "GENERAL"
            ),
            "status": "PASSED" if rejected == 0 else "PARTIAL",
        })

    return inspections


def generate_invoices(orders):
    invoices = []

    for i, order in enumerate(orders, start=1):
        invoices.append({
            "invoice_id": f"INV-{i:07d}",
            "supplier_id": order["supplier_id"],
            "po_id": order["po_id"],
            "invoice_date": order["order_date"],
            "invoice_amount": order["total_amount"],
            "currency": order["currency"],
            "status": "VERIFIED",
        })

    return invoices


def generate_risk_signals(suppliers):
    risks = []
    anomalies = []

    for supplier in suppliers:
        risks.append({
            "risk_signal_id": (
                f"RSK-{supplier['supplier_id']}-2026-01"
            ),
            "supplier_id": supplier["supplier_id"],
            "site_id": "",
            "risk_type": rng.choice([
                "FINANCIAL",
                "OPERATIONAL",
                "WEATHER",
                "COMPLIANCE"
            ]),
            "severity": rng.choice([
                "LOW",
                "MEDIUM",
                "HIGH"
            ]),
            "source": "Supplier Monitoring",
            "observed_at": "2026-10-20T10:00:00",
            "status": "OPEN",
        })

    # Anomaly 4: Missing risk signal source and timestamp
    risks[0]["source"] = ""
    risks[0]["observed_at"] = ""

    anomalies.append({
        "anomaly_id": "ANOM-004",
        "record_id": risks[0]["risk_signal_id"],
        "anomaly_type": "RISK_SIGNAL_MISSING_SOURCE_OR_TIME",
        "expected_detection": "Risk signal has missing source and timestamp",
    })

    return risks, anomalies


def generate_site_anomaly(sites, suppliers):
    wrong_site = dict(sites[0])
    wrong_site["supplier_id"] = suppliers[1]["supplier_id"]

    anomalies = [{
        "anomaly_id": "ANOM-005",
        "record_id": wrong_site["site_id"],
        "anomaly_type": "SUPPLIER_SITE_CONFLATION",
        "expected_detection": "Site is associated with the wrong supplier",
    }]

    return [wrong_site], anomalies


def generate_future_score_anomaly(suppliers):
    scores = [{
        "score_id": "SCORE-2026-ANOM003",
        "supplier_id": suppliers[0]["supplier_id"],
        "as_of_date": "2026-10-01",
        "computed_at": "2026-10-22T12:00:00",
        "source_data_max_date": "2026-10-15",
        "overall_score": 95.0,
    }]

    anomalies = [{
        "anomaly_id": "ANOM-003",
        "record_id": "SCORE-2026-ANOM003",
        "anomaly_type": "FUTURE_DATA_LEAKAGE",
        "expected_detection": "Score includes source data after its as-of date",
    }]

    return scores, anomalies


def save_json(filename, data):
    path = GROUND_TRUTH_DIR / filename

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def generate_all():
    global rng

    # Reset RNG on every run to guarantee reproducible data.
    rng = random.Random(RANDOM_SEED)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

    suppliers, sites, contracts = generate_suppliers(
        DATA_SCALE["suppliers"]
    )

    orders, lines = generate_orders(
        suppliers,
        sites,
        contracts,
        DATA_SCALE["purchase_orders"]
    )

    shipments, shipment_lines, events, shipment_anomalies = (
        generate_shipments(
            orders,
            lines,
            DATA_SCALE["shipments"]
        )
    )

    inspections = generate_inspections(
        shipments,
        lines,
        DATA_SCALE["inspections"]
    )

    invoices = generate_invoices(orders)

    risks, risk_anomalies = generate_risk_signals(
        suppliers
    )

    site_anomaly_data, site_anomalies = generate_site_anomaly(
        sites,
        suppliers
    )

    future_scores, future_anomalies = generate_future_score_anomaly(
        suppliers
    )

    datasets = {
        "suppliers.csv": suppliers,
        "sites.csv": sites,
        "contracts.csv": contracts,
        "purchase_orders.csv": orders,
        "po_lines.csv": lines,
        "shipments.csv": shipments,
        "shipment_lines.csv": shipment_lines,
        "delivery_events.csv": events,
        "inspections.csv": inspections,
        "invoices.csv": invoices,
        "risk_signals.csv": risks,
        "site_anomaly_records.csv": site_anomaly_data,
    }

    for filename, rows in datasets.items():
        write_csv(filename, rows)

    save_json(
        "future_score_anomaly.json",
        future_scores
    )

    all_anomalies = (
        shipment_anomalies
        + risk_anomalies
        + site_anomalies
        + future_anomalies
    )

    save_json(
        "ground_truth.json",
        all_anomalies
    )

    summary = {
        "seed": RANDOM_SEED,
        "generated_at": datetime.now().isoformat(),
        "row_counts": {
            filename: len(rows)
            for filename, rows in datasets.items()
        },
        "anomaly_count": len(all_anomalies),
    }

    with (RAW_DIR / "generation_summary.json").open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=4)

    print("Supplier Reliability data generation completed.")
    print(json.dumps(summary, indent=4))


if __name__ == "__main__":
    generate_all()