# !/usr/bin/env python3
"""
==============================================================
Description  : MySQL数据库操作模块 - 提供同步MySQL数据库连接和操作功能
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2022-12-22 17:35:56
LastEditTime : 2024-09-10 16:30:00
FilePath     : /CODE/xjlib/xt_database/mysql.py
Github       : https://github.com/sandorn/home

本模块提供以下核心功能:
- DbEngine类:MySQL数据库连接引擎,支持多种数据库驱动
- create_mysql_engine:创建MySQL连接实例的快捷函数
- 支持SQL执行、查询、插入、更新等基本操作
- 支持上下文管理器(with语句)使用方式
- 支持字典类型游标结果返回

主要特性:
- 支持两种初始化方式：直接参数方式和配置方式
- 配置从DB_CFG统一管理,支持多数据库配置切换
- 支持pymysql和MySQLdb两种驱动
- 自动提交模式,减少事务管理复杂性
- 完善的异常处理和日志记录
- 类型注解支持,提高代码可读性和IDE提示
==============================================================
"""

from __future__ import annotations

from typing import Any

import pymysql
from pymysql.cursors import DictCursor
from xtlog import mylog as logger
from xtwraps.log import get_function_location, log_wraps

from .cfg import DB_CFG
from .untilsql import make_insert_sql, make_update_sql

pymysql.install_as_MySQLdb()  # 让代码可像使用 mysqlclient 一样调用


