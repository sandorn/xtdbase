# !/usr/bin/env python
"""
==============================================================
Description  : DB_CFG 数据库配置模块使用示例
Author       : sandorn sandorn@live.cn
Date         : 2025-10-23
FilePath     : /examples/example_cfg_usage.py
Github       : https://github.com/sandorn/xtdbase

本示例展示如何使用 DB_CFG 进行数据库配置管理:
    1. 读取配置信息
    2. 配置信息的结构
    3. 如何添加自定义配置
    4. 配置的最佳实践
==============================================================
"""

from __future__ import annotations

from xtdbase.cfg import DB_CFG


def example_1_read_config():
    """示例 1: 读取数据库配置信息"""
    print('\n' + '=' * 60)
    print('示例 1: 读取数据库配置')
    print('=' * 60)

    # 方式 1: 通过属性访问配置
    try:
        config = DB_CFG.TXbook.value[0]
        print('\n配置名称: TXbook')
        print(f'数据库类型: {config.get("type")}')
        print(f'主机地址: {config.get("host")}')
        print(f'端口: {config.get("port")}')
        print(f'数据库名: {config.get("db")}')
        print(f'字符集: {config.get("charset")}')
        print(f'完整配置: {config}')
    except AttributeError:
        print('⚠️  配置 TXbook 不存在')

    # 方式 2: 通过字符串访问配置
    config_name = 'redis'
    if hasattr(DB_CFG, config_name):
        config = DB_CFG[config_name].value[0]
        print(f'\n配置名称: {config_name}')
        print(f'数据库类型: {config.get("type")}')
        print(f'完整配置: {config}')


def example_2_list_all_configs():
    """示例 2: 列出所有可用的配置"""
    print('\n' + '=' * 60)
    print('示例 2: 列出所有可用配置')
    print('=' * 60)

    # 获取所有配置名称(排除内置属性)
    all_configs = [key for key in dir(DB_CFG) if not key.startswith('_')]

    print(f'\n共有 {len(all_configs)} 个配置项:\n')

    for config_name in all_configs:
        config = DB_CFG[config_name].value[0]
        db_type = config.get('type', 'unknown')
        db_name = config.get('db', config.get('host', 'N/A'))
        print(f'  • {config_name:<15} [{db_type:<8}] -> {db_name}')


def example_3_check_config_exists():
    """示例 3: 检查配置是否存在"""
    print('\n' + '=' * 60)
    print('示例 3: 检查配置是否存在')
    print('=' * 60)

    test_configs = ['TXbook', 'redis', 'default', 'nonexistent']

    for config_name in test_configs:
        exists = hasattr(DB_CFG, config_name)
        status = '✅ 存在' if exists else '❌ 不存在'
        print(f'  配置 "{config_name}": {status}')


def example_4_safe_get_config():
    """示例 4: 安全获取配置(带默认值)"""
    print('\n' + '=' * 60)
    print('示例 4: 安全获取配置')
    print('=' * 60)

    def get_db_config(config_name: str, default: dict | None = None) -> dict:
        """安全获取数据库配置,如果不存在返回默认值"""
        try:
            if hasattr(DB_CFG, config_name):
                return DB_CFG[config_name].value[0].copy()
            print(f'⚠️  配置 "{config_name}" 不存在,使用默认配置')
            return default or {}
        except Exception as e:
            print(f'❌ 读取配置失败: {e}')
            return default or {}

    # 测试存在的配置
    config1 = get_db_config('TXbook')
    print(f'\n存在的配置: {config1.get("db", "N/A")}')

    # 测试不存在的配置(使用默认值)
    default_config = {
        'type': 'mysql',
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': 'password',
        'db': 'default_db',
    }
    config2 = get_db_config('nonexistent', default_config)
    print(f'不存在的配置(使用默认): {config2.get("db", "N/A")}')


def example_5_filter_configs_by_type():
    """示例 5: 按类型筛选配置"""
    print('\n' + '=' * 60)
    print('示例 5: 按类型筛选配置')
    print('=' * 60)

    def get_configs_by_type(db_type: str) -> dict[str, dict]:
        """获取指定类型的所有配置"""
        configs = {}
        for config_name in dir(DB_CFG):
            if not config_name.startswith('_'):
                config = DB_CFG[config_name].value[0]
                if config.get('type') == db_type:
                    configs[config_name] = config
        return configs

    # 获取所有 MySQL 配置
    mysql_configs = get_configs_by_type('mysql')
    print(f'\nMySQL 配置 ({len(mysql_configs)} 个):')
    for name, config in mysql_configs.items():
        print(f'  • {name}: {config.get("db")}@{config.get("host")}')

    # 获取所有 Redis 配置
    redis_configs = get_configs_by_type('redis')
    print(f'\nRedis 配置 ({len(redis_configs)} 个):')
    for name, config in redis_configs.items():
        print(f'  • {name}: {config.get("host")}:{config.get("port")}/{config.get("db")}')


def example_6_config_validation():
    """示例 6: 配置验证"""
    print('\n' + '=' * 60)
    print('示例 6: 配置完整性验证')
    print('=' * 60)

    def validate_mysql_config(config: dict) -> tuple[bool, list[str]]:
        """验证 MySQL 配置的完整性"""
        required_fields = ['host', 'port', 'user', 'password', 'db']
        missing_fields = [field for field in required_fields if field not in config]

        is_valid = len(missing_fields) == 0
        return is_valid, missing_fields

    # 测试几个配置
    test_configs = ['TXbook', 'redis']

    for config_name in test_configs:
        if hasattr(DB_CFG, config_name):
            config = DB_CFG[config_name].value[0]
            if config.get('type') == 'mysql':
                is_valid, missing = validate_mysql_config(config)
                status = '✅ 有效' if is_valid else f'❌ 缺少字段: {missing}'
                print(f'  {config_name}: {status}')
            else:
                print(f'  {config_name}: ⏭️  跳过(非MySQL配置)')


def example_7_best_practices():
    """示例 7: 配置管理最佳实践"""
    print('\n' + '=' * 60)
    print('示例 7: 配置管理最佳实践')
    print('=' * 60)

    print("""
    ✅ 最佳实践建议:

    1. 环境分离:
       - 开发环境: dev_db
       - 测试环境: test_db
       - 生产环境: prod_db

    2. 敏感信息保护:
       - 不要在代码中硬编码密码
       - 使用环境变量: os.getenv('DB_PASSWORD')
       - 使用配置文件: config.ini, .env
       - 使用密钥管理服务

    3. 配置结构:
       - 使用清晰的命名规范
       - 包含所有必需字段
       - 添加注释说明用途

    4. 连接池配置:
       - minsize: 最小连接数(推荐 1-5)
       - maxsize: 最大连接数(推荐 10-50)
       - pool_recycle: 连接回收时间(秒)

    5. 使用示例:
       from xtdbase import create_mysql_pool

       # 使用配置名称创建连接池
       async with create_mysql_pool('TXbook') as db:
           results = await db.fetchall('SELECT * FROM table')
    """)


def main():
    """主函数：运行所有示例"""
    print('\n' + '=' * 60)
    print('DB_CFG 数据库配置模块使用示例')
    print('=' * 60)

    # 运行所有示例
    example_1_read_config()
    example_2_list_all_configs()
    example_3_check_config_exists()
    example_4_safe_get_config()
    example_5_filter_configs_by_type()
    example_6_config_validation()
    example_7_best_practices()

    print('\n' + '=' * 60)
    print('✅ 所有示例运行完成!')
    print('=' * 60 + '\n')


if __name__ == '__main__':
    main()
