from collections.abc import AsyncGenerator  # 导入异步生成器类型，用于标注 FastAPI 数据库会话依赖。

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # 导入 SQLAlchemy 异步引擎和会话工具。

from src.core.config import get_settings  # 导入配置读取函数，获取数据库连接地址和调试开关。

settings = get_settings()  # 读取应用配置，数据库引擎会使用其中的 DATABASE_URL。
engine = create_async_engine(settings.database_url, echo=settings.database_echo, pool_pre_ping=True)  # 创建异步数据库引擎。
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)  # 创建异步会话工厂。


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:  # 定义 FastAPI 数据库依赖，每个请求获取一个异步会话。
    async with AsyncSessionLocal() as session:  # 从会话工厂创建会话，并在请求结束后自动关闭。
        yield session  # 把会话交给接口或应用服务使用。
