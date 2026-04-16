from google.genai import Client, errors
from google.genai.types import GenerateContentConfig, Content, Part

from src.llm.base import BaseLLM
from src.config.settings import settings
from src.models.cv_schema import CVData

class RateLimitError(Exception):
    pass

class GeminiLLM(BaseLLM):
    provider: str = "Gemini"

    def __init__(self, client: Client) -> None:
        self._client = client
        self._model = settings.DEFAULT_MODEL

    async def generate(
        self,
        prompt: str,
        *,
        system: str,
        json_output: bool,
        temperature: float = 0,
    ) -> CVData | str:
        config = GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            response_mime_type="application/json" if json_output else None,
            response_schema=CVData if json_output else None,
        )

        contents = Content(role="user", parts=[Part.from_text(text=prompt)])

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )

            if not response:
                raise ValueError("Empty response from Gemini")

            if json_output:
                if response.parsed is None:
                    raise ValueError("Expected CVData but got no parsed output")
                return response.parsed #type:ignore

            if response.text:
                return response.text

            raise ValueError("No valid response returned")

        except errors.APIError as e:
            if e.code in [429, 503]:
                raise RateLimitError("Rate limit exceeded")
            raise
