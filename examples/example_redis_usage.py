# !/usr/bin/env python
"""
==============================================================
Description  : RedisManager 使用示例
Author       : sandorn sandorn@live.cn
Date         : 2025-10-23
FilePath     : /examples/example_redis_usage.py
Github       : https://github.com/sandorn/xtdbase

本示例展示如何使用 RedisManager 进行 Redis 操作:
    1. 基本的键值操作
    2. 哈希操作
    3. 列表操作
    4. 集合操作
    5. 有序集合操作
    6. 过期时间管理
    7. 管道操作
    8. 实际应用场景
==============================================================
"""

from __future__ import annotations

from xtdbase import create_redis_client


def example_1_basic_string_operations():
    """示例 1: 基本字符串操作"""
    print('\n' + '=' * 60)
    print('示例 1: 基本字符串操作')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 设置键值
        redis.set('name', 'Alice')
        redis.set('age', '25')
        print('\n✅ 设置键值成功')

        # 获取键值
        name = redis.get('name')
        age = redis.get('age')
        print(f'\nname: {name}')
        print(f'age: {age}')

        # 设置带过期时间的键值(秒)
        redis.set('temp_key', 'temp_value', ex=60)
        print('\n✅ 设置临时键(60秒后过期)')

        # 检查键是否存在
        exists = redis.exists('name')
        print(f'\n键 "name" 是否存在: {exists}')

        # 删除键
        redis.delete('age')
        print('✅ 删除键 "age"')

        # 自增操作
        redis.set('counter', '0')
        redis.incr('counter')
        redis.incr('counter', amount=5)
        counter = redis.get('counter')
        print(f'\n计数器值: {counter}')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_2_hash_operations():
    """示例 2: 哈希操作"""
    print('\n' + '=' * 60)
    print('示例 2: 哈希操作(Hash)')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 设置哈希字段
        redis.hset('user:1', 'name', 'Bob')
        redis.hset('user:1', 'email', 'bob@example.com')
        redis.hset('user:1', 'age', '30')
        print('\n✅ 设置用户信息')

        # 获取单个哈希字段
        name = redis.hget('user:1', 'name')
        print(f'\n用户名: {name}')

        # 获取所有哈希字段
        user_data = redis.hgetall('user:1')
        print(f'\n完整用户信息: {user_data}')

        # 批量设置哈希字段
        redis.hmset('user:2', {'name': 'Charlie', 'email': 'charlie@example.com', 'age': '35'})
        print('✅ 批量设置用户信息')

        # 检查哈希字段是否存在
        exists = redis.hexists('user:1', 'name')
        print(f'\nuser:1 的 name 字段是否存在: {exists}')

        # 删除哈希字段
        redis.hdel('user:1', 'age')
        print('✅ 删除 age 字段')

        # 获取所有哈希键
        keys = redis.hkeys('user:1')
        print(f'\nuser:1 的所有字段: {keys}')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_3_list_operations():
    """示例 3: 列表操作"""
    print('\n' + '=' * 60)
    print('示例 3: 列表操作(List)')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 从左侧推入元素
        redis.lpush('queue', 'task1')
        redis.lpush('queue', 'task2')
        redis.lpush('queue', 'task3')
        print('\n✅ 推入任务到队列')

        # 从右侧推入元素
        redis.rpush('queue', 'task4')
        print('✅ 从右侧推入任务')

        # 从左侧弹出元素
        task = redis.lpop('queue')
        print(f'\n弹出任务: {task}')

        # 从右侧弹出元素
        task = redis.rpop('queue')
        print(f'从右侧弹出任务: {task}')

        # 获取列表长度
        length = redis.llen('queue')
        print(f'\n队列长度: {length}')

        # 获取列表指定范围的元素
        tasks = redis.lrange('queue', 0, -1)
        print(f'队列中的所有任务: {tasks}')

        # 获取列表指定索引的元素
        task = redis.lindex('queue', 0)
        print(f'队列第一个任务: {task}')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_4_set_operations():
    """示例 4: 集合操作"""
    print('\n' + '=' * 60)
    print('示例 4: 集合操作(Set)')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 添加元素到集合
        redis.sadd('tags', 'python', 'redis', 'database')
        redis.sadd('tags', 'python')  # 重复元素会被忽略
        print('\n✅ 添加标签到集合')

        # 获取集合所有成员
        tags = redis.smembers('tags')
        print(f'\n所有标签: {tags}')

        # 检查元素是否在集合中
        exists = redis.sismember('tags', 'python')
        print(f'\n"python" 是否在集合中: {exists}')

        # 获取集合元素数量
        count = redis.scard('tags')
        print(f'标签数量: {count}')

        # 移除集合元素
        redis.srem('tags', 'database')
        print('✅ 移除 "database" 标签')

        # 集合操作：并集、交集、差集
        redis.sadd('tags:user1', 'python', 'java', 'go')
        redis.sadd('tags:user2', 'python', 'javascript', 'go')

        # 交集
        intersection = redis.sinter('tags:user1', 'tags:user2')
        print(f'\n共同标签(交集): {intersection}')

        # 并集
        union = redis.sunion('tags:user1', 'tags:user2')
        print(f'所有标签(并集): {union}')

        # 差集
        diff = redis.sdiff('tags:user1', 'tags:user2')
        print(f'user1 独有标签(差集): {diff}')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_5_sorted_set_operations():
    """示例 5: 有序集合操作"""
    print('\n' + '=' * 60)
    print('示例 5: 有序集合操作(Sorted Set)')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 添加元素到有序集合(带分数)
        redis.zadd('scores', {'Alice': 95, 'Bob': 87, 'Charlie': 92})
        print('\n✅ 添加学生成绩')

        # 获取有序集合成员数量
        count = redis.zcard('scores')
        print(f'\n学生数量: {count}')

        # 获取指定范围的元素(按分数升序)
        students = redis.zrange('scores', 0, -1, withscores=True)
        print(f'\n所有学生(升序): {students}')

        # 获取指定范围的元素(按分数降序)
        top_students = redis.zrevrange('scores', 0, 2, withscores=True)
        print(f'前3名学生(降序): {top_students}')

        # 获取成员的分数
        score = redis.zscore('scores', 'Alice')
        print(f'\nAlice 的分数: {score}')

        # 获取成员的排名(从0开始)
        rank = redis.zrank('scores', 'Bob')
        print(f'Bob 的排名(升序): {rank}')

        # 增加成员的分数
        redis.zincrby('scores', 5, 'Bob')
        print('✅ Bob 的分数 +5')

        # 按分数范围查询
        mid_range = redis.zrangebyscore('scores', 85, 95, withscores=True)
        print(f'\n分数在 85-95 之间的学生: {mid_range}')

        # 删除成员
        redis.zrem('scores', 'Charlie')
        print('✅ 移除 Charlie')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_6_expiration_management():
    """示例 6: 过期时间管理"""
    print('\n' + '=' * 60)
    print('示例 6: 过期时间管理')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 设置带过期时间的键
        redis.set('session:user1', 'token123', ex=3600)  # 1小时后过期
        print('\n✅ 设置会话(1小时后过期)')

        # 为已存在的键设置过期时间
        redis.set('cache_key', 'cached_data')
        redis.expire('cache_key', 300)  # 5分钟后过期
        print('✅ 为缓存设置过期时间(5分钟)')

        # 获取键的剩余生存时间(秒)
        ttl = redis.ttl('session:user1')
        print(f'\nsession:user1 剩余时间: {ttl} 秒')

        # 移除键的过期时间
        redis.persist('cache_key')
        print('✅ 移除 cache_key 的过期时间(永久保存)')

        # 设置指定时间戳过期
        import time

        expire_time = int(time.time()) + 600  # 10分钟后
        redis.expireat('temp_key', expire_time)

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_7_pipeline_operations():
    """示例 7: 管道操作(批量执行)"""
    print('\n' + '=' * 60)
    print('示例 7: 管道操作')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 使用管道批量执行命令
        pipe = redis.pipeline()

        # 添加多个命令到管道
        pipe.set('key1', 'value1')
        pipe.set('key2', 'value2')
        pipe.set('key3', 'value3')
        pipe.incr('counter')
        pipe.get('key1')

        # 一次性执行所有命令
        results = pipe.execute()
        print(f'\n✅ 管道执行结果: {results}')

        print("""
        管道的优势:
        - 减少网络往返次数
        - 提高批量操作性能
        - 原子性执行多个命令
        """)

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_8_practical_scenarios():
    """示例 8: 实际应用场景"""
    print('\n' + '=' * 60)
    print('示例 8: 实际应用场景')
    print('=' * 60)

    try:
        redis = create_redis_client('redis')

        # 场景 1: 缓存用户信息
        print('\n📝 场景 1: 缓存用户信息')
        user_id = 'user:1001'
        redis.hmset(f'cache:{user_id}', {'name': 'John Doe', 'email': 'john@example.com', 'level': 'premium'})
        redis.expire(f'cache:{user_id}', 1800)  # 30分钟缓存
        print('✅ 用户信息已缓存(30分钟)')

        # 场景 2: 计数器(页面访问统计)
        print('\n📝 场景 2: 页面访问统计')
        page_key = 'pageview:homepage'
        redis.incr(page_key)
        views = redis.get(page_key)
        print(f'✅ 首页访问次数: {views}')

        # 场景 3: 分布式锁
        print('\n📝 场景 3: 分布式锁')
        lock_key = 'lock:resource1'
        # 尝试获取锁(NX 表示不存在时才设置)
        acquired = redis.set(lock_key, 'locked', ex=10, nx=True)
        if acquired:
            print('✅ 获取锁成功')
            # 执行业务逻辑...
            redis.delete(lock_key)  # 释放锁
            print('✅ 释放锁')
        else:
            print('❌ 获取锁失败(资源被占用)')

        # 场景 4: 排行榜
        print('\n📝 场景 4: 游戏排行榜')
        leaderboard = 'game:leaderboard'
        redis.zadd(leaderboard, {'player1': 1500, 'player2': 2300, 'player3': 1800, 'player4': 2100})
        top3 = redis.zrevrange(leaderboard, 0, 2, withscores=True)
        print(f'✅ 前3名玩家: {top3}')

        # 场景 5: 消息队列
        print('\n📝 场景 5: 简单消息队列')
        queue = 'message:queue'
        redis.lpush(queue, 'message1', 'message2', 'message3')
        message = redis.rpop(queue)
        print(f'✅ 消费消息: {message}')

        # 场景 6: 限流(令牌桶)
        print('\n📝 场景 6: API 限流')
        rate_limit_key = 'ratelimit:api:user123'
        current = redis.incr(rate_limit_key)
        if current == 1:
            redis.expire(rate_limit_key, 60)  # 1分钟窗口
        if current <= 100:  # 每分钟最多100次请求
            print(f'✅ 请求通过({current}/100)')
        else:
            print(f'❌ 请求被限流({current}/100)')

    except Exception as e:
        print(f'❌ 操作失败: {e}')


