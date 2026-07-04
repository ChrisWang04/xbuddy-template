"""Memory updater node — persists section state and manages completion.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/memory_updater.py

Runs after generate_decision. Using that decision it:
  1. When a section is complete/worth saving, summarizes what was collected for it
     (a cheap LLM call) and stores that as the section's content.
  2. Advances section_states (mark the current section DONE, next one IN_PROGRESS).
  3. Persists the section to Supabase (best-effort — a DB hiccup never breaks the turn).
  4. Sets should_generate_final_output once every section is DONE.

Completeness gate: a section is only marked DONE when the decision advanced it
(router_directive == "next"), i.e. generate_decision judged there was enough. Thin
sections stay IN_PROGRESS until that judgement is made.
"""

import logging

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from core.llm import get_model
from core.models import AnthropicModelName

from ..enums import RouterDirective, SectionID, SectionStatus
from ..models import SectionContent, SectionState, XBuddyState
from ..prompts import get_next_section, get_section_template

logger = logging.getLogger(__name__)

AGENT_ID = "fitness-buddy"


def _directive_value(directive) -> str:
    return getattr(directive, "value", directive) or RouterDirective.STAY.value


def _as_section_id(value) -> SectionID:
    if isinstance(value, SectionID):
        return value
    try:
        return SectionID(value)
    except (ValueError, TypeError):
        return list(SectionID)[0]


async def _summarize_section(section: SectionID, history: list, config: RunnableConfig) -> str:
    """Concise plain-text summary of what the user gave for this section."""
    template = get_section_template(section)
    prompt = (
        f"Summarize what the user has told us for the {template.name} section. "
        f"This section covers: {template.description} "
        f"Write a concise plain-text summary (1-3 sentences) of the information collected. "
        f"Use only what the user actually said. If little was provided, note what's still missing."
    )
    model = get_model(AnthropicModelName.HAIKU_45)
    resp = await model.ainvoke([SystemMessage(content=prompt), *history], config)
    content = resp.content
    if isinstance(content, list):
        content = "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return (content or "").strip()


def _persist_section(user_id: int, thread_id: str, state: SectionState) -> None:
    """Best-effort write to Supabase — swallow errors so persistence never breaks a turn."""
    try:
        from integrations.supabase.supabase_client import SupabaseClient

        SupabaseClient().save_section_state(
            user_id=user_id,
            thread_id=thread_id,
            section_id=state.section_id.value,
            content=state.content.content if state.content else {},
            plain_text=state.content.plain_text if state.content else "",
            status=state.status.value,
            satisfaction_status=state.satisfaction_status,
            agent_id=AGENT_ID,
        )
    except Exception as exc:  # noqa: BLE001 — persistence is best-effort
        logger.warning("memory_updater | Supabase persist failed (%s)", exc)


async def memory_updater_node(state: XBuddyState, config: RunnableConfig) -> dict:
    """Update section state, persist it, and check for completion."""
    updates: dict = {}
    current = _as_section_id(state.get("current_section"))
    directive = _directive_value(state.get("router_directive"))
    advancing = directive == RouterDirective.NEXT.value

    agent_output = state.get("agent_output")
    should_save = bool(agent_output and agent_output.should_save_content)
    is_satisfied = agent_output.is_satisfied if agent_output else None

    # Work on copies so we don't mutate the incoming state in place.
    section_states = {k: v.model_copy(deep=True) for k, v in state.get("section_states", {}).items()}
    history = state.get("messages", [])
    user_id = state.get("user_id", 1)
    thread_id = state.get("thread_id", "")

    # 1. Save the current section's content if the decision said so (or we're advancing).
    if should_save or advancing:
        summary = await _summarize_section(current, history, config)
        cur = section_states.get(current.value) or SectionState(section_id=current)
        cur.content = SectionContent(content={"text": summary}, plain_text=summary)
        cur.satisfaction_status = (
            "satisfied" if is_satisfied else "needs_improvement" if is_satisfied is False else None
        )
        # Completeness gate: only DONE when the decision advanced this section.
        if advancing:
            cur.status = SectionStatus.DONE
        elif cur.status == SectionStatus.PENDING:
            cur.status = SectionStatus.IN_PROGRESS
        section_states[current.value] = cur
        _persist_section(user_id, thread_id, cur)

    # 2. On advance, wake the next section.
    if advancing:
        nxt = get_next_section(current)
        if nxt and nxt.value in section_states and section_states[nxt.value].status == SectionStatus.PENDING:
            section_states[nxt.value].status = SectionStatus.IN_PROGRESS

    updates["section_states"] = section_states

    # 3. All sections done → signal the graph to generate the final plan.
    all_done = all(
        section_states.get(s.value) and section_states[s.value].status == SectionStatus.DONE
        for s in SectionID
    )
    if all_done:
        updates["should_generate_final_output"] = True

    logger.info(
        "memory_updater | section=%s advancing=%s saved=%s all_done=%s",
        current.value, advancing, should_save or advancing, all_done,
    )
    return updates
