from playwright.sync_api import sync_playwright

PROFILE_DIR = "./linkedin_profile"

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=False
    )
    page = browser.new_page()
    page.goto("https://www.linkedin.com/login")
    
    input("Login manually then press ENTER...")
    browser.close()
