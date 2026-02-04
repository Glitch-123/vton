import sqlite3
from pathlib import Path

# ROOT folder me ek hi DB file
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "virtual_tryon.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

