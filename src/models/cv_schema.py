from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class LanguageLevel(str, Enum):
    NATIVE      = "Native"
    FLUENT      = "Fluent"
    ADVANCED    = "Advanced"
    INTERMEDIATE = "Intermediate"
    BASIC       = "Basic"


class ContactInfo(BaseModel):
    full_name:  str           = Field(description="Full name of the candidate")
    email:      str           = Field(description="Professional email address")
    phone:      str           = Field(description="Phone number with country code if available")
    location:   Optional[str] = Field(None, description="City and country only, e.g. Dhaka, Bangladesh")
    linkedin:   Optional[str] = Field(None, description="Full LinkedIn profile URL")
    github:     Optional[str] = Field(None, description="Full GitHub profile URL")
    portfolio:  Optional[str] = Field(None, description="Personal website or portfolio URL")


class Experience(BaseModel):
    company:     str       = Field(description="Company or organization name")
    title:       str       = Field(description="Job title or role")
    location:    Optional[str] = Field(None, description="City or Remote")
    start:       str       = Field(description="Start date, e.g. Jan 2021")
    end:         str       = Field(description="End date or Present")
    bullets:     List[str] = Field(description="3 to 5 achievement-focused bullet points. Each must start with a strong action verb. Quantify results where the original CV provides numbers. Never invent metrics.")


class Education(BaseModel):
    institution: str           = Field(description="University or school name")
    degree:      str           = Field(description="Full degree title, e.g. BSc Computer Science")
    location:    Optional[str] = Field(None, description="City and country")
    start:       Optional[str] = Field(None, description="Start year or date")
    end:         str           = Field(description="Graduation year or Expected YYYY")
    grade:       Optional[str] = Field(None, description="GPA, percentage, or grade classification if present in original CV")
    highlights:  List[str]     = Field(default=[], description="Relevant coursework, thesis, or academic achievements if present")


class Certification(BaseModel):
    name:       str           = Field(description="Full certification name")
    issuer:     str           = Field(description="Issuing organization, e.g. AWS, Google, Coursera")
    year:       Optional[str] = Field(None, description="Year obtained")
    url:        Optional[str] = Field(None, description="Verification URL if present in original CV")
    expires:    Optional[str] = Field(None, description="Expiry date if applicable")


class Project(BaseModel):
    name:        str           = Field(description="Project name")
    description: str           = Field(description="2 to 3 sentences. What it does, tech used, your role, and impact if measurable")
    tech_stack:  List[str]     = Field(default=[], description="Technologies, frameworks, and tools used")
    url:         Optional[str] = Field(None, description="Live URL or demo link")
    repo:        Optional[str] = Field(None, description="GitHub or source code URL")
    year:        Optional[str] = Field(None, description="Year built or last updated")


class Language(BaseModel):
    name:  str           = Field(description="Language name")
    level: LanguageLevel = Field(description="Proficiency level")


class Publication(BaseModel):
    title:   str           = Field(description="Full publication title")
    journal: Optional[str] = Field(None, description="Journal, conference, or platform name")
    year:    Optional[str] = Field(None, description="Publication year")
    url:     Optional[str] = Field(None, description="DOI or URL if available")


class VolunteerWork(BaseModel):
    organization: str           = Field(description="Organization name")
    role:         str           = Field(description="Your role or title")
    start:        Optional[str] = Field(None, description="Start date")
    end:          Optional[str] = Field(None, description="End date or Present")
    description:  Optional[str] = Field(None, description="What you did and impact")


class CustomSectionItem(BaseModel):
    label:       Optional[str] = Field(None, description="Short label or year shown on the left")
    description: str           = Field(description="Main content of this item")
    url:         Optional[str] = Field(None, description="URL if relevant")


class CustomSection(BaseModel):
    title: str                    = Field(description="Section heading, e.g. Open Source, Awards, Conferences")
    items: List[CustomSectionItem] = Field(description="Items under this section")


class SkillGroup(BaseModel):
    category: str       = Field(description="Skill category name, e.g. Languages, Frameworks, Cloud, Tools")
    skills:   List[str] = Field(description="List of specific skills in this category")


class CVData(BaseModel):
    contact:         ContactInfo          = Field(description="All contact and personal information")
    summary:         str                  = Field(description="3 to 4 sentences. Tailored to the job description. Highlights years of experience, core strengths, and what the candidate brings to this specific role. Never use first person.")
    experience:      List[Experience]     = Field(description="Work experience in reverse chronological order")
    education:       List[Education]      = Field(description="Education in reverse chronological order")
    skill_groups:    List[SkillGroup]     = Field(description="Skills grouped by category. Always include at least one group.")
    certifications:  List[Certification]  = Field(default=[], description="Only populate if present in the original CV")
    projects:        List[Project]        = Field(default=[], description="Only populate if present in the original CV")
    languages:       List[Language]       = Field(default=[], description="Only populate if present in the original CV")
    publications:    List[Publication]    = Field(default=[], description="Only populate if present in the original CV")
    volunteer:       List[VolunteerWork]  = Field(default=[], description="Only populate if present in the original CV")
    custom_sections: List[CustomSection]  = Field(default=[], description="Any sections in the original CV that do not fit the above categories")
