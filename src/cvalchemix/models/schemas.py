"""
Pydantic models for structured data flowing through the application.
"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel


class JobPost(BaseModel):
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    scraped_at: datetime = datetime.now(timezone.utc)


class CVData(BaseModel):
    """Raw CV text split into labelled sections."""

    raw_text: str
    sections: dict[str, str]  # e.g. {"experience": "...", "skills": "..."}


class AnalysisResult(BaseModel):
    """Output of the CV-vs-job-post gap analysis."""

    missing_skills: list[str]
    weak_areas: list[str]
    suggestions: list[str]
    tailored_cv: str
