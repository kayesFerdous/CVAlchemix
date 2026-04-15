from llm.base import BaseLLM
from models.schemas import JobPost
from tools.linkedin_scraper import LinkedInScraperTool
from prompts.cv_rewrite_prompt import get_system_prompt, get_user_prompt_template

class JobApplicationAgent:
    def __init__(self, llm: BaseLLM) -> None:
        self._llm = llm
        self._scraper = LinkedInScraperTool()
        self._system_prompt = get_system_prompt()

    async def run(self, job_url: str) -> str:
        job_post: JobPost = await self._scraper.run(job_url)

        job_description = f"""
        Job Title: {job_post.title}


        Company: {job_post.company}


        Location: {job_post.location}


        Job Description : {job_post.description}
        """


        cv = "CV goes there" #TODO: load the saved cv

        user_prompt = get_user_prompt_template(job_description, cv_text=cv)
        response = await self._llm.generate(
            prompt=user_prompt,
            system=self._system_prompt
        )
        if response:
            return response
        else:
            return "there was an error"
