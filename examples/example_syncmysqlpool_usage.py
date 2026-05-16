# !/usr/bin/env python
"""
==============================================================
Description  : MySQLPoolSync 同步连接池使用示例
Author       : sandorn sandorn@live.cn
Date         : 2025-10-23
FilePath     : /examples/example_syncmysqlpool_usage.py
Github       : https://github.com/sandorn/xtdbase

本示例展示如何在同步环境中使用 MySQLPoolSync:
    1. 创建同步连接池
    2. 基本 CRUD 操作
    3. 事务管理
    4. 参数化查询
    5. 错误处理
    6. 连接池管理

注意: 本模块适用于无法使用 async/await 的同步代码环境
     如在异步环境,推荐使用 mysqlpool.py 中的 MySQLPool
==============================================================
"""

from __future__ import annotations

from xtlog import mylog

from xtdbase import create_sync_mysql_pool


def example_1_basic_query():
    """示例 1: 基本查询操作"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 1: 基本查询操作(同步模式)')
    mylog.info('=' * 60)

    try:
        # 创建同步连接池(自动使用 asyncio 事件循环)
        db = create_sync_mysql_pool('default')

        # 查询数据库列表
        databases = db.fetchall('SHOW DATABASES', ())
        mylog.info(f'\n查询到 {len(databases)} 个数据库')
        for db_info in databases[:5]:  # 只显示前5个
            mylog.info(f'  - {db_info}')

        # 查询当前数据库的表
        tables = db.fetchall('SHOW TABLES', ())
        mylog.info(f'\n当前数据库有 {len(tables)} 个表')
        for table in tables[:5]:
            mylog.info(f'  - {table}')

        # 关闭连接池
        db.close()
        mylog.info('\n✅ 基本查询完成')

    except Exception as e:
        mylog.info(f'❌ 查询失败: {e}')


def example_2_insert_data():
    """示例 2: 创建测试表并插入数据"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 2: 创建测试表并插入数据')
    mylog.info('=' * 60)

    try:
        db = create_sync_mysql_pool('default')

        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sync_test_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            age INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute(create_table_sql, ())
        mylog.info('\n✅ 测试表创建成功')

        # 插入单条记录
        sql = 'INSERT INTO sync_test_users (name, age) VALUES (%s, %s)'
        params = ('Alice', 25)

        affected = db.execute(sql, params)
        mylog.info(f'✅ 插入成功,影响行数: {affected}')

        # 插入多条记录(使用循环)
        users_data = [
            ('Bob', 30),
            ('Charlie', 35),
        ]

        for user_data in users_data:
            db.execute(sql, user_data)
        mylog.info(f'✅ 批量插入 {len(users_data)} 条记录完成')

        db.close()

    except Exception as e:
        mylog.info(f'❌ 插入失败: {e}')


def example_3_update_data():
    """示例 3: 更新数据"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 3: 更新数据')
    mylog.info('=' * 60)

    try:
        db = create_sync_mysql_pool('default')

        # 更新单条记录
        sql = 'UPDATE sync_test_users SET age = %s WHERE name = %s'
        params = (26, 'Alice')

        affected = db.execute(sql, params)
        mylog.info(f'\n✅ 更新成功,影响行数: {affected}')

        # 批量更新
        sql_batch = 'UPDATE sync_test_users SET age = age + 1 WHERE age > %s'
        affected = db.execute(sql_batch, (30,))
        mylog.info(f'✅ 批量更新,影响行数: {affected}')

        # 查询更新后的数据
        users = db.fetchall('SELECT * FROM sync_test_users', ())
        mylog.info('\n✅ 更新后的数据:')
        for user in users:
            mylog.info(f'  - {user}')

        db.close()

    except Exception as e:
        mylog.info(f'❌ 更新失败: {e}')


def example_4_delete_data():
    """示例 4: 删除数据并清理"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 4: 删除数据并清理')
    mylog.info('=' * 60)

    try:
        db = create_sync_mysql_pool('default')

        # 删除单条记录
        sql = 'DELETE FROM sync_test_users WHERE name = %s'
        affected = db.execute(sql, ('Bob',))
        mylog.info(f'\n✅ 删除成功,影响行数: {affected}')

        # 查询剩余数据
        remaining = db.fetchall('SELECT * FROM sync_test_users', ())
        mylog.info(f'✅ 剩余 {len(remaining)} 条记录')

        # 清理测试表
        db.execute('DROP TABLE IF EXISTS sync_test_users', ())
        mylog.info('✅ 测试表已删除')

        db.close()

    except Exception as e:
        mylog.info(f'❌ 删除失败: {e}')


