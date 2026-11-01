
# Supplier Reliability System - Data Dictionary

## 1. Overview

This document describes the main entities, fields, identifiers, and relationships used in the Supplier Reliability System.

The data is generated using a fixed random seed to support reproducibility.

## 2. Supplier Master Data

### suppliers.csv

| Column | Description |
|---|---|
| supplier_id | Unique supplier identifier |
| supplier_name | Supplier name |
| category | Supplier business category |
| country | Supplier country |
| registration_date | Supplier registration date |
| status | Supplier operational status |

### sites.csv

| Column | Description |
|---|---|
| site_id | Unique supplier site identifier |
| supplier_id | Associated supplier identifier |
| site_name | Supplier site name |
| country | Site country |

### contracts.csv

| Column | Description |
|---|---|
| contract_id | Unique contract identifier |
| supplier_id | Associated supplier |
| start_date | Contract start date |
| end_date | Contract end date |
| compliance_status | Contract compliance status |

## 3. Procurement Data

### purchase_orders.csv

| Column | Description |
|---|---|
| po_id | Unique purchase order identifier |
| supplier_id | Supplier associated with the order |
| site_id | Supplier site |
| order_date | Purchase order creation date |
| expected_delivery_date | Expected delivery date |
| total_amount | Purchase order amount |
| currency | Transaction currency |
| status | Purchase order lifecycle status |

### po_lines.csv

| Column | Description |
|---|---|
| po_line_id | Unique purchase order line identifier |
| po_id | Parent purchase order |
| product_id | Product identifier |
| ordered_quantity | Ordered quantity |
| unit_price | Price per unit |

## 4. Shipment Data

### shipments.csv

| Column | Description |
|---|---|
| shipment_id | Unique shipment identifier |
| po_id | Related purchase order |
| supplier_id | Supplier identifier |
| dispatch_date | Shipment dispatch date |
| expected_delivery_date | Expected delivery date |
| actual_delivery_date | Actual delivery date |
| carrier_name | Shipping carrier |
| status | Shipment lifecycle status |

### shipment_lines.csv

| Column | Description |
|---|---|
| shipment_line_id | Unique shipment line identifier |
| shipment_id | Parent shipment |
| po_line_id | Related purchase order line |
| shipped_quantity | Quantity shipped |

### delivery_events.csv

| Column | Description |
|---|---|
| event_id | Unique delivery event identifier |
| shipment_id | Related shipment |
| event_type | Delivery event type |
| event_timestamp | Date and time of event |
| location | Event location |

## 5. Quality and Financial Data

### inspections.csv

| Column | Description |
|---|---|
| inspection_id | Unique inspection identifier |
| supplier_id | Associated supplier |
| shipment_id | Related shipment |
| inspected_quantity | Total inspected quantity |
| accepted_quantity | Accepted quantity |
| rejected_quantity | Rejected quantity |
| inspection_date | Inspection date |

### invoices.csv

| Column | Description |
|---|---|
| invoice_id | Unique invoice identifier |
| po_id | Related purchase order |
| supplier_id | Associated supplier |
| invoice_amount | Invoice amount |
| currency | Invoice currency |
| status | Invoice verification status |
| invoice_date | Invoice date |

## 6. Risk and Scoring Data

### risk_signals.csv

| Column | Description |
|---|---|
| risk_signal_id | Unique risk signal identifier |
| supplier_id | Associated supplier |
| source | Source of the risk observation |
| severity | Risk severity |
| observed_at | Risk observation timestamp |
| description | Risk description |

### supplier_scores.csv

| Column | Description |
|---|---|
| score_id | Unique score identifier |
| supplier_id | Associated supplier |
| delivery_score | Delivery performance score |
| quality_score | Product quality score |
| cost_score | Cost performance score |
| capacity_score | Capacity utilization score |
| compliance_score | Compliance score |
| disruption_score | Disruption risk score |
| final_score | Weighted supplier reliability score |
| rating | Supplier reliability category |

## 7. Identifiers and Formats

| Entity | Identifier format |
|---|---|
| Supplier | SUP-000001 |
| Site | SITE-SUP-000001-01 |
| Purchase Order | PO-2026-000001 |
| Shipment | SHP-2026-000001 |
| Risk Signal | RSK-SUP-000001-2026-01 |
| Supplier Score | SCORE-2026-000001 |

## 8. Supplier Scoring Weights

| Metric | Weight |
|---|---:|
| Delivery | 30% |
| Quality | 25% |
| Cost | 15% |
| Capacity | 10% |
| Compliance | 10% |
| Disruption | 10% |
| Total | 100% |

Missing metrics are excluded and the remaining weights are renormalized.

## 9. Data Quality Exceptions

The database contains a data_quality_exceptions table.

It stores records rejected during database import, along with:
- Source filename
- Source table
- Original record data
- Database error message

Known anomaly examples are maintained separately in ground_truth data and are not used as scoring input features.
