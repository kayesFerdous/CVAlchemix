"""
LinkedIn Login Helper

Run this script once to manually log in to LinkedIn.  The session is
persisted in the browser profile directory so subsequent scraper runs
don't need to authenticate.

Usage:
    python login_helper.py
"""

from __future__ import annotations

from playwright.sync_api import sync_playwright

from src.config.settings import settings


def main() -> None:
    """Launch a browser, navigate to LinkedIn login, and wait for the user."""
    print(f"Using profile directory: {settings.PROFILE_DIR}")
    print("A browser window will open. Log in to LinkedIn, then come back here.\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch_persistent_context(
            user_data_dir=settings.PROFILE_DIR,
            headless=False,  # Must be visible for manual login
        )
        page = browser.new_page()
        page.goto("https://www.linkedin.com/login")

        input("✅ Login complete? Press ENTER to save session and close browser...")
        browser.close()

    print("Session saved. You can now run the scraper.")


if __name__ == "__main__":
    main()
