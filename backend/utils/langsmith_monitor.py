"""
LangSmith monitoring integration for LLM call tracking, prompt versioning, and cost tracking.
"""
from typing import Optional, Dict, Any
from utils.config import settings
import sys
import os


class LangSmithMonitor:
    """Monitor LLM calls using LangSmith."""
    
    def __init__(self):
        """Initialize LangSmith monitoring."""
        self.enabled = False
        self._initialize()
    
    def _initialize(self):
        """Initialize LangSmith if configured."""
        try:
            # Check for LangSmith API key
            langsmith_api_key = os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY")
            langsmith_tracing = os.getenv("LANGCHAIN_TRACING_V2", "false").lower()
            
            if langsmith_api_key and langsmith_tracing == "true":
                # Set environment variables for LangChain
                os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
                os.environ["LANGCHAIN_TRACING_V2"] = "true"
                os.environ["LANGCHAIN_ENDPOINT"] = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
                os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "novaintel")
                
                # Enable monitoring
                self.enabled = True
                print("[OK] LangSmith monitoring enabled", file=sys.stderr, flush=True)
                print(f"   Project: {os.getenv('LANGCHAIN_PROJECT', 'novaintel')}", file=sys.stderr, flush=True)
                print(f"   Endpoint: {os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')}", file=sys.stderr, flush=True)
            else:
                self.enabled = False
                if langsmith_api_key:
                    print("[INFO] LangSmith API key found but tracing not enabled", file=sys.stderr, flush=True)
                    print("   Set LANGCHAIN_TRACING_V2=true to enable monitoring", file=sys.stderr, flush=True)
                else:
                    print("[INFO] LangSmith monitoring not configured", file=sys.stderr, flush=True)
                    print("   Set LANGCHAIN_API_KEY and LANGCHAIN_TRACING_V2=true to enable", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[WARNING] LangSmith initialization failed: {e}", file=sys.stderr, flush=True)
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if LangSmith monitoring is enabled."""
        return self.enabled
    
    def track_prompt(
        self,
        prompt_name: str,
        prompt_version: str,
        prompt_template: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a prompt template for versioning.
        
        Args:
            prompt_name: Name of the prompt (e.g., "rfp_analyzer")
            prompt_version: Version string (e.g., "v1.0")
            prompt_template: The prompt template text
            metadata: Optional metadata
        """
        if not self.enabled:
            return
        
        try:
            # LangSmith automatically tracks prompts when used with LangChain
            # Store prompt metadata for reference
            prompt_key = f"{prompt_name}:{prompt_version}"
            # This is tracked automatically when using LangChain's ChatPromptTemplate
            pass
        except Exception as e:
            print(f"[WARNING] Failed to track prompt: {e}", file=sys.stderr, flush=True)
    
    def set_run_name(self, name: str):
        """Set the run name for current trace."""
        if not self.enabled:
            return
        
        try:
            # Set run name via environment or context
            os.environ["LANGCHAIN_RUN_NAME"] = name
        except Exception as e:
            print(f"[WARNING] Failed to set run name: {e}", file=sys.stderr, flush=True)
    
    def set_tags(self, tags: list):
        """Set tags for current trace."""
        if not self.enabled:
            return
        
        try:
            # Set tags via environment
            if tags:
                os.environ["LANGCHAIN_TAGS"] = ",".join(tags)
        except Exception as e:
            print(f"[WARNING] Failed to set tags: {e}", file=sys.stderr, flush=True)
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Set metadata for current trace."""
        if not self.enabled:
            return
        
        try:
            # LangSmith tracks metadata automatically with LangChain
            # Store in environment for context
            for key, value in metadata.items():
                env_key = f"LANGCHAIN_METADATA_{key.upper()}"
                os.environ[env_key] = str(value)
        except Exception as e:
            print(f"[WARNING] Failed to set metadata: {e}", file=sys.stderr, flush=True)
    
    def get_cost_estimate(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Optional[float]:
        """
        Estimate cost based on token usage.
        
        Args:
            provider: LLM provider ("openai", "anthropic", "google")
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        
        Returns:
            Estimated cost in USD
        """
        # Cost per 1M tokens (as of 2024)
        cost_estimates = {
            "openai": {
                "gpt-4o": {"input": 2.50, "output": 10.00},  # per 1M tokens
                "gpt-4": {"input": 30.00, "output": 60.00},
                "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
                "claude-3-opus": {"input": 15.00, "output": 75.00},
                "claude-3-sonnet": {"input": 3.00, "output": 15.00},
            },
            "google": {
                "gemini-2.0-flash": {"input": 0.075, "output": 0.30},  # Very cheap
                "gemini-pro": {"input": 0.50, "output": 1.50},
            }
        }
        
        provider_lower = provider.lower()
        if provider_lower not in cost_estimates:
            return None
        
        model_costs = cost_estimates[provider_lower].get(model)
        if not model_costs:
            # Try to find closest match
            for model_name, costs in cost_estimates[provider_lower].items():
                if model_name.lower() in model.lower() or model.lower() in model_name.lower():
                    model_costs = costs
                    break
        
        if not model_costs:
            return None
        
        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * model_costs["input"]
        output_cost = (output_tokens / 1_000_000) * model_costs["output"]
        
        return input_cost + output_cost


# Global instance
langsmith_monitor = LangSmithMonitor()

