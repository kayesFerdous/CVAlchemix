# """
# Browse — LinkedIn Job Scraper CLI

# Usage:
#     python main.py <linkedin-job-url>
#     python main.py https://www.linkedin.com/jobs/view/123456789
# """

# from __future__ import annotations

# import argparse
# import asyncio
# import logging
# import sys

# from config.logging import setup_logging
# from config.settings import settings
# from models.exceptions import ScraperError
# from tools.linkedin_scraper import LinkedInScraperTool

# logger = logging.getLogger(__name__)


# def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
#     """Parse command-line arguments."""
#     parser = argparse.ArgumentParser(
#         prog="browse",
#         description="Scrape job details from a LinkedIn job posting URL.",
#     )
#     parser.add_argument(
#         "url",
#         help="LinkedIn job URL (e.g. https://www.linkedin.com/jobs/view/123456789)",
#     )
#     return parser.parse_args(argv)


# async def scrape_job(url: str) -> None:
#     """Run the LinkedIn scraper and log results."""
#     scraper = LinkedInScraperTool()
#     job = await scraper.run(url)

#     logger.info("=" * 60)
#     logger.info("Title:       %s", job.title or "(not found)")
#     logger.info("Company:     %s", job.company or "(not found)")
#     logger.info("Location:    %s", job.location or "(not found)")
#     logger.info("-" * 60)

#     if job.description:
#         # Log first 500 chars to keep console output manageable
#         preview = job.description[:500]
#         logger.info("Description:\n%s", preview)
#         if len(job.description) > 500:
#             logger.info("... (%d more characters)", len(job.description) - 500)
#     else:
#         logger.info("Description: (not found)")

#     logger.info("=" * 60)


# def main(argv: list[str] | None = None) -> None:
#     """CLI entry point."""
#     setup_logging(level=settings.LOG_LEVEL)
#     args = parse_args(argv)

#     try:
#         asyncio.run(scrape_job(args.url))
#     except ScraperError as exc:
#         logger.error("Scraping failed: %s", exc)
#         sys.exit(1)
#     except KeyboardInterrupt:
#         logger.info("Aborted by user.")
#         sys.exit(130)

import asyncio
import logging
from google.genai import Client

from config.logging import setup_logging
from config.settings import settings
# from models.exceptions import ScraperError
from src.models.cv_schema import ContactInfo, Education, Experience, Project, SkillGroup
from src.models.cv_schema import CVData
from tools.linkedin_scraper import LinkedInScraperTool
from llm.gemini import GeminiLLM
from src.agents.job_application_agnet import JobApplicationAgent
from src.tools.latex_renderer import LatexRenderer

logger = logging.getLogger(__name__)

