"""
LLM Factory - Create LLM instances for different providers.
"""
from typing import Optional, Any
from langchain_core.runnables import Runnable
from utils.config import settings
from utils.gemini_service import gemini_service

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
        
        return GeminiResponse(result.get("content", ""), result.get("error"))

class GeminiResponse:
    """Response wrapper for LangChain compatibility."""
    
    def __init__(self, content: str, error: Optional[str] = None):
        self.content = content
        self.error = error
    
    def __str__(self):
        return self.content if self.content else ""

def get_llm(provider: Optional[str] = None, temperature: float = 0.1, model: Optional[str] = None):
    """
    Get LLM instance - Gemini only.
    
    Args:
        provider: LLM provider (defaults to "gemini")
        temperature: Temperature for generation
        model: Model name (optional, not used for Gemini)
    
    Returns:
        LLM instance compatible with LangChain
    """
    # Always use Gemini
    return GeminiLangChainWrapper(temperature=temperature)

