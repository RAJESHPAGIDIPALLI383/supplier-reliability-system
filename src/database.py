
import csv
import json
import sqlite3

from src.config import RAW_DIR, PROCESSED_DIR, DATABASE_DIR

DB_PATH = DATABASE_DIR / "supplier_reliability.db"
SQL_PATH = DATABASE_DIR / "supplier_reliability_seed.sql"

TABLES = [
    "suppliers",
    "sites",
    "contracts",
    "purchase_orders",
    "po_lines",
    "shipments",
    "shipment_lines",
    "delivery_events",
    "inspections",
    "invoices",
    "risk_signals",
    "supplier_scores",
    "supplier_score_history",
]

SCHEMAS = {
    "suppliers": """
        supplier_id TEXT PRIMARY KEY,
        supplier_name TEXT NOT NULL,
        country TEXT,
        category TEXT,
        registration_date TEXT,
        monthly_capacity_units INTEGER CHECK (
            monthly_capacity_units IS NULL OR monthly_capacity_units >= 0
        ),
        status TEXT
    """,

    "sites": """
        site_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        site_name TEXT,
        city TEXT,
        country TEXT,
        effective_from TEXT,
        effective_to TEXT,
        status TEXT CHECK (status IS NULL OR status = 'ACTIVE'),
        CHECK (
            effective_to IS NULL OR effective_from IS NULL
            OR effective_to >= effective_from
        ),
        UNIQUE (site_id, supplier_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    """,

    "contracts": """
        contract_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        contract_start_date TEXT,
        contract_end_date TEXT,
        contract_value REAL CHECK (
            contract_value IS NULL OR contract_value >= 0
        ),
        currency TEXT,
        compliance_status TEXT CHECK (
            compliance_status IS NULL OR compliance_status IN (
                'COMPLIANT', 'NON_COMPLIANT', 'PENDING'
            )
        ),
        status TEXT CHECK (status IS NULL OR status = 'ACTIVE'),
        CHECK (
            contract_end_date IS NULL OR contract_start_date IS NULL
            OR contract_end_date >= contract_start_date
        ),
        UNIQUE (contract_id, supplier_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    """,

    "purchase_orders": """
        po_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        site_id TEXT NOT NULL,
        contract_id TEXT NOT NULL,
        order_date TEXT,
        required_date TEXT,
        currency TEXT,
        total_amount REAL CHECK (
            total_amount IS NULL OR total_amount >= 0
        ),
        status TEXT CHECK (
            status IS NULL OR status IN (
                'APPROVED', 'COMPLETED', 'PARTIALLY_DELIVERED'
            )
        ),
        CHECK (
            required_date IS NULL OR order_date IS NULL
            OR required_date >= order_date
        ),
        FOREIGN KEY (site_id, supplier_id)
            REFERENCES sites(site_id, supplier_id),
        FOREIGN KEY (contract_id, supplier_id)
            REFERENCES contracts(contract_id, supplier_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    """,

    "po_lines": """
        po_line_id TEXT PRIMARY KEY,
        po_id TEXT NOT NULL,
        item_code TEXT,
        ordered_quantity INTEGER CHECK (
            ordered_quantity IS NULL OR ordered_quantity >= 0
        ),
        unit_price REAL CHECK (unit_price IS NULL OR unit_price >= 0),
        line_amount REAL CHECK (line_amount IS NULL OR line_amount >= 0),
        UNIQUE (po_line_id, po_id),
        FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
    """,

    "shipments": """
        shipment_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        po_id TEXT NOT NULL,
        dispatch_date TEXT,
        expected_delivery_date TEXT,
        actual_delivery_date TEXT,
        carrier_name TEXT,
        status TEXT CHECK (status IS NULL OR status = 'DELIVERED'),
        CHECK (
            actual_delivery_date IS NULL OR dispatch_date IS NULL
            OR actual_delivery_date >= dispatch_date
        ),
        UNIQUE (shipment_id, po_id),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
        FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
    """,

    "shipment_lines": """
        shipment_line_id TEXT PRIMARY KEY,
        shipment_id TEXT NOT NULL,
        po_line_id TEXT NOT NULL,
        shipped_quantity INTEGER CHECK (
            shipped_quantity IS NULL OR shipped_quantity >= 0
        ),
        FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
        FOREIGN KEY (po_line_id) REFERENCES po_lines(po_line_id)
    """,

    "delivery_events": """
        delivery_event_id TEXT PRIMARY KEY,
        shipment_id TEXT NOT NULL,
        event_type TEXT,
        event_timestamp TEXT,
        location TEXT,
        source TEXT,
        FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
    """,

    "inspections": """
        inspection_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        shipment_id TEXT NOT NULL,
        po_line_id TEXT NOT NULL,
        inspection_date TEXT,
        inspected_quantity INTEGER CHECK (
            inspected_quantity IS NULL OR inspected_quantity >= 0
        ),
        accepted_quantity INTEGER CHECK (
            accepted_quantity IS NULL OR accepted_quantity >= 0
        ),
        rejected_quantity INTEGER CHECK (
            rejected_quantity IS NULL OR rejected_quantity >= 0
        ),
        defect_category TEXT,
        status TEXT CHECK (
            status IS NULL OR status IN ('PARTIAL', 'PASSED')
        ),
        CHECK (
            inspected_quantity IS NULL OR accepted_quantity IS NULL
            OR rejected_quantity IS NULL
            OR inspected_quantity = accepted_quantity + rejected_quantity
        ),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
        FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id),
        FOREIGN KEY (po_line_id) REFERENCES po_lines(po_line_id)
    """,

    "invoices": """
        invoice_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        po_id TEXT NOT NULL,
        invoice_date TEXT,
        invoice_amount REAL CHECK (
            invoice_amount IS NULL OR invoice_amount >= 0
        ),
        currency TEXT,
        status TEXT CHECK (status IS NULL OR status = 'VERIFIED'),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
        FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id)
    """,

    "risk_signals": """
        risk_signal_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        site_id TEXT,
        risk_type TEXT,
        severity TEXT CHECK (
            severity IS NULL OR severity IN (
                'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
            )
        ),
        source TEXT,
        observed_at TEXT,
        status TEXT CHECK (status IS NULL OR status = 'OPEN'),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
        FOREIGN KEY (site_id) REFERENCES sites(site_id)
    """,

    "supplier_scores": """
        supplier_id TEXT PRIMARY KEY,
        score_id TEXT,
        scoring_period TEXT,
        data_as_of_date TEXT,
        score_generated_at TEXT,
        delivery_score REAL,
        quality_score REAL,
        cost_score REAL,
        capacity_score REAL,
        compliance_score REAL,
        disruption_score REAL,
        data_coverage REAL,
        final_score REAL,
        rating TEXT,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    """,

    "supplier_score_history": """
        score_id TEXT PRIMARY KEY,
        supplier_id TEXT NOT NULL,
        scoring_period TEXT NOT NULL,
        data_as_of_date TEXT NOT NULL,
        score_generated_at TEXT NOT NULL,
        delivery_score REAL,
        quality_score REAL,
        cost_score REAL,
        capacity_score REAL,
        compliance_score REAL,
        disruption_score REAL,
        data_coverage REAL CHECK (
            data_coverage IS NULL OR data_coverage BETWEEN 0 AND 100
        ),
        final_score REAL CHECK (
            final_score IS NULL OR final_score BETWEEN 0 AND 100
        ),
        rating TEXT,
        UNIQUE (supplier_id, scoring_period),
        FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
    """,
}


