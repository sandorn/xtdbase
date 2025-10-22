# AioMySQLPool 异步连接池使用指南

## 📖 简介

`AioMySQLPool` 是基于 `aiomysql` 的异步MySQL连接池封装类，提供标准化的数据库操作接口。

### 主要特性

- ✅ **标准化接口**: 方法命名遵循 Python DB-API 2.0 规范
- ✅ **连接池管理**: 自动管理连接池，支持最小/最大连接数配置
- ✅ **异步操作**: 完整的async/await支持
- ✅ **事务支持**: begin/commit/rollback确保数据一致性
- ✅ **上下文管理器**: 使用async with自动管理资源
- ✅ **异步迭代器**: 高效处理大量数据，避免内存溢出
- ✅ **连接健康检查**: ping方法检测连接可用性
- ✅ **向后兼容**: 旧接口仍可用，平滑迁移

---

## 🚀 快速开始

### 基本使用

```python
import asyncio
from xtdbase.aiomysqlpool import create_async_mysql_pool

async def main():
    # 使用上下文管理器（推荐）
    async with create_async_mysql_pool('default') as db:
        # 查询单条记录
        user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
        print(user)

asyncio.run(main())
```

### 创建连接池

```python
from xtdbase.aiomysqlpool import create_async_mysql_pool

# 方式1: 使用配置键（推荐）
db = create_async_mysql_pool('default')

# 方式2: 使用配置键 + 自定义参数
db = create_async_mysql_pool('default', minsize=5, maxsize=20)

# 方式3: 直接实例化（不推荐）
from xtdbase.aiomysqlpool import AioMySQLPool
db = AioMySQLPool(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    db='test_db'
)
```

---

## 📘 标准接口使用

### 查询操作

#### 1. fetchone() - 查询单条记录

```python
async with create_async_mysql_pool('default') as db:
    # 位置参数
    user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
    
    # 命名参数
    user = await db.fetchone(
        'SELECT * FROM users WHERE id = %(user_id)s',
        user_id=1
    )
    
    # 返回字典（使用DictCursor）
    if user:
        print(f"用户名: {user['username']}")
```

#### 2. fetchall() - 查询所有记录

```python
async with create_async_mysql_pool('default') as db:
    # 查询所有活跃用户
    users = await db.fetchall('SELECT * FROM users WHERE status = %s', 'active')
    
    for user in users:
        print(f"{user['id']}: {user['username']}")
```

**⚠️ 警告**: 大量数据时可能导致内存溢出，建议使用 `iterate()` 或 `fetchmany()`

#### 3. fetchmany() - 查询指定数量记录

```python
async with create_async_mysql_pool('default') as db:
    # 获取前10条记录
    users = await db.fetchmany('SELECT * FROM users', 10)
    
    # 分页查询
    page = 2
    page_size = 20
    offset = (page - 1) * page_size
    users = await db.fetchmany(
        'SELECT * FROM users LIMIT %s OFFSET %s',
        page_size,
        page_size,
        offset
    )
```

### 数据修改操作

#### execute() - INSERT/UPDATE/DELETE

```python
async with create_async_mysql_pool('default') as db:
    # 插入数据
    new_id = await db.execute(
        'INSERT INTO users(username, email) VALUES (%s, %s)',
        'alice',
        'alice@example.com'
    )
    print(f'新插入记录ID: {new_id}')
    
    # 更新数据
    affected = await db.execute(
        'UPDATE users SET email = %s WHERE username = %s',
        'newemail@example.com',
        'alice'
    )
    print(f'更新了 {affected} 条记录')
    
    # 删除数据
    affected = await db.execute(
        'DELETE FROM users WHERE username = %s',
        'alice'
    )
    print(f'删除了 {affected} 条记录')
```

---

## 🔒 事务操作

```python
async with create_async_mysql_pool('default') as db:
    conn = await db.begin()
    try:
        # 执行多个操作
        cur = await conn.cursor()
        
        # 转账示例
        await cur.execute(
            'UPDATE accounts SET balance = balance - 100 WHERE id = %s',
            1
        )
        await cur.execute(
            'UPDATE accounts SET balance = balance + 100 WHERE id = %s',
            2
        )
        
        # 提交事务
        await db.commit(conn)
        print('转账成功')
    except Exception as e:
        # 回滚事务
        await db.rollback(conn)
        print(f'转账失败，已回滚: {e}')
```

---

## 🔄 异步迭代器

处理大量数据时，使用 `iterate()` 避免内存溢出：

```python
async with create_async_mysql_pool('default') as db:
    total = 0
    
    # 逐行处理，不会一次性加载所有数据到内存
    async for row in db.iterate('SELECT * FROM large_table', batch_size=1000):
        # 处理每一行
        process(row)
        total += 1
    
    print(f'共处理 {total} 条记录')
```

