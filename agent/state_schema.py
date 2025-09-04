from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class VirtualBAState(BaseModel):
    """Custom state schema for Virtual BA workflow."""
    
    user_input: str = ""
    process_report: Dict[str, Any] = {}
    conversation_history: List[Dict[str, str]] = []
    route: Optional[str] = None
    calculated_metrics: Dict[str, Any] = {}
    advisory_recommendations: List[str] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary format expected by tools."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VirtualBAState':
        """Create state from dictionary."""
        return cls(**data) 