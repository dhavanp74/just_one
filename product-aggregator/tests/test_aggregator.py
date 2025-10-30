import sys
import os
import pandas as pd

# ensure package import works
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import core.aggregator as aggregator


def test_fetch_combined_calls_save_snapshot(monkeypatch):
    # prepare fake scraper outputs
    fake_amazon = [
        {"title": "A", "price": 10, "link": "http://a", "source": "Amazon"},
    ]
    fake_flipkart = [
        {"title": "B", "price": 20, "link": "http://b", "source": "Flipkart"},
    ]

    # monkeypatch scrapers
    monkeypatch.setitem(sys.modules, 'scrapers.amazon_scraper', type('M', (), {'scrape_amazon': lambda q, max_results=10: fake_amazon}))
    monkeypatch.setitem(sys.modules, 'scrapers.flipkart_scraper', type('M', (), {'scrape_flipkart': lambda q, max_results=10, headless=True: fake_flipkart}))
    # other scrapers return empty
    monkeypatch.setitem(sys.modules, 'scrapers.jiomart_scraper', type('M', (), {'scrape_jiomart': lambda q, max_results=10, headless=True: []}))
    monkeypatch.setitem(sys.modules, 'scrapers.snapdeal_scraper', type('M', (), {'scrape_snapdeal': lambda q, max_results=10, headless=True: []}))

    called = {"count": 0, "args": None}

    def fake_save_snapshot(df, query):
        called['count'] += 1
        called['args'] = (df, query)
        return 123

    monkeypatch.setattr('database.db_helper.save_snapshot', fake_save_snapshot, raising=False)

    df = aggregator.fetch_combined("test-query", max_per_site=2, save_snapshot_to_db=True)

    # assertions
    assert isinstance(df, pd.DataFrame)
    assert called['count'] == 1
    saved_df, saved_query = called['args']
    assert saved_query == "test-query"
    assert 'title' in saved_df.columns
    assert len(df) >= 2
