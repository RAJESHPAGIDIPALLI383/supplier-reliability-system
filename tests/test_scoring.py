
from src.scoring import (
    calculate_delivery_scores,
    calculate_quality_scores,
    calculate_cost_scores,
    calculate_compliance_scores,
    calculate_disruption_scores,
)


def test_delivery_score():
    shipments = [
        {
            "supplier_id": "SUP-000001",
            "status": "DELIVERED",
            "dispatch_date": "2026-01-01",
            "expected_delivery_date": "2026-01-10",
            "actual_delivery_date": "2026-01-08",
        },
        {
            "supplier_id": "SUP-000001",
            "status": "DELIVERED",
            "dispatch_date": "2026-01-01",
            "expected_delivery_date": "2026-01-10",
            "actual_delivery_date": "2026-01-12",
        },
    ]

    scores, invalid = calculate_delivery_scores(shipments)

    assert scores["SUP-000001"] == 50.0
    assert invalid == 0


def test_quality_score():
    inspections = [
        {
            "supplier_id": "SUP-000001",
            "inspected_quantity": "100",
            "accepted_quantity": "90",
            "rejected_quantity": "10",
        }
    ]

    scores, invalid = calculate_quality_scores(inspections)

    assert scores["SUP-000001"] == 90.0
    assert invalid == 0


def test_cost_score():
    orders = [
        {
            "po_id": "PO-001",
            "supplier_id": "SUP-000001",
            "total_amount": "1000",
            "currency": "INR",
        }
    ]

    invoices = [
        {
            "po_id": "PO-001",
            "supplier_id": "SUP-000001",
            "invoice_amount": "1100",
            "currency": "INR",
            "status": "VERIFIED",
        }
    ]

    scores, invalid = calculate_cost_scores(orders, invoices)

    assert scores["SUP-000001"] == 90.0
    assert invalid == 0


def test_compliance_score():
    contracts = [
        {"supplier_id": "SUP-000001", "compliance_status": "COMPLIANT"},
        {"supplier_id": "SUP-000001", "compliance_status": "PENDING"},
        {"supplier_id": "SUP-000001", "compliance_status": "NON_COMPLIANT"},
    ]

    scores = calculate_compliance_scores(contracts)

    assert scores["SUP-000001"] == 50.0


def test_invalid_risk_signal_is_excluded():
    signals = [
        {
            "supplier_id": "SUP-000001",
            "source": "",
            "observed_at": "",
            "severity": "HIGH",
        },
        {
            "supplier_id": "SUP-000002",
            "source": "Supplier Monitoring",
            "observed_at": "2026-10-20T10:00:00",
            "severity": "HIGH",
        },
    ]

    scores, invalid = calculate_disruption_scores(signals)

    assert "SUP-000001" not in scores
    assert scores["SUP-000002"] == 40.0
    assert invalid == 1
