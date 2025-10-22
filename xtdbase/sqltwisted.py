# !/usr/bin/env python3
"""
==============================================================
Description  : Twisted异步数据库操作模块 - 提供基于Twisted框架的异步MySQL数据库操作功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2023-01-21 00:08:37
LastEditTime : 2024-09-05 16:43:28
FilePath     : /CODE/xjLib/xt_database/sqltwisted.py
Github       : https://github.com/sandorn/home

本模块提供以下核心功能:
- SqlTwisted类:基于Twisted框架的异步MySQL数据库操作类
- 支持异步执行SQL查询、插入和更新操作
- 集成了结果回调和错误处理机制

主要特性:
- 基于Twisted的adbapi实现异步数据库操作
- 自动管理数据库连接池
- 支持自定义表名和数据库配置
- 提供统一的结果回调和错误处理
==============================================================
"""

from __future__ import annotations

import threading
import time
from typing import Any

from twisted.enterprise import adbapi
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from xtlog import mylog

from .cfg import DB_CFG

# 全局reactor线程管理
_reactor_thread: threading.Thread | None = None
_reactor_lock = threading.Lock()
_reactor_started = threading.Event()


def _ensure_reactor_running() -> None:
    """确保reactor在后台线程中运行

    此函数是线程安全的，可以被多次调用。
    只会在第一次调用时启动reactor线程。
    """
    global _reactor_thread

    # 快速检查：如果已经启动，直接返回
    if _reactor_started.is_set():
        return

    with _reactor_lock:
        # 双重检查：防止竞态条件
        if _reactor_started.is_set():
            return

        # 检查reactor是否已经在运行
        if _reactor_thread is not None and _reactor_thread.is_alive():
            _reactor_started.set()
            return

        # 启动reactor在后台线程
        mylog.debug('🚀 启动reactor后台线程...')
        _reactor_thread = threading.Thread(
            target=reactor.run,  # pyright: ignore[reportAttributeAccessIssue]
            kwargs={'installSignalHandlers': False},
            daemon=True,
            name='TwistedReactorThread',
        )
        _reactor_thread.start()

        # 等待reactor完全启动
        time.sleep(0.5)  # 给reactor足够的启动时间
        _reactor_started.set()
        mylog.debug('✅ reactor后台线程已启动')


