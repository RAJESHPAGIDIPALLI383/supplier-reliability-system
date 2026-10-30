
import csv
import json
import sqlite3

from src.config import RAW_DIR, PROCESSED_DIR, DATABASE_DIR


DATABASE_PATH = DATABASE_DIR / "supplier_reliability.db"


TABLES = {
    "suppliers": "suppliers.csv",
    "sites": "sites.csv",
    "contracts": "contracts.csv",
    "purchase_orders": "purchase_orders.csv",
    "po_lines": "po_lines.csv",
    "shipments": "shipments.csv",
    "shipment_lines": "shipment_lines.csv",
    "delivery_events": "delivery_events.csv",
    "inspections": "inspections.csv",
    "invoices": "invoices.csv",
    "risk_signals": "risk_signals.csv",
}


# --------------------------------------------------
# 1. CREATE DATABASE AND TABLE STRUCTURE
# --------------------------------------------------

def create_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id TEXT PRIMARY KEY
        );

        CREATE TABLE IF NOT EXISTS sites (
            site_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS contracts (
            contract_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            po_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            site_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id),
            FOREIGN KEY (site_id)
                REFERENCES sites(site_id)
        );

        CREATE TABLE IF NOT EXISTS po_lines (
            po_line_id TEXT PRIMARY KEY,
            po_id TEXT,
            FOREIGN KEY (po_id)
                REFERENCES purchase_orders(po_id)
        );

        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id TEXT PRIMARY KEY,
            po_id TEXT,
            supplier_id TEXT,
            FOREIGN KEY (po_id)
                REFERENCES purchase_orders(po_id),
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS shipment_lines (
            shipment_line_id TEXT PRIMARY KEY,
            shipment_id TEXT,
            po_line_id TEXT,
            FOREIGN KEY (shipment_id)
                REFERENCES shipments(shipment_id),
            FOREIGN KEY (po_line_id)
                REFERENCES po_lines(po_line_id)
        );

        CREATE TABLE IF NOT EXISTS delivery_events (
            event_id TEXT PRIMARY KEY,
            shipment_id TEXT,
            FOREIGN KEY (shipment_id)
                REFERENCES shipments(shipment_id)
        );

        CREATE TABLE IF NOT EXISTS inspections (
            inspection_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            shipment_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id),
            FOREIGN KEY (shipment_id)
                REFERENCES shipments(shipment_id)
        );

        CREATE TABLE IF NOT EXISTS invoices (
            invoice_id TEXT PRIMARY KEY,
            po_id TEXT,
            supplier_id TEXT,
            FOREIGN KEY (po_id)
                REFERENCES purchase_orders(po_id),
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS risk_signals (
            risk_signal_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS supplier_scores (
            score_id TEXT PRIMARY KEY,
            supplier_id TEXT,
            FOREIGN KEY (supplier_id)
                REFERENCES suppliers(supplier_id)
        );

        CREATE TABLE IF NOT EXISTS data_quality_exceptions (
            exception_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT,
            source_table TEXT,
            record_data TEXT,
            error_message TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_sites_supplier
        ON sites(supplier_id);

        CREATE INDEX IF NOT EXISTS idx_orders_supplier
        ON purchase_orders(supplier_id);

        CREATE INDEX IF NOT EXISTS idx_shipments_po
        ON shipments(po_id);

        CREATE INDEX IF NOT EXISTS idx_inspections_supplier
        ON inspections(supplier_id);

        CREATE INDEX IF NOT EXISTS idx_risks_supplier
        ON risk_signals(supplier_id);
    """)

    connection.commit()
    return connection


# --------------------------------------------------
# 2. AUTOMATICALLY ADD MISSING CSV COLUMNS
# --------------------------------------------------

def ensure_csv_columns(connection, table_name, columns):

    existing_columns = {
        row[1]
        for row in connection.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()
    }

    for column in columns:

        if column not in existing_columns:

            safe_column = column.replace('"', '""')

            connection.execute(
                f'ALTER TABLE "{table_name}" '
                f'ADD COLUMN "{safe_column}" TEXT'
            )


# --------------------------------------------------
# 3. IMPORT CSV DATA
# --------------------------------------------------

def import_csv(connection, table_name, filename):

    file_path = RAW_DIR / filename

    if not file_path.exists():
        print(f"Skipped: {filename} not found")
        return 0

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        columns = reader.fieldnames

        if not columns:
            print(f"Skipped: {filename} has no columns")
            return 0

        ensure_csv_columns(
            connection,
            table_name,
            columns
        )

        placeholders = ", ".join(
            ["?"] * len(columns)
        )

        column_names = ", ".join(
            '"' + column.replace('"', '""') + '"'
            for column in columns
        )

        query = (
            f'INSERT OR REPLACE INTO "{table_name}" '
            f"({column_names}) VALUES ({placeholders})"
        )

        imported = 0
        rejected = 0

        for row in reader:

            try:
                connection.execute(
                    query,
                    tuple(row[column] for column in columns)
                )

                imported += 1

            except sqlite3.IntegrityError as error:

                connection.execute(
                    """
                    INSERT INTO data_quality_exceptions (
                        source_file,
                        source_table,
                        record_data,
                        error_message
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        filename,
                        table_name,
                        json.dumps(row),
                        str(error)
                    )
                )

                rejected += 1

        connection.commit()

    print(
        f"{table_name}: "
        f"Imported={imported}, "
        f"Quarantined={rejected}"
    )

    return imported


# --------------------------------------------------
# 4. IMPORT SUPPLIER SCORES
# --------------------------------------------------

def import_supplier_scores(connection):

    file_path = PROCESSED_DIR / "supplier_scores.csv"

    if not file_path.exists():
        print(
            "Skipped supplier scores. "
            "Run scoring before database import."
        )
        return 0

    with open(
        file_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)
        columns = reader.fieldnames

        if not columns:
            return 0

        ensure_csv_columns(
            connection,
            "supplier_scores",
            columns
        )

        placeholders = ", ".join(
            ["?"] * len(columns)
        )

        column_names = ", ".join(
            '"' + column.replace('"', '""') + '"'
            for column in columns
        )

        query = (
            'INSERT OR REPLACE INTO supplier_scores '
            f"({column_names}) VALUES ({placeholders})"
        )

        imported = 0

        for row in reader:

            try:
                connection.execute(
                    query,
                    tuple(row[column] for column in columns)
                )

                imported += 1

            except sqlite3.IntegrityError as error:

                connection.execute(
                    """
                    INSERT INTO data_quality_exceptions (
                        source_file,
                        source_table,
                        record_data,
                        error_message
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        "supplier_scores.csv",
                        "supplier_scores",
                        json.dumps(row),
                        str(error)
                    )
                )

        connection.commit()

    print(f"supplier_scores: Imported={imported}")

    return imported


# --------------------------------------------------
# 5. DATABASE SUMMARY
# --------------------------------------------------

def show_database_summary(connection):

    print("\nDATABASE TABLE SUMMARY")
    print("-" * 45)

    tables = list(TABLES.keys())
    tables.extend([
        "supplier_scores",
        "data_quality_exceptions"
    ])

    for table in tables:

        result = connection.execute(
            f'SELECT COUNT(*) FROM "{table}"'
        ).fetchone()

        print(f"{table}: {result[0]} records")


# --------------------------------------------------
# 6. LOAD ALL DATA
# --------------------------------------------------

def load_all_data():

    connection = create_database()

    try:

        # Reload data consistently on every run.
        connection.execute("PRAGMA foreign_keys = OFF")

        for table in [
            "supplier_scores",
            "data_quality_exceptions",
            "risk_signals",
            "invoices",
            "inspections",
            "delivery_events",
            "shipment_lines",
            "shipments",
            "po_lines",
            "purchase_orders",
            "contracts",
            "sites",
            "suppliers"
        ]:
            connection.execute(
                f'DELETE FROM "{table}"'
            )

        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")

        total_rows = 0

        # Import parent tables before dependent tables.
        for table_name, filename in TABLES.items():

            total_rows += import_csv(
                connection,
                table_name,
                filename
            )

        total_rows += import_supplier_scores(connection)

        show_database_summary(connection)

        print("\n" + "=" * 45)
        print("DATABASE IMPORT COMPLETED")
        print("=" * 45)

        print(f"Database: {DATABASE_PATH}")
        print(f"Imported records: {total_rows}")

        exceptions = connection.execute(
            """
            SELECT COUNT(*)
            FROM data_quality_exceptions
            """
        ).fetchone()[0]

        print(f"Quarantined records: {exceptions}")

    finally:
        connection.close()

def export_sql():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)

    sql_path = DATABASE_DIR / "supplier_reliability_seed.sql"

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        with open(sql_path, "w", encoding="utf-8") as file:
            for line in connection.iterdump():
                file.write(line + "\n")

        print(f"SQL export created: {sql_path}")

    finally:
        connection.close()
        
if __name__ == "__main__":
    load_all_data()
    export_sql()