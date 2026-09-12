from playwright.sync_api import sync_playwright

BLS_URL = "https://algeria.blsspainvisa.com/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    print("Opening BLS...")
    page.goto(BLS_URL, wait_until="domcontentloaded", timeout=60000)

    print("Page title:", page.title())
    print("Current URL:", page.url)

    browser.close()

print("BLS test completed successfully.")
