"""Utility to list and preview saved snapshots from the SQLite DB used by db_helper.

Run with: python tools/inspect_snapshots.py [--query QUERY]
"""
import argparse
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database import db_helper


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Filter snapshots by query", default=None)
    args = parser.parse_args()

    snaps = db_helper.load_snapshots(query=args.query)
    if not snaps:
        print("No snapshots found.")
        return
    for s in snaps:
        print(f"ID: {s['id']}  Query: {s['query']}  Created: {s['created_at']}")
        df = s.get("df")
        if df is None or df.empty:
            print("  (empty snapshot)")
        else:
            print(df.head(3).to_string(index=False))
        print("-" * 40)


if __name__ == "__main__":
    main()