def example_5_transaction():
    """示例 5: 事务管理"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 5: 事务管理')
    mylog.info('=' * 60)

    try:
        # 注意：创建连接池时需要设置 autocommit=False 才能使用事务
        db = create_sync_mysql_pool('default', autocommit=False)

        # 创建测试表
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_accounts (
                id INT PRIMARY KEY,
                name VARCHAR(50),
                balance DECIMAL(10,2)
            )
        """,
            (),
        )

        # 插入初始数据（使用新语法避免 MySQL 9.4 的 VALUES() 弃用警告）
        db.execute(
            'INSERT INTO sync_accounts VALUES (%s, %s, %s) AS new_row ON DUPLICATE KEY UPDATE balance=new_row.balance',
            (1, 'Account1', 1000),
        )
        db.execute(
            'INSERT INTO sync_accounts VALUES (%s, %s, %s) AS new_row ON DUPLICATE KEY UPDATE balance=new_row.balance',
            (2, 'Account2', 500),
        )

        mylog.info('\n开始事务...')
        db.begin()

        try:
            # 执行多个操作（转账100元）
            db.execute('UPDATE sync_accounts SET balance = balance - %s WHERE id = %s', (100, 1))
            db.execute('UPDATE sync_accounts SET balance = balance + %s WHERE id = %s', (100, 2))

            # 提交事务
            db.commit()
            mylog.info('✅ 事务提交成功')

            # 查询结果
            accounts = db.fetchall('SELECT * FROM sync_accounts', ())
            mylog.info('✅ 转账后余额:')
            for acc in accounts:
                mylog.info(f'  - {acc}')

        except Exception as e:
            # 回滚事务
            db.rollback()
            mylog.info(f'❌ 事务回滚: {e}')

        # 清理
        db.execute('DROP TABLE IF EXISTS sync_accounts', ())
        db.close()

    except Exception as e:
        mylog.info(f'❌ 事务失败: {e}')


def example_6_parameterized_query():
    """示例 6: 参数化查询(防止 SQL 注入)"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 6: 参数化查询')
    mylog.info('=' * 60)

    try:
        db = create_sync_mysql_pool('default')

        # ✅ 正确：使用参数化查询
        user_input = "1' OR '1'='1"  # 模拟恶意输入
        safe_query = 'SELECT DATABASE() as current_db, %s as user_input'
        results = db.fetchall(safe_query, (user_input,))
        mylog.info(f'\n✅ 参数化查询(安全): {results}')
        mylog.info(f'   恶意输入被安全转义: {user_input}')

        # ❌ 危险：字符串拼接(不要这样做！)
        # dangerous_query = f"SELECT * FROM users WHERE name = '{user_input}'"
        # 这会导致 SQL 注入漏洞

        # 查询系统信息（无需特定表）
        system_info = db.fetchone('SELECT VERSION() as version, DATABASE() as db_name', ())
        mylog.info(f'\n✅ 系统信息查询: {system_info}')

        db.close()

    except Exception as e:
        mylog.info(f'❌ 查询失败: {e}')


def example_7_error_handling():
    """示例 7: 错误处理"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 7: 错误处理')
    mylog.info('=' * 60)

    try:
        db = create_sync_mysql_pool('default')

        # 测试无效的 SQL 语句
        try:
            db.execute('INVALID SQL STATEMENT', ())
        except Exception as e:
            mylog.info(f'\n✅ 捕获到 SQL 错误: {type(e).__name__}')
            mylog.info(f'   错误信息: {str(e)[:80]}')

        # 测试不存在的表
        try:
            db.fetchall('SELECT * FROM nonexistent_table_12345', ())
        except Exception as e:
            mylog.info(f'\n✅ 捕获到表不存在错误: {type(e).__name__}')
            mylog.info(f'   错误信息: {str(e)[:80]}')

        # 测试连接检查
        if db.ping():
            mylog.info('\n✅ 连接池状态正常')
        else:
            mylog.info('\n❌ 连接池状态异常')

        db.close()
        mylog.info('✅ 错误处理示例完成')

    except Exception as e:
        mylog.info(f'❌ 错误处理示例失败: {e}')


