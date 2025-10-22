# !/usr/bin/env python3
"""
==============================================================
Description  : Redis客户端测试示例
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2025-10-21
FilePath     : /examples/test_redis_client.py
Github       : https://github.com/sandorn/home

本文件展示了如何使用 Redis 客户端的各项功能
包括：连接初始化、基本操作、Hash操作、List操作、Set操作等
==============================================================
"""

from __future__ import annotations

import asyncio

from xtlog import mylog as logger

from xtdbase.cfg import DB_CFG
from xtdbase.redis_client import RedisManager, create_redis_client


class TestRedisClient:
    """Redis客户端测试类"""

    def __init__(self):
        """初始化测试类"""
        self.test_prefix = 'test_redis'
        self.test_keys = []  # 记录测试过程中创建的键,便于清理

    def setup(self):
        """设置测试环境"""
        logger.info('\n===================== 开始设置测试环境 =====================')
        # 创建同步客户端用于测试
        self.sync_redis = create_redis_client('redis')
        logger.success('成功创建同步Redis客户端')

        # 清理可能存在的测试数据
        self._cleanup_test_data()
        logger.info('===================== 测试环境设置完成 =====================\n')

    def teardown(self):
        """清理测试环境"""
        logger.info('\n===================== 开始清理测试环境 =====================')
        # 清理测试数据
        self._cleanup_test_data()
        # 关闭客户端
        if hasattr(self, 'sync_redis'):
            self.sync_redis.close()
        logger.info('===================== 测试环境清理完成 =====================\n')

    def _cleanup_test_data(self):
        """清理测试数据"""
        if hasattr(self, 'sync_redis') and self.sync_redis:
            # 删除所有测试键
            for key in self.test_keys:
                try:
                    self.sync_redis.delete(key)
                except Exception as e:
                    logger.debug(f'清理测试键失败: {key}, 错误: {e!s}')
            self.test_keys.clear()

    def _add_test_key(self, key: str):
        """添加测试键到清理列表"""
        self.test_keys.append(key)

    def test_basic_operations(self):
        """测试基本操作: SET, GET, DELETE, EXISTS"""
        logger.info('\n===== 测试基本操作 =====')

        # 测试 SET 和 GET
        key = f'{self.test_prefix}:basic:string'
        self._add_test_key(key)
        self.sync_redis.set(key, 'test_value')
        value = self.sync_redis.get(key)
        if value == b'test_value':
            logger.success(f'SET/GET测试成功: {value}')
        else:
            logger.error(f'SET/GET测试失败: {value}')
            return False

        # 测试 EXISTS
        if self.sync_redis.exists(key):
            logger.success(f'EXISTS测试成功: 键 {key} 存在')
        else:
            logger.error(f'EXISTS测试失败: 键 {key} 不存在')
            return False

        # 测试 DELETE
        self.sync_redis.delete(key)
        if not self.sync_redis.exists(key):
            logger.success(f'DELETE测试成功: 键 {key} 已删除')
        else:
            logger.error(f'DELETE测试失败: 键 {key} 仍然存在')
            return False

        return True

    def test_expiration(self):
        """测试过期时间设置: EXPIRE, TTL"""
        logger.info('\n===== 测试过期时间 =====')

        key = f'{self.test_prefix}:expire:key'
        self._add_test_key(key)

        # 设置键值和过期时间
        self.sync_redis.set(key, 'expire_test', ex=10)  # 10秒后过期

        # 检查TTL
        ttl = int(self.sync_redis.ttl(key))
        if 0 < ttl <= 10:
            logger.success(f'EXPIRE测试成功: TTL={ttl}秒')
        else:
            logger.error(f'EXPIRE测试失败: TTL={ttl}')
            return False

        # 测试 PERSIST (移除过期时间)
        self.sync_redis.persist(key)
        ttl = int(self.sync_redis.ttl(key))
        if ttl == -1:  # -1 表示没有过期时间
            logger.success('PERSIST测试成功: 过期时间已移除')
        else:
            logger.error(f'PERSIST测试失败: TTL={ttl}')
            return False

        return True

    def test_hash_operations(self):
        """测试Hash操作: HSET, HGET, HGETALL, HDEL"""
        logger.info('\n===== 测试Hash操作 =====')

        key = f'{self.test_prefix}:hash:user'
        self._add_test_key(key)

        # HSET - 设置Hash字段
        self.sync_redis.hset(key, 'name', '张三')
        self.sync_redis.hset(key, 'age', '25')
        self.sync_redis.hset(key, 'city', '北京')

        # HGET - 获取单个字段
        name = self.sync_redis.hget(key, 'name')
        if name == b'\xe5\xbc\xa0\xe4\xb8\x89':  # '张三' 的 UTF-8 编码
            logger.success(f'HGET测试成功: name={name}')
        else:
            logger.error(f'HGET测试失败: name={name}')
            return False

        # HGETALL - 获取所有字段
        user_data = dict(self.sync_redis.hgetall(key))
        if len(user_data) == 3:
            logger.success(f'HGETALL测试成功: {user_data}')
        else:
            logger.error(f'HGETALL测试失败: {user_data}')
            return False

        # HDEL - 删除字段
        self.sync_redis.hdel(key, 'city')
        remaining_fields = dict(self.sync_redis.hgetall(key))
        if len(remaining_fields) == 2:
            logger.success(f'HDEL测试成功: 剩余字段={len(remaining_fields)}')
        else:
            logger.error(f'HDEL测试失败: 剩余字段={len(remaining_fields)}')
            return False

        return True

    def test_list_operations(self):
        """测试List操作: LPUSH, RPUSH, LRANGE, LPOP, RPOP"""
        logger.info('\n===== 测试List操作 =====')

        key = f'{self.test_prefix}:list:queue'
        self._add_test_key(key)

        # RPUSH - 从右侧插入
        self.sync_redis.rpush(key, 'first', 'second', 'third')

        # LRANGE - 获取列表元素
        items = list(self.sync_redis.lrange(key, 0, -1))
        if len(items) == 3 and items[0] == b'first':
            logger.success(f'RPUSH/LRANGE测试成功: {items}')
        else:
            logger.error(f'RPUSH/LRANGE测试失败: {items}')
            return False

        # LPUSH - 从左侧插入
        self.sync_redis.lpush(key, 'zero')
        items = list(self.sync_redis.lrange(key, 0, -1))
        if items[0] == b'zero':
            logger.success(f'LPUSH测试成功: 第一个元素={items[0]}')
        else:
            logger.error(f'LPUSH测试失败: {items}')
            return False

        # LPOP - 从左侧弹出
        popped = self.sync_redis.lpop(key)
        if popped == b'zero':
            logger.success(f'LPOP测试成功: 弹出={popped}')
        else:
            logger.error(f'LPOP测试失败: {popped}')
            return False

        # RPOP - 从右侧弹出
        popped = self.sync_redis.rpop(key)
        if popped == b'third':
            logger.success(f'RPOP测试成功: 弹出={popped}')
        else:
            logger.error(f'RPOP测试失败: {popped}')
            return False

        return True

    def test_set_operations(self):
        """测试Set操作: SADD, SMEMBERS, SREM, SISMEMBER"""
        logger.info('\n===== 测试Set操作 =====')

        key = f'{self.test_prefix}:set:tags'
        self._add_test_key(key)

        # SADD - 添加成员
        self.sync_redis.sadd(key, 'python', 'redis', 'database')

        # SMEMBERS - 获取所有成员
        members = set(self.sync_redis.smembers(key))
        if len(members) == 3:
            logger.success(f'SADD/SMEMBERS测试成功: {members}')
        else:
            logger.error(f'SADD/SMEMBERS测试失败: {members}')
            return False

        # SISMEMBER - 检查成员是否存在
        if self.sync_redis.sismember(key, 'python'):
            logger.success('SISMEMBER测试成功: python 存在于集合中')
        else:
            logger.error('SISMEMBER测试失败')
            return False

        # SREM - 删除成员
        self.sync_redis.srem(key, 'database')
        members = set(self.sync_redis.smembers(key))
        if len(members) == 2:
            logger.success(f'SREM测试成功: 剩余成员={len(members)}')
        else:
            logger.error(f'SREM测试失败: {members}')
            return False

        return True

    def test_config_initialization(self):
        """测试配置方式初始化"""
        logger.info('\n===== 测试配置方式初始化 =====')

        # 使用配置创建客户端
        redis = create_redis_client('redis')

        # 测试连接
        if redis.ping():
            logger.success('配置方式初始化成功,连接正常')
            redis.close()
            return True
        logger.error('配置方式初始化失败,连接异常')
        redis.close()
        return False

    def test_manager_context(self):
        """测试RedisManager上下文管理器"""
        logger.info('\n===== 测试上下文管理器 =====')

        cfg = DB_CFG.redis.value[0].copy()

        # 使用上下文管理器
        manager = RedisManager(host=cfg['host'], port=cfg['port'], db=cfg['db'])
        manager.client = create_redis_client('redis')

        with manager:
            # 在上下文中执行操作
            key = f'{self.test_prefix}:context:test'
            self._add_test_key(key)
            manager.client.set(key, 'context_value')
            value = manager.client.get(key)

            if value == b'context_value':
                logger.success('上下文管理器测试成功')
                return True
            logger.error('上下文管理器测试失败')
            return False

        return True

    def test_ping(self):
        """测试Ping连接"""
        logger.info('\n===== 测试Ping连接 =====')

        if self.sync_redis.ping():
            logger.success('Ping测试成功,连接正常')
            return True
        logger.error('Ping测试失败,连接异常')
        return False

    def test_increment_decrement(self):
        """测试计数器操作: INCR, DECR, INCRBY, DECRBY"""
        logger.info('\n===== 测试计数器操作 =====')

        key = f'{self.test_prefix}:counter'
        self._add_test_key(key)

        # INCR - 递增
        val1 = self.sync_redis.incr(key)
        val2 = self.sync_redis.incr(key)
        if val1 == 1 and val2 == 2:
            logger.success(f'INCR测试成功: {val1} -> {val2}')
        else:
            logger.error(f'INCR测试失败: {val1}, {val2}')
            return False

        # INCRBY - 递增指定值
        val3 = self.sync_redis.incrby(key, 10)
        if val3 == 12:
            logger.success(f'INCRBY测试成功: {val3}')
        else:
            logger.error(f'INCRBY测试失败: {val3}')
            return False

        # DECR - 递减
        val4 = self.sync_redis.decr(key)
        if val4 == 11:
            logger.success(f'DECR测试成功: {val4}')
        else:
            logger.error(f'DECR测试失败: {val4}')
            return False

        # DECRBY - 递减指定值
        val5 = self.sync_redis.decrby(key, 5)
        if val5 == 6:
            logger.success(f'DECRBY测试成功: {val5}')
        else:
            logger.error(f'DECRBY测试失败: {val5}')
            return False

        return True

    def run_all_tests(self):
        """运行所有测试"""
        logger.info('\n' + '-' * 60 + '\n' + '                    Redis客户端全面测试\n' + '-' * 60)

        # 测试结果统计
        tests_run = 0
        tests_passed = 0

        try:
            # 设置测试环境
            self.setup()

            # 定义测试方法列表
            test_methods = [
                self.test_ping,
                self.test_config_initialization,
                self.test_basic_operations,
                self.test_expiration,
                self.test_increment_decrement,
                self.test_hash_operations,
                self.test_list_operations,
                self.test_set_operations,
                self.test_manager_context,
            ]

            # 运行每个测试方法
            for test_method in test_methods:
                tests_run += 1
                method_name = test_method.__name__
                logger.info(f'\n[{tests_run}/{len(test_methods)}] 运行测试: {method_name}')

                if test_method():
                    tests_passed += 1
                    logger.success(f'测试通过: {method_name}')
                else:
                    logger.error(f'测试失败: {method_name}')

            # 输出测试结果摘要
            logger.info(
                '\n'
                + '-' * 60
                + '\n'
                + '                    测试结果摘要\n'
                + f'                    总测试数: {tests_run}\n'
                + f'                    通过测试数: {tests_passed}\n'
                + f'                    失败测试数: {tests_run - tests_passed}\n'
                + f'                    通过率: {(tests_passed / tests_run * 100):.2f}%\n'
                + '-' * 60
            )

        finally:
            # 清理测试环境
            self.teardown()

        # 返回测试是否全部通过
        return tests_run == tests_passed


