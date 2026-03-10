我来修改代码，让 CRUD 操作自动管理 session，不需要显式传递。这样使用起来会更简洁。

## 1. **自动会话管理版本**

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator, Optional, Any, Type, TypeVar, List, Dict, Callable, Union
import threading
import functools
from config import DatabaseConfig

# 创建基类
Base = declarative_base()

# 类型变量
T = TypeVar('T', bound=Base)

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
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db = db_manager or DatabaseManager()
    
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
    def delete_by_id(self, model: Type[T], id: Any, session: Session = None, auto_commit: bool = None) -> bool:
        """根据ID删除记录"""
        instance = session.query(model).get(id)
        if instance:
            session.delete(instance)
            if auto_commit or (auto_commit is None and DatabaseConfig.AUTO_COMMIT):
                session.commit()
            return True
        return False
    
    # ========== 查询操作 ==========
    
    @auto_session
    def get_by_id(self, model: Type[T], id: Any, session: Session = None) -> Optional[T]:
        """根据ID获取记录"""
        return session.query(model).get(id)
    
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
    
    def __init__(self, db_manager: DatabaseManager, model: Type[T], session: Session = None):
        self.db = db_manager
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


# 全局数据库实例
db_manager = DatabaseManager()
db_crud = DatabaseCRUD(db_manager)
```

## 2. **使用示例**

```python
# models.py（保持不变）
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100))
    age = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, default=0)


# main.py - 使用示例
from database import db_crud
from models import User, Product

def demo_simple_crud():
    """演示简单的CRUD操作"""
    
    # 1. 添加用户（自动管理session）
    user1 = User(
        username="john_doe",
        email="john@example.com",
        full_name="John Doe",
        age=30
    )
    user1 = db_crud.add(user1)  # 自动创建和管理session
    print(f"添加用户成功，ID: {user1.id}")
    
    # 2. 批量添加（自动管理session）
    users_data = [
        {"username": "alice", "email": "alice@example.com", "age": 25},
        {"username": "bob", "email": "bob@example.com", "age": 28},
        {"username": "charlie", "email": "charlie@example.com", "age": 32}
    ]
    users = db_crud.bulk_insert(User, users_data)
    print(f"批量添加 {len(users)} 个用户")
    
    # 3. 查询操作
    # 根据ID查询
    user_by_id = db_crud.get_by_id(User, user1.id)
    print(f"根据ID查询: {user_by_id.username}")
    
    # 根据条件查询单个
    user_by_name = db_crud.get_one(User, username="alice")
    print(f"根据用户名查询: {user_by_name.email}")
    
    # 查询所有
    all_users = db_crud.get_all(User)
    print(f"所有用户数量: {len(all_users)}")
    
    # 带条件查询所有
    adult_users = db_crud.get_all(User, age=30)
    print(f"30岁用户数量: {len(adult_users)}")
    
    # 4. 更新操作
    if user_by_id:
        user_by_id.age = 31
        user_by_id.full_name = "John Smith"
        updated_user = db_crud.update(user_by_id)
        print(f"更新用户: {updated_user.age}岁")
    
    # 5. 删除操作
    # 根据ID删除
    deleted = db_crud.delete_by_id(User, user1.id)
    print(f"删除用户: {'成功' if deleted else '失败'}")
    
    # 删除对象
    if user_by_name:
        db_crud.delete(user_by_name)
        print("删除用户成功")
    
    # 6. 分页查询
    page_result = db_crud.paginate(User, page=1, page_size=2)
    print(f"分页查询: 第{page_result['page']}页/共{page_result['pages']}页")
    
    # 7. 计数和存在性检查
    user_count = db_crud.count(User)
    print(f"用户总数: {user_count}")
    
    exists = db_crud.exists(User, username="bob")
    print(f"用户bob是否存在: {exists}")
    
    # 8. 批量操作
    # 批量更新
    updated_count = db_crud.bulk_update(
        User, 
        {"age": 35},  # 更新数据
        username="bob"  # 条件
    )
    print(f"批量更新了 {updated_count} 条记录")
    
    # 批量删除
    deleted_count = db_crud.bulk_delete(User, age=25)
    print(f"批量删除了 {deleted_count} 条记录")

def demo_chained_query():
    """演示链式查询"""
    
    # 方法1：使用 query() 方法
    users = db_crud.query(User).filter_by(age=30).order_by(User.created_at.desc()).all()
    print(f"链式查询结果1: {len(users)} 条")
    
    # 方法2：使用 QueryBuilder 的 with 语句
    with db_crud.query(User) as q:
        results = q.filter(User.age > 25).order_by(User.username).limit(5).all()
        print(f"链式查询结果2: {len(results)} 条")
    
    # 方法3：手动构建查询链
    query = db_crud.query(User)
    query = query.filter(User.email.like("%@example.com"))
    query = query.filter(User.age >= 30)
    results = query.order_by(User.created_at).all()
    print(f"链式查询结果3: {len(results)} 条")

def demo_transaction():
    """演示事务操作"""
    
    # 方式1：使用事务上下文管理器
    with db_crud.transaction() as session:
        # 在事务中操作
        user1 = User(username="user1", email="user1@example.com", age=20)
        db_crud.add(user1, session=session)  # 使用传入的session
        
        user2 = User(username="user2", email="user2@example.com", age=25)
        db_crud.add(user2, session=session)
        
        # 如果这里抛出异常，所有操作都会回滚
        # raise Exception("模拟错误")
    
    print("事务操作完成")
    
    # 方式2：使用手动控制的事务（如果需要跨多个函数）
    session = db_crud.db.get_session()
    try:
        user3 = User(username="user3", email="user3@example.com", age=30)
        db_crud.add(user3, session=session)  # 显式传入session
        
        # 执行其他操作...
        session.commit()
        print("手动事务提交成功")
    except Exception as e:
        session.rollback()
        print(f"手动事务回滚: {e}")
    finally:
        db_crud.db.close_session(session)

