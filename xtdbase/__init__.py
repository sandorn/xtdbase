#!/usr/bin/env python
"""
==============================================================
xtdbase - 扩展数据库与数据处理工具库
==============================================================
Description  : 提供Excel操作、MySQL连接池、Redis客户端等统一接口
Author       : sandorn sandorn@live.cn
Date         : 2022-12-22 17:35:56
LastEditTime : 2025-10-23
Github       : https://github.com/sandorn/xtdbase

核心模块:
    Excel操作:
        - Excel: 统一的Excel读写类,支持openpyxl和pandas两种模式
        - ColumnMapping, SheetMapping, DataCollect: Excel数据映射模型

    MySQL操作:
        - MySQL: 符合DB-API 2.0的MySQL单连接类
        - MySQLPool: 异步MySQL连接池(推荐用于异步环境)
        - MySQLPoolSync: 同步调用的异步连接池(用于同步环境)
        - create_mysql_connection: MySQL单连接工厂函数
        - create_mysql_pool: 异步连接池工厂函数
        - create_sync_mysql_pool: 同步连接池工厂函数

    Redis操作:
        - RedisManager: Redis客户端封装类
        - create_redis_client: Redis客户端工厂函数

    工具模块:
        - make_insert_sql: 安全的INSERT语句构建
        - make_update_sql: 安全的UPDATE语句构建
        - DB_CFG: 数据库配置管理

使用示例:
    >>> # Excel操作
    >>> from xtdbase import Excel
    >>> with Excel('data.xlsx') as excel:
    ...     data = excel.read_all()

    >>> # 异步MySQL连接池
    >>> from xtdbase import create_mysql_pool
    >>> import asyncio
    >>> async def main():
    ...     async with create_mysql_pool('default') as db:
    ...         users = await db.fetchall('SELECT * FROM users')
    >>> asyncio.run(main())

    >>> # 同步MySQL连接池
    >>> from xtdbase import create_sync_mysql_pool
    >>> db = create_sync_mysql_pool('default')
    >>> users = db.fetchall('SELECT * FROM users')

    >>> # Redis操作
    >>> from xtdbase import create_redis_client
    >>> redis = create_redis_client('default')
    >>> redis.set('key', 'value')
==============================================================
"""

from __future__ import annotations

# 从 pyproject.toml 动态读取版本号
try:
    from importlib.metadata import version

    __version__ = version('xtdbase')
except Exception:
    __version__ = '0.1.0'  # 开发环境回退版本

# ==============================================
# Excel 操作模块
# ==============================================
from .excel import ColumnMapping, DataCollect, Excel, SheetMapping

__all__ = [
    # Excel
    'ColumnMapping',
    'DataCollect',
    'Excel',
    'SheetMapping',
]

# ==============================================
# MySQL 操作模块 (可选依赖)
# ==============================================
try:
    from .mysql import MySQL, create_mysql_connection

    __all__.extend(['MySQL', 'create_mysql_connection'])
except ImportError:
    pass

try:
    from .mysqlpool import MySQLPool, create_mysql_pool

    __all__.extend(['MySQLPool', 'create_mysql_pool'])
except ImportError:
    pass

try:
    from .syncmysqlpool import MySQLPoolSync, create_sync_mysql_pool

    __all__.extend(['MySQLPoolSync', 'create_sync_mysql_pool'])
except ImportError:
    pass

# ==============================================
# Redis 操作模块 (可选依赖)
# ==============================================
try:
    from .redis_client import RedisManager, create_redis_client

    __all__.extend(['RedisManager', 'create_redis_client'])
except ImportError:
    pass

# ==============================================
# SQL 工具函数 (可选依赖)
# ==============================================
try:
    from .untilsql import make_insert_sql, make_update_sql

    __all__.extend(['make_insert_sql', 'make_update_sql'])
except ImportError:
    pass

# ==============================================
# 配置模块 (可选依赖)
# ==============================================
try:
    from .cfg import DB_CFG

    __all__.extend(['DB_CFG'])
except ImportError:
    pass
