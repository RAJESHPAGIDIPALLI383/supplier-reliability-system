
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "database" / "supplier_reliability.db"


def get_auth_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_db():
    connection = get_auth_connection()

    try:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS app_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (
                    role IN ('admin', 'engineer', 'viewer')
                ),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
    finally:
        connection.close()

def get_user_by_email(email):
    connection = get_auth_connection()

    try:
        user = connection.execute(
            "SELECT * FROM app_users WHERE email = ?",
            (email,)
        ).fetchone()

        return dict(user) if user else None

    finally:
        connection.close()


def create_user(username, email, password_hash, role="viewer"):
    connection = get_auth_connection()

    try:
        cursor = connection.execute(
            """
            INSERT INTO app_users
            (username, email, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (username, email, password_hash, role)
        )

        connection.commit()

        user = connection.execute(
            "SELECT * FROM app_users WHERE id = ?",
            (cursor.lastrowid,)
        ).fetchone()

        return dict(user)

    finally:
        connection.close()