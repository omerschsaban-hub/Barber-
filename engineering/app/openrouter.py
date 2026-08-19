from __future__ import annotations
import os
import httpx

class OpenRouterError(RuntimeError):
    pass

async def structured_reasoning(system: str, user: str, *, model: str | None = None, timeout_s: float = 30.0) -> str:
    """Optional orchestration-only LLM call. Engineering values must be computed elsewhere."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise OpenRouterError("OPENROUTER_API_KEY is not configured")
    selected = model or os.getenv("OPENROUTER_MODEL")
    if not selected:
        raise OpenRouterError("OPENROUTER_MODEL is not configured")
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
        response = await client.post("https://openrouter.ai/api/v1/chat/completions", json=payload, headers=headers)
    if response.status_code >= 400:
        raise OpenRouterError(f"OpenRouter request failed with HTTP {response.status_code}")
    data = response.json()
    try:
        return str(data["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError("OpenRouter returned an invalid response") from exc
