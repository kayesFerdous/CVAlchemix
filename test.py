from playwright.sync_api import sync_playwright

PROFILE_DIR = "./linkedin_profile"


def extract_job_details(job_url: str):
    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False
        )

        page = browser.new_page()
        page.goto(job_url)

        # Better wait (instead of sleep)
        page.wait_for_load_state("networkidle")

        # Wait for main container
        try:
            page.wait_for_selector(
                ".job-details-jobs-unified-top-card",
                timeout=15000
            )
        except:
            print("⚠️ Job page not fully loaded")

        # ---------------------------
        # Title
        # ---------------------------
        try:
            title = page.locator(
                ".job-details-jobs-unified-top-card__job-title"
            ).inner_text().strip()
        except:
            title = "Not found"

        # ---------------------------
        # Company
        # ---------------------------
        try:
            company = page.locator(
                ".job-details-jobs-unified-top-card__company-name"
            ).inner_text().strip()
        except:
            company = "Not found"

        # ---------------------------
        # Location (robust)
        # ---------------------------
        try:
            bullets = page.locator(
                ".job-details-jobs-unified-top-card__primary-description-container span"
            ).all_inner_texts()

            # DEBUG (optional)
            print("DEBUG bullets:", bullets)

            # Try to detect location
            location = "Not found"
            for text in bullets:
                if "," in text:  # e.g. "Dhaka, Bangladesh"
                    location = text
                    break

            # fallback → first item
            if location == "Not found" and bullets:
                location = bullets[0]

        except:
            location = "Not found"

        # ---------------------------
        # Description
        # ---------------------------
        try:
            # Expand "See more" if exists
            see_more = page.locator(
                "button[aria-label*='see more']"
            )

            if see_more.count() > 0:
                see_more.first.click()

            description = page.locator(
                ".jobs-description__content"
            ).inner_text().strip()

        except:
            description = "Not found"

        browser.close()

        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description
        }


# ---------------------------
# TEST
# ---------------------------
if __name__ == "__main__":
    job_url = "https://www.linkedin.com/jobs/view/4397820709/"

    job = extract_job_details(job_url)

    print("\n====== RESULT ======")
    print("Title:", job["title"])
    print("Company:", job["company"])
    print("Location:", job["location"])
    print("Description:\n", job["description"][:500])
