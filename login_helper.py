"""
LinkedIn Login Helper

Run this script once to manually log in to LinkedIn.  The session is
persisted in the browser profile directory so subsequent scraper runs
don't need to authenticate.

Usage:
    python login_helper.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from cvalchemix.config.settings import settings


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
