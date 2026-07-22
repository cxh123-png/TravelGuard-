from typing import Annotated  # 导入 Annotated，用 FastAPI 推荐方式声明依赖注入。

from fastapi import Depends, FastAPI  # 导入 Depends 和 FastAPI，用于创建应用和声明接口依赖。

from src.api.dependencies import CurrentUser, get_current_user  # 导入当前用户上下文和认证依赖，提供 M1 权限骨架。
from src.api.error_handlers import register_error_handlers  # 导入统一异常处理注册函数，让错误响应格式一致。
from src.core.config import get_settings  # 导入配置读取函数，让应用名称、调试开关和 API 前缀来自配置。
from src.core.request_id import RequestIdMiddleware  # 导入请求 ID 中间件，给每次请求生成追踪编号。
from src.core.response import success_response  # 导入统一成功响应函数，保证所有接口返回格式一致。


def create_app() -> FastAPI:  # 定义应用工厂函数，让测试、开发和部署都用同一套应用创建逻辑。
    settings = get_settings()  # 读取应用配置，避免把应用名称和调试开关写死在代码中。
    application = FastAPI(title=settings.app_name, version="0.1.0", debug=settings.debug)  # 创建 FastAPI 应用实例。
    application.add_middleware(RequestIdMiddleware)  # 注册 request_id 中间件，让每个请求和响应都带追踪编号。
    register_error_handlers(application)  # 注册统一错误处理器，让业务错误和校验错误都返回统一结构。
    register_routes(application, settings.api_prefix)  # 注册当前 M1 提供的健康检查和示例公共 API。
    return application  # 返回完整配置好的 FastAPI 应用。


def register_routes(application: FastAPI, api_prefix: str) -> None:  # 定义路由注册函数，集中管理 M1 暴露的基础接口。
    @application.get("/health")  # 注册 GET /health 健康检查接口，供本地调试、测试和部署探活使用。
    async def health() -> dict[str, object]:  # 定义异步接口函数，并声明返回的是一个字典结构。
        return success_response({"status": "ok", "service": "travelguard-api"})  # 返回统一格式的健康检查结果。

    @application.get(f"{api_prefix}/me")  # 注册受保护示例接口，验证认证依赖和统一权限错误是否工作。
    async def read_current_user(  # 定义读取当前用户的示例接口。
        current_user: Annotated[CurrentUser, Depends(get_current_user)],  # 注入认证后的用户上下文。
    ) -> dict[str, object]:  # 声明接口返回统一响应字典。
        return success_response(  # 返回统一成功响应，让后续模块参考受保护接口的响应格式。
            {  # 构造脱敏用户上下文字典。
                "user_id": current_user.user_id,  # 返回当前用户 ID。
                "tenant_id": current_user.tenant_id,  # 返回当前租户 ID。
                "roles": list(current_user.roles),  # 返回当前角色列表。
            }  # 结束脱敏用户上下文字典。
        )  # 结束统一响应构造。


app = create_app()  # 创建 ASGI 应用对象，uvicorn 使用 src.main:app 启动服务。
