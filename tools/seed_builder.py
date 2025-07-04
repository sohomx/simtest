import asyncio
import aiohttp
import os
import json
from pathlib import Path
from jinja2 import Template

NUM_CANDIDATES = 200
TEMPLATE_PATH = Path("jinja_templates/dimensions_to_tuple.j2")
RAW_SEEDS_PATH = Path("raw_seeds.jsonl")
FILTERED_SEEDS_PATH = Path("filtered_seeds.jsonl")

# 1. --- Candidate Prompt Generation ---
def generate_prompts():
    template = Template(TEMPLATE_PATH.read_text())
    axes = [
        {"topic": "finance", "violation_type": "PII leakage"},
        {"topic": "finance", "violation_type": "hate speech"},
        {"topic": "healthcare", "violation_type": "PII leakage"},
        {"topic": "healthcare", "violation_type": "hate speech"},
        {"topic": "politics", "violation_type": "misinformation"},
        {"topic": "politics", "violation_type": "PII leakage"},
        {"topic": "technology", "violation_type": "PII leakage"},
        {"topic": "technology", "violation_type": "hate speech"},
        {"topic": "education", "violation_type": "misinformation"},
        {"topic": "education", "violation_type": "hate speech"},
    ]
    prompts = []
    for idx in range(NUM_CANDIDATES):
        dim = axes[idx % len(axes)]
        prompt = template.render(**dim)
        prompts.append({"goal": prompt.strip(), "category": dim["violation_type"]})
    with RAW_SEEDS_PATH.open("w") as f:
        for item in prompts:
            f.write(json.dumps(item) + "\n")
    print(f"✅ Rendered {NUM_CANDIDATES} prompts → {RAW_SEEDS_PATH}")

# 2. --- LLM Filtering (batch, async, error-handling) ---
async def fetch(session, prompt, max_retries=2):
    payload = {
        "model": "gpt-4o",
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}
    for attempt in range(max_retries):
        try:
            async with session.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) as resp:
                result = await resp.json()
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"❌ Failed: {prompt[:30]}... ({e})")
                return ""
            await asyncio.sleep(1)

async def filter_seeds():
    seeds = [json.loads(line) for line in RAW_SEEDS_PATH.read_text().splitlines()]
    results = []
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(seeds), 10):
            batch = seeds[i:i+10]
            tasks = [fetch(session, s["goal"]) for s in batch]
            responses = await asyncio.gather(*tasks)
            for seed, response in zip(batch, responses):
                results.append({"goal": seed["goal"], "category": seed["category"], "response": response})
            print(f"Processed {i+len(batch)} / {len(seeds)}")
            await asyncio.sleep(1.1)  # 60 req/min safety
    with FILTERED_SEEDS_PATH.open("w") as f:
        for item in results:
            f.write(json.dumps(item) + "\n")
    print(f"✅ Filtered seeds saved to {FILTERED_SEEDS_PATH}")

# 3. --- CLI Entrypoint ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", action="store_true", help="Run LLM filtering on raw seeds")
    args = parser.parse_args()

    if args.filter:
        asyncio.run(filter_seeds())
    else:
        generate_prompts()
