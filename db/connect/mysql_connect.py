# database.py
import threading

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator, Optional, Any, Dict

from conf.settings import DATABASES

# 创建基类
Base = declarative_base()


class DatabaseConfig:
    DATABASE_NAME = "knowledge"

    MYSQL_CONF = DATABASES[DATABASE_NAME]

    # 数据库连接配置
    MYSQL_HOST = MYSQL_CONF["host"]
    MYSQL_PORT = MYSQL_CONF["port"]
    MYSQL_USER = MYSQL_CONF["user"]
    MYSQL_PASSWORD = MYSQL_CONF["password"]
    MYSQL_DATABASE = MYSQL_CONF["database"]
    MYSQL_CHARSET = "utf8mb4"

    # 自动提交设置
    AUTO_COMMIT = True  # 设置为 False 则需手动提交

    # 连接池配置
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_RECYCLE = 3600

    # 连接池配置
    POOL_PRE_PING = True  # 连接前 ping 检查

    # SQLAlchemy 配置
    ECHO_SQL = False  # 是否打印 SQL 语句

    @classmethod
    def get_db_url(cls) -> str:
        """获取数据库连接 URL"""
        return (f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/"
                f"{cls.MYSQL_DATABASE}?charset={cls.MYSQL_CHARSET}")

    @classmethod
    def get_engine_config(cls) -> Dict[str, Any]:
        """获取引擎配置"""
        return {
            "pool_size": cls.POOL_SIZE,
            "max_overflow": cls.MAX_OVERFLOW,
            "pool_recycle": cls.POOL_RECYCLE,
            "pool_pre_ping": cls.POOL_PRE_PING,
            "echo": cls.ECHO_SQL,
        }


class DatabaseManager:
    """数据库管理器（单例模式）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化数据库连接"""
        # 创建引擎
        self.engine = create_engine(
            DatabaseConfig.get_db_url(),
            **DatabaseConfig.get_engine_config()
        )

        # 创建线程安全的 session factory
        session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        self.Session = scoped_session(session_factory)

        # 创建所有表（如果不存在）
        self.create_all_tables()

    def create_all_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)

    def drop_all_tables(self):
        """删除所有表（谨慎使用！）"""
        Base.metadata.drop_all(bind=self.engine)

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """获取数据库会话的上下文管理器"""
        session = self.Session()
        try:
            yield session
            if DatabaseConfig.AUTO_COMMIT:
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
            self.Session.remove()

    def get_session(self) -> Session:
        """获取数据库会话（需要手动关闭）"""
        return self.Session()

    def close_session(self, session: Optional[Session] = None):
        """关闭会话"""
        if session:
            session.close()
        self.Session.remove()

    def close_all(self):
        """关闭所有连接"""
        self.Session.remove()
        self.engine.dispose()


# 全局数据库实例
db_manager = DatabaseManager()
