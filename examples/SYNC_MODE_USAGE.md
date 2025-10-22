# SqlTwisted 同步模式使用指南

## 功能概述

为 `SqlTwisted` 添加了同步获取结果的功能，现在可以通过 `sync=True` 参数直接获取操作结果，无需手动处理 Deferred 回调。

## 快速开始

### 基本用法

```python
from xtdbase.sqltwisted import create_sqltwisted

# 创建数据库实例
db = create_sqltwisted('default')

# 直接获取结果（同步方式） - reactor会自动启动！
result = db.perform_query('SELECT VERSION()', sync=True)
print(f'数据库版本: {result}')

# 插入数据并获取影响行数
data = {'name': '张三', 'age': 25}
affected = db.insert(data, 'users', sync=True)
print(f'插入成功,影响行数: {affected}')

# 更新数据并获取影响行数
new_data = {'age': 26}
condition = {'name': '张三'}
affected = db.update(new_data, condition, 'users', sync=True)
print(f'更新成功,影响行数: {affected}')

db.close()
```

## API 参考

### perform_query(query, sync=False, timeout=30.0)

执行 SQL 查询语句

**参数:**

-   `query` (str): SQL 查询语句
-   `sync` (bool): 是否同步等待结果，默认 False
-   `timeout` (float): 同步模式下的超时时间（秒），默认 30 秒

**返回:**

-   异步模式: `Deferred[list[dict[str, Any]]]`
-   同步模式: `list[dict[str, Any]]`

**示例:**

```python
# 异步方式
d = db.perform_query('SELECT * FROM users')
d.addCallback(lambda results: print(results))

# 同步方式
results = db.perform_query('SELECT * FROM users', sync=True)
print(results)

# 设置超时
results = db.perform_query('SELECT * FROM large_table', sync=True, timeout=60.0)
```

### query(sql, sync=False, timeout=30.0)

执行 SQL 查询并处理结果

**参数:**

-   `sql` (str): SQL 查询语句
-   `sync` (bool): 是否同步等待结果，默认 False
-   `timeout` (float): 同步模式下的超时时间（秒），默认 30 秒

**返回:**

-   异步模式: `Deferred[list[dict[str, Any]]]`
-   同步模式: `list[dict[str, Any]]`

### insert(item, tablename=None, sync=False, timeout=30.0)

插入数据到指定表

**参数:**

-   `item` (dict): 要插入的数据字典
-   `tablename` (str | None): 目标数据表名
-   `sync` (bool): 是否同步等待结果，默认 False
-   `timeout` (float): 同步模式下的超时时间（秒），默认 30 秒

**返回:**

-   异步模式: `Deferred[int]`
-   同步模式: `int` (受影响行数)

**示例:**

```python
# 异步方式
data = {'name': '李四', 'age': 30}
d = db.insert(data, 'users')
d.addCallback(lambda affected: print(f'影响行数: {affected}'))

# 同步方式
data = {'name': '李四', 'age': 30}
affected = db.insert(data, 'users', sync=True)
print(f'影响行数: {affected}')
```

### update(item, condition, tablename=None, sync=False, timeout=30.0)

更新指定表中的数据

**参数:**

-   `item` (dict): 要更新的数据字典
-   `condition` (dict): 更新条件字典
-   `tablename` (str | None): 目标数据表名
-   `sync` (bool): 是否同步等待结果，默认 False
-   `timeout` (float): 同步模式下的超时时间（秒），默认 30 秒

**返回:**

-   异步模式: `Deferred[int]`
-   同步模式: `int` (受影响行数)

**示例:**

```python
# 异步方式
new_data = {'age': 31}
condition = {'name': '李四'}
d = db.update(new_data, condition, 'users')
d.addCallback(lambda affected: print(f'影响行数: {affected}'))

# 同步方式
new_data = {'age': 31}
condition = {'name': '李四'}
affected = db.update(new_data, condition, 'users', sync=True)
print(f'影响行数: {affected}')
```

## 使用场景对比

### 同步模式 (sync=True)

**适用场景:**

-   简单脚本和工具
-   数据迁移任务
-   测试代码
-   低并发应用
-   需要按顺序执行多个操作

