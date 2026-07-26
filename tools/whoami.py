"""Whoami tool — personal profile and context about the developer."""

import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from app import mcp
from orion_config import WHOAMI_FILE

logger = logging.getLogger(__name__)


class EducationEntry(BaseModel):
    """An academic degree or certification."""

    degree: str
    institution: str
    year: str | int


class CurrentWork(BaseModel):
    """Current job details."""

    role: str
    company: str
    area: str
    description: str
    stack: list[str] = Field(default_factory=list)


class SkillCategories(BaseModel):
    """Grouped technical skills."""

    machine_learning: list[str] = Field(default_factory=list)
    deep_learning: list[str] = Field(default_factory=list)
    nlp: list[str] = Field(default_factory=list)
    xai: list[str] = Field(default_factory=list)
    distributed: list[str] = Field(default_factory=list)
    deployment: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    """A personal or professional project."""

    name: str
    description: str
    stack: list[str] = Field(default_factory=list)
    repo: Optional[str] = None


class Profile(BaseModel):
    """Juan's professional profile — validated on load."""

    name: str
    role: str
    company: str
    location: str
    since: str
    area: str
    specialization: str
    summary: str
    work: dict[str, CurrentWork] = Field(default_factory=dict)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: Optional[SkillCategories] = None
    projects: list[ProjectEntry] = Field(default_factory=list)
    learning_goals: list[str] = Field(default_factory=list)


def _load_profile() -> Profile:
    """Load and validate the whoami profile from disk."""
    try:
        with open(WHOAMI_FILE, "r") as f:
            raw = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        logger.error("Failed to read whoami profile: %s", exc)
        raise

    try:
        return Profile.model_validate(raw)
    except ValidationError as exc:
        logger.error("Invalid whoami profile: %s", exc)
        raise


def _format_work(current: Optional[CurrentWork]) -> str:
    """Format current job section."""
    if not current:
        return ""
    return (
        f"  {current.role} at {current.company} ({current.area})\n"
        f"  {current.description}\n"
        f"  Daily stack: {', '.join(current.stack)}\n"
    )


def _format_education(entries: list[EducationEntry]) -> str:
    """Format education section as bullet list."""
    lines = []
    for edu in entries:
        lines.append(f"  - {edu.degree} — {edu.institution} ({edu.year})")
    return "\n".join(lines)


def _format_skills(skills: Optional[SkillCategories]) -> str:
    """Format skills section grouped by category."""
    if not skills:
        return ""
    lines = []
    categories = [
        ("Classical ML", skills.machine_learning),
        ("Deep Learning", skills.deep_learning),
        ("NLP", skills.nlp),
        ("XAI", skills.xai),
        ("Distributed Systems", skills.distributed),
        ("Deployment", skills.deployment),
    ]
    for label, items in categories:
        if items:
            lines.append(f"  {label}: {', '.join(items)}")
    if skills.languages:
        lines.append(f"  Languages: {', '.join(skills.languages)}")
    if skills.frameworks:
        lines.append(f"  Frameworks: {', '.join(skills.frameworks)}")
    return "\n".join(lines)


def _format_projects(entries: list[ProjectEntry]) -> str:
    """Format projects section."""
    lines = []
    for p in entries:
        repo_str = f" ({p.repo})" if p.repo else ""
        lines.append(f"  - {p.name}: {p.description}{repo_str}")
        lines.append(f"    Stack: {', '.join(p.stack)}")
    return "\n".join(lines)


@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
)
def whoami() -> str:
    """Return a comprehensive professional profile — who I am, my work,
    education, skills, projects, and what I'm currently learning.

    Use this when you need context about the developer you're assisting.
    """
    try:
        profile = _load_profile()
    except Exception:
        return "Unable to load profile. Check that whoami.json exists and is valid JSON."

    work_desc = _format_work(profile.work.get("current"))
    education = _format_education(profile.education)
    skills = _format_skills(profile.skills)
    projects = _format_projects(profile.projects)
    goals = "\n".join(f"  - {g}" for g in profile.learning_goals)

    return (
        f"# {profile.name}\n"
        f"\n"
        f"**{profile.role}** at **{profile.company}** — {profile.location}\n"
        f"Since: {profile.since}\n"
        f"Area: {profile.area}\n"
        f"Specialization: {profile.specialization}\n"
        f"\n"
        f"{profile.summary}\n"
        f"\n"
        f"## Current work\n"
        f"{work_desc}\n"
        f"## Education\n"
        f"{education}\n"
        f"\n"
        f"## Skills\n"
        f"{skills}\n"
        f"\n"
        f"## Personal projects\n"
        f"{projects}\n"
        f"\n"
        f"## Learning\n"
        f"{goals}\n"
    )
