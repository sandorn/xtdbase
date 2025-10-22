# SqlTwisted 异步数据库操作使用示例

本文档展示了 `xtdbase.sqltwisted` 模块的使用方法和测试示例。

## 重要更新：支持同步获取结果！

现在所有方法都支持 `sync=True` 参数，可以直接获取结果：

```python
# 同步方式（新增功能）
result = db.perform_query('SELECT * FROM users', sync=True)
affected = db.insert(data, 'users', sync=True)
affected = db.update(new_data, condition, 'users', sync=True)

# 异步方式（原有功能）
d = db.perform_query('SELECT * FROM users')
d.addCallback(lambda results: print(results))
```

## 文件说明

### test_sqltwisted.py

完整的 SqlTwisted 测试套件，基于 Twisted 框架的异步数据库操作，包含以下测试内容：

-   **查询操作**

    -   perform_query 方法测试
    -   query 方法测试
    -   链式查询操作

-   **数据操作**

    -   插入单条数据
    -   批量插入数据
    -   更新数据

-   **高级功能**
    -   链式操作（查询 → 更新 → 再查询）
    -   错误处理机制
    -   Deferred 回调链

## 运行测试

### 运行完整测试套件

```bash
python examples/test_sqltwisted.py
```

或使用 uv：

```bash
uv run python examples/test_sqltwisted.py
```

### 预期结果

```
------------------------------------------------------------
                    测试结果摘要
                    总测试数: 7
                    通过测试数: 7
                    失败测试数: 0
                    通过率: 100.00%
------------------------------------------------------------
```

## 快速使用示例

### 0. 同步方式使用（新增，推荐用于简单脚本）

```python
import threading
import time
from twisted.internet import reactor
from xtdbase.sqltwisted import create_sqltwisted

# 创建数据库实例
db = create_sqltwisted('default')

# 启动reactor在后台线程（仅需一次）
reactor_thread = threading.Thread(
    target=reactor.run,
    kwargs={'installSignalHandlers': False}
)
reactor_thread.daemon = True
reactor_thread.start()
time.sleep(0.5)  # 等待reactor启动

# 直接获取结果（sync=True）
result = db.perform_query('SELECT VERSION()', sync=True)
print(f'数据库版本: {result}')

# 插入数据
data = {'name': '张三', 'age': 25}
affected = db.insert(data, 'users', sync=True)
print(f'插入成功,影响行数: {affected}')

# 更新数据
new_data = {'age': 26}
condition = {'name': '张三'}
affected = db.update(new_data, condition, 'users', sync=True)
print(f'更新成功,影响行数: {affected}')

db.close()
```

**完整示例**: `examples/example_sync_usage.py`

### 1. 异步方式（适合复杂应用）

```python
from twisted.internet import reactor
from xtdbase.sqltwisted import create_sqltwisted

# 使用默认配置
db = create_sqltwisted('default')

# 执行查询
sql = 'SELECT * FROM users LIMIT 10'
d = db.perform_query(sql)

# 添加回调处理结果
def on_success(results):
    print(f'查询到 {len(results)} 条记录')
    print(results)
    db.close()
    reactor.stop()

d.addCallback(on_success)

# 启动事件循环
reactor.run()
```

### 2. 直接参数方式连接

```python
from xtdbase.sqltwisted import SqlTwisted

db = SqlTwisted(
    host='localhost',
    port=3306,
    user='your_user',
    password='your_password',
    db='your_database',
    tablename='your_table'
)

# 执行操作...
```

### 3. 插入数据

```python
db = create_sqltwisted('default', 'users')

# 准备数据
data = {
    'name': '张三',
    'age': 25,
    'email': 'zhangsan@example.com'
}

# 执行插入
d = db.insert(data, 'users')

# 处理结果
def on_insert(affected_rows):
    print(f'插入成功,影响行数: {affected_rows}')
    db.close()
    reactor.stop()

d.addCallback(on_insert)
reactor.run()
```

### 4. 更新数据

```python
db = create_sqltwisted('default', 'users')

# 更新数据和条件
new_data = {'age': 26, 'email': 'zhangsan_new@example.com'}
condition = {'name': '张三'}

# 执行更新
d = db.update(new_data, condition, 'users')

# 处理结果
def on_update(affected_rows):
    print(f'更新成功,影响行数: {affected_rows}')
    db.close()
    reactor.stop()

d.addCallback(on_update)
reactor.run()
```

### 5. 链式操作示例

```python
db = create_sqltwisted('default', 'users')

def query_first():
    """第一步：查询"""
    sql = 'SELECT * FROM users WHERE id = 1'
    return db.perform_query(sql)

def update_next(results):
    """第二步：更新"""
    print(f'查询结果: {results}')
    new_data = {'email': 'updated@example.com'}
    condition = {'id': 1}
    return db.update(new_data, condition, 'users')

def query_again(affected_rows):
    """第三步：再次查询验证"""
    print(f'更新行数: {affected_rows}')
    sql = 'SELECT * FROM users WHERE id = 1'
    return db.perform_query(sql)

def final_result(results):
    """最后：处理最终结果"""
    print(f'最终结果: {results}')
    db.close()
    reactor.stop()

# 链式调用
d = query_first()
d.addCallback(update_next)
d.addCallback(query_again)
d.addCallback(final_result)

reactor.run()
```

### 6. 错误处理示例

```python
db = create_sqltwisted('default')

sql = 'SELECT * FROM users'
d = db.perform_query(sql)

# 成功回调
def on_success(results):
    print(f'查询成功: {len(results)} 条记录')
    return results

# 错误回调
def on_error(failure):
    print(f'查询失败: {failure.value}')
    # 返回空列表作为默认值
    return []

# 最终处理
def final_process(results):
    print(f'最终处理: {results}')
    db.close()
    reactor.stop()

d.addCallback(on_success)
d.addErrback(on_error)
d.addCallback(final_process)

reactor.run()
```

