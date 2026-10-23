from fastapi import APIRouter, HTTPException, Response

from models import LoginRequest
from services.session_service import SESSION_LIFETIME_SECONDS
from services.user_service import login_user
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

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

SESSION_COOKIE_NAME = "__Host-pp_session"


@router.post("/login")
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