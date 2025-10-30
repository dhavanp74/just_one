    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import time

    from scrapers.base_scraper import make_driver
    from utils.logger import get_logger

    logger = get_logger(__name__)


    def scrape_flipkart(product_name, max_results=15, headless: bool = True):
        """Scrape Flipkart for product results.

        Parameters kept compatible with the previous signature. Uses shared
        `make_driver` helper and `logger` for structured logs.
        """
        driver = make_driver(headless=headless)
        results = []
        try:
            driver.get("https://www.flipkart.com/")

            # Close login popup if present
            try:
                close_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='✕']"))
                )
                close_btn.click()
            except Exception:
                pass

            # Search for product
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            search_box.clear()
            search_box.send_keys(product_name)
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)

            # Scroll to load products (for AJAX)
            for i in range(4):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)

            # Find all anchor tags leading to a product page ("/p/"), inside generic product containers
            blocks = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
            logger.debug("Found %d product links with XPath.", len(blocks))

            used_titles = set()
            for item in blocks:
                try:
                    # Filter out duplicate/advertisement links
                    title = item.text.strip()
                    link = item.get_attribute("href")
                    if not title or title in used_titles or not link:
                        continue
                    used_titles.add(title)

                    # Try to find the closest price upwards in the DOM
                    price_val = None
                    price_tag = None
                    # Sometimes price is in a parent, sometimes a sibling; try both
                    try:
                        price_tag = item.find_element(By.XPATH, "ancestor::div[contains(@class, '_2kHMtA') or contains(@class, '_4ddWXP') or contains(@class, '_1xHGtK')]//div[contains(text(),'₹')]")
                    except Exception:
                        # Try going up two levels
                        try:
                            price_tag = item.find_element(By.XPATH, "../../..//div[contains(text(),'₹')]")
                        except Exception:
                            pass
                    if price_tag:
                        price_txt = price_tag.text.replace(",", "").replace("₹", "").strip().split()[0]
                        if price_txt.replace('.', '', 1).isdigit():
                            price_val = float(price_txt)
                    if not price_val:
                        continue

                    # Get closest image (usually in same container block)
                    image = None
                    try:
                        img_tag = item.find_element(By.XPATH, ".//img")
                        image = img_tag.get_attribute('src')
                    except Exception:
                        pass

                    results.append({
                        "title": title,
                        "price": price_val,
                        "link": link,
                        "image": image,
                        "source": "Flipkart"
                    })
                    if len(results) >= max_results:
                        break
                except Exception as e:
                    logger.debug("Skip product due to error: %s", e)
            logger.info("[Flipkart] Parsed %d unique products.", len(results))
        finally:
            try:
                driver.quit()
        except Exception:
            logger.debug("Exception while quitting driver")
    return results

# Example:
# print(scrape_flipkart("nike shoes"))
# print(scrape_flipkart("thermo bottle"))
