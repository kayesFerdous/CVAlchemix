import re

# ---------------------------------------------------------------------------
# LinkedIn Job Page CSS Selectors
# ---------------------------------------------------------------------------

SELECTOR_JOB_TITLE: str = ".job-details-jobs-unified-top-card__job-title"
SELECTOR_COMPANY_NAME: str = ".job-details-jobs-unified-top-card__company-name"
SELECTOR_LOCATION: str = (
    ".job-details-jobs-unified-top-card__primary-description-container span"
)
SELECTOR_SEE_MORE_BUTTON: str = (
    "button[aria-label='Click to see more description']"
)
SELECTOR_JOB_DESCRIPTION: str = ".jobs-description__content"

# ---------------------------------------------------------------------------
# URL Validation
# ---------------------------------------------------------------------------

LINKEDIN_JOB_URL_PATTERN: re.Pattern[str] = re.compile(
    r"^https?://(www\.)?linkedin\.com/jobs/view/\d+",
    re.IGNORECASE,
)
