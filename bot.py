from playwright.sync_api import sync_playwright

BLS_URL = "https://algeria.blsspainvisa.com/algiers/"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page()

    print("Opening Algiers BLS...")
    page.goto(
        BLS_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("TITLE:", page.title())
    print("URL:", page.url)

    print("\n=== LINKS ===")

    for i, link in enumerate(page.locator("a").all()):
        try:
            text = link.inner_text().strip()
            href = link.get_attribute("href")

            if text or href:
                print(f"[{i}] {text}")
                print(f"    {href}")

        except Exception:
            pass

    browser.close()

print("\nDone.")
