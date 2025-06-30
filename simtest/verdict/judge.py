import os
import openai
from typing import Literal
from dataclasses import dataclass

JudgeVerdict = Literal["PASS", "FAIL", "EXPLAIN"]

@dataclass
class Judgement:
    verdict: JudgeVerdict
    explanation: str

class LLMJudge:
    def __init__(self):
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def evaluate(self, node_id: str, tool_name: str, task: str, output: dict) -> Judgement:
        prompt = f"""
You are evaluating an AI agent output for semantic correctness.

Task: "{task}"
Tool: {tool_name}
Output: {output}

Respond with JSON in this format:
{{ "verdict": "PASS" | "FAIL" | "EXPLAIN", "explanation": "short rationale" }}
"""

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            temperature=0,
            response_format="json",
            messages=[
                {"role": "user", "content": prompt.strip()}
            ]
        )

        parsed = response.choices[0].message.content
        parsed_json = eval(parsed) if isinstance(parsed, str) else parsed  # stub-safe

        return Judgement(
            verdict=parsed_json.get("verdict", "EXPLAIN"),
            explanation=parsed_json.get("explanation", "")
        )
