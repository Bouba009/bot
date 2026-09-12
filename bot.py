from playwright.sync_api import sync_playwright

BLS_URL = "https://algeria.blsspainvisa.com/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("Opening BLS...")
    page.goto(BLS_URL, wait_until="domcontentloaded", timeout=60000)

    print("\n=== LINKS FOUND ===")

    links = page.locator("a").all()

    for i, link in enumerate(links):
        try:
            text = link.inner_text().strip()
            href = link.get_attribute("href")

            if text or href:
                print(f"[{i}] TEXT: {text}")
                print(f"    URL: {href}")
        except:
            pass

    browser.close()

print("\nFinished.")
