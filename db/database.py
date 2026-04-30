import sqlite3
import logging
import json
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def get_connection():
    """Get a database connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for concurrent read/write
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def setup_db():
    """Create tables if they don't exist."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    aws_access_key_id TEXT,
                    aws_secret_access_key TEXT,
                    aws_region TEXT,
                    alert_email TEXT
                )
            """)

            # Backward-compatible user settings columns (older DBs may not have these).
            user_extra_columns = {
                "aws_regions": "TEXT",
                "smtp_host": "TEXT",
                "smtp_port": "INTEGER",
                "smtp_user": "TEXT",
                "smtp_password": "TEXT",
                "alert_from": "TEXT",
                "budget_threshold": "REAL",
                "snapshot_age_days": "INTEGER",
                "ec2_cpu_threshold": "REAL",
            }
            for col_name, col_type in user_extra_columns.items():
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                except sqlite3.OperationalError:
                    pass

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_waste_usd REAL DEFAULT 0,
                    resources_found INTEGER DEFAULT 0
                )
            """)

            try:
                cursor.execute("ALTER TABLE scans ADD COLUMN ai_advice TEXT")
            except sqlite3.OperationalError:
                pass


            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    detail TEXT,
                    waste_usd REAL DEFAULT 0,
                    region TEXT,
                    status TEXT DEFAULT 'detected',
                    detected_at TEXT,
                    FOREIGN KEY (scan_id) REFERENCES scans(id)
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT,
                    total_waste REAL DEFAULT 0,
                    threshold REAL DEFAULT 0,
                    email_sent INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    collected_at TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    namespace TEXT,
                    avg_value REAL,
                    max_value REAL,
                    min_value REAL,
                    unit TEXT,
                    period_seconds INTEGER,
                    start_time TEXT,
                    end_time TEXT,
                    region TEXT,
                    points INTEGER DEFAULT 0
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    predicted_avg REAL,
                    predicted_peak REAL,
                    horizon_hours INTEGER,
                    method TEXT,
                    region TEXT
                )
            """)
            try:
                cursor.execute("ALTER TABLE forecasts ADD COLUMN current_avg REAL")
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute("ALTER TABLE forecasts ADD COLUMN current_peak REAL")
            except sqlite3.OperationalError:
                pass

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    action TEXT NOT NULL,
                    parameters_json TEXT,
                    reason TEXT,
                    confidence REAL,
                    estimated_savings REAL,
                    status TEXT DEFAULT 'planned',
                    explanation TEXT,
                    region TEXT,
                    applied_at TEXT,
                    apply_result TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action_id INTEGER,
                    timestamp TEXT NOT NULL,
                    event TEXT NOT NULL,
                    actor TEXT,
                    message TEXT
                )
            """)

            conn.commit()
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database setup failed: {e}")
        raise

# --- User Management ---
def create_user(email, password_hash):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None # Email already exists
    except sqlite3.Error as e:
        logger.error(f"Failed to create user: {e}")
        return None

def get_user_by_email(email):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch user by email: {e}")
        return None

def get_user_by_id(user_id):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch user by id: {e}")
        return None

def update_user_credentials(user_id, aws_access, aws_secret, aws_region, alert_email):
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users 
                   SET aws_access_key_id = ?, aws_secret_access_key = ?, aws_region = ?, alert_email = ?
                   WHERE id = ?""",
                (aws_access, aws_secret, aws_region, alert_email, user_id)
            )
            conn.commit()
            return True
    except sqlite3.Error as e:
        logger.error(f"Failed to update user credentials: {e}")
        return False



def save_alert(alert_type, message, total_waste, threshold, email_sent=False):
    """Save an alert record to the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO alerts (timestamp, alert_type, message, total_waste, threshold, email_sent)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (datetime.now().isoformat(), alert_type, message, total_waste, threshold, 1 if email_sent else 0)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to save alert: {e}")
        return None


def get_alerts(limit=50):
    """Return recent alerts, newest first."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch alerts: {e}")
        return []


def clear_all_alerts():
    """Clear all alerts from the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts")
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to clear alerts: {e}")
        raise


