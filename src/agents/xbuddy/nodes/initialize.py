"""Initialize node — validates and sets up conversation state.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/initialize.py

This node runs once at the start of every invocation.
It should:
  1. Set user_id and thread_id from config if not in state
  2. Set default values for current_section and router_directive
  3. Log the initialization
"""

import logging
from langchain_core.runnables import RunnableConfig

from ..models import XBuddyState

logger = logging.getLogger(__name__)


async def initialize_node(state: XBuddyState, config: RunnableConfig) -> XBuddyState:
    """Initialize conversation state."""
    # TODO: Implement — see FounderBuddy's initialize_node
    raise NotImplementedError("PR 1: Implement initialize_node")
