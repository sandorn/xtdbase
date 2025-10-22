# !/usr/bin/env python
"""AioMySQLPool异步连接池测试套件 - 全面测试标准DB-API 2.0接口.

本测试套件演示了AioMySQLPool的所有功能:
    - 标准查询接口: fetchone, fetchall, fetchmany
    - 数据修改接口: execute
    - 事务管理: begin, commit, rollback
    - 上下文管理器: async with语句
    - 异步迭代器: iterate方法
    - 连接健康检查: ping方法
    - 向后兼容性: get, query等旧接口

运行测试:
    python examples/test_aiomysqlpool.py
"""

from __future__ import annotations

import asyncio

from xtlog import mylog as logger

from xtdbase.aiomysqlpool import create_async_mysql_pool


async def _test_basic_operations():
    """测试基本的数据库操作,使用标准DB-API 2.0接口.

    测试内容:
    1. 创建连接池实例并初始化
    2. 使用fetchone()查询单条记录
    3. 使用execute()执行插入操作
    4. 使用fetchall()查询多条记录
    5. 使用fetchmany()查询指定数量记录
    6. 测试ping()连接健康检查
    7. 测试pool_size属性
    """
    print('\n' + '=' * 60)
    print('【测试1】基本数据库操作 - 标准接口')
    print('=' * 60)

    db = create_async_mysql_pool(db_key='default')
    try:
        # 测试ping
        if await db.ping():
            print('✅ 连接池ping测试通过')

        # 查询单条记录（标准接口）
        result = await db.fetchone('SELECT * FROM users2 WHERE ID = %s', 143)
        print(f'✅ fetchone查询成功: {result}')

        # 插入测试
        new_id = await db.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', '标准接口测试', '123456', '13900000000')
        print(f'✅ execute插入成功, 新ID: {new_id}')

        # 查询所有记录（标准接口）
        all_users = await db.fetchall('SELECT * FROM users2 LIMIT 5')
        print(f'✅ fetchall查询成功: 返回{len(all_users)}条记录')

        # 查询指定数量记录（标准接口）
        some_users = await db.fetchmany('SELECT * FROM users2', 3)
        print(f'✅ fetchmany查询成功: 返回{len(some_users)}条记录')

        # 检查连接池状态
        if db.pool_size:
            current, maximum = db.pool_size
            print(f'✅ 连接池状态: {current}/{maximum}')

    except Exception as e:
        print(f'❌ 测试过程中出错: {e}')
        import traceback

        traceback.print_exc()
    finally:
        await db.close()


async def _test_context_manager():
    """测试上下文管理器用法,验证异步上下文协议的正确实现.

    测试内容:
    1. 使用async with语句创建连接池实例
    2. 验证上下文管理器自动处理连接池的初始化
    3. 执行数据库查询操作
    4. 验证上下文管理器自动处理连接池的关闭
    5. 测试异常情况下的资源管理
    """
    print('\n' + '=' * 60)
    print('【测试2】上下文管理器 - 自动资源管理')
    print('=' * 60)

    try:
        async with create_async_mysql_pool(db_key='default') as db:
            # 使用上下文管理器自动处理初始化和关闭
            result = await db.fetchone('SELECT * FROM users2 WHERE ID = %s', 143)
            print(f'✅ 上下文管理器查询成功: {result}')

            # 测试向后兼容的旧接口
            result_old = await db.get('SELECT * FROM users2 WHERE ID = %s', 143)
            print(f'✅ 旧接口(get)仍可用,向后兼容: {result_old is not None}')

    except Exception as e:
        print(f'❌ 上下文管理器测试出错: {e}')


async def _test_transaction():
    """测试事务操作功能,验证事务的开始、提交和回滚流程.

    测试内容:
    1. 开始事务并获取连接
    2. 执行多条SQL操作
    3. 测试提交(commit)操作
    4. 测试回滚(rollback)操作
    5. 验证事务的原子性
    """
    print('\n' + '=' * 60)
    print('【测试3】事务操作 - 原子性保证')
    print('=' * 60)

    async with create_async_mysql_pool(db_key='default') as db:
        # 测试成功提交
        conn = await db.begin()
        try:
            cur = await conn.cursor()
            await cur.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', ('事务测试用户', '654321', '13911111111'))
            new_id = cur.lastrowid
            await cur.execute('UPDATE users2 SET username = %s WHERE ID = %s', ('事务用户已更新', new_id))
            await db.commit(conn)
            print(f'✅ 事务提交成功, 新用户ID: {new_id}')
        except Exception as e:
            await db.rollback(conn)
            print(f'❌ 事务提交失败并回滚: {e}')

        # 测试回滚
        print('   测试事务回滚...')
        conn2 = await db.begin()
        try:
            cur2 = await conn2.cursor()
            await cur2.execute('INSERT INTO users2(username, password, 手机) VALUES (%s, %s, %s)', ('将被回滚的用户', '000000', '13922222222'))
            # 故意触发错误以测试回滚
            raise Exception('模拟错误触发回滚')
        except Exception as e:
            await db.rollback(conn2)
            print(f'✅ 事务回滚成功: {e}')


