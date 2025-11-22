"""
Web search tool for agents using DuckDuckGo, SerpAPI, or Google Custom Search API.
"""
from typing import Any, Dict, Optional
from workflows.tools.base_tool import BaseTool, ToolResult
import sys


class WebSearchTool(BaseTool):
    """Tool for web search using DuckDuckGo (free), SerpAPI, or Google Custom Search API."""
    
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None, engine_id: Optional[str] = None):
        """
        Initialize web search tool.
        
        Args:
            provider: "duckduckgo", "serpapi", or "google". If None, uses config.
            api_key: API key for SerpAPI or Google Search. If None, uses config.
            engine_id: Custom Search Engine ID for Google Search. If None, uses config.
        """
        from utils.config import settings
        
        super().__init__(
            name="web_search",
            description="Search the web for current information, facts, news, or research"
        )
        self.provider = (provider or getattr(settings, 'WEB_SEARCH_PROVIDER', 'duckduckgo')).lower()
        self.api_key = api_key or getattr(settings, 'GOOGLE_SEARCH_API_KEY', None) or getattr(settings, 'SERPAPI_API_KEY', None)
        self.engine_id = engine_id or getattr(settings, 'GOOGLE_SEARCH_ENGINE_ID', None)
        self._searcher = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the search provider."""
        try:
            # Try Google Custom Search API first if configured
            if self.provider == "google" and self.api_key and self.engine_id:
                try:
                    # Google Custom Search API uses requests directly
                    import requests
                    self._searcher = "google"
                    print("[OK] Web Search Tool initialized: Google Custom Search API", file=sys.stderr, flush=True)
                    return
                except ImportError:
                    print("[WARNING] requests not installed. Install with: pip install requests", file=sys.stderr, flush=True)
            
            # Try SerpAPI if configured
            if self.provider == "serpapi" and self.api_key:
                try:
                    from serpapi import GoogleSearch
                    self._searcher = GoogleSearch
                    print("[OK] Web Search Tool initialized: SerpAPI", file=sys.stderr, flush=True)
                    return
                except ImportError:
                    print("[WARNING] serpapi not installed. Install with: pip install google-search-results", file=sys.stderr, flush=True)
            
            # Default to DuckDuckGo (free)
            try:
                from duckduckgo_search import DDGS
                self._searcher = DDGS
                self.provider = "duckduckgo"
                print("[OK] Web Search Tool initialized: DuckDuckGo", file=sys.stderr, flush=True)
            except ImportError:
                print("[WARNING] duckduckgo_search not installed. Install with: pip install duckduckgo-search", file=sys.stderr, flush=True)
                self._searcher = None
        except Exception as e:
            print(f"[WARNING] Web search initialization failed: {e}", file=sys.stderr, flush=True)
            self._searcher = None
    
    def execute(self, query: str, max_results: int = 5) -> ToolResult:
        """
        Execute web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
        
        Returns:
            ToolResult with search results
        """
        if not self._searcher:
            return ToolResult(
                success=False,
                result=None,
                error="Web search not available. Install duckduckgo-search or serpapi."
            )
        
        try:
            if self.provider == "google" and self._searcher == "google":
                results = self._search_google(query, max_results)
            elif self.provider == "serpapi":
                results = self._search_serpapi(query, max_results)
            else:
                results = self._search_duckduckgo(query, max_results)
            
            return ToolResult(
                success=True,
                result=results,
                metadata={"provider": self.provider, "query": query}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                result=None,
                error=f"Web search failed: {str(e)}"
            )
    
    def _search_duckduckgo(self, query: str, max_results: int) -> list:
        """Search using DuckDuckGo."""
        results = []
        with self._searcher() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("href", ""),
                    "snippet": result.get("body", "")
                })
        return results
    
    def _search_google(self, query: str, max_results: int) -> list:
        """Search using Google Custom Search API."""
        import requests
        
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.engine_id,
            "q": query,
            "num": min(max_results, 10)  # Google API max is 10 per request
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            items = data.get("items", [])
            for item in items[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return results
        except Exception as e:
            raise Exception(f"Google Search API error: {str(e)}")
    
    def _search_serpapi(self, query: str, max_results: int) -> list:
        """Search using SerpAPI."""
        search = self._searcher({
            "q": query,
            "api_key": self.api_key,
            "num": max_results
        })
        
        results = []
        organic_results = search.get("organic_results", [])
        for result in organic_results[:max_results]:
            results.append({
                "title": result.get("title", ""),
                "url": result.get("link", ""),
                "snippet": result.get("snippet", "")
            })
        return results
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get JSON schema for parameters."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }


# Global instance
web_search_tool = WebSearchTool()

