"""
Prompt registry for versioning and tracking prompts with LangSmith.
"""
from typing import Dict, Any, Optional
from utils.langsmith_monitor import langsmith_monitor
from workflows.prompts.prompt_templates import (
    get_few_shot_rfp_analyzer_prompt,
    get_few_shot_challenge_extractor_prompt,
    get_few_shot_value_proposition_prompt,
    get_few_shot_discovery_question_prompt,
    get_few_shot_proposal_builder_prompt
)


class PromptRegistry:
    """Registry for tracking prompt versions and usage."""
    
    # Prompt versions
    PROMPT_VERSIONS = {
        "rfp_analyzer": "v1.0",
        "challenge_extractor": "v1.0",
        "value_proposition": "v1.0",
        "discovery_question": "v1.0",
        "proposal_builder": "v1.0",
        "proposal_refiner": "v1.0"
    }
    
    @classmethod
    def get_prompt(cls, prompt_name: str, version: Optional[str] = None) -> str:
        """
        Get prompt template by name and version.
        
        Args:
            prompt_name: Name of the prompt
            version: Optional version (defaults to latest)
        
        Returns:
            Prompt template string
        """
        version = version or cls.PROMPT_VERSIONS.get(prompt_name, "v1.0")
        
        prompt_map = {
            "rfp_analyzer": get_few_shot_rfp_analyzer_prompt,
            "challenge_extractor": get_few_shot_challenge_extractor_prompt,
            "value_proposition": get_few_shot_value_proposition_prompt,
            "discovery_question": get_few_shot_discovery_question_prompt,
            "proposal_builder": get_few_shot_proposal_builder_prompt,
        }
        
        getter = prompt_map.get(prompt_name)
        if not getter:
            raise ValueError(f"Unknown prompt: {prompt_name}")
        
        prompt_template = getter()
        
        # Track prompt with LangSmith
        if langsmith_monitor.is_enabled():
            langsmith_monitor.track_prompt(
                prompt_name=prompt_name,
                prompt_version=version,
                prompt_template=prompt_template,
                metadata={"version": version}
            )
        
        return prompt_template
    
    @classmethod
    def register_prompt(cls, prompt_name: str, prompt_template: str, version: str = "v1.0"):
        """
        Register a new prompt version.
        
        Args:
            prompt_name: Name of the prompt
            prompt_template: Prompt template text
            version: Version string
        """
        cls.PROMPT_VERSIONS[prompt_name] = version
        
        # Track with LangSmith
        if langsmith_monitor.is_enabled():
            langsmith_monitor.track_prompt(
                prompt_name=prompt_name,
                prompt_version=version,
                prompt_template=prompt_template
            )


# Global instance
prompt_registry = PromptRegistry()

