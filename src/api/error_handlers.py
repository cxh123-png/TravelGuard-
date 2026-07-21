from fastapi import FastAPI, Request  # 导入 FastAPI 应用和请求对象，用于注册异常处理器。
from fastapi.exceptions import RequestValidationError  # 导入 FastAPI 参数校验异常类型。
from fastapi.responses import JSONResponse  # 导入 JSONResponse，用来返回统一 JSON 错误响应。

from src.core.errors import AppError, ErrorCode  # 导入应用统一异常和错误码。
from src.core.request_id import get_request_id  # 导入 request_id 读取函数，把追踪编号放进错误响应。


def error_response(code: str, message: str, status_code: int, details: dict[str, object] | None = None) -> JSONResponse:  # 构造错误响应。
    return JSONResponse(  # 返回 FastAPI/Starlette 标准 JSON 响应对象。
        status_code=status_code,  # 设置 HTTP 状态码。
        content={  # 设置统一错误响应体。
            "code": code,  # 业务错误码。
            "data": {"details": details or {}},  # 错误详情放在 data.details，保持响应外壳稳定。
            "message": message,  # 人类可读错误信息。
            "request_id": get_request_id(),  # 当前请求追踪编号。
        },  # 结束响应体。
    )  # 结束 JSONResponse 构造。


def register_error_handlers(app: FastAPI) -> None:  # 定义异常处理器注册函数，应用启动时调用一次。
    @app.exception_handler(AppError)  # 注册应用内可预期业务异常处理器。
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:  # 处理 AppError 并返回统一错误响应。
        return error_response(exc.code, exc.message, exc.status_code, exc.details)  # 把异常字段转换为统一响应。

    @app.exception_handler(RequestValidationError)  # 注册请求参数校验异常处理器。
    async def handle_validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:  # 处理参数校验失败。
        return error_response(ErrorCode.VALIDATION_ERROR, "Request validation failed.", 422, {"errors": exc.errors()})  # 返回统一校验错误。

    @app.exception_handler(Exception)  # 注册兜底异常处理器，避免未处理异常泄漏内部细节。
    async def handle_unexpected_error(_request: Request, _exc: Exception) -> JSONResponse:  # 处理未预期异常。
        return error_response(ErrorCode.INTERNAL_ERROR, "Internal server error.", 500)  # 返回统一 500 错误。
