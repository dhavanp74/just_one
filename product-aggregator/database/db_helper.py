import os
import sqlite3
import json
import datetime
import io
from typing import List, Dict

import pandas as pd


def init_db(db_path: str = None) -> str:
    """Ensure DB exists and required table is created. Returns db_path."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            created_at TEXT,
            data_json TEXT
        )
        """
    )
    conn.commit()
    conn.close()
    return db_path


def save_snapshot(df: pd.DataFrame, query: str, db_path: str = None) -> int:
    """Save a DataFrame snapshot as a JSON blob. Returns the inserted row id."""
    if db_path is None:
        db_path = init_db()
    else:
        init_db(db_path)

    data_json = df.to_json(orient="records", force_ascii=False)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO snapshots (query, created_at, data_json) VALUES (?, ?, ?)",
        (query, datetime.datetime.now(datetime.timezone.utc).isoformat(), data_json),
    )
    conn.commit()
    rowid = cur.lastrowid
    conn.close()
    return rowid


def load_snapshots(query: str = None, db_path: str = None) -> List[Dict]:
    """Load snapshots. Returns list of dicts {id, query, created_at, df}.
    If query is provided, filters by it.
    """
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.db")
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    if query:
        cur.execute(
            "SELECT id, query, created_at, data_json FROM snapshots WHERE query = ? ORDER BY id DESC",
            (query,),
        )
    else:
        cur.execute("SELECT id, query, created_at, data_json FROM snapshots ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    results: List[Dict] = []
    for id_, q, created_at, data_json in rows:
        try:
            # pandas.read_json will deprecate passing a literal JSON string directly.
            # Wrap in StringIO to keep compatibility and silence FutureWarning.
            df = pd.read_json(io.StringIO(data_json), orient="records")
        except Exception:
            df = pd.DataFrame()
        results.append({"id": id_, "query": q, "created_at": created_at, "df": df})
    return results


def delete_snapshot(snapshot_id: int, db_path: str = None) -> bool:
    """Delete a snapshot row by id. Returns True if a row was deleted."""
    if db_path is None:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "products.db")
    if not os.path.exists(db_path):
        return False
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DELETE FROM snapshots WHERE id = ?", (snapshot_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted > 0


if __name__ == "__main__":
    # quick manual check
    df = pd.DataFrame([{"title": "test", "price": 99}])
    db = init_db()
    print("DB at", db)
    rid = save_snapshot(df, "quick-test", db)
    print("Saved snapshot id", rid)
    print(load_snapshots("quick-test", db))
