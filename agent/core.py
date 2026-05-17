"""
Core agent loop — implements the ReAct pattern:
  Think → Act (tool call) → Observe (tool result) → Think → ...
until Claude decides to write the final report.
"""

import json
import anthropic

from tools import TOOL_SCHEMAS, run_tool
from agent.prompts import SYSTEM_PROMPT, build_user_prompt


def run_agent(
    topic: str,
    api_key: str,
    model: str = "claude-sonnet-4-5",
    max_iterations: int = 15,
    on_step=None,          # callback(step_dict) for streaming UI updates
) -> dict:
    """
    Run the research agent on `topic`.

    Args:
        topic: Research topic string
        api_key: Anthropic API key
        model: Claude model to use
        max_iterations: Safety cap on tool-call rounds
        on_step: Optional callback called after each step with a status dict

    Returns:
        {
            "report": str,          # Final markdown report
            "steps": list[dict],    # All intermediate steps
            "tool_calls": int,      # Total tool invocations
            "error": str | None,
        }
    """
    client = anthropic.Anthropic(api_key=api_key)

    messages = [
        {"role": "user", "content": build_user_prompt(topic)}
    ]

    steps = []
    tool_call_count = 0
    report = None
    error = None

    for iteration in range(max_iterations):
        # ── Call Claude ──────────────────────────────────────────────────────
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        # ── Check stop reason ────────────────────────────────────────────────
        stop_reason = response.stop_reason  # "tool_use" | "end_turn" | "max_tokens"

        # Collect text blocks
        text_blocks = [b.text for b in response.content if b.type == "text"]
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        # Record thinking / partial text
        if text_blocks:
            step = {
                "type": "thinking",
                "iteration": iteration + 1,
                "text": "\n".join(text_blocks),
            }
            steps.append(step)
            if on_step:
                on_step(step)

        # ── If no more tool calls → final answer ─────────────────────────────
        if stop_reason == "end_turn" or not tool_use_blocks:
            report = "\n".join(text_blocks)
            break

        # ── Process tool calls ────────────────────────────────────────────────
        # Append Claude's full response (with tool_use blocks) to history
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_block in tool_use_blocks:
            tool_name = tool_block.name
            tool_input = tool_block.input
            tool_use_id = tool_block.id
            tool_call_count += 1

            step = {
                "type": "tool_call",
                "iteration": iteration + 1,
                "tool": tool_name,
                "input": tool_input,
            }
            steps.append(step)
            if on_step:
                on_step(step)

            # ── Execute the tool ──────────────────────────────────────────────
            result = run_tool(tool_name, tool_input)

            result_step = {
                "type": "tool_result",
                "iteration": iteration + 1,
                "tool": tool_name,
                "result_summary": _summarise_result(result),
            }
            steps.append(result_step)
            if on_step:
                on_step(result_step)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": json.dumps(result),
                }
            )

        # Append all tool results in one user message
        messages.append({"role": "user", "content": tool_results})

    else:
        error = f"Reached max iterations ({max_iterations}) without a final report."
        report = "\n".join(
            b.text for b in response.content if b.type == "text"
        ) or "No report generated."

    return {
        "report": report,
        "steps": steps,
        "tool_calls": tool_call_count,
        "error": error,
    }


def _summarise_result(result: dict) -> str:
    """Create a short human-readable summary of a tool result for the UI."""
    if "error" in result:
        return f"❌ Error: {result['error']}"
    if "papers" in result:
        n = result.get("count", len(result["papers"]))
        source = result.get("source", "")
        titles = [p.get("title", "")[:60] for p in result["papers"][:3]]
        return f"✅ {source}: found {n} papers — e.g. {'; '.join(titles)}"
    if "content" in result:
        return f"✅ Scraped {result['url']} ({result['total_chars']} chars)"
    if "title" in result:
        return f"✅ Fetched: {result['title'][:80]}"
    return "✅ Done"
