import asyncio
import logging
from google.genai import Client

from src.config.logging import setup_logging
from src.config.settings import settings
from src.llm.gemini import GeminiLLM
from src.agents.job_application_agnet import JobApplicationAgent

logger = logging.getLogger(__name__)


async def run():
    client = Client(api_key=settings.GOOGLE_API_KEY)
    llm = GeminiLLM(client)
    output_pdf = ""

    agent = JobApplicationAgent(llm)
    url = input("enter the url: ")
    response = await agent.run(url, output_path=output_pdf)
    print(response)

def main():
    setup_logging(level=settings.LOG_LEVEL)
    asyncio.run(run())


if __name__ == "__main__":
    main()

