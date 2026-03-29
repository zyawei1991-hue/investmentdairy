# 投资日报系统 - 部署指南

## 🚀 快速开始

### 系统要求
- Python 3.10+
- Windows/macOS/Linux
- 稳定的网络连接

### 第一步：克隆/下载项目
```bash
# 克隆项目（如果你使用git）
git clone <项目地址>
cd investment-daily

# 或者直接下载项目文件到 investment-daily 目录
```

### 第二步：安装依赖
```bash
pip install -r requirements.txt
```

## 📦 项目文件说明

### 必需的核心文件
```bash
investment-daily/
├── main.py                    # 主程序入口（必需）
├── config.yaml                # 配置文件（必需）
├── requirements.txt           # 依赖列表（必需）
├── PROJECT_OVERVIEW.md        # 项目总览（推荐）
└── DEPLOYMENT_GUIDE.md       # 部署指南（本文件）
```

### 非必需但有用的文件
```bash
investment-daily/
├── tencent_smartsheet_fixed.py  # 智能表格管理器（可选，但推荐）
├── emergency_wrapper.py         # 应急包装脚本（可选）
└── auto_trigger.bat           # 自动触发脚本（Windows）
```

## 🔧 配置设置

### 创建配置文件
复制 `config_template.yaml` 到 `config.yaml` 并编辑：

```bash
# 如果没有配置文件模板
cp config_template.yaml config.yaml  # Linux/Mac
copy config_template.yaml config.yaml  # Windows
```

### 最少必要配置
```yaml
# config.yaml 最少配置

strategy: "value"
market: "A股"

tencent_docs:
  token: "your_token_here"  # 腾讯文档token，需申请
  data_sheet_id: ""  # 智能表格ID，可不配置

feishu:
  enabled: false  # 如果不需要飞书推送
  # app_id: ""
  # app_secret: ""
  # chat_id: ""
```

### 完整配置结构
完整的配置包含以下部分（参考现有config.yaml）：
- 投资风格与参数
- 持仓列表
- API配置
- 飞书推送配置
- 腾讯文档配置
- 智能表格配置

## 🧪 测试运行

### 测试基本功能
```bash
# 检查Python环境
python --version

# 安装依赖
pip install requests
pip install schedule
pip install pyyaml

# 测试基本运行
python main.py --morning
```

### 测试API连接
```bash
python test_api.py  # 测试腾讯财经API
python test_feishu_integration.py  # 测试飞书API（可选）
```

## 📱 飞书推送配置（可选）

### 申请飞书应用
1. 访问 https://open.feishu.cn/app
2. 创建企业自建应用
3. 获取 App ID 和 App Secret
4. 开启「机器人」权限

### 创建推送群聊
1. 在飞书中创建新群聊
2. 右键群聊 → 设置 → 复制群聊ID（chat_id）
3. 将机器人添加到群聊

### 配置飞书
```yaml
# config.yaml 飞书部分
feishu:
  enabled: true
  app_id: "cli_xxxxxx"
  app_secret: "xxxxxxxxxx"
  push_target: "chat_id"
  chat_id: "oc_xxxxxxxxxxxxxx"
```

## 📄 腾讯文档配置（可选）

### 申请腾讯文档token
1. 访问 https://docs.qq.com/openapi
2. 申请开发者token（有效期一年）
3. 获取智能表格ID

### 配置腾讯文档
```yaml
# config.yaml 腾讯文档部分
tencent_docs:
  token: "your_token_here"
  data_sheet_id: "DV0xxxxxxxxxxx"
```

## 🕐 自动化部署

### 手动定时运行
```bash
# 创建定时任务（Linux/macOS）
crontab -e

# 添加以下行（每天8:00和15:30执行）
0 8 * * 1-5 cd /path/to/investment-daily && python main.py --evening
30 15 * * 1-5 cd /path/to/investment-daily && python main.py --evening
```

### 使用WorkBuddy自动化（推荐）
1. 导入项目到WorkBuddy
2. 配置自动化任务
3. 设置执行时间（工作日8:00和15:30）
4. 指定工作目录为项目路径

## 🐛 故障排除

### 常见问题

#### Q1: 运行时报错 "ModuleNotFoundError"
```bash
# 安装缺失的包
pip install requests
pip install schedule
pip install pyyaml
```

#### Q2: API连接失败
- 检查网络连接
- 检查代理设置
- 验证API token有效性

#### Q3: 飞书推送收不到
- 确认飞书机器人已加入群聊
- 检查chat_id是否正确
- 验证app_id/app_secret权限

#### Q4: 智能表格无数据
- 确认腾讯文档token有效
- 检查表格ID是否正确
- 确认有写入权限

### 调试模式
```bash
# 查看详细日志
python main.py --morning --verbose

# 或启用调试模式
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔐 安全注意事项

### 密钥管理
```yaml
# 建议将敏感信息存储在环境变量
# 或在部署时动态注入
# 不要在代码仓库中提交真实的配置文件
```

### 权限控制
- API Token有有效期，定期更新
- 飞书应用权限控制在最小必要范围
- 腾讯文档token妥善保管

## 📊 数据安全

### 本地数据
- config.yaml包含持仓信息，妥善保存
- 定期备份配置和日志文件

### 云端数据
- 云端存储遵循隐私协议
- 智能表格数据加密存储

## 🔄 升级维护

### 备份策略
```bash
# 备份关键文件
cp config.yaml config.yaml.backup.$(date +%Y%m%d)
cp -r logs logs.backup.$(date +%Y%m%d)
```

### 更新检查
```bash
# 检查依赖更新
pip list --outdated

# 更新依赖
pip install --upgrade -r requirements.txt
```

### 数据迁移
如需迁移到新服务器，需要：
1. 复制整个项目文件夹
2. 导出配置文件
3. 在新的环境中重新配置API

## 📞 获取帮助

### 问题上报
如果遇到无法解决的问题，请提供：
1. 操作系统和Python版本
2. 详细的错误信息
3. config.yaml（敏感信息脱敏）
4. 复现步骤

### 联系开发者
通过项目维护者联系技术支持。

## 📄 许可证与使用
本项目仅供学习和内部使用，请遵守相关法律法规和API使用协议。

---

**部署完成！** 🎉

如需进一步优化建议：
1. 代码结构分析
2. 性能优化
3. 功能扩展
4. 安全加固

请提供具体的需求和背景，我们将提供针对性建议。