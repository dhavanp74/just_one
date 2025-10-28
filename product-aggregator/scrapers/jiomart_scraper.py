import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_jiomart(product_name, max_results=15):
    driver = uc.Chrome()
    results = []
    try:
        driver.get("https://www.jiomart.com/")

        # Search for product
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "autocomplete-0-input"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)

        # Scroll for AJAX content
        for i in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        # Find product blocks (each product link, usually /p/ or /product/)
        blocks = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/') or contains(@href, '/product/')]")
        print(f"Found {len(blocks)} product links with XPath.")

        used_titles = set()
        for item in blocks:
            try:
                title = item.text.strip()
                link = item.get_attribute("href")
                if not title or title in used_titles or not link:
                    continue
                used_titles.add(title)

                # Find nearest price (looks for ₹, Rs)
                price_val = None
                price_tag = None
                try:
                    price_tag = item.find_element(By.XPATH, "ancestor::div[contains(@class, 'plp-card-details')]//*[contains(text(),'₹') or contains(text(),'Rs')]")
                except:
                    try:
                        price_tag = item.find_element(By.XPATH, "../../..//*[contains(text(),'₹') or contains(text(),'Rs')]")
                    except:
                        pass
                if price_tag:
                    price_txt = price_tag.text.replace(",", "").replace("₹", "").replace("Rs", "").strip().split()[0]
                    if price_txt.replace('.', '', 1).isdigit():
                        price_val = float(price_txt)
                if not price_val:
                    continue

                # Get image
                image = None
                try:
                    img_tag = item.find_element(By.XPATH, ".//img")
                    image = img_tag.get_attribute("src")
                except:
                    pass

                results.append({
                    "title": title,
                    "price": price_val,
                    "link": link,
                    "image": image,
                    "source": "JioMart"
                })
                if len(results) >= max_results:
                    break
            except Exception as e:
                print("Skip product due to error:", e)
        print(f"[JioMart] Parsed {len(results)} unique products.")
    finally:
        driver.quit()
    return results

# Example:
# print(scrape_jiomart("laptop"))
# print(scrape_jiomart("water bottle"))
