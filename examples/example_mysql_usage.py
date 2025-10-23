"""MySQL 同步连接使用示例.

本示例演示如何使用 MySQL 类进行同步数据库操作，包括:
1. 创建和管理数据库连接
2. 执行 SQL 查询(增删改查)
3. 事务管理
4. 使用上下文管理器自动管理连接
5. 参数化查询防止 SQL 注入
"""

from __future__ import annotations

from xtdbase.mysql import MySQL, create_mysql_connection

# 数据库配置
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'sandorn',
    'password': '123456',
    'db': 'bxflb',
    'charset': 'utf8mb4',
}


def example_basic_usage() -> None:
    """示例 1:基本用法 - 创建连接和执行查询."""
    print('\n' + '=' * 60)
    print('示例 1:基本用法')
    print('=' * 60)

    # 方式 1:直接创建实例
    db = MySQL(**db_config)
    try:
        # 先清理旧表
        db.execute('DROP TABLE IF EXISTS users')
        print('✅ 旧表已清理')

        # 创建测试表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            email VARCHAR(100) UNIQUE,
            age INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        db.execute(create_table_sql)
        print('✅ 测试表创建成功')

        # 插入数据
        insert_sql = 'INSERT INTO users (name, email, age) VALUES (%s, %s, %s)'
        db.execute(insert_sql, ('Alice', 'alice@example.com', 25))
        print('✅ 数据插入成功')

        # 查询单条数据
        select_sql = 'SELECT * FROM users WHERE name = %s'
        user = db.fetchone(select_sql, ('Alice',))
        print(f'✅ 查询结果: {user}')

    finally:
        db.close()
        print('✅ 连接已关闭\n')


def example_factory_function() -> None:
    """示例 2:使用工厂函数创建连接."""
    print('=' * 60)
    print('示例 2:使用工厂函数')
    print('=' * 60)

    # 使用工厂函数创建连接
    db = create_mysql_connection('default')

    try:
        # 批量插入数据
        users_data = [
            ('Bob', 'bob@example.com', 30),
            ('Charlie', 'charlie@example.com', 28),
            ('Diana', 'diana@example.com', 32),
        ]

        insert_sql = 'INSERT INTO users (name, email, age) VALUES (%s, %s, %s)'
        for user_data in users_data:
            db.execute(insert_sql, user_data)

        print(f'✅ 成功插入 {len(users_data)} 条数据')

        # 查询所有数据
        all_users = db.fetchall('SELECT * FROM users')
        print(f'✅ 查询到 {len(all_users)} 条记录:')
        for user in all_users:
            print(f'   - {user["name"]} ({user["email"]}) - {user["age"]}岁')

    finally:
        db.close()
        print('✅ 连接已关闭\n')


def example_context_manager() -> None:
    """示例 3:使用上下文管理器自动管理连接."""
    print('=' * 60)
    print('示例 3:上下文管理器(推荐)')
    print('=' * 60)

    # 使用 with 语句自动管理连接
    with MySQL(**db_config) as db:
        # 更新数据
        update_sql = 'UPDATE users SET age = %s WHERE name = %s'
        db.execute(update_sql, (26, 'Alice'))
        print('✅ 数据更新成功')

        # 查询更新后的数据
        user = db.fetchone('SELECT * FROM users WHERE name = %s', ('Alice',))
        print(f'✅ 更新后的数据: {user}')

        # 条件查询
        young_users = db.fetchall('SELECT * FROM users WHERE age < %s', (30,))
        print(f'✅ 年龄小于30的用户: {len(young_users)} 人')
        for user in young_users:
            print(f'   - {user["name"]}: {user["age"]}岁')

    print('✅ 上下文管理器自动关闭连接\n')


def example_transaction_management() -> None:
    """示例 4:事务管理."""
    print('=' * 60)
    print('示例 4:事务管理')
    print('=' * 60)

    # 创建局部配置副本，避免污染全局配置
    local_config = db_config.copy()
    local_config['autocommit'] = False

    with MySQL(**local_config) as db:
        try:
            # 开始事务
            db.begin()
            print('✅ 事务开始')

            # 删除一条记录
            delete_sql = 'DELETE FROM users WHERE name = %s'
            db.execute(delete_sql, ('Bob',))
            print('✅ 删除记录: Bob')

            # 插入新记录
            insert_sql = 'INSERT INTO users (name, email, age) VALUES (%s, %s, %s)'
            db.execute(insert_sql, ('Eve', 'eve@example.com', 29))
            print('✅ 插入新记录: Eve')

            # 提交事务
            db.commit()
            print('✅ 事务提交成功')

            # 验证结果
            users = db.fetchall('SELECT name FROM users ORDER BY name')
            print(f'✅ 当前用户列表: {[u["name"] for u in users]}')

        except Exception as e:
            # 回滚事务
            db.rollback()
            print(f'❌ 事务回滚: {e}')

    print('✅ 事务处理完成\n')


