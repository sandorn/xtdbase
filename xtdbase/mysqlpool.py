# !/usr/bin/env python
"""
==============================================================
Description  : 异步MySQL连接池模块 - 基于aiomysql提供标准化的异步数据库操作
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-22 17:00:00
FilePath     : /xtdbase/mysqlpool.py
Github       : https://github.com/sandorn/xtdbase

本模块提供以下核心功能:
    - MySQLPool: 单例模式的异步MySQL连接池类,基于aiomysql实现高效连接管理
    - create_mysql_pool: 快捷工厂函数,简化连接池创建过程

主要特性:
    - 连接池自动管理: 支持最小/最大连接数配置和自动连接回收
    - 标准化接口: 方法命名与Python DB-API 2.0规范保持一致
    - 完整的CRUD操作: fetchone/fetchall/fetchmany/execute等标准接口
    - 异步上下文管理器: 使用async with语句自动处理资源
    - 事务支持: begin/commit/rollback确保数据一致性和原子性
    - 异步迭代器: 高效处理大量数据,避免内存溢出
    - 连接健康检查: 自动重连和ping检测确保连接可用性
    - 统一的错误处理: 完善的异常捕获和日志记录机制
    - 完整的类型注解: 支持Python 3.10+现代类型系统

使用示例:
    >>> import asyncio
    >>> from xtdbase.mysqlpool import create_mysql_pool
    >>>
    >>> async def main():
    ...     # 使用上下文管理器（推荐）
    ...     async with create_mysql_pool('default') as db:
    ...         # 查询单条记录
    ...         user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
    ...         # 查询多条记录
    ...         users = await db.fetchall('SELECT * FROM users LIMIT 10')
    ...         # 执行插入/更新
    ...         affected = await db.execute('INSERT INTO users(name) VALUES (%s)', 'Alice')
    >>>
    >>> asyncio.run(main())

注意事项:
    - 本模块采用单例模式,相同配置会返回同一个连接池实例
    - 建议使用异步上下文管理器确保资源正确释放
    - 大量数据查询建议使用iterate()方法避免内存溢出
    - 事务操作需要手动管理commit和rollback
==============================================================
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from threading import RLock
from typing import Any
from weakref import WeakValueDictionary

import aiomysql
import pymysql
from xtlog import mylog

from .cfg import DB_CFG


class Singleton:
    """线程安全的单例混入类实现

    核心功能：
    - 通过混入方式实现单例模式
    - 支持与其他类的多重继承
    - 双重检查锁确保线程安全
    - 使用弱引用字典避免内存泄漏
    - 提供完整的实例管理接口

    类方法：
    - get_instance: 获取当前单例实例（不创建新实例）
    - reset_instance: 重置单例实例
    - has_instance: 检查是否存在单例实例

    类属性：
    - _instances: 弱引用字典，存储类与实例的映射关系
    - _instance_lock: 可重入锁，确保线程安全
    """

    _instance_lock: RLock = RLock()  # 可重入锁，避免递归调用问题
    _instances: WeakValueDictionary[type, Any] = WeakValueDictionary()

    def __new__(cls: type[Any], *args: Any, **kwargs: Any) -> Any:
        """实例化处理（带错误日志和双重检查锁）"""
        # 第一次检查(无锁)
        if cls in cls._instances:
            return cls._instances[cls]

        # 获取锁
        with cls._instance_lock:
            # 第二次检查(有锁)
            if cls in cls._instances:
                return cls._instances[cls]

            try:
                # 创建实例
                instance = super().__new__(cls)
                # 存储实例引用
                cls._instances[cls] = instance
                # 注意：不手动调用__init__，让Python正常流程处理初始化
                return instance
            except Exception as e:
                # 清理失败的实例
                if cls in cls._instances:
                    del cls._instances[cls]
                # 改进错误处理，记录异常并重新抛出
                raise RuntimeError(f'SingletonMixin {cls.__name__} __new__ failed: {e}') from e

    @classmethod
    def reset_instance(cls: type[Any]) -> None:
        """重置单例实例"""
        with cls._instance_lock:
            cls._instances.pop(cls, None)  # 移除该类的实例引用

    @classmethod
    def has_instance(cls: type[Any]) -> bool:
        """检查是否存在单例实例"""
        return cls in cls._instances

    @classmethod
    def get_instance(cls: type[Any]) -> Any | None:
        """获取当前单例实例（不创建新实例）"""
        return cls._instances.get(cls) if cls in cls._instances else None


class MySQLPool(Singleton):
    """异步MySQL连接池封装类,遵循Python DB-API 2.0规范.

    Attributes:
        pool: aiomysql连接池实例
        cfg: 连接池配置字典
        autocommit: 是否自动提交事务
        cursorclass: 游标类型,默认DictCursor
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db: str,
        minsize: int = 1,
        maxsize: int = 10,
        charset: str = 'utf8mb4',
        autocommit: bool = True,
        cursorclass: type[aiomysql.cursors.Cursor] = aiomysql.cursors.DictCursor,
        pool_recycle: int = -1,
        **kwargs,
    ):
        """初始化连接池配置.

        Args:
            host: 数据库主机地址
            port: 数据库端口号
            user: 数据库用户名
            password: 数据库密码
            db: 数据库名称
            minsize: 连接池最小连接数,默认1
            maxsize: 连接池最大连接数,默认10
            charset: 数据库字符集,默认'utf8mb4'
            autocommit: 是否自动提交,默认True
            cursorclass: 游标类型,默认DictCursor
            pool_recycle: 连接回收时间(秒),-1表示不回收,默认-1
            **kwargs: 其他aiomysql.create_pool参数
        """
        # 验证必要参数
        required_params = [
            (host, 'host'),
            (port, 'port'),
            (user, 'user'),
            (password, 'password'),
            (db, 'db'),
        ]
        for param, name in required_params:
            if param is None:
                raise ValueError(f'缺少必要的数据库连接参数: {name}')

        # 设置实例属性
        self.autocommit = autocommit
        self.cursorclass = cursorclass
        self.pool: aiomysql.Pool | None = None

        # 构建连接池配置字典
        self.cfg = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'minsize': minsize,
            'maxsize': maxsize,
            'charset': charset,
            'autocommit': autocommit,
            'cursorclass': cursorclass,
            'pool_recycle': pool_recycle,
            'echo': __name__ == '__main__',
        }
        self.cfg.update(kwargs)

        mylog.debug(f'初始化连接池配置: {host}:{port}/{db}, minsize={minsize}, maxsize={maxsize}')

    async def close(self) -> None:
        """关闭连接池,释放所有资源."""
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            mylog.info('✅ 连接池已关闭,所有连接已释放')
            self.pool = None

    async def init_pool(self) -> None:
        """初始化连接池.若已存在则跳过."""
        if self.pool is not None:
            mylog.debug('连接池已存在,跳过初始化')
            return

        mylog.info(f'🚀 正在初始化连接池: {self.cfg["host"]}:{self.cfg["port"]}/{self.cfg["db"]}')
        self.pool = await aiomysql.create_pool(
            **self.cfg,
            loop=asyncio.get_running_loop(),
        )
        mylog.info(f'✅ 连接池初始化成功,池大小: {self.cfg["minsize"]}-{self.cfg["maxsize"]}')

    async def ping(self) -> bool:
        """测试连接池是否可用.

        Returns:
            bool: 连接正常返回True,否则返回False
        """
        try:
            if self.pool is None:
                await self.init_pool()

            assert self.pool is not None  # Type guard: 连接池已初始化
            async with self.pool.acquire() as conn:
                await conn.ping()
                return True
        except Exception as e:
            mylog.error(f'❌ 连接池ping失败: {e!s}')
            return False

    @property
    def pool_size(self) -> tuple[int, int] | None:
        """获取连接池状态(当前连接数, 最大连接数)."""
        if self.pool is None:
            return None
        # 类型断言：aiomysql.Pool的size和maxsize属性在连接池创建后总是int类型
        return (self.pool.size, self.pool.maxsize)  # type: ignore[return-value]

    async def execute(self, query: str, *parameters, **kwparameters) -> int:
        """执行INSERT/UPDATE/DELETE语句.

        Args:
            query: SQL语句
            *parameters: 位置参数
            **kwparameters: 命名参数

        Returns:
            int: INSERT返回lastrowid,UPDATE/DELETE返回受影响行数
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(query, kwparameters or parameters)
            except (pymysql.err.InternalError, pymysql.err.OperationalError):
                # 连接失效,尝试重连
                mylog.warning('连接失效,正在重连并重试...')
                await conn.ping()
                await cur.execute(query, kwparameters or parameters)
            return cur.lastrowid if 'INSERT' in query.upper() else cur.rowcount

    async def get_cursor(self) -> tuple[aiomysql.Connection, aiomysql.Cursor]:
        """获取连接和游标.使用后必须调用close_cursor()释放资源.

        Returns:
            tuple: (连接对象, 游标对象)
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        conn = await self.pool.acquire()
        cur = await conn.cursor(cursorclass=self.cursorclass)
        return conn, cur

    async def close_cursor(self, conn: aiomysql.Connection, cur: aiomysql.Cursor) -> None:
        """关闭游标并释放连接.

        Args:
            conn: 连接对象
            cur: 游标对象
        """
        try:
            if not self.autocommit:
                await conn.commit()
            await cur.close()
        finally:
            if self.pool is not None:
                self.pool.release(conn)

    async def fetchone(self, query: str, *parameters, **kwparameters) -> dict[str, Any] | None:
        """查询单条记录(DB-API 2.0).

        Args:
            query: SELECT语句
            *parameters: 位置参数
            **kwparameters: 命名参数

        Returns:
            dict[str, Any] | None: 查询结果字典,无记录返回None
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchone()
            except (pymysql.err.InternalError, pymysql.err.OperationalError):
                mylog.warning('连接失效,正在重连并重试...')
                await conn.ping()
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchone()

    async def fetchall(self, query: str, *parameters, **kwparameters) -> list[dict[str, Any]]:
        """查询所有记录(DB-API 2.0).大数据量请使用iterate().

        Args:
            query: SELECT语句
            *parameters: 位置参数
            **kwparameters: 命名参数

        Returns:
            list[dict[str, Any]]: 结果列表,无记录返回空列表
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchall()
            except (pymysql.err.InternalError, pymysql.err.OperationalError):
                mylog.warning('连接失效,正在重连并重试...')
                await conn.ping()
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchall()

    async def fetchmany(self, query: str, size: int, *parameters, **kwparameters) -> list[dict[str, Any]]:
        """查询指定数量记录(DB-API 2.0).

        Args:
            query: SELECT语句
            size: 获取记录数量
            *parameters: 位置参数
            **kwparameters: 命名参数

        Returns:
            list[dict[str, Any]]: 结果列表,最多size条
        """
        if size <= 0:
            raise ValueError(f'size必须大于0,当前值: {size}')

        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchmany(size)
            except (pymysql.err.InternalError, pymysql.err.OperationalError):
                mylog.warning('连接失效,正在重连并重试...')
                await conn.ping()
                await cur.execute(query, kwparameters or parameters)
                return await cur.fetchmany(size)

    async def __aenter__(self) -> MySQLPool:
        """进入异步上下文,自动初始化连接池."""
        await self.init_pool()
        mylog.debug('进入异步上下文管理器')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出异步上下文,自动关闭连接池."""
        if exc_type is not None:
            mylog.error(f'上下文中发生异常: {exc_type.__name__}: {exc_val}')
        await self.close()
        mylog.debug('退出异步上下文管理器')

    async def begin(self) -> aiomysql.Connection:
        """开始事务,返回连接对象.必须手动调用commit()或rollback().

        Returns:
            aiomysql.Connection: 事务连接
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        conn = await self.pool.acquire()
        await conn.begin()
        mylog.debug('事务已开始')
        return conn

    async def commit(self, conn: aiomysql.Connection) -> None:
        """提交事务并释放连接.

        Args:
            conn: begin()返回的连接
        """
        try:
            await conn.commit()
            mylog.debug('事务已提交')
        finally:
            if self.pool is not None:
                self.pool.release(conn)

    async def rollback(self, conn: aiomysql.Connection) -> None:
        """回滚事务并释放连接.

        Args:
            conn: begin()返回的连接
        """
        try:
            await conn.rollback()
            mylog.debug('事务已回滚')
        finally:
            if self.pool is not None:
                self.pool.release(conn)

    async def iterate(
        self,
        query: str,
        *parameters,
        batch_size: int = 1000,
        **kwparameters,
    ) -> AsyncIterator[dict[str, Any]]:
        """异步迭代查询结果,内存友好,适合大数据量.

        Args:
            query: SELECT语句
            *parameters: 位置参数
            batch_size: 每批获取数量,默认1000
            **kwparameters: 命名参数

        Yields:
            dict[str, Any]: 每条记录
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        async with self.pool.acquire() as conn, conn.cursor() as cur:
            try:
                await cur.execute(query, kwparameters or parameters)
            except (pymysql.err.InternalError, pymysql.err.OperationalError):
                mylog.warning('连接失效,正在重连并重试...')
                await conn.ping()
                await cur.execute(query, kwparameters or parameters)

            processed = 0
            while True:
                batch = await cur.fetchmany(batch_size)
                if not batch:
                    break
                for row in batch:
                    processed += 1
                    yield row

            mylog.debug(f'迭代完成,共处理 {processed} 条记录')


def create_mysql_pool(db_key: str = 'default', **kwargs: Any) -> MySQLPool:
    """创建MySQL连接池工厂函数(推荐使用).

    从cfg.py的DB_CFG读取配置并创建连接池实例(单例模式).

    Args:
        db_key: 配置键名,默认'default'
        **kwargs: 额外参数,会覆盖配置中的同名参数

    Returns:
        MySQLPool: 连接池实例

    Raises:
        ValueError: db_key不是字符串或配置不存在
    """
    # 参数类型验证
    if not isinstance(db_key, str):
        raise ValueError(f'配置键必须是字符串类型,当前类型: {type(db_key).__name__}')

    # 配置键存在性检查
    if not hasattr(DB_CFG, db_key):
        available_keys = [key for key in dir(DB_CFG) if not key.startswith('_')]
        raise ValueError(f'DB_CFG中不存在配置键 "{db_key}"\n可用的配置键: {", ".join(available_keys)}')

    # 获取配置并创建连接池
    cfg = DB_CFG[db_key].value[0].copy()
    cfg.pop('type', None)  # 移除type字段(如果存在)

    mylog.info(f'🔨 正在创建连接池实例,配置键: {db_key}')
    return MySQLPool(**cfg, **kwargs)