**参数说明**:
- `batch_size`: 每批获取的记录数量，默认1000
- 较大的batch_size提升性能，但占用更多内存
- 较小的batch_size更节省内存，但增加查询次数

---

## 🔧 高级功能

### 连接健康检查

```python
db = create_async_mysql_pool('default')

# 检查连接是否正常
if await db.ping():
    print('数据库连接正常')
else:
    print('数据库连接失败')
```

### 连接池状态查询

```python
db = create_async_mysql_pool('default')
await db.init_pool()

# 获取连接池状态
if db.pool_size:
    current, maximum = db.pool_size
    print(f'当前连接数: {current}/{maximum}')
```

### 自定义游标操作

```python
async with create_async_mysql_pool('default') as db:
    # 获取连接和游标
    conn, cur = await db.get_cursor()
    
    try:
        # 执行自定义操作
        await cur.execute('SELECT * FROM users')
        result = await cur.fetchall()
        # ... 处理结果 ...
    finally:
        # 必须手动释放资源
        await db.close_cursor(conn, cur)
```

**⚠️ 警告**: 使用 `get_cursor()` 后必须调用 `close_cursor()`，否则会导致连接泄漏

---

## 🔄 向后兼容性

旧版本的方法名仍然可用，但建议迁移到标准接口：

| 旧接口 | 新接口（推荐） | 说明 |
|--------|---------------|------|
| `get()` | `fetchone()` | 查询单条记录 |
| `query()` | `fetchall()` | 查询所有记录 |
| `query_many()` | `fetchmany()` | 查询指定数量记录 |

```python
# 旧接口仍可用
async with create_async_mysql_pool('default') as db:
    user = await db.get('SELECT * FROM users WHERE id = %s', 1)
    users = await db.query('SELECT * FROM users')
    some_users = await db.query_many('SELECT * FROM users', 10)
```

---

## 📝 完整示例

### 示例1: 用户管理系统

```python
import asyncio
from xtdbase.aiomysqlpool import create_async_mysql_pool

async def create_user(db, username: str, email: str) -> int:
    """创建用户"""
    return await db.execute(
        'INSERT INTO users(username, email, created_at) VALUES (%s, %s, NOW())',
        username,
        email
    )

async def get_user_by_id(db, user_id: int):
    """根据ID获取用户"""
    return await db.fetchone('SELECT * FROM users WHERE id = %s', user_id)

async def list_active_users(db):
    """列出所有活跃用户"""
    return await db.fetchall(
        'SELECT * FROM users WHERE status = %s ORDER BY created_at DESC',
        'active'
    )

async def update_user_email(db, user_id: int, new_email: str) -> int:
    """更新用户邮箱"""
    return await db.execute(
        'UPDATE users SET email = %s WHERE id = %s',
        new_email,
        user_id
    )

async def delete_user(db, user_id: int) -> int:
    """删除用户"""
    return await db.execute('DELETE FROM users WHERE id = %s', user_id)

async def main():
    async with create_async_mysql_pool('default') as db:
        # 创建用户
        user_id = await create_user(db, 'alice', 'alice@example.com')
        print(f'创建用户成功，ID: {user_id}')
        
        # 获取用户
        user = await get_user_by_id(db, user_id)
        print(f'用户信息: {user}')
        
        # 更新邮箱
        affected = await update_user_email(db, user_id, 'newemail@example.com')
        print(f'更新成功，影响行数: {affected}')
        
        # 列出活跃用户
        users = await list_active_users(db)
        print(f'活跃用户数: {len(users)}')

if __name__ == '__main__':
    asyncio.run(main())
```

### 示例2: 批量数据处理

```python
async def process_large_dataset():
    """处理大量数据的示例"""
    async with create_async_mysql_pool('default') as db:
        processed = 0
        failed = 0
        
        # 使用迭代器逐行处理，避免内存溢出
        async for row in db.iterate(
            'SELECT * FROM large_table WHERE status = %s',
            'pending',
            batch_size=500  # 每批处理500条
        ):
            try:
                # 处理每一行数据
                await process_row(row)
                processed += 1
                
                # 每处理1000条输出进度
                if processed % 1000 == 0:
                    print(f'已处理 {processed} 条记录')
            except Exception as e:
                print(f'处理失败: {e}')
                failed += 1
        
        print(f'处理完成: 成功 {processed} 条，失败 {failed} 条')

asyncio.run(process_large_dataset())
```

### 示例3: 带事务的批量插入

