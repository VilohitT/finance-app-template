"""Tool definitions for the agent: Read, Write, Edit, Bash.

Tools execute on the user's local filesystem (mounted as the project root in
Docker). Path validation restricts operations to allowed roots — the agent
cannot read or write outside the project tree.
"""

import subprocess
from pathlib import Path
from typing import Any

from . import config


# Tool schemas in the Anthropic API format.
TOOLS_SCHEMA: list[dict[str, Any]] = [
    {
        "name": "read_file",
        "description": (
            "Read a file from the project directory. Use for reading goals.md, "
            "portfolio.md, principles.md, user-principles.md, decisions-log.md, "
            "laws/*.md, and any other markdown or data file in the project."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from the project root, e.g. 'goals.md' or 'laws/equity-mf.md'.",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": (
            "Write or overwrite a file in the project directory. Use for creating "
            "or fully rewriting foundation files. For surgical edits to existing "
            "files, prefer edit_file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from the project root."},
                "content": {"type": "string", "description": "Full file content to write."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace a specific string in an existing file with new content. "
            "Use for surgical edits to foundation files (goals.md, portfolio.md, "
            "user-principles.md, etc.). The old_string must match exactly once."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Relative path from the project root."},
                "old_string": {"type": "string", "description": "Exact text to find. Must match once."},
                "new_string": {"type": "string", "description": "Replacement text."},
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    {
        "name": "bash",
        "description": (
            "Run a shell command in the project root. Use for running Python "
            "scripts (scripts/discover.py, scripts/fetch_nav.py, scripts/"
            "render_portfolio.py, etc.) and SQLite queries against data/market.db. "
            "Do not use for network operations beyond what the scripts already do."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute."},
                "timeout_seconds": {
                    "type": "integer",
                    "description": "Optional timeout in seconds (default 60, max 300).",
                },
            },
            "required": ["command"],
        },
    },
]


def execute(name: str, tool_input: dict[str, Any]) -> tuple[str, bool]:
    """Run a tool and return (output, is_error)."""
    try:
        if name == "read_file":
            return _read_file(tool_input["path"]), False
        if name == "write_file":
            return _write_file(tool_input["path"], tool_input["content"]), False
        if name == "edit_file":
            return _edit_file(
                tool_input["path"], tool_input["old_string"], tool_input["new_string"]
            ), False
        if name == "bash":
            timeout = min(int(tool_input.get("timeout_seconds", 60)), 300)
            return _bash(tool_input["command"], timeout), False
        return f"Unknown tool: {name}", True
    except Exception as exc:
        return f"Error executing {name}: {exc}", True


def _resolve_in(roots: list[Path], rel_path: str) -> Path:
    """Resolve a relative path against allowed roots; reject path traversal."""
    candidate = (config.PROJECT_ROOT / rel_path).resolve()
    for root in roots:
        try:
            candidate.relative_to(root)
            return candidate
        except ValueError:
            continue
    allowed = ", ".join(str(r) for r in roots)
    raise PermissionError(f"Path {rel_path} is outside allowed roots ({allowed}).")


def _read_file(rel_path: str) -> str:
    path = _resolve_in(config.ALLOWED_READ_ROOTS, rel_path)
    if not path.exists():
        return f"File not found: {rel_path}"
    if path.is_dir():
        return f"Path is a directory: {rel_path}"
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return f"File is not text/UTF-8: {rel_path}"
    # Cap at ~200KB to protect context.
    if len(content) > 200_000:
        return content[:200_000] + f"\n\n[truncated — file is {len(content):,} chars]"
    return content


def _write_file(rel_path: str, content: str) -> str:
    path = _resolve_in(config.ALLOWED_WRITE_ROOTS, rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content):,} chars to {rel_path}"


def _edit_file(rel_path: str, old_string: str, new_string: str) -> str:
    path = _resolve_in(config.ALLOWED_WRITE_ROOTS, rel_path)
    if not path.exists():
        return f"File not found: {rel_path}"
    content = path.read_text(encoding="utf-8")
    occurrences = content.count(old_string)
    if occurrences == 0:
        return f"old_string not found in {rel_path}"
    if occurrences > 1:
        return f"old_string occurs {occurrences} times in {rel_path}; needs to be unique"
    new_content = content.replace(old_string, new_string, 1)
    path.write_text(new_content, encoding="utf-8")
    return f"Edited {rel_path}"


def _bash(command: str, timeout: int) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=str(config.PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"
    parts: list[str] = []
    if result.stdout:
        parts.append(result.stdout)
    if result.stderr:
        parts.append(f"[stderr]\n{result.stderr}")
    parts.append(f"[exit {result.returncode}]")
    output = "\n".join(parts)
    if len(output) > 100_000:
        output = output[:100_000] + f"\n\n[truncated — output was {len(output):,} chars]"
    return output
