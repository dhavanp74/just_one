import sys
import os
import pandas as pd

# Ensure product-aggregator is on sys.path so 'database' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from database import db_helper


def test_save_and_load_snapshot(tmp_path):
    db_file = str(tmp_path / "test.db")
    df = pd.DataFrame([{"title": "a", "price": 10}])

    rid = db_helper.save_snapshot(df, "test_query", db_path=db_file)
    assert isinstance(rid, int) and rid > 0

    snaps = db_helper.load_snapshots("test_query", db_path=db_file)
    assert len(snaps) == 1
    s = snaps[0]
    assert s["query"] == "test_query"
    loaded_df = s["df"]
    assert loaded_df.iloc[0]["title"] == "a"
    assert int(loaded_df.iloc[0]["price"]) == 10


def test_delete_snapshot(tmp_path):
    db_file = str(tmp_path / "test_delete.db")
    df = pd.DataFrame([{"title": "deltest", "price": 5}])

    rid = db_helper.save_snapshot(df, "del_query", db_path=db_file)
    assert isinstance(rid, int) and rid > 0

    snaps = db_helper.load_snapshots("del_query", db_path=db_file)
    assert len(snaps) == 1

    ok = db_helper.delete_snapshot(rid, db_path=db_file)
    assert ok is True

    snaps_after = db_helper.load_snapshots("del_query", db_path=db_file)
    assert len(snaps_after) == 0
