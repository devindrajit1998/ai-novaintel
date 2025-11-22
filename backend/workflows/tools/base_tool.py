"""
Base tool interface for agent tools.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool = Field(description="Whether tool execution succeeded")
    result: Any = Field(description="Tool execution result")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class BaseTool(ABC):
    """Base class for all agent tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get JSON schema for tool parameters."""
        pass

