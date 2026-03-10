"""
MySQL 8.0 检查点保存器
支持标准的检查点接口，兼容 LangGraph
"""

import json
import logging
from typing import Any, Optional, Sequence, Dict, List
from contextlib import contextmanager

import pymysql
from pymysql import MySQLError
from pymysql.cursors import DictCursor
from pymysql.connections import Connection

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint
from langgraph.checkpoint.base import CheckpointMetadata

# 设置日志
logger = logging.getLogger(__name__)


class MySQLCheckpointSaver(BaseCheckpointSaver):
    """
    MySQL 检查点保存器

    特性：
    1. 支持 MySQL 8.0+ 和 MariaDB 10.5+
    2. 连接池管理
    3. 自动重连
    4. JSON 类型支持
    5. 索引优化
    """

    def __init__(self, host: str = "localhost", port: int = 3306, user: str = "root", password: str = "",
                 database: str = "langgraph_checkpoints", charset: str = "utf8mb4", pool_size: int = 5,
                 autocommit: bool = True, use_ssl: bool = False, ssl_ca: Optional[str] = None,
                 ssl_cert: Optional[str] = None, ssl_key: Optional[str] = None, connect_timeout: int = 10,
                 read_timeout: int = 30, write_timeout: int = 30):
        """
        初始化 MySQL 检查点保存器

        Args:
            host: MySQL 主机
            port: 端口
            user: 用户名
            password: 密码
            database: 数据库名
            charset: 字符集
            pool_size: 连接池大小
            autocommit: 是否自动提交
            use_ssl: 是否使用 SSL
            ssl_ca: SSL CA 证书路径
            ssl_cert: SSL 证书路径
            ssl_key: SSL 密钥路径
            connect_timeout: 连接超时(秒)
            read_timeout: 读取超时(秒)
            write_timeout: 写入超时(秒)
        """
        super().__init__()
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.pool_size = pool_size
        self.autocommit = autocommit
        self.use_ssl = use_ssl
        self.ssl_ca = ssl_ca
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout

        # 连接池
        self._connection_pool: List[Connection] = []
        self._pool_lock = False

        # 初始化数据库
        self._init_database()
        self._init_table()

        logger.info(f"MySQLCheckpointSaver 初始化完成，数据库: {database}")

    @contextmanager
    def _get_connection(self) -> Connection:
        """
        从连接池获取连接（上下文管理器）

        Yields:
            Connection: MySQL 连接
        """
        conn = None
        try:
            conn = self._create_connection()
            yield conn
        finally:
            if conn:
                self._release_connection(conn)

    def _create_connection(self) -> Connection:
        """
        创建新连接
        """
        ssl_config = None
        if self.use_ssl:
            ssl_config = {
                'ca': self.ssl_ca,
                'cert': self.ssl_cert,
                'key': self.ssl_key
            }

        try:
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                cursorclass=DictCursor,
                autocommit=self.autocommit,
                ssl=ssl_config,
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                write_timeout=self.write_timeout
            )
            return conn
        except MySQLError as e:
            logger.error(f"创建 MySQL 连接失败: {e}")
            raise

    def _release_connection(self, conn: Connection):
        """
        释放连接回连接池或关闭
        """
        try:
            if len(self._connection_pool) < self.pool_size and not conn._closed:
                self._connection_pool.append(conn)
            else:
                conn.close()
        except Exception as e:
            logger.warning(f"释放连接时出错: {e}")
            try:
                conn.close()
            except:
                pass

    def _init_database(self):
        """
        初始化数据库（如果不存在则创建）
        """
        try:
            # 先连接到 MySQL（不指定数据库）
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset=self.charset
            )

            with conn.cursor() as cursor:
                # 创建数据库（如果不存在）
                cursor.execute(f"""
                    CREATE DATABASE IF NOT EXISTS `{self.database}`
                    CHARACTER SET {self.charset}
                    COLLATE {self.charset}_unicode_ci
                """)

                # 切换到该数据库
                cursor.execute(f"USE `{self.database}`")

                # 检查 MySQL 版本
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                logger.info(f"MySQL 版本: {version}")

            conn.commit()
            conn.close()

        except MySQLError as e:
            logger.error(f"初始化数据库失败: {e}")
            raise

    def _init_table(self):
        """
        初始化检查点表
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                # 创建检查点表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `checkpoints` (
                        `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        `thread_id` VARCHAR(255) NOT NULL COMMENT '线程ID',
                        `checkpoint_id` VARCHAR(255) NOT NULL COMMENT '检查点ID',
                        `checkpoint_data` JSON NOT NULL COMMENT '检查点数据',
                        `metadata` JSON DEFAULT (JSON_OBJECT()) COMMENT '元数据',
                        `parent_checkpoint` VARCHAR(255) DEFAULT NULL COMMENT '父检查点ID',
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',

                        -- 唯一约束
                        UNIQUE KEY `uk_thread_checkpoint` (`thread_id`, `checkpoint_id`),

                        -- 索引
                        KEY `idx_thread_id` (`thread_id`),
                        KEY `idx_created_at` (`created_at`),
                        KEY `idx_parent` (`parent_checkpoint`)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                    COMMENT='LangGraph 检查点表'
                """)

                # 创建检查点历史表（可选，用于审计）
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `checkpoint_history` (
                        `id` BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
                        `thread_id` VARCHAR(255) NOT NULL,
                        `checkpoint_id` VARCHAR(255) NOT NULL,
                        `operation` ENUM('CREATE', 'UPDATE', 'DELETE') NOT NULL,
                        `old_data` JSON DEFAULT NULL,
                        `new_data` JSON DEFAULT NULL,
                        `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

                # 创建配置表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS `checkpoint_config` (
                        `config_key` VARCHAR(100) PRIMARY KEY,
                        `config_value` JSON NOT NULL,
                        `description` VARCHAR(255) DEFAULT NULL,
                        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)

                # 插入默认配置
                cursor.execute("""
                    INSERT IGNORE INTO `checkpoint_config` 
                    (`config_key`, `config_value`, `description`)
                    VALUES 
                    ('version', '"1.0.0"', '检查点版本'),
                    ('retention_days', '30', '数据保留天数'),
                    ('max_checkpoints_per_thread', '1000', '每个线程最大检查点数')
                """)

                # 创建清理过期数据的存储过程
                cursor.execute("""
                    CREATE PROCEDURE IF NOT EXISTS `cleanup_expired_checkpoints`(
                        IN retention_days INT
                    )
                    BEGIN
                        DECLARE deleted_count INT DEFAULT 0;
                        DECLARE start_time TIMESTAMP;

                        SET start_time = NOW();

                        -- 删除过期的检查点
                        DELETE FROM `checkpoints` 
                        WHERE `created_at` < DATE_SUB(NOW(), INTERVAL retention_days DAY);

                        SET deleted_count = ROW_COUNT();

                        -- 记录清理日志
                        INSERT INTO `checkpoint_config` 
                        (`config_key`, `config_value`, `description`)
                        VALUES 
                        (
                            'last_cleanup',
                            JSON_OBJECT(
                                'timestamp', JSON_QUOTE(DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s')),
                                'deleted_count', deleted_count,
                                'retention_days', retention_days
                            ),
                            '最后一次清理记录'
                        )
                        ON DUPLICATE KEY UPDATE 
                            `config_value` = JSON_OBJECT(
                                'timestamp', JSON_QUOTE(DATE_FORMAT(start_time, '%Y-%m-%d %H:%i:%s')),
                                'deleted_count', deleted_count,
                                'retention_days', retention_days
                            ),
                            `updated_at` = NOW();

                        SELECT deleted_count;
                    END
                """)

                conn.commit()

                logger.info("检查点表初始化完成")

    def put(self, config: dict, checkpoint: Checkpoint, metadata: dict) -> None:
        """
        保存检查点到数据库

        Args:
            config: 配置字典，包含 thread_id
            checkpoint: 检查点数据
            metadata: 元数据
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = checkpoint["id"]

        # 获取父检查点（如果有）
        parent_checkpoint = checkpoint.get("parent_checkpoint")

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # 使用 ON DUPLICATE KEY UPDATE 实现插入或更新
                    cursor.execute("""
                        INSERT INTO `checkpoints` 
                        (`thread_id`, `checkpoint_id`, `checkpoint_data`, `metadata`, `parent_checkpoint`)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            `checkpoint_data` = VALUES(`checkpoint_data`),
                            `metadata` = VALUES(`metadata`),
                            `parent_checkpoint` = VALUES(`parent_checkpoint`),
                            `updated_at` = CURRENT_TIMESTAMP
                    """, (
                        thread_id,
                        checkpoint_id,
                        json.dumps(checkpoint, ensure_ascii=False),
                        json.dumps(metadata, ensure_ascii=False),
                        parent_checkpoint
                    ))

                    # 记录历史
                    cursor.execute("""
                        INSERT INTO `checkpoint_history`
                        (`thread_id`, `checkpoint_id`, `operation`)
                        VALUES (%s, %s, 'CREATE')
                        ON DUPLICATE KEY UPDATE
                            `operation` = 'UPDATE',
                            `created_at` = CURRENT_TIMESTAMP
                    """, (thread_id, checkpoint_id))

                    conn.commit()

                    logger.debug(f"检查点已保存: thread_id={thread_id}, checkpoint_id={checkpoint_id}")

                except MySQLError as e:
                    conn.rollback()
                    logger.error(f"保存检查点失败: {e}")
                    raise

    def get(self, config: dict) -> Optional[Checkpoint]:
        """
        从数据库获取检查点

        Args:
            config: 配置字典，包含 thread_id 和可选的 thread_ts

        Returns:
            Checkpoint or None: 检查点数据，不存在则返回 None
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("thread_ts", "latest")

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    if checkpoint_id == "latest":
                        # 获取最新的检查点
                        cursor.execute("""
                            SELECT `checkpoint_data`
                            FROM `checkpoints`
                            WHERE `thread_id` = %s
                            ORDER BY `created_at` DESC
                            LIMIT 1
                        """, (thread_id,))
                    else:
                        # 获取指定ID的检查点
                        cursor.execute("""
                            SELECT `checkpoint_data`
                            FROM `checkpoints`
                            WHERE `thread_id` = %s AND `checkpoint_id` = %s
                        """, (thread_id, checkpoint_id))

                    result = cursor.fetchone()

                    if result and result["checkpoint_data"]:
                        checkpoint_data = result["checkpoint_data"]
                        # 如果是字符串，则解析为JSON
                        if isinstance(checkpoint_data, str):
                            return json.loads(checkpoint_data)
                        return checkpoint_data

                    logger.debug(f"检查点不存在: thread_id={thread_id}, checkpoint_id={checkpoint_id}")
                    return None

                except MySQLError as e:
                    logger.error(f"获取检查点失败: {e}")
                    raise

    def list(self, config: dict) -> Sequence[Checkpoint]:
        """
        列出线程的所有检查点

        Args:
            config: 配置字典，包含 thread_id

        Returns:
            Sequence[Checkpoint]: 检查点列表
        """
        thread_id = config["configurable"]["thread_id"]

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("""
                        SELECT `checkpoint_data`
                        FROM `checkpoints`
                        WHERE `thread_id` = %s
                        ORDER BY `created_at` DESC
                    """, (thread_id,))

                    results = cursor.fetchall()
                    checkpoints = []

                    for row in results:
                        if row and row["checkpoint_data"]:
                            checkpoint_data = row["checkpoint_data"]
                            if isinstance(checkpoint_data, str):
                                checkpoints.append(json.loads(checkpoint_data))
                            else:
                                checkpoints.append(checkpoint_data)

                    logger.debug(f"列出检查点: thread_id={thread_id}, count={len(checkpoints)}")
                    return checkpoints

                except MySQLError as e:
                    logger.error(f"列出检查点失败: {e}")
                    raise

    def get_tuple(self, config: dict) -> Optional[tuple[Checkpoint, CheckpointMetadata]]:
        """
        获取检查点及其元数据

        Args:
            config: 配置字典

        Returns:
            tuple or None: (检查点, 元数据) 或 None
        """
        thread_id = config["configurable"]["thread_id"]
        checkpoint_id = config["configurable"].get("thread_ts", "latest")

        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    if checkpoint_id == "latest":
                        cursor.execute("""
                            SELECT `checkpoint_data`, `metadata`
                            FROM `checkpoints`
                            WHERE `thread_id` = %s
                            ORDER BY `created_at` DESC
                            LIMIT 1
                        """, (thread_id,))
                    else:
                        cursor.execute("""
                            SELECT `checkpoint_data`, `metadata`
                            FROM `checkpoints`
                            WHERE `thread_id` = %s AND `checkpoint_id` = %s
                        """, (thread_id, checkpoint_id))

                    result = cursor.fetchone()

                    if result:
                        checkpoint_data = result["checkpoint_data"]
                        metadata = result["metadata"]

                        # 解析JSON数据
                        if isinstance(checkpoint_data, str):
                            checkpoint = json.loads(checkpoint_data)
                        else:
                            checkpoint = checkpoint_data

                        if isinstance(metadata, str):
                            metadata_dict = json.loads(metadata)
                        else:
                            metadata_dict = metadata

                        return checkpoint, metadata_dict

                    return None

                except MySQLError as e:
                    logger.error(f"获取检查点元组失败: {e}")
                    raise

    # 额外功能方法

    def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """
        删除特定检查点

        Args:
            thread_id: 线程ID
            checkpoint_id: 检查点ID

        Returns:
            bool: 是否成功删除
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    # 先备份到历史表
                    cursor.execute("""
                        INSERT INTO `checkpoint_history`
                        (`thread_id`, `checkpoint_id`, `operation`, `old_data`)
                        SELECT 
                            `thread_id`, 
                            `checkpoint_id`, 
                            'DELETE',
                            `checkpoint_data`
                        FROM `checkpoints`
                        WHERE `thread_id` = %s AND `checkpoint_id` = %s
                    """, (thread_id, checkpoint_id))

                    # 删除检查点
                    cursor.execute("""
                        DELETE FROM `checkpoints`
                        WHERE `thread_id` = %s AND `checkpoint_id` = %s
                    """, (thread_id, checkpoint_id))

                    deleted = cursor.rowcount > 0
                    conn.commit()

                    if deleted:
                        logger.info(f"检查点已删除: {thread_id}/{checkpoint_id}")

                    return deleted

                except MySQLError as e:
                    conn.rollback()
                    logger.error(f"删除检查点失败: {e}")
                    raise

    def cleanup_old_checkpoints(self, retention_days: int = 30) -> int:
        """
        清理过期检查点

        Args:
            retention_days: 保留天数

        Returns:
            int: 删除的记录数
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.callproc("cleanup_expired_checkpoints", (retention_days,))
                    result = cursor.fetchone()

                    conn.commit()

                    deleted_count = result[0] if result else 0
                    logger.info(f"清理过期检查点完成，删除了 {deleted_count} 条记录")

                    return deleted_count

                except MySQLError as e:
                    conn.rollback()
                    logger.error(f"清理检查点失败: {e}")
                    raise

    def get_thread_stats(self, thread_id: str) -> Dict[str, Any]:
        """
        获取线程统计信息

        Args:
            thread_id: 线程ID

        Returns:
            Dict: 统计信息
        """
        with self._get_connection() as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total_checkpoints,
                            MIN(created_at) as first_checkpoint,
                            MAX(created_at) as last_checkpoint,
                            TIMESTAMPDIFF(SECOND, MIN(created_at), MAX(created_at)) as duration_seconds
                        FROM `checkpoints`
                        WHERE `thread_id` = %s
                    """, (thread_id,))

                    stats = cursor.fetchone()

                    if stats:
                        return {
                            "thread_id": thread_id,
                            "total_checkpoints": stats["total_checkpoints"],
                            "first_checkpoint": stats["first_checkpoint"],
                            "last_checkpoint": stats["last_checkpoint"],
                            "duration_seconds": stats["duration_seconds"]
                        }

                    return {
                        "thread_id": thread_id,
                        "total_checkpoints": 0,
                        "first_checkpoint": None,
                        "last_checkpoint": None,
                        "duration_seconds": 0
                    }

                except MySQLError as e:
                    logger.error(f"获取线程统计失败: {e}")
                    raise

    def close(self):
        """关闭所有连接"""
        for conn in self._connection_pool:
            try:
                conn.close()
            except:
                pass
        self._connection_pool.clear()
        logger.info("MySQLCheckpointSaver 已关闭")


# 工厂函数
def create_mysql_checkpoint_saver(
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "langgraph_checkpoints",
        **kwargs
) -> MySQLCheckpointSaver:
    """
    创建 MySQL 检查点保存器（工厂函数）

    Args:
        host: MySQL 主机
        port: 端口
        user: 用户名
        password: 密码
        database: 数据库名
        **kwargs: 其他 MySQLCheckpointSaver 参数

    Returns:
        MySQLCheckpointSaver 实例
    """
    return MySQLCheckpointSaver(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        **kwargs
    )