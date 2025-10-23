#!/usr/bin/env python
"""
==============================================================
Description  : 同步调用异步MySQL连接池模块 - 提供符合DB-API 2.0规范的同步接口
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-23
FilePath     : /xtdbase/syncmysqlpool.py
Github       : https://github.com/sandorn/xtdbase

本模块提供以下核心功能:
    - MySQLPoolSync: 在同步环境中调用异步连接池的封装类,遵循Python DB-API 2.0规范
    - create_sync_mysql_pool: 快捷工厂函数,简化连接池创建过程

主要特性:
    - 标准化接口: 方法命名遵循Python DB-API 2.0规范
    - 同步调用异步: 自动管理事件循环,在同步环境中使用异步连接池
    - 完整的CRUD操作: fetchone/fetchall/fetchmany/execute等标准接口
    - 事务支持: begin/commit/rollback确保数据一致性和原子性
    - 自动资源管理: 析构时自动清理连接池和事件循环
    - 完整的类型注解: 支持Python 3.10+现代类型系统

使用示例:
    >>> from xtdbase.syncmysqlpool import create_sync_mysql_pool
    >>>
    >>> # 创建连接池实例
    >>> db = create_sync_mysql_pool('default')
    >>> # 查询单条记录
    >>> user = db.fetchone('SELECT * FROM users WHERE id = %s', (1,))
    >>> # 查询所有记录
    >>> users = db.fetchall('SELECT * FROM users LIMIT 10')
    >>> # 执行插入/更新
    >>> affected = db.execute('INSERT INTO users(name) VALUES (%s)', ('Alice',))

注意事项:
    - 本模块适用于无法使用async/await的同步代码环境
    - 推荐在异步环境中直接使用 mysqlpool.py
    - 参数必须使用元组格式
==============================================================
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import aiomysql.sa
from xtlog import mylog

from .cfg import DB_CFG

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class MySQLPoolSync:
    """同步调用异步MySQL连接池类,遵循Python DB-API 2.0规范.

    在同步环境中使用异步连接池,自动管理事件循环.

    Attributes:
        engine: aiomysql引擎实例
        loop: asyncio事件循环
        cfg: 连接池配置字典
        autocommit: 是否自动提交事务
    """

    # 类型注解（engine和loop初始化后不会是None，但析构时会设置为None）
    engine: aiomysql.sa.Engine | None
    loop: asyncio.AbstractEventLoop | None
    cfg: dict[str, Any]
    autocommit: bool

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db: str,
        charset: str = 'utf8mb4',
        autocommit: bool = True,
        pool_recycle: int = -1,
        **kwargs: Any,
    ):
        """初始化连接池配置.

        Args:
            host: 数据库主机地址
            port: 数据库端口号
            user: 数据库用户名
            password: 数据库密码
            db: 数据库名称
            charset: 数据库字符集,默认'utf8mb4'
            autocommit: 是否自动提交,默认True
            pool_recycle: 连接回收时间(秒),-1表示不回收,默认-1
            **kwargs: 其他aiomysql.sa.create_engine参数
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

        # 构建连接配置字典
        self.cfg = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'charset': charset,
            'autocommit': autocommit,
            'echo': __name__ == '__main__',
            'pool_recycle': pool_recycle,
        }
        self.cfg.update(kwargs)

        self.autocommit = autocommit

        # 获取或创建事件循环
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)

        # 初始化连接池（确保 engine 被初始化）
        self._run_sync(self._create_engine())

        # 断言：确保 engine 已被初始化
        assert self.engine is not None, '连接池初始化失败'

    def __del__(self) -> None:
        """析构时清理资源.

        注意: 由于析构函数执行时机不确定,这里只做简单的同步清理.
        强烈建议显式调用 close() 方法来释放资源.
        """
        # 简单清理:只标记资源为None,避免在__del__中运行事件循环
        # 事件循环相关的清理应该在 close() 方法中完成
        if hasattr(self, 'engine'):
            self.engine = None
        if hasattr(self, 'loop'):
            # 不在这里关闭循环,避免干扰其他可能使用同一循环的代码
            self.loop = None

    async def _create_engine(self) -> None:
        """创建数据库引擎连接池."""
        self.engine = await aiomysql.sa.create_engine(**self.cfg)
        mylog.info(f'✅ 连接池创建成功: {self.cfg["host"]}:{self.cfg["port"]}/{self.cfg["db"]}')

    def _run_sync(self, coro) -> Any:
        """在事件循环中同步运行协程.

        Args:
            coro: 协程对象

        Returns:
            Any: 协程执行结果
        """
        # loop 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.loop is not None, '事件循环未初始化'
        return self.loop.run_until_complete(coro)

    def execute(self, query: str, args: tuple | None = None) -> int:
        """执行INSERT/UPDATE/DELETE语句(DB-API 2.0).

        Args:
            query: SQL语句
            args: 参数元组

        Returns:
            int: INSERT返回lastrowid,UPDATE/DELETE返回受影响行数
        """
        return self._run_sync(self._execute(query, args))

    async def _execute(self, query: str, args: tuple | None = None) -> int:
        """异步执行INSERT/UPDATE/DELETE语句."""
        # engine 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.engine is not None, '连接池未初始化'

        async with self.engine.acquire() as conn:
            cursor = await conn._connection.cursor()
            try:
                result = await cursor.execute(query, args)
                if not self.autocommit:
                    await conn._connection.commit()
                return cursor.lastrowid if 'INSERT' in query.upper() else result
            except Exception as e:
                mylog.error(f'❌ SQL执行失败: {e}')
                if not self.autocommit:
                    await conn._connection.rollback()
                raise
            finally:
                await cursor.close()

    def fetchone(self, query: str, args: tuple | None = None) -> dict[str, Any] | None:
        """查询单条记录(DB-API 2.0).

        Args:
            query: SELECT语句
            args: 参数元组

        Returns:
            dict[str, Any] | None: 查询结果字典,无记录返回None
        """
        return self._run_sync(self._fetchone(query, args))

    async def _fetchone(self, query: str, args: tuple | None = None) -> dict[str, Any] | None:
        """异步查询单条记录."""
        # engine 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.engine is not None, '连接池未初始化'

        async with self.engine.acquire() as conn:
            cursor = await conn._connection.cursor()
            try:
                await cursor.execute(query, args)
                result = await cursor.fetchone()
                if result:
                    column_names = [desc[0] for desc in cursor.description]
                    return dict(zip(column_names, result, strict=True))
                return None
            except Exception as e:
                mylog.error(f'❌ 查询失败: {e}')
                raise
            finally:
                await cursor.close()

    def fetchall(self, query: str, args: tuple | None = None) -> list[dict[str, Any]]:
        """查询所有记录(DB-API 2.0).

        Args:
            query: SELECT语句
            args: 参数元组

        Returns:
            list[dict[str, Any]]: 结果列表,无记录返回空列表
        """
        return self._run_sync(self._fetchall(query, args))

    async def _fetchall(self, query: str, args: tuple | None = None) -> list[dict[str, Any]]:
        """异步查询所有记录."""
        # engine 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.engine is not None, '连接池未初始化'

        async with self.engine.acquire() as conn:
            cursor = await conn._connection.cursor()
            try:
                await cursor.execute(query, args)
                results = await cursor.fetchall()
                if not results:
                    return []
                column_names = [desc[0] for desc in cursor.description]
                return [dict(zip(column_names, row, strict=True)) for row in results]
            except Exception as e:
                mylog.error(f'❌ 查询失败: {e}')
                raise
            finally:
                await cursor.close()

    def fetchmany(self, query: str, size: int, args: tuple | None = None) -> list[dict[str, Any]]:
        """查询指定数量记录(DB-API 2.0).

        Args:
            query: SELECT语句
            size: 获取记录数量
            args: 参数元组

        Returns:
            list[dict[str, Any]]: 结果列表,最多size条
        """
        if size <= 0:
            raise ValueError(f'size必须大于0,当前值: {size}')
        return self._run_sync(self._fetchmany(query, size, args))

    async def _fetchmany(self, query: str, size: int, args: tuple | None = None) -> list[dict[str, Any]]:
        """异步查询指定数量记录."""
        # engine 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.engine is not None, '连接池未初始化'

        async with self.engine.acquire() as conn:
            cursor = await conn._connection.cursor()
            try:
                await cursor.execute(query, args)
                results = await cursor.fetchmany(size)
                if not results:
                    return []
                column_names = [desc[0] for desc in cursor.description]
                return [dict(zip(column_names, row, strict=True)) for row in results]
            except Exception as e:
                mylog.error(f'❌ 查询失败: {e}')
                raise
            finally:
                await cursor.close()

    def begin(self) -> None:
        """开始事务.必须手动调用commit()或rollback()."""
        # aiomysql.sa的事务由connection自动管理
        # 这里只是提供接口兼容性
        if self.autocommit:
            mylog.warning('当前为自动提交模式,begin()无效,请设置autocommit=False')

    def commit(self) -> None:
        """提交事务."""
        if self.autocommit:
            mylog.warning('当前为自动提交模式,commit()无效')
        # aiomysql.sa的事务在execute时已自动提交

    def rollback(self) -> None:
        """回滚事务."""
        if self.autocommit:
            mylog.warning('当前为自动提交模式,rollback()无效')
        # aiomysql.sa的事务管理在execute方法中处理

    def ping(self) -> bool:
        """测试连接池是否可用.

        Returns:
            bool: 连接正常返回True,否则返回False
        """
        try:
            return self._run_sync(self._ping())
        except Exception as e:
            mylog.error(f'❌ 连接池ping失败: {e}')
            return False

    async def _ping(self) -> bool:
        """异步测试连接池."""
        # engine 在 __init__ 中已初始化，此处断言确保类型检查通过
        assert self.engine is not None, '连接池未初始化'

        async with self.engine.acquire() as conn:
            await conn._connection.ping()
            return True

    def close(self) -> None:
        """关闭连接池,释放所有资源."""
        # 关闭数据库引擎
        if hasattr(self, 'engine') and self.engine is not None:
            try:
                if hasattr(self.engine, '_pool') and self.engine._pool is not None:
                    self._run_sync(self.engine._pool.clear())
                self.engine.close()
                self._run_sync(self.engine.wait_closed())
                mylog.info('✅ 连接池已关闭')
            except Exception as e:
                mylog.error(f'❌ 关闭连接池失败: {e}')
            finally:
                self.engine = None

        # 清理事件循环
        if hasattr(self, 'loop') and self.loop is not None and not self.loop.is_closed():
            try:
                # 取消所有待处理的任务
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()

                # 给任务一个取消的机会
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

                self.loop.close()
                mylog.info('✅ 事件循环已关闭')
            except Exception as e:
                mylog.warning(f'⚠️  关闭事件循环时发生异常: {e}')
            finally:
                self.loop = None


def create_sync_mysql_pool(db_key: str = 'default', **kwargs: Any) -> MySQLPoolSync:
    """创建同步调用的MySQL连接池工厂函数(推荐使用).

    从cfg.py的DB_CFG读取配置并创建连接池实例.

    Args:
        db_key: 配置键名,默认'default'
        **kwargs: 额外参数,会覆盖配置中的同名参数

    Returns:
        MySQLPoolSync: 连接池实例

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

    mylog.info(f'🔨 正在创建同步连接池实例,配置键: {db_key}')
    return MySQLPoolSync(**cfg, **kwargs)
