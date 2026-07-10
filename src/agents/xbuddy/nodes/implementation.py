"""Implementation node — generates the final output when all sections are complete.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/generate_business_plan.py

For FitnessBuddy the final artifact is a structured training + nutrition plan. This node:
  1. Gathers every section's summary from section_states.
  2. Calls the LLM (Sonnet) to synthesize the plan, grounded only in what was collected.
  3. Persists it to Supabase (best-effort).
  4. Sets finished = True and stores it in final_output.
"""

import logging

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig

from core.llm import get_model

from ..enums import SectionID
from ..models import XBuddyState
from ..prompts import get_section_template

logger = logging.getLogger(__name__)

AGENT_ID = "fitness-buddy"

PLAN_PROMPT = """You are FitnessBuddy. The user has finished all five sections. Using ONLY the
collected information below, write a clear, structured, personalized training + nutrition plan.

Collected information:
{collected}

Write the plan with these parts:
1. Overview — their goal and how this plan gets them there.
2. Weekly training split — which days and what focus, fitting their schedule, location, and equipment.
3. Key exercises & progression — grounded in their available equipment; avoid anything that aggravates their injuries or that they dislike.
4. Nutrition guidance — aligned with their diet pattern, restrictions, and goal.
5. Tips & staying on track.

Be specific, encouraging, and practical. Use their actual details. Do not invent facts that
aren't in the collected information — if something is missing, give sensible general guidance
and briefly note the assumption."""


def _text(content) -> str:
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content or ""


def _persist_plan(user_id, thread_id: str, plan: str) -> None:
    """Best-effort save to Supabase — never let a DB error break plan delivery."""
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        logger.warning("implementation | user_id %r not int-coercible", user_id)
    try:
        from integrations.supabase.supabase_client import SupabaseClient

        SupabaseClient().save_business_plan(
            user_id=user_id,
            thread_id=thread_id,
            content=plan,
            markdown_content=plan,
            agent_id=AGENT_ID,
        )
    except Exception as exc:  # noqa: BLE001 — best-effort
        logger.warning("implementation | Supabase save failed (%s)", exc)


async def implementation_node(state: XBuddyState, config: RunnableConfig) -> dict:
    """Synthesize the final training + nutrition plan from all section summaries."""
    section_states = state.get("section_states", {})

    lines = []
    for sid in SectionID:
        st = section_states.get(sid.value)
        summary = st.content.plain_text if st and st.content else ""
        lines.append(f"- {get_section_template(sid).name}: {summary.strip() or '(not provided)'}")
    collected = "\n".join(lines)

    model = get_model()  # Sonnet — quality matters for the final artifact
    resp = await model.ainvoke([HumanMessage(content=PLAN_PROMPT.format(collected=collected))], config)
    plan = _text(resp.content).strip()

    _persist_plan(state.get("user_id", 1), state.get("thread_id", ""), plan)

    logger.info("implementation | plan generated (%d chars)", len(plan))
    return {
        "messages": [resp],
        "final_output": plan,
        "finished": True,
    }
