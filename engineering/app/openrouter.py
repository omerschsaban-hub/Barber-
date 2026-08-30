from __future__ import annotations

import os

import httpx


class OpenRouterError(RuntimeError):
    """Backward-compatible error name for orchestration LLM failures."""


def _llm_endpoint_and_key() -> tuple[str, str | None]:
    """Use OpenAI-compatible configuration first, while retaining OpenRouter support."""
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
        return f"{base}/chat/completions", openai_key
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    return "https://openrouter.ai/api/v1/chat/completions", openrouter_key


async def structured_reasoning(
    system: str,
    user: str,
    *,
    model: str | None = None,
    timeout_s: float = 30.0,
) -> str:
    """Call an OpenAI-compatible model for orchestration-only reasoning.

    Deterministic engineering values remain outside the LLM. OPENAI_API_KEY and
    OPENAI_API_BASE support OpenAI or the sandbox-compatible proxy; OpenRouter is
    retained as a fallback for existing deployments.
    """
    endpoint, key = _llm_endpoint_and_key()
    if not key:
        raise OpenRouterError("OPENAI_API_KEY or OPENROUTER_API_KEY is not configured")
    selected = model or os.getenv("OPENAI_MODEL") or os.getenv("OPENROUTER_MODEL") or "gpt-5-mini"
    payload = {
        "model": selected,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=timeout_s) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
    if response.status_code >= 400:
        raise OpenRouterError(f"LLM request failed with HTTP {response.status_code}")
    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("LLM returned an invalid response") from exc
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("LLM returned empty content")
    return content
