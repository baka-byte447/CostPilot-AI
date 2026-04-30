import os
import sqlite3
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv
import requests

def run_validations():
    print("Running Startup Validations...")
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    success = True

    # 1. JWT Secret
    secret = os.getenv("JWT_SECRET")
    if not secret or secret == "change-me":
        print("FAIL: JWT_SECRET is missing or insecure")
        success = False
    else:
        print("PASS: JWT_SECRET is secure")

    # 2. AWS Keys
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            content = f.read()
            if "AWS_ACCESS_KEY_ID=" in content:
                print("FAIL: Hardcoded AWS keys found in .env")
                success = False
            else:
                print("PASS: No hardcoded AWS keys in .env")

    # 3. DB Schema
    db_path = Path(__file__).parent.parent.parent / "database" / "metrics.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(metrics);")
            cols = [r[1] for r in cur.fetchall()]
            if "user_id" not in cols:
                print("FAIL: metrics table missing user_id column")
                success = False
            else:
                print("PASS: metrics table has user_id")
        except Exception as e:
            print(f"FAIL: Database error - {e}")
            success = False
    else:
        print("WARN: Database file not found yet (might be created on startup)")

    print(f"Startup Validation {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == "__main__":
    exit(0 if run_validations() else 1)
