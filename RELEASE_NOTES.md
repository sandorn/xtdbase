# xtdbase v0.1.0 发布说明

## 🎉 发布成功！

**发布时间**: 2025-10-23  
**PyPI 地址**: https://pypi.org/project/xtdbase/0.1.0/

---

## 📦 安装方式

### 基础安装

```bash
pip install xtdbase
```

### 安装 MySQL 支持

```bash
pip install xtdbase[mysql]
```

### 安装 Redis 支持

```bash
pip install xtdbase[redis]
```

### 完整安装（推荐）

```bash
pip install xtdbase[all]
```

---

## ✨ 主要特性

### 1. Excel 操作

-   统一的 Excel 接口，支持 `openpyxl` 和 `pandas`
-   细粒度单元格操作 + 批量数据处理
-   上下文管理器自动保存
-   流式读取大文件

### 2. MySQL 数据库

-   **MySQL**: 同步连接，符合 DB-API 2.0
-   **MySQLPool**: 异步连接池，高性能并发
-   **MySQLPoolSync**: 同步接口调用异步池
-   完整事务支持（begin/commit/rollback）
-   参数化查询防 SQL 注入

### 3. Redis 客户端

-   支持所有 Redis 数据类型
-   连接池管理
-   自动重连机制

### 4. SQL 工具

-   `make_insert_sql`: 安全生成 INSERT
-   `make_update_sql`: 安全生成 UPDATE
-   防止 SQL 注入

---

## 📝 快速开始

### Excel 操作示例

```python
from xtdbase import Excel

# 使用上下文管理器
with Excel('data.xlsx', 'Sheet1') as excel:
    # 写入单元格
    excel.write_cell('A1', 'Hello')

    # 批量写入
    data = [
        {'name': 'Alice', 'age': 25},
        {'name': 'Bob', 'age': 30}
    ]
    excel.batch_write(data)
```

### MySQL 同步操作示例

```python
from xtdbase import MySQL

with MySQL(host='localhost', user='root', password='pwd', db='test') as db:
    # 查询
    users = db.fetchall('SELECT * FROM users WHERE age > %s', (18,))

    # 插入
    db.execute('INSERT INTO users (name, age) VALUES (%s, %s)', ('Alice', 25))

    # 事务
    db.begin()
    try:
        db.execute('UPDATE accounts SET balance = balance - 100 WHERE id = 1')
        db.execute('UPDATE accounts SET balance = balance + 100 WHERE id = 2')
        db.commit()
    except Exception:
        db.rollback()
```

### MySQL 异步操作示例

```python
from xtdbase import create_mysql_pool
import asyncio

async def main():
    async with create_mysql_pool('default') as db:
        users = await db.fetchall('SELECT * FROM users')
        print(users)

asyncio.run(main())
```

---

## 📊 包信息

| 项目        | 详情            |
| ----------- | --------------- |
| 包名        | xtdbase         |
| 版本        | 0.1.0           |
| Python 要求 | >= 3.13         |
| 许可证      | MIT             |
| 作者        | sandorn         |
| 邮箱        | sandorn@live.cn |

---

## 📚 文档资源

-   **PyPI 主页**: https://pypi.org/project/xtdbase/
-   **GitHub 仓库**: https://github.com/sandorn/xtdbase
-   **完整文档**: 查看项目 README.md
-   **示例代码**: 查看 `examples/` 目录

---

## 🔧 依赖包

### 核心依赖

-   openpyxl >= 3.1.5
-   pandas >= 2.3.3
-   pydantic >= 2.12.3
-   xtlog >= 0.1.9

### 可选依赖

**MySQL**:

-   aiomysql >= 0.2.0
-   pymysql >= 1.1.2
-   sqlalchemy >= 2.0.0

**Redis**:

-   redis >= 6.4.0

**加密**:

-   cryptography >= 44.0.0

---

## ✅ 质量保证

-   ✅ 所有代码通过 `ruff` 检查
-   ✅ 所有代码通过 `basedpyright` 类型检查
-   ✅ 符合 DB-API 2.0 标准
-   ✅ 兼容 MySQL 9.4
-   ✅ 完整的类型注解
-   ✅ 详细的文档和示例

---

## 🐛 问题反馈

如遇到任何问题，请在 GitHub 提交 issue:
https://github.com/sandorn/xtdbase/issues

---

## 🙏 致谢

感谢所有使用 xtdbase 的开发者！

---

## 📅 下一步计划

### v0.2.0 (计划中)

-   [ ] PostgreSQL 支持
-   [ ] SQLite 支持
-   [ ] MongoDB 支持
-   [ ] 性能监控和指标
-   [ ] 单元测试覆盖率 90%+

### v0.3.0 (计划中)

-   [ ] 数据库迁移工具
-   [ ] ORM 功能
-   [ ] 查询构建器
-   [ ] 缓存策略
-   [ ] 分布式事务支持

---

**享受使用 xtdbase！** 🚀
