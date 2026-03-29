"""
直连配置助手 - 为 Clash 添加国内网站直连规则
"""
import sys
import os

print("""
=== Clash 直连规则配置 ===

请在 Clash 控制面板中手动添加以下规则：

1. 打开 Clash 控制面板
2. 点击左侧【配置文件】
3. 找到当前使用的配置文件，点击【编辑】
4. 在 rules 部分的最前面添加以下内容：

# 投资日报程序直连规则
- DOMAIN-SUFFIX,eastmoney.com,DIRECT
- DOMAIN-SUFFIX,weixin.qq.com,DIRECT
- DOMAIN-SUFFIX,qyapi.weixin.qq.com,DIRECT

5. 点击右上角【下载】或【保存】
6. 回到【概览】，点击【重载配置】

完成后运行：python main.py --test
""")

# 询问是否创建配置备份
choice = input("\n是否创建 Clash 配置示例文件？(y/n): ").strip().lower()
if choice == 'y':
    config_dir = os.path.join(os.path.expanduser('~'), '.config', 'clash')
    example_path = os.path.join(os.path.dirname(__file__), 'clash-rules-example.txt')
    
    with open(example_path, 'w', encoding='utf-8') as f:
        f.write("""# Clash 直连规则示例
# 将以下规则添加到你的 Clash 配置文件的 rules 部分
# 注意：添加到规则列表的最前面

# 投资日报程序直连规则（添加到 rules 最前面）
- DOMAIN-SUFFIX,eastmoney.com,DIRECT
- DOMAIN-SUFFIX,weixin.qq.com,DIRECT
- DOMAIN-SUFFIX,qyapi.weixin.qq.com,DIRECT

# 原有规则...
# - MATCH,代理节点名
""")
    
    print(f"\n✅ 已创建示例文件: {example_path}")
    print("可以将这些规则复制到 Clash 配置中")

print("\n按任意键退出...")
input()
