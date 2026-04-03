"""Router node — handles section navigation and context loading.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/router.py

This node:
  1. Reads the router_directive (STAY / NEXT / MODIFY)
  2. Updates current_section accordingly
  3. Loads the context_packet for the current section
  4. Checks if all sections are complete
"""

import logging
from langchain_core.runnables import RunnableConfig

from ..models import XBuddyState

logger = logging.getLogger(__name__)


async def router_node(state: XBuddyState, config: RunnableConfig) -> XBuddyState:
    """Route to the correct section and load context."""
    # TODO: Implement — see FounderBuddy's router_node
    raise NotImplementedError("PR 2: Implement router_node")
