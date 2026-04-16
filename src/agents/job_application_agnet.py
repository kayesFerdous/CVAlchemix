from pathlib import Path
from datetime import datetime

from test2 import cv
from llm.base import BaseLLM
from config.logging import logging
from models.schemas import JobPost
from models.cv_schema import CVData
from tools.latex_renderer import LatexRenderer
from tools.linkedin_scraper import LinkedInScraperTool
from prompts.cv_rewrite_prompt import get_system_prompt, get_user_prompt_template


logger = logging.getLogger(__name__)

class JobApplicationAgent:
    def __init__(self, llm: BaseLLM) -> None:
        self._llm = llm
        self._system_prompt = get_system_prompt()
        self._scraper = LinkedInScraperTool()
        self._renderer = LatexRenderer()

    async def run(self, job_url: str, output_path: str) -> str | None:
        job_post: JobPost = await self._scraper.run(job_url)

        job_description = f"""
        Job Title: {job_post.title}

        Company: {job_post.company}

        Location: {job_post.location}

        Job Description : {job_post.description}
        """

        user_prompt = get_user_prompt_template(job_description, cv_text=cv)

        response: CVData = await self._llm.generate( #type:ignore
            prompt=user_prompt,
            system=self._system_prompt,
            json_output=True,
        )
        data = response.model_dump(exclude_none=True)

        now = datetime.now()
        date_time = f"{now:%Y-%m-%d}_{now.hour}_{now:%M}"
        company_name = job_post.company or "unknown_company"
        company_slug = "_".join(company_name.split())

        base_output_path = Path(output_path) if output_path else Path(".")
        output_file = base_output_path / "cv" / f"{company_slug}_{date_time}" / "cv.pdf"

        try:
            pdf = self._renderer.run(data, output_path=str(output_file))
            print(f"\nPDF generated successfully: {pdf}")
            return pdf
        except ValueError as exc:
            logger.error("Data validation failed: %s", exc)
            print(f"\nCV data is invalid: {exc}")
        except RuntimeError as exc:
            logger.error("Rendering / compilation failed: %s", exc)
            print(f"\nPDF generation failed: {exc}")
            print("   Check the intermediate .tex file for details.")
        return None
