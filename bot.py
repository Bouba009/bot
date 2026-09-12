from playwright.sync_api import sync_playwright

BLS_URL = "https://algeria.blsspainvisa.com/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    print("Opening BLS...")
    page.goto(BLS_URL, wait_until="domcontentloaded", timeout=60000)

    print("\n=== BOOK APPOINTMENT LINKS ===")

    links = page.locator("a").all()

    for link in links:
        try:
            text = link.inner_text().strip()
            href = link.get_attribute("href")

            if "appointment" in text.lower() or "book" in text.lower():
                print("TEXT:", text)
                print("HREF:", href)
                print("----------------------")

        except Exception:
            pass

    browser.close()

print("Finished.")