cv_instance = CVData(
    contact=ContactInfo(
        full_name="Fardows Alam Kayes",
        email="kayesfardows@gmail.com",
        phone="+880-01560-065127",
        location="Narayanganj, Dhaka, Bangladesh",
        github="https://github.com/fardows-kayes",
        portfolio="https://kayees.me",
        linkedin="https://linkedin.com/profile/kayesfardows"
    ),
    summary=(
        "AI Developer with a strong foundation in Machine Learning and Natural Language Processing. "
        "Proficient in the Python ecosystem and specialized in building RAG applications and chatbots "
        "using frameworks like FastAPI, LangChain, and LangGraph. Experienced in backend architecture "
        "and containerized deployments, delivering scalable solutions for real-world challenges."
    ),
    experience=[
        Experience(
            company="Green University of Bangladesh",
            title="Undergraduate Researcher",
            location="Narayanganj, Bangladesh",
            start="2024",
            end="Present",
            bullets=[
                "Conducting undergraduate thesis research on 'Researcher Profiling' under the supervision of Prof. Dr. Md. Saiful Azad.",
                "Developed methodologies for automated author data extraction and profiling using NLP techniques.",
                "Collaborating with academic faculty to refine data processing pipelines for research publication analysis."
            ]
        ),
        Experience(
            company="HackTheAI Hackathon",
            title="Team Leader",
            location="Dhaka, Bangladesh",
            start="Sep 2025",
            end="Sep 2025",
            bullets=[
                "Led a development team to secure 1st rank within Green University and 13th overall in national preliminaries.",
                "Architected a functional AI prototype under strict time constraints, finishing in the Top 50 of 250 participating teams.",
                "Managed end-to-end project workflow, from initial ideation to the final technical presentation."
            ]
        ),
        Experience(
            company="GUB Competitive Programming Community (GUBCPC)",
            title="Club Member & Designer",
            location="Narayanganj, Bangladesh",
            start="Nov 2025",
            end="Present",
            bullets=[
                "Handled development-related tasks and visual design assets to support community operations and events.",
                "Collaborated with the core team to organize programming contests and technical workshops for 100+ students.",
                "Streamlined internal club workflows through the implementation of digital tools and automation."
            ]
        )
    ],
    education=[
        Education(
            start="2022",
            institution="Green University of Bangladesh",
            degree="B.Sc. in Computer Science and Engineering",
            location="Dhaka, Bangladesh",
            end="2026",
            highlights=["Thesis: Researcher Profiling using AI"],
            grade=None
        ),
        Education(
            start="2019",
            institution="Giasuddin Islamic Model College",
            degree="Higher Secondary Certificate (HSC)",
            location="Narayanganj, Bangladesh",
            end="2020",
            grade="4.83/5.0"
        )
    ],
    skill_groups=[
        SkillGroup(category="Backend Development", skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "Node.js"]),
        SkillGroup(category="AI & ML", skills=["RAG Pipelines", "LangChain", "LangGraph", "ChromaDB", "Qdrant", "Ollama"]),
        SkillGroup(category="Frontend", skills=["Next.js", "TypeScript", "Tailwind CSS"]),
        SkillGroup(category="DevOps & Tools", skills=["Arch Linux", "Docker", "Neovim", "Git", "tmux"])
    ],
    projects=[
        Project(
            url=None,
            year=None,
            name="AskMyPDF",
            description="A RAG-powered chatbot allowing users to query PDF documents. Features vector-based document parsing and context-aware response generation.",
            tech_stack=["Python", "FastAPI", "LangChain", "Groq API"],
            repo="https://github.com/fardows-kayes/AskMyPDF"
        ),
        Project(
            url=None,
            year=None,
            name="Google Calendar MCP Server",
            description="Implemented a Model Context Protocol server to bridge AI agents with Google Calendar for automated event management.",
            tech_stack=["Python", "Gemini CLI", "Google API"],
            repo="https://github.com/fardows-kayes/calendar-mcp"
        ),
        Project(
            url=None,
            year=None,
            name="Blab-10",
            description="Real-time chat platform with private room approval workflows and modern neobrutalist UI elements.",
            tech_stack=["Next.js", "TypeScript", "Tailwind CSS"],
            repo="https://github.com/fardows-kayes/blab-10"
        )
    ]
)

async def run():
    client = Client(api_key=settings.GOOGLE_API_KEY)
    llm = GeminiLLM(client)

    agent = JobApplicationAgent(llm)
    url = input("enter the url: ")
    response = await agent.run(url)

    if not response:
        logger.error("Agent returned no CV data — nothing to render.")
        return

    logger.info("CV data received (%s). Starting PDF generation …", type(response).__name__)

    renderer = LatexRenderer("/home/kayes/new_world/python/browse/templates")
    output_pdf = "output.pdf"

    try:
        pdf_path = renderer.run(
            data=response.model_dump(exclude_none=True),
            output_path=output_pdf,
        )
        print(f"\nPDF generated successfully: {pdf_path}")
    except ValueError as exc:
        logger.error("Data validation failed: %s", exc)
        print(f"\nCV data is invalid: {exc}")
    except RuntimeError as exc:
        logger.error("Rendering / compilation failed: %s", exc)
        print(f"\nPDF generation failed: {exc}")
        print("   Check the intermediate .tex file for details.")


def main():
    setup_logging(level=settings.LOG_LEVEL)
    asyncio.run(run())


if __name__ == "__main__":
    main()

