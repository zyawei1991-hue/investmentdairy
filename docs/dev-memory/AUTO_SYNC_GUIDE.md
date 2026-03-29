# 开发记忆知识库 - 全自动化配置指南

> 🎯 目标：实现完全自动化的协同开发，避免人为失误

---

## ✅ 已配置的自动化功能

### 1️⃣ GitHub Actions 自动化

| 功能 | 触发条件 | 说明 |
|------|---------|------|
| **自动更新时间戳** | 记忆文件变更 | 更新README.md中的last_updated |
| **自动记录每日日志** | develop/master分支push | 自动记录提交信息到daily/ |
| **自动同步分支** | develop分支push | 自动合并到staging和main |
| **飞书通知** | 记忆更新（可选） | 推送通知到飞书群 |
| **手动触发** | 随时 | 支持手动运行workflow |

### 2️⃣ 自动化流程

```
开发者/AI提交代码
    ↓
GitHub检测到push
    ↓
自动执行GitHub Actions
    ↓
更新开发记忆文件
    ↓
自动提交并推送
    ↓
（可选）发送飞书通知
```

---

## 🔧 配置步骤

### 步骤1：启用GitHub Actions（已自动启用）

两个仓库的GitHub Actions已配置完成：
- [DigiVita Workflow](https://github.com/zyawei1991-hue/digivita-collaboration/actions)
- [投资日报 Workflow](https://github.com/zyawei1991-hue/investmentdairy/actions)

### 步骤2：配置飞书通知（可选）

如果需要记忆更新时推送飞书通知：

1. **获取飞书机器人Webhook**
   - 在飞书群聊中添加机器人
   - 选择"自定义机器人"
   - 复制Webhook地址

2. **配置GitHub Secret**
   - 打开GitHub仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - Name: `FEISHU_WEBHOOK`
   - Value: `https://open.feishu.cn/open-apis/bot/v2/hook/xxx`
   - 点击 "Add secret"

3. **验证配置**
   - 推送一次代码
   - 检查飞书群是否收到通知

---

## 📋 开发者工作流（全自动）

### 开始工作

```bash
# 拉取最新代码和记忆
git checkout develop
git pull origin develop

# 查看项目上下文
cat docs/dev-memory/CONTEXT.md

# 查看当前任务
cat docs/dev-memory/CURRENT.md
```

### 开发功能

```bash
# 创建功能分支
git checkout -b feature/功能名-你的名字

# 开发代码...

# 提交代码
git add .
git commit -m "feat(模块): 功能描述"
git push origin feature/功能名-你的名字

# 在GitHub创建Pull Request合并到develop
```

### 自动执行（无需操作）

✅ GitHub Actions会自动：
- 记录你的提交到每日日志
- 更新记忆时间戳
- 同步到所有分支
- 发送飞书通知（如已配置）

---

## 🤖 AI工具集成

### Kiro集成

**启动时自动加载**：
```bash
# 在Kiro的启动配置中添加
git pull origin develop
cat docs/dev-memory/CONTEXT.md
cat docs/dev-memory/CURRENT.md
```

**完成后自动更新**：
```bash
# Kiro完成任务后执行
git add docs/dev-memory/
git commit -m "docs: Kiro协助完成XXX"
git push origin develop
# GitHub Actions会自动记录
```

### AI Agent集成

**我的自动化流程**：
1. 启动时自动拉取最新记忆
2. 完成任务后自动更新记忆
3. 推送后GitHub Actions自动记录

---

## 📊 自动化效果

### 示例：开发者A完成功能

```bash
# 开发者A的操作
git checkout develop
git pull
git checkout -b feature/user-login-devA
# 开发代码...
git commit -m "feat(auth): 实现用户登录"
git push origin feature/user-login-devA
# 创建PR合并到develop
```

**GitHub Actions自动执行**：
```markdown
# docs/dev-memory/daily/2026-03-29.md

### 🤖 自动记录 16:51
- **提交**: feat(auth): 实现用户登录
- **作者**: devA
- **分支**: develop
- **文件**: src/auth/login.tsx, backend/routers/auth.py
```

### 示例：AI助手完成任务

```bash
# AI助手的操作
git pull origin develop
# 完成任务...
git add docs/dev-memory/
git commit -m "docs: AI助手优化持仓分析算法"
git push origin develop
```

**GitHub Actions自动执行**：
```markdown
# docs/dev-memory/daily/2026-03-29.md

### 🤖 自动记录 17:12
- **提交**: docs: AI助手优化持仓分析算法
- **作者**: AI-Agent
- **分支**: develop
- **文件**: docs/dev-memory/CURRENT.md, main.py
```

---

## 🎯 完整工作流程图

```
┌─────────────────────────────────────────────────────────┐
│                    开发者/AI开始工作                      │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  git pull origin develop        │
        │  拉取最新代码和记忆              │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  阅读 CONTEXT.md                │
        │  了解项目上下文                  │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  阅读 CURRENT.md                │
        │  了解当前任务                    │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  开发功能/完成任务               │
        └─────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  git commit + git push          │
        │  提交代码                        │
        └─────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              GitHub Actions 自动执行                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ✅ 更新记忆时间戳                                │   │
│  │ ✅ 记录到每日日志                                │   │
│  │ ✅ 同步到所有分支                                │   │
│  │ ✅ 发送飞书通知（如已配置）                       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────────────────────┐
        │  其他开发者/AI拉取最新记忆        │
        │  看到你的更新                     │
        └─────────────────────────────────┘
```

---

## ⚠️ 注意事项

### 1. 避免手动编辑每日日志

每日日志由GitHub Actions自动生成，手动编辑会被覆盖。

如果需要添加额外说明，使用：
```bash
# 在提交信息中添加详细说明
git commit -m "feat(auth): 实现用户登录

- 添加前端登录页面
- 实现后端JWT认证
- 集成飞书登录
- 更新开发记忆"
```

### 2. 重要决策需要手动记录

重要决策仍需手动创建ADR：
```bash
# 创建决策记录
cp docs/dev-memory/templates/decision-record.md docs/dev-memory/decisions/ADR-XXX-title.md
# 编辑内容
git add docs/dev-memory/decisions/
git commit -m "docs: 添加决策记录 ADR-XXX"
git push origin develop
```

### 3. 冲突处理

如果GitHub Actions自动合并失败：
- GitHub会发送邮件通知
- 需要手动解决冲突
- 重新推送后自动继续

---

## 🔍 验证配置

### 检查GitHub Actions状态

访问仓库的Actions页面：
- [DigiVita Actions](https://github.com/zyawei1991-hue/digivita-collaboration/actions)
- [投资日报 Actions](https://github.com/zyawei1991-hue/investmentdairy/actions)

### 手动触发测试

```bash
# 在GitHub Actions页面
# 点击 "Run workflow" 按钮
# 手动触发一次测试
```

### 查看执行日志

每次GitHub Actions执行都会生成详细日志：
- 更新了哪些文件
- 记录了哪些内容
- 是否发送了通知

---

## 📞 支持

如有问题，请：
1. 检查GitHub Actions日志
2. 查看本文档
3. 联系项目负责人

---

**维护者**: AI Agent + GitHub Actions

**更新时间**: 2026-03-29