async def test_async_client():
    """测试异步Redis客户端"""
    logger.info('\n' + '=' * 60)
    logger.info('异步Redis客户端测试')
    logger.info('=' * 60)

    try:
        # 创建异步客户端
        async_redis = create_redis_client('redis', async_client=True)

        # 测试基本操作
        await async_redis.set('async_test_key', 'async_test_value')
        value = await async_redis.get('async_test_key')
        logger.success(f'异步SET/GET测试成功: {value}')

        # 测试 Ping
        ping_result = await async_redis.ping()
        logger.success(f'异步Ping测试成功: {ping_result}')

        # 清理
        await async_redis.delete('async_test_key')

        # 关闭
        if hasattr(async_redis, 'aclose'):
            await async_redis.aclose()
        logger.success('异步客户端测试全部通过')
        return True
    except Exception as e:
        logger.error(f'异步客户端测试失败: {e!s}')
        import traceback

        traceback.print_exc()
        return False


def main():
    """主函数 - 运行所有测试"""
    # 运行同步客户端测试
    test_runner = TestRedisClient()
    sync_passed = test_runner.run_all_tests()

    # 运行异步客户端测试
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async_passed = loop.run_until_complete(test_async_client())
    loop.close()

    return 0 if (sync_passed and async_passed) else 1


if __name__ == '__main__':
    exit(main())
