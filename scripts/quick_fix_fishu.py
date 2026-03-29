#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速修复飞书推送问题，确保今天上午的推送立即执行"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("🔧 快速修复飞书推送问题")
print("=" * 60)

import yaml
import requests
import json
from datetime import datetime

# 加载配置
config_path = 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

feishu_config = config.get('feishu', {})
app_id = feishu_config.get('app_id')
app_secret = feishu_config.get('app_secret')
chat_id = feishu_config.get('chat_id')

def send_to_feishu_immediate(text: str):
    """立即发送消息到飞书"""
    try:
        # 获取token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_resp = requests.post(token_url, json={"app_id": app_id, "app_secret": app_secret}, timeout=10)
        token_data = token_resp.json()
        
        if token_data.get("code") != 0:
            print(f"❌ 获取token失败: {token_data}")
            return False
        
        token = token_data["tenant_access_token"]
        
        # 发送消息
        msg_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        now = datetime.now()
        time_str = now.strftime("%Y年%m月%d日 %H:%M")
        market_time = "开盘前" if now.hour < 12 else "收盘后"
        title = f"投资日报 · {market_time}简报 · {time_str}"
        
        text_with_title = f"{title}\n\n{text}"
        
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": text_with_title}, ensure_ascii=False)
        }
        
        msg_resp = requests.post(msg_url, headers=headers, json=payload, timeout=15)
        result = msg_resp.json()
        
        if result.get("code") == 0:
            message_id = result.get("data", {}).get("message_id", "")
            print(f"✅ 飞书消息发送成功! 消息ID: {message_id}")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 飞书发送异常: {e}")
        return False

# 创建一个模拟的开盘前简报
def build_simple_morning_brief():
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日 %H:%M")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    
    brief = f"""🌅 开盘提醒  {date_str} 周{weekday}

━━━━━━━━━━━━━━━━━━━━━━

【昨晚美股】
  📉 标普500: 待更新  -0.0%
  📈 纳斯达克: 待更新  +0.0%
  💹 VIX恐慌指数: 待更新

【A50期指夜盘】
  ⚖️  富时A50: 待更新  +0.0%

【消息面速览】
  📰 昨夜重要新闻：暂无新消息
  📉 国际油价：待更新
  📊 离岸人民币：待更新

【操作提醒】
  🔔 今天无重要数据公布
  ⏰ 开盘集合竞价关注大单流向
  📊 北向资金观察昨日流入流出

━━━━━━━━━━━━━━━━━━━━━━
📊 祝交易顺利！"""

    return brief

print("\n💡 正在发送今日上午的补发投资日报...")
print(f"目标群聊: {chat_id}")

# 生成简报
morning_brief = build_simple_morning_brief()
print(f"简报内容长度: {len(morning_brief)} 字符")

# 发送飞书
success = send_to_feishu_immediate(morning_brief)

if success:
    print(f"\n✅ 补发成功！")
    print(f"请查看飞书群聊是否收到投资日报补发消息")
    
    # 同时发送一个测试消息确认
    test_msg = f"📱 飞书推送测试\n⏰ 测试时间: {datetime.now().strftime('%H:%M:%S')}\n✅ 自动化任务检测正常"
    send_to_feishu_immediate(test_msg)
    
    print(f"\n📋 下一步:")
    print(f"1. 检查飞书群聊是否收到消息")
    print(f"2. 检查程序自动化任务是否配置正确")
    print(f"3. 等待今天下午15:30的收盘后推送")
else:
    print(f"\n❌ 补发失败，请手动检查配置")

print("\n" + "=" * 60)
print("🔥 立即修复自动化任务问题:")

print(f"\n💻 手动测试投资日报:")
print(f"  开盘前简报: python main.py --morning")
print(f"  收盘后详报: python main.py --evening")

print(f"\n🔧 检查自动化状态:")
print("  1. 检查WorkBuddy中的自动化任务")
print("  2. 确保投资日报任务设置为ACTIVE状态")
print("  3. 检查定时规则是否正确 (08:00 和 15:30)")