import traceback
from typing import List, Dict, Optional

import pandas as pd


def _normalize(item: Dict) -> Dict:
    """Normalize scraper result dicts to a common schema.

    Schema: title, description, price, currency, link, image, source
    """
    return {
        "title": item.get("title") or item.get("name") or "",
        "description": item.get("description") or item.get("title") or "",
        "price": item.get("price") or None,
        "currency": item.get("currency") or "INR",
        "link": item.get("link") or item.get("url") or "",
        "image": item.get("image") or item.get("img") or None,
        "source": item.get("source") or "unknown",
    }


def fetch_combined(
    query: str,
    max_per_site: int = 10,
    sources: Optional[List[str]] = None,
    headless: bool = True,
    save_snapshot_to_db: bool = True,
) -> pd.DataFrame:
    """Fetch results from available scrapers and return a combined DataFrame.

    - Calls scrapers found in the `scrapers` package.
    - If a scraper fails, it is skipped and the error is logged.
    - Results are normalized into a simple schema.
    """
    results: List[Dict] = []

    # Try to import and call each scraper. Each call is isolated so failures
    # don't bring down the whole aggregator.
    # Amazon (requests-based) - call only if sources is None or contains "Amazon"
    try:
        if sources is None or "Amazon" in sources:
            from scrapers import amazon_scraper

            try:
                a = amazon_scraper.scrape_amazon(query, max_results=max_per_site)
                for it in a:
                    results.append(_normalize(it))
            except Exception:
                print("[aggregator] Amazon scraper failed:\n", traceback.format_exc())
    except Exception:
        # Amazon scraper missing / import failed
        print("[aggregator] Could not import amazon_scraper:\n", traceback.format_exc())

    # Selenium-based scrapers: attempt to call if available. They may require
    # undetected_chromedriver + Chrome; failures are caught and reported.
    try:
        if sources is None or "Flipkart" in sources:
            from scrapers import flipkart_scraper

            try:
                f = flipkart_scraper.scrape_flipkart(query, max_results=max_per_site, headless=headless)
                for it in f:
                    results.append(_normalize(it))
            except Exception:
                print("[aggregator] Flipkart scraper failed:\n", traceback.format_exc())
    except Exception:
        print("[aggregator] Could not import flipkart_scraper (ok if not installed):\n", traceback.format_exc())

    try:
        if sources is None or "JioMart" in sources:
            from scrapers import jiomart_scraper

            try:
                j = jiomart_scraper.scrape_jiomart(query, max_results=max_per_site, headless=headless)
                for it in j:
                    results.append(_normalize(it))
            except Exception:
                print("[aggregator] JioMart scraper failed:\n", traceback.format_exc())
    except Exception:
        print("[aggregator] Could not import jiomart_scraper (ok if not installed):\n", traceback.format_exc())

    try:
        if sources is None or "Snapdeal" in sources:
            from scrapers import snapdeal_scraper

            try:
                s = snapdeal_scraper.scrape_snapdeal(query, max_results=max_per_site, headless=headless)
                for it in s:
                    results.append(_normalize(it))
            except Exception:
                print("[aggregator] Snapdeal scraper failed:\n", traceback.format_exc())
    except Exception:
        print("[aggregator] Could not import snapdeal_scraper (ok if not installed):\n", traceback.format_exc())

    # Build DataFrame. Keep columns consistent.
    if not results:
        return pd.DataFrame(columns=["title", "description", "price", "currency", "link", "image", "source"]) 

    df = pd.DataFrame(results)

    # Deduplicate by link when possible, otherwise by title.
    if "link" in df.columns:
        df = df.drop_duplicates(subset=["link"])
    df = df.drop_duplicates(subset=["title"])  # fallback

    # Reorder columns
    cols = ["title", "description", "price", "currency", "link", "image", "source"]
    df = df[[c for c in cols if c in df.columns]]

    # Optionally persist snapshot
    if save_snapshot_to_db:
        try:
            from database.db_helper import save_snapshot

            try:
                save_snapshot(df, query)
            except Exception:
                print("[aggregator] failed to save snapshot:\n", traceback.format_exc())
        except Exception:
            # db_helper missing or import failed; continue silently
            print("[aggregator] db_helper not available (skipping save):\n", traceback.format_exc())

    return df


if __name__ == "__main__":
    # Quick local smoke: only run when executed directly.
    print(fetch_combined("test", max_per_site=3).head())
