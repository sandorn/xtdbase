#!/usr/bin/env python3
"""
==============================================================
Description  : MySQL同步连接模块 - 提供符合DB-API 2.0规范的同步数据库操作
Author       : sandorn sandorn@live.cn
LastEditTime : 2025-10-23
FilePath     : /xtdbase/mysql.py
Github       : https://github.com/sandorn/xtdbase

本模块提供以下核心功能:
    - MySQL: 同步MySQL连接类,遵循Python DB-API 2.0规范
    - create_mysql_connection: 快捷工厂函数,简化连接创建过程

主要特性:
    - 标准化接口: 方法命名遵循Python DB-API 2.0规范
    - 完整的CRUD操作: fetchone/fetchall/fetchmany/execute等标准接口
    - 上下文管理器: 使用with语句自动处理资源
    - 事务支持: begin/commit/rollback确保数据一致性和原子性
    - 统一的错误处理: 完善的异常捕获和日志记录机制
    - 完整的类型注解: 支持Python 3.10+现代类型系统

使用示例:
    >>> from xtdbase.mysql import create_mysql_connection
    >>>
    >>> # 使用上下文管理器（推荐）
    >>> with create_mysql_connection('default') as db:
    ...     # 查询单条记录
    ...     user = db.fetchone('SELECT * FROM users WHERE id = %s', (1,))
    ...     # 查询多条记录
    ...     users = db.fetchall('SELECT * FROM users LIMIT 10')
    ...     # 执行插入/更新
    ...     affected = db.execute('INSERT INTO users(name) VALUES (%s)', ('Alice',))

注意事项:
    - 推荐使用上下文管理器确保资源正确释放
    - 参数必须使用元组格式，即使只有一个参数也要写成 (value,)
    - 事务操作需要手动管理commit和rollback
==============================================================
"""

from __future__ import annotations

from typing import Any

import pymysql
import pymysql.cursors
from xtlog import mylog

from .cfg import DB_CFG

pymysql.install_as_MySQLdb()


class MySQL:
    """同步MySQL连接类,遵循Python DB-API 2.0规范.

    Attributes:
        conn: pymysql连接实例
        cfg: 连接配置字典
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
        charset: str = 'utf8mb4',
        autocommit: bool = True,
        cursorclass: type[pymysql.cursors.Cursor] = pymysql.cursors.DictCursor,
        **kwargs: Any,
    ):
        """初始化连接配置.

        Args:
            host: 数据库主机地址
            port: 数据库端口号
            user: 数据库用户名
            password: 数据库密码
            db: 数据库名称
            charset: 数据库字符集,默认'utf8mb4'
            autocommit: 是否自动提交,默认True
            cursorclass: 游标类型,默认DictCursor
            **kwargs: 其他pymysql.connect参数
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

        # 构建连接配置字典
        self.cfg = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'db': db,
            'charset': charset,
            'autocommit': autocommit,
            'cursorclass': cursorclass,
        }
        self.cfg.update(kwargs)

        # 创建连接
        try:
            self.conn = pymysql.connect(**self.cfg)
            mylog.info(f'✅ 数据库连接成功: {host}:{port}/{db}')
        except Exception as e:
            mylog.error(f'❌ 数据库连接失败: {e}')
            raise

    def __enter__(self) -> MySQL:
        """进入上下文,返回连接实例."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """退出上下文,自动关闭连接."""
        if exc_type is not None:
            mylog.error(f'上下文中发生异常: {exc_type.__name__}: {exc_val}')
        self.close()
        return False

    def __del__(self) -> None:
        """对象销毁时自动关闭连接."""
        self.close()

    def close(self) -> None:
        """关闭数据库连接."""
        if hasattr(self, 'conn') and self.conn and self.conn.open:
            try:
                self.conn.close()
                mylog.info('✅ 数据库连接已关闭')
            except Exception as e:
                mylog.error(f'❌ 关闭连接失败: {e}')

    def execute(self, query: str, args: tuple | None = None) -> int:
        """执行INSERT/UPDATE/DELETE语句(DB-API 2.0).

        Args:
            query: SQL语句
            args: 参数元组

        Returns:
            int: INSERT返回lastrowid,UPDATE/DELETE返回受影响行数

        Note:
            - autocommit=True时,每次执行后自动提交
            - autocommit=False时,需手动调用commit()或rollback()
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, args)
                # 只在 autocommit 模式下自动提交
                # 否则等待显式调用 commit()
                return cur.lastrowid if 'INSERT' in query.upper() else cur.rowcount
        except Exception as e:
            mylog.error(f'❌ SQL执行失败: {e}')
            raise

    def fetchone(self, query: str, args: tuple | None = None) -> dict[str, Any] | None:
        """查询单条记录(DB-API 2.0).

        Args:
            query: SELECT语句
            args: 参数元组

        Returns:
            dict[str, Any] | None: 查询结果字典,无记录返回None
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, args)
                result = cur.fetchone()
                return dict(result) if result else None  # type: ignore[arg-type]
        except Exception as e:
            mylog.error(f'❌ 查询失败: {e}')
            raise

    def fetchall(self, query: str, args: tuple | None = None) -> list[dict[str, Any]]:
        """查询所有记录(DB-API 2.0).

        Args:
            query: SELECT语句
            args: 参数元组

        Returns:
            list[dict[str, Any]]: 结果列表,无记录返回空列表
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, args)
                results = cur.fetchall()
                return [dict(row) for row in results] if results else []  # type: ignore[arg-type]
        except Exception as e:
            mylog.error(f'❌ 查询失败: {e}')
            raise

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

        try:
            with self.conn.cursor() as cur:
                cur.execute(query, args)
                results = cur.fetchmany(size)
                return [dict(row) for row in results] if results else []  # type: ignore[arg-type]
        except Exception as e:
            mylog.error(f'❌ 查询失败: {e}')
            raise

    def begin(self) -> None:
        """开始事务.必须手动调用commit()或rollback()."""
        try:
            self.conn.begin()
            mylog.debug('事务已开始')
        except Exception as e:
            mylog.error(f'❌ 开始事务失败: {e}')
            raise

    def commit(self) -> None:
        """提交事务."""
        try:
            self.conn.commit()
            mylog.debug('事务已提交')
        except Exception as e:
            mylog.error(f'❌ 提交事务失败: {e}')
            raise

    def rollback(self) -> None:
        """回滚事务."""
        try:
            self.conn.rollback()
            mylog.debug('事务已回滚')
        except Exception as e:
            mylog.error(f'❌ 回滚事务失败: {e}')
            raise

    def ping(self) -> bool:
        """测试连接是否可用.

        Returns:
            bool: 连接正常返回True,否则返回False
        """
        try:
            self.conn.ping()
            return True
        except Exception as e:
            mylog.error(f'❌ 连接ping失败: {e}')
            return False


def create_mysql_connection(db_key: str = 'default', **kwargs: Any) -> MySQL:
    """创建MySQL连接工厂函数(推荐使用).

    从cfg.py的DB_CFG读取配置并创建连接实例.

    Args:
        db_key: 配置键名,默认'default'
        **kwargs: 额外参数,会覆盖配置中的同名参数

    Returns:
        MySQL: 连接实例

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

    # 获取配置并创建连接
    cfg = DB_CFG[db_key].value[0].copy()
    cfg.pop('type', None)  # 移除type字段(如果存在)

    mylog.info(f'🔨 正在创建数据库连接,配置键: {db_key}')
    return MySQL(**cfg, **kwargs)
