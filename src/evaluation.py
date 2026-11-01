import csv
import json
from collections import Counter

from src.config import RAW_DIR, PROCESSED_DIR, REPORTS_DIR


EXPECTED_ANOMALY_CHECKS = [
    "Delivery date must not precede dispatch",
    "Supplier site conflation",
    "Risk signal source and timestamp",
    "Shipment purchase order relationship",
    "Supplier score future data leakage",
]


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def read_csv(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def evaluate_anomaly_detection():
    report_path = REPORTS_DIR / "validation_report.json"
    report = read_json(report_path)

    results = report.get("results", [])

    detected = []
    missed = []

    for expected_check in EXPECTED_ANOMALY_CHECKS:
        matching_result = next(
            (
                result for result in results
                if result.get("check") == expected_check
            ),
            None,
        )

        if matching_result and matching_result.get("passed") is False:
            detected.append(expected_check)
        else:
            missed.append(expected_check)

    total = len(EXPECTED_ANOMALY_CHECKS)
    detected_count = len(detected)

    detection_rate = (
        detected_count / total * 100 if total else 0
    )

    return {
        "known_anomalies": total,
        "detected_anomalies": detected_count,
        "missed_anomalies": len(missed),
        "detection_rate_percentage": round(detection_rate, 2),
        "detected_checks": detected,
        "missed_checks": missed,
    }


def evaluate_supplier_scores():
    score_path = PROCESSED_DIR / "supplier_scores.csv"
    rows = read_csv(score_path)

    scores = []
    coverage_values = []
    ratings = Counter()

    for row in rows:
        score = row.get("final_score", "")
        coverage = row.get("data_coverage", "")
        rating = row.get("rating", "UNKNOWN")

        if score.strip():
            scores.append(float(score))

        if coverage.strip():
            coverage_values.append(float(coverage))

        ratings[rating] += 1

    return {
        "supplier_count": len(rows),
        "scored_supplier_count": len(scores),
        "average_score": round(
            sum(scores) / len(scores), 2
        ) if scores else None,
        "average_data_coverage": round(
            sum(coverage_values) / len(coverage_values), 2
        ) if coverage_values else None,
        "rating_distribution": dict(ratings),
    }


def run_evaluation():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    anomaly_results = evaluate_anomaly_detection()
    scoring_results = evaluate_supplier_scores()

    evaluation = {
        "evaluation_status": (
            "PASSED"
            if anomaly_results["missed_anomalies"] == 0
            else "REVIEW_REQUIRED"
        ),
        "anomaly_detection": anomaly_results,
        "supplier_scoring": scoring_results,
        "evaluation_notes": [
            "Evaluation uses validation results and supplier scores.",
            "Ground-truth labels are not used as scoring features.",
            "All five injected anomalies are evaluated.",
            "Supplier scores are calculated from source records.",
        ],
    }

    output_path = REPORTS_DIR / "evaluation_report.json"

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(evaluation, file, indent=4)

    print(json.dumps(evaluation, indent=4))
    print(f"\nEvaluation report saved: {output_path}")

    return evaluation


if __name__ == "__main__":
    run_evaluation()