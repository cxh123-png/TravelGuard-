from enum import StrEnum  # 导入字符串枚举，让错误码既有枚举约束又能直接序列化为字符串。
from typing import Any  # 导入 Any 类型，用于描述错误详情可以是任意 JSON 结构。


class ErrorCode(StrEnum):  # 定义统一错误码集合，后续模块不要随意手写错误字符串。
    UNAUTHORIZED = "UNAUTHORIZED"  # 表示请求未认证或认证失败。
    FORBIDDEN = "FORBIDDEN"  # 表示用户已认证但没有权限。
    NOT_FOUND = "NOT_FOUND"  # 表示请求的资源不存在。
    VALIDATION_ERROR = "VALIDATION_ERROR"  # 表示输入参数校验失败。
    INTERNAL_ERROR = "INTERNAL_ERROR"  # 表示服务端未预期异常。


class AppError(Exception):  # 定义业务异常基类，应用内可预期错误都应该抛出它。
    def __init__(  # 定义异常初始化方法，统一保存错误码、消息、状态码和详情。
        self,  # 当前异常实例。
        code: ErrorCode,  # 业务错误码，用于前端和调用方稳定判断错误类型。
        message: str,  # 人类可读错误信息，用于页面提示或日志说明。
        status_code: int = 400,  # HTTP 状态码，默认使用 400 表示请求错误。
        details: dict[str, Any] | None = None,  # 可选错误详情，用于补充字段级错误或调试信息。
    ) -> None:  # 声明初始化方法不返回业务值。
        super().__init__(message)  # 调用 Exception 基类初始化，保证异常字符串是 message。
        self.code = code  # 保存业务错误码。
        self.message = message  # 保存错误消息。
        self.status_code = status_code  # 保存 HTTP 状态码。
        self.details = details or {}  # 保存错误详情，没有传入时使用空字典。