class SqlTwisted:
    """SqlTwisted - 基于Twisted框架的异步MySQL数据库操作类

    提供异步执行SQL查询、插入和更新操作的功能,自动管理数据库连接池
    并集成了结果回调和错误处理机制。

    Attributes:
        tablename: 默认数据表名
        dbpool: Twisted数据库连接池对象
        cfg: 数据库连接配置字典

    Example:
        >>> # 使用工厂函数创建实例（推荐）
        >>> db = create_sqltwisted('default', 'users')
        >>> # 执行查询
        >>> d = db.perform_query('SELECT * FROM users LIMIT 10')
        >>> d.addCallback(lambda results: print(results))
        >>> # 启动事件循环
        >>> reactor.run()
    """

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db: str,
        charset: str = 'utf8mb4',
        autocommit: bool = True,
        tablename: str | None = None,
        **kwargs: Any,
    ) -> None:
        """初始化SqlTwisted实例,创建数据库连接池

        Args:
            host: 数据库主机地址
            port: 数据库端口号
            user: 数据库用户名
            password: 数据库密码
            db: 数据库名称
            charset: 数据库字符集,默认为'utf8mb4'
            autocommit: 是否自动提交事务,默认为True
            tablename: 默认操作的表名
            **kwargs: 其他Twisted ConnectionPool支持的参数

        Raises:
            ValueError: 当缺少必要的数据库连接参数时抛出
            Exception: 当创建数据库连接池失败时抛出
        """
        self.tablename = tablename
        self.engine = None

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
                raise ValueError(f'❌ 缺少必要的数据库连接参数: {name}')

        # 设置直接参数
        self.cfg = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'charset': charset,
            'autocommit': autocommit,
        }
        self.cfg.update(kwargs)

        # 创建数据库连接池
        try:
            self.dbpool = adbapi.ConnectionPool('pymysql', **self.cfg)
            mylog.info(f'✅ 成功创建Twisted数据库连接池: {host}:{port}/{db}')
        except Exception as err:
            mylog.error(f'❌ 创建数据库连接池失败: {err}')
            raise Exception(f'❌ 创建数据库连接池失败: {err}') from err

    def close(self) -> None:
        """关闭数据库连接池

        Note:
            此方法仅关闭连接池,不会停止reactor事件循环
            如需停止reactor,请显式调用reactor.stop()
        """
        try:
            self.dbpool.close()
            mylog.info('✅ 数据库连接池已关闭')
        except Exception as e:
            mylog.error(f'❌ 关闭数据库连接池失败: {e!s}')

    def _wait_for_result(self, deferred: Deferred[Any], timeout: float = 30.0) -> Any:
        """等待Deferred完成并返回结果

        Args:
            deferred: Deferred对象
            timeout: 超时时间（秒），默认30秒

        Returns:
            Any: Deferred的结果

        Raises:
            TimeoutError: 当操作超时时抛出
            Exception: 当Deferred失败时抛出其异常

        Note:
            此方法会自动确保reactor在后台线程运行
        """
        # 确保reactor正在运行
        _ensure_reactor_running()

        result_container = {'result': None, 'error': None, 'done': False}
        event = threading.Event()

        def on_success(result):
            result_container['result'] = result
            result_container['done'] = True
            event.set()
            return result

        def on_error(failure):
            result_container['error'] = failure
            result_container['done'] = True
            event.set()
            return failure

        deferred.addCallback(on_success)
        deferred.addErrback(on_error)

        # 等待结果
        if not event.wait(timeout):
            raise TimeoutError(f'操作超时({timeout}秒)')

        # 检查是否有错误
        if result_container['error'] is not None:
            # 抛出原始异常
            raise result_container['error'].value

        return result_container['result']

    def perform_query(self, query: str, sync: bool = False, timeout: float = 30.0) -> Deferred[list[dict[str, Any]]] | list[dict[str, Any]]:
        """执行SQL查询语句

        Args:
            query: SQL查询语句
            sync: 是否同步等待结果，默认False（返回Deferred）
            timeout: 同步模式下的超时时间（秒），默认30秒

        Returns:
            Deferred[List[Dict[str, Any]]] | List[Dict[str, Any]]:
                异步模式返回Deferred对象，同步模式返回查询结果列表

        Raises:
            TimeoutError: 同步模式下操作超时时抛出
            Exception: 查询失败时抛出
        """

        # 添加内部回调,但确保结果能够继续传递
        def internal_success(results):
            """内部成功回调,记录日志并返回结果"""
            mylog.info(f'【perform_query 查询成功】: 共{len(results)}条记录')
            return results

        def internal_failure(error):
            """内部失败回调,记录日志并传递错误"""
            mylog.error(f'【perform_query 查询失败】: {error!s}')
            return error

        mylog.info(f'开始执行SQL查询: {query}')
        try:
            defer = self.dbpool.runQuery(query)
            # 确保回调收到的结果不为None
            defer.addCallback(lambda results: results or [])
            defer.addCallbacks(internal_success, internal_failure)

            # 如果需要同步结果，等待Deferred完成
            if sync:
                return self._wait_for_result(defer, timeout)

            return defer
        except Exception as e:
            mylog.error(f'执行查询失败: {e!s}')
            raise

    def query(self, sql: str, sync: bool = False, timeout: float = 30.0) -> Deferred[list[dict[str, Any]]] | list[dict[str, Any]]:
        """执行SQL查询并处理结果

        Args:
            sql: SQL查询语句
            sync: 是否同步等待结果，默认False（返回Deferred）
            timeout: 同步模式下的超时时间（秒），默认30秒

        Returns:
            Deferred[List[Dict[str, Any]]] | List[Dict[str, Any]]:
                异步模式返回Deferred对象，同步模式返回查询结果列表

        Raises:
            TimeoutError: 同步模式下操作超时时抛出
            Exception: 查询失败时抛出
        """
        mylog.info(f'开始执行SQL查询操作: {sql}')
        try:
            defer = self.dbpool.runInteraction(self._query, sql)
            defer.addBoth(self.handle_back, sql, 'query')

            # 如果需要同步结果，等待Deferred完成
            if sync:
                return self._wait_for_result(defer, timeout)

            return defer
        except Exception as e:
            mylog.error(f'执行查询操作失败: {e!s}')
            raise

    def insert(self, item: dict[str, Any], tablename: str | None = None, sync: bool = False, timeout: float = 30.0) -> Deferred[int] | int:
        """插入数据到指定表

        Args:
            item: 要插入的数据字典
            tablename: 目标数据表名（可选,默认使用实例初始化时的表名）
            sync: 是否同步等待结果，默认False（返回Deferred）
            timeout: 同步模式下的超时时间（秒），默认30秒

        Returns:
            Deferred[int] | int: 异步模式返回Deferred对象，同步模式返回受影响行数

        Raises:
            TimeoutError: 同步模式下操作超时时抛出
            Exception: 插入失败时抛出
        """
        tablename = tablename or self.tablename
        mylog.info(f'开始执行数据插入操作,表名:{tablename},数据项数:{len(item)}')
        try:
            defer = self.dbpool.runInteraction(self._insert, item, tablename)
            defer.addBoth(self.handle_back, item, 'insert')

            # 如果需要同步结果，等待Deferred完成
            if sync:
                return self._wait_for_result(defer, timeout)

            return defer
        except Exception as e:
            mylog.error(f'执行插入操作失败: {e!s}')
            raise

    def update(self, item: dict[str, Any], condition: dict[str, Any], tablename: str | None = None, sync: bool = False, timeout: float = 30.0) -> Deferred[int] | int:
        """更新指定表中的数据

        Args:
            item: 要更新的数据字典
            condition: 更新条件字典
            tablename: 目标数据表名（可选,默认使用实例初始化时的表名）
            sync: 是否同步等待结果，默认False（返回Deferred）
            timeout: 同步模式下的超时时间（秒），默认30秒

        Returns:
            Deferred[int] | int: 异步模式返回Deferred对象，同步模式返回受影响行数

        Raises:
            TimeoutError: 同步模式下操作超时时抛出
            Exception: 更新失败时抛出
        """
        tablename = tablename or self.tablename
        mylog.info(f'开始执行数据更新操作,表名:{tablename},条件:{condition}')
        try:
            defer = self.dbpool.runInteraction(self._update, item, condition, tablename)
            defer.addBoth(self.handle_back, item, 'update')

            # 如果需要同步结果，等待Deferred完成
            if sync:
                return self._wait_for_result(defer, timeout)

            return defer
        except Exception as e:
            mylog.error(f'执行更新操作失败: {e!s}')
            raise

    def handle_back(self, result: Any, item: str | dict[str, Any], *args: Any) -> Any:
        """统一处理异步操作的回调结果

        Args:
            result: 操作结果
            item: 原始操作的参数（SQL语句或数据字典）
            *args: 附加参数,通常包含操作类型

        Returns:
            Any: 原始操作结果
        """
        operation = args[0] if args else 'unknown'
        mylog.info(f'【SqlTwisted异步回调 [{operation}] 】: 操作完成')
        return result

    def _query(self, cursor: Any, sql: str) -> list[dict[str, Any]]:
        """执行SQL查询的内部方法

        Args:
            cursor: 数据库游标对象
            sql: SQL查询语句

        Returns:
            List[Dict[str, Any]]: 查询结果集
        """
        try:
            mylog.debug(f'执行SQL查询语句: {sql}')
            # 直接执行查询,不再转换SQL语句类型
            cursor.execute(sql)  # self.dbpool 自带cursor
            results = cursor.fetchall()
            return results or []  # 确保返回空列表而不是None
        except Exception as e:
            mylog.error(f'执行查询操作异常: {e!s}')
            return []

    def _insert(self, cursor: Any, item: dict[str, Any], tablename: str) -> int:
        """执行数据插入的内部方法

        Args:
            cursor: 数据库游标对象
            item: 要插入的数据字典
            tablename: 目标数据表名

        Returns:
            int: 影响的行数
        """
        try:
            # 构建 SQL 语句（使用参数化查询，安全）
            # 列名和表名来自可信源，值使用占位符防止注入
            columns = ', '.join(item.keys())
            values = ', '.join([f'%({k})s' for k in item])
            sql = f'INSERT INTO {tablename} ({columns}) VALUES ({values})'  # noqa: S608
            mylog.debug(f'执行SQL插入语句: {sql}')
            # 使用参数化查询（%(key)s 占位符），安全防止 SQL 注入
            return cursor.execute(sql, item)
        except Exception as e:
            mylog.error(f'执行插入操作异常: {e!s}')
            raise

    def _update(self, cursor: Any, item: dict[str, Any], condition: dict[str, Any], tablename: str) -> int:
        """执行数据更新的内部方法

        Args:
            cursor: 数据库游标对象
            item: 要更新的数据字典
            condition: 更新条件字典
            tablename: 目标数据表名

        Returns:
            int: 影响的行数
        """
        try:
            # 构建 SQL 语句（使用参数化查询，安全）
            # 列名和表名来自可信源，值使用占位符防止注入
            set_clause = ', '.join([f'{k} = %({k})s' for k in item])
            where_clause = ' AND '.join([f'{k} = %({k}_cond)s' for k in condition])

            # 合并参数
            params = item.copy()
            for k, v in condition.items():
                params[f'{k}_cond'] = v

            sql = f'UPDATE {tablename} SET {set_clause} WHERE {where_clause}'  # noqa: S608
            mylog.debug(f'执行SQL更新语句: {sql}')
            # 使用参数化查询（%(key)s 占位符），安全防止 SQL 注入
            return cursor.execute(sql, params)
        except Exception as e:
            mylog.error(f'执行更新操作异常: {e!s}')
            raise


