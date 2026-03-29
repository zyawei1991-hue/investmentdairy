---
last_updated: 2026-03-29T16:25:00+08:00
updated_by: AI-Agent
tags: [context, architecture, config]
---

# 项目上下文

> 所有开发者、AI工具在开始工作前必须阅读此文档

---

## 🎯 项目概述

**投资日报系统** 是一个AI驱动的智能投资分析与推送系统，实现投资组合的自动化监控、分析和报告推送。

---

## 🏗️ 技术架构

### 核心技术

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.12 | 主语言 |
| FastAPI | - | API框架（可选） |
| requests | - | HTTP请求 |

### AI能力

| 服务 | 用途 |
|------|------|
| Claude Opus 4.5 | 投资分析、建议生成 |
| Web Search | 实时行情、新闻获取 |

### 飞书集成

| 功能 | 说明 |
|------|------|
| 飞书OpenAPI | 消息推送、文档创建 |
| 多维表格 | 数据存储和历史归档 |

---

## 📁 项目结构

```
investmentdairy/
├── main.py                      # 主程序入口
├── feishu_client.py             # 飞书API封装
├── tencent_smartsheet_fixed.py  # 多维表格操作
├── config_template.yaml         # 配置模板
├── config.yaml                  # 实际配置（不提交Git）
├── docs/
│   └── dev-memory/              # 开发记忆知识库
├── scripts/                     # 脚本
└── test_files/                  # 测试文件
```

---

## ⏰ 定时任务

| 任务 | 时间 | 说明 |
|------|------|------|
| 早盘推送 | 工作日 8:00 | 隔夜外盘 + 昨日A股 + 今日关注 |
| 收盘推送 | 工作日 15:30 | 市场概览 + 持仓监控 + AI建议 |

**休市日自动跳过**

---

## 📊 数据结构

### 多维表格

| 表名 | 用途 | 字段 |
|------|------|------|
| 持仓记录 | 股票、ETF、转债持仓 | 股票代码、名称、持仓数、成本价、现价、盈亏 |
| 每日行情 | 大盘指数、北向资金 | 日期、上证、深证、创业板、北向资金 |
| 资金动向 | 板块资金流向 | 日期、板块、净流入、涨跌幅 |
| 每日投资建议 | AI分析和建议 | 日期、建议类型、内容、风险提示 |
| 财务分析 | 持仓股票财务指标 | 股票代码、ROE、毛利率、净利率、负债率、市盈率 |
| ETF配置建议 | ETF估值和建议比例 | ETF代码、名称、当前价格、估值分位、建议比例 |

---

## 🔐 配置说明

### config.yaml 结构

```yaml
# 飞书配置
feishu:
  app_id: cli_xxx
  app_secret: xxx
  group_id: oc_xxx  # 推送的群聊ID

# AI配置
ai:
  api_key: xxx
  model: claude-opus-4-5
  base_url: https://api.anthropic.com

# 持仓配置
holdings:
  stocks:
    - code: "600000.SH"
      name: "浦发银行"
      shares: 1000
      cost: 10.5
  etfs:
    - code: "510300.SH"
      name: "沪深300ETF"
      shares: 500
      cost: 4.2
  bonds:
    - code: "110xxx.SH"
      name: "XX转债"
      shares: 100
      cost: 120

# 多维表格配置
bitable:
  app_token: xxx
  table_ids:
    holdings: tblxxx
    daily_market: tblxxx
    capital_flow: tblxxx
    advice: tblxxx
```

### 必需的环境变量

```bash
# 如果不使用config.yaml，可以使用环境变量
export FEISHU_APP_ID=cli_xxx
export FEISHU_APP_SECRET=xxx
export AI_API_KEY=xxx
```

---

## 🔄 工作流程

### 早盘推送流程

```
1. 获取隔夜美股行情
2. 获取昨日A股收盘行情
3. 获取北向资金流向
4. 读取最新持仓记录
5. 计算持仓盈亏
6. 生成AI分析建议
7. 推送飞书消息简报
8. 创建飞书文档详报
```

### 收盘推送流程

```
1. 获取今日A股收盘行情
2. 获取北向资金流向
3. 获取板块资金动向
4. 更新持仓现价和盈亏
5. 更新多维表格记录
6. 生成AI分析和建议
7. 推送飞书消息简报
8. 创建飞书文档详报
```

---

## 🚨 常见问题

### Q: 如何测试推送？

```bash
python main.py --test --type morning  # 测试早盘推送
python main.py --test --type closing  # 测试收盘推送
```

### Q: 如何添加新持仓？

编辑 `config.yaml` 的 `holdings` 部分，或通过飞书多维表格添加记录。

### Q: 如何修改推送时间？

修改定时任务配置（cron或系统任务调度）。

### Q: 如何查看日志？

查看控制台输出或重定向到日志文件：

```bash
python main.py >> logs/investment-$(date +%Y%m%d).log 2>&1
```

---

## 📞 联系方式

- **项目负责人**: 张亚威
- **技术支持**: AI Agent

---

**重要**: 开始任何开发工作前，请务必阅读 `CURRENT.md` 了解当前任务状态。
