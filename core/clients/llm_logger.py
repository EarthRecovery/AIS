"""每次大模型调用的明细记录器（LangChain 异步回调）。

挂到各 Agent 的 ChatOpenAI 上（callbacks=[get_llm_logger()], tags=["<agent>"]），
on_chat_model_start 抓 prompt，on_llm_end 抓回复+用量，写入 ais_llm_logs。
全程 best-effort：任何异常都吞掉，绝不影响正常的 LLM 调用。
"""

import time

from langchain_core.callbacks import AsyncCallbackHandler


def _fmt_messages(messages) -> str:
    parts = []
    for batch in (messages or []):
        for m in batch:
            role = getattr(m, "type", None) or m.__class__.__name__
            content = getattr(m, "content", "")
            if isinstance(content, list):
                content = " ".join(str(x) for x in content)
            parts.append(f"[{role}]\n{content}")
    return "\n\n".join(parts)


def _extract(response):
    """从 LLMResult 取 (回复文本, model, usage dict)。"""
    text, model, usage = "", None, {}
    try:
        gens = response.generations or []
        chunks = []
        for batch in gens:
            for g in batch:
                t = getattr(g, "text", "") or ""
                if not t:
                    msg = getattr(g, "message", None)
                    t = getattr(msg, "content", "") if msg else ""
                chunks.append(t)
        text = "\n".join(c for c in chunks if c)
    except Exception:
        pass
    out = getattr(response, "llm_output", None) or {}
    model = out.get("model_name") or out.get("model")
    tu = out.get("token_usage") or out.get("usage") or {}
    if tu:
        usage = {"prompt_tokens": tu.get("prompt_tokens"),
                 "completion_tokens": tu.get("completion_tokens"),
                 "total_tokens": tu.get("total_tokens")}
    else:
        # 流式等情况：尝试从 message.usage_metadata 取
        try:
            md = response.generations[0][0].message.usage_metadata or {}
            usage = {"prompt_tokens": md.get("input_tokens"),
                     "completion_tokens": md.get("output_tokens"),
                     "total_tokens": md.get("total_tokens")}
        except Exception:
            usage = {}
    return text, model, usage


class DBLLMLogger(AsyncCallbackHandler):
    def __init__(self):
        self._pending = {}   # run_id -> {prompt, tags, t0}

    async def on_chat_model_start(self, serialized, messages, *, run_id, tags=None, **kwargs):
        try:
            self._pending[str(run_id)] = {"prompt": _fmt_messages(messages),
                                          "tags": tags or [], "t0": time.monotonic()}
        except Exception:
            pass

    async def on_llm_start(self, serialized, prompts, *, run_id, tags=None, **kwargs):
        # 非 chat 模型的兜底
        try:
            if str(run_id) not in self._pending:
                self._pending[str(run_id)] = {"prompt": "\n\n".join(prompts or []),
                                              "tags": tags or [], "t0": time.monotonic()}
        except Exception:
            pass

    async def on_llm_end(self, response, *, run_id, **kwargs):
        info = self._pending.pop(str(run_id), None)
        try:
            text, model, usage = _extract(response)
            await self._save(info, text, model, usage, ok=True, error=None)
        except Exception:
            pass

    async def on_llm_error(self, error, *, run_id, **kwargs):
        info = self._pending.pop(str(run_id), None)
        try:
            await self._save(info, "", None, {}, ok=False, error=str(error)[:2000])
        except Exception:
            pass

    async def _save(self, info, response, model, usage, ok, error):
        from storage.db import SessionLocal
        from storage.models.llm_log import LLMLog
        info = info or {}
        tags = info.get("tags") or []
        agent = tags[0] if tags else None
        t0 = info.get("t0")
        dur = int((time.monotonic() - t0) * 1000) if t0 else None
        usage = usage or {}
        async with SessionLocal() as db:
            db.add(LLMLog(
                agent=agent, model=model, prompt=info.get("prompt"), response=response,
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=usage.get("completion_tokens"),
                total_tokens=usage.get("total_tokens"),
                duration_ms=dur, ok=ok, error=error))
            await db.commit()


_LOGGER = None


def get_llm_logger() -> DBLLMLogger:
    global _LOGGER
    if _LOGGER is None:
        _LOGGER = DBLLMLogger()
    return _LOGGER