def demo_execute_sql():
    """演示执行原生SQL"""
    
    # 执行查询SQL
    result = db_crud.execute_sql(
        "SELECT username, age FROM users WHERE age > :age ORDER BY created_at DESC",
        {"age": 25}
    )
    
    for row in result:
        print(f"SQL查询结果: {row.username}, {row.age}岁")
    
    # 执行更新SQL
    result = db_crud.execute_sql(
        "UPDATE users SET age = age + 1 WHERE username = :username",
        {"username": "bob"}
    )
    print(f"更新了 {result.rowcount} 条记录")

def demo_multi_models():
    """演示多模型操作"""
    
    # 添加产品
    product1 = Product(name="iPhone", price=9999, stock=100)
    product2 = Product(name="MacBook", price=19999, stock=50)
    
    db_crud.add(product1)
    db_crud.add(product2)
    
    # 查询产品
    products = db_crud.get_all(Product)
    print(f"产品数量: {len(products)}")
    
    # 复杂查询：联合查询示例
    # 注意：这里演示跨模型操作时使用手动session管理
    with db_crud.db.session_scope() as session:
        # 可以使用原生SQL进行联合查询
        result = session.execute("""
            SELECT u.username, p.name as product_name, p.price
            FROM users u, products p
            WHERE u.age > 25
            ORDER BY u.created_at DESC
        """)
        
        for row in result:
            print(f"联合查询: {row.username} - {row.product_name}")

def demo_fastapi_usage():
    """演示在 FastAPI 中的使用"""
    
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from typing import Optional
    
    app = FastAPI()
    
    class UserCreate(BaseModel):
        username: str
        email: str
        full_name: Optional[str] = None
        age: Optional[int] = None
    
    class UserResponse(BaseModel):
        id: int
        username: str
        email: str
        full_name: Optional[str]
        age: Optional[int]
        
        class Config:
            orm_mode = True
    
    @app.post("/users/", response_model=UserResponse)
    def create_user(user_data: UserCreate):
        """创建用户 - 不需要显式传递session"""
        # 检查用户名是否已存在
        existing = db_crud.get_one(User, username=user_data.username)
        if existing:
            raise HTTPException(status_code=400, detail="用户名已存在")
        
        # 创建用户
        user = User(**user_data.dict())
        return db_crud.add(user)
    
    @app.get("/users/", response_model=list[UserResponse])
    def list_users(skip: int = 0, limit: int = 100):
        """获取用户列表"""
        return db_crud.query(User).offset(skip).limit(limit).all()
    
    @app.get("/users/{user_id}", response_model=UserResponse)
    def get_user(user_id: int):
        """获取单个用户"""
        user = db_crud.get_by_id(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user
    
    @app.put("/users/{user_id}", response_model=UserResponse)
    def update_user(user_id: int, user_data: UserCreate):
        """更新用户"""
        user = db_crud.get_by_id(User, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 更新字段
        for key, value in user_data.dict(exclude_unset=True).items():
            setattr(user, key, value)
        
        return db_crud.update(user)
    
    @app.delete("/users/{user_id}")
    def delete_user(user_id: int):
        """删除用户"""
        success = db_crud.delete_by_id(User, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"message": "用户删除成功"}

if __name__ == "__main__":
    print("开始演示自动session管理的CRUD操作...")
    
    # 创建表
    db_crud.db.create_all_tables()
    
    # 演示各种操作
    demo_simple_crud()
    print("\n" + "="*50 + "\n")
    
    demo_chained_query()
    print("\n" + "="*50 + "\n")
    
    demo_transaction()
    print("\n" + "="*50 + "\n")
    
    demo_execute_sql()
    print("\n" + "="*50 + "\n")
    
    demo_multi_models()
    
    print("\n演示完成！")
```

## 3. **主要改进特点**

### **自动会话管理**
- 使用 `@auto_session` 装饰器自动管理 session
- 无需显式传递 session 参数
- 自动提交事务（可配置）

### **使用方式更简洁**
```python
# 以前需要这样：
with db.get_session() as session:
    user = db.add(session, user_obj)

# 现在只需要：
user = db_crud.add(user_obj)  # 自动管理session
```

### **灵活的查询方式**
```python
# 方式1：简单查询
users = db_crud.get_all(User, age=30)

# 方式2：链式查询
users = db_crud.query(User).filter_by(age=30).order_by(User.created_at).all()

# 方式3：使用 QueryBuilder 上下文
with db_crud.query(User) as q:
    users = q.filter(User.age > 25).limit(10).all()
```

### **事务管理**
```python
# 自动事务
with db_crud.transaction() as session:
    db_crud.add(user1, session=session)
    db_crud.add(user2, session=session)
```

### **仍然支持手动传递 session**
```python
# 如果需要手动控制 session，仍然可以传递
with db_crud.db.session_scope() as session:
    user = db_crud.add(user_obj, session=session)
    # 继续使用同一个 session 进行其他操作
```

## 4. **配置说明**

在 `config.py` 中：

```python
class DatabaseConfig:
    # 数据库连接配置
    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = "your_password"
    MYSQL_DATABASE = "your_database"
    
    # 自动提交设置
    AUTO_COMMIT = True  # 设置为 False 则需手动提交
    
    # 连接池配置
    POOL_SIZE = 5
    MAX_OVERFLOW = 10
    POOL_RECYCLE = 3600
```

这个版本让数据库操作更加简洁，同时保持了灵活性。你可以根据实际需求选择自动或手动管理 session。