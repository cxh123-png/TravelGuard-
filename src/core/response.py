from typing import Any  # 导入 Any 类型，表示响应 data 可以承载任意结构的数据。

from src.core.request_id import get_request_id  # 导入 request_id 读取函数，把追踪编号放进统一响应体。


def success_response(data: Any, message: str = "success") -> dict[str, Any]:  # 定义统一成功响应函数，供所有接口复用。
    return {  # 返回一个标准字典，FastAPI 会自动序列化成 JSON。
        "code": "OK",  # 业务状态码，OK 表示请求在业务层处理成功。
        "data": data,  # 业务数据区域，接口真正想返回的内容放在这里。
        "message": message,  # 人类可读的提示信息，默认是 success。
        "request_id": get_request_id(),  # 当前请求的追踪编号，用于排查日志和问题。
    }  # 结束统一响应字典。
