
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    RAW_DIR,
    PROCESSED_DIR,
    REPORTS_DIR,
    SCORING_WEIGHTS,
)


HISTORY_FILE = "supplier_score_history.csv"
CURRENT_FILE = "supplier_scores.csv"


def read_csv_from(directory, filename):
    path = directory / filename

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def read_csv(filename):
    return read_csv_from(RAW_DIR, filename)


def write_csv(filename, rows):
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    if not rows:
        return

    path = PROCESSED_DIR / filename

    with open(path, "w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_number(value):
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_delivery_scores(shipments):
    supplier_data = defaultdict(lambda: {"eligible": 0, "on_time": 0})
    invalid_count = 0

    for shipment in shipments:
        if shipment.get("status") != "DELIVERED":
            continue

        supplier_id = shipment.get("supplier_id")
        dispatch = shipment.get("dispatch_date")
        expected = shipment.get("expected_delivery_date")
        actual = shipment.get("actual_delivery_date")

        if not supplier_id or not dispatch or not expected or not actual:
            continue

        if actual < dispatch:
            invalid_count += 1
            continue

        supplier_data[supplier_id]["eligible"] += 1

        if actual <= expected:
            supplier_data[supplier_id]["on_time"] += 1

    scores = {}

    for supplier_id, data in supplier_data.items():
        scores[supplier_id] = (
            data["on_time"] / data["eligible"] * 100
            if data["eligible"] else None
        )

    return scores, invalid_count


def calculate_quality_scores(inspections):
    supplier_data = defaultdict(
        lambda: {"accepted": 0.0, "inspected": 0.0}
    )

    invalid_count = 0

    for inspection in inspections:
        inspected = safe_number(inspection.get("inspected_quantity"))
        accepted = safe_number(inspection.get("accepted_quantity"))
        rejected = safe_number(inspection.get("rejected_quantity"))
        supplier_id = inspection.get("supplier_id")

        if (
            not supplier_id
            or inspected is None
            or accepted is None
            or rejected is None
            or inspected <= 0
            or accepted < 0
            or rejected < 0
            or abs(inspected - accepted - rejected) > 0.001
        ):
            invalid_count += 1
            continue

        supplier_data[supplier_id]["accepted"] += accepted
        supplier_data[supplier_id]["inspected"] += inspected

    scores = {}

    for supplier_id, data in supplier_data.items():
        scores[supplier_id] = (
            data["accepted"] / data["inspected"] * 100
            if data["inspected"] > 0 else None
        )

    return scores, invalid_count


def calculate_cost_scores(orders, invoices):
    orders_by_id = {
        order["po_id"]: order
        for order in orders
        if order.get("po_id")
    }

    invoice_totals = defaultdict(float)
    invalid_count = 0

    for invoice in invoices:
        if invoice.get("status") != "VERIFIED":
            continue

        po_id = invoice.get("po_id")
        order = orders_by_id.get(po_id)

        if not order:
            invalid_count += 1
            continue

        if (
            invoice.get("supplier_id") != order.get("supplier_id")
            or invoice.get("currency") != order.get("currency")
        ):
            invalid_count += 1
            continue

        amount = safe_number(invoice.get("invoice_amount"))

        if amount is None or amount < 0:
            invalid_count += 1
            continue

        invoice_totals[po_id] += amount

    supplier_data = defaultdict(
        lambda: {"po_amount": 0.0, "variance": 0.0}
    )

    for po_id, invoice_amount in invoice_totals.items():
        order = orders_by_id[po_id]
        po_amount = safe_number(order.get("total_amount"))

        if po_amount is None or po_amount <= 0:
            invalid_count += 1
            continue

        supplier_id = order["supplier_id"]

        supplier_data[supplier_id]["po_amount"] += po_amount
        supplier_data[supplier_id]["variance"] += abs(
            invoice_amount - po_amount
        )

    scores = {}

    for supplier_id, data in supplier_data.items():
        variance_percentage = (
            data["variance"] / data["po_amount"] * 100
        )

        scores[supplier_id] = max(
            0.0,
            min(100.0, 100.0 - variance_percentage)
        )

    return scores, invalid_count


def calculate_capacity_scores(suppliers, orders, po_lines):
    supplier_capacity = {}

    for supplier in suppliers:
        capacity = safe_number(
            supplier.get("monthly_capacity_units")
        )

        if capacity is not None and capacity > 0:
            supplier_capacity[supplier["supplier_id"]] = capacity

    po_quantities = defaultdict(float)

    for line in po_lines:
        quantity = safe_number(line.get("ordered_quantity"))

        if quantity is not None and quantity > 0:
            po_quantities[line.get("po_id")] += quantity

    monthly_load = defaultdict(float)

    for order in orders:
        supplier_id = order.get("supplier_id")
        order_date = order.get("order_date")
        po_id = order.get("po_id")

        if not supplier_id or not order_date:
            continue

        month = order_date[:7]
        quantity = po_quantities.get(po_id, 0)

        if quantity > 0:
            monthly_load[(supplier_id, month)] += quantity

    supplier_month_scores = defaultdict(list)

    for (supplier_id, month), quantity in monthly_load.items():
        capacity = supplier_capacity.get(supplier_id)

        if capacity is None:
            continue

        utilization_percentage = quantity / capacity * 100

        score = max(
            0.0,
            min(100.0, 200.0 - utilization_percentage)
        )

        supplier_month_scores[supplier_id].append(score)

    scores = {}

    for supplier_id, monthly_scores in supplier_month_scores.items():
        scores[supplier_id] = (
            sum(monthly_scores) / len(monthly_scores)
        )

    return scores


def calculate_compliance_scores(contracts):
    status_scores = {
        "COMPLIANT": 100.0,
        "PENDING": 50.0,
        "NON_COMPLIANT": 0.0,
    }

    supplier_data = defaultdict(list)

    for contract in contracts:
        supplier_id = contract.get("supplier_id")
        status = contract.get("compliance_status")

        if supplier_id and status in status_scores:
            supplier_data[supplier_id].append(status_scores[status])

    return {
        supplier_id: sum(values) / len(values)
        for supplier_id, values in supplier_data.items()
    }


def calculate_disruption_scores(risk_signals):
    severity_penalties = {
        "LOW": 10.0,
        "MEDIUM": 30.0,
        "HIGH": 60.0,
        "CRITICAL": 90.0,
    }

    supplier_data = defaultdict(list)
    invalid_count = 0

    for signal in risk_signals:
        supplier_id = signal.get("supplier_id")
        source = signal.get("source")
        observed_at = signal.get("observed_at")
        severity = signal.get("severity")

        if (
            not supplier_id
            or not source
            or not observed_at
            or severity not in severity_penalties
        ):
            invalid_count += 1
            continue

        supplier_data[supplier_id].append(
            severity_penalties[severity]
        )

    scores = {}

    for supplier_id, penalties in supplier_data.items():
        average_penalty = sum(penalties) / len(penalties)
        scores[supplier_id] = max(
            0.0,
            100.0 - average_penalty
        )

    return scores, invalid_count


def get_data_as_of_date(data_sources):
    dates = []

    date_fields = {
        "purchase_orders": ["order_date"],
        "shipments": ["dispatch_date", "actual_delivery_date"],
        "inspections": ["inspection_date"],
        "invoices": ["invoice_date"],
        "risk_signals": ["observed_at"],
    }

    for source_name, fields in date_fields.items():
        for row in data_sources.get(source_name, []):
            for field in fields:
                value = row.get(field)

                if not value:
                    continue

                date_value = str(value)[:10]

                try:
                    datetime.strptime(date_value, "%Y-%m-%d")
                    dates.append(date_value)
                except ValueError:
                    continue

    return max(dates) if dates else datetime.now(
        timezone.utc
    ).date().isoformat()


def load_existing_history():
    return read_csv_from(PROCESSED_DIR, HISTORY_FILE)


def create_score_history(current_rows, scoring_period, data_as_of_date):
    old_history = load_existing_history()

    history_by_supplier_period = {}

    for row in old_history:
        key = (
            row.get("supplier_id"),
            row.get("scoring_period"),
        )
        history_by_supplier_period[key] = row

    year = scoring_period[:4]

    existing_numbers = []

    for row in old_history:
        score_id = row.get("score_id", "")

        if score_id.startswith(f"SCORE-{year}-"):
            try:
                existing_numbers.append(
                    int(score_id.split("-")[-1])
                )
            except ValueError:
                continue

    next_number = max(existing_numbers, default=0) + 1

    generated_at = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )

    new_snapshot = []

    for row in sorted(current_rows, key=lambda x: x["supplier_id"]):
        key = (row["supplier_id"], scoring_period)
        previous = history_by_supplier_period.get(key)

        if previous:
            score_id = previous["score_id"]
            score_generated_at = previous["score_generated_at"]
        else:
            score_id = f"SCORE-{year}-{next_number:06d}"
            score_generated_at = generated_at
            next_number += 1

        history_row = {
            "score_id": score_id,
            "supplier_id": row["supplier_id"],
            "scoring_period": scoring_period,
            "data_as_of_date": data_as_of_date,
            "score_generated_at": score_generated_at,
            "delivery_score": row["delivery_score"],
            "quality_score": row["quality_score"],
            "cost_score": row["cost_score"],
            "capacity_score": row["capacity_score"],
            "compliance_score": row["compliance_score"],
            "disruption_score": row["disruption_score"],
            "data_coverage": row["data_coverage"],
            "final_score": row["final_score"],
            "rating": row["rating"],
        }

        new_snapshot.append(history_row)

    # Preserve previous scoring periods and replace the current period.
    current_keys = {
        (row["supplier_id"], scoring_period)
        for row in new_snapshot
    }

    preserved_history = [
        row for row in old_history
        if (
            row.get("supplier_id"),
            row.get("scoring_period"),
        ) not in current_keys
    ]

    complete_history = preserved_history + new_snapshot

    complete_history.sort(
        key=lambda row: (
            row.get("scoring_period", ""),
            row.get("supplier_id", ""),
        )
    )

    write_csv(HISTORY_FILE, complete_history)

    # Current snapshot remains compatible with evaluation.py.
    write_csv(CURRENT_FILE, new_snapshot)

    return new_snapshot, complete_history


