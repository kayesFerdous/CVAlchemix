from config.logging import logging
from llm.base import BaseLLM
from models.schemas import JobPost
from models.cv_schema import CVData
from tools.latex_renderer import LatexRenderer
from tools.linkedin_scraper import LinkedInScraperTool
from prompts.cv_rewrite_prompt import get_system_prompt, get_user_prompt_template
from test2 import cv


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
        output_file = output_path+"cv/cv_"+job_post.company.replace(" ", "_")+".pdf" #type:ignore

        try:
            pdf = self._renderer.run(data, output_path=output_file)
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
