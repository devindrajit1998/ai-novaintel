"""
LLM Factory - Create LLM instances for different providers.
Supports Gemini, OpenAI, and Claude with intelligent routing.
"""
from typing import Optional, Any, Literal
from langchain_core.runnables import Runnable
from utils.config import settings
from utils.gemini_service import gemini_service
from utils.model_router import model_router, TaskType
from utils.langsmith_monitor import langsmith_monitor
import sys

# LangChain compatible wrapper for Gemini
class GeminiLangChainWrapper(Runnable):
    """Wrapper to make Gemini service compatible with LangChain."""
    
    def __init__(self, temperature: float = 0.1):
        super().__init__()
        self.temperature = temperature
        self.service = gemini_service
    
    def invoke(self, input: Any, config: Optional[dict] = None) -> 'GeminiResponse':
        """Invoke the LLM with a prompt."""
        prompt_input = input
        
        # Handle LangChain ChatPromptValue format
        if hasattr(prompt_input, 'messages'):
            # LangChain ChatPromptTemplate result
            try:
                messages = prompt_input.messages
                formatted_messages = []
                system_instruction = None
                
                for msg in messages:
                    # Extract content and role from LangChain message
                    if hasattr(msg, 'content'):
                        content = msg.content
                    elif isinstance(msg, str):
                        content = msg
                    else:
                        content = str(msg)
                    
                    # Determine role
                    role = "user"
                    if hasattr(msg, 'type'):
                        msg_type = msg.type
                        if msg_type == "system":
                            system_instruction = content
                            continue
                        elif msg_type == "ai" or msg_type == "assistant":
                            role = "assistant"
                        else:
                            role = "user"
                    elif hasattr(msg, 'role'):
                        msg_role = msg.role
                        if msg_role == "system":
                            system_instruction = content
                            continue
                        elif msg_role == "assistant" or msg_role == "ai":
                            role = "assistant"
                        else:
                            role = "user"
                    
                    formatted_messages.append({
                        "role": role,
                        "content": content
                    })
                
                # Use chat if we have messages, otherwise use generate_content
                if formatted_messages:
                    # If we have system instruction, add it as a system message at the beginning
                    if system_instruction:
                        formatted_messages.insert(0, {
                            "role": "system",
                            "content": system_instruction
                        })
                    result = self.service.chat(formatted_messages, temperature=self.temperature)
                else:
                    # Fallback to generate_content
                    prompt_text = system_instruction or ""
                    result = self.service.generate_content(prompt_text, temperature=self.temperature)
            except Exception as e:
                # If message parsing fails, try to convert to string
                prompt_text = str(prompt_input)
                result = self.service.generate_content(prompt_text, temperature=self.temperature)
        
        # Handle dict format
        elif isinstance(prompt_input, dict):
            if "messages" in prompt_input:
                messages = prompt_input["messages"]
                formatted_messages = []
                system_instruction = None
                
                for msg in messages:
                    if hasattr(msg, 'content'):
                        content = msg.content
                        role = "user"
                        if hasattr(msg, 'role'):
                            role = msg.role if msg.role != "system" else "system"
                        elif hasattr(msg, 'type'):
                            role = msg.type if msg.type != "system" else "system"
                    else:
                        content = str(msg)
                        role = "user"
                    
                    if role == "system":
                        system_instruction = content
                    else:
                        formatted_messages.append({
                            "role": role if role != "assistant" else "assistant",
                            "content": content
                        })
                
                result = self.service.chat(formatted_messages, temperature=self.temperature)
            else:
                # Simple text prompt
                prompt = str(prompt_input.get("input", prompt_input))
                system_instruction = prompt_input.get("system", None)
                result = self.service.generate_content(
                    prompt,
                    system_instruction=system_instruction,
                    temperature=self.temperature
                )
        else:
            # Direct string or other format
            result = self.service.generate_content(
                str(prompt_input),
                temperature=self.temperature
            )
        
        # Return the content as a string for LangChain compatibility
        # LangChain output parsers (PydanticOutputParser) expect a string, not a custom object
        content = result.get("content", "")
        error = result.get("error")
        
        if error:
            # If there's an error, raise an exception
            # The output parser will handle the error appropriately
            raise ValueError(f"LLM error: {error}")
        
        # Return as string directly - this is what LangChain output parsers expect
        return content

