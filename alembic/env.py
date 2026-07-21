from logging.config import fileConfig  # 导入日志配置函数，让 Alembic 使用 alembic.ini 的日志设置。

from alembic import context  # 导入 Alembic 运行上下文，用于离线/在线迁移。
from sqlalchemy import pool  # 导入连接池配置，迁移时使用 NullPool 避免长期持有连接。
from sqlalchemy.engine import Connection  # 导入同步连接类型，用于迁移回调类型标注。
from sqlalchemy.ext.asyncio import async_engine_from_config  # 导入异步引擎工厂，让 Alembic 支持 asyncpg。

from src.core.config import get_settings  # 导入配置读取函数，迁移时读取 DATABASE_URL。
from src.db.base import Base  # 导入 ORM 元数据基类，自动迁移会读取它的 metadata。


config = context.config  # 获取 Alembic 配置对象。
settings = get_settings()  # 读取应用配置，确保迁移和应用使用同一个数据库地址来源。
config.set_main_option("sqlalchemy.url", settings.database_url)  # 用环境变量中的数据库地址覆盖 alembic.ini 占位地址。

if config.config_file_name is not None:  # 如果 Alembic 找到了配置文件。
    fileConfig(config.config_file_name)  # 初始化 Alembic 日志配置。

target_metadata = Base.metadata  # 暴露 SQLAlchemy 元数据，供 alembic revision --autogenerate 使用。


def run_migrations_offline() -> None:  # 定义离线迁移模式，不直接连接数据库而是生成 SQL。
    url = config.get_main_option("sqlalchemy.url")  # 读取最终数据库 URL。
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})  # 配置离线迁移。

    with context.begin_transaction():  # 开启迁移事务块。
        context.run_migrations()  # 执行离线迁移生成逻辑。


def do_run_migrations(connection: Connection) -> None:  # 定义同步迁移回调，Alembic 在线迁移会调用它。
    context.configure(connection=connection, target_metadata=target_metadata)  # 把数据库连接和元数据交给 Alembic。

    with context.begin_transaction():  # 开启数据库迁移事务。
        context.run_migrations()  # 执行迁移脚本。


async def run_async_migrations() -> None:  # 定义异步在线迁移入口，适配 asyncpg 数据库驱动。
    connectable = async_engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)  # 创建异步迁移引擎。

    async with connectable.connect() as connection:  # 打开异步数据库连接。
        await connection.run_sync(do_run_migrations)  # 在异步连接中运行 Alembic 的同步迁移逻辑。

    await connectable.dispose()  # 释放迁移引擎资源。


def run_migrations_online() -> None:  # 定义在线迁移入口，Alembic CLI 会调用它连接数据库。
    import asyncio  # 在函数内部导入 asyncio，避免离线模式不必要加载。

    asyncio.run(run_async_migrations())  # 运行异步迁移协程。


if context.is_offline_mode():  # 判断当前是否是离线迁移模式。
    run_migrations_offline()  # 离线模式执行 SQL 生成逻辑。
else:  # 否则进入真实数据库在线迁移模式。
    run_migrations_online()  # 在线模式连接数据库并执行迁移。
