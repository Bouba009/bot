import os
import re
import time
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BLS_URL = "https://algeria.blsspainvisa.com/"
MANAGE_URL = "https://algeria.blsinternational.com/manage-appointments"

USERNAME = os.environ.get("BLS_USERNAME", "")
PASSWORD = os.environ.get("BLS_PASSWORD", "")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# كلمات يمكن تعديلها حسب نوع الموعد
TARGET_APPLICATION = os.environ.get(
    "TARGET_APPLICATION",
    "First application / première demande"
)

CHECK_INTERVAL = 10


def telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram is not configured.")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

        requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=20
        )

    except Exception as e:
        print("Telegram error:", e)


def clean(text):
    return re.sub(r"\s+", " ", text).strip().lower()


def find_login(page):
    """
    يحاول اكتشاف حقول تسجيل الدخول بدون الاعتماد على
    أسماء ثابتة قد تتغير في موقع BLS.
    """

    selectors_user = [
        'input[type="email"]',
        'input[name*="email" i]',
        'input[id*="email" i]',
        'input[name*="user" i]',
        'input[id*="user" i]',
        'input[type="text"]'
    ]

    selectors_pass = [
        'input[type="password"]',
        'input[name*="pass" i]',
        'input[id*="pass" i]'
    ]

    user = None
    password = None

    for selector in selectors_user:
        try:
            element = page.locator(selector).first

            if element.is_visible():
                user = element
                break
        except:
            pass

    for selector in selectors_pass:
        try:
            element = page.locator(selector).first

            if element.is_visible():
                password = element
                break
        except:
            pass

    return user, password


def login(page):

    print("Opening BLS...")

    page.goto(
        BLS_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    print("URL:", page.url)
    print("TITLE:", page.title())

    # إذا كان الموقع يحتاج الانتقال لصفحة الدخول
    if "login" not in page.url.lower():

        possible_login = [
            "text=تسجيل الدخول",
            "text=Login",
            "text=Sign in",
            "text=Connexion",
            "a[href*='login' i]",
            "button:has-text('Login')"
        ]

        for selector in possible_login:
            try:
                element = page.locator(selector).first

                if element.is_visible():
                    element.click()
                    page.wait_for_load_state(
                        "domcontentloaded",
                        timeout=30000
                    )
                    break
            except:
                pass

    user, password = find_login(page)

    if not user or not password:

        print("Login fields were not found.")

        page.screenshot(
            path="login_not_found.png",
            full_page=True
        )

        return False

    print("Login form detected.")

    user.fill(USERNAME)
    password.fill(PASSWORD)

    login_buttons = [
        "button[type='submit']",
        "input[type='submit']",
        "text=Login",
        "text=تسجيل الدخول",
        "text=Connexion",
        "button:has-text('دخول')"
    ]

    for selector in login_buttons:

        try:
            button = page.locator(selector).first

            if button.is_visible():
                button.click()

                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=60000
                )

                break

        except:
            pass

    time.sleep(3)

    print("After login URL:", page.url)

    return True


def open_manage(page):

    print("Opening appointment management...")

    page.goto(
        MANAGE_URL,
        wait_until="domcontentloaded",
        timeout=60000
    )

    time.sleep(3)

    print("Manage URL:", page.url)
    print("Manage title:", page.title())

    text = clean(page.locator("body").inner_text())

    if (
        "login" in page.url.lower()
        or "تسجيل الدخول" in text
        or "connexion" in text
    ):
        print("Session is not authenticated.")
        return False

    return True


def open_appointment(page):

    print("Searching for application...")

    body = clean(page.locator("body").inner_text())

    target = clean(TARGET_APPLICATION)

    if target not in body:

        # نحاول البحث عن أي زر/بطاقة مرتبطة بالطلب
        print("Target application text was not found.")

        page.screenshot(
            path="application_not_found.png",
            full_page=True
        )

        return False

    print("Application found.")

    # الزر الظاهر في الصورة:
    # المضي قدمًا في اختيار الموعد

    buttons = [
        "text=المضي قدمًا في اختيار الموعد",
        "text=Proceed to appointment selection",
        "text=Proceed",
        "text=Continue",
        "text=Continuer"
    ]

    for selector in buttons:

        try:

            element = page.locator(selector).first

            if element.is_visible():

                print("Appointment selection button found.")

                element.click()

                page.wait_for_load_state(
                    "domcontentloaded",
                    timeout=60000
                )

                time.sleep(3)

                print("Appointment page:", page.url)

                return True

        except Exception as e:
            print("Button attempt failed:", e)

    print("Appointment selection button was not found.")

    page.screenshot(
        path="appointment_button_not_found.png",
        full_page=True
    )

    return False


def check_availability(page):

    print("Checking appointment availability...")

    time.sleep(2)

    text = page.locator("body").inner_text()

    normalized = clean(text)

    # كلمات تدل غالبًا على عدم وجود موعد
    unavailable_words = [
        "no appointment",
        "no appointments",
        "no available",
        "not available",
        "aucun rendez-vous",
        "aucun créneau",
        "لا توجد مواعيد",
        "لا يوجد موعد",
        "غير متاح"
    ]

    for word in unavailable_words:

        if word in normalized:

            print("No appointment currently available.")

            return False

    # البحث عن عناصر مرتبطة بالتاريخ/الوقت
    date_selectors = [
        "input[type='date']",
        "input[type='datetime-local']",
        "select",
        "[class*='calendar' i]",
        "[class*='datepicker' i]",
        "[class*='slot' i]",
        "[class*='appointment' i]"
    ]

    found = []

    for selector in date_selectors:

        try:

            count = page.locator(selector).count()

            if count > 0:

                found.append(
                    f"{selector}: {count}"
                )

        except:
            pass

    print("Appointment-related elements:")

    for item in found:
        print(item)

    # إذا ظهرت عناصر اختيار الموعد نعتبر أن هناك
    # شيئًا يستحق فحصًا يدويًا.
    if found:

        page.screenshot(
            path="appointment_available.png",
            full_page=True
        )

        return True

    return False


def main():

    if not USERNAME or not PASSWORD:

        print("ERROR: BLS_USERNAME / BLS_PASSWORD are missing.")
        return

    print("================================")
    print("BLS APPOINTMENT MONITOR")
    print("================================")

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            viewport={
                "width": 1365,
                "height": 900
            },
            locale="fr-FR"
        )

        page = context.new_page()

        try:

            logged = login(page)

            if not logged:
                telegram(
                    "❌ BLS: Login form could not be detected."
                )
                return

            if not open_manage(page):

                telegram(
                    "❌ BLS: Could not open appointment management."
                )

                return

            if not open_appointment(page):

                print(
                    "Could not reach appointment selection."
                )

                return

            available = check_availability(page)

            if available:

                message = (
                    "🚨 BLS APPOINTMENT CHECK\n\n"
                    "A possible appointment slot/page was detected.\n\n"
                    f"{page.url}\n\n"
                    "Open BLS and verify it manually."
                )

                print(message)

                telegram(message)

            else:

                print(
                    "❌ No appointment detected."
                )

        except PlaywrightTimeoutError as e:

            print("TIMEOUT:", e)

            telegram(
                "⚠️ BLS bot timeout while loading the website."
            )

        except Exception as e:

            print("ERROR:", e)

            telegram(
                "⚠️ BLS bot error:\n" + str(e)[:500]
            )

        finally:

            browser.close()


if __name__ == "__main__":
    main()
