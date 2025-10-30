from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from scrapers.base_scraper import make_driver
from utils.logger import get_logger

logger = get_logger(__name__)


def scrape_snapdeal(product_name, max_results=15, headless: bool = True):
    driver = make_driver(headless=headless)
    results = []
    try:
        driver.get("https://www.snapdeal.com/")
        # Search for product
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "inputValEnter"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        for i in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        time.sleep(2) # let images load

        # Product cards: look for listing divs with product links (/product/)
        blocks = driver.find_elements(By.XPATH, "//div[contains(@class, 'product-tuple-listing')]")
        logger.debug("Found %d product blocks.", len(blocks))

        for block in blocks:
            try:
                # Title
                title = ""
                try:
                    title = block.find_element(By.CLASS_NAME, "product-title").text.strip()
                except Exception:
                    try:
                        title = block.find_element(By.CLASS_NAME, "product-desc-rating").text.strip()
                    except Exception:
                        continue
                # Product link
                link = None
                try:
                    anchor = block.find_element(By.TAG_NAME, "a")
                    link = anchor.get_attribute("href")
                except Exception:
                    continue
                # Price
                price_val = None
                try:
                    price_tag = block.find_element(By.CLASS_NAME, "product-price")
                    price_txt = price_tag.text.replace(",", "").replace("Rs.", "").replace("₹", "").strip().split()[0]
                    if price_txt.replace('.', '', 1).isdigit():
                        price_val = float(price_txt)
                except Exception:
                    continue
                if not (title and link and price_val):
                    continue
                # Image
                image = None
                try:
                    img_tag = block.find_element(By.TAG_NAME, "img")
                    image = img_tag.get_attribute("src")
                    # Sometimes snapdeal uses data-src for lazy load
                    if (not image or image.strip() == "" or image.startswith("data:")):
                        image = img_tag.get_attribute("data-src")
                except Exception:
                    image = None

                results.append({
                    "title": title,
                    "price": price_val,
                    "link": link,
                    "image": image,
                    "source": "Snapdeal"
                })
                if len(results) >= max_results:
                    break
            except Exception as e:
                logger.debug("Skip product due to error: %s", e)
        logger.info("[Snapdeal] Parsed %d unique products.", len(results))
    finally:
        try:
            driver.quit()
        except Exception:
            logger.debug("Exception while quitting driver")
    return results

# Example usage:
# print(scrape_snapdeal("power bank"))
# print(scrape_snapdeal("laptop"))
