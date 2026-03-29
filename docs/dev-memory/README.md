---
last_updated: 2026-03-29T16:25:00+08:00
updated_by: AI-Agent
related_projects: [investmentdairy]
tags: [index, dev-memory]
---

# 投资日报系统 - 开发记忆知识库

> 📍 **单一信息源** - 所有开发相关信息都在这里记录和同步

---

## 🎯 这个知识库的作用

| 作用 | 说明 |
|------|------|
| 📖 **项目上下文** | 技术栈、架构、配置说明 |
| 📋 **当前任务** | 正在进行中的开发任务 |
| 📅 **每日更新** | 开发进展、问题、解决方案 |
| 🏗️ **项目档案** | 关键信息和里程碑 |
| 📝 **决策记录** | 重要技术/业务决策 |

---

## 📂 目录结构

```
docs/dev-memory/
├── README.md              # 本文件（索引）
├── CONTEXT.md             # 项目上下文
├── CURRENT.md             # 当前进行中的任务
├── daily/                 # 每日更新日志
├── projects/              # 项目档案
├── decisions/             # 决策记录（ADR）
└── templates/             # 文档模板
```

---

## 🚀 快速开始

### 新开发者入职

```bash
# 1. 克隆仓库
git clone https://github.com/zyawei1991-hue/investmentdairy.git
cd investmentdairy

# 2. 阅读核心文档
cat docs/dev-memory/CONTEXT.md     # 了解项目上下文
cat docs/dev-memory/CURRENT.md     # 查看当前任务
cat README.md                      # 项目说明

# 3. 配置环境
cp config_template.yaml config.yaml
# 编辑config.yaml填写实际配置

# 4. 运行测试
python main.py --test
```

### AI工具集成

```bash
# 启动时自动加载记忆
git pull origin master
CONTEXT=$(cat docs/dev-memory/CONTEXT.md)
CURRENT=$(cat docs/dev-memory/CURRENT.md)

# 完成任务后更新记忆
echo "## [任务描述]\n完成内容...\n" >> docs/dev-memory/daily/$(date +%Y-%m-%d).md
git add docs/dev-memory/ && git commit -m "docs: 更新开发记忆" && git push
```

---

## 📋 当前状态

| 项目 | 状态 | 说明 |
|------|------|------|
| 定时推送 | 🟢 运行中 | 早盘8:00 + 收盘15:30 |
| 多维表格 | 🟢 正常 | 数据归档正常 |
| AI分析 | 🟢 正常 | Claude Opus 4.5 |

---

## 🔗 相关链接

- [DigiVita开发记忆](https://github.com/zyawei1991-hue/digivita-collaboration/tree/develop/docs/dev-memory)
- [项目总览](../PROJECT_OVERVIEW.md)
- [部署指南](../DEPLOYMENT_GUIDE.md)

---

## 📝 最近更新

| 日期 | 更新内容 |
|------|---------|
| 2026-03-29 | 项目同步到GitHub，开发记忆知识库搭建 |

---

**维护者**: AI Agent + 张亚威

**更新频率**: 每日/每次重要变更
