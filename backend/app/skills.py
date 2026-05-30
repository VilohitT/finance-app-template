"""Skill loader: reads SKILL.md files for slash-command invocations."""

from pathlib import Path
from typing import Optional

from . import config


def list_skills() -> list[dict]:
    """Return all available skills with their descriptions."""
    skills = []
    if not config.SKILLS_ROOT.exists():
        return skills
    for skill_dir in sorted(config.SKILLS_ROOT.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        skills.append({
            "name": skill_dir.name,
            "description": _extract_description(skill_md),
        })
    return skills


def load_skill(name: str) -> Optional[str]:
    """Return the full SKILL.md content for a named skill, or None if missing."""
    skill_md = config.SKILLS_ROOT / name / "SKILL.md"
    if not skill_md.exists():
        return None
    return skill_md.read_text()


def _extract_description(skill_md: Path) -> str:
    """Pull the `description:` field from the SKILL.md frontmatter."""
    content = skill_md.read_text()
    # Frontmatter is between --- markers at the top.
    if not content.startswith("---"):
        return ""
    end_idx = content.find("\n---", 3)
    if end_idx == -1:
        return ""
    frontmatter = content[3:end_idx]
    # Description field can span multiple lines; capture until next field or end.
    lines = frontmatter.splitlines()
    desc_lines: list[str] = []
    in_desc = False
    for line in lines:
        if line.startswith("description:"):
            in_desc = True
            desc_lines.append(line[len("description:"):].strip())
        elif in_desc and line and not line[0].isalpha():
            # Continuation line (indented).
            desc_lines.append(line.strip())
        elif in_desc and ":" in line and line.split(":")[0].strip().isidentifier():
            # New field — stop.
            break
        elif in_desc:
            desc_lines.append(line.strip())
    return " ".join(desc_lines).strip()
