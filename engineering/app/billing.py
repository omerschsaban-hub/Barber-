from __future__ import annotations

from fastapi import APIRouter, Cookie, Header, HTTPException, Request

from .owned_auth import COOKIE_NAME, _bearer, user_from_token
from .plan_catalog import access_for_user

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/access")
def access(
    request: Request,
    authorization: str | None = Header(default=None),
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
):
    identity = user_from_token(_bearer(request, authorization) or session)
    if not identity:
        raise HTTPException(401, "Unauthorized")
    resolved = access_for_user(identity["id"])
    return {"authenticated": True, "pro": resolved["plan"] != "free", **resolved}
