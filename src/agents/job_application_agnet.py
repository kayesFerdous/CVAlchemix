import asyncio
from pathlib import Path
from datetime import datetime

from config.ui import console
from llm.base import BaseLLM
from config.logging import logging
from models.schemas import JobPost
from models.cv_schema import CVData
from tools.latex_renderer import LatexRenderer
from tools.linkedin_scraper import LinkedInScraperTool
from prompts.cv_rewrite_prompt import get_system_prompt, get_user_prompt_template

logger = logging.getLogger(__name__)

class JobApplicationAgent:
    def __init__(self, llm: BaseLLM, cv: str) -> None:
        self._llm = llm
        self.cv = cv
        self._system_prompt = get_system_prompt()
        self._scraper = LinkedInScraperTool()
        self._renderer = LatexRenderer()

    async def run(self, job_url: str, output_path: str) -> str | None:
        # Step 1: Scrape job post
        with console.status("[bold cyan]Step 1/3:[/bold cyan] Scraping job posting from LinkedIn..."):
            job_post: JobPost = await self._scraper.run(job_url)
        console.print(f"[green]✔[/green] Scraped: [bold]{job_post.title}[/bold] at {job_post.company}")

        job_description = f"""
        Job Title: {job_post.title}

        Company: {job_post.company}

        Location: {job_post.location}

        Job Description : {job_post.description}
        """

        user_prompt = get_user_prompt_template(job_description, cv_text=self.cv)

        # Step 2: Generate tailored CV via LLM
        with console.status("[bold cyan]Step 2/3:[/bold cyan] Generating tailored CV with AI (this may take up to 60s)..."):
            try:
                response: CVData = await asyncio.wait_for(
                    self._llm.generate( #type:ignore
                        prompt=user_prompt,
                        system=self._system_prompt,
                        json_output=True,
                    ),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                console.print("[red]✗[/red] LLM request timed out after 120 seconds.")
                raise RuntimeError("LLM generation timed out. Try again or check your API key / model.")
        console.print("[green]✔[/green] AI-generated CV received")

        data = response.model_dump(exclude_none=True)

        now = datetime.now()
        date_time = f"{now:%Y-%m-%d}_{now.hour}_{now:%M}"
        company_name = job_post.company or "unknown_company"
        company_slug = "_".join(company_name.split())

        base_output_path = Path(output_path) if output_path else Path(".")
        output_file = base_output_path / "cv" / f"{company_slug}_{date_time}" / "cv.pdf"

        # Step 3: Render PDF
        with console.status("[bold cyan]Step 3/3:[/bold cyan] Rendering PDF..."):
            try:
                pdf = self._renderer.run(data, output_path=str(output_file))
            except ValueError as exc:
                logger.error("Data validation failed: %s", exc)
                console.print(f"[red]✗ CV data is invalid:[/red] {exc}")
                return None
            except RuntimeError as exc:
                logger.error("Rendering / compilation failed: %s", exc)
                console.print(f"[red]✗ PDF generation failed:[/red] {exc}")
                console.print("   Check the intermediate .tex file for details.")
                return None

        return pdf
