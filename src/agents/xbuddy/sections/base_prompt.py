"""Base classes and shared prompt rules for all sections.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/sections/base_prompt.py
"""

from typing import Any

from pydantic import BaseModel, Field

from ..enums import SectionID


class ValidationRule(BaseModel):
    """Validation rule for field input."""
    field_name: str
    rule_type: str  # "min_length", "max_length", "regex", "required", "choices"
    value: Any
    error_message: str


class SectionTemplate(BaseModel):
    """Template for an agent section."""
    section_id: SectionID
    name: str
    description: str
    system_prompt_template: str
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    next_section: SectionID | None = None


# TODO: Write your base rules. These are shared across ALL sections.
# See FounderBuddy's BASE_RULES for the pattern — it defines:
#   - Agent persona and communication style
#   - No-placeholder rule
#   - Section navigation rules
#   - Questioning approach (one question at a time)
BASE_RULES = """You are a helpful AI assistant guiding users through a structured conversation.

TODO: Replace this with your agent's persona and rules.

RULES:
- Ask ONE question at a time
- Never use placeholder text like [TBD] or [Not provided]
- Stay within the current section unless the user asks to switch
- Present a summary when a section is complete and ask for satisfaction
"""

BASE_PROMPTS = {
    "base_rules": BASE_RULES,
}
