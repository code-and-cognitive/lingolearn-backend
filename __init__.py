"""LingoLearn API Backend Package"""

__version__ = "1.0.0"
__app_name__ = "LingoLearn API"

from config import settings
from agent import get_agent

__all__ = ["settings", "get_agent"]
