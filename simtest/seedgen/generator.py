import os
import random
import openai
from typing import Literal
from dataclasses import dataclass
from simtest.seeds.loader import Seed
from tiktoken import encoding_for_model

MODEL = "gpt-3.5-turbo"
INPUT_COST_PER_1K = 0.0005   # prompt
OUTPUT_COST_PER_1K = 0.0015  # completion
MAX_COST = 1.00              # enforce <$1
MAX_TOKENS = 150             # completion cap

@dataclass
class CostReport:
    total_tokens: int
    total_cost: float
    prompt_tokens: int
    output_tokens: int

class SeedGenerator:
    def __init__(self, suite: str, n: int = 100, domain: str = "", rng_seed: int = 42):
        self.suite = suite
        self.n = n
        self.domain = domain
        self.rng = random.Random(rng_seed)
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    def _count_tokens(self, text: str) -> int:
        enc = encoding_for_model(MODEL)
        return len(enc.encode(text))

    def generate(self) -> tuple[list[Seed], CostReport]:
        results = []
        total_prompt_tokens = 0
        total_output_tokens = 0

        for i in range(self.n):
            prompt = f"Generate a valid input for the `{self.suite}` tool. Domain: {self.domain}"
            completion = openai.chat.completions.create(
                model=MODEL,
                temperature=0,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MAX_TOKENS,
            )
            text = completion.choices[0].message.content.strip()

            ptoks = self._count_tokens(prompt)
            otoks = self._count_tokens(text)

            total_prompt_tokens += ptoks
            total_output_tokens += otoks

            total_cost = (
                (total_prompt_tokens / 1000) * INPUT_COST_PER_1K +
                (total_output_tokens / 1000) * OUTPUT_COST_PER_1K
            )

            if total_cost > MAX_COST:
                print("⚠️  Cost limit reached. Stopping early.")
                break

            results.append(
                Seed(
                    node_id=self.suite,
                    input={"raw": text},
                    expect=None,
                    vars={},
                    description="LLM-generated seed",
                )
            )

        total_tokens = total_prompt_tokens + total_output_tokens
        final_cost = (
            (total_prompt_tokens / 1000) * INPUT_COST_PER_1K +
            (total_output_tokens / 1000) * OUTPUT_COST_PER_1K
        )

        return results, CostReport(
            total_tokens=total_tokens,
            total_cost=final_cost,
            prompt_tokens=total_prompt_tokens,
            output_tokens=total_output_tokens
        )

