import argparse
import time

import structlog
from openai import OpenAI
from pydantic import ValidationError

from llm_project.agent.config import settings
from llm_project.agent.logging_config import configure_logging
from llm_project.api.schemas import ChatRequest, Message

configure_logging()
log = structlog.get_logger()

client = OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="CLI 问答 v0")
    parser.add_argument("question")
    parser.add_argument("--model", default="qwen3:0.6b")
    parser.add_argument("--stream", action="store_true")
    args = parser.parse_args()

    req = ChatRequest(
        model=args.model,
        messages=[Message(role="user", content=args.question)],
        stream=args.stream,
    )

    start = time.perf_counter()
    usage = None

    if req.stream:
        response = client.chat.completions.create(
            model=req.model,
            messages=[m.model_dump() for m in req.messages],
            stream=True,
            stream_options={"include_usage": True},
        )
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
            if chunk.usage:
                usage = chunk.usage
        print()
    else:
        response = client.chat.completions.create(
            model=req.model,
            messages=[m.model_dump() for m in req.messages],
        )
        print(response.choices[0].message.content)
        usage = response.usage

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    log.info(
        "llm_call",
        model=req.model,
        stream=req.stream,
        elapsed_ms=elapsed_ms,
        input_tokens=getattr(usage, "prompt_tokens", None),
        output_tokens=getattr(usage, "completion_tokens", None),
    )


if __name__ == "__main__":
    try:
        main()
    except ValidationError as e:
        log.error("配置错误，请检查 .env 文件", errors=e.errors())
        raise SystemExit(1) from None