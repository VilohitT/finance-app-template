"""Agent loop: runs Claude with a skill prompt + custom tools, streams to client.

Uses the Anthropic SDK directly (not Managed Agents) because our tools execute
on the user's local filesystem, not in an Anthropic-hosted container.

Streaming events are yielded as dicts that the WebSocket layer forwards to the
frontend as JSON. Event shape:
  {"type": "text", "delta": "..."}
  {"type": "tool_use", "name": "read_file", "input": {...}, "id": "..."}
  {"type": "tool_result", "tool_use_id": "...", "output": "...", "is_error": bool}
  {"type": "done", "stop_reason": "end_turn"}
  {"type": "error", "message": "..."}
"""

import logging
from typing import AsyncIterator

import anthropic

from . import config, settings, skills, tools

logger = logging.getLogger(__name__)


SYSTEM_PROMPT_HEADER = """You are operating in an Indian-context personal investment planning system. The user is interacting with you via a chat UI; their foundation files (goals.md, principles.md, user-principles.md, portfolio.md, decisions-log.md, laws/) live in the project root and you can read and write them via the read_file, write_file, and edit_file tools. Scripts live in scripts/ and you can run them via the bash tool. Sub-portfolio names, sleeve targets, glide paths, regime, and routing rules come from user-principles.md — never hardcode them.

The skill that was invoked appears below. Follow it exactly.

---

"""


async def run_skill(
    skill_name: str,
    user_message: str,
    conversation_history: list[dict] | None = None,
) -> AsyncIterator[dict]:
    """Run a skill against the Anthropic API and yield streaming events."""
    s = settings.load()
    if not s.anthropic_api_key:
        yield {"type": "error", "message": "No Anthropic API key configured. Visit settings."}
        return

    skill_content = skills.load_skill(skill_name)
    if skill_content is None:
        yield {"type": "error", "message": f"Skill not found: {skill_name}"}
        return

    system_prompt = SYSTEM_PROMPT_HEADER + skill_content
    messages = list(conversation_history or [])
    messages.append({"role": "user", "content": user_message})

    client = anthropic.AsyncAnthropic(api_key=s.anthropic_api_key)
    async for event in _agent_loop(client, system_prompt, messages, s):
        yield event


async def _agent_loop(
    client: anthropic.AsyncAnthropic,
    system_prompt: str,
    messages: list[dict],
    s: settings.Settings,
) -> AsyncIterator[dict]:
    """Inner loop: streams Claude responses, executes tools, continues until end_turn."""
    max_turns = 30
    turn = 0
    while turn < max_turns:
        turn += 1
        try:
            async with client.messages.stream(
                model=s.model,
                max_tokens=config.MAX_TOKENS,
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                thinking={"type": "adaptive"},
                output_config={"effort": s.effort},
                tools=tools.TOOLS_SCHEMA,
                messages=messages,
            ) as stream:
                async for raw_event in stream:
                    forwarded = _forward_event(raw_event)
                    if forwarded is not None:
                        yield forwarded
                final_message = await stream.get_final_message()
        except anthropic.APIStatusError as exc:
            yield {"type": "error", "message": f"API error: {exc.message}"}
            return
        except Exception as exc:
            logger.exception("agent loop error")
            yield {"type": "error", "message": f"Unexpected error: {exc}"}
            return

        # Append assistant turn (always — even on tool_use).
        messages.append({"role": "assistant", "content": final_message.content})

        if final_message.stop_reason == "end_turn":
            yield {"type": "done", "stop_reason": "end_turn"}
            return
        if final_message.stop_reason == "max_tokens":
            yield {"type": "done", "stop_reason": "max_tokens"}
            return
        if final_message.stop_reason == "refusal":
            yield {"type": "done", "stop_reason": "refusal"}
            return
        if final_message.stop_reason != "tool_use":
            yield {"type": "done", "stop_reason": final_message.stop_reason or "unknown"}
            return

        # Execute tool calls, send results back.
        tool_results = []
        for block in final_message.content:
            if block.type != "tool_use":
                continue
            output, is_error = tools.execute(block.name, dict(block.input))
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                    "is_error": is_error,
                }
            )
            yield {
                "type": "tool_result",
                "tool_use_id": block.id,
                "output": output,
                "is_error": is_error,
            }
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    yield {"type": "error", "message": f"Reached max turns ({max_turns}) without completion."}


def _forward_event(event) -> dict | None:
    """Translate Anthropic SDK stream events to our wire format."""
    et = getattr(event, "type", None)
    if et == "content_block_delta":
        delta = getattr(event, "delta", None)
        delta_type = getattr(delta, "type", None)
        if delta_type == "text_delta":
            return {"type": "text", "delta": delta.text}
        if delta_type == "thinking_delta":
            return {"type": "thinking", "delta": delta.thinking}
    if et == "content_block_start":
        block = getattr(event, "content_block", None)
        block_type = getattr(block, "type", None)
        if block_type == "tool_use":
            return {"type": "tool_use_start", "name": block.name, "id": block.id}
    if et == "message_delta":
        usage = getattr(event, "usage", None)
        if usage is not None:
            return {
                "type": "usage",
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
                "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
                "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None),
            }
    return None
