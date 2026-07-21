from sqlalchemy.orm import DeclarativeBase  # 导入 SQLAlchemy 声明式基类，用于后续所有 ORM 模型继承。


class Base(DeclarativeBase):  # 定义项目统一 ORM 基类，M2-M7 的数据库模型都应该继承它。
    pass  # 当前 M1 只提供基类，不定义具体业务表。