class GeminiResponse:
    """Response wrapper for LangChain compatibility."""
    
    def __init__(self, content: str, error: Optional[str] = None):
        self.content = content
        self.error = error
        # Add 'text' attribute for LangChain compatibility
        self.text = content
    
    def __str__(self):
        return self.content if self.content else ""
    
    def __repr__(self):
        return f"GeminiResponse(content={self.content[:50]}..., error={self.error})"

def get_llm(
    provider: Optional[str] = None,
    temperature: float = 0.1,
    model: Optional[str] = None,
    task_type: Optional[TaskType] = None,
    prefer_provider: Optional[Literal["gemini", "openai", "claude"]] = None
):
    """
    Get LLM instance - Supports Gemini, OpenAI, and Claude with intelligent routing.
    
    Args:
        provider: LLM provider ("gemini", "openai", "claude", or None for auto-routing)
        temperature: Temperature for generation
        model: Model name (optional)
        task_type: Task type for intelligent routing
        prefer_provider: Preferred provider if available
    
    Returns:
        LLM instance compatible with LangChain
    """
    # Auto-select provider if not specified
    if not provider:
        if task_type:
            provider = model_router.select_model(task_type, prefer_provider)
        else:
            # Default to Gemini or use preferred
            provider = prefer_provider or "gemini"
    
    # Get specific model name
    model_name = model or model_router.get_model_name(provider, task_type)
    
    # Set LangSmith monitoring metadata if enabled
    if langsmith_monitor.is_enabled():
        langsmith_monitor.set_run_name(f"{provider}:{model_name}")
        langsmith_monitor.set_tags([provider, model_name, task_type.value if task_type else "default"])
        langsmith_monitor.set_metadata({
            "provider": provider,
            "model": model_name,
            "temperature": temperature,
            "task_type": task_type.value if task_type else None
        })
    
    # Create appropriate wrapper
    if provider == "gemini":
        return GeminiLangChainWrapper(temperature=temperature)
    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=settings.OPENAI_API_KEY,
                # LangSmith automatically tracks if enabled
            )
            # Tag for LangSmith
            if langsmith_monitor.is_enabled():
                llm.tags = ["openai", model_name]
            return llm
        except ImportError:
            print("[WARNING] langchain-openai not installed. Install with: pip install langchain-openai", file=sys.stderr, flush=True)
            print("[FALLBACK] Using Gemini instead", file=sys.stderr, flush=True)
            return GeminiLangChainWrapper(temperature=temperature)
    elif provider == "claude":
        try:
            from langchain_anthropic import ChatAnthropic
            llm = ChatAnthropic(
                model=model_name,
                temperature=temperature,
                api_key=settings.ANTHROPIC_API_KEY,
                # LangSmith automatically tracks if enabled
            )
            # Tag for LangSmith
            if langsmith_monitor.is_enabled():
                llm.tags = ["anthropic", model_name]
            return llm
        except ImportError:
            print("[WARNING] langchain-anthropic not installed. Install with: pip install langchain-anthropic", file=sys.stderr, flush=True)
            print("[FALLBACK] Using Gemini instead", file=sys.stderr, flush=True)
            return GeminiLangChainWrapper(temperature=temperature)
    else:
        # Unknown provider, default to Gemini
        print(f"[WARNING] Unknown provider '{provider}', using Gemini instead", file=sys.stderr, flush=True)
        return GeminiLangChainWrapper(temperature=temperature)

