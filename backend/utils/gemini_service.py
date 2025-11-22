"""
Gemini LLM Service - Direct API integration with Google Gemini.
"""
from typing import Optional, Dict, Any, List
import json
import re
import requests
from utils.config import settings
from utils.retry import retry, async_retry
from utils.circuit_breaker import circuit_breaker, async_circuit_breaker

class GeminiService:
    """Service for interacting with Google Gemini API directly with retry and circuit breaker."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    def is_available(self) -> bool:
        """Check if Gemini service is available."""
        return bool(self.api_key)
    
    @retry(max_attempts=3, backoff="exponential", base_delay=1.0, exceptions=(requests.RequestException,))
    @circuit_breaker(failure_threshold=5, recovery_timeout=60.0, expected_exception=Exception)
    def _make_request(self, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request with retry and circuit breaker."""
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            url = f"{url}?key={self.api_key}"
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def generate_content(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: User prompt
            system_instruction: System instruction (optional)
            temperature: Temperature for generation
            max_tokens: Maximum tokens (optional)
        
        Returns:
            dict with 'content', 'error' keys
        """
        if not self.is_available():
            return {
                "content": None,
                "error": "Gemini API key not configured"
            }
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        # Build request payload
        contents = [{"parts": [{"text": prompt}]}]
        
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["maxOutputTokens"] = max_tokens
        
        payload = {
            "contents": contents,
            "generationConfig": generation_config
        }
        
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        try:
            response_data = self._make_request(url, payload)
            
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    content = candidate["content"]["parts"][0].get("text", "")
                    return {
                        "content": content,
                        "error": None
                    }
            
            return {
                "content": None,
                "error": "No response from Gemini API"
            }
        except requests.RequestException as e:
            return {
                "content": None,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "content": None,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Chat with Gemini using message history.
        
        Args:
            messages: List of messages with 'role' and 'content'
            temperature: Temperature for generation
        
        Returns:
            dict with 'content', 'error' keys
        """
        if not self.is_available():
            return {
                "content": None,
                "error": "Gemini API key not configured"
            }
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append({
                    "parts": [{"text": content}],
                    "role": "user"
                })
            elif role == "assistant":
                contents.append({
                    "parts": [{"text": content}],
                    "role": "model"
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature
            }
        }
        
        # Add system instruction if provided
        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }
        
        # Ensure we have at least one content
        if not contents:
            contents.append({
                "parts": [{"text": ""}],
                "role": "user"
            })
            payload["contents"] = contents
        
        try:
            response_data = self._make_request(url, payload)
            
            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    content = candidate["content"]["parts"][0].get("text", "")
                    return {
                        "content": content,
                        "error": None
                    }
            
            return {
                "content": None,
                "error": "No content in response"
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "content": None,
                "error": f"API request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "content": None,
                "error": f"Error: {str(e)}"
            }
    
    def extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from text response."""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return None

# Global instance
gemini_service = GeminiService()

