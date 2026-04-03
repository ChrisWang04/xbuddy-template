"""Agent tools.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/tools.py

TODO: Implement get_context tool that loads the context packet for a section.
This is called by the router node to get the system prompt and validation
rules for the current section.
"""

from langchain_core.tools import tool


@tool
async def get_context(
    user_id: int,
    thread_id: str,
    section_id: str,
    user_data: dict | None = None,
) -> dict:
    """Load context packet for a section.

    Returns a dict with: section_id, status, system_prompt, draft, validation_rules
    """
    # TODO: Implement — load section template, check existing state in DB
    raise NotImplementedError("Implement get_context tool")