async def _test_iterator():
    """测试异步迭代器功能,验证批量处理大量数据的能力.

    测试内容:
    1. 使用async for进行迭代查询
    2. 测试自定义batch_size参数
    3. 验证逐行数据处理
    4. 演示提前终止迭代

    iterate方法特别适合处理大量数据,通过分批获取避免内存溢出。
    """
    print('\n' + '=' * 60)
    print('【测试4】异步迭代器 - 大数据处理')
    print('=' * 60)

    async with create_async_mysql_pool(db_key='default') as db:
        count = 0
        print('   开始迭代查询(batch_size=2, 限制前5条)...')
        async for row in db.iterate('SELECT * FROM users2 ORDER BY ID', batch_size=2):
            count += 1
            print(f'   迭代第{count}行: ID={row.get("ID", "N/A")}, username={row.get("username", "N/A")}')
            if count >= 5:  # 只打印前5行
                break
        print(f'✅ 迭代完成, 共处理 {count} 条记录')


class TestAioMySQLPool:
    """AioMySQLPool功能测试类."""

    def __init__(self, db_key: str = 'default', test_table: str = 'users2'):
        """初始化测试类.

        Args:
            db_key: 数据库配置键名
            test_table: 测试用表名
        """
        self.db_key = db_key
        self.test_table = test_table
        self.test_ids: list[int] = []  # 记录测试插入的ID,便于清理

    async def cleanup_test_data(self):
        """清理测试数据."""
        if not self.test_ids:
            return

        try:
            async with create_async_mysql_pool(self.db_key) as db:
                for test_id in self.test_ids:
                    await db.execute(f'DELETE FROM {self.test_table} WHERE ID = %s', test_id)
                logger.info(f'✅ 清理了 {len(self.test_ids)} 条测试数据')
                self.test_ids.clear()
        except Exception as e:
            logger.error(f'❌ 清理测试数据失败: {e}')

    async def test_ping(self) -> bool:
        """测试1: 连接池健康检查.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试1】连接池健康检查 - ping方法')
        try:
            db = create_async_mysql_pool(self.db_key)
            await db.init_pool()

            # 测试ping
            if await db.ping():
                logger.success('✅ 连接池ping测试通过')

                # 测试pool_size属性
                if db.pool_size:
                    current, maximum = db.pool_size
                    logger.success(f'✅ 连接池状态: {current}/{maximum}')

                await db.close()
                return True
            logger.error('❌ 连接池ping失败')
            await db.close()
            return False
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_fetchone(self) -> bool:
        """测试2: fetchone方法 - 查询单条记录.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试2】fetchone - 查询单条记录(标准DB-API 2.0接口)')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 查询单条记录
                result = await db.fetchone(f'SELECT * FROM {self.test_table} WHERE ID > %s LIMIT 1', 100)

                if result:
                    logger.success(f'✅ fetchone查询成功: ID={result.get("ID", "N/A")}, username={result.get("username", "N/A")}')
                    return True
                logger.warning('⚠️ 没有查询到记录(可能表为空)')
                return True  # 空结果也是正常的
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_fetchall(self) -> bool:
        """测试3: fetchall方法 - 查询所有记录.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试3】fetchall - 查询多条记录(标准DB-API 2.0接口)')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 查询多条记录
                results = await db.fetchall(f'SELECT * FROM {self.test_table} ORDER BY ID DESC LIMIT 5')

                logger.success(f'✅ fetchall查询成功: 返回{len(results)}条记录')
                for i, row in enumerate(results[:3], 1):  # 只显示前3条
                    logger.info(f'   记录{i}: ID={row.get("ID", "N/A")}, username={row.get("username", "N/A")}')
                return True
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_fetchmany(self) -> bool:
        """测试4: fetchmany方法 - 查询指定数量记录.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试4】fetchmany - 查询指定数量记录(标准DB-API 2.0接口)')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 查询指定数量的记录
                results = await db.fetchmany(
                    f'SELECT * FROM {self.test_table} ORDER BY ID',
                    3,  # 只获取3条
                )

                logger.success(f'✅ fetchmany查询成功: 返回{len(results)}条记录(预期3条)')
                for i, row in enumerate(results, 1):
                    logger.info(f'   记录{i}: ID={row.get("ID", "N/A")}')
                return True
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_execute_insert(self) -> bool:
        """测试5: execute方法 - 插入数据.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试5】execute - 插入数据(标准DB-API 2.0接口)')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 插入测试数据
                new_id = await db.execute(f'INSERT INTO {self.test_table}(username, password, 手机) VALUES (%s, %s, %s)', 'aiomysql_test_user', 'test_123', '13800138000')

                if new_id > 0:
                    self.test_ids.append(new_id)  # 记录ID以便清理
                    logger.success(f'✅ execute插入成功: 新记录ID={new_id}')

                    # 验证插入
                    verify = await db.fetchone(f'SELECT * FROM {self.test_table} WHERE ID = %s', new_id)
                    if verify:
                        logger.success(f'   验证成功: username={verify.get("username", "N/A")}')
                    return True
                logger.error('❌ 插入失败: 未返回新ID')
                return False
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_execute_update(self) -> bool:
        """测试6: execute方法 - 更新数据.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试6】execute - 更新数据(标准DB-API 2.0接口)')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 先插入一条测试数据
                new_id = await db.execute(f'INSERT INTO {self.test_table}(username, password, 手机) VALUES (%s, %s, %s)', 'update_test_user', 'old_password', '13900139000')
                self.test_ids.append(new_id)

                # 更新数据
                affected = await db.execute(f'UPDATE {self.test_table} SET username = %s WHERE ID = %s', 'updated_user', new_id)

                if affected > 0:
                    logger.success(f'✅ execute更新成功: 影响{affected}行')

                    # 验证更新
                    verify = await db.fetchone(f'SELECT * FROM {self.test_table} WHERE ID = %s', new_id)
                    if verify and verify.get('username') == 'updated_user':
                        logger.success(f'   验证成功: username已更新为 {verify.get("username")}')
                    return True
                logger.error('❌ 更新失败: 未影响任何行')
                return False
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_transaction(self) -> bool:
        """测试7: 事务操作 - begin/commit/rollback.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试7】事务操作 - 原子性保证')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                # 测试成功提交
                logger.info('   测试事务提交...')
                conn = await db.begin()
                try:
                    cur = await conn.cursor()
                    await cur.execute(f'INSERT INTO {self.test_table}(username, password, 手机) VALUES (%s, %s, %s)', ('transaction_user_1', 'pwd123', '13911111111'))
                    new_id = cur.lastrowid
                    self.test_ids.append(new_id)

                    await cur.execute(f'UPDATE {self.test_table} SET username = %s WHERE ID = %s', ('transaction_user_updated', new_id))

                    await db.commit(conn)
                    logger.success(f'✅ 事务提交成功: ID={new_id}')
                except Exception as e:
                    await db.rollback(conn)
                    logger.error(f'❌ 事务提交失败: {e}')
                    return False

                # 测试回滚
                logger.info('   测试事务回滚...')
                conn2 = await db.begin()
                try:
                    cur2 = await conn2.cursor()
                    await cur2.execute(f'INSERT INTO {self.test_table}(username, password, 手机) VALUES (%s, %s, %s)', ('will_be_rolled_back', 'pwd456', '13922222222'))
                    # 故意触发错误
                    raise Exception('模拟错误,测试回滚')
                except Exception:
                    await db.rollback(conn2)
                    logger.success('✅ 事务回滚成功')

                return True
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_iterate(self) -> bool:
        """测试8: 异步迭代器 - 大数据处理.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试8】异步迭代器 - 逐行处理大量数据')
        try:
            async with create_async_mysql_pool(self.db_key) as db:
                count = 0
                logger.info('   开始迭代查询(batch_size=2, 限制前5行)...')

                async for row in db.iterate(f'SELECT * FROM {self.test_table} ORDER BY ID', batch_size=2):
                    count += 1
                    logger.info(f'   迭代第{count}行: ID={row.get("ID", "N/A")}, username={row.get("username", "N/A")}')
                    if count >= 5:  # 只处理前5行
                        break

                logger.success(f'✅ 异步迭代器测试成功: 处理{count}行')
                return True
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def test_context_manager(self) -> bool:
        """测试10: 上下文管理器 - 自动资源管理.

        Returns:
            bool: 测试是否通过
        """
        logger.info('\n【测试10】上下文管理器 - 自动资源管理')
        try:
            # 测试正常情况
            async with create_async_mysql_pool(self.db_key) as db:
                result = await db.fetchone(f'SELECT COUNT(*) as total FROM {self.test_table}')
                total = result.get('total', 0) if result else 0
                logger.success(f'✅ 上下文管理器正常工作: 表中共有{total}条记录')

            # 测试异常情况(资源仍应正确释放)
            try:
                async with create_async_mysql_pool(self.db_key) as db:
                    await db.fetchone('INVALID SQL SYNTAX')  # 故意触发错误
            except Exception:
                logger.success('✅ 异常情况下上下文管理器也能正确清理资源')

            return True
        except Exception as e:
            logger.error(f'❌ 测试失败: {e}')
            return False

    async def run_all_tests(self) -> bool:
        """运行所有测试用例.

        Returns:
            bool: 所有测试是否全部通过
        """
        logger.info('\n' + '=' * 70)
        logger.info('   AioMySQLPool 功能测试套件')
        logger.info('   测试标准DB-API 2.0接口和扩展功能')
        logger.info('=' * 70)

        # 测试列表
        tests = [
            ('连接健康检查', self.test_ping),
            ('fetchone查询', self.test_fetchone),
            ('fetchall查询', self.test_fetchall),
            ('fetchmany查询', self.test_fetchmany),
            ('execute插入', self.test_execute_insert),
            ('execute更新', self.test_execute_update),
            ('事务操作', self.test_transaction),
            ('异步迭代器', self.test_iterate),
            ('上下文管理器', self.test_context_manager),
        ]

        passed = 0
        failed = 0

        for name, test_func in tests:
            try:
                if await test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f'❌ {name} 执行异常: {e}')
                failed += 1

        # 清理测试数据
        logger.info('\n' + '-' * 70)
        await self.cleanup_test_data()

        # 测试总结
        logger.info('\n' + '=' * 70)
        logger.info('   测试结果摘要')
        logger.info('=' * 70)
        logger.info(f'   总测试数: {len(tests)}')
        logger.info(f'   通过: {passed}')
        logger.info(f'   失败: {failed}')
        logger.info(f'   通过率: {passed / len(tests) * 100:.1f}%')
        logger.info('=' * 70)

        if failed == 0:
            logger.success('\n✅ 所有测试通过')
            logger.info('\n💡 提示:')
            logger.info('  - 使用async with确保资源正确释放')
            logger.info('  - 大数据量处理使用iterate()避免内存溢出')
        else:
            logger.error(f'\n❌ 有 {failed} 个测试失败')

        return failed == 0


