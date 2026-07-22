from datetime import UTC, datetime, timedelta  # 导入时间工具，用来生成 JWT 过期时间。
from typing import Any  # 导入 Any 类型，用于表达 JWT payload 的通用 JSON 字段。

import jwt  # 导入 PyJWT，用于编码和解码 JWT。

from src.core.config import get_settings  # 导入配置读取函数，获取 JWT 密钥和算法。
from src.core.errors import AppError, ErrorCode  # 导入统一异常和错误码，认证失败时使用。


def create_access_token(subject: str, tenant_id: str, roles: list[str]) -> str:  # 定义访问令牌生成函数，供后续登录模块复用。
    settings = get_settings()  # 读取当前配置，拿到 JWT 密钥、算法和有效期。
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)  # 计算令牌过期时间。
    payload: dict[str, Any] = {"sub": subject, "tenant_id": tenant_id, "roles": roles, "exp": expires_at}  # 构造 JWT 载荷。
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)  # 使用配置中的密钥和算法签发令牌。


def decode_access_token(token: str) -> dict[str, Any]:  # 定义令牌解析函数，供认证依赖读取当前用户上下文。
    settings = get_settings()  # 读取当前配置，拿到 JWT 解码需要的密钥和算法。
    try:  # 捕获 PyJWT 抛出的各种解析失败异常。
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])  # 校验签名并解析 payload。
    except jwt.PyJWTError as exc:  # 捕获过期、签名错误、格式错误等 JWT 异常。
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token.", status_code=401) from exc  # 转换成统一认证错误。
    return dict(payload)  # 转成普通字典返回，避免调用方依赖第三方库内部类型。
