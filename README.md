# xtdbase

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

> **扩展数据库与数据处理工具库** - 提供 Excel 操作、MySQL 连接池、Redis 客户端等统一且符合标准的接口

## 📋 目录

-   [特性](#-特性)
-   [安装](#-安装)
-   [快速开始](#-快速开始)
-   [核心模块](#-核心模块)
    -   [Excel 操作](#1-excel-操作)
    -   [MySQL 操作](#2-mysql-操作)
    -   [Redis 操作](#3-redis-操作)
    -   [SQL 工具](#4-sql-工具)
-   [高级用法](#-高级用法)
-   [示例代码](#-示例代码)
-   [配置说明](#-配置说明)
-   [最佳实践](#-最佳实践)
-   [常见问题](#-常见问题)
-   [开发路线](#-开发路线)
-   [贡献指南](#-贡献指南)
-   [许可证](#-许可证)

## ✨ 特性

### 核心优势

-   **🎯 标准化接口**: 所有数据库操作完全符合 Python DB-API 2.0 规范
-   **⚡ 高性能**: 基于 aiomysql 的异步连接池,支持高并发场景
-   **🔄 灵活切换**: 同时支持异步和同步两种调用方式
-   **📊 Excel 增强**: 统一的 Excel 操作接口,支持细粒度单元格操作和批量数据处理
-   **🛡️ 类型安全**: 完整的类型注解,支持 Python 3.13+ 现代类型系统
-   **🔧 易于配置**: 集中式配置管理,支持多环境切换
-   **📝 文档完善**: 详细的 API 文档和丰富的示例代码

### 技术特点

-   连接池自动管理(最小/最大连接数、自动回收)
-   事务支持(begin/commit/rollback)
-   异步迭代器(大数据量内存友好处理)
-   连接健康检查(自动重连、ping 检测)
-   SQL 注入防护(参数化查询)
-   统一异常处理和日志记录

## 📦 安装

### 基础安装 (仅 Excel 功能)

```bash
pip install xtdbase
```

### 带 MySQL 支持

```bash
pip install xtdbase[mysql]
```

### 带 Redis 支持

```bash
pip install xtdbase[redis]
```

### 完整安装 (所有功能)

```bash
pip install xtdbase[all]
```

### 从源码安装

```bash
git clone https://github.com/sandorn/xtdbase.git
cd xtdbase
pip install -e ".[all]"
```

### 依赖说明

**核心依赖** (自动安装):

-   `openpyxl>=3.1.5` - Excel 文件操作
-   `pandas>=2.3.3` - 数据处理和分析
-   `pydantic>=2.12.3` - 数据验证和模型
-   `xtlog>=0.1.9` - 统一日志工具

**可选依赖** (按需安装):

-   `[mysql]` - MySQL 数据库支持
    -   `aiomysql>=0.2.0` - 异步 MySQL 驱动
    -   `pymysql>=1.1.2` - MySQL 连接器
-   `[redis]` - Redis 缓存支持
    -   `redis>=6.4.0` - Redis 客户端
-   `[crypto]` - 加密功能支持
    -   `cryptography>=44.0.0` - 加密库
-   `[test]` - 测试工具
    -   `pytest>=7.0.0`
    -   `pytest-asyncio>=0.21.0`
-   `[all]` - 包含上述所有可选依赖

## 🚀 快速开始

### Excel 操作

```python
from xtdbase import Excel

# 1. 读取 Excel 文件
with Excel('data.xlsx') as excel:
    # 读取所有数据
    data = excel.read_all()

    # 读取指定单元格
    value = excel.read_cell('A1')

    # 写入数据
    excel.write_cell('B1', 'Hello')
    excel.append([['Row1', 'Data1'], ['Row2', 'Data2']])

# 2. 批量数据处理
data = [
    {'name': 'Alice', 'age': 25},
    {'name': 'Bob', 'age': 30}
]
Excel.list_to_excel('output.xlsx', data)
```

### 异步 MySQL 连接池

```python
import asyncio
from xtdbase import create_mysql_pool

async def main():
    # 使用上下文管理器(推荐)
    async with create_mysql_pool('default') as db:
        # 查询单条记录
        user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)

        # 查询所有记录
        users = await db.fetchall('SELECT * FROM users LIMIT 10')

        # 执行插入/更新
        affected = await db.execute(
            'INSERT INTO users(name, email) VALUES (%s, %s)',
            'Alice',
            'alice@example.com'
        )

        # 大数据量迭代(内存友好)
        async for row in db.iterate('SELECT * FROM large_table'):
            process_row(row)

asyncio.run(main())
```

### 同步 MySQL 连接池

```python
from xtdbase import create_sync_mysql_pool

# 创建连接池
db = create_sync_mysql_pool('default')

# 查询操作
users = db.fetchall('SELECT * FROM users LIMIT 10', ())
user = db.fetchone('SELECT * FROM users WHERE id = %s', (1,))

# 执行操作
affected = db.execute('INSERT INTO users(name) VALUES (%s)', ('Alice',))

# 关闭连接池
db.close()
```

### Redis 操作

```python
from xtdbase import create_redis_client

# 创建 Redis 客户端
redis = create_redis_client('default')

# 基本操作
redis.set('key', 'value', ex=3600)  # 设置带过期时间
value = redis.get('key')

# 哈希操作
redis.hset('user:1', 'name', 'Alice')
name = redis.hget('user:1', 'name')
```

## 📚 核心模块

### 1. Excel 操作

#### `Excel` 类

统一的 Excel 操作接口,支持两种工作模式:

**实例模式** (基于 openpyxl):

-   细粒度单元格操作
-   工作表管理
-   支持上下文管理器

**类方法模式** (基于 pandas):

-   批量数据处理
-   多文件合并
-   高性能读写

```python
from xtdbase import Excel, ColumnMapping

# 实例模式 - 细粒度操作
with Excel('data.xlsx') as excel:
    # 创建/切换工作表
    excel.create_sheet('NewSheet')
    excel._switch_sheet('NewSheet')

    # 单元格操作
    excel.write_cell('A1', 'Header')
    value = excel.read_cell('A1')

    # 批量写入
    excel.write_cells([
        {'row': 1, 'col': 1, 'value': 'Name'},
        {'row': 1, 'col': 2, 'value': 'Age'}
    ])

    # 迭代读取(内存友好)
    for row_dict in excel.iter_rows_dict():
        print(row_dict)

# 类方法模式 - 批量处理
data = [{'name': 'Alice', 'age': 25}, {'name': 'Bob', 'age': 30}]

# 简单导出
Excel.list_to_excel('output.xlsx', data)

# 自定义列映射
mappings = [
    ColumnMapping(column_name='name', column_alias='姓名', width=15),
    ColumnMapping(column_name='age', column_alias='年龄', width=10)
]
Excel.list_to_excel('output.xlsx', data, mappings)

# 多工作表导出
from xtdbase import DataCollect, SheetMapping

sheet_data = DataCollect(
    sheet_list=[
        SheetMapping(sheet_name='用户', data=users_data),
        SheetMapping(sheet_name='订单', data=orders_data)
    ]
)
Excel.multi_sheet_write('report.xlsx', sheet_data)

# 合并多个 Excel 文件
Excel.merge_excel_files(
    output_file='merged.xlsx',
    input_files=['file1.xlsx', 'file2.xlsx']
)
```

#### 数据模型

```python
from xtdbase import ColumnMapping, SheetMapping, DataCollect

# 列映射配置
column = ColumnMapping(
    column_name='user_id',      # 原始列名
    column_alias='用户ID',       # 显示别名
    width=15,                    # 列宽
    is_merge=False               # 是否合并相同值单元格
)

# 工作表映射
sheet = SheetMapping(
    sheet_name='Sheet1',         # 工作表名称
    data=[{...}, {...}],         # 数据列表
    mappings=[column1, column2]  # 列映射配置
)

# 多工作表数据集合
data_collect = DataCollect(
    sheet_list=[sheet1, sheet2]
)
```

### 2. MySQL 操作

#### 2.1 `MySQL` - 单连接类

符合 DB-API 2.0 规范的 MySQL 连接类,适用于简单场景:

```python
from xtdbase import create_mysql_connection

# 创建连接
db = create_mysql_connection('default')

# 查询操作
user = db.fetchone('SELECT * FROM users WHERE id = %s', (1,))
users = db.fetchall('SELECT * FROM users LIMIT 10')

# 执行操作
affected = db.execute('INSERT INTO users(name) VALUES (%s)', ('Alice',))

# 事务操作
db.begin()
try:
    db.execute('UPDATE users SET status = %s WHERE id = %s', (1, 100))
    db.commit()
except Exception:
    db.rollback()

# 关闭连接
db.close()
```

#### 2.2 `MySQLPool` - 异步连接池

高性能异步 MySQL 连接池,完全符合 DB-API 2.0:

```python
import asyncio
from xtdbase import create_mysql_pool

async def main():
    async with create_mysql_pool('default') as db:
        # 标准查询方法
        user = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
        users = await db.fetchall('SELECT * FROM users')
        some_users = await db.fetchmany('SELECT * FROM users', size=10)

        # 执行 INSERT/UPDATE/DELETE
        last_id = await db.execute(
            'INSERT INTO users(name, email) VALUES (%s, %s)',
            'Alice',
            'alice@example.com'
        )

        # 事务操作
        conn = await db.begin()
        try:
            cursor = await conn.cursor()
            await cursor.execute('UPDATE accounts SET balance = balance - 100 WHERE id = 1')
            await cursor.execute('UPDATE accounts SET balance = balance + 100 WHERE id = 2')
            await db.commit(conn)
        except Exception:
            await db.rollback(conn)

        # 大数据量迭代(内存友好)
        async for row in db.iterate('SELECT * FROM large_table', batch_size=1000):
            await process_row(row)

        # 连接池状态
        size, maxsize = db.pool_size
        print(f'当前连接数: {size}/{maxsize}')

        # 连接健康检查
        is_ok = await db.ping()

asyncio.run(main())
```

**连接池参数配置**:

```python
from xtdbase import MySQLPool

pool = MySQLPool(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    db='mydb',
    minsize=1,           # 最小连接数
    maxsize=10,          # 最大连接数
    charset='utf8mb4',
    autocommit=True,     # 自动提交
    pool_recycle=-1      # 连接回收时间(秒),-1表示不回收
)
```

#### 2.3 `MySQLPoolSync` - 同步调用的异步连接池

在同步环境中使用异步连接池:

```python
from xtdbase import create_sync_mysql_pool

# 创建连接池
db = create_sync_mysql_pool('default')

# 查询操作(参数必须使用元组)
user = db.fetchone('SELECT * FROM users WHERE id = %s', (1,))
users = db.fetchall('SELECT * FROM users LIMIT %s', (10,))
some = db.fetchmany('SELECT * FROM users', 5, ())

# 执行操作
affected = db.execute(
    'INSERT INTO users(name, email) VALUES (%s, %s)',
    ('Alice', 'alice@example.com')
)

# 事务操作
db.begin()
try:
    db.execute('UPDATE accounts SET balance = %s WHERE id = %s', (1000, 1))
    db.commit()
except Exception:
    db.rollback()

# 连接检查
if db.ping():
    print('连接正常')

# 关闭连接池
db.close()
```

**重要提示**: `MySQLPoolSync` 的参数必须使用元组格式 `(value,)` 或 `(value1, value2)`。

### 3. Redis 操作

#### `RedisManager` 类

Redis 客户端封装,提供常用操作:

```python
from xtdbase import create_redis_client

# 创建客户端
redis = create_redis_client('default')

# 字符串操作
redis.set('key', 'value', ex=3600)  # 设置,过期时间3600秒
value = redis.get('key')
redis.delete('key')

# 哈希操作
redis.hset('user:1', 'name', 'Alice')
redis.hset('user:1', 'age', 25)
name = redis.hget('user:1', 'name')
user_data = redis.hgetall('user:1')

# 列表操作
redis.lpush('queue', 'task1')
redis.rpush('queue', 'task2')
task = redis.lpop('queue')

# 集合操作
redis.sadd('tags', 'python', 'database')
members = redis.smembers('tags')

# 有序集合
redis.zadd('scores', {'Alice': 95, 'Bob': 87})
top_users = redis.zrange('scores', 0, 9, desc=True)

# 管道操作(批量执行)
pipe = redis.pipeline()
pipe.set('key1', 'value1')
pipe.set('key2', 'value2')
pipe.incr('counter')
results = pipe.execute()
```

### 4. SQL 工具

#### 安全的 SQL 语句构建

防止 SQL 注入的参数化语句构建:

```python
from xtdbase import make_insert_sql, make_update_sql

# 构建 INSERT 语句
data = {'name': 'Alice', 'email': 'alice@example.com', 'age': 25}
sql, params = make_insert_sql(data, 'users')
# sql: "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)"
# params: ('Alice', 'alice@example.com', 25)

# 执行插入
affected = db.execute(sql, params)

# 构建 UPDATE 语句
update_data = {'email': 'new@example.com', 'age': 26}
where_clause = {'id': 1}
sql, params = make_update_sql(update_data, where_clause, 'users')
# sql: "UPDATE users SET email=%s, age=%s WHERE id=%s"
# params: ('new@example.com', 26, 1)

# 执行更新
affected = db.execute(sql, params)
```

## 🎓 高级用法

### 异步连接池高级特性

#### 1. 批量操作优化

```python
async def batch_insert(db, records):
    """批量插入优化"""
    # 方式1: 使用事务
    conn = await db.begin()
    try:
        cursor = await conn.cursor()
        for record in records:
            await cursor.execute(
                'INSERT INTO users(name, email) VALUES (%s, %s)',
                (record['name'], record['email'])
            )
        await db.commit(conn)
    except Exception:
        await db.rollback(conn)
        raise

    # 方式2: 使用 executemany (推荐)
    from xtdbase import make_insert_sql
    sql, _ = make_insert_sql(records[0], 'users')
    params_list = [tuple(r.values()) for r in records]
    # 注意: aiomysql 需要手动实现 executemany 的逻辑
```

#### 2. 连接池监控

```python
async def monitor_pool(db):
    """监控连接池状态"""
    size, maxsize = db.pool_size
    usage_rate = (size / maxsize) * 100

    if usage_rate > 80:
        print(f'⚠️ 连接池使用率过高: {usage_rate:.1f}%')

    # 检查连接健康
    if not await db.ping():
        print('❌ 连接池异常')
```

#### 3. 大数据流式处理

```python
async def process_large_dataset(db):
    """流式处理大量数据"""
    processed = 0
    batch_size = 1000

    async for row in db.iterate(
        'SELECT * FROM large_table WHERE status = %s',
        'active',
        batch_size=batch_size
    ):
        # 逐行处理,避免内存溢出
        await process_record(row)
        processed += 1

        if processed % 10000 == 0:
            print(f'已处理 {processed} 条记录')
```

### Excel 高级特性

#### 1. 流式读取大文件

```python
def process_large_excel(file_path):
    """流式处理大型 Excel 文件"""
    with Excel(file_path) as excel:
        # 使用迭代器,避免一次性加载所有数据
        for row_dict in excel.iter_rows_dict(start_row=2):
            # 逐行处理
            process_row(row_dict)
```

#### 2. 多工作表数据导出

```python
from xtdbase import Excel, DataCollect, SheetMapping, ColumnMapping

def export_multi_sheet_report(users, orders, products):
    """导出多工作表报表"""

    # 配置用户表
    user_mappings = [
        ColumnMapping(column_name='id', column_alias='ID', width=10),
        ColumnMapping(column_name='name', column_alias='姓名', width=15),
        ColumnMapping(column_name='email', column_alias='邮箱', width=25)
    ]

    # 配置订单表
    order_mappings = [
        ColumnMapping(column_name='order_id', column_alias='订单号', width=20),
        ColumnMapping(column_name='amount', column_alias='金额', width=12)
    ]

    # 组装数据
    data_collect = DataCollect(
        sheet_list=[
            SheetMapping(sheet_name='用户列表', data=users, mappings=user_mappings),
            SheetMapping(sheet_name='订单列表', data=orders, mappings=order_mappings),
            SheetMapping(sheet_name='产品列表', data=products)
        ]
    )

    # 导出
    Excel.multi_sheet_write('report.xlsx', data_collect)
```

#### 3. 动态列宽和格式

```python
from xtdbase import ColumnMapping

# 自动列宽
mappings = [
    ColumnMapping(column_name='short', column_alias='短', width=8),
    ColumnMapping(column_name='medium', column_alias='中等长度', width=15),
    ColumnMapping(column_name='long', column_alias='这是一个很长的列名', width=30)
]

Excel.list_to_excel('output.xlsx', data, mappings)
```

## 📖 示例代码

项目提供了丰富的示例代码,位于 `examples/` 目录:

### Excel 示例

-   `example_excel_unified.py` - Excel 统一接口完整示例
-   `examples/README_excel.md` - Excel 操作详细指南

### MySQL 示例

-   `example_mysqlpool_usage.py` - 异步连接池使用示例
-   `test_mysqlpool.py` - 连接池完整测试用例
-   `examples/README_mysqlpool.md` - MySQL 连接池详细指南

### Redis 示例

-   `test_redis_client.py` - Redis 客户端测试用例
-   `examples/README_redis.md` - Redis 操作指南

### 运行示例

```bash
# 运行 Excel 示例
python examples/example_excel_unified.py

# 运行 MySQL 连接池测试
python examples/test_mysqlpool.py

# 运行 Redis 测试
python examples/test_redis_client.py
```

## ⚙️ 配置说明

### 数据库配置

在 `xtdbase/cfg.py` 中配置数据库连接:

```python
from enum import Enum

class DB_CFG(Enum):
    # 默认配置
    default = [{
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'db': 'mydb',
        'charset': 'utf8mb4',
        'type': 'mysql'
    }]

    # 测试环境
    test = [{
        'host': 'test-db.example.com',
        'port': 3306,
        'user': 'test_user',
        'password': 'test_pass',
        'db': 'test_db',
        'charset': 'utf8mb4',
        'type': 'mysql'
    }]

    # 生产环境
    production = [{
        'host': 'prod-db.example.com',
        'port': 3306,
        'user': 'prod_user',
        'password': 'prod_pass',
        'db': 'prod_db',
        'charset': 'utf8mb4',
        'type': 'mysql'
    }]
```

### 使用配置

```python
from xtdbase import create_mysql_pool

# 使用默认配置
db_default = create_mysql_pool('default')

# 使用测试环境配置
db_test = create_mysql_pool('test')

# 使用生产环境配置
db_prod = create_mysql_pool('production')

# 覆盖部分配置
db_custom = create_mysql_pool('default', maxsize=20, pool_recycle=3600)
```

## 💡 最佳实践

### 1. 连接池配置

```python
# 推荐配置
pool = MySQLPool(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    db='mydb',
    minsize=5,              # 最小连接数: 保持5个常驻连接
    maxsize=20,             # 最大连接数: 高峰期最多20个连接
    charset='utf8mb4',      # 字符集: 支持emoji等特殊字符
    autocommit=True,        # 自动提交: 简单操作推荐开启
    pool_recycle=3600       # 回收时间: 1小时回收一次连接
)
```

### 2. 异常处理

```python
import asyncio
from xtdbase import create_mysql_pool

async def safe_query():
    """安全的数据库查询"""
    try:
        async with create_mysql_pool('default') as db:
            result = await db.fetchone('SELECT * FROM users WHERE id = %s', 1)
            return result
    except Exception as e:
        print(f'查询失败: {e}')
        return None
```

### 3. 资源管理

```python
# ✅ 推荐: 使用上下文管理器
async with create_mysql_pool('default') as db:
    users = await db.fetchall('SELECT * FROM users')
    # 自动关闭连接池

# ❌ 不推荐: 手动管理
db = create_mysql_pool('default')
await db.init_pool()
users = await db.fetchall('SELECT * FROM users')
await db.close()  # 容易忘记关闭
```

### 4. 参数化查询

```python
# ✅ 推荐: 参数化查询(防止SQL注入)
user_id = request.get('user_id')
user = await db.fetchone('SELECT * FROM users WHERE id = %s', user_id)

# ❌ 危险: 字符串拼接(SQL注入风险)
user = await db.fetchone(f'SELECT * FROM users WHERE id = {user_id}')
```

### 5. 批量操作优化

```python
# ✅ 推荐: 使用事务批量插入
conn = await db.begin()
try:
    cursor = await conn.cursor()
    for record in records:
        await cursor.execute('INSERT INTO users(name) VALUES (%s)', (record['name'],))
    await db.commit(conn)
except Exception:
    await db.rollback(conn)

# ❌ 不推荐: 逐条自动提交
for record in records:
    await db.execute('INSERT INTO users(name) VALUES (%s)', record['name'])
```

## ❓ 常见问题

### 1. 连接池大小如何设置?

**建议配置**:

-   低并发 (< 10): `minsize=1, maxsize=5`
-   中并发 (10-100): `minsize=5, maxsize=20`
-   高并发 (> 100): `minsize=10, maxsize=50`

### 2. 异步 vs 同步,如何选择?

**使用异步连接池** (`MySQLPool`):

-   FastAPI、aiohttp 等异步框架
-   需要处理高并发请求
-   有大量 I/O 等待时间

**使用同步连接池** (`MySQLPoolSync`):

-   Flask、Django 等同步框架
-   简单脚本或工具
-   无法使用 async/await 语法

### 3. 如何处理连接超时?

```python
# 设置连接超时参数
pool = MySQLPool(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    db='mydb',
    connect_timeout=10,      # 连接超时10秒
    pool_recycle=3600        # 1小时回收连接
)
```

### 4. 大文件 Excel 操作内存溢出?

```python
# 使用迭代器逐行处理
with Excel('large_file.xlsx') as excel:
    for row_dict in excel.iter_rows_dict(start_row=2):
        # 逐行处理,不会一次性加载所有数据
        process_row(row_dict)
```

### 5. 如何启用 SQL 日志?

```python
# 在配置中启用 echo
pool = MySQLPool(
    host='localhost',
    port=3306,
    user='root',
    password='password',
    db='mydb',
    echo=True  # 打印所有 SQL 语句
)
```

## 🗓️ 开发路线

### v0.2.0 (计划中)

-   [ ] 支持 PostgreSQL 连接池
-   [ ] 添加 ORM 映射功能
-   [ ] 性能监控和指标收集
-   [ ] 完善的单元测试覆盖

### v0.3.0 (规划中)

-   [ ] 分布式事务支持
-   [ ] 读写分离自动路由
-   [ ] 数据库迁移工具
-   [ ] GraphQL 查询支持

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/sandorn/xtdbase.git
cd xtdbase

# 安装开发依赖
pip install -e ".[test]"

# 运行测试
pytest

# 代码格式化
ruff format .

# 代码检查
ruff check .
```

### 提交规范

-   feat: 新功能
-   fix: 修复 bug
-   docs: 文档更新
-   refactor: 代码重构
-   test: 测试相关
-   chore: 构建/工具相关

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👥 作者

**sandorn**

-   Email: sandorn@live.cn
-   GitHub: [@sandorn](https://github.com/sandorn)

## 🙏 致谢

感谢以下开源项目:

-   [aiomysql](https://github.com/aio-libs/aiomysql) - 异步 MySQL 驱动
-   [openpyxl](https://openpyxl.readthedocs.io/) - Excel 操作库
-   [pandas](https://pandas.pydata.org/) - 数据分析库
-   [redis-py](https://github.com/redis/redis-py) - Redis Python 客户端

## 📞 支持

如有问题或建议,请:

1. 提交 [Issue](https://github.com/sandorn/xtdbase/issues)
2. 发送邮件至 sandorn@live.cn
3. 查看 [Wiki 文档](https://github.com/sandorn/xtdbase/wiki)

---

<p align="center">
  <strong>⭐ 如果这个项目对您有帮助,请给我们一个 Star!</strong>
</p>
