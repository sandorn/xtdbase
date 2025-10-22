# !/usr/bin/env python3
"""
==============================================================
Description  : SqlTwisted同步方式使用示例
Develop      : VSCode
Author       : sandorn sandorn@live.cn
Date         : 2025-10-21
FilePath     : /examples/example_sync_usage.py
Github       : https://github.com/sandorn/home

本文件展示如何使用 sync=True 参数以同步方式获取结果
适合简单脚本和快速验证场景
==============================================================
"""

from __future__ import annotations

import time

from xtlog import mylog as logger

from xtdbase.sqltwisted import create_sqltwisted


def main():
    """同步方式使用示例

    注意: reactor会自动在后台线程启动，无需手动管理！
    """
    try:
        # 创建数据库实例
        db = create_sqltwisted('default', tablename='users2')

        logger.info('\n' + '=' * 60)
        logger.info('SqlTwisted 同步方式使用示例')
        logger.info('✨ reactor自动管理，无需手动启动！')
        logger.info('=' * 60)

        # 示例1: 查询数据库版本
        logger.info('\n【示例1】查询数据库版本')
        result = db.perform_query('SELECT VERSION() AS version', sync=True)
        logger.success(f'数据库版本: {result[0] if result else "未知"}')

        # 示例2: 查询示例
        logger.info('\n【示例2】执行查询')
        sql = 'SELECT * from users2 limit 1'
        result = db.query(sql, sync=True)
        logger.success(f'查询结果: {result}')

        # 示例3: 插入数据（需要有对应的表）
        logger.info('\n【示例3】插入数据示例(注释状态)')
        data = {'username': '张三444', '手机': 12311112345}
        affected = db.insert(data, sync=True)
        logger.success(f'插入成功,影响行数: {affected}')

        # 示例4: 更新数据（需要有对应的表）
        logger.info('\n【示例4】更新数据示例(注释状态)')

        condition = {'username': '张三444'}
        new_data = {'username': '56789'}
        affected = db.update(new_data, condition, sync=True)
        logger.success(f'更新成功,影响行数: {affected}')

        # 示例5: 超时设置
        logger.info('\n【示例5】设置超时时间')
        result = db.perform_query('SELECT SLEEP(1)', sync=True, timeout=5.0)
        logger.success('查询完成(5秒超时内)')

        # 清理
        db.close()
        logger.info('\n' + '=' * 60)
        logger.success('所有示例执行完成!')
        logger.info('=' * 60)

    except Exception as e:
        logger.error(f'❌ 示例运行失败: {e!s}')
        import traceback

        traceback.print_exc()


if __name__ == '__main__':
    main()

    # 等待一段时间后退出
    time.sleep(1)
    logger.info('\n程序结束')
