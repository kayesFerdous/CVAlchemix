from abc import ABC, abstractmethod

from models.cv_schema import CVData

class BaseLLM(ABC):
    provider: str = "no_provider"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str,
        json_output: bool,
        temperature: float = 0,
    ) -> str | CVData| None:
        """Return a plain-text completion."""
        ...
