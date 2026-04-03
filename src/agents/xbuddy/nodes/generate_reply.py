"""Generate reply node — creates conversational responses.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/generate_reply.py

This node:
  1. Reads the context_packet (system prompt for current section)
  2. Builds the message history (short_memory)
  3. Calls the LLM with streaming
  4. Returns the AI response as a message
"""

import logging
from langchain_core.runnables import RunnableConfig

from ..models import XBuddyState

logger = logging.getLogger(__name__)


async def generate_reply_node(state: XBuddyState, config: RunnableConfig) -> XBuddyState:
    """Generate a conversational reply for the current section."""
    # TODO: Implement — see FounderBuddy's generate_reply_node
    raise NotImplementedError("PR 3: Implement generate_reply_node")
