\# Supplier Reliability System - Source Manifest



\## 1. Project Information



Project: Supplier Reliability Scoring System



Data Type: Synthetic / Programmatically Generated Data



Random Seed: 20261022



Generator: src/generate\_data.py



Configuration: src/config.py



\## 2. Data Sources



All datasets in this project are generated programmatically.

No real supplier personal or confidential business data is used.



| Dataset | Description |

|---|---|

| suppliers.csv | Supplier master records |

| sites.csv | Supplier operating locations |

| contracts.csv | Supplier contract information |

| purchase\_orders.csv | Purchase order records |

| po\_lines.csv | Purchase order line details |

| shipments.csv | Shipment records |

| shipment\_lines.csv | Shipment line details |

| delivery\_events.csv | Shipment delivery event history |

| inspections.csv | Quality inspection records |

| invoices.csv | Supplier invoice records |

| risk\_signals.csv | Supplier risk observations |



\## 3. Dataset Scale



| Entity | Baseline Records |

|---|---:|

| Suppliers | 1,000 |

| Purchase Orders | 10,000 |

| Shipments | 15,000 |

| Inspections | 20,000 |



Additional records are generated for related entities and

deliberate anomaly testing.



\## 4. Reproducibility



The generator uses a fixed random seed:



20261022



Run command:



python -m src.generate\_data



The random generator is reset at the beginning of each generation

run to support reproducible CSV outputs.



\## 5. Derived Data



Supplier scores are calculated from generated source records.



Scoring dimensions:



\- Delivery: 30%

\- Quality: 25%

\- Cost: 15%

\- Capacity: 10%

\- Compliance: 10%

\- Disruption: 10%



Generated supplier scores are stored in:



data/processed/supplier\_scores.csv



\## 6. Ground Truth and Anomalies



Known anomaly labels are maintained separately from scoring inputs.



Location:



data/ground\_truth/



Five deliberate anomaly scenarios:



1\. Shipment without a valid purchase order.

2\. Delivery date earlier than dispatch date.

3\. Supplier score using future data.

4\. Risk signal missing source and timestamp.

5\. Supplier site mapped to an incorrect supplier.



Ground-truth labels are used for evaluation only.

They are not used as supplier scoring features.



\## 7. Validation and Evaluation



Validation report:



reports/validation\_report.json



Evaluation report:



reports/evaluation\_report.json



The validation module checks data integrity and detects

the deliberately introduced anomalies.



\## 8. Limitations



\- Data is synthetic and does not represent actual supplier performance.

\- Scoring weights and business rules are configurable.

\- Real-world deployment would require verified enterprise data sources.

