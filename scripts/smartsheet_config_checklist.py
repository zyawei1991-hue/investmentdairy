#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档智能表格配置清单和验证工具
"""

import json
import sys
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def print_checklist():
    """打印配置检查清单"""
    
    # 基本信息
    print("=" * 80)
    print("🎯 腾讯文档智能表格 17字段配置清单")
    print("=" * 80)
    
    # 字段定义
    fields = [
        # 基本信息字段 (3个)
        {
            "name": "日期",
            "type": "日期",
            "desc": "格式：年-月-日 (yyyy-mm-dd)",
            "test_value": datetime.now().strftime("%Y-%m-%d"),
            "category": "基本信息"
        },
        {
            "name": "报告类型",
            "type": "单选",
            "desc": "选项：开盘前(蓝色)，收盘后(绿色)",
            "test_value": "收盘后",
            "category": "基本信息"
        },
        {
            "name": "报告时间",
            "type": "文本",
            "desc": "格式：HH:MM (24小时制)",
            "test_value": "00:00",
            "category": "基本信息"
        },
        
        # 市值与盈亏字段 (5个)
        {
            "name": "总市值",
            "type": "数字(货币)",
            "desc": "格式：货币，小数位：2位",
            "test_value": "200000.00",
            "category": "市值盈亏"
        },
        {
            "name": "当日盈亏",
            "type": "数字(货币)",
            "desc": "格式：货币，小数位：2位",
            "test_value": "1000.00",
            "category": "市值盈亏"
        },
        {
            "name": "总盈亏",
            "type": "数字(货币)",
            "desc": "格式：货币，小数位：2位",
            "test_value": "5000.00",
            "category": "市值盈亏"
        },
        {
            "name": "仓位比例",
            "type": "数字(百分比)",
            "desc": "格式：百分比，小数位：1位",
            "test_value": "78.6",
            "category": "市值盈亏"
        },
        {
            "name": "持仓数量",
            "type": "数字(常规)",
            "desc": "格式：常规数字，小数位：0位",
            "test_value": "21",
            "category": "市值盈亏"
        },
        
        # 市场指标字段 (7个)
        {
            "name": "上证指数",
            "type": "文本",
            "desc": "沪深主板指数",
            "test_value": "3890.00 (+0.12%)",
            "category": "市场指标"
        },
        {
            "name": "深证成指",
            "type": "文本",
            "desc": "深圳综合指数",
            "test_value": "待获取",
            "category": "市场指标"
        },
        {
            "name": "创业板指",
            "type": "文本",
            "desc": "创业板指数",
            "test_value": "待获取",
            "category": "市场指标"
        },
        {
            "name": "估值温度",
            "type": "单选",
            "desc": "选项：低温(蓝)/中温(绿)/高温(红)",
            "test_value": "中温",
            "category": "市场指标"
        },
        {
            "name": "北向资金",
            "type": "文本",
            "desc": "北上资金流向",
            "test_value": "待获取",
            "category": "市场指标"
        },
        {
            "name": "涨跌家数",
            "type": "文本",
            "desc": "全市场涨跌统计",
            "test_value": "待获取",
            "category": "市场指标"
        },
        {
            "name": "最佳表现",
            "type": "文本",
            "desc": "当日涨幅最大标的",
            "test_value": "测试ETF",
            "category": "市场指标"
        },
        
        # AI分析字段 (2个)
        {
            "name": "AI市场趋势",
            "type": "文本",
            "desc": "AI分析的市场概况",
            "test_value": "市场表现平稳，测试数据",
            "category": "AI分析"
        },
        {
            "name": "AI操作建议",
            "type": "文本",
            "desc": "AI提供的投资建议",
            "test_value": "建议保持现有仓位",
            "category": "AI分析"
        },
        {
            "name": "腾讯文档链接",
            "type": "链接",
            "desc": "详报文档链接",
            "test_value": "https://docs.qq.com/aio/测试链接",
            "category": "AI分析"
        }
    ]
    
    # 按类别分组
    categories = {}
    for field in fields:
        category = field["category"]
        if category not in categories:
            categories[category] = []
        categories[category] = categories[category] + [field]
    
    # 打印配置状态
    print(f"📋 字段总数: {len(fields)}")
    print(f"📊 分类数量: {len(categories)}")
    print()
    
    # 打印分类配置
    for cat_name, cat_fields in categories.items():
        print(f"🏷️ 【{cat_name}】 字段 (共{len(cat_fields)}个)")
        print("-" * 60)
        
        for i, field in enumerate(cat_fields, 1):
            status = "⚪"
            print(f"  {status} {i:2d}. {field['name']:10} [{field['type']:8}]")
            print(f"      描述: {field['desc']}")
            print(f"      测试值: {field['test_value']}")
            print()
    
    print("=" * 80)
    print("🛠️  配置进度检查")
    print("=" * 80)
    
    # 交互式检查
    completed = 0
    for field in fields:
        print(f"❓ 请确认: 是否已添加字段 '{field['name']}' ({field['type']})?")
        print(f"   描述: {field['desc']}")
        response = input("   [Y]已完成 / [N]未完成 / [S]跳过: ").strip().lower()
        
        if response == 'y':
            completed += 1
            print(f"   ✅ 已添加\n")
        elif response == 'n':
            print(f"   ❌ 请添加此字段: {field['name']} ({field['type']})\n")
        else:
            print(f"   ⏸️  已跳过\n")
    
    # 完成统计
    completion_rate = int(completed / len(fields) * 100)
    print(f"📈 配置完成度: {completed}/{len(fields)} ({completion_rate}%)")
    
    if completion_rate >= 90:
        print("🎉 恭喜！配置基本完成，可以开始测试！")
        print("🔗 表格链接: https://docs.qq.com/smartsheet/DV0FubVVtYXJteUdQ")
        return True
    elif completion_rate >= 50:
        print("📋 还需继续配置一些字段")
        print("💡 提示: 建议至少完成所有基础字段")
        return False
    else:
        print("🚨 配置进度不足，请先完成基本字段配置")
        return False

def print_quick_setup_guide():
    """打印快速设置指南"""
    print("\n" + "=" * 80)
    print("🚀 腾讯文档智能表格快速设置指南")
    print("=" * 80)
    
    print("\n📱 第一步：打开表格")
    print("   1. 浏览器访问: https://docs.qq.com/smartsheet/DV0FubVVtYXJteUdQ")
    print("   2. 确认能正常打开")
    print("   3. 确认有编辑权限")
    
    print("\n📝 第二步：添加关键字段（先添加前5个）")
    print("   1. 日期 (日期类型)")
    print("   2. 报告类型 (单选: 开盘前/收盘后)")
    print("   3. 总市值 (数字: 货币格式)")
    print("   4. 当日盈亏 (数字: 货币格式)")
    print("   5. 仓位比例 (数字: 百分比格式)")
    
    print("\n🧪 第三步：添加测试数据")
    print("   添加任意一行测试数据：")
    print("   日期: 今天")
    print("   报告类型: 收盘后")
    print("   总市值: 100000")
    
    print("\n📞 第四步：反馈")
    print("   完成以上步骤后告诉我，我会立即测试API")
    
    print("\n⏰ 预计时间：")
    print("   简单配置：5分钟（前5个字段）")
    print("   完整配置：15分钟（全部17个字段）")

def generate_field_config_script():
    """生成字段配置脚本（用于手动参考）"""
    print("\n" + "=" * 80)
    print("📋 字段配置脚本（复制粘贴用）")
    print("=" * 80)
    
    script = """
