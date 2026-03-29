# 腾讯文档智能表格集成指南

## 背景
投资日报程序目前生成两类数据：
1. **每日简报** - 发送到飞书群聊的消息
2. **详细报告** - 腾讯文档详报（markdown格式）

**新增需求**：将日报数据存储到腾讯文档智能表格（多维表）中，用于历史数据分析。

## 解决方案
利用已有的腾讯文档MCP能力，使用 **smartsheet.* 工具** 将数据写入智能表格。

## 已完成的模块
1. `tencent_smartsheet.py` - 完整的智能表格管理类
2. 17个字段的表结构设计
3. 数据格式转换逻辑
4. MCP调用适配层

## 集成步骤

### 步骤1：创建智能表格
1. 登录腾讯文档 (https://docs.qq.com)
2. 新建 → 智能表格（或从模板创建）
3. 获取文件ID：从URL中复制 `DVxxxxx` 部分
   - 示例：`https://docs.qq.com/sheet/DV2ZrYUtCaG1odE9G` → 文件ID: `DV2ZrYUtCaG1odE9G`

### 步骤2：更新配置文件
在 `config.yaml` 中修改 `tencent_docs` 配置节：

```yaml
tencent_docs:
  token: "7bd23133a8c346008cc7b86385e1c06d"  # 已有的token
  report_doc_id: "DV1VVTk9OcUxhcEtT"          # 详报文档ID（自动更新）
  data_sheet_id: "你的智能表格文件ID"          # 👈 新增：智能表格文件ID
```

### 步骤3：在主程序中集成
在 `main.py` 的 `build_evening_brief()` 函数中，在创建腾讯文档后添加代码：

**修改位置**（约第1420行）：
```python
# 原有代码
doc_url = write_to_tencent_doc(detail_md, f"投资日报 · {today}")
if doc_url:
    link_msg = f"📄 今日详报已更新：{doc_url}"
    send_wecom(cfg.get("webhook_url", ""), link_msg)
    print(f"\n📄 详报链接: {doc_url}")

# ⬇️ 新增代码：保存到智能表格
try:
    # 导入智能表格模块
    from tencent_smartsheet import TencentSmartSheetManager
    
    # 初始化管理器
    smartsheet = TencentSmartSheetManager()
    
    # 确定报告类型
    report_type = "收盘后" if not is_morning else "开盘前"
    
    # 保存数据到智能表格
    success = smartsheet.save_daily_report(
        report_date=date_str,
        report_type=report_type,
        report_time=datetime.now().strftime("%H:%M"),
        report_data=detail_data,
        doc_url=doc_url  # 传递腾讯文档链接
    )
    
    if success:
        print(f"\n✅ 日报数据已保存到腾讯文档智能表格")
    else:
        print(f"\n⚠️  智能表格保存失败（可能未配置data_sheet_id）")
except ImportError as e:
    print(f"\nℹ️  智能表格模块未找到: {e}")
except Exception as e:
    print(f"\n⚠️  智能表格保存异常: {e}")
```

**注意**：`detail_data` 是已经在函数中生成的数据，包含所有需要的字段（summary, market_stats, ai_analysis等）。

### 步骤4：运行测试
1. 运行测试：`python main.py --evening --test`
2. 检查控制台输出，确认智能表格调用成功
3. 检查腾讯文档智能表格，确认数据已写入

## 数据结构说明

### 智能表格字段（17个）

| 字段名 | 类型 | 说明 | 数据来源 |
|--------|------|------|----------|
| **日期** | 日期 | YYYY-MM-DD | `date_str` |
| **报告类型** | 单选 | 开盘前/收盘后 | `is_morning` 判断 |
| **报告时间** | 文本 | HH:MM | 当前时间 |
| **总市值** | 货币 | 元，两位小数 | `summary.total_value` |
| **当日盈亏** | 货币 | 元，两位小数 | `summary.daily_profit_loss` |
| **总盈亏** | 货币 | 元，两位小数 | `summary.total_profit_loss` |
| **仓位比例** | 百分比 | 如 78.6% | `summary.position_ratio` |
| **持仓数量** | 数字 | 持仓标的数量 | `summary.holding_count` |
| **上证指数** | 文本 | 如 +0.45% | `market_stats.sh_index` |
| **深证成指** | 文本 | 如 +0.78% | `market_stats.sz_index` |
| **创业板指** | 文本 | 如 +1.23% | `market_stats.cy_index` |
| **估值温度** | 单选 | 低温/中温/高温 | `market_stats.market_temperature` |
| **北向资金** | 文本 | 净流入 ¥15.2亿元 | `market_stats.north_fund_flow` |
| **涨跌家数** | 文本 | 涨 2680 家 / 跌 1820 家 | `market_stats.advance_decline` |
| **AI市场趋势** | 文本 | AI分析摘要（前100字） | `ai_analysis.market_summary` |
| **AI操作建议** | 文本 | AI建议（前100字） | `ai_analysis.suggestions` |
| **腾讯文档链接** | 超链接 | 查看详情链接 | `doc_url` |

### 数据类型映射
- **货币**：数字，自动格式化为人民币
- **百分比**：小数（78.6% → 0.786）
- **日期**：时间戳字符串（毫秒）
- **单选**：选项对象数组 `[{"text": "开盘前"}]`
- **超链接**：链接对象 `[{"text": "查看详情", "type": "url", "link": "https://..."}]`
- **文本**：文本对象数组 `[{"text": "内容", "type": "text"}]`

## 错误处理
模块包含完整的错误处理：
1. **缺少Token**：打印警告，不影响主流程
2. **缺少data_sheet_id**：打印提示，不执行保存
3. **MCP调用失败**：记录错误，不影响日报生成
4. **字段类型不匹配**：自动转换和格式化

## 测试验证
1. **单元测试**：直接运行 `python tencent_smartsheet.py`
2. **集成测试**：运行 `python main.py --evening --test`
3. **生产测试**：第二天自动运行时查看结果

## 维护说明
1. **字段结构调整**：修改 `tencent_smartsheet.py` 中的 `FIELD_DEFINITIONS`
2. **数据映射调整**：修改 `prepare_record_data()` 方法
3. **MCP工具版本**：需保持腾讯文档MCP服务可用

## 时间计划
- **立即执行**：创建智能表格，更新配置（5分钟）
- **代码集成**：在main.py中添加调用（10分钟）
- **测试验证**：运行测试，确认数据写入（5分钟）
- **生产运行**：明天08:00和15:30自动执行

## 价值收益
1. **历史数据持久化**：自动保存所有日报历史记录
2. **数据分析能力**：支持筛选、排序、图表分析
3. **数据可视化**：腾讯文档智能表格的内置图表功能
4. **团队协作**：与团队分享投资数据
5. **决策支持**：长期趋势分析，辅助投资决策