"""Generate decision node — turns the exchange into a structured routing decision.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/nodes/generate_decision.py

This is the "for the machine" half of the turn. It:
  1. Analyzes the conversation so far for the CURRENT section.
  2. Produces a structured ChatAgentDecision: router_directive (stay / next / modify),
     whether the user seems satisfied, and whether the section content is worth saving.
  3. Writes router_directive back to state so the router acts on it next turn.

Structured output is produced via with_structured_output(ChatAgentDecision), so the
result is schema-validated. If the model/parse ever fails, we fall back to STAY — the
safe default (keep asking) rather than wrongly advancing.
"""

import logging

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from core.llm import get_model
from core.models import AnthropicModelName

from ..enums import RouterDirective, SectionID
from ..models import ChatAgentDecision, ChatAgentOutput, XBuddyState
from ..prompts import get_section_template

logger = logging.getLogger(__name__)

DECISION_SYSTEM_PROMPT = """You are the navigation controller for FitnessBuddy. Based ONLY on the
conversation so far, decide what should happen next for the CURRENT section.

Current section: {name} ({section_id})
This section should cover: {description}
Required fields: {required}

Produce a structured decision:
- router_directive:
    "stay"  -> the current section still needs more information from the user.
    "next"  -> the current section is covered well enough to move on.
    "modify:<section_id>" -> ONLY if the user explicitly asked to go back and change a
        previous section. Valid ids: goals, profile, schedule, preferences, nutrition.
- is_satisfied: true / false / null — does the user seem satisfied with what's captured here?
- user_satisfaction_feedback: a short note on their satisfaction, or null.
- should_save_content: true once this section has enough content worth saving.

Be conservative: default to "stay" when unsure. Do NOT advance just because a question was
asked — only advance once the user has actually given the information this section needs."""


def _extract_text(content) -> str:
    """AIMessage content may be a plain string or a list of content blocks."""
    if isinstance(content, list):
        return "".join(
            b.get("text", "")
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return content or ""


async def generate_decision_node(state: XBuddyState, config: RunnableConfig) -> dict:
    """Analyze the conversation and produce a structured routing decision."""
    current = state.get("current_section", list(SectionID)[0])
    if not isinstance(current, SectionID):
        try:
            current = SectionID(current)
        except ValueError:
            current = list(SectionID)[0]

    template = get_section_template(current)
    system = DECISION_SYSTEM_PROMPT.format(
        name=template.name,
        section_id=current.value,
        description=template.description,
        required=", ".join(template.required_fields) or "none",
    )
    history = state.get("messages", [])

    # A cheaper/faster model is plenty for a structured classification.
    model = get_model(AnthropicModelName.HAIKU_45).with_structured_output(ChatAgentDecision)
    try:
        decision = await model.ainvoke([SystemMessage(content=system), *history], config)
    except Exception as exc:  # unparseable / LLM error -> safe fallback
        logger.warning("generate_decision | failed (%s) — defaulting to STAY", exc)
        decision = ChatAgentDecision(
            router_directive=RouterDirective.STAY.value,
            should_save_content=False,
        )

    last_reply = next((m for m in reversed(history) if isinstance(m, AIMessage)), None)
    agent_output = ChatAgentOutput(
        reply=_extract_text(last_reply.content) if last_reply else "",
        router_directive=decision.router_directive,
        user_satisfaction_feedback=decision.user_satisfaction_feedback,
        is_satisfied=decision.is_satisfied,
        should_save_content=decision.should_save_content,
    )

    logger.info(
        "generate_decision | directive=%s satisfied=%s save=%s",
        decision.router_directive, decision.is_satisfied, decision.should_save_content,
    )
    return {
        "router_directive": decision.router_directive,
        "agent_output": agent_output,
    }
