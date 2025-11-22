"""
Tool Manager - Manages and coordinates all agent tools.
"""
from typing import List, Dict, Any, Optional
from workflows.tools.base_tool import BaseTool
from workflows.tools.web_search_tool import web_search_tool
from workflows.tools.calculator_tool import calculator_tool
from workflows.tools.database_query_tool import database_query_tool
import sys


class ToolManager:
    """Manages all available tools for agents."""
    
    def __init__(self):
        """Initialize tool manager with all available tools."""
        self.tools: Dict[str, BaseTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools."""
        # Register web search (if available)
        if web_search_tool._searcher or (web_search_tool.provider == "google" and web_search_tool.api_key and web_search_tool.engine_id):
            self.tools["web_search"] = web_search_tool
        
        # Register calculator (always available)
        self.tools["calculator"] = calculator_tool
        
        # Register database query (always available)
        self.tools["database_query"] = database_query_tool
        
        available_tools = list(self.tools.keys())
        print(f"[OK] Tool Manager initialized - Available tools: {', '.join(available_tools)}", file=sys.stderr, flush=True)
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """List all available tool names."""
        return list(self.tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools (for LLM function calling)."""
        return [tool.get_schema() for tool in self.tools.values()]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool
            **kwargs: Tool parameters
        
        Returns:
            ToolResult
        """
        tool = self.get_tool(tool_name)
        if not tool:
            from workflows.tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                result=None,
                error=f"Tool not found: {tool_name}"
            )
        
        return tool.execute(**kwargs)


# Global instance
tool_manager = ToolManager()

