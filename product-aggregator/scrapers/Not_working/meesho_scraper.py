import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_meesho(product_name, max_results=15):
    driver = uc.Chrome()
    results = []
    try:
        driver.get("https://www.meesho.com/")
        # Close pop-up if it appears
        try:
            close_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//span[contains(@class,'Icon-sc-1m29qj1-0')]"))
            )
            close_btn.click()
        except Exception:
            pass

        # Search for product
        search_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder,'Try Saree, Kurti or Search by Product Code')]"))
        )
        search_box.clear()
        search_box.send_keys(product_name)
        search_box.send_keys(Keys.RETURN)
        time.sleep(2)

        # Infinite scroll loop (keeps scrolling until no more cards appear or limit hit)
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 20
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)
            cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'SearchProductCard')]")
            if len(cards) > last_count:
                last_count = len(cards)
                scroll_attempts = 0
            else:
                scroll_attempts += 1
            # If scraping plenty, or stuck for 3 scrolls, break out
            if scroll_attempts >= 3 or last_count >= max_results * 2:
                break

        cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'SearchProductCard')]")
        print(f"Found {len(cards)} product cards.")

        for card in cards:
            try:
                # Product link
                link = None
                try:
                    anchor = card.find_element(By.TAG_NAME, "a")
                    link = anchor.get_attribute("href")
                    if link and not link.startswith("http"):
                        link = "https://www.meesho.com" + link
                except:
                    continue
                # Product title
                title = ""
                try:
                    title_elem = card.find_element(By.XPATH, ".//p[contains(@class,'Text__Paragraph') or contains(@class,'Text__Title')]")
                    title = title_elem.text.strip()
                except:
                    continue
                # Product price
                price_val = None
                try:
                    price_tag = card.find_element(By.XPATH, ".//h5[contains(@class,'Text__StyledText') or contains(@class,'Price__StyledPrice')]")
                    price_txt = price_tag.text.replace(",", "").replace("₹", "").replace("Rs.", "").strip().split()[0]
                    if price_txt.replace('.', '', 1).isdigit():
                        price_val = float(price_txt)
                except:
                    continue
                # Image
                image = None
                try:
                    img_tag = card.find_element(By.TAG_NAME, "img")
                    image = img_tag.get_attribute("src")
                    if not image or image.strip() == "":
                        image = img_tag.get_attribute("data-src")
                except:
                    image = None

                results.append({
                    "title": title,
                    "price": price_val,
                    "link": link,
                    "image": image,
                    "source": "Meesho"
                })
                if len(results) >= max_results:
                    break
            except Exception as e:
                print("Skip product due to error:", e)
        print(f"[Meesho] Parsed {len(results)} unique products.")
    finally:
        driver.quit()
    return results

# Example usage:
# print(scrape_meesho('kurti'))
