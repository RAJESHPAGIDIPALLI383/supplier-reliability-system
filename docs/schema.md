
# Supplier Reliability System - Database Schema

## 1. Overview

This project generates and evaluates supplier reliability data using a relational SQLite database.

The database stores supplier master data, operational transactions, delivery events, inspections, invoices, risk signals, and supplier scores.

## 2. Database

Database name: supplier_reliability.db

SQL seed file: supplier_reliability_seed.sql

Database engine: SQLite

## 3. Core Entities

| Entity | Description |
|---|---|
| Suppliers | Supplier master records |
| Sites | Supplier operating locations |
| Contracts | Supplier agreements |
| Purchase Orders | Procurement orders |
| PO Lines | Individual order line items |
| Shipments | Shipment records |
| Shipment Lines | Items included in shipments |
| Delivery Events | Shipment tracking history |
| Inspections | Quality inspection records |
| Invoices | Supplier billing records |
| Risk Signals | Supplier risk observations |
| Supplier Scores | Calculated reliability scores |

## 4. Relationships

- One Supplier can have multiple Sites.
- One Supplier can have multiple Contracts.
- One Supplier can have multiple Purchase Orders.
- One Purchase Order can contain multiple PO Lines.
- One Purchase Order can have multiple Shipments.
- One Shipment can contain multiple Shipment Lines.
- One Shipment can have multiple Delivery Events.
- One Supplier can have multiple Inspections.
- One Supplier can have multiple Invoices.
- One Supplier can have multiple Risk Signals.
- One Supplier can have multiple historical Score records.

## 5. Primary Keys

Each main entity uses a unique identifier.

Examples:

- Supplier: SUP-000001
- Purchase Order: PO-2026-000001
- Shipment: SHP-2026-000001
- Risk Signal: RSK-SUP-000001-2026-01
- Supplier Score: SCORE-2026-000001

## 6. Foreign Keys

Foreign keys connect transaction records with their parent entities.

Examples:

- sites.supplier_id references suppliers.supplier_id
- purchase_orders.supplier_id references suppliers.supplier_id
- shipments.po_id references purchase_orders.po_id
- delivery_events.shipment_id references shipments.shipment_id
- inspections.supplier_id references suppliers.supplier_id

## 7. Data Quality Handling

The database uses primary key and foreign key constraints.

Invalid records are preserved in the data_quality_exceptions table.

The deliberate shipment-without-PO anomaly is quarantined rather than silently discarded.

Additional validation checks detect:
- Delivery before dispatch
- Supplier site conflation
- Risk signals without source or timestamp
- Shipment without a valid purchase order
- Future-data leakage in supplier scoring

## 8. Database Integrity

Foreign key integrity was verified using:

PRAGMA foreign_key_check;

Expected result for imported records:

[]

## 9. Export

The SQLite database is exported into a SQL seed file using SQLite's iterdump functionality.