# 腾讯文档智能表格字段配置快速参考

## 字段类型映射
| 类型名称 | 腾讯文档中选什么 | 格式设置 |
|----------|------------------|----------|
| 日期 | 选择"日期" | 格式：年-月-日 |
| 单选 | 选择"单选" → 添加选项 | 设置颜色 |
| 文本 | 选择"文本" | 默认 |
| 货币 | 选择"数字" → 格式：货币 → 小数位：2 | ¥ 123,456.78 |
| 百分比 | 选择"数字" → 格式：百分比 → 小数位：1 | 78.6% |
| 常规数字 | 选择"数字" → 格式：常规 → 小数位：0 | 21 |
| 链接 | 选择"链接" | 自动识别URL |

## 必填字段列表（按优先级）
1. 日期 (日期)
2. 报告类型 (单选)
3. 报告时间 (文本)
4. 总市值 (货币)
5. 当日盈亏 (货币)
6. 总盈亏 (货币)
7. 仓位比例 (百分比)
8. 持仓数量 (数字)

## 单选配置
- 报告类型: 开盘前(蓝色)、收盘后(绿色)
- 估值温度: 低温(蓝色)、中温(绿色)、高温(红色)

## 测试数据示例
| 字段 | 测试值 |
|------|--------|
| 日期 | 2026-03-27 |
| 报告类型 | 收盘后 |
| 报告时间 | 00:00 |
| 总市值 | 200000.00 |
| 当日盈亏 | 1000.00 |
| 总盈亏 | 5000.00 |
| 仓位比例 | 78.6 |
| 持仓数量 | 21 |
    """
    
    print(script)

def main():
    """主函数"""
    print("🔍 腾讯文档智能表格配置助手")
    print()
    
    print_quick_setup_guide()
    
    print("\n" + "=" * 80)
    print("📊 配置模式选择")
    print("=" * 80)
    print("1. 快速配置模式（先搞定前5个关键字段）")
    print("2. 完整配置模式（一次配置全部17字段）")
    print("3. 生成配置参考脚本")
    print("4. 仅查看指导手册")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == '1':
        print("\n🎯 快速配置模式启动...")
        print("建议按顺序添加:")
        print("  1. 日期")
        print("  2. 报告类型")
        print("  3. 总市值")
        print("  4. 当日盈亏")
        print("  5. 仓位比例")
        print("\n添加完成后输入任意字符继续: ", end="")
        input()
        
        print("\n✅ 快速配置完成！")
        print("请访问表格确认:")
        print("  https://docs.qq.com/smartsheet/DV0FubVVtYXJteUdQ")
        print("\n完成输入Y，有问题输入N: ", end="")
        result = input().strip().lower()
        
        if result == 'y':
            print("\n🎉 好极了！我将立即测试API连接...")
            # 这里可以添加API测试
            return True
        else:
            print("\n❌ 请描述遇到的问题...")
            return False
    
    elif choice == '2':
        print("\n📋 完整配置模式启动...")
        return print_checklist()
    
    elif choice == '3':
        generate_field_config_script()
        return True
    
    elif choice == '4':
        print("\n📚 指导手册模式...")
        print("请打开我创建的可视化指南:")
        print("  file:///C:/Users/Administrator/Desktop/investment-daily/smartsheet_visual_guide.html")
        print("或访问:")
        print("  https://docs.qq.com/smartsheet/DV0FubVVtYXJteUdQ")
        return True
    
    else:
        print("无效选择")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ 配置准备完成！下一步：API连接测试")
        else:
            print("\n❌ 需要进一步配置")
    except KeyboardInterrupt:
        print("\n\n👋 用户中断操作")