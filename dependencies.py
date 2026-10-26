from fastapi import HTTPException, Request
from services.session_service import get_session_user_id
from models import LoginRequest

from services.login_rate_limit_service import (
    WINDOW_SECONDS,
    allow_login_attempt,
)

import os

SESSION_COOKIE_NAME = "__Host-pp_session"
#登录时验证密码；之后查看会议等操作，浏览器携带 Cookie，服务器通过凭证查出用户 ID。

def require_user_id(request: Request) -> int: #request: Request 浏览器发来的请求
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token is not None:
        user_id = get_session_user_id(token) #重复使用已有的SQL
        if user_id is not None:
            return user_id #告知用户ID

    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"Cache-Control": "no-store"},
    )

def require_trusted_origin(request: Request) -> None:
    expected_origin = os.getenv("PP_APP_ORIGIN") #认可的网页地址，不是 Azure 地址。配置由服务器控制，不从客户端获取。

    if not expected_origin:
        raise HTTPException(
            status_code=503, #服务器没配置好
            detail="Application origin is not configured",
            headers={"Cache-Control": "no-store"},
        )

    actual_origin = request.headers.get("origin")

    if actual_origin != expected_origin:
        raise HTTPException(
            status_code=403, #来源不符合要求
            detail="Untrusted request origin",
            headers={"Cache-Control": "no-store"},
        )

def require_login_budget(request: Request, data: LoginRequest) -> None:
    if request.client is None:
        raise HTTPException(
            status_code=503,
            detail="Client address unavailable",
            headers={"Cache-Control": "no-store"},
        )

    keys = (
        f"ip:{request.client.host}",
        f"account:{data.username}",
    )

    for key in keys:
        if not allow_login_attempt(key):
            raise HTTPException(
                status_code=429,
                detail="Too many login attempts",
                headers={
                    "Retry-After": str(WINDOW_SECONDS),
                    "Cache-Control": "no-store",
                },
            )
