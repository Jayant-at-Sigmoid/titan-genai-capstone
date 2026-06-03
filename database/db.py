import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from utils.logger import app_logger

# Locate db path in project root
DB_NAME = "compliance.db"
DB_PATH = os.getenv("COMPLIANCE_DB_PATH", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), DB_NAME))
DATABASE_URL = os.getenv("DATABASE_URL", "")

class PostgreSQLRow:
    """Mock Row class that implements both tuple-based indexing and dict-based indexing to mirror sqlite3.Row."""
    def __init__(self, description, values):
        self._keys = [desc[0] for desc in description] if description else []
        self._values = list(values)
        self._dict = dict(zip(self._keys, self._values))

    def __getitem__(self, item):
        if isinstance(item, int):
            return self._values[item]
        return self._dict[item]

    def keys(self):
        return self._keys

    def items(self):
        return self._dict.items()

    def __contains__(self, key):
        return key in self._dict

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

class PostgreSQLCursor:
    """Wrapper for PostgreSQL cursor that translates SQLite syntax and provides lastrowid fallback."""
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        # 1. Translate parameter placeholders (? to %s)
        translated_query = query.replace("?", "%s")
        # 2. Translate table creation primary key autoincrement syntax
        translated_query = translated_query.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        
        # 3. Translate SQLite unique conflict queries (INSERT OR IGNORE / INSERT OR REPLACE)
        if "INSERT OR IGNORE INTO settings" in translated_query:
            translated_query = translated_query.replace(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (%s, %s)",
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING"
            )
        if "INSERT OR REPLACE INTO settings" in translated_query:
            translated_query = translated_query.replace(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (%s, %s)",
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            )
            
        # 4. Handle auto-increment key retrieval for postgres
        is_insert = translated_query.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in translated_query.upper():
            if "INTO settings" not in translated_query.upper():
                translated_query += " RETURNING id"

        if params is not None:
            self._cursor.execute(translated_query, params)
        else:
            self._cursor.execute(translated_query)

        # 5. Extract returned ID to populate lastrowid
        if is_insert and "INTO settings" not in translated_query.upper():
            try:
                row = self._cursor.fetchone()
                if row:
                    self.lastrowid = row[0]
            except Exception:
                pass

    def executemany(self, query, seq_of_params):
        translated_query = query.replace("?", "%s")
        if "INSERT OR IGNORE INTO settings" in translated_query:
            translated_query = translated_query.replace(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (%s, %s)",
                "INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING"
            )
        self._cursor.executemany(translated_query, seq_of_params)

    def fetchone(self):
        res = self._cursor.fetchone()
        if res is not None:
            return PostgreSQLRow(self._cursor.description, res)
        return None

    def fetchall(self):
        res = self._cursor.fetchall()
        desc = self._cursor.description
        return [PostgreSQLRow(desc, row) for row in res]

    def close(self):
        self._cursor.close()

    def __iter__(self):
        desc = self._cursor.description
        for row in self._cursor:
            yield PostgreSQLRow(desc, row)