def calculate_supplier_scores():
    suppliers = read_csv("suppliers.csv")
    orders = read_csv("purchase_orders.csv")
    po_lines = read_csv("po_lines.csv")
    shipments = read_csv("shipments.csv")
    inspections = read_csv("inspections.csv")
    invoices = read_csv("invoices.csv")
    contracts = read_csv("contracts.csv")
    risk_signals = read_csv("risk_signals.csv")

    delivery_scores, invalid_deliveries = calculate_delivery_scores(
        shipments
    )

    quality_scores, invalid_inspections = calculate_quality_scores(
        inspections
    )

    cost_scores, invalid_invoices = calculate_cost_scores(
        orders, invoices
    )

    capacity_scores = calculate_capacity_scores(
        suppliers, orders, po_lines
    )

    compliance_scores = calculate_compliance_scores(contracts)

    disruption_scores, invalid_risks = calculate_disruption_scores(
        risk_signals
    )

    metric_scores = {
        "delivery": delivery_scores,
        "quality": quality_scores,
        "cost": cost_scores,
        "capacity": capacity_scores,
        "compliance": compliance_scores,
        "disruption": disruption_scores,
    }

    current_rows = []

    for supplier in suppliers:
        supplier_id = supplier["supplier_id"]

        available_metrics = {}
        available_weight = 0.0
        weighted_total = 0.0

        for metric, scores in metric_scores.items():
            score = scores.get(supplier_id)

            if score is None:
                continue

            weight = SCORING_WEIGHTS[metric]
            available_metrics[metric] = round(score, 2)
            weighted_total += score * weight
            available_weight += weight

        if available_weight > 0:
            final_score = weighted_total / available_weight
            data_coverage = available_weight * 100
        else:
            final_score = None
            data_coverage = 0.0

        if final_score is None:
            rating = "INSUFFICIENT_DATA"
        elif final_score >= 85:
            rating = "EXCELLENT"
        elif final_score >= 70:
            rating = "GOOD"
        elif final_score >= 50:
            rating = "MODERATE"
        else:
            rating = "POOR"

        current_rows.append({
            "supplier_id": supplier_id,
            "delivery_score": available_metrics.get("delivery", ""),
            "quality_score": available_metrics.get("quality", ""),
            "cost_score": available_metrics.get("cost", ""),
            "capacity_score": available_metrics.get("capacity", ""),
            "compliance_score": available_metrics.get("compliance", ""),
            "disruption_score": available_metrics.get("disruption", ""),
            "data_coverage": round(data_coverage, 2),
            "final_score": (
                round(final_score, 2)
                if final_score is not None else ""
            ),
            "rating": rating,
        })

    data_sources = {
        "purchase_orders": orders,
        "shipments": shipments,
        "inspections": inspections,
        "invoices": invoices,
        "risk_signals": risk_signals,
    }

    data_as_of_date = get_data_as_of_date(data_sources)
    scoring_period = data_as_of_date[:7]

    snapshot, history = create_score_history(
        current_rows,
        scoring_period,
        data_as_of_date,
    )

    scored = [
        row for row in snapshot
        if row["final_score"] != ""
    ]

    average_score = (
        sum(float(row["final_score"]) for row in scored) / len(scored)
        if scored else 0.0
    )

    summary = {
        "supplier_count": len(suppliers),
        "scored_suppliers": len(scored),
        "insufficient_data": len(suppliers) - len(scored),
        "average_score": round(average_score, 2),
        "scoring_period": scoring_period,
        "data_as_of_date": data_as_of_date,
        "score_history_records": len(history),
        "invalid_records_excluded": {
            "delivery_records": invalid_deliveries,
            "inspection_records": invalid_inspections,
            "invoice_records": invalid_invoices,
            "risk_signal_records": invalid_risks,
        },
        "scoring_weights": SCORING_WEIGHTS,
        "notes": [
            "Missing metrics are excluded and weights are renormalized.",
            "Cost compares verified invoices with matching PO amounts and currency.",
            "Capacity uses monthly PO-line quantities compared with monthly supplier capacity.",
            "Invalid delivery dates and risk signals are excluded.",
            "Ground-truth anomaly labels are not used as scoring features.",
            "Score history is stored separately from the current supplier snapshot.",
            "Repeated scoring for the same supplier and period reuses its score ID.",
        ],
    }

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        REPORTS_DIR / "scoring_summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    calculate_supplier_scores()
