from abc import ABC, abstractmethod

class BaseLLM(ABC):
    provider: str = "no_provider"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        temperature: float = 0,
    ) -> str | None:
        """Return a plain-text completion."""
        ...
