import json
import subprocess
import re

path = "/Users/keyshuo/py-test/LLM-Project/src/llm_project/test/question.jsonl"
with open(path, encoding="utf-8") as f:
    datas = [json.loads(line) for line in f if line.strip()]

print("第一条示例:", datas[0])

LOG_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

def clean(text):
    lines = [l for l in text.splitlines() if not LOG_RE.match(l.strip())]
    return "\n".join(lines).replace("**", "").strip()

for item in datas:
    question = item["question"]

    r = subprocess.run(
        [
            "uv", "run", "python", "-m", "llm_project.agent.main",
            question,
            "--model", "qwen3:0.6b",
            "--stream",
        ],
        capture_output=True,
        text=True,
    )

    answer=clean(r.stdout.strip())

    print("=" * 60)
    print("Q:", question)
    print("A:", answer)
    print(r.stderr)