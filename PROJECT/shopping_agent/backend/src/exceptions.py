from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.auth.exceptions import AuthError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AuthError)
    def handle_auth_error(request: Request, exc: AuthError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error_code": exc.error_code, "message": exc.message},
        )
