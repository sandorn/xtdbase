#!/usr/bin/env python
"""
==============================================================
Description  : untilsql SQL 工具函数使用示例
Author       : sandorn sandorn@live.cn
Date         : 2025-10-23
FilePath     : /examples/example_untilsql_usage.py
Github       : https://github.com/sandorn/xtdbase

本示例展示如何使用 untilsql 模块的 SQL 构建工具:
    1. make_insert_sql - 构建 INSERT 语句
    2. make_update_sql - 构建 UPDATE 语句
    3. 防止 SQL 注入
    4. 处理各种数据类型
    5. 实际应用场景
==============================================================
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from xtdbase.untilsql import make_insert_sql, make_update_sql


def example_1_basic_insert():
    """示例 1: 基本 INSERT 语句构建"""
    print('\n' + '=' * 60)
    print('示例 1: 基本 INSERT 语句构建')
    print('=' * 60)

    # 简单数据插入
    data = {'name': 'Alice', 'email': 'alice@example.com', 'age': 25}

    sql, params = make_insert_sql(data, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print(f'\n参数:\n  {params}')
    print('\n✅ 生成的是参数化查询，安全防止 SQL 注入')


def example_2_various_data_types():
    """示例 2: 处理各种数据类型"""
    print('\n' + '=' * 60)
    print('示例 2: 处理各种数据类型')
    print('=' * 60)

    # 包含多种数据类型的数据
    data = {
        'username': 'bob',  # 字符串
        'age': 30,  # 整数
        'score': 95.5,  # 浮点数
        'is_active': True,  # 布尔值
        'created_at': datetime.now(),  # 日期时间
        'tags': ['python', 'database'],  # 列表(会转为 JSON)
        'profile': {'city': 'Beijing', 'country': 'China'},  # 字典(会转为 JSON)
        'status': None,  # None 值
    }

    sql, params = make_insert_sql(data, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print('\n参数类型:')
    for i, param in enumerate(params):
        print(f'  - 参数 {i + 1}: {type(param).__name__} = {param}')

    print('\n💡 自动处理:')
    print('  - 列表/字典 → JSON 字符串')
    print('  - datetime → 格式化字符串')
    print('  - Enum → 枚举值')
    print('  - None → NULL')


def example_3_handle_enums():
    """示例 3: 处理枚举类型"""
    print('\n' + '=' * 60)
    print('示例 3: 处理枚举类型')
    print('=' * 60)

    # 定义枚举
    class UserRole(Enum):
        ADMIN = 'admin'
        USER = 'user'
        GUEST = 'guest'

    class Status(Enum):
        ACTIVE = 1
        INACTIVE = 0

    # 包含枚举的数据
    data = {'username': 'charlie', 'role': UserRole.ADMIN, 'status': Status.ACTIVE}

    sql, params = make_insert_sql(data, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print(f'\n参数:\n  {params}')
    print('\n✅ 枚举类型自动转换为其值')


def example_4_basic_update():
    """示例 4: 基本 UPDATE 语句构建"""
    print('\n' + '=' * 60)
    print('示例 4: 基本 UPDATE 语句构建')
    print('=' * 60)

    # 更新数据
    data = {'email': 'newemail@example.com', 'age': 26, 'updated_at': datetime.now()}

    # WHERE 条件
    where = {'id': 1}

    sql, params = make_update_sql(data, where, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print(f'\n参数:\n  {params}')
    print('\n💡 WHERE 条件参数会追加到 SET 参数之后')


def example_5_complex_where_conditions():
    """示例 5: 复杂 WHERE 条件"""
    print('\n' + '=' * 60)
    print('示例 5: 复杂 WHERE 条件')
    print('=' * 60)

    # 更新数据
    data = {'status': 'verified'}

    # 多个 WHERE 条件(AND 关系)
    where = {
        'age__gte': 18,  # age >= 18
        'country': 'China',
        'is_active': True,
    }

    sql, params = make_update_sql(data, where, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print(f'\n参数:\n  {params}')
    print('\n⚠️  注意: WHERE 条件使用 AND 连接')


def example_6_prevent_sql_injection():
    """示例 6: SQL 注入防护"""
    print('\n' + '=' * 60)
    print('示例 6: SQL 注入防护')
    print('=' * 60)

    # 模拟恶意输入
    malicious_input = {'username': "'; DROP TABLE users; --", 'email': "admin' OR '1'='1"}

    sql, params = make_insert_sql(malicious_input, 'users')

    print('\n恶意输入:')
    print(f'  username: {malicious_input["username"]}')
    print(f'  email: {malicious_input["email"]}')

    print('\n✅ 生成的安全 SQL:')
    print(f'  {sql}')
    print('\n参数(被安全转义):')
    print(f'  {params}')

    print('\n💡 参数化查询确保恶意 SQL 被当作普通字符串处理')


def example_7_null_values():
    """示例 7: 处理 NULL 值"""
    print('\n' + '=' * 60)
    print('示例 7: 处理 NULL 值')
    print('=' * 60)

    # 包含 None 值
    data = {
        'username': 'user1',
        'email': 'user1@example.com',
        'phone': None,  # 未提供电话
        'bio': None,  # 未提供简介
    }

    sql, params = make_insert_sql(data, 'users')

    print(f'\nSQL 语句:\n  {sql}')
    print(f'\n参数:\n  {params}')
    print('\n✅ None 值会被正确处理为 NULL')


def example_8_batch_operations():
    """示例 8: 批量操作"""
    print('\n' + '=' * 60)
    print('示例 8: 批量操作')
    print('=' * 60)

    # 批量插入数据
    users_data = [{'name': 'User1', 'email': 'user1@example.com', 'age': 20}, {'name': 'User2', 'email': 'user2@example.com', 'age': 25}, {'name': 'User3', 'email': 'user3@example.com', 'age': 30}]

    print(f'\n生成 {len(users_data)} 条 INSERT 语句:\n')

    for i, user_data in enumerate(users_data, 1):
        sql, params = make_insert_sql(user_data, 'users')
        print(f'{i}. SQL: {sql}')
        print(f'   参数: {params}\n')


def example_9_practical_use_with_db():
    """示例 9: 与数据库配合使用"""
    print('\n' + '=' * 60)
    print('示例 9: 与数据库配合使用')
    print('=' * 60)

    print("""
    💡 实际使用示例:

    1. 与 MySQL 单连接配合:
       ```python
       from xtdbase import create_mysql_connection
       from xtdbase.untilsql import make_insert_sql

       db = create_mysql_connection('default')

       # 插入数据
       data = {'name': 'Alice', 'email': 'alice@example.com'}
       sql, params = make_insert_sql(data, 'users')
       affected = db.execute(sql, params)

       db.close()
       ```

    2. 与异步连接池配合:
       ```python
       from xtdbase import create_mysql_pool
       from xtdbase.untilsql import make_insert_sql
       import asyncio

       async def insert_user():
           async with create_mysql_pool('default') as db:
               data = {'name': 'Bob', 'age': 30}
               sql, params = make_insert_sql(data, 'users')
               await db.execute(sql, *params)

       asyncio.run(insert_user())
       ```

    3. 与同步连接池配合:
       ```python
       from xtdbase import create_sync_mysql_pool
       from xtdbase.untilsql import make_update_sql

       db = create_sync_mysql_pool('default')

       # 更新数据
       data = {'email': 'new@example.com'}
       where = {'id': 1}
       sql, params = make_update_sql(data, where, 'users')
       affected = db.execute(sql, params)

       db.close()
       ```

    4. 批量操作:
       ```python
       from xtdbase import create_mysql_pool
       from xtdbase.untilsql import make_insert_sql

       async def batch_insert(users):
           async with create_mysql_pool('default') as db:
               conn = await db.begin()
               try:
                   cursor = await conn.cursor()
                   for user in users:
                       sql, params = make_insert_sql(user, 'users')
                       await cursor.execute(sql, params)
                   await db.commit(conn)
               except Exception:
                   await db.rollback(conn)
                   raise
       ```
    """)


def example_10_best_practices():
    """示例 10: 最佳实践"""
    print('\n' + '=' * 60)
    print('示例 10: SQL 构建最佳实践')
    print('=' * 60)

    print("""
    ✅ 最佳实践建议:

    1. 始终使用参数化查询:
       ✓ 使用 make_insert_sql/make_update_sql
       ✗ 不要使用字符串拼接构建 SQL

    2. 数据验证:
       ✓ 在构建 SQL 前验证数据类型
       ✓ 检查必填字段
       ✓ 验证数据长度和格式

    3. 错误处理:
       ✓ 捕获 SQL 执行异常
       ✓ 记录错误日志
       ✓ 提供友好的错误提示

    4. 性能优化:
       ✓ 批量操作使用事务
       ✓ 避免在循环中执行 SQL
       ✓ 合理使用索引

    5. 字段命名:
       ✓ 使用有意义的字段名
       ✓ 遵循数据库命名规范
       ✓ 避免使用保留字

    6. 复杂查询:
       ⚠️  make_insert_sql/make_update_sql 适合简单场景
       ⚠️  复杂查询建议手写 SQL + 参数化

    7. 数据类型:
       ✓ datetime → 使用 datetime 对象
       ✓ JSON → 使用 dict/list(自动转换)
       ✓ 枚举 → 使用 Enum 类型
       ✓ NULL → 使用 None

    8. 安全建议:
       ✓ 永远不要信任用户输入
       ✓ 使用参数化查询防止 SQL 注入
       ✓ 限制数据库用户权限
       ✓ 定期审计 SQL 日志
    """)


def main():
    """主函数：运行所有示例"""
    print('\n' + '=' * 60)
    print('untilsql SQL 工具函数使用示例')
    print('=' * 60)

    # 运行所有示例
    example_1_basic_insert()
    example_2_various_data_types()
    example_3_handle_enums()
    example_4_basic_update()
    example_5_complex_where_conditions()
    example_6_prevent_sql_injection()
    example_7_null_values()
    example_8_batch_operations()
    example_9_practical_use_with_db()
    example_10_best_practices()

    print('\n' + '=' * 60)
    print('✅ 所有示例运行完成！')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
