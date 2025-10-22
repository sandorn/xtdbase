# !/usr/bin/env python
"""AioMySQLPool 简单使用示例.

演示如何使用异步MySQL连接池进行基本的数据库操作。
"""

from __future__ import annotations

import asyncio

from xtlog import mylog as logger

from xtdbase.aiomysqlpool import create_async_mysql_pool


async def basic_query_example():
    """示例1: 基本查询操作."""
    logger.info('\n' + '=' * 60)
    logger.info('【示例1】基本查询操作')
    logger.info('=' * 60)

    async with create_async_mysql_pool('default') as db:
        # 查询单条记录
        user = await db.fetchone('SELECT * FROM users2 WHERE ID = %s', 143)
        if user:
            logger.success(f'查询到用户: ID={user.get("ID")}, username={user.get("username")}')

        # 查询多条记录
        users = await db.fetchall('SELECT * FROM users2 LIMIT 5')
        logger.success(f'查询到 {len(users)} 条记录')


async def insert_update_example():
    """示例2: 插入和更新数据."""
    logger.info('\n' + '=' * 60)
    logger.info('【示例2】插入和更新数据')
    logger.info('=' * 60)

    async with create_async_mysql_pool('default') as db:
        # 插入数据
        new_id = await db.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', 'example_user', 'password123', '13800138000')
        logger.success(f'插入成功, 新ID: {new_id}')

        # 更新数据
        affected = await db.execute('UPDATE users2 SET username = %s WHERE ID = %s', 'updated_user', new_id)
        logger.success(f'更新成功, 影响行数: {affected}')

        # 清理测试数据
        await db.execute('DELETE FROM users2 WHERE ID = %s', new_id)
        logger.info('已清理测试数据')


async def transaction_example():
    """示例3: 事务操作."""
    logger.info('\n' + '=' * 60)
    logger.info('【示例3】事务操作')
    logger.info('=' * 60)

    async with create_async_mysql_pool('default') as db:
        conn = await db.begin()
        try:
            cur = await conn.cursor()

            # 插入多条记录
            await cur.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', ('transaction_user1', 'pwd1', '13911111111'))
            id1 = cur.lastrowid

            await cur.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', ('transaction_user2', 'pwd2', '13922222222'))
            id2 = cur.lastrowid

            # 提交事务
            await db.commit(conn)
            logger.success(f'事务提交成功, 插入ID: {id1}, {id2}')

            # 清理测试数据
            await db.execute(f'DELETE FROM users2 WHERE ID IN ({id1}, {id2})')
            logger.info('已清理测试数据')

        except Exception as e:
            # 回滚事务
            await db.rollback(conn)
            logger.error(f'事务失败, 已回滚: {e}')


async def iterator_example():
    """示例4: 使用迭代器处理数据."""
    logger.info('\n' + '=' * 60)
    logger.info('【示例4】异步迭代器 - 大数据处理')
    logger.info('=' * 60)

    async with create_async_mysql_pool('default') as db:
        count = 0
        # 使用迭代器逐行处理，适合大量数据
        async for row in db.iterate('SELECT * FROM users2 ORDER BY ID', batch_size=10):
            count += 1
            if count <= 3:  # 只显示前3条
                logger.info(f'  行{count}: ID={row.get("ID")}, username={row.get("username")}')
            if count >= 10:  # 限制处理数量
                break

        logger.success(f'迭代完成, 共处理 {count} 条记录')


async def main():
    """运行所有示例."""
    try:
        logger.info('\n' + '=' * 60)
        logger.info('   AioMySQLPool 使用示例')
        logger.info('=' * 60)

        await basic_query_example()
        await insert_update_example()
        await transaction_example()
        await iterator_example()

        logger.info('\n' + '=' * 60)
        logger.success('✅ 所有示例执行完成!')
        logger.info('=' * 60)
        logger.info('\n💡 更多详细测试请运行: python examples/test_aiomysqlpool.py')

    except Exception as e:
        logger.error(f'\n❌ 示例执行失败: {e}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())
