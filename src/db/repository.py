from typing import Generic, TypeVar  # 导入泛型工具，为仓储基类表达实体类型。

from sqlalchemy.ext.asyncio import AsyncSession  # 导入异步会话类型，仓储通过它访问数据库。

ModelT = TypeVar("ModelT")  # 定义模型泛型变量，表示仓储管理的 ORM 模型类型。


class Repository(Generic[ModelT]):  # 定义最小仓储基类，后续模块可以继承它实现领域仓储。
    def __init__(self, session: AsyncSession) -> None:  # 初始化仓储时注入数据库会话。
        self.session = session  # 保存会话，供具体仓储方法执行查询或写入。

    async def add(self, model: ModelT) -> ModelT:  # 提供通用新增方法，把模型加入当前事务。
        self.session.add(model)  # 将模型对象加入 SQLAlchemy 会话。
        return model  # 返回原模型，方便调用方继续使用。
