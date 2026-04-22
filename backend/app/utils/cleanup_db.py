import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../database/metrics.db")
)


def cleanup_negative_metrics() -> dict:
    if not os.path.exists(DB_PATH):
        return {"error": f"DB not found at {DB_PATH}", "rows_fixed": 0}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("UPDATE metrics SET cpu_usage = 0.0 WHERE cpu_usage < 0")
    cpu_fixed = cursor.rowcount
    cursor.execute("UPDATE metrics SET memory_usage = 0.0 WHERE memory_usage < 0")
    mem_fixed = cursor.rowcount
    cursor.execute("UPDATE metrics SET request_load = 0.0 WHERE request_load < 0")
    req_fixed = cursor.rowcount

    conn.commit()
    conn.close()

    total = cpu_fixed + mem_fixed + req_fixed
    logger.info(f"DB cleanup: {cpu_fixed} cpu rows, {mem_fixed} memory rows, {req_fixed} request rows zeroed.")
    return {
        "cpu_rows_fixed":     cpu_fixed,
        "memory_rows_fixed":  mem_fixed,
        "request_rows_fixed": req_fixed,
        "total_rows_fixed":   total
    }


if __name__ == "__main__":
    result = cleanup_negative_metrics()
    print(result)