def save_scan(total_waste, resources_found):
    """Save a scan record and return the scan ID."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO scans (timestamp, total_waste_usd, resources_found) VALUES (?, ?, ?)",
                (datetime.now().isoformat(), total_waste, resources_found)
            )
            scan_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Scan #{scan_id} saved — ${total_waste} waste, {resources_found} resources.")
            return scan_id
    except sqlite3.Error as e:
        logger.error(f"Failed to save scan: {e}")
        raise


def save_resource(scan_id, resource_type, resource_id, detail, waste_usd, region):
    """Save a detected resource to the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO resources 
                   (scan_id, resource_type, resource_id, detail, waste_usd, region, status, detected_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (scan_id, resource_type, resource_id, detail, waste_usd, region, "detected", datetime.now().isoformat())
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to save resource {resource_id}: {e}")
        raise


def get_all_scans():
    """Return all scan records, newest first."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch scans: {e}")
        return []


def clear_all_scans():
    """Clear all scans and associated resources from the database."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resources")
            cursor.execute("DELETE FROM scans")
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to clear scans: {e}")
        raise


def get_scan_resources(scan_id):
    """Return all resources for a given scan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resources WHERE scan_id = ? ORDER BY waste_usd DESC", (scan_id,))
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch resources for scan {scan_id}: {e}")
        return []


def get_latest_scan():
    """Return the most recent scan and its resources."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scans ORDER BY timestamp DESC LIMIT 1")
            scan = cursor.fetchone()
            if scan:
                scan = dict(scan)
                scan["resources"] = get_scan_resources(scan["id"])
                return scan
            return None
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch latest scan: {e}")
        return None


def get_cost_trend(limit=30):
    """Return the last N scans for cost trend charting."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT timestamp, total_waste_usd, resources_found FROM scans ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            rows = [dict(row) for row in cursor.fetchall()]
            rows.reverse()  # oldest first for chart
            return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch cost trend: {e}")
        return []


def update_resource_status(resource_id, status):
    """Update the status of a resource (e.g., 'deleted', 'kept')."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE resources SET status = ? WHERE resource_id = ?",
                (status, resource_id)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update resource {resource_id}: {e}")
        raise


def update_scan_ai_advice(scan_id, advice):
    """Update the AI advice for a given scan."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE scans SET ai_advice = ? WHERE id = ?",
                (advice, scan_id)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update scan {scan_id} AI advice: {e}")
        raise


def save_metrics(metrics):
    """Save collected metric series summaries."""
    if not metrics:
        return
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for m in metrics:
                cursor.execute(
                    """INSERT INTO metrics
                       (collected_at, resource_id, resource_type, metric_name, namespace,
                        avg_value, max_value, min_value, unit, period_seconds, start_time,
                        end_time, region, points)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now().isoformat(),
                        m.resource_id,
                        m.resource_type,
                        m.metric_name,
                        m.namespace,
                        m.avg_value,
                        m.max_value,
                        m.min_value,
                        m.unit,
                        m.period,
                        m.start_time.isoformat(),
                        m.end_time.isoformat(),
                        m.region,
                        len(m.datapoints),
                    ),
                )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to save metrics: {e}")
        raise


