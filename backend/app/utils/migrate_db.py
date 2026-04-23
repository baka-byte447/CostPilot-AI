import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../database/metrics.db")
)

def migrate():
    if not os.path.exists(DB_PATH):
        logger.info(f"No DB found at {DB_PATH}, skipping migration.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE metrics ADD COLUMN user_id INTEGER REFERENCES users(id)")
        logger.info("Added user_id column to metrics table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Column user_id already exists.")
        else:
            logger.error(f"Migration error: {e}")

    try:
        cursor.execute("ALTER TABLE metrics ADD COLUMN is_simulated INTEGER DEFAULT 0")
        logger.info("Added is_simulated column to metrics table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            logger.info("Column is_simulated already exists.")
        else:
            logger.error(f"Migration error: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