class DbEngine:
    """MySQL数据库连接引擎类,提供数据库连接和基本操作功能

    该类提供了同步MySQL数据库连接和操作的能力,主要适用于需要在同步代码中
    执行数据库操作的场景。支持多种数据库驱动和上下文管理器模式。

    Args:
        host: 数据库主机地址（直接参数方式）
        port: 数据库端口号（直接参数方式）
        user: 数据库用户名（直接参数方式）
        password: 数据库密码（直接参数方式）
        db: 数据库名称（直接参数方式）
        charset: 数据库字符集,默认为'utf8mb4'
        autocommit: 是否自动提交事务,默认为True
        tablename: 默认操作的表名,可选

    Attributes:
        conn: 数据库连接对象
        cur: 数据库游标对象
        DictCursor: 字典类型游标类
        tablename: 默认操作的表名
        cfg: 数据库连接配置字典
        charset: 数据库字符集

    Raises:
        ValueError: 当缺少必要的数据库连接参数时抛出
        Exception: 当数据库连接失败时抛出

    Example:
        >>> # 使用直接参数方式
        >>> db = DbEngine(
        >>>     host='localhost',
        >>>     port=3306,
        >>>     user='sandorn',
        >>>     password='123456',
        >>>     db='test_db'
        >>> )
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
        """初始化DbEngine实例

        Args:
            host: 数据库主机地址（直接参数方式）
            port: 数据库端口号（直接参数方式）
            user: 数据库用户名（直接参数方式）
            password: 数据库密码（直接参数方式）
            db: 数据库名称（直接参数方式）
            charset: 数据库字符集,默认为'utf8mb4'
            autocommit: 是否自动提交事务,默认为True
            tablename: 默认操作的表名,可选
            **kwargs: 其他数据库连接参数,会被合并到cfg中

        Notes:
            1. 连接成功后自动创建游标对象
            2. 支持pymysql和MySQLdb两种驱动
            3. 所有连接参数都是必需的
        """

        self.tablename: str | None = tablename
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

        # 直接构建配置字典
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

        # 连接数据库（让pymysql自己抛出异常）
        self.conn = pymysql.connect(**self.cfg)
        # 创建字典游标对象，便于以字典形式访问查询结果
        self.cur = self.conn.cursor(DictCursor)

    def __enter__(self) -> DbEngine:
        """支持上下文管理器的入口方法"""
        logger.info(f'进入数据库上下文: {self}')
        return self

    def __exit__(self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: Any) -> bool:
        """支持上下文管理器的退出方法,自动关闭连接

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        logger.info(f'退出数据库上下文: {self}')

        # 如果发生异常,记录异常信息
        if exc_tb is not None:
            logger.error(f'数据库操作异常: exc_type={exc_type}, exc_val={exc_val}')
            return False  # 不抑制异常

        return True

    def __del__(self) -> None:
        """对象销毁时自动关闭连接"""
        self.close()

    def __repr__(self) -> str:
        """返回对象的描述信息"""
        return f'MySQL数据库连接引擎,当前配置: {self.cfg}'

    __str__ = __repr__

    def close(self) -> None:
        """关闭数据库连接和游标"""
        if hasattr(self, 'cur') and self.cur:
            self.cur.close()
        logger.info('游标已关闭')

        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        logger.info('数据库连接已关闭')

    @log_wraps
    def execute(self, sql: str, args: list[Any] | None = None) -> int:
        """执行SQL语句

        Args:
            sql: SQL语句
            args: SQL参数列表,默认为None

        Returns:
            int: 受影响的记录数量
        """
        self.cur.execute(sql, args)
        return self.cur.rowcount

    @log_wraps
    def query(self, sql: str, args: list[Any] | None = None, return_dict: bool = True) -> list[dict[str, Any]] | list[tuple[Any]]:
        """执行查询操作

        Args:
            sql: SQL查询语句
            args: SQL参数列表,默认为None
            return_dict: 是否返回字典格式,默认为True

        Returns:
            list[dict[str, Any]] | list[tuple[Any]]: 查询结果列表
                - 当 return_dict=True 时返回字典列表
                - 当 return_dict=False 时返回元组列表
        """
        self.cur.execute(sql, args)
        results = self.cur.fetchall()
        # DictCursor已经返回字典格式，直接转换为列表返回
        return list(results) if results else []

    @log_wraps
    def has_table(self, table_name: str) -> bool:
        """判断数据库是否包含指定表

        Args:
            table_name: 表名

        Returns:
            bool: 是否存在该表
        """
        self.cur.execute('show tables')
        tablerows = self.cur.fetchall()
        # 遍历字典列表，获取每个表名（字典的第一个值）
        return any(next(iter(row.values())) == table_name for row in tablerows if row)

    @log_wraps
    def get_version(self) -> str | None:
        """获取数据库版本号

        Returns:
            Optional[str]: 数据库版本号,如果获取失败返回None
        """
        self.cur.execute('SELECT VERSION()')
        result = self.cur.fetchone()
        # 从字典结果中获取版本号
        return next(iter(result.values())) if result else None

    def get_all(self, table_name: str, args: list[Any] | None = None) -> list[dict[str, Any]]:
        """获取表中所有记录

        Args:
            table_name: 表名
            args: SQL参数列表,默认为None

        Returns:
            list[dict[str, Any]]: 查询结果列表（字典格式）
        """
        sql = f'SELECT * FROM `{table_name}`'  # noqa
        results = self.query(sql, args)
        return results if isinstance(results, list) else []

    def _handle_error(self, prefix: str, error: Exception, sql: str) -> bool:
        """错误处理方法

        Args:
            prefix: 错误信息前缀
            error: 异常对象
            sql: 相关的SQL语句

        Returns:
            bool: 始终返回False表示操作失败
        """
        msg = get_function_location(self._handle_error)
        # 记录错误日志,SQL语句过长时截断
        safe_sql = (sql[:200] + '...') if len(sql) > 200 else sql
        logger.error(f'{msg} | {prefix} | {error}\nSQL: {safe_sql}')
        return False

    def insert_many(self, data_list: list[dict[str, Any]] | tuple[dict[str, Any], ...], table_name: str) -> int:
        """批量插入数据

        Args:
            data_list: 数据列表,每个元素为字典
            table_name: 表名

        Returns:
            int: 受影响的总记录数量

        Raises:
            TypeError: 当data_list不是列表或元组时
            ValueError: 当data_list为空时
        """
        if not isinstance(data_list, (list, tuple)):
            raise TypeError('data_list must be list or tuple type')

        if not data_list:
            logger.warning('数据列表为空, 没有需要插入的数据')
            return 0

        row_count = 0
        for item in data_list:
            row_count += self.insert(item, table_name)
        return row_count

    @log_wraps
    def insert(self, data: dict[str, Any], table_name: str) -> int:
        """插入单条数据

        Args:
            data: 数据字典
            table_name: 表名

        Returns:
            int: 受影响的记录数量

        Raises:
            ValueError: 当data不是字典或为空时
        """
        if not isinstance(data, dict):
            raise ValueError('data must be dict type')

        if not data:
            raise ValueError('data cannot be empty')

        sql_result = make_insert_sql(data, table_name)
        # 处理可能的元组返回值
        if isinstance(sql_result, tuple):
            sql, params = sql_result
            self.cur.execute(sql, params)
        else:
            self.cur.execute(sql_result)
        return self.cur.rowcount

    @log_wraps
    def update(self, new_data: dict[str, Any], condition: dict[str, Any], table_name: str) -> int:
        """更新数据

        Args:
            new_data: 新数据字典
            condition: 条件字典
            table_name: 表名

        Returns:
            int: 受影响的记录数量

        Raises:
            ValueError: 当new_data不是字典或为空时
        """
        if not isinstance(new_data, dict):
            raise ValueError('new_data must be dict type')

        if not new_data:
            raise ValueError('new_data cannot be empty')

        sql_result = make_update_sql(new_data, condition, table_name)
        # 处理可能的元组返回值
        if isinstance(sql_result, tuple):
            sql, params = sql_result
            self.cur.execute(sql, params)
        else:
            self.cur.execute(sql_result)
        return self.cur.rowcount

    @log_wraps
    def query_dict(self, sql: str) -> list[dict[str, Any]]:
        """执行查询并返回字典类型结果

        Args:
            sql: SQL查询语句

        Returns:
            list[dict[str, Any]]: 查询结果列表(字典形式)
        """
        self.cur.execute(sql)
        results = self.cur.fetchall()
        return list(results) if results else []


