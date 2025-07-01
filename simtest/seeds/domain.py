from pathlib import Path
from jinja2 import Template
import os
import openai
import ast
from simtest.seeds.types import Seed

class DomainSeedGenerator:
    def __init__(self, domain: str, tools: list[str], count: int = 20):
        self.domain = domain
        self.tools = tools
        self.count = count

    def generate(self) -> list[Seed]:
        prompt_path = Path("prompts/domain_seed.jinja")
        with open(prompt_path) as f:
            template = Template(f.read())

        prompt = template.render(domain=self.domain, tools=self.tools, count=self.count)

        model = "gpt-4o" if os.getenv("USE_GPT_4O", "1") == "1" else "gpt-3.5-turbo"
        response = openai.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )

        content = response.choices[0].message.content.strip()

        def clean(text: str) -> str:
            return text.strip().strip(",").strip('"').strip("'").strip("`")

        seeds: list[Seed] = []

        try:
            raw_list = ast.literal_eval(content)
            if isinstance(raw_list, list):
                for task in raw_list:
                    task = clean(task)
                    if isinstance(task, str) and 3 < len(task.split()) <= 20:
                        seeds.append(Seed.raw(task))
        except Exception:
            for line in content.splitlines():
                line = clean(line)
                if line.lower().startswith("```"):
                    continue
                if line and any(char.isalnum() for char in line) and 3 < len(line.split()) <= 20:
                    seeds.append(Seed.raw(line))

        return seeds


