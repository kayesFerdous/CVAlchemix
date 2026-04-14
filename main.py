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
from tools.linkedin_scraper import LinkedInScraperTool
from llm.gemini import GeminiLLM
from agents.job_application_agnet import JobApplicationAgent

logger = logging.getLogger(__name__)

async def run():
    client = Client(api_key=settings.GOOGLE_API_KEY)
    llm = GeminiLLM(client)

    agent = JobApplicationAgent(llm)
    url = input("enter the url: ")
    response = await agent.run(url)

    # llm = GeminiLLM(client)
    # 
    # prompt = input("user input: ")
    # system = "just repeat the word"
    #
    # response = await llm.generate(prompt, system=system)
    print(response)



def main():
    # setup_logging(settings.LOG_LEVEL)
    # tool = LinkedInScraperTool()

    # url = input("Enter the url: ")
    asyncio.run(run())

if __name__ == "__main__":
    main()

