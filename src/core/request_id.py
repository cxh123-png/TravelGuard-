from collections.abc import Awaitable, Callable  # 导入异步回调类型，用来给中间件的下一步处理函数做类型标注。
from contextvars import ContextVar  # 导入上下文变量，让同一次请求里的代码都能读取同一个 request_id。
from uuid import uuid4  # 导入 UUID 生成函数，在请求没有携带 ID 时自动生成唯一 ID。

from starlette.middleware.base import BaseHTTPMiddleware  # 导入 Starlette 中间件基类，FastAPI 底层基于 Starlette。
from starlette.requests import Request  # 导入请求对象类型，用来读取请求头等请求信息。
from starlette.responses import Response  # 导入响应对象类型，用来写入响应头。

REQUEST_ID_HEADER = "X-Request-ID"  # 定义请求 ID 使用的 HTTP 头名称，方便全项目统一引用。
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)  # 定义请求级上下文变量，默认没有 ID。


class RequestIdMiddleware(BaseHTTPMiddleware):  # 定义请求 ID 中间件，负责在请求进入和响应返回时处理追踪编号。
    async def dispatch(  # 实现 BaseHTTPMiddleware 要求的 dispatch 方法，每次请求都会执行这里。
        self,  # 当前中间件实例，Python 类方法的固定第一个参数。
        request: Request,  # 当前 HTTP 请求对象，包含请求头、路径、方法等信息。
        call_next: Callable[[Request], Awaitable[Response]],  # 后续处理函数，会把请求交给路由或下一个中间件。
    ) -> Response:  # 声明这个中间件最终会返回一个 HTTP 响应对象。
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())  # 优先复用客户端传入的 ID，否则生成新 UUID。
        token = request_id_var.set(request_id)  # 把 request_id 写入当前请求上下文，并保存 token 用于稍后恢复。

        try:  # 使用 try/finally，确保后续接口即使报错也能清理上下文变量。
            response = await call_next(request)  # 把请求继续传给后续处理流程，并等待接口返回响应。
        finally:  # 无论接口成功还是失败，都会执行这里的清理逻辑。
            request_id_var.reset(token)  # 恢复上下文变量，避免当前请求的 ID 泄漏到其他请求。

        response.headers[REQUEST_ID_HEADER] = request_id  # 把 request_id 写入响应头，方便调用方和日志排查问题。
        return response  # 返回带有 X-Request-ID 响应头的最终响应。


def get_request_id() -> str:  # 定义公共函数，让业务代码可以读取当前请求的 request_id。
    return request_id_var.get() or str(uuid4())  # 如果当前上下文没有 ID，则兜底生成一个新的 UUID。
