import functools
from contextlib import contextmanager
from typing import Type, Callable, List, TypeVar, Any, Optional, Dict

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from db.connect.mysql_connect import db_manager, DatabaseConfig, DatabaseManager, Base

T = TypeVar('T', bound=Base)


def auto_session(func: Callable) -> Callable:
    """自动会话装饰器

    如果被装饰的函数没有传入 session 参数，则自动创建并管理 session
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # 检查是否已经传入了 session
        if 'session' in kwargs and kwargs['session'] is not None:
            # 使用传入的 session
            return func(self, *args, **kwargs)

        # 自动创建和管理 session
        with self.db.session_scope() as session:
            kwargs['session'] = session
            return func(self, *args, **kwargs)

    return wrapper


class DatabaseCRUD:
    """数据库增删改查操作类（自动会话管理）"""

    def __init__(self, manager: DatabaseManager = None):
        self.db = manager or DatabaseManager()

    # ========== 基础增删改操作 ==========

    @auto_session
    def add(self, instance: Base, session: Session = None, auto_commit: bool = None) -> Base:
        """添加单个记录"""
        try:
            session.add(instance)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
                session.refresh(instance)
            return instance
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @auto_session
    def add_all(self, instances: List[Base], session: Session = None, auto_commit: bool = None) -> List[Base]:
        """批量添加记录"""
        try:
            session.add_all(instances)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
                for instance in instances:
                    session.refresh(instance)
            return instances
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @auto_session
    def update(self, instance: Base, session: Session = None, auto_commit: bool = None) -> Base:
        """更新记录"""
        try:
            # 使用 merge 确保对象在 session 中
            merged_instance = session.merge(instance)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
                session.refresh(merged_instance)
            return merged_instance
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @auto_session
    def delete(self, instance: Base, session: Session = None, auto_commit: bool = None) -> bool:
        """删除记录"""
        try:
            # 确保对象在 session 中
            instance = session.merge(instance)
            session.delete(instance)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @auto_session
    def delete_by_id(self, model: Type[T], model_id: Any, session: Session = None, auto_commit: bool = None) -> bool:
        """根据ID删除记录"""
        instance = session.query(model).get(model_id)
        if instance:
            session.delete(instance)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
            return True
        return False

    # ========== 查询操作 ==========

    @auto_session
    def get_by_id(self, model: Type[T], model_id: Any, session: Session = None) -> Optional[T]:
        """根据ID获取记录"""
        return session.query(model).get(model_id)

    @auto_session
    def get_one(self, model: Type[T], session: Session = None, **filters) -> Optional[T]:
        """获取单个记录"""
        return session.query(model).filter_by(**filters).first()

    @auto_session
    def get_all(self, model: Type[T], session: Session = None, **filters) -> List[T]:
        """获取所有记录"""
        query = session.query(model)
        if filters:
            query = query.filter_by(**filters)
        return query.all()

    def query(self, model: Type[T]):
        """获取查询对象（返回 QueryBuilder 以便链式调用）"""
        return QueryBuilder(self.db, model)

    # ========== 分页查询 ==========

    @auto_session
    def paginate(self, model: Type[T], page: int = 1, page_size: int = 10,
                 session: Session = None, **filters) -> Dict[str, Any]:
        """分页查询"""
        query = session.query(model)
        if filters:
            query = query.filter_by(**filters)

        total = query.count()
        pages = (total + page_size - 1) // page_size

        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return {
            'items': items,
            'total': total,
            'page': page,
            'pages': pages,
            'size': page_size
        }

    # ========== 批量操作 ==========

    @auto_session
    def bulk_insert(self, model: Type[T], data_list: List[Dict[str, Any]],
                    session: Session = None) -> List[T]:
        """批量插入数据"""
        instances = [model(**data) for data in data_list]
        return self.add_all(instances, session=session)

    @auto_session
    def bulk_update(self, model: Type[T], update_data: Dict[str, Any],
                    session: Session = None, **filters) -> int:
        """批量更新"""
        try:
            result = session.query(model).filter_by(**filters).update(
                update_data,
                synchronize_session='fetch'
            )
            if DatabaseConfig.AUTO_COMMIT:
                session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    @auto_session
    def bulk_delete(self, model: Type[T], session: Session = None, **filters) -> int:
        """批量删除"""
        try:
            result = session.query(model).filter_by(**filters).delete(
                synchronize_session='fetch'
            )
            if DatabaseConfig.AUTO_COMMIT:
                session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    # ========== 计数和存在性检查 ==========

    @auto_session
    def count(self, model: Type[T], session: Session = None, **filters) -> int:
        """计数"""
        query = session.query(model)
        if filters:
            query = query.filter_by(**filters)
        return query.count()

    @auto_session
    def exists(self, model: Type[T], session: Session = None, **filters) -> bool:
        """检查记录是否存在"""
        return session.query(model).filter_by(**filters).first() is not None

    # ========== 执行原生SQL ==========

    @auto_session
    def execute_sql(self, sql: str, params: Dict = None, session: Session = None) -> Any:
        """执行原生SQL"""
        try:
            result = session.execute(sql, params or {})
            if DatabaseConfig.AUTO_COMMIT:
                session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            raise e

    # ========== 事务管理 ==========
    @contextmanager
    def transaction(self):
        """事务上下文管理器（自动管理session）"""
        with self.db.session_scope() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    # ========== 链式查询支持 ==========

    @auto_session
    def filter(self, model: Type[T], session: Session = None, **filters):
        """过滤查询（返回可继续链式调用的查询对象）"""
        return QueryBuilder(self.db, model, session=session).filter_by(**filters)


class QueryBuilder:
    """查询构建器，支持链式调用"""

    def __init__(self, manager: DatabaseManager, model: Type[T], session: Session = None):
        self.db = manager
        self.model = model
        self.session = session
        self._query = None

    def _get_session(self) -> Session:
        """获取session"""
        if self.session is None:
            self.session = self.db.get_session()
        return self.session

    def filter_by(self, **kwargs):
        """过滤条件"""
        self._query = self._get_session().query(self.model).filter_by(**kwargs)
        return self

    def filter(self, *args):
        """复杂过滤条件"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        self._query = self._query.filter(*args)
        return self

    def exists(self):
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.exists()
        finally:
            self._close_session_if_needed()

    def order_by(self, *args):
        """排序"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        self._query = self._query.order_by(*args)
        return self

    def limit(self, limit: int):
        """限制数量"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int):
        """偏移量"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        self._query = self._query.offset(offset)
        return self

    def all(self) -> List[T]:
        """执行查询获取所有结果"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.all()
        finally:
            self._close_session_if_needed()

    def first(self) -> Optional[T]:
        """执行查询获取第一个结果"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.first()
        finally:
            self._close_session_if_needed()

    def one(self) -> T:
        """执行查询获取单个结果（必须只有一条）"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.one()
        finally:
            self._close_session_if_needed()

    def one_or_none(self) -> Optional[T]:
        """执行查询获取单个结果或None"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.one_or_none()
        finally:
            self._close_session_if_needed()

    def count(self) -> int:
        """计数"""
        if self._query is None:
            self._query = self._get_session().query(self.model)
        try:
            return self._query.count()
        finally:
            self._close_session_if_needed()

    def _close_session_if_needed(self):
        """如果需要则关闭session"""
        if self.session is not None:
            self.db.close_session(self.session)
            self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_session_if_needed()


db_query = DatabaseCRUD(db_manager)
