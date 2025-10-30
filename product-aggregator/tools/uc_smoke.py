"""Small diagnostic to verify undetected_chromedriver + Chrome can start.

Run this inside your conda env (or venv) where undetected_chromedriver is installed.
It will start a headless Chrome, fetch example.com and print versions.
"""
import sys
import traceback

try:
    import undetected_chromedriver as uc
    from selenium import webdriver
except Exception as e:
    print("ERROR: undetected_chromedriver or selenium not available:", e)
    sys.exit(2)


def run_headless():
    opts = uc.ChromeOptions()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--disable-dev-shm-usage")

    print("Starting undetected_chromedriver in headless mode...")
    try:
        driver = uc.Chrome(options=opts)
        driver.get("https://example.com")
        print("Page title:", driver.title)
        # print versions
        try:
            caps = driver.capabilities
            browser_version = caps.get("browserVersion") or caps.get("version")
            print("Browser version:", browser_version)
        except Exception:
            pass
        driver.quit()
        print("OK: headless Chrome started and loaded example.com")
    except Exception as e:
        print("ERROR: could not start headless Chrome:")
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    run_headless()
