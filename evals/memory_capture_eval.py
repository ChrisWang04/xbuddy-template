"""LangSmith eval — does memory_updater's section summary capture the key facts?

This is FitnessBuddy's first eval. It targets the summarization step inside
memory_updater: given a short section conversation with known facts, it produces a
summary and an LLM judge scores how many of those facts survived. A summary that
drops a fact the user clearly stated is exactly the "memory bug" this is meant to catch.

Run from repo root:  uv run python evals/memory_capture_eval.py
Needs ANTHROPIC_API_KEY + LangSmith keys in .env. Prints an experiment URL.
"""

import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langsmith import Client, evaluate

from agents.xbuddy.enums import SectionID
from agents.xbuddy.prompts import get_section_template
from core.llm import get_model
from core.models import AnthropicModelName

DATASET_NAME = "fitnessbuddy-memory-capture"

# Each example: a short section conversation + the facts a correct summary must keep.
EXAMPLES = [
    {
        "inputs": {
            "section": "goals",
            "conversation": [
                ["user", "I want to build upper-body muscle, mostly chest and arms."],
                ["assistant", "Love it — what's your rough timeline?"],
                ["user", "About 3 months, I've got a wedding to look good for."],
            ],
        },
        "outputs": {"facts": ["build upper-body muscle (chest/arms)", "~3 month timeline", "wedding motivation"]},
    },
    {
        "inputs": {
            "section": "profile",
            "conversation": [
                ["user", "I'm 29, about 180cm and 82kg."],
                ["assistant", "Any injuries I should plan around?"],
                ["user", "My left shoulder gets sore if I overhead press."],
            ],
        },
        "outputs": {"facts": ["age 29", "180cm / 82kg", "left shoulder pain with overhead press"]},
    },
    {
        "inputs": {
            "section": "schedule",
            "conversation": [
                ["user", "I can train 4 days a week, about 45 minutes each."],
                ["assistant", "Where will you be training?"],
                ["user", "At home — I only have adjustable dumbbells and a pull-up bar."],
            ],
        },
        "outputs": {"facts": ["4 days/week", "~45 min sessions", "trains at home", "dumbbells + pull-up bar"]},
    },
]


def ensure_dataset(client: Client):
    try:
        return client.read_dataset(dataset_name=DATASET_NAME)
    except Exception:
        ds = client.create_dataset(DATASET_NAME, description="Section-summary fact capture for FitnessBuddy memory.")
        for ex in EXAMPLES:
            client.create_example(inputs=ex["inputs"], outputs=ex["outputs"], dataset_id=ds.id)
        return ds


def _to_messages(conversation):
    return [
        HumanMessage(content=text) if role == "user" else AIMessage(content=text)
        for role, text in conversation
    ]


def _text(content) -> str:
    if isinstance(content, list):
        return "".join(b.get("text", "") for b in content if isinstance(b, dict))
    return content or ""


def summarize(section: SectionID, history) -> str:
    """Sync mirror of memory_updater._summarize_section (so the eval stays simple)."""
    template = get_section_template(section)
    prompt = (
        f"Summarize what the user has told us for the {template.name} section. "
        f"This section covers: {template.description} "
        f"Write a concise plain-text summary (1-3 sentences) of the information collected. "
        f"Use only what the user actually said. If little was provided, note what's still missing."
    )
    model = get_model(AnthropicModelName.HAIKU_45)
    resp = model.invoke([SystemMessage(content=prompt), *history])
    return _text(resp.content).strip()


def target(inputs: dict) -> dict:
    section = SectionID(inputs["section"])
    history = _to_messages(inputs["conversation"])
    return {"summary": summarize(section, history)}


_judge = get_model(AnthropicModelName.HAIKU_45)


def fact_capture(run, example) -> dict:
    """LLM-judge: fraction of the reference facts that survived into the summary."""
    summary = run.outputs.get("summary", "") if run.outputs else ""
    facts = example.outputs.get("facts", []) if example.outputs else []
    if not facts:
        return {"key": "fact_capture", "score": 0.0}

    prompt = (
        "You are grading whether a summary preserved key facts.\n"
        f"SUMMARY:\n{summary}\n\n"
        f"FACTS (count = {len(facts)}):\n- " + "\n- ".join(facts) + "\n\n"
        "How many of these facts are captured (even paraphrased) in the summary? "
        f"Reply with ONLY an integer from 0 to {len(facts)}."
    )
    resp = _judge.invoke(prompt)
    match = re.search(r"\d+", _text(resp.content))
    captured = int(match.group()) if match else 0
    return {"key": "fact_capture", "score": min(captured, len(facts)) / len(facts)}


if __name__ == "__main__":
    client = Client()
    ensure_dataset(client)
    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[fact_capture],
        experiment_prefix="fitnessbuddy-memory-capture",
        client=client,
    )
    print("\n✅ eval done — open the experiment in LangSmith (link above) to see per-example fact_capture scores.")