def save_forecasts(forecasts):
    """Save forecasted metric values."""
    if not forecasts:
        return
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for f in forecasts:
                cursor.execute(
                    """INSERT INTO forecasts
                       (created_at, resource_id, resource_type, metric_name, predicted_avg,
                        predicted_peak, horizon_hours, method, region, current_avg, current_peak)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now().isoformat(),
                        f.resource_id,
                        f.resource_type,
                        f.metric_name,
                        f.predicted_avg,
                        f.predicted_peak,
                        f.horizon_hours,
                        f.method,
                        f.region,
                        getattr(f, "current_avg", None),
                        getattr(f, "current_peak", None),
                    ),
                )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to save forecasts: {e}")
        raise


def save_optimizations(actions):
    """Persist optimization actions and update actions with IDs."""
    if not actions:
        return []
    ids = []
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            for action in actions:
                cursor.execute(
                    """INSERT INTO optimizations
                       (created_at, resource_id, resource_type, action, parameters_json,
                        reason, confidence, estimated_savings, status, explanation, region)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now().isoformat(),
                        action.get("resource_id"),
                        action.get("resource_type"),
                        action.get("action"),
                        json.dumps(action.get("parameters") or {}),
                        action.get("reason"),
                        action.get("confidence"),
                        action.get("estimated_savings"),
                        action.get("status", "planned"),
                        action.get("explanation"),
                        action.get("region"),
                    ),
                )
                action_id = cursor.lastrowid
                action["id"] = action_id
                ids.append(action_id)
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to save optimizations: {e}")
        raise
    return ids


def update_optimization_status(action_id, status, apply_result=None, applied_at=None):
    """Update optimization status and apply metadata."""
    if not action_id:
        return
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE optimizations
                   SET status = ?, applied_at = ?, apply_result = ?
                   WHERE id = ?""",
                (
                    status,
                    applied_at or datetime.now().isoformat(),
                    apply_result,
                    action_id,
                ),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update optimization {action_id}: {e}")
        raise


def update_optimization_explanation(action_id, explanation):
    """Update explanation text for an optimization action."""
    if not action_id:
        return
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE optimizations SET explanation = ? WHERE id = ?",
                (explanation, action_id),
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Failed to update optimization explanation {action_id}: {e}")
        raise


def get_recent_optimizations(limit=50):
    """Return recent optimization actions, newest first."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM optimizations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            rows = [dict(row) for row in cursor.fetchall()]
            for row in rows:
                if row.get("parameters_json"):
                    try:
                        row["parameters"] = json.loads(row["parameters_json"])
                    except Exception:
                        row["parameters"] = {}
            return rows
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch optimizations: {e}")
        return []


def get_recent_forecasts(limit=50):
    """Return recent forecasts, newest first."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM forecasts ORDER BY created_at DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch forecasts: {e}")
        return []


def get_latest_optimization_by_resource(resource_id):
    """Return latest optimization record for the resource."""
    if not resource_id:
        return None
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM optimizations WHERE resource_id = ? ORDER BY created_at DESC LIMIT 1",
                (resource_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            result = dict(row)
            if result.get("parameters_json"):
                try:
                    result["parameters"] = json.loads(result["parameters_json"])
                except Exception:
                    result["parameters"] = {}
            return result
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch latest optimization for {resource_id}: {e}")
        return None


def save_audit_log(action_id, event, actor=None, message=None):
    """Save an audit log entry for an optimization action."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO audit_logs (action_id, timestamp, event, actor, message) VALUES (?, ?, ?, ?, ?)""",
                (action_id, datetime.now().isoformat(), event, actor or 'web-ui', message),
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Failed to save audit log for {action_id}: {e}")
        return None


def get_audit_logs(action_id, limit=100):
    """Return recent audit logs for a given optimization action."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM audit_logs WHERE action_id = ? ORDER BY timestamp DESC LIMIT ?",
                (action_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch audit logs for {action_id}: {e}")
        return []

def get_user_by_email(email):
    """Return user record by email."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Failed to fetch user {email}: {e}")
        return None

def create_user(email, password_hash):
    """Create a new user and return the user_id."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash, alert_email) VALUES (?, ?, ?)",
                (email, password_hash, email)
            )
            conn.commit()
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    except sqlite3.Error as e:
        logger.error(f"Failed to create user {email}: {e}")
        return None

def update_user_credentials(user_id, access_key, secret_key, region, alert_email):
    """Update AWS credentials and alert email for a user."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE users SET 
                   aws_access_key_id = ?, 
                   aws_secret_access_key = ?, 
                   aws_region = ?, 
                   alert_email = ? 
                   WHERE id = ?""",
                (access_key, secret_key, region, alert_email, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        logger.error(f"Failed to update credentials for user {user_id}: {e}")
        return False