def connect_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def create_database(connection):
    cursor = connection.cursor()

    cursor.execute("DROP TABLE IF EXISTS data_quality_exceptions")

    cursor.execute("""
        CREATE TABLE data_quality_exceptions (
            exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            target_table TEXT NOT NULL,
            record_json TEXT NOT NULL,
            error_message TEXT NOT NULL
        )
    """)

    for table in reversed(TABLES):
        cursor.execute(f"DROP TABLE IF EXISTS {table}")

    for table in TABLES:
        cursor.execute(
            f"CREATE TABLE {table} ({SCHEMAS[table]})"
        )

    indexes = [
        "CREATE INDEX idx_sites_supplier ON sites(supplier_id)",
        "CREATE INDEX idx_contracts_supplier ON contracts(supplier_id)",
        "CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id)",
        "CREATE INDEX idx_po_site ON purchase_orders(site_id)",
        "CREATE INDEX idx_shipments_po ON shipments(po_id)",
        "CREATE INDEX idx_events_shipment ON delivery_events(shipment_id)",
        "CREATE INDEX idx_inspections_supplier ON inspections(supplier_id)",
        "CREATE INDEX idx_risks_supplier ON risk_signals(supplier_id)",
        "CREATE INDEX idx_score_history_supplier ON supplier_score_history(supplier_id)",
        "CREATE INDEX idx_score_history_period ON supplier_score_history(scoring_period)",
    ]

    for statement in indexes:
        cursor.execute(statement)

    cursor.execute("""
        CREATE TRIGGER validate_shipment_supplier
        BEFORE INSERT ON shipments
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM purchase_orders po
            WHERE po.po_id = NEW.po_id
              AND po.supplier_id = NEW.supplier_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Shipment supplier does not match PO supplier');
        END
    """)

    cursor.execute("""
        CREATE TRIGGER validate_invoice_supplier
        BEFORE INSERT ON invoices
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM purchase_orders po
            WHERE po.po_id = NEW.po_id
              AND po.supplier_id = NEW.supplier_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Invoice supplier does not match PO supplier');
        END
    """)

    cursor.execute("""
        CREATE TRIGGER validate_risk_site_supplier
        BEFORE INSERT ON risk_signals
        FOR EACH ROW
        WHEN NEW.site_id IS NOT NULL
         AND NOT EXISTS (
            SELECT 1
            FROM sites s
            WHERE s.site_id = NEW.site_id
              AND s.supplier_id = NEW.supplier_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Risk signal site does not match supplier');
        END
    """)

    cursor.execute("""
        CREATE TRIGGER validate_shipment_line_po
        BEFORE INSERT ON shipment_lines
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM shipments sh
            JOIN po_lines pl ON pl.po_id = sh.po_id
            WHERE sh.shipment_id = NEW.shipment_id
              AND pl.po_line_id = NEW.po_line_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Shipment line PO line does not match shipment PO');
        END
    """)

    cursor.execute("""
        CREATE TRIGGER validate_inspection_relationships
        BEFORE INSERT ON inspections
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM shipments sh
            JOIN po_lines pl ON pl.po_id = sh.po_id
            WHERE sh.shipment_id = NEW.shipment_id
              AND sh.supplier_id = NEW.supplier_id
              AND pl.po_line_id = NEW.po_line_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'Inspection supplier or PO line does not match shipment');
        END
    """)

    connection.commit()


