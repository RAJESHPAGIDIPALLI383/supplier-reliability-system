
# Supplier Reliability Scoring and Monitoring System

An explainable, reproducible, and data-driven supplier reliability system that evaluates supplier performance across delivery, quality, cost, capacity, compliance, and disruption risk.

## 1. Project Overview

Supplier performance directly affects procurement operations, product quality, delivery timelines, and business continuity.

This project generates realistic supplier procurement data, validates data quality, identifies known anomalies, and calculates explainable supplier reliability scores.

The system is designed to support transparent supplier evaluation and data-driven procurement decisions.

## 2. Key Features

- Synthetic supplier and procurement data generation.
- Fixed-seed reproducible datasets.
- Relational SQLite database.
- Primary key and foreign key validation.
- Data quality anomaly detection.
- Supplier reliability scoring.
- Missing-data-aware score calculation.
- Separate ground-truth anomaly labels.
- Automated unit and reproducibility tests.
- CSV, JSON, SQLite, and SQL seed exports.

## 3. Technology Stack

- Python 3
- SQLite
- SQL
- CSV and JSON
- Pytest
- Git and GitHub

## 4. Supplier Scoring Model

The system evaluates suppliers using six dimensions.

| Dimension | Weight |
|---|---:|
| Delivery | 30% |
| Quality | 25% |
| Cost | 15% |
| Capacity | 10% |
| Compliance | 10% |
| Disruption | 10% |
| **Total** | **100%** |

The final score uses available metrics and renormalizes the remaining weights when data is missing.

### Supplier Rating Categories

| Score | Rating |
|---|---|
| 85–100 | Excellent |
| 70–84.99 | Good |
| 50–69.99 | Moderate |
| Below 50 | Poor |

## 5. Dataset Scale

Baseline dataset:

| Entity | Records |
|---|---:|
| Suppliers | 1,000 |
| Purchase Orders | 10,000 |
| Shipments | 15,000 |
| Inspections | 20,000 |

Additional entities include sites, contracts, PO lines, shipment lines, delivery events, invoices, and risk signals.

The generator uses a fixed seed (`20261022`) to support reproducibility.

## 6. Known Data Quality Scenarios

The project includes five labelled anomaly scenarios:

1. Shipment without a valid Purchase Order.
2. Delivery date earlier than dispatch date.
3. Supplier score using future data.
4. Risk signal missing source and observation timestamp.
5. Supplier site associated with the wrong supplier.

Ground-truth labels are stored separately and are not used as scoring input features.

Invalid records are detected through validation and database constraints.

## 7. Project Structure

```text
supplier-reliability-system/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── ground_truth/
│
├── database/
│   ├── supplier_reliability.db
│   └── supplier_reliability_seed.sql
│
├── docs/
│   ├── schema.md
│   └── data_dictionary.md
│
├── reports/
│
├── src/
│   ├── config.py
│   ├── generate_data.py
│   ├── database.py
│   ├── validation.py
│   ├── scoring.py
│   ├── evaluation.py
│   └── main.py
│
├── tests/
│   ├── test_generation.py
│   ├── test_validation.py
│   ├── test_scoring.py
│   └── test_reproducibility.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

## 8. Installation

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd supplier-reliability-system
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## 9. Run the Project

Generate the synthetic dataset:

```bash
python -m src.generate_data
```

Run data validation:

```bash
python -m src.validation
```

Calculate supplier reliability scores:

```bash
python -m src.scoring
```

Create and populate the SQLite database and export SQL:

```bash
python -m src.database
```

Run automated tests:

```bash
python -m pytest -v
```

## 10. Database and Data Quality

The SQLite database maintains relationships between suppliers, sites, purchase orders, shipments, inspections, invoices, and risk signals.

Foreign key constraints protect relational integrity.

Invalid records rejected during import are preserved in the `data_quality_exceptions` table with their original record data and error message.

The database can be checked using:

```sql
PRAGMA foreign_key_check;
```

## 11. Test Results

The current automated test suite has passed:

**11 tests passed**

The tests cover:

- Required dataset record counts.
- Unique supplier and purchase order identifiers.
- Reproducible data generation.
- Delivery score calculation.
- Quality score calculation.
- Cost score calculation.
- Compliance score calculation.
- Invalid risk signal exclusion.
- Known anomaly detection.
- Primary key and foreign key checks.

## 12. Documentation

- `docs/schema.md` - Database structure and relationships.
- `docs/data_dictionary.md` - Dataset columns and descriptions.

## 13. Future Improvements

- Interactive supplier monitoring dashboard.
- Advanced supplier risk prediction.
- Historical supplier performance trends.
- API integration with procurement systems.
- Automated supplier alerts and notifications.

## 14. Project Objective

The objective is to demonstrate how structured data generation, relational database design, data quality validation, and explainable scoring can support supplier reliability decisions.

---

**Project:** Supplier Reliability Scoring and Monitoring System  
**Language:** Python  
**Database:** SQLite  
**Testing:** Pytest
