# 投资日报系统 - 打包信息

## 打包日期
2026-03-27 22:08:13

## 版本信息
- 主版本: 价值投资版 (v5.0)
- 更新时间: 2026-03-27
- 状态: 稳定运行

## 包含的核心文件
- main.py
- config_template.yaml
- requirements.txt
- README.md
- tencent_smartsheet_fixed.py
- tencent_smartsheet_clean.py
- emergency_wrapper.py
- auto_trigger.bat
- PROJECT_OVERVIEW.md
- DEPLOYMENT_GUIDE.md

## 主要功能特性
1. 每日自动生成投资日报
2. 开盘前简报 (08:00)
3. 收盘后详报 (15:30)
4. 智能表格数据存储
5. 飞书推送 (可配置)
6. AI分析与建议生成

## 部署结构
```
investment-daily/
├── main.py                    # 主程序入口
├── config.yaml               # 配置文件 (需从模板复制)
├── requirements.txt          # 依赖包列表
├── tencent_smartsheet_fixed.py  # 智能表格管理器
├── emergency_wrapper.py      # 应急包装脚本
├── PROJECT_OVERVIEW.md      # 项目总览
├── DEPLOYMENT_GUIDE.md      # 部署指南
├── scripts/                 # 工具脚本目录
├── test_files/             # 测试文件目录
└── docs/                   # 文档目录
```

## 部署前准备
1. 复制 `config_template.yaml` 为 `config.yaml`
2. 填写真实配置信息
3. 安装依赖: `pip install -r requirements.txt`
4. 测试运行: `python main.py --morning`

## 敏感信息保护
重要提醒
- 真实配置文件 `config.yaml` 不在打包文件中
- API密钥、账号密码等敏感信息已脱敏
- 部署时请使用自己的真实配置

## 技术支持
如有问题，请参考 `DEPLOYMENT_GUIDE.md` 或联系开发者。