def import_csv(connection, filename, table, directory=RAW_DIR):
    path = directory / filename

    if not path.exists():
        print(f"File not found: {path}")
        return 0, 0

    imported = 0
    quarantined = 0

    with open(path, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            columns = list(row.keys())
            placeholders = ", ".join(["?"] * len(columns))
            column_names = ", ".join(columns)
            values = [row[column] or None for column in columns]

            sql = (
                f"INSERT INTO {table} ({column_names}) "
                f"VALUES ({placeholders})"
            )

            try:
                connection.execute(sql, values)
                imported += 1

            except sqlite3.IntegrityError as error:
                connection.execute(
                    """
                    INSERT INTO data_quality_exceptions (
                        source_file,
                        target_table,
                        record_json,
                        error_message
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        filename,
                        table,
                        json.dumps(row),
                        str(error),
                    ),
                )

                quarantined += 1

    connection.commit()

    print(
        f"{table}: Imported={imported}, "
        f"Quarantined={quarantined}"
    )

    return imported, quarantined


def show_database_summary(connection):
    print("\nDATABASE SUMMARY")
    print("-" * 50)

    total_records = 0

    for table in TABLES:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        total_records += count
        print(f"{table}: {count}")

    quarantined = connection.execute(
        "SELECT COUNT(*) FROM data_quality_exceptions"
    ).fetchone()[0]

    print(f"data_quality_exceptions: {quarantined}")
    print(f"\nImported records: {total_records}")
    print(f"Quarantined records: {quarantined}")

    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print(f"Foreign key violations: {len(violations)}")


def export_sql(connection):
    with open(SQL_PATH, "w", encoding="utf-8") as file:
        for statement in connection.iterdump():
            file.write(statement + "\n")

    print(f"SQL export created: {SQL_PATH}")


def load_all_data():
    connection = connect_database()

    try:
        create_database(connection)

        import_order = [
            ("suppliers.csv", "suppliers"),
            ("sites.csv", "sites"),
            ("contracts.csv", "contracts"),
            ("purchase_orders.csv", "purchase_orders"),
            ("po_lines.csv", "po_lines"),
            ("shipments.csv", "shipments"),
            ("shipment_lines.csv", "shipment_lines"),
            ("delivery_events.csv", "delivery_events"),
            ("inspections.csv", "inspections"),
            ("invoices.csv", "invoices"),
            ("risk_signals.csv", "risk_signals"),
        ]

        for filename, table in import_order:
            import_csv(connection, filename, table)

        import_csv(
            connection,
            "supplier_scores.csv",
            "supplier_scores",
            directory=PROCESSED_DIR,
        )

        import_csv(
            connection,
            "supplier_score_history.csv",
            "supplier_score_history",
            directory=PROCESSED_DIR,
        )

        show_database_summary(connection)
        export_sql(connection)

    finally:
        connection.close()


def main():
    print("SUPPLIER RELIABILITY DATABASE")
    print("=" * 50)

    load_all_data()


if __name__ == "__main__":
    main()
