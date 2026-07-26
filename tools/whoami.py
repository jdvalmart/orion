"""Whoami tool — personal profile and context about the developer."""

import json
import logging
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from app import mcp
from orion_config import WHOAMI_FILE

logger = logging.getLogger(__name__)


class Education(BaseModel):
    degree: str
    institution: str
    year: str | int


class Work(BaseModel):
    role: str
    company: str
    area: str
    description: str
    stack: list[str] = Field(default_factory=list)


class Skills(BaseModel):
    machine_learning: list[str] = Field(default_factory=list)
    deep_learning: list[str] = Field(default_factory=list)
    nlp: list[str] = Field(default_factory=list)
    xai: list[str] = Field(default_factory=list)
    distributed: list[str] = Field(default_factory=list)
    deployment: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str
    stack: list[str] = Field(default_factory=list)
    repo: Optional[str] = None


class Profile(BaseModel):
    name: str
    role: str
    company: str
    location: str
    since: str
    area: str
    specialization: str
    summary: str
    work: dict = Field(default_factory=dict)
    education: list[Education] = Field(default_factory=list)
    skills: Optional[Skills] = None
    projects: list[Project] = Field(default_factory=list)
    learning_goals: list[str] = Field(default_factory=list)


def _load_profile() -> Profile:
    """Load the whoami profile from disk."""
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


def _format_education(education: list[Education]) -> str:
    lines = []
    for edu in education:
        lines.append(f"  - {edu.degree} — {edu.institution} ({edu.year})")
    return "\n".join(lines)


def _format_skills(skills: Optional[Skills]) -> str:
    if not skills:
        return ""
    lines = []
    for category in [
        ("ML Clásico", skills.machine_learning),
        ("Deep Learning", skills.deep_learning),
        ("NLP", skills.nlp),
        ("XAI", skills.xai),
        ("Sistemas Distribuidos", skills.distributed),
        ("Deployment", skills.deployment),
    ]:
        if category[1]:
            lines.append(f"  {category[0]}: {', '.join(category[1])}")
    if skills.languages:
        lines.append(f"  Lenguajes: {', '.join(skills.languages)}")
    if skills.frameworks:
        lines.append(f"  Frameworks: {', '.join(skills.frameworks)}")
    return "\n".join(lines)


def _format_projects(projects: list[Project]) -> str:
    lines = []
    for p in projects:
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

    current = profile.work.get("current", {})
    work_desc = ""
    if current:
        work_desc = (
            f"  {current.get('role', '')} en {current.get('company', '')} "
            f"({current.get('area', '')})\n"
            f"  {current.get('description', '')}\n"
            f"  Stack diario: {', '.join(current.get('stack', []))}\n"
        )

    education = _format_education(profile.education)
    skills = _format_skills(profile.skills)
    projects = _format_projects(profile.projects)
    goals = "\n".join(f"  - {g}" for g in profile.learning_goals)

    return (
        f"# {profile.name}\n"
        f"\n"
        f"**{profile.role}** en **{profile.company}** — {profile.location}\n"
        f"Desde: {profile.since}\n"
        f"Área: {profile.area}\n"
        f"Especialización: {profile.specialization}\n"
        f"\n"
        f"{profile.summary}\n"
        f"\n"
        f"## Trabajo actual\n"
        f"{work_desc}\n"
        f"## Formación\n"
        f"{education}\n"
        f"\n"
        f"## Habilidades\n"
        f"{skills}\n"
        f"\n"
        f"## Proyectos personales\n"
        f"{projects}\n"
        f"\n"
        f"## Aprendiendo\n"
        f"{goals}\n"
    )
