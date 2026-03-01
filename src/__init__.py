"""LingoLearn API Backend Package"""

__version__ = "1.0.0"
__app_name__ = "LingoLearn API"

from src.core.config import settings
from src.agent.agent import get_agent

__all__ = ["settings", "get_agent"]
