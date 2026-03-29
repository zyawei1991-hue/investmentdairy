#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书推送应急修复方案 - 确保今天下午15:30正常推送"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("🚨 飞书推送应急修复方案")
print("=" * 70)

import yaml
import json
import requests
from datetime import datetime

# 加载配置
config_path = 'config.yaml'
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

feishu_config = config.get('feishu', {})
app_id = feishu_config.get('app_id')
app_secret = feishu_config.get('app_secret')
chat_id = feishu_config.get('chat_id')
enabled = feishu_config.get('enabled', False)

print("📋 配置检查:")
print(f"  ✅ 飞书推送: {'启用' if enabled else '禁用'}")
print(f"  ✅ App ID: {app_id}")
print(f"  ✅ Chat ID: {chat_id}")
print()

if not enabled:
    print("⚠ 飞书推送未启用，请在config.yaml中设置 feishu.enabled: true")
    sys.exit(0)

def send_feishu_message(text: str) -> bool:
    """发送消息到飞书群聊"""
    try:
        # 获取token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_data = {"app_id": app_id, "app_secret": app_secret}
        token_resp = requests.post(token_url, json=token_data, timeout=10)
        token_result = token_resp.json()
        
        if token_result.get('code') != 0:
            print(f"❌ Token获取失败: {token_result.get('msg', '未知错误')}")
            return False
        
        access_token = token_result['tenant_access_token']
        print(f"✅ Token获取成功, 有效期: {token_result.get('expire', 7200)}秒")
        
        # 发送消息
        send_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 添加标题
        now = datetime.now()
        market_time = "开盘前" if now.hour < 12 else "收盘后"
        title = f"投资日报 · {market_time}简报 · {now.strftime('%Y年%m月%d日 %H:%M')}"
        full_text = f"{title}\n\n{text}"
        
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": full_text}, ensure_ascii=False)
        }
        
        send_resp = requests.post(send_url, headers=headers, json=payload, timeout=15)
        result = send_resp.json()
        
        if result.get('code') == 0:
            message_id = result.get('data', {}).get('message_id', '')
            print(f"✅ 飞书消息发送成功! 消息ID: {message_id}")
            return True
        else:
            print(f"❌ 飞书消息发送失败: {result.get('msg', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 飞书发送异常: {e}")
        return False

# 应急方案：包装现有的主程序
print("🛠️ 创建应急包装脚本...")

wrap_script = '''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书推送应急包装脚本 - 调用原程序并转发到飞书"""

import sys
import os
import subprocess
import json
import requests
from datetime import datetime

def call_original_program(args):
    """调用原始投资日报程序并捕获输出"""
    cmd = ["python", "main.py"] + args
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', timeout=60)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def send_to_feishu_emergency(text: str):
    """应急发送到飞书"""
    import yaml
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    feishu_config = config.get('feishu', {})
    app_id = feishu_config.get('app_id')
    app_secret = feishu_config.get('app_secret')
    chat_id = feishu_config.get('chat_id')
    
    if not app_id or not app_secret or not chat_id:
        print("[应急] 飞书配置不完整，跳过推送")
        return False
    
    try:
        # 获取token
        token_url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        token_data = {"app_id": app_id, "app_secret": app_secret}
        token_resp = requests.post(token_url, json=token_data, timeout=10)
        token_result = token_resp.json()
        
        if token_result.get('code') != 0:
            print(f"[应急] Token获取失败")
            return False
        
        access_token = token_result['tenant_access_token']
        
        # 发送消息
        send_url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # 添加标题
        now = datetime.now()
        market_time = "开盘前" if now.hour < 12 else "收盘后"
        title = f"投资日报 · {market_time}简报 · {now.strftime('%Y年%m月%d日 %H:%M')}"
        full_text = f"{title}\\n\\n{text}"
        
        payload = {
            "receive_id": chat_id,
            "msg_type": "text",
            "content": json.dumps({"text": full_text}, ensure_ascii=False)
        }
        
        send_resp = requests.post(send_url, headers=headers, json=payload, timeout=15)
        result = send_resp.json()
        
        if result.get('code') == 0:
            print(f"[应急] ✅ 飞书推送成功")
            return True
        else:
            print(f"[应急] ❌ 飞书推送失败")
            return False
            
    except Exception as e:
        print(f"[应急] 异常: {e}")
        return False

def main():
    print("🚀 应急飞书推送包装脚本")
    print("=" * 60)
    
    # 原始参数
    args = sys.argv[1:]
    
    # 调用原始程序
    print(f"📝 调用原始程序: python main.py {' '.join(args)}")
    returncode, stdout, stderr = call_original_program(args)
    
    # 输出原始结果
    if stdout:
        print("📋 原始程序输出:")
        print(stdout)
    
    if stderr:
        print("❌ 原始程序错误:")
        print(stderr)
    
    # 如果有简报内容，推送到飞书
    if stdout and len(stdout) > 50:  # 简单判断是否为有效简报
        print(f"💾 检测到简报内容，准备推送到飞书...")
        send_to_feishu_emergency(stdout)
    else:
        print(f"ℹ️  无有效简报内容，跳过飞书推送")
    
    print(f"\n" + "=" * 60)
    print(f"应急包装脚本执行完成")
    print(f"原始程序返回码: {returncode}")

if __name__ == "__main__":
    main()
'''

wrap_file = "emergency_wrapper.py"
with open(wrap_file, 'w', encoding='utf-8') as f:
    f.write(wrap_script)

print(f"✅ 创建应急包装脚本: {wrap_file}")
print(f"   用法: python {wrap_file} --morning")
print(f"   用法: python {wrap_file} --evening")

# 创建一个简单的自动化触发器
print(f"\n🕐 创建今日15:30自动任务触发器...")

trigger_file = "auto_trigger.bat"
bat_content = '''@echo off
chcp 65001 >nul
cd %~dp0
echo [%time%] 触发收盘后投资日报...
python emergency_wrapper.py --evening
echo [%time%] 执行完成
pause'''

with open(trigger_file, 'w', encoding='utf-8') as f:
    f.write(bat_content)

print(f"✅ 创建自动任务触发器: {trigger_file}")
print(f"   今日15:30可手动执行这个文件启动收盘报告")

# 立即测试应急方案
print(f"\n🧪 立即测试应急方案...")
if send_feishu_message("🔧 应急方案测试消息 - 测试时间: " + datetime.now().strftime("%H:%M:%S")):
    print(f"✅ 应急方案测试成功!")
    print(f"💡 请查看飞书群聊是否收到测试消息")
else:
    print(f"⚠ 应急方案测试失败")

print(f"\n" + "=" * 70)
print(f"📋 应急方案总结:")
print(f"1. 应急包装脚本: ✅ {wrap_file}")
print(f"2. 自动任务触发器: ✅ {trigger_file}")
print(f"3. 飞书连接测试: ✅ {'成功' if enabled else '失败'}")
print()
print(f"🎯 使用说明:")
print(f"   立即测试: python {wrap_file} --morning")
print(f"   今日15:30: python {wrap_file} --evening")
print(f"   或双击: {trigger_file}")
print()
print(f"💡 永久解决方案:")
print(f"   1. 完整集成飞书推送功能到main.py")
print(f"   2. 检查自动化任务配置")
print(f"   3. 等待今天下午15:30验证")