# !/usr/bin/env python3
"""
==============================================================
Description  : SqlTwisted异步数据库操作测试示例
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2025-10-21
FilePath     : /examples/test_sqltwisted.py
Github       : https://github.com/sandorn/home

本文件展示了如何使用 SqlTwisted 进行 Twisted 异步数据库操作
包括：查询、插入、更新、链式调用等操作
==============================================================
"""

from __future__ import annotations

from typing import Any

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from xtlog import mylog as logger

from xtdbase.cfg import DB_CFG
from xtdbase.sqltwisted import SqlTwisted, create_sqltwisted


class TestSqlTwisted:
    """SqlTwisted测试类"""

    def __init__(self):
        """初始化测试类"""
        self.db: SqlTwisted | None = None
        self.test_table = 'test_sqltwisted'
        self.test_data = [
            {'name': '张三', 'age': 28, 'email': 'zhangsan@example.com'},
            {'name': '李四', 'age': 32, 'email': 'lisi@example.com'},
            {'name': '王五', 'age': 45, 'email': 'wangwu@example.com'},
        ]
        self.test_counter = {'total': 0, 'passed': 0, 'failed': 0}

    def setup(self) -> Deferred[Any]:
        """设置测试环境"""
        logger.info('\n===================== 开始设置测试环境 =====================')

        def on_setup_complete(_):
            logger.success('测试环境设置完成')
            logger.info('===================== 测试环境设置完成 =====================\n')
            return _

        # 使用配置方式创建数据库连接
        self.db = create_sqltwisted('default', self.test_table)
        logger.success('成功创建SqlTwisted实例')

        # 创建测试表
        d = self._create_test_table()
        d.addCallback(on_setup_complete)
        return d

    def teardown(self) -> None:
        """清理测试环境"""
        logger.info('\n===================== 开始清理测试环境 =====================')

        def on_drop_complete(_):
            logger.success(f'成功删除测试表: {self.test_table}')
            if self.db:
                self.db.close()
            logger.info('===================== 测试环境清理完成 =====================\n')
            reactor.stop()  # pyright: ignore[reportAttributeAccessIssue]

        # 删除测试表
        sql = f'DROP TABLE IF EXISTS `{self.test_table}`'
        if self.db:
            d = self.db.perform_query(sql)
            d.addCallback(on_drop_complete)
        else:
            reactor.stop()  # pyright: ignore[reportAttributeAccessIssue]

    def _create_test_table(self) -> Deferred[Any]:
        """创建测试表"""
        # 先删除可能存在的表
        drop_sql = f'DROP TABLE IF EXISTS `{self.test_table}`'

        def create_table(_):
            # 创建新表
            create_sql = f"""
            CREATE TABLE `{self.test_table}` (
                `id` INT AUTO_INCREMENT PRIMARY KEY,
                `name` VARCHAR(50) NOT NULL,
                `age` INT NOT NULL,
                `email` VARCHAR(100) NOT NULL,
                `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            if self.db:
                return self.db.perform_query(create_sql)
            raise RuntimeError('数据库连接未初始化')

        if self.db:
            d = self.db.perform_query(drop_sql)
            d.addCallback(create_table)
            return d
        raise RuntimeError('数据库连接未初始化')

    def test_perform_query(self) -> Deferred[Any]:
        """测试perform_query查询方法"""
        logger.info('\n===== 测试 perform_query 查询 =====')
        self.test_counter['total'] += 1

        sql = 'SELECT VERSION() AS version'
        res: Any = ''

        def on_success(results):
            if results and len(results) > 0:
                logger.success(f'perform_query测试成功: {results[0]}')
                self.test_counter['passed'] += 1
            else:
                logger.error('perform_query测试失败: 无结果')
                self.test_counter['failed'] += 1
            res = results
            return results

        def on_error(failure):
            logger.error(f'perform_query测试失败: {failure.value!s}')
            self.test_counter['failed'] += 1
            return failure

        if self.db:
            d = self.db.perform_query(sql)
            d.addCallback(on_success)
            d.addErrback(on_error)
            return d
        logger.info(1111111111111111, res)
        raise RuntimeError('数据库连接未初始化')

    def test_query_method(self) -> Deferred[Any]:
        """测试query查询方法"""
        logger.info('\n===== 测试 query 查询方法 =====')
        self.test_counter['total'] += 1

        sql = f'SELECT * FROM `{self.test_table}` LIMIT 5'

        def on_success(results):
            logger.success(f'query方法测试成功: 返回 {len(results or [])} 条记录')
            self.test_counter['passed'] += 1
            return results

        def on_error(failure):
            logger.error(f'query方法测试失败: {failure.value!s}')
            self.test_counter['failed'] += 1
            return failure

        if self.db:
            d = self.db.query(sql)
            d.addCallback(on_success)
            d.addErrback(on_error)
            return d
        raise RuntimeError('数据库连接未初始化')

    def test_insert_single(self) -> Deferred[Any]:
        """测试插入单条数据"""
        logger.info('\n===== 测试插入单条数据 =====')
        self.test_counter['total'] += 1

        data = {'name': '赵六', 'age': 36, 'email': 'zhaoliu@example.com'}

        def on_success(affected_rows):
            if affected_rows >= 1:
                logger.success(f'插入单条数据成功,影响行数: {affected_rows}')
                self.test_counter['passed'] += 1
            else:
                logger.error(f'插入单条数据失败,影响行数: {affected_rows}')
                self.test_counter['failed'] += 1
            return affected_rows

        def on_error(failure):
            logger.error(f'插入单条数据失败: {failure.value!s}')
            self.test_counter['failed'] += 1
            return failure

        if self.db:
            d = self.db.insert(data, self.test_table)
            d.addCallback(on_success)
            d.addErrback(on_error)
            return d
        raise RuntimeError('数据库连接未初始化')

    def test_insert_batch(self) -> Deferred[Any]:
        """测试批量插入数据"""
        logger.info('\n===== 测试批量插入数据 =====')
        self.test_counter['total'] += 1

        def insert_next(index: int = 0) -> Deferred[Any] | int:
            """递归插入数据"""
            if index >= len(self.test_data):
                logger.success(f'批量插入完成,共插入 {len(self.test_data)} 条记录')
                self.test_counter['passed'] += 1
                return index

            data = self.test_data[index]
            if self.db:
                d = self.db.insert(data, self.test_table)
                d.addCallback(lambda _: insert_next(index + 1))
                return d
            raise RuntimeError('数据库连接未初始化')

        return insert_next(0)  # pyright: ignore[reportReturnType]

    def test_update(self) -> Deferred[Any]:
        """测试更新数据"""
        logger.info('\n===== 测试更新数据 =====')
        self.test_counter['total'] += 1

        new_data = {'age': 30, 'email': 'zhangsan_new@example.com'}
        condition = {'name': '张三'}

        def on_success(affected_rows):
            if affected_rows >= 1:
                logger.success(f'更新数据成功,影响行数: {affected_rows}')
                self.test_counter['passed'] += 1
            else:
                logger.error(f'更新数据失败,影响行数: {affected_rows}')
                self.test_counter['failed'] += 1
            return affected_rows

        def on_error(failure):
            logger.error(f'更新数据失败: {failure.value!s}')
            self.test_counter['failed'] += 1
            return failure

        if self.db:
            d = self.db.update(new_data, condition, self.test_table)
            d.addCallback(on_success)
            d.addErrback(on_error)
            return d
        raise RuntimeError('数据库连接未初始化')

    def test_chain_operations(self) -> Deferred[Any]:
        """测试链式操作"""
        logger.info('\n===== 测试链式操作 =====')
        self.test_counter['total'] += 1

        test_id = 1

        def after_query(results):
            logger.info(f'初始查询结果: {len(results or [])} 条记录')
            # 更新数据
            update_data = {'email': 'chain_test@example.com'}
            condition = {'id': test_id}
            if self.db:
                return self.db.update(update_data, condition, self.test_table)
            raise RuntimeError('数据库连接未初始化')

        def after_update(affected_rows):
            logger.info(f'更新操作影响行数: {affected_rows}')
            # 再次查询验证
            sql = f'SELECT * FROM `{self.test_table}` WHERE id = {test_id}'
            if self.db:
                return self.db.perform_query(sql)
            raise RuntimeError('数据库连接未初始化')

        def final_check(results):
            if results and len(results) > 0:
                logger.success(f'链式操作测试成功,最终结果: {results[0]}')
                self.test_counter['passed'] += 1
            else:
                logger.error('链式操作测试失败')
                self.test_counter['failed'] += 1
            return results

        # 执行链式调用
        sql = f'SELECT * FROM `{self.test_table}` WHERE id = {test_id}'
        if self.db:
            d = self.db.perform_query(sql)
            d.addCallback(after_query)
            d.addCallback(after_update)
            d.addCallback(final_check)
            return d
        raise RuntimeError('数据库连接未初始化')

    def test_error_handling(self) -> Deferred[Any]:
        """测试错误处理"""
        logger.info('\n===== 测试错误处理 =====')
        self.test_counter['total'] += 1

        # 执行错误的SQL
        invalid_sql = 'SELECT * FROM non_existent_table'

        def on_error(failure):
            logger.success(f'错误处理测试成功,正确捕获了异常: {type(failure.value).__name__}')
            self.test_counter['passed'] += 1
            return  # 返回None继续后续测试

        def on_unexpected_success(results):
            logger.error(f'错误处理测试失败,应该抛出异常但返回了: {results}')
            self.test_counter['failed'] += 1
            return results

        if self.db:
            d = self.db.perform_query(invalid_sql)
            d.addCallback(on_unexpected_success)
            d.addErrback(on_error)
            return d
        raise RuntimeError('数据库连接未初始化')

    def print_summary(self, _):
        """打印测试结果摘要"""
        logger.info(
            '\n'
            + '-' * 60
            + '\n'
            + '                    测试结果摘要\n'
            + f'                    总测试数: {self.test_counter["total"]}\n'
            + f'                    通过测试数: {self.test_counter["passed"]}\n'
            + f'                    失败测试数: {self.test_counter["failed"]}\n'
            + f'                    通过率: {(self.test_counter["passed"] / self.test_counter["total"] * 100):.2f}%\n'
            + '-' * 60
        )
        return _

    def run_all_tests(self) -> Deferred[Any]:
        """运行所有测试"""
        logger.info('\n' + '-' * 60 + '\n' + '                SqlTwisted异步数据库操作全面测试\n' + '-' * 60)

        def chain_test(d: Deferred[Any], test_func) -> Deferred[Any]:
            """链式执行测试"""
            return d.addCallback(lambda _: test_func())

        # 设置测试环境
        d = self.setup()

        # 链式执行所有测试
        test_methods = [
            self.test_perform_query,
            self.test_query_method,
            self.test_insert_single,
            self.test_insert_batch,
            self.test_update,
            self.test_chain_operations,
            self.test_error_handling,
        ]

        for test_method in test_methods:
            d = chain_test(d, test_method)

        # 打印摘要并清理
        d.addCallback(self.print_summary)
        d.addCallback(lambda _: self.teardown())

        return d


def main():
    """主函数 - 运行所有测试"""
    try:
        test_runner = TestSqlTwisted()
        test_runner.run_all_tests()

        # 启动事件循环
        reactor.run()  # pyright: ignore[reportAttributeAccessIssue]
    except Exception as e:
        logger.error(f'❌ 测试运行失败: {e!s}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    main()
