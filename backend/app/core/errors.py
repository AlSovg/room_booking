from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.rules import RuleViolation


class AppError(Exception):
    """Ошибка API в формате `{"error": {code, message, details}}` (docs/02-design.md, п. 3.3)."""

    def __init__(self, status: int, code: str, message: str, details: dict | None = None,
                 headers: dict | None = None):
        self.status, self.code, self.message, self.details, self.headers = status, code, message, details, headers


def _body(code: str, message: str, details: dict | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, e: AppError):
        return JSONResponse(_body(e.code, e.message, e.details), e.status, e.headers)

    @app.exception_handler(RuleViolation)
    async def _rule(_: Request, e: RuleViolation):
        return JSONResponse(_body(e.code, e.message, e.details), 422)

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, e: RequestValidationError):
        errors = [{"loc": err["loc"], "msg": err["msg"]} for err in e.errors()]
        return JSONResponse(_body("VALIDATION_ERROR", "Некорректные данные", {"errors": errors}), 422)
