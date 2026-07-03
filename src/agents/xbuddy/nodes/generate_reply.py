"""Generate reply node — creates the conversational, user-facing response.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/generate_reply.py

This node is the "for the human" half of the turn:
  1. Reads the context_packet the router loaded (shared rules + current section prompt).
  2. Builds the message history.
  3. Calls the LLM (streaming) with that system prompt + history.
  4. Returns the AI reply as a message.

The paired generate_decision node is the "for the machine" half — it turns the same
exchange into a structured routing decision.
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from core.llm import get_model

from ..models import XBuddyState
from ..sections.base_prompt import BASE_RULES

logger = logging.getLogger(__name__)


async def generate_reply_node(state: XBuddyState, config: RunnableConfig) -> dict:
    """Generate a conversational reply for the current section."""
    packet = state.get("context_packet")
    system_prompt = packet.system_prompt if packet else BASE_RULES
    history = state.get("messages", [])

    # get_model() returns the configured chat model with streaming=True, so tokens
    # stream out over the /stream endpoint automatically.
    model = get_model()
    response = await model.ainvoke([SystemMessage(content=system_prompt), *history], config)

    section = getattr(packet, "section_id", None)
    logger.info("generate_reply | section=%s", getattr(section, "value", section))
    return {"messages": [response], "awaiting_user_input": True}
