# !/usr/bin/env python3
"""
Excel统一操作类使用示例

演示Excel类的两种使用模式:
1. 精细操作模式 (openpyxl) - 单元格读写、流式读取
2. 批量操作模式 (pandas) - 大数据量批量读写
"""

from __future__ import annotations

import os
import sys

from xtdbase import ColumnMapping, DataCollect, Excel


def example_1_cell_operations():
    """示例1: 精细的单元格操作 (openpyxl模式)"""
    print('\n=== 示例1: 精细的单元格操作 ===')

    file_path = 'test_output/example1_cells.xlsx'

    with Excel(file_path, 'Sheet1') as excel:
        # 写入单元格
        excel.write_cell(1, 1, '姓名', auto_save=False)
        excel.write_cell(1, 2, '年龄', auto_save=False)
        excel.write_cell(1, 3, '城市', auto_save=False)

        # 批量写入单元格
        cells = [
            (2, 1, 'Alice'),
            (2, 2, 25),
            (2, 3, '北京'),
            (3, 1, 'Bob'),
            (3, 2, 30),
            (3, 3, '上海'),
        ]
        excel.write_cells(cells)

        # 读取单元格
        name = excel.read_cell(2, 1)
        print(f'读取到的姓名: {name}')

        # 读取整行
        row_data = excel.read_row(2)
        print(f'第2行数据: {row_data}')

        # 读取整列
        col_data = excel.read_col(1)
        print(f'第1列数据: {col_data}')

        # 读取所有数据
        all_data = excel.read_all()
        print(f'所有数据: {all_data}')

        # 以字典形式读取
        dict_data = excel.read_all_dict()
        print(f'字典形式数据: {dict_data}')

    print(f'✓ 文件已保存: {file_path}')


def example_2_batch_operations():
    """示例2: 批量数据操作 (pandas模式) - 状态复用"""
    print('\n=== 示例2: 批量数据操作 - 状态复用 ===')

    file_path = 'test_output/example2_batch.xlsx'

    # 准备数据
    users_data = [
        {'id': 1, 'name': 'Alice', 'age': 25, 'city': '北京'},
        {'id': 2, 'name': 'Bob', 'age': 30, 'city': '上海'},
        {'id': 3, 'name': 'Charlie', 'age': 28, 'city': '广州'},
    ]

    # 定义列映射
    col_mappings = [
        ColumnMapping(column_name='id', column_alias='用户ID'),
        ColumnMapping(column_name='name', column_alias='姓名'),
        ColumnMapping(column_name='age', column_alias='年龄'),
        ColumnMapping(column_name='city', column_alias='城市'),
    ]

    # 使用状态复用: 不传递file参数,使用当前实例的文件
    with Excel(file_path, 'Users') as excel:
        # 批量写入数据到当前文件和当前工作表
        excel.batch_write(users_data, col_mappings)

        # 批量读取数据
        read_data = excel.batch_read(col_mappings=col_mappings)
        print(f'读取到的数据: {read_data}')

    print(f'✓ 文件已保存: {file_path}')


def example_3_explicit_file():
    """示例3: 显式传递file参数 - 写入不同文件"""
    print('\n=== 示例3: 显式传递file参数 ===')

    temp_file = 'test_output/temp.xlsx'
    output_file = 'test_output/example3_explicit.xlsx'

    # 准备数据
    products_data = [
        {'id': 1, 'name': 'iPhone', 'price': 5999},
        {'id': 2, 'name': 'iPad', 'price': 3999},
    ]

    col_mappings = [
        ColumnMapping(column_name='id', column_alias='产品ID'),
        ColumnMapping(column_name='name', column_alias='产品名称'),
        ColumnMapping(column_name='price', column_alias='价格'),
    ]

    # 创建临时实例,但写入到不同的文件
    with Excel(temp_file) as excel:
        # 显式指定输出文件和工作表名
        excel.batch_write(products_data, col_mappings, file=output_file, sheet_name='Products')
        print(f'✓ 数据已写入到: {output_file}')


