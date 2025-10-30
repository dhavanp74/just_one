import requests
from bs4 import BeautifulSoup
from utils.logger import get_logger

logger = get_logger(__name__)


def scrape_amazon(product_name, max_results=10, timeout: int = 10, retries: int = 1):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive"
    }

    query = product_name.replace(" ", "+")
    url = f"https://www.amazon.in/s?k={query}"

    resp = None
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            break
        except Exception as e:
            last_exc = e
            logger.warning("Amazon request attempt %d failed: %s", attempt, e)
    if resp is None:
        logger.error("Amazon request failed after retries: %s", last_exc)
        return []

    if resp.status_code != 200:
        logger.error("Amazon returned status %d", resp.status_code)
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = soup.select("div.s-result-item[data-component-type='s-search-result']")

    results = []
    for item in items[:max_results]:
        name_tag = item.select_one("h2 span")
        price_tag = item.select_one("span.a-price-whole")
        link_tag = item.select_one("a.a-link-normal.s-no-outline")
        img_tag = item.select_one("img.s-image")
        rating_tag = item.select_one("span.a-icon-alt")

        if not name_tag or not price_tag or not link_tag:
            continue

        title = name_tag.get_text(strip=True)
        try:
            price_val = float(price_tag.get_text(strip=True).replace(",", ""))
        except ValueError:
            continue

        full_link = "https://www.amazon.in" + link_tag.get("href")
        image_url = img_tag.get("src") if img_tag else None
        rating = rating_tag.get_text(strip=True) if rating_tag else "N/A"

        results.append({
            "title": title,
            "price": price_val,
            "rating": rating,
            "link": full_link,
            "image": image_url,
            "source": "Amazon"
        })

    return results

# Example
# print(scrape_amazon("Nike shoes"))
