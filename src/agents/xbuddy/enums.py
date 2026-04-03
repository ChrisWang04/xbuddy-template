"""Enumerations for your XBuddy Agent."""

from enum import Enum


class SectionStatus(str, Enum):
    """Status of an agent section."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class RouterDirective(str, Enum):
    """Router directive for navigation control."""
    STAY = "stay"
    NEXT = "next"
    MODIFY = "modify"  # Format: "modify:section_id"


class SectionID(str, Enum):
    """Your agent's section identifiers.

    TODO: Rename these to match your domain.
    For example, if you're building StudentBuddy:
      GOALS = "goals"
      SCHEDULE = "schedule"
      RESOURCES = "resources"
      STUDY_PLAN = "study_plan"
      REVIEW = "review"
    """
    SECTION_1 = "section_1"
    SECTION_2 = "section_2"
    SECTION_3 = "section_3"
    SECTION_4 = "section_4"
    SECTION_5 = "section_5"
