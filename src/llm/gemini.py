from google.genai import Client, errors
from google.genai.types import GenerateContentConfig, Content, Part

from llm.base import BaseLLM
from config.settings import settings
from models.cv_schema import CVData

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
    ) -> str | CVData | None:
        config = GenerateContentConfig(
            system_instruction = system or None,
            temperature = temperature,
            response_mime_type = "application/json" if json_output else None,
            response_schema = CVData if json_output else None,
        )
        contents = Content(role="user", parts=[Part.from_text(text=prompt)])

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents=contents,
                config=config,
            )

            if response and response.text:
                if json_output:
                    clean_json = response.text.strip().removeprefix("```json").removesuffix("```").strip()
                    return CVData.model_validate_json(clean_json)
                return response.text

            return None

        except errors.APIError as e:
            if e.code in [429, 503]:
                raise RateLimitError("Rate limit exceeded")
        
