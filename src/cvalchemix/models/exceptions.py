class ScraperError(Exception):
    """Base exception for all scraper-related errors."""


class InvalidURLError(ScraperError):
    """Raised when the provided URL is not a valid LinkedIn job URL."""


class BrowserLaunchError(ScraperError):
    """Raised when the browser fails to start."""


class PageLoadError(ScraperError):
    """Raised when a page fails to load or a required selector is missing."""


class ExtractionError(ScraperError):
    """Raised when a specific field cannot be extracted from the page."""
