from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from models import LoginRequest
from services.user_service import login_user
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from dependencies import (
    SESSION_COOKIE_NAME,
    require_trusted_origin,
    require_user_id,
)
from services.session_service import (
    SESSION_LIFETIME_SECONDS,
    revoke_session,
)


class AuthRoute(APIRoute):
    def get_route_handler(self):
        original_handler = super().get_route_handler()

        async def safe_handler(request):
            try:
                return await original_handler(request)
            except RequestValidationError:
                return JSONResponse(
                    status_code=422,
                    content={"detail": "Invalid login request"},
                    headers={"Cache-Control": "no-store"},
                )

        return safe_handler

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    route_class=AuthRoute,
)

@router.post(
    "/login",
    dependencies=[Depends(require_trusted_origin)],
)
def login(data: LoginRequest, response: Response):
    result = login_user(
        data.username,
        data.password.get_secret_value(),
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"Cache-Control": "no-store"},
        )

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=result["token"],
        max_age=SESSION_LIFETIME_SECONDS,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"

    return {
        "id": result["user"]["id"],
        "username": result["user"]["username"],
    }

@router.post(
    "/logout",
    status_code=204,
    dependencies=[Depends(require_trusted_origin)],
)
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token is not None:
        revoke_session(token)

    response = Response(status_code=204)
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return response

@router.get("/me")
def get_current_user(
    response: Response,
    user_id: int = Depends(require_user_id),
):
    response.headers["Cache-Control"] = "no-store"
    return {"id": user_id}