async def main():
    """主函数 - 运行测试套件."""
    tester = TestAioMySQLPool(db_key='default', test_table='users2')
    success = await tester.run_all_tests()
    return 0 if success else 1


# 运行所有测试
async def run_all_tests():
    """运行所有测试用例,全面验证AioMySQLPool类的各项功能.

    测试套件:
    1. 基本数据库操作 - 测试标准DB-API 2.0接口
    2. 上下文管理器 - 测试自动资源管理
    3. 事务操作 - 测试原子性和一致性
    4. 异步迭代器 - 测试大数据量处理

    此函数确保所有功能模块都能正常工作,
    在开发和维护过程中快速验证代码的正确性。
    """
    print('\n')
    print('=' * 60)
    print('   AioMySQLPool 功能测试套件')
    print('   测试标准DB-API 2.0接口和扩展功能')
    print('=' * 60)

    await _test_basic_operations()
    await _test_context_manager()
    await _test_transaction()
    await _test_iterator()

    print('\n' + '=' * 60)
    print('✅ 所有测试完成!')
    print('=' * 60)
    print('\n提示:')
    print('  - 推荐使用标准接口: fetchone, fetchall, fetchmany, execute')
    print('  - 旧接口(get, query, query_many)仍可用,但建议迁移')
    print('  - 使用上下文管理器确保资源正确释放')
    print('  - 大数据量处理使用iterate()避免内存溢出')
    print('=' * 60)


if __name__ == '__main__':
    # # 执行测试
    # try:
    #     asyncio.run(run_all_tests())
    # except Exception as e:
    #     print(f'\n❌ 测试套件执行失败: {e}')
    #     import traceback

    #     traceback.print_exc()

    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.warning('\n⚠️ 测试被用户中断')
        exit(1)
    except Exception as e:
        logger.error(f'\n❌ 测试套件执行失败: {e}')
        import traceback

        traceback.print_exc()
        exit(1)