def example_transaction_rollback() -> None:
    """示例 5:事务回滚演示."""
    print('=' * 60)
    print('示例 5:事务回滚演示')
    print('=' * 60)

    # 创建局部配置副本
    local_config = db_config.copy()
    local_config['autocommit'] = False

    with MySQL(**local_config) as db:
        # 记录初始状态
        initial_count = db.fetchone('SELECT COUNT(*) as count FROM users')
        print(f'✅ 初始用户数: {initial_count["count"]}')

        try:
            # 必须先开始事务
            db.begin()
            print('✅ 事务开始')

            # 插入一条正常记录
            db.execute(
                'INSERT INTO users (name, email, age) VALUES (%s, %s, %s)',
                ('Frank', 'frank@example.com', 35),
            )
            print('✅ 插入记录: Frank')

            # 故意插入重复邮箱，触发唯一约束错误
            db.execute(
                'INSERT INTO users (name, email, age) VALUES (%s, %s, %s)',
                ('Grace', 'alice@example.com', 27),  # alice@example.com 已存在
            )
            print('✅ 插入记录: Grace')

            db.commit()
            print('✅ 事务提交')

        except Exception as e:
            db.rollback()
            print(f'❌ 发生错误,事务已回滚: {e}')

            # 验证回滚后数据未改变
            final_count = db.fetchone('SELECT COUNT(*) as count FROM users')
            print(f'✅ 回滚后用户数: {final_count["count"]}')
            print(f'✅ 数据一致性验证: {"通过" if initial_count == final_count else "失败"}')

    print('✅ 事务回滚演示完成\n')


def example_fetchmany() -> None:
    """示例 6:分批获取数据."""
    print('=' * 60)
    print('示例 6:分批获取数据(使用 LIMIT/OFFSET)')
    print('=' * 60)

    with MySQL(**db_config) as db:
        batch_size = 2
        offset = 0
        batch_num = 1

        while True:
            # 使用 LIMIT 和 OFFSET 分批查询
            query = f'SELECT * FROM users ORDER BY id LIMIT {batch_size} OFFSET {offset}'
            users = db.fetchall(query)

            if not users:
                break

            print(f'\n批次 {batch_num} (每批 {batch_size} 条):')
            for user in users:
                print(f'  - ID: {user["id"]}, 名称: {user["name"]}, 邮箱: {user["email"]}')

            offset += batch_size
            batch_num += 1

    print('\n✅ 分批查询完成\n')


def example_query_with_conditions() -> None:
    """示例 7:复杂查询条件."""
    print('=' * 60)
    print('示例 7:复杂查询条件')
    print('=' * 60)

    with MySQL(**db_config) as db:
        # 查询:年龄在指定范围内的用户
        query = 'SELECT * FROM users WHERE age BETWEEN %s AND %s ORDER BY age'
        users = db.fetchall(query, (25, 30))
        print(f'✅ 年龄在 25-30 之间的用户 ({len(users)} 人):')
        for user in users:
            print(f'   - {user["name"]}: {user["age"]}岁')

        # 查询:名称包含特定字符的用户
        query = 'SELECT * FROM users WHERE name LIKE %s'
        users = db.fetchall(query, ('%a%',))  # 名称中包含 'a' 的用户
        print(f'\n✅ 名称中包含 "a" 的用户 ({len(users)} 人):')
        for user in users:
            print(f'   - {user["name"]}')

        # 聚合查询
        avg_age = db.fetchone('SELECT AVG(age) as avg_age FROM users')
        print(f'\n✅ 用户平均年龄: {avg_age["avg_age"]:.1f} 岁')

    print('✅ 复杂查询完成\n')


def example_cleanup() -> None:
    """清理测试数据."""
    print('=' * 60)
    print('清理测试数据')
    print('=' * 60)

    with MySQL(**db_config) as db:
        db.execute('DROP TABLE IF EXISTS users')
        print('✅ 测试表已删除')

    print('✅ 清理完成\n')


def main() -> None:
    """主函数 - 运行所有示例."""
    print('\n' + '🚀 MySQL 同步连接使用示例'.center(60, '='))
    print('注意: 请先修改数据库配置信息再运行示例\n')

    try:
        # 运行所有示例
        example_basic_usage()
        example_factory_function()
        example_context_manager()
        example_transaction_management()
        example_transaction_rollback()
        example_fetchmany()
        example_query_with_conditions()

        # 清理测试数据
        example_cleanup()  # 自动清理测试数据

    except Exception as e:
        print(f'\n❌ 示例执行失败: {e}')
        print('提示: 请检查数据库配置是否正确')


if __name__ == '__main__':
    main()
