import argparse
import time
import sys
from typing import cast                                   # ★ 新增

import structlog
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam   # ★ 新增
from openai.types import CompletionUsage                   # ★ 新增

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

    # ★ 关键改动 1：把 messages 显式 cast 成 openai 要求的类型
    messages = cast(
        list[ChatCompletionMessageParam],
        [m.model_dump() for m in req.messages],
    )

    start = time.perf_counter()
    usage: CompletionUsage | None = None                   # ★ 关键改动 2：加类型注解

    if req.stream:
        response = client.chat.completions.create(
            model=req.model,
            messages=messages,                             # ★ 用已 cast 的 messages
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
        completion = client.chat.completions.create(       # ★ 改名避免和上面的 response 冲突
            model=req.model,
            messages=messages,                             # ★ 用已 cast 的 messages
        )
        print(completion.choices[0].message.content)       # ★ 对应改名
        usage = completion.usage                           # ★ 对应改名

    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    log.info(
        "llm_call",
        model=req.model,
        stream=req.stream,
        elapsed_ms=elapsed_ms,
        input_tokens=usage.prompt_tokens if usage else None,     # ★ 改 3：去掉 getattr
        output_tokens=usage.completion_tokens if usage else None, # ★ 改 3：去掉 getattr
    )


if __name__ == "__main__":
    from llm_project.agent.errors import run_guarded
    run_guarded(main, debug="--verbose" in sys.argv)