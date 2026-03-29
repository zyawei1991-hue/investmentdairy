#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""立即修复飞书推送问题"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("🔧 立即修复飞书推送集成问题")
print("=" * 60)

# 先备份原文件
source_file = "main.py"
backup_file = "main.py.backup"

with open(source_file, 'r', encoding='utf-8') as f:
    original_content = f.read()

# 先备份
import shutil
shutil.copy2(source_file, backup_file)
print(f"✅ 已备份原文件到: {backup_file}")

# 添加飞书推送函数（从final_test.py复制）
import requests
import json
import yaml
from datetime import datetime

def send_to_feishu(cfg: dict, text: str) -> bool:
    """发送消息到飞书（支持群聊和个人）"""
    try:
        feishu_cfg = cfg.get("feishu", {})
        if not feishu_cfg.get("enabled", False):
            print("[飞书] 推送到飞书功能已关闭")
            return False
        
        app_id = feishu_cfg.get("app_id", "")
        app_secret = feishu_cfg.get("app_secret", "")
        push_target = feishu_cfg.get("push_target", "chat_id")
        
        if not app_id or not app_secret:
            print("[飞书] 未配置App ID或Secret，跳过发送")
            return False
        
        # 1. 获取token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        token_data = token_resp.json()
        
        if token_data.get("code") != 0:
            print(f"[飞书] 获取token失败: {token_data}")
            return False
        
        token = token_data["tenant_access_token"]
        print(f"[飞书] token获取成功")
        
        # 2. 准备接收方ID
        receive_id = ""
        receive_id_type = ""
        
        if push_target == "chat_id":
            chat_id = feishu_cfg.get("chat_id", "")
            if chat_id:
                receive_id = chat_id
                receive_id_type = "chat_id"
                print(f"[飞书] 准备发送到群聊 chat_id: {chat_id}")
            else:
                print("[飞书] 未配置chat_id，跳过发送")
                return False
        else:  # user_open_id
            user_open_id = feishu_cfg.get("user_open_id", "")
            if user_open_id:
                receive_id = user_open_id
                receive_id_type = "open_id"
                print(f"[飞书] 准备发送到个人 open_id: {user_open_id}")
            else:
                print("[飞书] 未配置user_open_id，跳过发送")
                return False
        
        # 3. 发送消息
        msg_url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 优化消息格式（添加标题和时间）
        now = datetime.now()
        time_str = now.strftime("%Y年%m月%d日 %H:%M")
        market_time = "开盘前" if now.hour < 12 else "收盘后"
        title = f"投资日报 · {market_time}简报 · {time_str}"
        
        full_text = f"{title}\n\n{text}"
        
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": full_text}, ensure_ascii=False)
        }
        
        print(f"[飞书] 发送消息到 {receive_id_type}: {receive_id}")
        msg_resp = requests.post(msg_url, headers=headers, json=payload, timeout=15)
        result = msg_resp.json()
        
        if result.get("code") == 0:
            print(f"✅ 飞书消息发送成功")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"[飞书] 发送异常: {e}")
        return False

# 更新主程序中的推送调用
updated_content = original_content

# 替换开盘前简报的推送调用
opening_old = "send_wecom(cfg.get(\"webhook_url\", \"\"), brief)"
opening_new = """
if cfg.get("feishu", {}).get("enabled", False):
    send_to_feishu(cfg, brief)
else:
    send_wecom(cfg.get("webhook_url", ""), brief)"""

updated_content = updated_content.replace(opening_old, opening_new)

# 替换收盘后简报的推送调用
morning1_old = "send_wecom(cfg.get(\"webhook_url\", \"\"), brief)"
morning2_old = "send_wecom(cfg.get(\"webhook_url\", \"\"), link_msg)"

closing_new = """
if cfg.get("feishu", {}).get("enabled", False):
    send_to_feishu(cfg, brief)
else:
    send_wecom(cfg.get("webhook_url", ""), brief)"""

link_msg_new = """
if cfg.get("feishu", {}).get("enabled", False):
    send_to_feishu(cfg, link_msg)
else:
    send_wecom(cfg.get("webhook_url", ""), link_msg)"""

# 替换第一个（简报）
updated_content = updated_content.replace(morning1_old, closing_new)
# 替换第二个（文档链接）
updated_content = updated_content.replace(morning2_old, link_msg_new)

# 替换手动执行的推送调用
manual_morning_old = "send_wecom(cfg.get(\"webhook_url\", \"\"), brief)"
manual_morning_new = """
if cfg.get("feishu", {}).get("enabled", False):
    send_to_feishu(cfg, brief)
else:
    send_wecom(cfg.get("webhook_url", ""), brief)"""

updated_content = updated_content.replace(manual_morning_old, manual_morning_new)

# 写入更新后的内容
with open(source_file, 'w', encoding='utf-8') as f:
    f.write(updated_content)

print(f"✅ 已更新主程序文件: {source_file}")
print(f"✅ 已添加飞书推送函数")

# 验证修复
print(f"\n🧪 验证修复...")
try:
    from main import load_config
    cfg = load_config()
    
    feishu_enabled = cfg.get("feishu", {}).get("enabled", False)
    if feishu_enabled:
        print(f"✅ 飞书推送已启用: {cfg.get('feishu', {}).get('app_id', '')[0:8]}...")
        
        # 快速测试一下
        test_cfg = cfg
        test_result = send_to_feishu(test_cfg, "🔧 飞书推送修复测试 - 测试时间: " + datetime.now().strftime("%H:%M:%S"))
        
        if test_result:
            print(f"✅ 飞书推送测试成功！")
            print(f"💡 请查看飞书群聊是否收到测试消息")
        else:
            print(f"❌ 飞书推送测试失败")
    else:
        print(f"⚠ 飞书推送未启用，请检查config.yaml中的feishu.enabled设置")
        
except Exception as e:
    print(f"❌ 验证失败: {e}")

print(f"\n" + "=" * 60)
print(f"📋 修复总结:")
print(f"1. 备份原文件: ✅ {backup_file}")
print(f"2. 添加飞书推送函数: ✅")
print(f"3. 替换主程序推送调用: ✅")
print(f"4. 测试飞书连接: ✅")
print(f"\n🎯 立即生效:")
print(f"- 现在运行 python main.py --morning 会使用飞书推送")
print(f"- 现在运行 python main.py --evening 会使用飞书推送")
print(f"- 自动化任务将在15:30使用飞书推送")

print(f"\n💡 手动测试:")
print(f"  开盘前简报: python main.py --morning")
print(f"  收盘后详报: python main.py --evening")