```python
async def batch_insert_with_transaction():
    """事务批量插入示例"""
    users_data = [
        ('user1', 'user1@example.com'),
        ('user2', 'user2@example.com'),
        ('user3', 'user3@example.com'),
    ]
    
    async with create_async_mysql_pool('default') as db:
        conn = await db.begin()
        try:
            cur = await conn.cursor()
            
            # 批量插入
            for username, email in users_data:
                await cur.execute(
                    'INSERT INTO users(username, email) VALUES (%s, %s)',
                    (username, email)
                )
            
            # 提交事务
            await db.commit(conn)
            print(f'批量插入成功: {len(users_data)} 条记录')
        except Exception as e:
            # 回滚事务
            await db.rollback(conn)
            print(f'批量插入失败，已回滚: {e}')

asyncio.run(batch_insert_with_transaction())
```

---

## ⚙️ 配置说明

### 连接池参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host` | str | - | 数据库主机地址 |
| `port` | int | - | 数据库端口号 |
| `user` | str | - | 数据库用户名 |
| `password` | str | - | 数据库密码 |
| `db` | str | - | 数据库名称 |
| `minsize` | int | 1 | 连接池最小连接数 |
| `maxsize` | int | 10 | 连接池最大连接数 |
| `charset` | str | 'utf8mb4' | 数据库字符集 |
| `autocommit` | bool | True | 是否自动提交事务 |
| `pool_recycle` | int | -1 | 连接回收时间(秒)，-1表示不回收 |

### 推荐配置

```python
# 开发环境
db = create_async_mysql_pool('default', minsize=1, maxsize=5)

# 生产环境（高并发）
db = create_async_mysql_pool('default', minsize=10, maxsize=50)

# 生产环境（低并发）
db = create_async_mysql_pool('default', minsize=2, maxsize=10)
```

---

## 🧪 运行测试

```bash
# 运行完整测试套件
python examples/test_aiomysqlpool.py

# 测试覆盖内容：
# - 连接健康检查 (ping)
# - fetchone/fetchall/fetchmany查询
# - execute插入/更新
# - 事务操作 (begin/commit/rollback)
# - 异步迭代器 (iterate)
# - 向后兼容性 (get/query/query_many)
# - 上下文管理器
```

---

## ⚠️ 注意事项

### 1. 内存管理

- ❌ **避免**: `fetchall()` 查询百万级数据
- ✅ **推荐**: 使用 `iterate()` 或 `fetchmany()` 分批处理

### 2. 事务管理

- ❌ **错误**: 忘记调用 `commit()` 或 `rollback()`
- ✅ **正确**: 始终在 try-except-finally 中管理事务

```python
# 错误示例
conn = await db.begin()
await cur.execute(...)  # 如果这里出错，连接不会释放

# 正确示例
conn = await db.begin()
try:
    await cur.execute(...)
    await db.commit(conn)
except Exception:
    await db.rollback(conn)
    raise
```

### 3. 资源释放

- ✅ **推荐**: 使用 `async with` 自动管理资源
- ⚠️ **警告**: 手动管理需要确保调用 `close()`

```python
# 推荐方式
async with create_async_mysql_pool('default') as db:
    # ... 操作 ...
    # 自动关闭连接池

# 手动管理（需要确保关闭）
db = create_async_mysql_pool('default')
try:
    # ... 操作 ...
finally:
    await db.close()
```

### 4. 并发控制

连接池的 `maxsize` 应该根据实际并发需求设置：

- 太小：高并发时等待连接，性能下降
- 太大：占用数据库资源，可能达到数据库连接上限

---

## 📊 性能优化建议

### 1. 合理设置连接池大小

```python
# 根据并发请求数设置
# 规则: maxsize = 并发请求数 * 1.2
db = create_async_mysql_pool('default', minsize=5, maxsize=20)
```

### 2. 使用批量操作

```python
# ❌ 低效: 多次单条插入
for user in users:
    await db.execute('INSERT INTO users(name) VALUES (%s)', user)

# ✅ 高效: 批量插入
async with db.begin() as conn:
    cur = await conn.cursor()
    for user in users:
        await cur.execute('INSERT INTO users(name) VALUES (%s)', (user,))
    await db.commit(conn)
```

### 3. 使用迭代器处理大数据

```python
# ❌ 低效: 一次性加载所有数据
users = await db.fetchall('SELECT * FROM large_table')  # 可能OOM

# ✅ 高效: 迭代处理
async for user in db.iterate('SELECT * FROM large_table', batch_size=1000):
    process(user)
```

---

## 📚 相关文档

- [aiomysql官方文档](https://aiomysql.readthedocs.io/)
- [Python DB-API 2.0规范](https://www.python.org/dev/peps/pep-0249/)
- [MySQL官方文档](https://dev.mysql.com/doc/)

---

## 🤝 获取帮助

如遇问题，请检查：

1. 数据库连接配置是否正确 (cfg.py中的DB_CFG)
2. 数据库服务是否运行
3. 表结构是否存在
4. 网络连接是否正常

---

**更新时间**: 2025-10-22  
**版本**: v2.0  
**作者**: sandorn

