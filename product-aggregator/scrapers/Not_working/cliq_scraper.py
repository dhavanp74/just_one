import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time

def scrape_tatacliq(product_name, max_results=15):
    driver = uc.Chrome()
    results = []
    try:
        driver.get("https://www.tatacliq.com/")
        time.sleep(3)
        # 1. Click the search icon to expand input
        try:
            search_icon = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and contains(@class, 'SearchHeader_prominentSearchRedHolder')]"))
            )
            search_icon.click()
            time.sleep(0.8)
        except Exception as e:
            print("Search icon not clickable", e)
            driver.quit()
            return []

        # 2. Tab or focus until a real input field appears, then send keys
        action = ActionChains(driver)
        # Try 5 tabs, sending the query + RETURN at each step until something works
        found = False
        for i in range(6):
            action.send_keys(Keys.TAB).perform()
            time.sleep(0.4)
            inputs = driver.find_elements(By.XPATH, "//input")
            active = driver.switch_to.active_element
            if inputs:
                try:
                    # Try using the active element
                    active.clear()
                    active.send_keys(product_name)
                    time.sleep(0.5)
                    active.send_keys(Keys.RETURN)
                    found = True
                    break
                except Exception:
                    continue
            else:
                # As last resort, send keys to BODY
                driver.find_element(By.TAG_NAME, "body").send_keys(product_name + Keys.RETURN)
                break
            time.sleep(0.3)

        if not found:
            print("Tried tab+type fallback, but real input was never found.")
            driver.quit()
            return []

        time.sleep(2)
        for _ in range(4):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

        blocks = driver.find_elements(By.XPATH, "//div[contains(@class,'ProductModule__Container')]")
        print(f"Found {len(blocks)} Tata Cliq product cards.")
        for card in blocks:
            try:
                title = card.find_element(By.XPATH, ".//div[contains(@class,'ProductModule__Name')]").text.strip()
                anchor = card.find_element(By.TAG_NAME, "a")
                link = anchor.get_attribute("href")
                if link and not link.startswith("http"):
                    link = "https://www.tatacliq.com" + link
                price_val = None
                try:
                    price_tag = card.find_element(By.XPATH, ".//div[contains(@class,'ProductModule__Price')]")
                    price_txt = price_tag.text.replace(",", "").replace("₹", "").replace("Rs.", "").strip().split()[0]
                    if price_txt.replace('.', '', 1).isdigit():
                        price_val = float(price_txt)
                except:
                    continue
                image = None
                try:
                    img_tag = card.find_element(By.TAG_NAME, "img")
                    image = img_tag.get_attribute("src")
                    if (not image or image.strip() == "" or image.startswith("data:")):
                        image = img_tag.get_attribute("data-src")
                except:
                    image = None
                results.append({
                    "title": title,
                    "price": price_val,
                    "link": link,
                    "image": image,
                    "source": "Tata Cliq"
                })
                if len(results) >= max_results:
                    break
            except Exception as e:
                print("Skip product due to error:", e)
        print(f"[Tata Cliq] Parsed {len(results)} unique products.")
    finally:
        driver.quit()
    return results

# Example usage:
# print(scrape_tatacliq("Refrigerator"))