def example_4_multi_sheet():
    """示例4: 多工作表操作"""
    print('\n=== 示例4: 多工作表操作 ===')

    file_path = 'test_output/example4_multi_sheet.xlsx'

    # 准备多个工作表的数据
    users_data = DataCollect(
        data_list=[
            {'id': 1, 'name': 'Alice', 'age': 25},
            {'id': 2, 'name': 'Bob', 'age': 30},
        ],
        col_mappings=[
            ColumnMapping(column_name='id', column_alias='用户ID'),
            ColumnMapping(column_name='name', column_alias='姓名'),
            ColumnMapping(column_name='age', column_alias='年龄'),
        ],
        sheet_name='Users',
    )

    products_data = DataCollect(
        data_list=[
            {'id': 1, 'name': 'iPhone', 'price': 5999},
            {'id': 2, 'name': 'iPad', 'price': 3999},
        ],
        col_mappings=[
            ColumnMapping(column_name='id', column_alias='产品ID'),
            ColumnMapping(column_name='name', column_alias='产品名称'),
            ColumnMapping(column_name='price', column_alias='价格'),
        ],
        sheet_name='Products',
    )

    with Excel(file_path) as excel:
        excel.multi_sheet_write([users_data, products_data])

    print(f'✓ 多工作表文件已保存: {file_path}')

    # 读取不同工作表的数据
    with Excel(file_path, 'Users') as excel:
        users = excel.batch_read()
        print(f'用户数据: {users}')

    with Excel(file_path, 'Products') as excel:
        products = excel.batch_read()
        print(f'产品数据: {products}')


def example_5_merge_files():
    """示例5: 文件合并 (静态方法)"""
    print('\n=== 示例5: 文件合并 ===')

    # 创建测试文件
    file1 = 'test_output/merge_file1.xlsx'
    file2 = 'test_output/merge_file2.xlsx'
    output = 'test_output/example5_merged.xlsx'

    with Excel(file1) as excel:
        excel.batch_write([{'name': 'File1 Data1'}, {'name': 'File1 Data2'}])

    with Excel(file2) as excel:
        excel.batch_write([{'name': 'File2 Data1'}, {'name': 'File2 Data2'}])

    # 使用静态方法合并文件
    Excel.merge_files([file1, file2], output)

    print(f'✓ 合并后的文件已保存: {output}')


def example_6_streaming_read():
    """示例6: 流式读取大文件 (内存友好)"""
    print('\n=== 示例6: 流式读取大文件 ===')

    file_path = 'test_output/example6_streaming.xlsx'

    # 创建一些测试数据
    data = [{'id': i, 'name': f'User{i}', 'score': i * 10} for i in range(1, 101)]
    with Excel(file_path) as excel:
        excel.batch_write(data)

    # 流式读取数据
    with Excel(file_path) as excel:
        print('流式读取前10行数据:')
        for i, row_dict in enumerate(excel.iter_rows_dict()):
            if i >= 10:
                break
            print(f'  {row_dict}')

    print(f'✓ 流式读取完成: {file_path}')


def example_7_mixed_mode():
    """示例7: 混合模式 - 精细操作 + 批量操作"""
    print('\n=== 示例7: 混合模式 ===')

    file_path = 'test_output/example7_mixed.xlsx'

    with Excel(file_path, 'Data') as excel:
        # 先用批量模式写入大量数据
        data = [{'name': f'User{i}', 'score': i * 10} for i in range(1, 11)]
        mappings = [
            ColumnMapping(column_name='name', column_alias='姓名'),
            ColumnMapping(column_name='score', column_alias='分数'),
        ]
        excel.batch_write(data, mappings)

        # 重新加载后用精细模式修改特定单元格
        # 注意: batch_write会重新加载工作簿,所以可以继续操作
        excel.write_cell(1, 3, '备注')
        excel.write_cell(2, 3, '优秀')
        excel.write_cell(3, 3, '良好')

        # 读取所有数据(包括新添加的列)
        all_data = excel.read_all()
        print('混合操作后的数据:')
        for row in all_data[:5]:
            print(f'  {row}')

    print(f'✓ 混合模式文件已保存: {file_path}')


def main():
    """运行所有示例"""
    # 确保输出目录存在
    os.makedirs('test_output', exist_ok=True)

    print('=' * 60)
    print('Excel统一操作类示例')
    print('=' * 60)

    try:
        example_1_cell_operations()
        example_2_batch_operations()
        example_3_explicit_file()
        example_4_multi_sheet()
        example_5_merge_files()
        example_6_streaming_read()
        example_7_mixed_mode()

        print('\n' + '=' * 60)
        print('✓ 所有示例运行成功!')
        print('=' * 60)

    except Exception as e:
        print(f'\n✗ 运行出错: {e}')
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
