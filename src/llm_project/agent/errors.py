"""把底层异常翻译成人类可读的提示。"""
import os
import sys
import traceback
from typing import Callable                              # ★ 关键：之前没 import，导致 run_guarded 的 fn 报未定义

from pydantic import ValidationError                    # ★ 新增：用于精确窄化


def friendly_hint(e: BaseException) -> str:
    cur: BaseException | None = e                        # ★ 加标注，后续赋值 BaseException | None
    seen: set[int] = set()                               # ★ 加标注，解决 set[Unknown]

    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        name = type(cur).__name__
        mod = type(cur).__module__ or ""

        if "httpx" in mod:
            if name == "ConnectError":
                return (
                    "无法连接到 LLM 服务。\n"
                    "  1) OPENAI_BASE_URL 是否正确\n"
                    "  2) 服务是否启动（如 ollama serve）"
                )
            if name == "TimeoutException":
                return "请求超时，服务可能未响应。"
            if name == "HTTPStatusError":
                resp = getattr(cur, "response", None)             # ★ 改：不要 cur.response
                req = getattr(cur, "request", None)               # ★ 改：不要 cur.request
                code = getattr(resp, "status_code", "?")          # ★ 改：从 resp 取
                url = str(getattr(req, "url", "?"))               # ★ 改：从 req 取
                if code == 404:
                    return (
                        f"接口不存在 (404): {url}\n"
                        "  Ollama 的 base_url 应为 http://localhost:11434/v1"
                    )
                if code == 401:
                    return "认证失败 (401)，检查 OPENAI_API_KEY。"
                if code == 429:
                    return "请求过多 (429)，稍后重试。"
                return f"HTTP {code}: {url}"

        if mod.startswith("openai"):
            msg = str(cur)
            if "Connection" in name or "Timeout" in name:
                return f"{name}: 无法连接服务，检查 base_url 和服务状态"
            if "404" in msg:
                return f"404：接口/模型不存在。\n  详情: {msg[:200]}"
            if "not found" in msg.lower():
                return f"模型不存在: {msg[:200]}\n  ollama list 看看模型名"
            return f"{name}: {msg[:300]}"

        if isinstance(cur, ValidationError):                       # ★ 改用 isinstance 窄化，不依赖 getattr
            missing: list[str] = []
            for err in cur.errors():
                if err.get("type") == "missing":
                    loc = err["loc"]                               # ★ loc 是必填字段，直接取
                    missing.append(str(loc[0]) if loc else "?")
            if missing:
                return (
                    "缺少环境变量: " + ", ".join(missing)
                    + "\n  检查项目根目录 .env"
                )
            return f"配置校验失败: {str(cur)[:300]}"

        cur = cur.__cause__ or cur.__context__

    return f"{type(e).__name__}: {e}"


def run_guarded(fn: Callable[[], None], *, debug: bool = False) -> None:   # ★ Callable 已 import，fn 有类型
    """在入口处调用：接住所有异常 → 打印人话 → 退出码 1。"""
    try:
        fn()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\n[中断]", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n[错误] {friendly_hint(e)}", file=sys.stderr)
        if debug or os.getenv("DEBUG"):
            print("\n--- 完整 traceback ---", file=sys.stderr)
            traceback.print_exc()
        sys.exit(1)