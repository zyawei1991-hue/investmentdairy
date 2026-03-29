---
last_updated: 2026-03-29T16:26:00+08:00
updated_by: AI-Agent
tags: [ADR, decision, knowledge-base]
---

# ADR-001: 使用GitHub作为开发记忆知识库

## 状态

✅ 已采纳

## 背景

投资日报系统需要建立开发记忆知识库，用于记录项目上下文、任务进展、技术决策等信息。同时需要与DigiVita项目的开发记忆统一管理。

## 决策

使用**GitHub仓库**作为开发记忆知识库，与DigiVita项目保持一致。

## 理由

1. **与DigiVita统一**: 两个项目使用相同的开发记忆管理方式
2. **版本控制**: 每次更新都有commit记录，可追溯历史
3. **与代码关联**: 开发记忆和代码在同一平台，方便对照
4. **权限统一**: 已有GitHub Token，无需额外配置
5. **多工具支持**: 支持AI、CI/CD等工具集成

## 影响

### 正面
- 跨项目协作更方便
- 版本历史完整
- 开发者熟悉的Markdown格式

### 负面
- 不支持实时协作编辑

## 实施日期

2026-03-29

## 相关文档

- [DigiVita开发记忆](https://github.com/zyawei1991-hue/digivita-collaboration/tree/develop/docs/dev-memory)
- [开发记忆索引](../README.md)
