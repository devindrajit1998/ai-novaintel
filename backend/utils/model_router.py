"""
Model Router - Intelligently routes tasks to the best LLM model.
Supports Gemini (fast, cost-effective), Claude (reasoning), and OpenAI (quality).
"""
from typing import Optional, Dict, Any, Literal
from enum import Enum
from utils.config import settings
import sys

class TaskType(str, Enum):
    """Types of tasks for model routing."""
    FAST_GENERATION = "fast_generation"  # Gemini Flash
    COMPLEX_REASONING = "complex_reasoning"  # Claude
    HIGH_QUALITY = "high_quality"  # GPT-4o
    ANALYSIS = "analysis"  # Claude or GPT-4o
    DRAFTING = "drafting"  # Gemini Flash
    REFINEMENT = "refinement"  # GPT-4o or Claude
    CREATIVE = "creative"  # Claude
    STRUCTURED_OUTPUT = "structured_output"  # GPT-4o or Claude


class ModelRouter:
    """Router that selects the best model for each task."""
    
    def __init__(self):
        self.gemini_available = False
        self.openai_available = False
        self.claude_available = False
        self._initialize()
    
    def _initialize(self):
        """Initialize and check model availability."""
        # Check Gemini
        if settings.GEMINI_API_KEY:
            try:
                from utils.gemini_service import gemini_service
                self.gemini_available = gemini_service.is_available()
            except Exception:
                self.gemini_available = False
        
        # Check OpenAI
        if settings.OPENAI_API_KEY:
            try:
                import openai
                # Test connection
                self.openai_available = True
            except ImportError:
                self.openai_available = False
            except Exception:
                self.openai_available = False
        
        # Check Claude
        if settings.ANTHROPIC_API_KEY:
            try:
                import anthropic
                # Test connection
                self.claude_available = True
            except ImportError:
                self.claude_available = False
            except Exception:
                self.claude_available = False
        
        # Log availability
        available = []
        if self.gemini_available:
            available.append("Gemini")
        if self.openai_available:
            available.append("OpenAI")
        if self.claude_available:
            available.append("Claude")
        
        if available:
            print(f"[OK] Model Router initialized - Available models: {', '.join(available)}", file=sys.stderr, flush=True)
        else:
            print("[WARNING] Model Router - No models available. Check API keys.", file=sys.stderr, flush=True)
    
    def select_model(
        self,
        task_type: TaskType,
        prefer_provider: Optional[Literal["gemini", "openai", "claude"]] = None
    ) -> str:
        """
        Select the best model for a task.
        
        Args:
            task_type: Type of task
            prefer_provider: Preferred provider (if available)
        
        Returns:
            Provider name: "gemini", "openai", or "claude"
        """
        # Use preferred provider if available and suitable
        if prefer_provider == "gemini" and self.gemini_available:
            return "gemini"
        if prefer_provider == "openai" and self.openai_available:
            return "openai"
        if prefer_provider == "claude" and self.claude_available:
            return "claude"
        
        # Route based on task type
        if task_type == TaskType.FAST_GENERATION:
            # Fast generation: Gemini Flash
            if self.gemini_available:
                return "gemini"
        
        elif task_type == TaskType.COMPLEX_REASONING:
            # Complex reasoning: Claude
            if self.claude_available:
                return "claude"
            # Fallback to GPT-4o
            if self.openai_available:
                return "openai"
        
        elif task_type == TaskType.HIGH_QUALITY:
            # High quality: GPT-4o
            if self.openai_available:
                return "openai"
            # Fallback to Claude
            if self.claude_available:
                return "claude"
        
        elif task_type == TaskType.ANALYSIS:
            # Analysis: Claude or GPT-4o
            if self.claude_available:
                return "claude"
            if self.openai_available:
                return "openai"
        
        elif task_type == TaskType.DRAFTING:
            # Drafting: Gemini Flash (fast and cheap)
            if self.gemini_available:
                return "gemini"
        
        elif task_type == TaskType.REFINEMENT:
            # Refinement: GPT-4o or Claude
            if self.openai_available:
                return "openai"
            if self.claude_available:
                return "claude"
        
        elif task_type == TaskType.CREATIVE:
            # Creative: Claude
            if self.claude_available:
                return "claude"
            # Fallback to GPT-4o
            if self.openai_available:
                return "openai"
        
        elif task_type == TaskType.STRUCTURED_OUTPUT:
            # Structured output: GPT-4o or Claude
            if self.openai_available:
                return "openai"
            if self.claude_available:
                return "claude"
        
        # Default fallback: use first available
        if self.gemini_available:
            return "gemini"
        if self.openai_available:
            return "openai"
        if self.claude_available:
            return "claude"
        
        # No models available
        raise ValueError("No LLM models available. Check API keys.")
    
    def get_model_name(self, provider: str, task_type: Optional[TaskType] = None) -> str:
        """Get the specific model name for a provider."""
        if provider == "gemini":
            return getattr(settings, "GEMINI_MODEL", "gemini-2.0-flash")
        elif provider == "openai":
            # Use GPT-4o for high quality, GPT-3.5-turbo for fast tasks
            if task_type in [TaskType.HIGH_QUALITY, TaskType.REFINEMENT, TaskType.ANALYSIS]:
                return "gpt-4o"
            return "gpt-3.5-turbo"
        elif provider == "claude":
            # Use Claude 3.5 Sonnet for best quality
            return "claude-3-5-sonnet-20241022"
        else:
            raise ValueError(f"Unknown provider: {provider}")


# Global instance
model_router = ModelRouter()

