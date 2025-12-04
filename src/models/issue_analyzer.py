from pydantic import BaseModel
from enum import Enum

class Complexity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
        
class IssueAnalyzer(BaseModel):
    """Information about an issue."""
    reason: str | None = None
    complexity: Complexity | None = None