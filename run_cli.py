"""
CLI runner — no Streamlit required.
Usage:
    python run_cli.py "quantum reservoir computing"
    python run_cli.py "spiking neural networks" --model claude-haiku-4-5-20251001
"""

import sys
import os
import argparse
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Autonomous Research Agent CLI")
    parser.add_argument("topic", help="Research topic to investigate")
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Claude model to use",
    )
    parser.add_argument(
        "--max-iter", type=int, default=12, help="Max tool-call iterations (default 12)"
    )
    parser.add_argument(
        "--output", help="Save report to this file (optional)"
    )
    args = parser.parse_args()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌  ANTHROPIC_API_KEY not set. Add it to your .env file.")
        sys.exit(1)

    from agent import run_agent

    print(f"\n🔬  Researching: {args.topic}")
    print(f"    Model: {args.model}  |  Max iterations: {args.max_iter}\n")
    print("─" * 60)

    def on_step(step):
        if step["type"] == "thinking":
            snippet = step["text"][:100].replace("\n", " ")
            print(f"  🧠  [{step['iteration']}] {snippet}…")
        elif step["type"] == "tool_call":
            print(f"  🔧  [{step['iteration']}] {step['tool']}({list(step['input'].keys())})")
        elif step["type"] == "tool_result":
            print(f"  📋  {step['result_summary']}")

    result = run_agent(
        topic=args.topic,
        api_key=api_key,
        model=args.model,
        max_iterations=args.max_iter,
        on_step=on_step,
    )

    print("\n" + "─" * 60)
    print(f"✅  Done — {result['tool_calls']} tool calls, {len(result['steps'])} steps\n")

    if result["error"]:
        print(f"⚠️  Warning: {result['error']}\n")

    print(result["report"])

    if args.output:
        with open(args.output, "w") as f:
            f.write(result["report"])
        print(f"\n💾  Report saved to: {args.output}")


if __name__ == "__main__":
    main()
