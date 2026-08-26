"""Small compatibility bridge from the minimal deployment contract to legacy env names."""
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


def load() -> None:
    gmail = _object("GMAIL_OAUTH_JSON")
    for key, env_name in (("client_id", "GMAIL_CLIENT_ID"), ("client_secret", "GMAIL_CLIENT_SECRET"), ("refresh_token", "GMAIL_REFRESH_TOKEN")):
        if gmail.get(key) and not os.getenv(env_name):
            os.environ[env_name] = gmail[key]

    revenuecat = _object("REVENUECAT_CONFIG")
    for key, env_name in (("secret_api_key", "REVENUECAT_SECRET_API_KEY"), ("webhook_auth", "REVENUECAT_WEBHOOK_AUTH"), ("webhook_signing_secret", "REVENUECAT_WEBHOOK_SIGNING_SECRET")):
        if revenuecat.get(key) and not os.getenv(env_name):
            os.environ[env_name] = revenuecat[key]

    os.environ.setdefault("GMAIL_SENDER", "omerschaban@gmail.com")
    os.environ.setdefault("OPENAI_MODEL", "gpt-5.6")
    os.environ.setdefault("DB_POOL_MIN", "1")
    os.environ.setdefault("DB_POOL_MAX", "8")
    os.environ.setdefault("FLYWHEEL_ENABLE_PRODUCTION", "false")


load()
