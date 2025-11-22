"""Prompt templates for workflow agents."""
from .prompt_templates import (
    get_few_shot_rfp_analyzer_prompt,
    get_few_shot_challenge_extractor_prompt,
    get_few_shot_value_proposition_prompt,
    get_few_shot_discovery_question_prompt,
    get_few_shot_proposal_builder_prompt
)

__all__ = [
    "get_few_shot_rfp_analyzer_prompt",
    "get_few_shot_challenge_extractor_prompt",
    "get_few_shot_value_proposition_prompt",
    "get_few_shot_discovery_question_prompt",
    "get_few_shot_proposal_builder_prompt"
]

