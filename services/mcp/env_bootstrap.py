"""Minimal runtime configuration bridge for the MCP service."""
from __future__ import annotations

import json
import os


def _object(name: str) -> dict[str, str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{name} must contain valid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{name} must contain a JSON object")
    return {str(k): str(v) for k, v in value.items() if v is not None}


def _file_object(path: str) -> dict[str, str]:
    try:
        with open(path, encoding="utf-8") as handle:
            value = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items() if v is not None}


def load() -> None:
    revenuecat = _object("REVENUECAT_CONFIG")
    if not revenuecat:
        revenuecat = _file_object(os.getenv("REVENUECAT_CONFIG_FILE", "/etc/secrets/fabrient-revenuecat-config.json"))
    for key, env_name in (("secret_api_key", "REVENUECAT_SECRET_API_KEY"), ("webhook_auth", "REVENUECAT_WEBHOOK_AUTH"), ("webhook_signing_secret", "REVENUECAT_WEBHOOK_SIGNING_SECRET")):
        if revenuecat.get(key) and not os.getenv(env_name):
            os.environ[env_name] = revenuecat[key]

    os.environ.setdefault("OPENAI_MODEL", "gpt-5.6")
    os.environ.setdefault("FABRIENT_ENGINE_URL", "https://fabrient-engineering.onrender.com")
    os.environ.setdefault("FABRIENT_MCP_TIMEOUT", "120")


load()
