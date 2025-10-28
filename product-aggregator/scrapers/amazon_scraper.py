import requests
from bs4 import BeautifulSoup

def scrape_amazon(product_name, max_results=10):
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

    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        print(f"❌ Amazon returned status {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
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
