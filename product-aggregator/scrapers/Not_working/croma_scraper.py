import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_croma(product_name, max_results=15):
    driver = uc.Chrome()
    results = []
    try:
        driver.get("https://www.croma.com/")
        # Accept cookies if popup appears
        try:
            accept_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept')]"))
            )
            accept_btn.click()
        except Exception:
            pass

        # Search for product
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchV2"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)
        for i in range(6):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
        time.sleep(3) # Extra sleep for lazy images

        blocks = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
        print(f"Found {len(blocks)} product links with XPath.")

        used_titles = set()
        for item in blocks:
            try:
                title = item.text.strip()
                link = item.get_attribute("href")
                if not title or title in used_titles or not link:
                    continue
                used_titles.add(title)

                # Find price near product link
                price_val = None
                try:
                    price_tag = item.find_element(By.XPATH, "../../..//*[contains(text(),'₹')]")
                    price_txt = price_tag.text.replace(",", "").replace("₹", "").strip().split()[0]
                    if price_txt.replace('.', '', 1).isdigit():
                        price_val = float(price_txt)
                except:
                    continue
                if not price_val:
                    continue

                # FINAL image extraction logic begins here:
                image = None
                try:
                    parent = item.find_element(By.XPATH, "../../..")
                    img_tags = parent.find_elements(By.TAG_NAME, "img")
                    for tag in img_tags:
                        src = tag.get_attribute("src")
                        datasrc = tag.get_attribute("data-src")
                        # Skip svg/logo, prefer product images (jpg/png/webp) and those with 'media'
                        if src and not src.endswith('.svg') and (
                            'media' in src or
                            src.endswith(('.jpg', '.jpeg', '.png', '.webp'))
                        ):
                            image = src
                            break
                        if datasrc and not datasrc.endswith('.svg') and (
                            'media' in datasrc or
                            datasrc.endswith(('.jpg', '.jpeg', '.png', '.webp'))
                        ):
                            image = datasrc
                            break
                except:
                    image = None

                results.append({
                    "title": title,
                    "price": price_val,
                    "link": link,
                    "image": image,
                    "source": "Croma"
                })

                if len(results) >= max_results:
                    break
            except Exception as e:
                print("Skip product due to error:", e)
        print(f"[Croma] Parsed {len(results)} unique products.")
    finally:
        driver.quit()
    return results

# Example usage:
# print(scrape_croma('Washing machine'))
# print(scrape_croma('headphones'))
