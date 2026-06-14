"""Authentication using persistent browser profile (no cookie files needed)."""
import os
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from config import YOUTUBE_STUDIO_URL

# Use a persistent browser profile directory
PROFILE_DIR = Path(__file__).parent / "browser_profile"
PROFILE_DIR.mkdir(exist_ok=True)


def get_context():
    """Create a browser context using persistent profile and Edge."""
    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        channel="msedge",
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
    )
    return browser, p


def is_logged_in(page) -> bool:
    """Check if we're on the YouTube Studio dashboard (logged in)."""
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
        url = page.url
        # If still on login page, not logged in
        if "accounts.google.com" in url or "signin" in url.lower():
            return False
        # Check for studio elements
        if page.locator("ytcp-dashboard-page").count() > 0:
            return True
        if "studio.youtube.com" in url:
            return True
        return False
    except:
        return False


def login():
    """Open YouTube Studio and let user login manually. Session persists in profile."""
    print("Opening YouTube Studio for login...")
    print("Please login with your Google account in the browser window.")
    print("You have 180 seconds to complete login.")
    print("The browser will close automatically after that.\n")

    context, playwright = get_context()
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(YOUTUBE_STUDIO_URL, wait_until="domcontentloaded")

    import time
    for remaining in range(180, 0, -10):
        print(f"Waiting... {remaining} seconds left")
        time.sleep(10)
        if is_logged_in(page):
            print("Login detected!")
            break

    if is_logged_in(page):
        print("Login successful! Session saved to profile.")
    else:
        print("Login not detected. Session will still be saved in profile.")
        print("Run 'python cli.py login' again to retry.")

    context.close()
    playwright.stop()


if __name__ == "__main__":
    login()