def create_sqltwisted(db_key: str = 'default', tablename: str | None = None, **kwargs) -> SqlTwisted:
    """创建SqlTwisted实例的快捷工厂函数

    提供一种更便捷的方式创建SqlTwisted实例,自动处理数据库配置参数

    Args:
        db_key: 数据库配置键名,对应DB_CFG中的配置项,默认为'default'
        tablename: 默认操作的表名,可选

    Returns:
        SqlTwisted: 配置好的SqlTwisted实例

    Raises:
        ValueError:
            - 当db_key参数不是字符串类型时抛出
            - 当DB_CFG中不存在指定的配置键时抛出

    Example:
        >>> # 创建默认数据库连接
        >>> db = create_sqltwisted()
        >>> # 创建指定配置的数据库连接
        >>> db = create_sqltwisted('TXbx')
        >>> # 创建指定表名的数据库连接
        >>> db = create_sqltwisted('TXbx', 'users2')

    Notes:
        1. 使用DB_CFG中的配置创建连接池,避免硬编码数据库连接信息
        2. 创建过程中自动初始化连接池,可直接用于数据库操作
        3. 配置文件应包含host、port、user、password、db等必要信息
    """
    # 参数类型验证
    if not isinstance(db_key, str):
        raise ValueError(f'❌ 配置键非字符串类型: [{type(db_key).__name__}]')

    # 配置键存在性检查
    if not hasattr(DB_CFG, db_key):
        raise ValueError(f'❌ DB_CFG数据库配置中 [{db_key}] 不存在')

    # 获取配置并创建连接池
    cfg = DB_CFG[db_key].value[0].copy()
    cfg.pop('type', None)  # 移除类型字段(如果存在)

    mylog.info(f'▶️ 正在创建SqlTwisted实例,配置键: {db_key}')

    # 创建并返回SqlTwisted实例
    return SqlTwisted(**cfg, tablename=tablename, **kwargs)
