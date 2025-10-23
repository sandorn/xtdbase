# 更新日志

本文档记录 xtdbase 项目的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-10-23

### ✨ 新增

#### Excel 模块

-   统一的 `Excel` 类，整合了细粒度单元格操作和批量数据处理
-   支持 `openpyxl` 和 `pandas` 双引擎
-   支持上下文管理器自动保存
-   支持流式读取大文件（内存友好）
-   完整的类型注解支持

#### MySQL 模块

-   `MySQL`: 同步 MySQL 连接类，符合 DB-API 2.0 规范
-   `MySQLPool`: 异步 MySQL 连接池，基于 `aiomysql`
-   `MySQLPoolSync`: 同步调用接口的异步连接池
-   完整的事务支持（begin/commit/rollback）
-   连接健康检查（ping）
-   参数化查询防 SQL 注入

#### Redis 模块

-   `RedisManager`: Redis 客户端封装
-   支持字符串、哈希、列表、集合等所有 Redis 数据类型
-   连接池管理
-   自动重连机制

#### SQL 工具

-   `make_insert_sql`: 安全生成 INSERT 语句
-   `make_update_sql`: 安全生成 UPDATE 语句
-   防止 SQL 注入
-   支持批量操作

### 🔧 改进

-   所有模块统一使用 `xtlog` 进行日志记录
-   完整的类型注解，支持类型检查器
-   符合 DB-API 2.0 标准的数据库接口
-   优化的错误处理和异常信息
-   内存优化和性能改进

### 📝 文档

-   完整的 README.md 文档
-   每个模块的详细示例代码
-   API 文档和使用指南
-   最佳实践和常见问题

### 🗑️ 移除

-   移除已弃用的 `sqltwisted` 模块（被 `asyncio` 替代）
-   移除旧的向后兼容方法
-   清理冗余代码和注释

### 🐛 修复

-   修复事务回滚时的原子性问题
-   修复事件循环清理导致的资源泄漏
-   修复 MySQL 9.4 的 `VALUES()` 函数弃用警告
-   修复类型检查错误

### 📦 依赖

#### 核心依赖

-   openpyxl >= 3.1.5
-   pandas >= 2.3.3
-   pydantic >= 2.12.3
-   xtlog >= 0.1.9

#### 可选依赖

-   **mysql**: aiomysql >= 0.2.0, pymysql >= 1.1.2, sqlalchemy >= 2.0.0
-   **redis**: redis >= 6.4.0
-   **crypto**: cryptography >= 44.0.0
-   **test**: pytest >= 7.0.0, pytest-asyncio >= 0.21.0

---

## 计划中的功能

### [0.2.0] - 计划中

-   [ ] PostgreSQL 支持
-   [ ] SQLite 支持
-   [ ] MongoDB 支持
-   [ ] 更多的 Excel 高级功能
-   [ ] 性能监控和指标
-   [ ] 自动化测试覆盖率提升至 90%+

### [0.3.0] - 计划中

-   [ ] 数据库迁移工具
-   [ ] ORM 功能
-   [ ] 查询构建器
-   [ ] 缓存策略
-   [ ] 分布式事务支持

---

[0.1.0]: https://github.com/sandorn/xtdbase/releases/tag/v0.1.0