**优点:**

-   代码简单直观
-   无需理解 Deferred 机制
-   类似传统数据库操作
-   调试方便

**缺点:**

-   会阻塞等待结果
-   需要在后台线程运行 reactor
-   不适合高并发场景
-   无法充分利用异步优势

### 异步模式 (默认)

**适用场景:**

-   Web 应用
-   高并发服务
-   需要链式操作
-   Twisted 框架应用
-   需要并发执行多个查询

**优点:**

-   真正的异步非阻塞
-   高并发性能好
-   可以链式调用
-   充分利用 Twisted 优势

**缺点:**

-   需要理解 Deferred
-   代码相对复杂
-   需要管理回调链
-   学习曲线陡峭

## 错误处理

### 同步模式

```python
try:
    result = db.perform_query('SELECT * FROM users', sync=True, timeout=10.0)
    print(result)
except TimeoutError:
    print('查询超时')
except Exception as e:
    print(f'查询失败: {e}')
```

### 异步模式

```python
def on_success(results):
    print(results)

def on_error(failure):
    print(f'查询失败: {failure}')

d = db.perform_query('SELECT * FROM users')
d.addCallbacks(on_success, on_error)
```

## 混合使用

同步和异步模式可以混合使用（reactor 会自动管理）：

```python
from xtdbase.sqltwisted import create_sqltwisted

# 创建数据库实例
db = create_sqltwisted('default')

# 同步查询 - reactor自动启动
users = db.query('SELECT * FROM users', sync=True)

# 异步插入
d = db.insert({'name': '王五', 'age': 28}, 'users')
d.addCallback(lambda r: print(f'异步插入完成: {r}'))

# 同步更新
affected = db.update({'age': 29}, {'name': '王五'}, 'users', sync=True)
print(f'同步更新影响行数: {affected}')
```

## 完整示例

运行完整的同步模式示例：

```bash
uv run examples/example_sync_usage.py
```

查看输出：

```
============================================================
SqlTwisted 同步方式使用示例
============================================================

【示例1】查询数据库版本
✅ 数据库版本: ('9.4.0',)

【示例2】执行查询
✅ 查询结果: ((2,),)

【示例5】设置超时时间
✅ 查询完成(5秒超时内)

============================================================
✅ 所有示例执行完成!
============================================================
```

## 注意事项

1. **Reactor 管理**: ✨ reactor 会自动在后台线程启动，无需手动管理！
2. **超时设置**: 默认 30 秒，可根据实际情况调整
3. **错误处理**: 同步模式使用 try-except，异步模式使用 addErrback
4. **性能考虑**: 高并发场景建议使用异步模式
5. **资源清理**: 使用完毕记得调用 `db.close()`
6. **首次调用**: 第一次调用 sync=True 时会启动 reactor（约 0.5 秒）

## 技术实现

### \_wait_for_result 方法

内部使用 `threading.Event` 来等待 Deferred 完成：

```python
def _wait_for_result(self, deferred: Deferred[Any], timeout: float = 30.0) -> Any:
    """等待Deferred完成并返回结果"""
    result_container = {'result': None, 'error': None, 'done': False}
    event = threading.Event()

    def on_success(result):
        result_container['result'] = result
        result_container['done'] = True
        event.set()
        return result

    def on_error(failure):
        result_container['error'] = failure
        result_container['done'] = True
        event.set()
        return failure

    deferred.addCallback(on_success)
    deferred.addErrback(on_error)

    # 等待结果
    if not event.wait(timeout):
        raise TimeoutError(f'操作超时({timeout}秒)')

    # 检查是否有错误
    if result_container['error'] is not None:
        raise result_container['error'].value

    return result_container['result']
```

## 更多资源

-   **完整文档**: `examples/README_sqltwisted.md`
-   **测试示例**: `examples/test_sqltwisted.py`
-   **同步示例**: `examples/example_sync_usage.py`
-   **源代码**: `xtdbase/sqltwisted.py`

## 版本历史

-   **v1.1.0** (2025-10-21)
    -   新增同步模式支持 (sync=True)
    -   新增超时设置 (timeout 参数)
    -   新增完整的同步使用示例
    -   更新文档和测试用例
