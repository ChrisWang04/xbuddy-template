"""Section prompts and navigation helpers.

Reference: https://github.com/Victoria824/FounderBuddy/blob/main/src/agents/founder_buddy/prompts.py

TODO: Implement:
  - get_section_template(section_id) -> SectionTemplate
  - get_next_section(current_section) -> SectionID | None
  - get_next_unfinished_section(state) -> SectionID | None
"""

from .enums import SectionID
from .sections.base_prompt import SectionTemplate


def get_section_template(section_id: SectionID) -> SectionTemplate:
    """Return the template for a given section."""
    # TODO: Map each SectionID to its SectionTemplate
    raise NotImplementedError("Implement section template mapping")


def get_next_section(current: SectionID) -> SectionID | None:
    """Return the next section in sequence, or None if all complete."""
    order = list(SectionID)
    idx = order.index(current)
    if idx + 1 < len(order):
        return order[idx + 1]
    return None


def get_next_unfinished_section(section_states: dict) -> SectionID | None:
    """Find the first section that isn't done yet."""
    for section_id in SectionID:
        state = section_states.get(section_id.value)
        if not state or state.status != "done":
            return section_id
    return None
