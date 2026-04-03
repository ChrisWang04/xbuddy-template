"""Implementation node — generates the final output when all sections are complete.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/generate_business_plan.py

In FounderBuddy this generates a business plan. In your XBuddy, this
produces whatever final artifact your agent creates:
  - StudentBuddy: a personalized study plan
  - JobBuddy: a career transition roadmap
  - FitnessBuddy: a structured training program

This node:
  1. Gathers all section data from section_states
  2. Calls the LLM to synthesize a final document
  3. Saves the output to Supabase
  4. Sets finished = True
"""

import logging
from langchain_core.runnables import RunnableConfig

from ..models import XBuddyState

logger = logging.getLogger(__name__)


async def implementation_node(state: XBuddyState, config: RunnableConfig) -> XBuddyState:
    """Generate the final output artifact."""
    # TODO: Implement — see FounderBuddy's generate_business_plan_node
    raise NotImplementedError("PR 5: Implement implementation_node")
