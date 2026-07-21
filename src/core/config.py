from functools import lru_cache  # 导入缓存装饰器，避免每次读取配置都重新解析环境变量。

from pydantic import Field  # 导入 Field，用来给配置字段设置默认值和说明。
from pydantic_settings import BaseSettings, SettingsConfigDict  # 导入 Pydantic Settings，用环境变量构造配置对象。


class Settings(BaseSettings):  # 定义全项目配置类，所有基础设施配置都从这里读取。
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")  # 指定本地 .env 文件和忽略多余变量。

    app_name: str = Field(default="TravelGuard AI")  # 应用名称，用于文档、日志和健康检查。
    app_env: str = Field(default="local")  # 当前运行环境，例如 local、test、staging 或 production。
    debug: bool = Field(default=False)  # 调试开关，生产环境必须保持关闭。
    api_prefix: str = Field(default="/api/v1")  # 业务 API 的统一版本前缀。

    database_url: str = Field(default="postgresql+asyncpg://travelguard:travelguard@127.0.0.1:5432/travelguard")  # 数据库连接地址。
    database_echo: bool = Field(default=False)  # 是否打印 SQL 语句，排查数据库问题时才打开。

    jwt_secret_key: str = Field(default="change-me-in-local-env-with-at-least-32-bytes")  # JWT 签名密钥，本地默认值不能用于正式环境。
    jwt_algorithm: str = Field(default="HS256")  # JWT 签名算法，M1 先提供基础骨架。
    access_token_expire_minutes: int = Field(default=60)  # 访问令牌有效时间，单位是分钟。

    redis_url: str = Field(default="redis://127.0.0.1:6379/0")  # Redis 地址，后续 Celery 和缓存会使用。
    milvus_host: str = Field(default="127.0.0.1")  # Milvus 主机地址，后续政策 RAG 会使用。
    milvus_port: int = Field(default=19530)  # Milvus 端口，默认是 19530。
    minio_endpoint: str = Field(default="127.0.0.1:9000")  # MinIO 地址，后续文件存储会使用。
    minio_access_key: str = Field(default="minioadmin")  # MinIO 访问账号，本地开发默认值。
    minio_secret_key: str = Field(default="minioadmin")  # MinIO 访问密钥，本地开发默认值。


@lru_cache  # 缓存配置对象，让应用生命周期内复用同一个 Settings 实例。
def get_settings() -> Settings:  # 定义配置读取函数，方便 FastAPI 依赖注入和普通代码复用。
    return Settings()  # 从环境变量和 .env 文件构造配置对象。
