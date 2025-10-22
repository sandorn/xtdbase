# Redis 客户端使用示例

本文档展示了 `xtdbase.redis_client` 模块的使用方法和测试示例。

## 文件说明

### test_redis_client.py

完整的 Redis 客户端测试套件，包含以下测试内容：

- **连接测试**
  - Ping 连接测试
  - 配置方式初始化

- **基本操作**
  - SET/GET/DELETE/EXISTS
  - 过期时间设置 (EXPIRE/TTL/PERSIST)
  - 计数器操作 (INCR/DECR/INCRBY/DECRBY)

- **数据结构操作**
  - Hash 操作 (HSET/HGET/HGETALL/HDEL)
  - List 操作 (LPUSH/RPUSH/LRANGE/LPOP/RPOP)
  - Set 操作 (SADD/SMEMBERS/SREM/SISMEMBER)

- **高级功能**
  - 上下文管理器
  - 异步客户端操作

## 运行测试

### 运行完整测试套件

```bash
python examples/test_redis_client.py
```

或使用 uv：

```bash
uv run python examples/test_redis_client.py
```

### 预期结果

```
------------------------------------------------------------
                    测试结果摘要
                    总测试数: 9
                    通过测试数: 9
                    失败测试数: 0
                    通过率: 100.00%
------------------------------------------------------------
```

## 快速使用示例

### 1. 配置方式连接（推荐）

```python
from xtdbase.redis_client import create_redis_client

# 使用默认配置
redis = create_redis_client('redis')

# 基本操作
redis.set('key', 'value')
value = redis.get('key')
print(value)  # b'value'

# 关闭连接
redis.close()
```

### 2. 直接参数方式连接

```python
from redis import Redis

redis = Redis(host='localhost', port=6379, db=0)

# 测试连接
if redis.ping():
    print('连接成功')

redis.close()
```

### 3. 使用上下文管理器

```python
from xtdbase.redis_client import RedisManager, create_redis_client
from xtdbase.cfg import DB_CFG

cfg = DB_CFG.redis.value[0]
manager = RedisManager(host=cfg['host'], port=cfg['port'], db=cfg['db'])
manager.client = create_redis_client('redis')

with manager:
    # 自动管理连接生命周期
    manager.client.set('context_key', 'context_value')
    value = manager.client.get('context_key')
    print(value)
# 连接自动关闭
```

### 4. Hash 操作示例

```python
redis = create_redis_client('redis')

# 设置 Hash 字段
redis.hset('user:1', 'name', '张三')
redis.hset('user:1', 'age', '25')
redis.hset('user:1', 'city', '北京')

# 获取单个字段
name = redis.hget('user:1', 'name')

# 获取所有字段
user_data = redis.hgetall('user:1')
print(user_data)

# 删除字段
redis.hdel('user:1', 'city')
```

### 5. List 操作示例

```python
redis = create_redis_client('redis')

# 从右侧插入
redis.rpush('queue', 'task1', 'task2', 'task3')

# 从左侧弹出
task = redis.lpop('queue')
print(task)  # b'task1'

# 获取列表范围
tasks = redis.lrange('queue', 0, -1)
print(tasks)  # [b'task2', b'task3']
```

### 6. Set 操作示例

```python
redis = create_redis_client('redis')

# 添加成员
redis.sadd('tags', 'python', 'redis', 'database')

# 获取所有成员
members = redis.smembers('tags')
print(members)

# 检查成员是否存在
if redis.sismember('tags', 'python'):
    print('python 存在于集合中')

# 删除成员
redis.srem('tags', 'database')
```

### 7. 异步客户端示例

```python
import asyncio
from xtdbase.redis_client import create_redis_client

async def async_example():
    # 创建异步客户端
    redis = create_redis_client('redis', async_client=True)
    
    # 异步操作
    await redis.set('async_key', 'async_value')
    value = await redis.get('async_key')
    print(value)
    
    # 测试连接
    ping_result = await redis.ping()
    print(f'Ping: {ping_result}')
    
    # 关闭连接
    await redis.aclose()

# 运行异步代码
asyncio.run(async_example())
```

### 8. 过期时间设置

```python
redis = create_redis_client('redis')

# 设置键值和过期时间（10秒后过期）
redis.set('temp_key', 'temp_value', ex=10)

# 检查剩余时间
ttl = redis.ttl('temp_key')
print(f'剩余时间: {ttl}秒')

# 移除过期时间
redis.persist('temp_key')
```

### 9. 计数器操作

```python
redis = create_redis_client('redis')

# 递增
count = redis.incr('visitor_count')
print(f'访问次数: {count}')

# 递增指定值
count = redis.incrby('visitor_count', 10)
print(f'访问次数: {count}')

# 递减
count = redis.decr('visitor_count')
print(f'访问次数: {count}')
```

## 注意事项

1. **Redis 配置**：确保在 `xtdbase/cfg.py` 中配置了正确的 Redis 连接信息
2. **Redis 服务**：确保 Redis 服务器正在运行
3. **依赖包**：确保已安装 `redis` 包

## 配置示例

在 `xtdbase/cfg.py` 中添加 Redis 配置：

```python
class DB_CFG(Enum):
    redis = ({'host': 'localhost', 'port': 6379, 'db': 0, 'type': 'redis'},)
```

## 更多信息

查看源码文档：`xtdbase/redis_client.py`