### 7. 批量插入示例

```python
db = create_sqltwisted('default', 'users')

# 准备批量数据
users = [
    {'name': '张三', 'age': 25, 'email': 'zhangsan@example.com'},
    {'name': '李四', 'age': 30, 'email': 'lisi@example.com'},
    {'name': '王五', 'age': 28, 'email': 'wangwu@example.com'},
]

def insert_batch(index=0):
    """递归插入"""
    if index >= len(users):
        print(f'批量插入完成,共 {len(users)} 条')
        db.close()
        reactor.stop()
        return

    data = users[index]
    d = db.insert(data, 'users')
    d.addCallback(lambda _: insert_batch(index + 1))

insert_batch()
reactor.run()
```

### 8. 处理回调结果

```python
db = create_sqltwisted('default')

sql = 'SELECT * FROM users LIMIT 10'
d = db.perform_query(sql)

# 多个回调处理
def process_results(results):
    """处理查询结果"""
    print(f'查询到 {len(results)} 条记录')
    # 进行数据转换、过滤等操作
    filtered = [r for r in results if r.get('age', 0) > 25]
    return filtered

def format_results(results):
    """格式化结果"""
    for row in results:
        print(f"用户: {row.get('name')}, 年龄: {row.get('age')}")
    return results

def cleanup(_):
    """清理"""
    db.close()
    reactor.stop()

# 链式添加回调
d.addCallback(process_results)
d.addCallback(format_results)
d.addCallback(cleanup)

reactor.run()
```

## Twisted Deferred 机制说明

SqlTwisted 所有异步方法都返回 `Deferred` 对象，这是 Twisted 框架的核心概念：

### Deferred 基本使用

```python
# 1. 获取 Deferred 对象
d = db.perform_query('SELECT * FROM users')

# 2. 添加成功回调
d.addCallback(lambda results: print(results))

# 3. 添加错误回调
d.addErrback(lambda failure: print(f'错误: {failure.value}'))

# 4. 可以链式添加多个回调
d.addCallback(process_data)
d.addCallback(save_to_file)
d.addCallback(send_notification)
```

### Deferred 链式调用规则

1. **回调返回值**：每个回调的返回值会传递给下一个回调
2. **错误传播**：如果某个回调抛出异常，会触发错误回调
3. **回调顺序**：回调按照添加顺序执行

## 同步模式 vs 异步模式

### 同步模式（sync=True）

**优点：**

-   代码简单直观，类似传统数据库操作
-   直接返回结果，无需回调
-   适合简单脚本和快速验证

**缺点：**

-   会阻塞等待结果
-   需要在后台线程运行 reactor
-   不适合高并发场景

**适用场景：**

-   简单脚本
-   数据迁移工具
-   测试代码
-   低并发应用

### 异步模式（默认）

**优点：**

-   真正的异步非阻塞
-   高并发性能好
-   可以链式调用多个操作

**缺点：**

-   需要理解 Deferred 机制
-   代码相对复杂
-   需要管理回调链

**适用场景：**

-   Web 应用
-   高并发场景
-   需要链式操作
-   Twisted 框架应用

## 注意事项

1. **数据库配置**：确保在 `xtdbase/cfg.py` 中配置了正确的数据库连接信息
2. **Reactor 循环**：
    - 异步模式：需要调用 `reactor.run()` 启动事件循环
    - 同步模式：需要在后台线程运行 reactor
3. **超时设置**：同步模式可以设置 `timeout` 参数（默认 30 秒）
4. **错误处理**：
    - 同步模式：使用 try-except 捕获异常
    - 异步模式：使用 addErrback 处理错误
5. **资源清理**：使用完毕后记得关闭数据库连接

## 配置示例

在 `xtdbase/cfg.py` 中添加数据库配置：

```python
class DB_CFG(Enum):
    default = ({'host': 'localhost', 'port': 3306, 'user': 'root',
                'password': 'password', 'db': 'test', 'type': 'mysql'},)
```

## 更多信息

查看源码文档：`xtdbase/sqltwisted.py`

## 常见问题

### Q: reactor 循环无法停止？

A: 确保在所有操作完成后调用 `reactor.stop()`，通常在最后一个回调中调用。

### Q: 如何处理多个并发查询？

A: 可以创建多个 Deferred 对象并使用 `defer.DeferredList` 来处理：

```python
from twisted.internet import defer

d1 = db.perform_query('SELECT * FROM users')
d2 = db.perform_query('SELECT * FROM orders')

dl = defer.DeferredList([d1, d2])
dl.addCallback(lambda results: print(results))
```

### Q: 如何在回调中访问外部变量？

A: 使用闭包或者将变量作为回调参数传递：

```python
user_id = 123

def update_user(results):
    # 可以访问外部的 user_id
    return db.update({'status': 'active'}, {'id': user_id}, 'users')

d = db.perform_query('SELECT * FROM users')
d.addCallback(update_user)
```

### Q: 同步模式和异步模式可以混用吗？

A: 可以，但要确保 reactor 在运行：

```python
# 混用示例
result1 = db.query('SELECT * FROM users', sync=True)  # 同步
d = db.insert(data, 'users')  # 异步
d.addCallback(lambda r: print(f'异步插入完成: {r}'))
result2 = db.query('SELECT * FROM orders', sync=True)  # 同步
```

### Q: 同步模式下如何设置超时时间？

A: 使用 `timeout` 参数：

```python
try:
    result = db.perform_query('SELECT * FROM large_table', sync=True, timeout=60.0)
except TimeoutError:
    print('查询超时（60秒）')
```
