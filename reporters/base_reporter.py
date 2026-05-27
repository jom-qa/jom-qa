from abc import ABC, abstractmethod
from typing import Optional

class BaseBugReporter(ABC):
    """Interface induk untuk sistem modular bug reporting jom-QA."""

    @abstractmethod
    def authenticate(self) -> bool:
        pass

    @abstractmethod
    def create_bug_report(
        self, 
        title: str, 
        description: str, 
        req_id: str, 
        module_name: str, 
        screenshot_path: Optional[str] = None
    ) -> str:
        pass
