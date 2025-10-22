# !/usr/bin/env python
"""
==============================================================
Description  : 异步MySQL连接池模块 - 基于aiomysql提供标准化的异步数据库操作
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-22 17:00:00
FilePath     : /xtdbase/aiomysqlpool.py
Github       : https://github.com/sandorn/xtdbase

本模块提供以下核心功能:
    - AioMySQLPool: 单例模式的异步MySQL连接池类,基于aiomysql实现高效连接管理
    - create_async_mysql_pool: 快捷工厂函数,简化连接池创建过程

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
    >>> from xtdbase.aiomysqlpool import create_async_mysql_pool
    >>>
    >>> async def main():
    ...     # 使用上下文管理器（推荐）
    ...     async with create_async_mysql_pool('default') as db:
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
from typing import Any

import aiomysql
import pymysql
from xtlog import mylog
from xtwraps import SingletonMixin

from xtdbase.cfg import DB_CFG


class AioMySQLPool(SingletonMixin):
    """异步MySQL连接池封装类 - 基于aiomysql实现高效的数据库连接管理.

    本类继承自单例模式混入类,确保相同配置只创建一个连接池实例,
    提供完整的异步数据库操作接口,方法命名遵循Python DB-API 2.0规范。

    Attributes:
        pool (aiomysql.Pool | None): aiomysql连接池实例
        cfg (dict[str, Any]): 连接池配置字典
        autocommit (bool): 是否自动提交事务
        cursorclass (type[aiomysql.cursors.Cursor]): 游标类型,默认DictCursor

    主要功能:
        - 标准查询接口: fetchone, fetchall, fetchmany
        - 数据修改接口: execute (INSERT/UPDATE/DELETE)
        - 事务管理: begin, commit, rollback
        - 连接管理: init_pool, close, ping
        - 迭代器支持: iterate (处理大量数据)
        - 上下文管理器: 自动资源管理

    Example:
        基本使用::

            >>> import asyncio
            >>> from xtdbase.aiomysqlpool import create_async_mysql_pool
            >>>
            >>> async def main():
            ...     # 方式1: 使用上下文管理器（推荐）
            ...     async with create_async_mysql_pool('default') as db:
            ...         # 查询单条记录
            ...         user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
            ...         print(user)
            ...
            ...         # 查询多条记录
            ...         users = await db.fetchall('SELECT * FROM users LIMIT 10')
            ...         print(f'共查询到 {len(users)} 条记录')
            ...
            ...         # 执行插入
            ...         new_id = await db.execute(
            ...             'INSERT INTO users(username, email) VALUES (%s, %s)',
            ...             'alice', 'alice@example.com'
            ...         )
            ...         print(f'新插入记录ID: {new_id}')
            >>>
            >>> asyncio.run(main())

        事务操作::

            >>> async def transaction_example():
            ...     async with create_async_mysql_pool('default') as db:
            ...         conn = await db.begin()
            ...         try:
            ...             # 执行多个操作
            ...             cur = await conn.cursor()
            ...             await cur.execute('INSERT INTO accounts(name, balance) VALUES (%s, %s)', ('Alice', 1000))
            ...             await cur.execute('UPDATE accounts SET balance = balance - 100 WHERE name = %s', 'Alice')
            ...             # 提交事务
            ...             await db.commit(conn)
            ...         except Exception:
            ...             # 回滚事务
            ...             await db.rollback(conn)
            ...             raise

        迭代器处理大量数据::

            >>> async def iterate_example():
            ...     async with create_async_mysql_pool('default') as db:
            ...         # 批量处理,避免内存溢出
            ...         async for row in db.iterate('SELECT * FROM large_table', batch_size=1000):
            ...             # 处理每一行
            ...             process(row)

    Note:
        - 使用单例模式,相同连接参数会返回同一实例
        - 方法命名遵循DB-API 2.0规范,与标准库保持一致
        - 建议使用上下文管理器自动管理资源
        - 连接失效时会自动重连并重试操作
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
        """初始化异步MySQL连接池配置.

        Args:
            host: 数据库主机地址（如 'localhost' 或 IP地址）
            port: 数据库端口号（MySQL默认3306）
            user: 数据库用户名
            password: 数据库密码
            db: 数据库名称
            minsize: 连接池最小连接数,保持活跃的最少连接,默认1
            maxsize: 连接池最大连接数,最多允许的连接数,默认10
            charset: 数据库字符集,推荐使用'utf8mb4'支持完整Unicode,默认'utf8mb4'
            autocommit: 是否自动提交事务,True为每条SQL自动提交,默认True
            cursorclass: 游标类型,DictCursor返回字典,默认DictCursor
            pool_recycle: 连接回收时间(秒),超过此时间的连接会被回收,-1表示不回收,默认-1
            **kwargs: 其他aiomysql.create_pool支持的参数

        Raises:
            ValueError: 当必要的连接参数缺失时抛出

        Example:
            >>> # 直接初始化连接池（不推荐,建议使用create_async_mysql_pool工厂函数）
            >>> db = AioMySQLPool(host='localhost', port=3306, user='root', password='password', db='test_db', minsize=5, maxsize=20)

        Note:
            - 推荐使用create_async_mysql_pool()工厂函数创建实例
            - minsize建议设置为1-5,避免占用过多连接
            - maxsize根据并发需求设置,通常10-50
            - 使用DictCursor可以通过字段名访问结果
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
        """关闭连接池,释放所有资源.

        关闭连接池中的所有连接并释放资源。
        此方法是幂等的,多次调用不会产生错误。

        Example:
            >>> db = create_async_mysql_pool('default')
            >>> # ... 执行数据库操作 ...
            >>> await db.close()

        Note:
            - 使用上下文管理器时会自动调用此方法
            - 关闭后需要重新初始化才能使用
        """
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            mylog.info('✅ 连接池已关闭,所有连接已释放')
            self.pool = None

    async def init_pool(self) -> None:
        """初始化连接池.

        创建aiomysql连接池实例,建立初始连接。
        如果连接池已存在,则直接返回不重复创建。

        Raises:
            aiomysql.Error: 创建连接池失败时抛出
            ValueError: 配置参数错误时抛出

        Example:
            >>> db = create_async_mysql_pool('default')
            >>> await db.init_pool()  # 显式初始化
            >>> # 通常不需要手动调用,首次查询时会自动初始化

        Note:
            - 通常不需要手动调用,首次查询时会自动初始化
            - 使用单例模式,相同配置返回同一实例
            - 初始化时会创建minsize数量的连接
        """
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

        尝试从连接池获取连接并执行ping操作,验证数据库连接是否正常。

        Returns:
            bool: 连接正常返回True,否则返回False

        Example:
            >>> db = create_async_mysql_pool('default')
            >>> if await db.ping():
            ...     print('数据库连接正常')
            ... else:
            ...     print('数据库连接失败')

        Note:
            - 此方法会自动初始化连接池（如果未初始化）
            - 可用于健康检查和连接恢复验证
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
        """获取连接池当前状态.

        Returns:
            tuple[int, int] | None: (当前连接数, 最大连接数),未初始化返回None

        Example:
            >>> db = create_async_mysql_pool('default')
            >>> await db.init_pool()
            >>> if db.pool_size:
            ...     current, maximum = db.pool_size
            ...     print(f'当前连接数: {current}/{maximum}')
        """
        if self.pool is None:
            return None
        # 类型断言：aiomysql.Pool的size和maxsize属性在连接池创建后总是int类型
        return (self.pool.size, self.pool.maxsize)  # type: ignore[return-value]

    async def execute(self, query: str, *parameters, **kwparameters) -> int:
        """执行INSERT/UPDATE/DELETE等DML语句,返回受影响行数或最后插入ID.

        Args:
            query: SQL语句,支持占位符(%s)
            *parameters: 位置参数,用于替换占位符
            **kwparameters: 命名参数,用于替换占位符

        Returns:
            int: INSERT返回lastrowid(新插入记录的ID),
                 UPDATE/DELETE返回受影响的行数

        Raises:
            aiomysql.Error: SQL执行错误时抛出
            pymysql.err.IntegrityError: 违反约束时抛出

        Example:
            >>> # 插入数据
            >>> new_id = await db.execute('INSERT INTO users(username, email) VALUES (%s, %s)', 'alice', 'alice@example.com')
            >>> print(f'新插入记录ID: {new_id}')
            >>>
            >>> # 更新数据
            >>> affected = await db.execute('UPDATE users SET email = %s WHERE username = %s', 'newemail@example.com', 'alice')
            >>> print(f'更新了 {affected} 条记录')
            >>>
            >>> # 删除数据
            >>> affected = await db.execute('DELETE FROM users WHERE username = %s', 'alice')

        Note:
            - 连接失效时会自动重连并重试一次
            - INSERT操作返回lastrowid,其他操作返回受影响行数
            - 使用参数化查询防止SQL注入
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
        """获取数据库连接和游标.

        从连接池获取一个连接并创建游标,用于执行自定义SQL操作。

        Returns:
            tuple[aiomysql.Connection, aiomysql.Cursor]: (连接对象, 游标对象)

        Raises:
            aiomysql.Error: 获取连接失败时抛出

        Example:
            >>> db = create_async_mysql_pool('default')
            >>> conn, cur = await db.get_cursor()
            >>> try:
            ...     await cur.execute('SELECT * FROM users')
            ...     result = await cur.fetchall()
            ... finally:
            ...     await db.close_cursor(conn, cur)

        Warning:
            使用完毕后必须调用close_cursor()释放资源,否则会导致连接泄漏

        Note:
            - 推荐使用fetchone/fetchall等高级方法
            - 仅在需要细粒度控制时使用此方法
        """
        if self.pool is None:
            await self.init_pool()

        assert self.pool is not None  # Type guard: 连接池已初始化
        conn = await self.pool.acquire()
        cur = await conn.cursor(cursorclass=self.cursorclass)
        return conn, cur

    async def close_cursor(self, conn: aiomysql.Connection, cur: aiomysql.Cursor) -> None:
        """关闭游标并释放连接回连接池.

        Args:
            conn: 数据库连接对象
            cur: 游标对象

        Example:
            >>> conn, cur = await db.get_cursor()
            >>> # ... 执行操作 ...
            >>> await db.close_cursor(conn, cur)

        Note:
            - 非autocommit模式下会自动提交事务
            - 确保每次get_cursor()后都调用此方法
        """
        try:
            if not self.autocommit:
                await conn.commit()
            await cur.close()
        finally:
            if self.pool is not None:
                self.pool.release(conn)

    async def fetchone(self, query: str, *parameters, **kwparameters) -> dict[str, Any] | None:
        """查询单条记录,返回字典格式结果.

        符合DB-API 2.0规范的fetchone方法,查询结果集的第一条记录。

        Args:
            query: SELECT查询语句,支持占位符(%s)
            *parameters: 位置参数,用于替换占位符
            **kwparameters: 命名参数,用于替换占位符

        Returns:
            dict[str, Any] | None: 查询结果字典（使用DictCursor时）,
                                   没有记录时返回None

        Raises:
            aiomysql.Error: SQL执行错误时抛出
            pymysql.err.ProgrammingError: SQL语法错误时抛出

        Example:
            >>> # 位置参数
            >>> user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
            >>> if user:
            ...     print(f'用户名: {user["username"]}')
            >>>
            >>> # 命名参数
            >>> user = await db.fetchone('SELECT * FROM users WHERE id = %(user_id)s', user_id=1)

        Note:
            - 连接失效时会自动重连并重试一次
            - 使用DictCursor返回字典,可通过字段名访问
            - 对应MySQL的SELECT ... LIMIT 1
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
        """查询所有记录,返回字典列表.

        符合DB-API 2.0规范的fetchall方法,返回查询结果集的所有记录。

        Args:
            query: SELECT查询语句,支持占位符(%s)
            *parameters: 位置参数,用于替换占位符
            **kwparameters: 命名参数,用于替换占位符

        Returns:
            list[dict[str, Any]]: 查询结果列表,每条记录为字典格式,
                                  无记录时返回空列表[]

        Raises:
            aiomysql.Error: SQL执行错误时抛出
            pymysql.err.ProgrammingError: SQL语法错误时抛出

        Example:
            >>> # 查询所有记录
            >>> users = await db.fetchall('SELECT * FROM users')
            >>> for user in users:
            ...     print(f'{user["id"]}: {user["username"]}')
            >>>
            >>> # 带条件查询
            >>> active_users = await db.fetchall('SELECT * FROM users WHERE status = %s', 'active')
            >>> print(f'活跃用户数: {len(active_users)}')

        Warning:
            - 查询大量数据时可能导致内存溢出
            - 建议大数据量使用fetchmany()或iterate()

        Note:
            - 连接失效时会自动重连并重试一次
            - 结果全部加载到内存,适合小数据量
            - 对于大数据量,推荐使用iterate()方法
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
        """查询指定数量的记录,返回字典列表.

        符合DB-API 2.0规范的fetchmany方法,返回指定数量的记录。

        Args:
            query: SELECT查询语句,支持占位符(%s)
            size: 要获取的记录数量
            *parameters: 位置参数,用于替换占位符
            **kwparameters: 命名参数,用于替换占位符

        Returns:
            list[dict[str, Any]]: 查询结果列表,最多size条记录,
                                  记录不足size条时返回实际数量

        Raises:
            aiomysql.Error: SQL执行错误时抛出
            ValueError: size参数无效时抛出

        Example:
            >>> # 获取前10条记录
            >>> users = await db.fetchmany('SELECT * FROM users', 10)
            >>> print(f'获取了 {len(users)} 条记录')
            >>>
            >>> # 分页查询
            >>> page_size = 20
            >>> offset = 0
            >>> users = await db.fetchmany('SELECT * FROM users LIMIT %s OFFSET %s', page_size, page_size, offset)

        Note:
            - 连接失效时会自动重连并重试一次
            - 适合实现分页功能
            - 对比iterate(),此方法一次性返回size条记录
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

    # 异步上下文管理器支持
    async def __aenter__(self) -> AioMySQLPool:
        """异步上下文管理器入口 - 自动初始化连接池.

        Returns:
            AioMySQLPool: 当前连接池实例

        Example:
            >>> async with create_async_mysql_pool('default') as db:
            ...     users = await db.fetchall('SELECT * FROM users')

        Note:
            - 自动调用init_pool()初始化连接池
            - 退出时自动调用close()释放资源
        """
        await self.init_pool()
        mylog.debug('进入异步上下文管理器')
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口 - 自动关闭连接池.

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息

        Note:
            - 无论是否发生异常都会关闭连接池
            - 异常会继续向上传播
        """
        if exc_type is not None:
            mylog.error(f'上下文中发生异常: {exc_type.__name__}: {exc_val}')
        await self.close()
        mylog.debug('退出异步上下文管理器')

    # 事务支持
    async def begin(self) -> aiomysql.Connection:
        """开始事务,返回事务连接对象.

        获取一个连接并开始事务,用于执行需要原子性的多个操作。

        Returns:
            aiomysql.Connection: 事务连接对象,需要手动提交或回滚

        Raises:
            aiomysql.Error: 开始事务失败时抛出

        Example:
            >>> async with create_async_mysql_pool('default') as db:
            ...     conn = await db.begin()
            ...     try:
            ...         cur = await conn.cursor()
            ...         await cur.execute('INSERT INTO accounts(name, balance) VALUES (%s, %s)', ('Alice', 1000))
            ...         await cur.execute('UPDATE accounts SET balance = balance - 100 WHERE name = %s', 'Alice')
            ...         await db.commit(conn)
            ...         print('事务提交成功')
            ...     except Exception as e:
            ...         await db.rollback(conn)
            ...         print(f'事务回滚: {e}')

        Warning:
            - 必须手动调用commit()或rollback()
            - 忘记提交/回滚会导致连接无法释放

        Note:
            - 事务内的所有操作要么全部成功,要么全部回滚
            - 适用于转账、批量更新等需要原子性的场景
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
            conn: begin()返回的事务连接对象

        Raises:
            aiomysql.Error: 提交失败时抛出

        Example:
            >>> conn = await db.begin()
            >>> # ... 执行多个操作 ...
            >>> await db.commit(conn)

        Note:
            - 提交后连接会自动释放回连接池
            - 提交失败会抛出异常,连接不会被释放
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
            conn: begin()返回的事务连接对象

        Raises:
            aiomysql.Error: 回滚失败时抛出

        Example:
            >>> conn = await db.begin()
            >>> try:
            ...     # ... 执行操作 ...
            ...     await db.commit(conn)
            ... except Exception:
            ...     await db.rollback(conn)  # 出错时回滚

        Note:
            - 回滚后连接会自动释放回连接池
            - 回滚会撤销事务中的所有操作
        """
        try:
            await conn.rollback()
            mylog.debug('事务已回滚')
        finally:
            if self.pool is not None:
                self.pool.release(conn)

    # 异步迭代器支持
    async def iterate(
        self,
        query: str,
        *parameters,
        batch_size: int = 1000,
        **kwparameters,
    ) -> AsyncIterator[dict[str, Any]]:
        """迭代查询结果,适用于处理大量数据.

        使用异步迭代器逐批获取查询结果,避免一次性加载所有数据导致内存溢出。

        Args:
            query: SELECT查询语句
            *parameters: 位置参数
            batch_size: 每批获取的记录数量,默认1000
            **kwparameters: 命名参数

        Yields:
            dict[str, Any]: 每条查询结果记录

        Raises:
            aiomysql.Error: SQL执行错误时抛出

        Example:
            >>> async with create_async_mysql_pool('default') as db:
            ...     total = 0
            ...     async for row in db.iterate('SELECT * FROM large_table', batch_size=500):
            ...         # 逐行处理,不会一次性加载所有数据到内存
            ...         process(row)
            ...         total += 1
            ...     print(f'共处理 {total} 条记录')
            >>>
            >>> # 带条件的迭代
            >>> async for user in db.iterate('SELECT * FROM users WHERE status = %s', 'active'):
            ...     send_email(user['email'])

        Warning:
            - 迭代过程中会一直占用一个数据库连接
            - 建议尽快处理每条记录,避免长时间占用连接

        Note:
            - 连接失效时会自动重连并重试
            - 批量大小(batch_size)影响性能和内存占用
            - 适合处理百万级以上的大数据量
            - 对比fetchall(),此方法按需加载,内存友好
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


# 工厂函数 - 提供更简便的数据库操作方式
def create_async_mysql_pool(db_key: str = 'default', **kwargs: Any) -> AioMySQLPool:
    """创建异步MySQL连接池实例的工厂函数.

    根据配置键从DB_CFG中读取配置并创建连接池实例。
    这是推荐的创建连接池的方式,比直接实例化AioMySQLPool更简便。

    Args:
        db_key: 数据库配置键名,对应cfg.py中DB_CFG的配置项,默认'default'
        **kwargs: 额外的连接池参数,会覆盖配置中的同名参数
            - minsize: 最小连接数
            - maxsize: 最大连接数
            - pool_recycle: 连接回收时间
            - 等等...

    Returns:
        AioMySQLPool: 异步MySQL连接池实例(单例)

    Raises:
        ValueError: 当db_key不是字符串或配置不存在时抛出
        KeyError: 当配置键不存在时抛出

    Example:
        基本使用::

            >>> # 1. 使用默认配置
            >>> db = create_async_mysql_pool()
            >>> await db.init_pool()
            >>>
            >>> # 2. 使用指定配置
            >>> db = create_async_mysql_pool('production')
            >>>
            >>> # 3. 使用上下文管理器（推荐）
            >>> async with create_async_mysql_pool('default') as db:
            ...     users = await db.fetchall('SELECT * FROM users')
            >>>
            >>> # 4. 自定义连接池参数
            >>> db = create_async_mysql_pool('default', minsize=5, maxsize=20)

        完整示例::

            >>> import asyncio
            >>> from xtdbase.aiomysqlpool import create_async_mysql_pool
            >>>
            >>> async def main():
            ...     async with create_async_mysql_pool('default') as db:
            ...         # 查询操作
            ...         user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
            ...         users = await db.fetchall('SELECT * FROM users')
            ...
            ...         # 插入操作
            ...         new_id = await db.execute(
            ...             'INSERT INTO users(name, email) VALUES (%s, %s)',
            ...             'Alice', 'alice@example.com'
            ...         )
            ...
            ...         # 事务操作
            ...         conn = await db.begin()
            ...         try:
            ...             cur = await conn.cursor()
            ...             await cur.execute('UPDATE accounts SET balance = balance - 100 WHERE id = 1')
            ...             await cur.execute('UPDATE accounts SET balance = balance + 100 WHERE id = 2')
            ...             await db.commit(conn)
            ...         except Exception:
            ...             await db.rollback(conn)
            >>>
            >>> asyncio.run(main())

    Note:
        - 使用单例模式,相同db_key返回同一实例
        - 配置来自cfg.py的DB_CFG枚举
        - kwargs参数会覆盖配置中的同名参数
        - 推荐使用上下文管理器自动管理资源
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
    return AioMySQLPool(**cfg, **kwargs)