def create_mysql_engine(db_key: str = 'default', tablename: str | None = None, autocommit: bool = True, **kwargs) -> DbEngine:
    """快捷函数 - 提供更简便的数据库操作方式
    创建MySQL连接实例的快捷函数 - 使用配置方式初始化
    该函数根据提供的数据库配置键名(db_key),从DB_CFG配置中获取数据库连接参数,
    并使用这些参数初始化一个DbEngine实例。支持指定默认操作的表名、是否自动提交事务
    以及使用的数据库驱动类型。

    Args:
        db_key: 数据库配置键名,用于从DB_CFG中获取对应的数据库配置,默认为'default'
        tablename: 默认操作的表名,可选
        autocommit: 是否自动提交事务,默认为True

    Returns:
        DbEngine: MySQL连接实例,已完成连接初始化

    Raises:
        ValueError:
            - 当db_key参数不是字符串类型时抛出
            - 当DB_CFG中不存在指定的配置键时抛出

    Example:
        >>> # 使用配置方式（推荐）
        >>> db = create_mysql_engine()  # 使用默认配置
        >>> db = create_mysql_engine('test_db')  # 使用指定配置
        >>> db = create_mysql_engine('test_db', 'users', False)  # 指定配置、表名、事务设置
    """
    if not isinstance(db_key, str):
        raise ValueError(f'配置键非字符串类型: [{type(db_key).__name__}]')

    # 配置键存在性检查
    if not hasattr(DB_CFG, db_key):
        raise ValueError(f'配置 [{db_key}] 不存在 ')

    # 获取配置并创建连接池
    cfg = DB_CFG[db_key].value[0].copy()
    cfg.pop('type', None)  # 移除类型字段(如果存在)

    return DbEngine(**cfg, autocommit=autocommit, tablename=tablename, **kwargs)
