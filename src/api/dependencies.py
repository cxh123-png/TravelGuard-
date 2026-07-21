from collections.abc import Callable  # 导入 Callable 类型，用来标注角色依赖工厂的返回值。
from dataclasses import dataclass  # 导入 dataclass，用简洁方式定义当前用户上下文。
from typing import Annotated  # 导入 Annotated，用 FastAPI 推荐方式声明依赖注入。

from fastapi import Depends  # 导入 Depends，用于声明 FastAPI 依赖注入。
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # 导入 Bearer 认证工具，解析 Authorization 请求头。

from src.core.errors import AppError, ErrorCode  # 导入统一异常和错误码，权限失败时使用。
from src.core.security import decode_access_token  # 导入 JWT 解析函数，得到用户、租户和角色信息。

bearer_scheme = HTTPBearer(auto_error=False)  # 创建 Bearer 认证方案，auto_error=False 让我们自己返回统一错误格式。


@dataclass(frozen=True)  # 使用不可变 dataclass，避免请求处理中意外修改用户上下文。
class CurrentUser:  # 定义当前用户上下文，后续 M2-M7 的接口都可以依赖它。
    user_id: str  # 当前认证用户 ID。
    tenant_id: str  # 当前用户所属租户 ID，用于企业数据隔离。
    roles: tuple[str, ...]  # 当前用户角色集合，用于最小权限判断。


async def get_current_user(  # 定义认证依赖函数，负责把 Bearer token 转换成 CurrentUser。
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],  # 从 Authorization 请求头读取 Bearer token。
) -> CurrentUser:  # 声明认证成功后返回当前用户上下文。
    if credentials is None:  # 如果请求没有 Authorization: Bearer token。
        raise AppError(ErrorCode.UNAUTHORIZED, "Authentication required.", status_code=401)  # 返回统一未认证错误。

    payload = decode_access_token(credentials.credentials)  # 解析 Bearer token，得到 JWT payload。
    user_id = str(payload.get("sub") or "")  # 从 sub 字段读取用户 ID，没有则转为空字符串。
    tenant_id = str(payload.get("tenant_id") or "")  # 从 tenant_id 字段读取租户 ID，没有则转为空字符串。
    roles_value = payload.get("roles") or []  # 从 roles 字段读取角色列表，没有则使用空列表。

    if not user_id or not tenant_id:  # 如果令牌缺少必要身份信息。
        raise AppError(ErrorCode.UNAUTHORIZED, "Token is missing required identity fields.", status_code=401)  # 返回统一认证错误。

    roles = tuple(str(role) for role in roles_value)  # 把角色统一转换为字符串元组，方便后续权限判断。
    return CurrentUser(user_id=user_id, tenant_id=tenant_id, roles=roles)  # 返回不可变的当前用户上下文。


def require_roles(*allowed_roles: str) -> Callable[[CurrentUser], object]:  # 定义角色检查工厂，调用时传入允许访问的角色名。
    async def dependency(  # 定义真正给 FastAPI 使用的依赖函数。
        current_user: Annotated[CurrentUser, Depends(get_current_user)],  # 先复用认证依赖拿到当前用户。
    ) -> CurrentUser:  # 权限通过后继续返回当前用户上下文。
        if not set(current_user.roles).intersection(allowed_roles):  # 如果当前用户角色和允许角色没有交集。
            raise AppError(ErrorCode.FORBIDDEN, "Permission denied.", status_code=403)  # 返回统一无权限错误。
        return current_user  # 权限通过时，把当前用户上下文继续交给接口使用。

    return dependency  # 返回依赖函数，让接口可以写 Depends(require_roles("admin"))。
