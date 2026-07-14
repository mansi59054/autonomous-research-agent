# evals/run_evals.py
import os
import json
import datetime

from dotenv import load_dotenv
load_dotenv()

from evals.test_cases import TEST_CASES
from evals.rubric import score_run
from agent.core import run_agent


def run_all_evals():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set. Check your .env file is loaded.")

    results = []

    for case in TEST_CASES:
        topic = case["topic"]
        print(f"Running agent on: {topic}")

        result = run_agent(topic, api_key=api_key)

        final_report = result["report"]
        run_log = result["steps"]
        tool_call_count = result["tool_calls"]
        error = result["error"]

        if error:
            print(f"  ⚠️ Agent returned an error: {error}")

        scores = score_run(topic, run_log, final_report)

        tool_check_passed = tool_call_count >= case["min_citations"]

        results.append({
            "topic": topic,
            "tool_calls": tool_call_count,
            "tool_check_passed": tool_check_passed,
            "error": error,
            "rubric_scores": scores,
        })

        print(f"  Tool calls: {tool_call_count} (need >= {case['min_citations']}) — "
              f"{'PASS' if tool_check_passed else 'FAIL'}")

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = f"evals/results/eval_run_{timestamp}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved results to {output_path}")
    return results


if __name__ == "__main__":
    run_all_evals()