def example_8_connection_pool_config():
    """示例 8: 连接池配置"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 8: 连接池配置')
    mylog.info('=' * 60)

    mylog.info("""
    MySQLPoolSync 主要配置参数:

    1. 基本连接参数:
       - host: 数据库主机地址
       - port: 数据库端口号 (默认 3306)
       - user: 数据库用户名
       - password: 数据库密码
       - db: 数据库名称

    2. 字符集:
       - charset: 字符集 (推荐 'utf8mb4')

    3. 事务控制:
       - autocommit: 自动提交 (True/False)
         * True: 每个操作自动提交(推荐用于简单查询)
         * False: 需要手动提交(用于事务操作)

    4. 连接回收:
       - pool_recycle: 连接回收时间(秒)
         * -1: 不回收
         * 3600: 1小时回收一次(推荐)

    5. 使用示例:
    """)

    # 基本配置
    db1 = create_sync_mysql_pool('default')
    mylog.info('  ✅ 使用默认配置创建连接池')
    db1.close()

    # 自定义配置
    db2 = create_sync_mysql_pool('default', autocommit=False, pool_recycle=3600)
    mylog.info('  ✅ 使用自定义配置创建连接池')
    db2.close()


def example_9_comparison_with_async():
    """示例 9: 与异步版本对比"""
    mylog.info('\n' + '=' * 60)
    mylog.info('示例 9: 同步 vs 异步对比')
    mylog.info('=' * 60)

    mylog.info("""
    MySQLPoolSync (同步) vs MySQLPool (异步) 对比:

    📊 MySQLPoolSync(本模块)- 同步模式:
    ✅ 优点:
       - 适用于同步代码环境(Flask、传统脚本)
       - 代码简单直观,无需 async/await
       - 可在任何 Python 环境中运行

    ❌ 缺点:
       - 性能略低于原生异步
       - 不适合高并发场景
       - 无法与其他异步代码良好配合

    使用场景:
       db = create_sync_mysql_pool('default')
       users2 = db.fetchall('SELECT * FROM users2', ())  # 同步调用
       db.close()

    ---

    ⚡ MySQLPool - 异步模式(推荐):
    ✅ 优点:
       - 高性能,适合高并发
       - 原生 asyncio 支持
       - 更好的资源利用

    ❌ 缺点:
       - 需要异步环境支持
       - 代码稍复杂(async/await)
       - 学习曲线稍陡

    使用场景:
       async with create_mysql_pool('default') as db:
           users2 = await db.fetchall('SELECT * FROM users2')  # 异步调用

    ---

    💡 选择建议:
       - 新项目 → 使用 MySQLPool (异步)
       - 同步环境 → 使用 MySQLPoolSync
       - FastAPI/aiohttp → 使用 MySQLPool
       - Flask/Django → 可用 MySQLPoolSync
    """)


def main():
    """主函数：演示所有示例"""
    mylog.info('\n' + '=' * 60)
    mylog.info('MySQLPoolSync 同步连接池使用示例')
    mylog.info('=' * 60)

    mylog.info("""
    ⚠️  注意事项:
    1. 本示例需要有效的数据库连接配置
    2. 请先在 cfg.py 中配置好数据库连接信息
    3. 参数必须使用元组格式: (value,) 或 (value1, value2)
    4. 示例中的部分操作可能会失败(如表不存在),这是正常的

    如需运行实际示例,请取消下面示例函数的注释。
    """)

    # 取消注释以运行示例
    example_1_basic_query()
    example_2_insert_data()
    example_3_update_data()
    example_4_delete_data()
    example_5_transaction()
    example_6_parameterized_query()
    example_7_error_handling()
    # example_8_connection_pool_config()
    # example_9_comparison_with_async()

    mylog.info('\n' + '=' * 60)
    mylog.info('✅ 示例展示完成!')
    mylog.info('=' * 60 + '\n')


if __name__ == '__main__':
    main()
