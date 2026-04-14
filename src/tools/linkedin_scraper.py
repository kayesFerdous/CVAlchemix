from __future__ import annotations

import logging
from typing import Optional

from playwright.async_api import (
    BrowserContext,
    Page,
    async_playwright,
)
from config.constants import (
    LINKEDIN_JOB_URL_PATTERN,
    SELECTOR_COMPANY_NAME,
    SELECTOR_JOB_DESCRIPTION,
    SELECTOR_JOB_TITLE,
    SELECTOR_LOCATION,
    SELECTOR_SEE_MORE_BUTTON,
)
from config.settings import settings
from models.exceptions import (
    BrowserLaunchError,
    ExtractionError,
    InvalidURLError,
    PageLoadError,
)
from models.schemas import JobPost
from tools.base import BaseTool

logger = logging.getLogger(__name__)


class LinkedInScraperTool(BaseTool):

    name = "linkedin_scraper"
    description = "Extracts title, company, location, and description from a LinkedIn job URL."

    async def run(self, url: str) -> JobPost:  # type: ignore[override]
        self._validate_url(url)

        browser: Optional[BrowserContext] = None
        try:
            browser = await self._launch_browser()
            page = await browser.new_page()
            await self._navigate_to_job(page, url)

            title = await self._extract_text(page, SELECTOR_JOB_TITLE, "title")
            company = await self._extract_text(page, SELECTOR_COMPANY_NAME, "company")
            location = await self._extract_location(page)
            description = await self._extract_description(page)

            job = JobPost(
                url=url,
                title=title,
                company=company,
                location=location,
                description=description,
            )
            logger.info("Successfully scraped job: %s at %s", title, company)
            return job

        except (InvalidURLError, BrowserLaunchError, PageLoadError, ExtractionError):
            raise  # re-raise known exceptions as-is
        except Exception as exc:
            logger.error("Unexpected error while scraping %s: %s", url, exc)
            raise PageLoadError(f"Failed to scrape {url}") from exc
        finally:
            if browser is not None:
                await browser.close()
                logger.debug("Browser closed.")

    # --------------------------------------------------------------------- #
    #  Private helpers                                                       #
    # --------------------------------------------------------------------- #

    @staticmethod
    def _validate_url(url: str) -> None:
        if not LINKEDIN_JOB_URL_PATTERN.match(url):
            raise InvalidURLError(
                f"Expected a LinkedIn job URL (https://www.linkedin.com/jobs/...), "
                f"got: {url}"
            )

    @staticmethod
    async def _launch_browser() -> BrowserContext:
        """Start a persistent Chromium context."""
        try:
            pw = await async_playwright().start()
            browser = await pw.chromium.launch_persistent_context(
                user_data_dir=settings.PROFILE_DIR,
                headless=settings.BROWSER_HEADLESS,
            )
            logger.debug("Browser launched (headless=%s).", settings.BROWSER_HEADLESS)
            return browser
        except Exception as exc:
            raise BrowserLaunchError(f"Could not launch browser: {exc}") from exc

    @staticmethod
    async def _navigate_to_job(page: Page, url: str) -> None:
        """Navigate to the job URL and wait for the title selector."""
        try:
            logger.info("Navigating to %s", url)
            await page.goto(url)
            await page.wait_for_selector(
                SELECTOR_JOB_TITLE,
                timeout=settings.SCRAPE_TIMEOUT_MS,
            )
            # Allow dynamic content to settle
            await page.wait_for_timeout(2000)
        except Exception as exc:
            raise PageLoadError(
                f"Page did not load within {settings.SCRAPE_TIMEOUT_MS}ms: {exc}"
            ) from exc

    @staticmethod
    async def _extract_text(
        page: Page, selector: str, field_name: str
    ) -> Optional[str]:
        """Extract and strip inner text from a single selector."""
        try:
            text = await page.inner_text(selector)
            return text.strip() if text else None
        except Exception as exc:
            logger.warning("Could not extract %s: %s", field_name, exc)
            return None

    @staticmethod
    async def _extract_location(page: Page) -> Optional[str]:
        """Extract location from the first matching span."""
        try:
            locator = page.locator(SELECTOR_LOCATION).first
            text = await locator.inner_text()
            return text.strip() if text else None
        except Exception as exc:
            logger.warning("Could not extract location: %s", exc)
            return None

    @staticmethod
    async def _extract_description(page: Page) -> Optional[str]:
        """Expand the 'See more' section (if present) and extract the description."""
        try:
            see_more = await page.query_selector(SELECTOR_SEE_MORE_BUTTON)
            if see_more:
                await see_more.click()
                await page.wait_for_timeout(1000)

            text = await page.inner_text(SELECTOR_JOB_DESCRIPTION)
            return text.strip() if text else None
        except Exception as exc:
            logger.warning("Could not extract description: %s", exc)
            return None