class PostgreSQLConnection:
    """Wrapper for PostgreSQL connection to expose standard cursor interface."""
    def __init__(self, pg_conn):
        self._conn = pg_conn
        self.row_factory = None

    def cursor(self):
        return PostgreSQLCursor(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

def get_db_connection():
    """Returns a connection to the database. Supports PostgreSQL if DATABASE_URL is configured, otherwise SQLite."""
    if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://"):
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            return PostgreSQLConnection(conn)
        except ImportError:
            app_logger.error("psycopg2 is required for PostgreSQL. Fallback to SQLite.")
            
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if tables do not exist."""
    db_type = "PostgreSQL" if DATABASE_URL.startswith("postgresql://") or DATABASE_URL.startswith("postgres://") else "SQLite"
    app_logger.info(f"Initializing {db_type} Database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Scans Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        status TEXT NOT NULL,
        compliance_score REAL DEFAULT 100.0,
        overall_risk TEXT DEFAULT 'LOW',
        report_path TEXT,
        redacted_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Violations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS violations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER NOT NULL,
        page_number INTEGER NOT NULL,
        category TEXT NOT NULL, -- PII, Confidential, Abuse, Encoding, Policy
        entity_type TEXT,       -- Email, Phone, Trade Secret, etc.
        severity TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
        confidence REAL DEFAULT 1.0,
        snippet TEXT,
        reason TEXT,
        remediation TEXT,
        review_status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected
        FOREIGN KEY (scan_id) REFERENCES scans(id) ON DELETE CASCADE
    )
    """)

    # Policies Table (For RAG reference uploads)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Rules Table (Dynamic configuration management)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL, -- PII, Confidential, Abuse, Encoding, etc.
        name TEXT NOT NULL,
        pattern TEXT NOT NULL,  -- Regex or keywords
        severity TEXT NOT NULL, -- LOW, MEDIUM, HIGH, CRITICAL
        is_active INTEGER DEFAULT 1
    )
    """)

    # Human Review Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        violation_id INTEGER NOT NULL,
        review_status TEXT NOT NULL,
        reviewer_notes TEXT,
        reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (violation_id) REFERENCES violations(id) ON DELETE CASCADE
    )
    """)

    # Settings Table (Enhancement 3 & 7)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # Sync Metadata Table (Enhancement 3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_metadata (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        last_modified TEXT,
        file_hash TEXT UNIQUE NOT NULL,
        sync_status TEXT DEFAULT 'Pending', -- Pending, Synced, Failed, Analyzed
        s3_key TEXT,
        upload_timestamp TIMESTAMP,
        source_folder TEXT
    )
    """)

    # Events Table (Enhancement 8)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL, -- FILE_DETECTED, FILE_SYNCED, FILE_ANALYZED, REPORT_GENERATED, REVIEW_COMPLETED
        resource TEXT,
        description TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Model Metrics Table (Enhancement 2 & 10)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS model_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model_name TEXT,
        latency REAL,
        input_tokens INTEGER,
        output_tokens INTEGER,
        estimated_cost REAL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Insert default compliance rules if the table is empty
    cursor.execute("SELECT COUNT(*) FROM rules")
    if cursor.fetchone()[0] == 0:
        default_rules = [
            # PII Rules
            ("PII", "Email Pattern", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "MEDIUM", 1),
            ("PII", "Phone Pattern", r"\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}", "MEDIUM", 1),
            ("PII", "Credit Card Pattern", r"\b(?:\d[ -]*?){13,16}\b", "HIGH", 1),
            ("PII", "Aadhaar Card Pattern", r"^[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}$", "HIGH", 1),
            ("PII", "PAN Card Pattern", r"[A-Z]{5}[0-9]{4}[A-Z]{1}", "HIGH", 1),
            # Confidential Rules
            ("Confidential", "Confidentiality Notice", r"(?i)confidential|internal use only|proprietary|do not distribute", "MEDIUM", 1),
            ("Confidential", "Financial Projections", r"(?i)revenue forecast|ebitda projection|profit margin|q[1-4] financial", "HIGH", 1),
            ("Confidential", "Intellectual Property", r"(?i)trade secret|patent pending|proprietary algorithm|source code disclosure", "CRITICAL", 1),
            # Abuse/Unlawful Rules
            ("Abuse", "Threats or Harassment", r"(?i)kill you|destroy you|extort|blackmail", "CRITICAL", 1),
            ("Abuse", "Hate Speech Terms", r"(?i)slurs|derogatory racial|hate groups", "CRITICAL", 1)
        ]
        cursor.executemany(
            "INSERT INTO rules (category, name, pattern, severity, is_active) VALUES (?, ?, ?, ?, ?)",
            default_rules
        )
        app_logger.info("Inserted default compliance rules.")

    # Initialize default settings
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ("auto_analysis_mode", "Manual"),
            ("onedrive_tenant_id", ""),
            ("onedrive_client_id", ""),
            ("onedrive_client_secret", ""),
            ("onedrive_folder_path", "ComplianceDocs")
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            default_settings
        )
        app_logger.info("Inserted default settings.")

    conn.commit()
    conn.close()
    app_logger.info("Database initialized successfully.")

# Helper queries
def add_scan(filename: str, file_path: str, status: str = "Pending") -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scans (filename, file_path, status) VALUES (?, ?, ?)",
        (filename, file_path, status)
    )
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scan_id

def update_scan_status(scan_id: int, status: str, compliance_score: float = None, overall_risk: str = None, report_path: str = None, redacted_path: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = ["status = ?"]
    params = [status]
    
    if compliance_score is not None:
        fields.append("compliance_score = ?")
        params.append(compliance_score)
    if overall_risk is not None:
        fields.append("overall_risk = ?")
        params.append(overall_risk)
    if report_path is not None:
        fields.append("report_path = ?")
        params.append(report_path)
    if redacted_path is not None:
        fields.append("redacted_path = ?")
        params.append(redacted_path)
        
    params.append(scan_id)
    query = f"UPDATE scans SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    conn.close()

def add_violation(scan_id: int, page_number: int, category: str, entity_type: str, severity: str, confidence: float, snippet: str, reason: str, remediation: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO violations (scan_id, page_number, category, entity_type, severity, confidence, snippet, reason, remediation)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scan_id, page_number, category, entity_type, severity, confidence, snippet, reason, remediation))
    violation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return violation_id

def get_scan(scan_id: int) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_scans_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_violations_for_scan(scan_id: int) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM violations WHERE scan_id = ?", (scan_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_policy_document(filename: str, file_path: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO policies (filename, file_path) VALUES (?, ?)",
        (filename, file_path)
    )
    policy_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return policy_id

def get_policies_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM policies ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_rules_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rules WHERE is_active = 1")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_rule(category: str, name: str, pattern: str, severity: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO rules (category, name, pattern, severity, is_active) VALUES (?, ?, ?, ?, 1)",
        (category, name, pattern, severity)
    )
    rule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return rule_id

def delete_rule(rule_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rules WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()

def delete_scan(scan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM violations WHERE scan_id = ?", (scan_id,))
    cursor.execute("DELETE FROM scans WHERE id = ?", (scan_id,))
    conn.commit()
    conn.close()

def delete_event(event_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
    conn.commit()
    conn.close()

def clear_events():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events")
    conn.commit()
    conn.close()

def update_violation_status(violation_id: int, review_status: str, notes: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE violations SET review_status = ? WHERE id = ?",
        (review_status, violation_id)
    )
    cursor.execute(
        "INSERT INTO reviews (violation_id, review_status, reviewer_notes) VALUES (?, ?, ?)",
        (violation_id, review_status, notes)
    )
    
    # Fetch filename for event logging
    cursor.execute("""
        SELECT s.filename FROM scans s
        JOIN violations v ON v.scan_id = s.id
        WHERE v.id = ?
    """, (violation_id,))
    row = cursor.fetchone()
    filename = row["filename"] if row else "Unknown Document"
    
    # Log GRC event
    cursor.execute("""
        INSERT INTO events (event_type, resource, description)
        VALUES (?, ?, ?)
    """, ("REVIEW_COMPLETED", filename, f"Auditor updated violation ID COMP-{violation_id} to status: {review_status}"))
    
    conn.commit()
    conn.close()

# Settings Helpers
def get_setting(key: str, default: str = "") -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

# OneDrive / S3 Sync Helpers
def add_sync_record(filename: str, last_modified: str, file_hash: str, sync_status: str, s3_key: str = None, source_folder: str = None) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO sync_metadata (filename, last_modified, file_hash, sync_status, s3_key, source_folder)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (filename, last_modified, file_hash, sync_status, s3_key, source_folder))
        record_id = cursor.lastrowid
        conn.commit()
    except Exception:
        record_id = -1
    conn.close()
    return record_id

def get_sync_records() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sync_metadata ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_sync_status_by_hash(file_hash: str, status: str, s3_key: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if s3_key:
        cursor.execute("""
            UPDATE sync_metadata 
            SET sync_status = ?, s3_key = ?, upload_timestamp = CURRENT_TIMESTAMP
            WHERE file_hash = ?
        """, (status, s3_key, file_hash))
    else:
        cursor.execute("UPDATE sync_metadata SET sync_status = ? WHERE file_hash = ?", (status, file_hash))
    conn.commit()
    conn.close()

# Event Logging Helpers (Event-Driven GRC)
def log_event(event_type: str, resource: str, description: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events (event_type, resource, description)
        VALUES (?, ?, ?)
    """, (event_type, resource, description))
    conn.commit()
    conn.close()

def get_events_list() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Model Analytics Logging
def log_model_metric(model_name: str, latency: float, input_tokens: int, output_tokens: int, estimated_cost: float):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO model_metrics (model_name, latency, input_tokens, output_tokens, estimated_cost)
        VALUES (?, ?, ?, ?, ?)
    """, (model_name, latency, input_tokens, output_tokens, estimated_cost))
    conn.commit()
    conn.close()

def get_model_metrics() -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM model_metrics ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
