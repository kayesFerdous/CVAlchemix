from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class BaseTool(ABC):
    """Interface contract for all tools in the system."""

    name: str = "unnamed_tool"
    description: str = "No description provided."

    @abstractmethod
    async def run(self, **kwargs: Any) -> BaseModel:
        """Execute the tool and return a structured result."""
        ...