def example_9_best_practices():
    """示例 9: 最佳实践"""
    print('\n' + '=' * 60)
    print('示例 9: Redis 使用最佳实践')
    print('=' * 60)

    print("""
    ✅ Redis 最佳实践建议:

    1. 键命名规范:
       ✓ 使用冒号分隔: "user:1001:profile"
       ✓ 使用有意义的前缀: "cache:", "session:", "lock:"
       ✓ 避免过长的键名
       ✗ 不要: "u1p", "data", "temp"

    2. 内存管理:
       ✓ 为临时数据设置过期时间
       ✓ 定期清理不需要的键
       ✓ 使用 Hash 存储对象(节省内存)
       ✗ 避免存储大对象(> 1MB)

    3. 性能优化:
       ✓ 使用管道批量操作
       ✓ 使用连接池
       ✓ 避免在循环中执行 Redis 命令
       ✗ 不要使用 keys * (生产环境)

    4. 数据持久化:
       ✓ RDB: 定期快照(适合备份)
       ✓ AOF: 命令日志(更安全)
       ✓ 混合持久化(推荐)

    5. 安全建议:
       ✓ 设置密码(requirepass)
       ✓ 绑定可信IP
       ✓ 禁用危险命令(如 FLUSHALL)
       ✓ 使用专用数据库编号

    6. 监控指标:
       - 内存使用率
       - 命中率
       - 连接数
       - 慢查询日志

    7. 常见场景:
       - 缓存: String, Hash
       - 计数器: String (INCR)
       - 队列: List
       - 去重: Set
       - 排行榜: Sorted Set
       - 分布式锁: String (SETNX)
       - 会话存储: Hash
    """)


def main():
    """主函数：运行所有示例"""
    print('\n' + '=' * 60)
    print('RedisManager 使用示例')
    print('=' * 60)

    print("""
    ⚠️  注意事项:
    1. 本示例需要 Redis 服务器正在运行
    2. 请先在 cfg.py 中配置好 Redis 连接信息
    3. 示例会在 Redis 中创建测试数据

    如需运行实际示例，请取消下面示例函数的注释。
    """)

    # 取消注释以运行示例
    example_1_basic_string_operations()
    example_2_hash_operations()
    example_3_list_operations()
    example_4_set_operations()
    example_5_sorted_set_operations()
    example_6_expiration_management()
    example_7_pipeline_operations()
    example_8_practical_scenarios()
    example_9_best_practices()

    print('\n' + '=' * 60)
    print('✅ 示例展示完成！')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
