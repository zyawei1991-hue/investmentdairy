import requests, json, sys
import yaml

print("测试飞书推送...")

# 加载配置
with open("config.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

feishu = cfg.get("feishu", {})
if not feishu.get("enabled"):
    print("飞书推送未启用")
    sys.exit(1)

app_id = feishu["app_id"]
app_secret = feishu["app_secret"]
chat_id = feishu["chat_id"]

print(f"App ID: {app_id[:8]}...")
print(f"Chat ID: {chat_id}")

# 获取token
resp = requests.post(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": app_id, "app_secret": app_secret},
    timeout=10
)
token_data = resp.json()
if token_data["code"] != 0:
    print("Token失败:", token_data)
    sys.exit(1)

token = token_data["tenant_access_token"]
print("Token获取成功")

# 发消息
msg = {
    "receive_id": chat_id,
    "msg_type": "text",
    "content": json.dumps({
        "text": "[飞书推送测试]\\n时间：2026-03-26 13:45\\n\\n投资日报飞书推送配置完成！"
    }, ensure_ascii=False)
}

url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

resp = requests.post(url, headers=headers, json=msg, timeout=15)
result = resp.json()

print("结果code:", result.get("code"))
print("结果msg:", result.get("msg"))

if result.get("code") == 0:
    print("飞书推送成功！")
    print("消息ID:", result.get("data", {}).get("message_id", ""))
    sys.exit(0)
else:
    print("飞书推送失败")
    sys.exit(1)