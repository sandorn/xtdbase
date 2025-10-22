# !/usr/bin/env python3
"""
==============================================================
Description  : MySQL数据库引擎测试示例
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2025-10-21
FilePath     : /examples/test_mysql_engine.py
Github       : https://github.com/sandorn/home

本文件展示了如何使用 MySQL 数据库引擎的各项功能
包括：连接初始化、SQL执行、查询、插入、更新等操作
==============================================================
"""

from __future__ import annotations

import pymysql
from xtlog import mylog as logger

from xtdbase.cfg import DB_CFG
from xtdbase.mysql import DbEngine, create_mysql_engine


class TestMySQLEngine:
    """MySQL数据库引擎测试类"""

    def __init__(self):
        """初始化测试类"""
        self.test_db = None  # 测试数据库实例
        self.test_table = 'test_mysql_engine'
        self.test_data = [
            {'name': '张三', 'age': 28, 'email': 'zhangsan@example.com'},
            {'name': '李四', 'age': 32, 'email': 'lisi@example.com'},
            {'name': '王五', 'age': 45, 'email': 'wangwu@example.com'},
        ]

    def setup(self):
        """设置测试环境"""
        logger.info('\n===================== 开始设置测试环境 =====================')
        # 使用配置方式创建数据库连接
        self.test_db = create_mysql_engine('default')
        logger.success('成功创建数据库连接')

        # 创建测试表
        self._create_test_table()
        logger.success('成功创建测试表')
        logger.info('===================== 测试环境设置完成 =====================\n')

    def teardown(self):
        """清理测试环境"""
        logger.info('\n===================== 开始清理测试环境 =====================')
        # 删除测试表
        if self.test_db and self._has_test_table():
            sql = f'DROP TABLE IF EXISTS `{self.test_table}`'
            self.test_db.execute(sql)
            logger.success(f'成功删除测试表: {self.test_table}')
        logger.info('===================== 测试环境清理完成 =====================\n')

    def _create_test_table(self):
        """创建测试表"""
        # 先删除可能存在的表
        sql = f'DROP TABLE IF EXISTS `{self.test_table}`'
        self.test_db.execute(sql)  # pyright: ignore[reportOptionalMemberAccess]

        # 创建新表
        sql = f"""
        CREATE TABLE `{self.test_table}` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `name` VARCHAR(50) NOT NULL,
            `age` INT NOT NULL,
            `email` VARCHAR(100) NOT NULL,
            `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.test_db.execute(sql)  # pyright: ignore[reportOptionalMemberAccess]

    def _has_test_table(self):
        """检查测试表是否存在"""
        return self.test_db.has_table(self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

    def test_direct_params_initialization(self):
        """测试直接参数方式初始化"""
        logger.info('\n===== 测试直接参数方式初始化 =====')
        # 从配置中获取参数
        cfg = DB_CFG.default.value[0].copy()

        # 使用直接参数方式创建连接
        db = DbEngine(host=cfg['host'], port=cfg['port'], user=cfg['user'], password=cfg['password'], db=cfg['db'])

        # 验证连接
        version = db.get_version()
        logger.success(f'直接参数方式初始化成功,数据库版本: {version}')

        # 关闭连接
        return True

    def test_config_initialization(self):
        """测试配置方式初始化"""
        logger.info('\n===== 测试配置方式初始化 =====')
        # 使用配置方式创建连接
        db = create_mysql_engine('default')

        # 验证连接
        version = db.get_version()
        logger.success(f'配置方式初始化成功,数据库版本: {version}')

        return True

    def test_execute_sql(self):
        """测试执行SQL语句"""
        logger.info('\n===== 测试执行SQL语句 =====')
        # 执行简单的SQL语句
        sql = 'SELECT 1 + 1 AS result'
        row_count = self.test_db.execute(sql)  # pyright: ignore[reportOptionalMemberAccess]
        logger.success(f'SQL执行成功,影响行数: {row_count}')

        # 验证结果
        result = self.test_db.query(sql)  # pyright: ignore[reportOptionalMemberAccess]
        if result and result[0]['result'] == 2:
            logger.success(f'SQL执行结果验证成功: {result}')
            return True
        logger.error(f'SQL执行结果验证失败: {result}')
        return False

    def test_query(self):
        """测试查询操作"""
        logger.info('\n===== 测试查询操作 =====')
        # 插入测试数据
        for data in self.test_data:
            self.test_db.insert(data, self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        # 执行查询
        sql = f'SELECT * FROM `{self.test_table}`'  # noqa: S608
        results = self.test_db.query(sql)  # pyright: ignore[reportOptionalMemberAccess]

        if results and len(results) == len(self.test_data):
            logger.success(f'查询成功,返回 {len(results)} 条记录')
            logger.debug(f'查询结果示例: {results[0]}')
            return True
        logger.error(f'查询失败,返回 {len(results) if results else 0} 条记录')
        return False

    def test_insert_single(self):
        """测试插入单条数据"""
        logger.info('\n===== 测试插入单条数据 =====')
        # 插入单条数据
        data = {'name': '赵六', 'age': 36, 'email': 'zhaoliu@example.com'}
        row_count = self.test_db.insert(data, self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        if row_count == 1:
            logger.success(f'插入单条数据成功,影响行数: {row_count}')

            # 验证插入结果
            sql = f"SELECT * FROM `{self.test_table}` WHERE name = '赵六'"  # noqa: S608
            results = self.test_db.query(sql)  # pyright: ignore[reportOptionalMemberAccess]
            if results and len(results) == 1:
                logger.success('插入结果验证成功')
                return True
            logger.error('插入结果验证失败')
            return False
        logger.error(f'插入单条数据失败,影响行数: {row_count}')
        return False

    def test_insert_many(self):
        """测试批量插入数据"""
        logger.info('\n===== 测试批量插入数据 =====')
        # 批量插入数据
        batch_data = [{'name': '孙七', 'age': 29, 'email': 'sunqi@example.com'}, {'name': '周八', 'age': 42, 'email': 'zhouba@example.com'}]
        row_count = self.test_db.insert_many(batch_data, self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        if row_count == len(batch_data):
            logger.success(f'批量插入数据成功,影响行数: {row_count}')

            # 验证插入结果
            sql = f"SELECT * FROM `{self.test_table}` WHERE name IN ('孙七', '周八')"  # noqa: S608
            results = self.test_db.query(sql)  # pyright: ignore[reportOptionalMemberAccess]
            if results and len(results) == len(batch_data):
                logger.success('批量插入结果验证成功')
                return True
            logger.error('批量插入结果验证失败')
            return False
        logger.error(f'批量插入数据失败,影响行数: {row_count}')
        return False

    def test_update(self):
        """测试更新数据"""
        logger.info('\n===== 测试更新数据 =====')
        # 更新数据
        new_data = {'age': 30, 'email': 'zhangsan_new@example.com'}
        condition = {'name': '张三'}
        row_count = self.test_db.update(new_data, condition, self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        if row_count >= 1:
            logger.success(f'更新数据成功,影响行数: {row_count}')

            # 验证更新结果
            sql = f"SELECT * FROM `{self.test_table}` WHERE name = '张三'"  # noqa: S608
            results = self.test_db.query(sql)  # pyright: ignore[reportOptionalMemberAccess]
            if results and results[0]['age'] == 30 and results[0]['email'] == 'zhangsan_new@example.com':
                logger.success('更新结果验证成功')
                return True
            logger.error('更新结果验证失败')
            return False
        logger.error(f'更新数据失败,影响行数: {row_count}')
        return False

    def test_get_all(self):
        """测试获取表中所有记录"""
        logger.info('\n===== 测试获取表中所有记录 =====')
        # 获取所有记录
        results = self.test_db.get_all(self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        if results:
            logger.success(f'获取表中所有记录成功,返回 {len(results)} 条记录')
            logger.debug(f'记录示例: {results[0]}')
            return True
        logger.error(f'获取表中所有记录失败,返回 {len(results) if results else 0} 条记录')
        return False

    def test_has_table(self):
        """测试检查表是否存在"""
        logger.info('\n===== 测试检查表是否存在 =====')
        # 检查测试表是否存在
        exists = self.test_db.has_table(self.test_table)  # pyright: ignore[reportOptionalMemberAccess]

        if exists:
            logger.success(f'检查表存在成功,表 {self.test_table} 存在')
            return True
        logger.error(f'检查表存在失败,表 {self.test_table} 不存在')
        return False

    def test_get_version(self):
        """测试获取数据库版本"""
        logger.info('\n===== 测试获取数据库版本 =====')
        # 获取数据库版本
        version = self.test_db.get_version()  # pyright: ignore[reportOptionalMemberAccess]

        if version:
            logger.success(f'获取数据库版本成功: {version}')
            return True
        logger.error('获取数据库版本失败')
        return False

    def test_context_manager(self):
        """测试上下文管理器方式"""
        logger.info('\n===== 测试上下文管理器方式 =====')
        # 使用上下文管理器
        with create_mysql_engine('default') as db_ctx:
            # 执行操作
            version = db_ctx.get_version()
            logger.success(f'上下文管理器方式获取版本: {version}')

            # 执行查询
            sql = f'SELECT COUNT(*) AS count FROM `{self.test_table}`'  # noqa: S608
            result = db_ctx.query(sql)
            logger.success(f'上下文管理器方式执行查询成功,表记录数: {result[0]["count"]}')

        logger.success('上下文管理器方式测试成功')
        return True

    def test_error_handling(self):
        """测试错误处理 - 验证@log_wraps装饰器正确处理异常"""
        logger.info('\n===== 测试错误处理 =====')
        # 执行错误的SQL语句，由于@log_wraps装饰器会捕获异常
        # 所以不会抛出异常，而是记录错误并返回异常对象
        invalid_sql = 'SELECT * FROM non_existent_table'
        result = self.test_db.query(invalid_sql)  # pyright: ignore[reportOptionalMemberAccess]

        # log_wraps装饰器捕获异常后会返回异常对象本身
        # 验证返回的是pymysql的错误对象（表不存在）
        if isinstance(result, pymysql.Error):
            logger.success(f'错误处理测试成功,装饰器正确捕获并返回了异常对象: {type(result).__name__}')
            return True

        logger.error(f'错误处理测试失败,返回值: {result}, 类型: {type(result)}')
        return False

    def run_all_tests(self):
        """运行所有测试"""
        logger.info('\n' + '-' * 60 + '\n' + '                    MySQL数据库引擎全面测试\n' + '-' * 60)

        # 测试结果统计
        tests_run = 0
        tests_passed = 0

        try:
            # 设置测试环境
            self.setup()

            # 定义测试方法列表
            test_methods = [
                self.test_config_initialization,
                self.test_direct_params_initialization,
                self.test_execute_sql,
                self.test_query,
                self.test_insert_single,
                self.test_insert_many,
                self.test_update,
                self.test_get_all,
                self.test_has_table,
                self.test_get_version,
                self.test_context_manager,
                self.test_error_handling,
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


def main():
    """主函数 - 运行所有测试"""
    # 运行MySQL数据库引擎测试
    test_runner = TestMySQLEngine()
    all_passed = test_runner.run_all_tests()

    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
