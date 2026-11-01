
from src.validation import run_validation


def test_validation_detects_all_five_known_anomalies():
    results = run_validation()

    assert results["total_checks"] == 25

    failed_checks = [
        result["check"]
        for result in results["results"]
        if not result["passed"]
    ]

    assert len(failed_checks) == 5

    expected_anomalies = [
        "Delivery date must not precede dispatch",
        "Supplier site conflation",
        "Risk signal source and timestamp",
        "Shipment purchase order relationship",
        "Supplier score future data leakage",
    ]

    for anomaly in expected_anomalies:
        assert anomaly in failed_checks


def test_primary_key_and_foreign_key_checks_pass():
    results = run_validation()

    for result in results["results"]:
        if "primary key" in result["check"].lower():
            assert result["passed"], result["check"]

        if "foreign key" in result["check"].lower():
            assert result["passed"], result["check"]
