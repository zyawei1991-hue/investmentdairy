#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试智能表格集成
"""

import sys
import yaml
from datetime import datetime

print("调试智能表格集成")
print("=" * 60)

# 首先检查main.py中的智能表格代码
with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

# 找到智能表格存储部分
import re

# 搜索智能表格存储代码
smart_sheet_code_block = re.search(r'# 存储数据到智能表格.*?except Exception as e:', main_content, re.DOTALL)
if smart_sheet_code_block:
    print("1. 在main.py中找到智能表格存储代码块")
    code = smart_sheet_code_block.group(0)
    print(f"   代码块长度: {len(code)}字符")
    
    # 检查是否有调用save_daily_report
    if 'save_daily_report' in code:
        print("   包含save_daily_report调用: ✓")
    else:
        print("   未找到save_daily_report调用: ✗")
        
    # 检查是否有SMART_SHEET_AVAILABLE条件
    if 'if SMART_SHEET_AVAILABLE:' in code:
        print("   有SMART_SHEET_AVAILABLE条件检查: ✓")
    else:
        print("   无SMART_SHEET_AVAILABLE条件检查: ✗")
else:
    print("1. 未在main.py中找到智能表格存储代码块")

# 检查配置文件
print("\n2. 检查配置文件...")
with open('config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

tencent_config = config.get('tencent_docs', {})
sheet_id = tencent_config.get('data_sheet_id', '')

if sheet_id:
    print(f"   智能表格文件ID: {sheet_id}")
    print(f"   链接: https://docs.qq.com/smartsheet/{sheet_id}")
else:
    print("   未配置智能表格文件ID")

# 模拟运行一次存储
print("\n3. 模拟数据存储...")
try:
    from tencent_smartsheet import TencentSmartSheetManager
    
    dummy_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'report_type': '测试报告',
        'report_time': datetime.now().strftime('%H:%M'),
        'total_value': 420015,
        'day_pnl': -6009.72,
        'total_pnl': 13169.22,
        'position_ratio': 0.786,
        'holdings_count': 21,
        'shangzheng_index': '3889.08',
        'shenzheng_index': '待获取',
        'chuangye_index': '3272.49',
        'valuation_temp': 0.60,
        'north_fund': '+0.00亿元',
        'advance_decline': '待获取',
        'best_performer': '芯片ETF华夏',
        'ai_market_trend': '市场整体弱势',
        'ai_operation_suggest': '建议观望',
        'doc_url': 'https://docs.qq.com/aio/DV0VXVXFoVGp6UHBo'
    }
    
    manager = TencentSmartSheetManager('config.yaml')
    manager.load_config()
    
    # 注意：这里只是模拟，实际调用会因为API限制而无法在测试中完成
    print(f"   模拟存储数据到智能表格: {manager.get_sheet_url()}")
    print(f"   数据项数: {len(dummy_data)}个字段")
    print("   注意：实际API调用需要联网和有效的MCP配置")
    
except Exception as e:
    print(f"   模拟失败: {e}")

print("\n" + "=" * 60)
print("调试完成")
print("=" * 60)