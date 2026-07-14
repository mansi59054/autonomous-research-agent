# evals/rubric.py
import os
import json
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

RUBRIC = {
    "reasoning_coherence": "Did each reasoning step logically follow from the previous one, without contradictions or random jumps?",
    "tool_call_appropriateness": "Did the agent call tools that were actually relevant to the research topic, avoiding unnecessary or off-topic calls?",
    "output_structure_conformance": "Does the final report follow clear markdown structure with headers and a references section?",
    "citation_accuracy": "Do the citations in the report plausibly match papers that would exist for this topic, without fabricated titles or authors?",
}

def score_run(topic, run_log, final_report):
    log_text = json.dumps(run_log, indent=2, default=str)

    scores = {}
    for criterion, question in RUBRIC.items():
        prompt = f"""You are grading an AI research agent's output.

Research topic: {topic}
Question to grade: {question}

Agent's step-by-step run log:
{log_text}

Agent's final report:
{final_report}

Respond in exactly this format:
SCORE: <1-5>
REASON: <one sentence>
"""
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        scores[criterion] = response.content[0].text

    return scores
