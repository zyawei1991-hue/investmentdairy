"""
投资日报主程序（价值投资版 v3）- 飞书版
- 开盘前 08:00：市场概览 + 估值温度 + 持仓关注提醒 + 飞书推送
- 收盘后 15:30：简报（持仓汇总）+ 飞书推送 + 飞书文档详报 + 飞书多维表格存储
"""

import requests
import schedule
import time
import yaml
import sys
import re
import json
import threading
import urllib3
from datetime import datetime, date
from pathlib import Path

# ── 飞书模块 ──────────────────────────────────────
try:
    from feishu_client import (
        FeishuClient, 
        FeishuBitableClient,
        send_feishu_message,
        write_to_feishu_doc,
        save_to_feishu_bitable
    )
    FEISHU_AVAILABLE = True
except ImportError:
    FEISHU_AVAILABLE = False
    print("⚠ 飞书模块未找到，飞书推送功能受限")

# ── 腾讯智能表格模块（保留作为备选）──────────────────
try:
    from tencent_smartsheet_fixed import TencentSmartSheetManager  # 使用修复版
    SMART_SHEET_AVAILABLE = True
    # 智能表格功能开关（因权限问题暂时关闭）
    SMART_SHEET_ENABLED = False  # 禁用腾讯智能表格，改用飞书多维表格
except ImportError:
    SMART_SHEET_AVAILABLE = False
    SMART_SHEET_ENABLED = False
    print("⚠ 智能表格模块未找到，数据存储功能受限")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ── 路径 ──────────────────────────────────────────
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.yaml"


# ── 配置加载 ──────────────────────────────────────
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── 股票代码前缀识别 ──────────────────────────────
def get_full_code(code: str) -> str:
    """根据股票代码自动添加市场前缀"""
    code = str(code).zfill(6)
    if code.startswith(("sh", "sz")):
        return code
    # 上交所：60xxxx主板、68xxxx科创板、51/56/58xxxx ETF、11xxxx可转债
    if code.startswith(("60", "68", "51", "56", "58", "11")):
        return f"sh{code}"
    # 深交所：00xxxx、30xxxx、15/16xxxx ETF、12xxxx可转债
    return f"sz{code}"


# ── 网络会话 ──────────────────────────────────────
def _new_session():
    s = requests.Session()
    s.trust_env = False
    s.verify = False
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/'
    })
    return s


def _calc_change(price, pre_close):
    if pre_close and pre_close > 0 and price > 0:
        change = price - pre_close
        change_pct = change / pre_close * 100
        return change, change_pct
    return 0, 0


# ── 个股/指数行情（腾讯API）────────────────────────
def fetch_quote_tencent(code: str) -> dict:
    full_code = get_full_code(code)
    url = f"https://qt.gtimg.cn/q={full_code}"
    session = _new_session()
    resp = session.get(url, timeout=10)
    resp.encoding = 'gbk'
    match = re.search(r'v_.*?="(.*?)"', resp.text.strip())
    if not match:
        raise Exception("响应格式异常")
    data = match.group(1).split('~')
    if len(data) < 32:
        raise Exception(f"数据不完整: {len(data)} 字段")
    price = float(data[3]) if data[3] else 0
    pre_close = float(data[4]) if data[4] else 0
    change, change_pct = _calc_change(price, pre_close)

    # field[39] = PE（腾讯接口，直接为倍数，非0.01倍）
    pe = None
    if len(data) > 39 and data[39]:
        try:
            pe_val = float(data[39])
            pe = pe_val if pe_val > 0 else None
        except:
            pass

    # field[46] = PB（市净率）
    pb = None
    if len(data) > 46 and data[46]:
        try:
            pb_val = float(data[46])
            pb = pb_val if pb_val > 0 else None
        except:
            pass

    return {
        "name": data[1],
        "price": price,
        "pre_close": pre_close,
        "open": float(data[5]) if data[5] else 0,
        "high": float(data[7]) if data[7] else 0,
        "low": float(data[8]) if data[8] else 0,
        "volume": float(data[6]) if data[6] else 0,
        "amount": float(data[37]) * 100 if len(data) > 37 and data[37] else 0,  # 百元→元
        "change": change,
        "change_pct": change_pct,
        "pe": pe,
        "pb": pb,
    }


def fetch_quote_eastmoney(code: str) -> dict:
    """东方财富行情（备用）"""
    full_code = get_full_code(code)
    market = 1 if full_code.startswith("sh") else 0
    pure_code = full_code[2:]
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{pure_code}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60"
    session = _new_session()
    resp = session.get(url, timeout=10)
    data = resp.json().get("data", {})
    if not data:
        raise Exception("无数据")
    price = data.get("f43", 0) / 100
    pre_close = data.get("f60", 0) / 100
    change, change_pct = _calc_change(price, pre_close)
    return {
        "name": data.get("f58", ""),
        "price": price,
        "pre_close": pre_close,
        "open": data.get("f46", 0) / 100,
        "high": data.get("f44", 0) / 100,
        "low": data.get("f45", 0) / 100,
        "volume": data.get("f47", 0),
        "amount": data.get("f48", 0),
        "change": change,
        "change_pct": change_pct,
        "pe": None,
    }


def fetch_quote(code: str, max_retries=3) -> dict:
    for attempt in range(max_retries):
        try:
            return fetch_quote_tencent(code)
        except Exception as e:
            print(f"  ⚠️ 腾讯源 尝试{attempt+1}/{max_retries} [{code}]: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)
    try:
        print(f"  🔄 切换东财源 [{code}]")
        return fetch_quote_eastmoney(code)
    except Exception as e:
        raise Exception(f"所有数据源失败 [{code}]: {e}")


# ── 市场情绪数据 ──────────────────────────────────
def fetch_market_breadth() -> dict:
    """
    获取A股涨跌家数。
    策略：东财行情列表分页统计，pz=100，两次请求（升/降序）
    获取总数 total，以及涨幅榜末位/跌幅榜末位，估算涨跌比。
    """
    try:
        session = _new_session()
        base_url = (
            "https://push2.eastmoney.com/api/qt/clist/get"
            "?pn=1&pz=100&np=1&fltt=2&invt=2&fid=f3"
            "&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80%2Cm%3A1+t%3A2%2Cm%3A1+t%3A23%2Cm%3A0+t%3A81+s%3A2048"
            "&fields=f3&ut=bd1d9ddb04089700cf9c27f6f7426281"
        )
        # 降序（涨幅前100）
        r1 = session.get(base_url + "&po=1", timeout=10)
        d1 = r1.json()
        total = d1.get("data", {}).get("total", 0)
        items_up = d1.get("data", {}).get("diff", [])

        # 升序（跌幅前100）
        r2 = session.get(base_url + "&po=0", timeout=10)
        d2 = r2.json()
        items_down = d2.get("data", {}).get("diff", [])

        # 统计两个样本
        up_in_up_sample = sum(1 for x in items_up if x.get("f3", 0) > 0)
        up_in_down_sample = sum(1 for x in items_down if x.get("f3", 0) > 0)
        down_in_up_sample = sum(1 for x in items_up if x.get("f3", 0) < 0)
        down_in_down_sample = sum(1 for x in items_down if x.get("f3", 0) < 0)

        # 涨幅榜100中全涨 → 说明今天涨家数至少有up_in_up_sample家
        # 涨幅末位的值
        last_up_val = items_up[-1].get("f3", 0) if items_up else 0
        # 跌幅末位的值
        last_down_val = items_down[-1].get("f3", 0) if items_down else 0

        # 粗估：如果涨幅前100末位还>0，说明涨家数>100
        # 用总数×涨幅比例来估算（这是近似值）
        # 更好方案：用涨幅>0 的比例 × total
        # 由于只有100条，我们用以下逻辑：
        # 涨家数近似 = up_in_up_sample样本全涨，last_up_val是它的下限
        # 跌家数近似 = down_in_down_sample

        # 实际上东财接口限制100条，我们取二次请求并合并
        all_f3 = ([x.get("f3", 0) for x in items_up] +
                  [x.get("f3", 0) for x in items_down])
        # 去重后的分布不代表全市场，但可以用来展示大致情绪
        # 最终用 total 和样本末位的值来提示

        return {
            "total": total,
            "up_min": up_in_up_sample,   # 涨家数下限（实际更多）
            "down_min": down_in_down_sample,  # 跌家数下限
            "last_up": last_up_val,
            "last_down": last_down_val,
            "note": f"全市场{total}只，涨幅榜末位{last_up_val:+.1f}%，跌幅榜末位{last_down_val:+.1f}%",
        }
    except Exception as e:
        return {"error": str(e)}


def generate_ai_analysis(summary: dict, idx_data: list, breadth: dict,
                          nb: dict, news_data: dict, results: list,
                          etf_val: dict = None) -> str:
    """
    调用 AI 生成今日市场总结 + 持仓估值分析 + 操作建议。
    etf_val: fetch_etf_valuation() 的返回值，包含ETF对应指数PE
    失败时返回空字符串，不影响日报其他部分。
    """
    if etf_val is None:
        etf_val = {}
    try:
        # ── 组装 prompt 上下文 ──
        # 1. 大盘情况
        idx_lines = []
        for idx in idx_data:
            if "error" not in idx:
                q = idx["q"]
                pe = q.get("pe")
                pe_s = f"PE {pe:.1f}x" if pe else ""
                idx_lines.append(
                    f"  {idx['name']}: {q['price']:.2f} {fmt_pct(q['change_pct'])} {pe_s}"
                )
        idx_text = "\n".join(idx_lines)

        # 2. 市场情绪
        nb_val = nb.get("net_buy_today", 0)
        nb_s = f"北向资金 {nb_val:+.2f}亿" if nb_val != 0 else "北向资金数据暂无"
        up_c = breadth.get("up_count", 0)
        down_c = breadth.get("down_count", 0)
        breadth_s = f"涨跌家数约 {up_c}:{down_c}" if up_c else ""

        # 3. 持仓总览
        total_v = summary.get("total_value", 0)
        total_p = summary.get("total_profit", 0)
        total_pct = summary.get("total_pct", 0)
        day_chg = summary.get("day_change", 0)
        etf_r = summary.get("etf_ratio", 0)

        # 4. 逐标的估值明细（ETF + 个股）
        valuation_lines = []
        for r in results:
            if "error" in r:
                continue
            code = r.get("code", "")
            name = r.get("name", "")
            rtype = r.get("type", "stock")
            price = r.get("price", 0)
            cost = r.get("cost", 0)
            profit_pct = r.get("profit_pct")
            chg = r.get("change_pct", 0)
            profit_s = f"{profit_pct:+.1f}%" if profit_pct is not None else "待确认"

            if rtype == "etf":
                # ETF：显示对应指数PE及分位
                ev = etf_val.get(code, {})
                idx_pe = ev.get("pe")
                idx_name = ev.get("index_name", "")
                pe_label_s = ev.get("pe_label", "—")
                advice_s = ev.get("advice", "")
                if idx_pe:
                    valuation_lines.append(
                        f"  ETF {name}({code}): 持仓盈亏{profit_s} 今日{fmt_pct(chg)}"
                        f" | 跟踪{idx_name} PE={idx_pe:.1f}x [{pe_label_s}] {advice_s}"
                    )
                else:
                    valuation_lines.append(
                        f"  ETF {name}({code}): 持仓盈亏{profit_s} 今日{fmt_pct(chg)}"
                        f" | 跟踪{idx_name} PE数据暂无"
                    )
            elif rtype == "stock":
                # 个股：直接显示PE/PB
                q = r.get("q", {})
                pe = q.get("pe")
                pb = q.get("pb")
                pe_s = f"PE={pe:.1f}x" if pe else "PE=N/A"
                pb_s = f"PB={pb:.2f}x" if pb else ""
                valuation_lines.append(
                    f"  股票 {name}({code}): 持仓盈亏{profit_s} 今日{fmt_pct(chg)}"
                    f" | {pe_s} {pb_s}"
                )
            elif rtype == "bond":
                # 可转债：显示现价vs成本
                premium = (price - cost) / cost * 100 if cost > 0 else 0
                valuation_lines.append(
                    f"  转债 {name}({code}): 持仓盈亏{profit_s} 今日{fmt_pct(chg)}"
                    f" | 现价{price:.1f} 成本{cost:.1f} 溢价{premium:+.1f}%"
                )

        positions_detail = "\n".join(valuation_lines) if valuation_lines else "（持仓数据获取中）"

        # 5. 宏观消息摘要
        hot = news_data.get("今日热点概要", [])
        macro = [n["摘要"][:60] for n in news_data.get("宏观热点", [])[:5]]
        cctv = [n["标题"][:50] for n in news_data.get("央视要闻", [])[:3]]
        news_text = ""
        if hot:
            news_text += "今日热点板块: " + "；".join(hot[:2]) + "\n"
        if macro:
            news_text += "宏观动态: " + "；".join(macro[:3]) + "\n"
        if cctv:
            news_text += "央视要闻: " + "；".join(cctv[:2]) + "\n"

        prompt = f"""你是一位专注A股的价值投资顾问，请基于今日数据生成收盘分析报告。

【今日大盘】
{idx_text}

【市场情绪】
{nb_s}
{breadth_s}

【持仓概览】
总市值 {total_v:,.0f}元，当日盈亏 {day_chg:+,.0f}元，总持仓盈亏 {total_p:+,.0f}元({total_pct:+.1f}%)，ETF占比 {etf_r:.0f}%

【逐标的持仓与估值】
{positions_detail}

【今日消息面】
{news_text}

请严格按以下结构输出（总字数控制在450字以内，不要废话）：

**今日市场总结**
（大盘表现+主要驱动因素，2-3句）

**持仓估值分析**
（逐一点评持仓中估值明显偏低或偏高的标的，给出判断依据；重点关注ETF的指数PE分位和个股PE/PB，3-5条）

**操作建议**
（基于以上估值水位+消息面，给出具体加减仓建议，不超过4条；价值投资风格，不建议短线操作）

要求：
- 直接给结论，不说"根据数据显示"套话
- 估值分析要引用具体PE数字和分位判断
- 建议写成"动作+标的+理由"的格式，如"可继续定投沪深300ETF：PE 13.8x处历史25%分位以下\""""

        # ── 调用 API ──
        session = _new_session()
        resp = session.post(
            "http://1.95.142.151:3000/v1/messages",
            headers={
                "x-api-key": "sk-LrQCk8dmDvwgJoStf3rTNFCwRGKGNYYKu7uUTqjszxVHxfmZ",
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-opus-4-5",
                "max_tokens": 900,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=45,
        )
        if resp.status_code == 200:
            return resp.json()["content"][0]["text"].strip()
        else:
            print(f"  ⚠️ AI分析接口返回 {resp.status_code}")
            return ""
    except Exception as e:
        print(f"  ⚠️ AI分析生成失败: {e}")
        return ""


def fetch_market_news(date_str: str = "") -> dict:
    """
    获取今日市场消息面：宏观热点新闻 + 今日热点板块 + 央视要闻。
    聚焦"影响市场情绪"的宏观事件，而非微观股票数据。
    date_str: 格式 YYYYMMDD，默认今天
    """
    import akshare as ak
    if not date_str:
        date_str = datetime.now().strftime("%Y%m%d")
    result = {}

    # ── 1. 中证网快讯（宏观热点为主）────────────────────────────────
    # 标签分类：今日热点 / 市场动态 / 宏观 / 华尔街原声 / 市场洞察
    try:
        df_cx = ak.stock_news_main_cx()
        # 优先级：今日热点 > 市场洞察 > 市场动态 > 华尔街原声
        priority_tags = ["今日热点", "市场洞察", "宏观", "市场动态", "华尔街原声", "周刊提前看"]
        hot_news = []
        seen = set()
        for tag in priority_tags:
            subset = df_cx[df_cx["tag"] == tag]
            for _, row in subset.iterrows():
                summary = str(row.get("summary", "")).strip()
                if summary and summary not in seen:
                    seen.add(summary)
                    hot_news.append({
                        "分类": tag,
                        "摘要": summary[:85],
                    })
                if len(hot_news) >= 10:
                    break
            if len(hot_news) >= 10:
                break
        result["宏观热点"] = hot_news
    except Exception as e:
        result["宏观热点"] = []

    # ── 2. 央视要闻（今日国内重要政策/事件）─────────────────────────
    try:
        df_cctv = ak.news_cctv(date=date_str)
        cctv_list = []
        for _, row in df_cctv.iterrows():
            title = str(row.get("title", "")).strip()
            if title:
                cctv_list.append({"标题": title[:70]})
        result["央视要闻"] = cctv_list[:6]
        result["央视要闻日期"] = date_str
    except Exception as e:
        result["央视要闻"] = []

    # ── 3. 今日市场热点板块（从中证网「今日热点」提取行业关键词）────
    try:
        hot_tags = []
        for item in result.get("宏观热点", []):
            if item["分类"] == "今日热点":
                hot_tags.append(item["摘要"])
        result["今日热点概要"] = hot_tags[:3]
    except Exception:
        result["今日热点概要"] = []

    return result


def fetch_northbound_flow() -> dict:
    """
    获取北向资金净流入（东财 kamt.rtmin 接口）
    n2s = 北向资金（港→A股），最后一条数据格式：时间,沪股通,深股通,合计,余额,??
    单位：万元
    """
    try:
        session = _new_session()
        url = "https://push2.eastmoney.com/api/qt/kamt.rtmin/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&cb="
        resp = session.get(url, timeout=8)
        d = resp.json()
        data = d.get("data", {})
        n2s = data.get("n2s", [])   # 北向资金分钟数据
        n2s_date = data.get("n2sDate", "")

        if not n2s:
            return {"error": "n2s 为空"}

        # 取最后一条（当天最终数据）
        last = n2s[-1].split(",")
        if len(last) < 4:
            return {"error": f"数据格式异常: {n2s[-1]}"}

        t = last[0]
        sh_net = float(last[1])   # 沪股通净买入（万元）
        sz_net = float(last[2])   # 深股通净买入（万元）
        total = float(last[3])    # 北向合计净买入（万元）

        return {
            "hsh": sh_net / 10000,    # 转亿元
            "hsz": sz_net / 10000,
            "total": total / 10000,
            "time": t,
            "date": n2s_date,
        }
    except Exception as e:
        return {"error": str(e)}


# ── 持仓计算 ──────────────────────────────────────
def calc_holdings(holdings: list) -> list:
    results = []
    for h in holdings:
        try:
            q = fetch_quote(h["code"])
            price = q["price"]
            cost = float(h.get("cost", 0))
            shares = int(h["shares"])

            # 成本价异常保护（0或负）
            if cost <= 0:
                results.append({
                    **h,
                    "q": q,
                    "price": price,
                    "value": price * shares,
                    "profit": None,
                    "profit_pct": None,
                    "change_pct": q["change_pct"],
                    "cost_error": True,
                    "display_name": q.get("name", h.get("name", "")),
                })
                continue

            if price <= 0:
                results.append({**h, "error": "价格为0", "q": q})
                continue

            value = price * shares
            profit = (price - cost) * shares
            profit_pct = (price - cost) / cost * 100

            results.append({
                **h,
                "q": q,
                "price": price,
                "value": value,
                "profit": profit,
                "profit_pct": profit_pct,
                "change_pct": q["change_pct"],
                "display_name": q.get("name", h.get("name", "")),
            })
        except Exception as e:
            results.append({**h, "error": str(e)})
    return results


def calc_summary(results: list) -> dict:
    valid = [r for r in results if "error" not in r and r.get("value", 0) > 0]
    total_value = sum(r.get("value", 0) for r in valid)
    total_profit = sum(r.get("profit") or 0 for r in valid if r.get("profit") is not None)
    total_cost = sum(r.get("value", 0) - (r.get("profit") or 0) for r in valid if r.get("profit") is not None)

    day_change = sum(
        r.get("value", 0) * r.get("change_pct", 0) / 100
        for r in valid if r.get("change_pct") is not None
    )

    etf_value = sum(r.get("value", 0) for r in valid if r.get("type") == "etf")
    stock_value = sum(r.get("value", 0) for r in valid if r.get("type") in ("stock", "bond"))

    total_pct = total_profit / total_cost * 100 if total_cost > 0 else 0

    return {
        "total_value": total_value,
        "total_profit": total_profit,
        "total_cost": total_cost,
        "total_pct": total_pct,
        "day_change": day_change,
        "etf_value": etf_value,
        "stock_value": stock_value,
        "etf_ratio": etf_value / total_value * 100 if total_value > 0 else 0,
    }


# ── 指数行情（带PE）────────────────────────────────
def fetch_indices(indices: list) -> list:
    results = []
    for idx in indices:
        try:
            q = fetch_quote(idx["code"])
            results.append({**idx, "q": q})
        except Exception as e:
            results.append({**idx, "error": str(e)})
    return results


# ── ETF 估值映射（ETF代码 → 跟踪指数代码+名称）──────────────
# 对于ETF，用跟踪指数的PE来衡量估值；指数代码使用腾讯格式
ETF_INDEX_MAP = {
    # ETF代码    : (指数代码,       指数名,    PE历史均值参考, 历史低分位PE, 历史高分位PE)
    "562800": ("sh000822",  "中证有色金属",    25,  15, 40),
    "588000": ("sh000688",  "科创50",          80,  50, 200),
    "516350": ("sz399959",  "中证航空航天",    40,  25, 70),
    "513050": ("sh000852",  "中证1000",        50,  30, 80),   # 中概互联跟踪港股，用中证1000近似
    "513000": ("sh000016",  "上证50",          12,  8,  18),   # 恒生指数ETF，用上证50近似
    "510300": ("sh000300",  "沪深300",         14,  10, 20),
    "515100": ("sh000300",  "沪深300(红利)",   14,  10, 20),   # 红利低波 benchmark 参考沪深300
    "512070": ("sh000300",  "沪深300(金融)",   14,  10, 20),   # 证券保险 benchmark
    "510660": ("sz399006",  "创业板指(医药)",  60,  35, 100),  # 医药ETF
    "515000": ("sh000016",  "上证50(地产)",    11,  8,  18),
    "159995": ("sh688000",  "科创板50",        80,  50, 200),  # 芯片/科创
    "159928": ("sh000016",  "上证50(消费)",    12,  8,  18),
    "159949": ("sz399006",  "创业板50",        55,  30, 90),
}

# PE历史分位参考（简化：基于A股历史规律的经验值）
# pe_percentile: 返回 (分位描述, 简短建议)
def pe_percentile_label(pe: float, low: float, high: float) -> tuple:
    """根据历史区间给出估值分位描述"""
    if pe is None:
        return ("—", "")
    mid = (low + high) / 2
    if pe <= low:
        return ("历史低位(<25%)", "低估，可积极配置")
    elif pe <= mid * 0.85:
        return ("偏低(25-40%)", "估值合理偏低")
    elif pe <= mid * 1.15:
        return ("历史中位", "估值中性")
    elif pe <= high:
        return ("偏高(60-75%)", "估值偏贵，谨慎追高")
    else:
        return ("历史高位(>75%)", "高估，注意风险")


def fetch_etf_valuation(holdings: list) -> dict:
    """
    批量获取 ETF 持仓对应指数的 PE 估值。
    返回 {etf_code: {"index_name": str, "pe": float, "pe_label": str, "advice": str}}
    """
    # 收集需要查的指数代码（去重）
    idx_codes_needed = {}
    for h in holdings:
        code = h.get("code", "")
        if h.get("type") == "etf" and code in ETF_INDEX_MAP:
            idx_code, idx_name, pe_mid, pe_low, pe_high = ETF_INDEX_MAP[code]
            idx_codes_needed[idx_code] = (idx_name, pe_mid, pe_low, pe_high)

    if not idx_codes_needed:
        return {}

    # 批量拉取指数行情（单次请求）
    try:
        codes_str = ",".join(idx_codes_needed.keys())
        session = _new_session()
        resp = session.get(f"https://qt.gtimg.cn/q={codes_str}", timeout=10)
        resp.encoding = "gbk"
        # 解析
        idx_pe_map = {}  # idx_code -> pe
        for line in resp.text.strip().split("\n"):
            if "=" not in line:
                continue
            m = re.search(r'v_(\w+)="(.*?)"', line)
            if not m:
                continue
            full_c = m.group(1)  # e.g. sh000300
            parts = m.group(2).split("~")
            pe = None
            if len(parts) > 39 and parts[39]:
                try:
                    v = float(parts[39])
                    pe = v if v > 0 else None
                except:
                    pass
            idx_pe_map[full_c] = pe
    except Exception:
        idx_pe_map = {}

    # 组装结果
    result = {}
    for h in holdings:
        code = h.get("code", "")
        if h.get("type") == "etf" and code in ETF_INDEX_MAP:
            idx_code, idx_name, pe_mid, pe_low, pe_high = ETF_INDEX_MAP[code]
            pe = idx_pe_map.get(idx_code)
            label, advice = pe_percentile_label(pe, pe_low, pe_high)
            result[code] = {
                "index_name": idx_name,
                "index_code": idx_code,
                "pe": pe,
                "pe_label": label,
                "advice": advice,
            }
    return result


# ── 格式化工具 ────────────────────────────────────
def fmt_pct(v: float) -> str:
    return f"+{v:.2f}%" if v >= 0 else f"{v:.2f}%"

def fmt_money(v: float) -> str:
    if v is None:
        return "N/A"
    return f"+{v:,.2f}" if v >= 0 else f"{v:,.2f}"

def fmt_money_short(v: float) -> str:
    """简短金额，用于简报"""
    if v is None:
        return "N/A"
    sign = "+" if v >= 0 else ""
    if abs(v) >= 10000:
        return f"{sign}{v/10000:.1f}万"
    return f"{sign}{v:.0f}元"

def color_icon(v: float) -> str:
    """中国市场：涨红跌绿"""
    return "🔴" if v > 0 else ("🟢" if v < 0 else "⬜")

def fmt_amount(v: float) -> str:
    if v >= 1e8:
        return f"{v/1e8:.1f}亿"
    elif v >= 1e4:
        return f"{v/1e4:.1f}万"
    return f"{v:.0f}"

def pe_label(pe: float) -> str:
    """PE估值简单标注"""
    if pe is None:
        return ""
    if pe < 15:
        return "（低估）"
    if pe < 25:
        return "（适中）"
    if pe < 40:
        return "（偏高）"
    return "（高估）"


# ── 开盘前简报 ────────────────────────────────────
def build_morning_brief(cfg: dict) -> str:
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日 %H:%M")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    sep = "━━━━━━━━━━━━━━━━━━━━━━"

    lines = [f"🌅 开盘提醒  {date_str} 周{weekday}\n"]
    lines.append(sep)

    # 【昨日收盘】
    lines.append("\n【昨日收盘】")
    idx_data = fetch_indices(cfg.get("indices", []))
    for idx in idx_data:
        if "error" in idx:
            lines.append(f"  ❌ {idx['name']}: 获取失败")
        else:
            q = idx["q"]
            icon = color_icon(q["change_pct"])
            pe = q.get("pe")
            pe_str = f"  PE:{pe:.1f}x" if pe else ""
            amt_str = f"  成交{fmt_amount(q['amount'])}" if q.get("amount", 0) > 0 else ""
            lines.append(
                f"  {icon} {idx['name']}: {q['price']:.2f}  {fmt_pct(q['change_pct'])}{pe_str}{amt_str}"
            )

    # 【估值温度】
    lines.append("\n【估值温度】")
    has_pe = False
    for idx in idx_data:
        if "error" not in idx:
            q = idx["q"]
            pe = q.get("pe")
            if pe:
                has_pe = True
                label = pe_label(pe)
                lines.append(f"  🌡️ {idx['name']} PE: {pe:.1f}倍{label}")
    if not has_pe:
        lines.append("  ⚪ 估值数据暂不可用")

    # 【资金情绪】
    lines.append("\n【资金情绪】")
    nb = fetch_northbound_flow()
    if nb and "error" not in nb:
        total = nb.get("total", 0)
        icon = "📈" if total >= 0 else "📉"
        lines.append(f"  {icon} 北向资金: {fmt_money(total)}亿 ({nb.get('date', '')})")
    else:
        lines.append(f"  ⚪ 北向资金: 数据待更新")

    breadth = fetch_market_breadth()
    if breadth and "error" not in breadth:
        total_stocks = breadth.get("total", 0)
        last_up = breadth.get("last_up", 0)
        last_down = breadth.get("last_down", 0)
        lines.append(f"  📊 全市场 {total_stocks} 只  涨幅榜末位{last_up:+.1f}%  跌幅榜末位{last_down:+.1f}%")

    # 【今日关注】
    lines.append("\n【今日关注】")
    holdings = cfg.get("holdings", [])
    results = calc_holdings(holdings)
    alerts = [r for r in results if "error" not in r and r.get("change_pct", 0) <= -3]
    if alerts:
        lines.append("  ⚠️ 以下标的昨日跌幅较大，关注：")
        for r in sorted(alerts, key=lambda x: x.get("change_pct", 0)):
            lines.append(f"     {r['name']}({r['code']})  {fmt_pct(r['change_pct'])}")
    else:
        lines.append("  ✅ 持仓整体稳定，无大跌标的")

    lines.append("\n" + sep)
    lines.append("📊 祝交易顺利！")
    return "\n".join(lines)


# ── 收盘后简报 ────────────────────────────────────
def build_evening_brief(cfg: dict) -> tuple:
    now = datetime.now()
    date_str = now.strftime("%Y年%m月%d日 %H:%M")
    weekday = ["一", "二", "三", "四", "五", "六", "日"][now.weekday()]
    sep = "━━━━━━━━━━━━━━━━━━━━━━"

    holdings = cfg.get("holdings", [])
    idx_cfg = cfg.get("indices", [])

    results = calc_holdings(holdings)
    summary = calc_summary(results)
    idx_data = fetch_indices(idx_cfg)
    nb = fetch_northbound_flow()
    breadth = fetch_market_breadth()
    news_data = fetch_market_news(now.strftime("%Y%m%d"))

    lines = [f"📊 收盘日报  {date_str} 周{weekday}\n"]
    lines.append(sep)

    # 【市场概览】
    lines.append("\n【市场概览】")
    for idx in idx_data:
        if "error" not in idx:
            q = idx["q"]
            icon = color_icon(q["change_pct"])
            amt_str = f"  成交{fmt_amount(q['amount'])}" if q.get("amount", 0) > 0 else ""
            pe = q.get("pe")
            pe_str = f"  PE:{pe:.1f}x" if pe else ""
            lines.append(
                f"  {icon} {idx['name']}: {q['price']:.2f}  {fmt_pct(q['change_pct'])}{pe_str}{amt_str}"
            )

    # 【估值温度】
    lines.append("\n【估值温度】")
    any_pe = False
    for idx in idx_data:
        if "error" not in idx:
            pe = idx["q"].get("pe")
            if pe:
                any_pe = True
                label = pe_label(pe)
                lines.append(f"  🌡️ {idx['name']} PE: {pe:.1f}倍{label}")
    if not any_pe:
        lines.append("  ⚪ 估值数据暂不可用")

    # 市场情绪
    lines.append("\n【市场情绪】")
    if breadth and "error" not in breadth:
        total_s = breadth.get("total", 0)
        last_up = breadth.get("last_up", 0)
        last_down = breadth.get("last_down", 0)
        lines.append(f"  📊 A股全市场 {total_s} 只")
        lines.append(f"  涨幅榜末位 {last_up:+.1f}%  跌幅榜末位 {last_down:+.1f}%")
    if nb and "error" not in nb:
        total = nb.get("total", 0)
        icon = "📈" if total >= 0 else "📉"
        lines.append(f"  {icon} 北向资金: {fmt_money(total)}亿元 ({nb.get('date', '')})")
    elif "error" in (nb or {}):
        lines.append(f"  ⚪ 北向资金: 数据暂不可用")

    # 【持仓监控】
    lines.append("\n【持仓监控】")
    etf_results = [r for r in results if r.get("type") == "etf" and "error" not in r]
    stock_results = [r for r in results if r.get("type") in ("stock", "bond") and "error" not in r]

    # ETF仓位
    etf_pct = summary.get("etf_ratio", 0)
    lines.append(f"\n💼 ETF仓位 ({etf_pct:.0f}%)")
    for i, r in enumerate(sorted(etf_results, key=lambda x: x.get("value", 0), reverse=True)):
        is_last = (i == len(etf_results) - 1)
        prefix = "└─" if is_last else "├─"
        icon = color_icon(r["change_pct"])
        profit_str = fmt_money_short(r["profit"]) if r.get("profit") is not None else "成本待确认"
        pct_str = fmt_pct(r["profit_pct"]) if r.get("profit_pct") is not None else ""
        lines.append(
            f"  {prefix} {icon} {r['name']}: {r['price']:.3f}元 ({fmt_pct(r['change_pct'])})"
        )
        indent = "     " if is_last else "│    "
        lines.append(f"  {indent}持仓盈亏: {profit_str} ({pct_str})")

    # 个股仓位
    stock_pct = 100 - etf_pct
    lines.append(f"\n💼 个股仓位 ({stock_pct:.0f}%)")
    for i, r in enumerate(sorted(stock_results, key=lambda x: x.get("value", 0), reverse=True)):
        is_last = (i == len(stock_results) - 1)
        prefix = "└─" if is_last else "├─"
        icon = color_icon(r["change_pct"])
        profit_str = fmt_money_short(r["profit"]) if r.get("profit") is not None else "成本待确认"
        pct_str = fmt_pct(r["profit_pct"]) if r.get("profit_pct") is not None else ""
        extra = ""
        if r.get("cost_error"):
            extra = "  ⚠️成本待确认"
        lines.append(
            f"  {prefix} {icon} {r['name']}({r['code']}): {r['price']:.3f}元 ({fmt_pct(r['change_pct'])}){extra}"
        )
        indent = "     " if is_last else "│    "
        lines.append(f"  {indent}持仓盈亏: {profit_str} ({pct_str})")

    # 💰 今日汇总
    lines.append("\n💰 今日汇总")
    lines.append(f"   总市值: {summary['total_value']:,.0f}元")
    day_chg = summary.get("day_change", 0)
    lines.append(f"   当日盈亏: {fmt_money(day_chg)}元 ({fmt_pct(day_chg/summary['total_value']*100) if summary['total_value'] > 0 else ''})")
    if summary["total_cost"] > 0:
        lines.append(f"   总盈亏: {fmt_money(summary['total_profit'])}元 ({fmt_pct(summary['total_pct'])})")

    # 【关注提醒】
    errors = [r for r in results if "error" in r]
    cost_warns = [r for r in results if r.get("cost_error")]
    big_drops = [r for r in results if "error" not in r and r.get("change_pct", 0) <= -3]
    big_rises = [r for r in results if "error" not in r and r.get("change_pct", 0) >= 5]

    if errors or cost_warns or big_drops or big_rises:
        lines.append("\n【关注提醒】")
        for r in big_rises:
            lines.append(f"  🚀 {r['name']} 今日涨幅较大 {fmt_pct(r['change_pct'])}")
        for r in big_drops:
            lines.append(f"  ⚠️ {r['name']} 今日跌幅较大 {fmt_pct(r['change_pct'])}")
        for r in cost_warns:
            lines.append(f"  📌 {r['name']}({r['code']}) 成本未填写，盈亏无法计算")
        for r in errors:
            lines.append(f"  ❌ {r.get('name', r['code'])} 数据获取失败")

    # 【消息面】
    lines.append("\n【消息面】")
    # 今日热点板块（来自中证网「今日热点」标签）
    hot_summary = news_data.get("今日热点概要", [])
    if hot_summary:
        lines.append("  🔥 今日热点:")
        for h in hot_summary[:2]:
            lines.append(f"    · {h[:55]}")
    # 宏观热点新闻（中证网快讯，按分类优先级）
    macro_news = news_data.get("宏观热点", [])
    if macro_news:
        lines.append("  📊 宏观动态:")
        shown = 0
        for n in macro_news:
            if n.get("分类") not in ["今日热点"]:  # 避免与上面重复
                lines.append(f"    · [{n['分类']}] {n['摘要'][:50]}")
                shown += 1
                if shown >= 4:
                    break
    # 央视要闻（政策导向）
    cctv = news_data.get("央视要闻", [])
    if cctv:
        lines.append("  📺 央视要闻:")
        for item in cctv[:3]:
            lines.append(f"    · {item['标题'][:50]}")


    lines.append("\n" + sep)

    # 【AI 分析建议】—— 放在最后，不阻塞前面内容展示
    print("  🤖 正在获取持仓估值数据...")
    cfg = load_config()
    etf_val = fetch_etf_valuation(cfg.get("holdings", []))
    print("  🤖 正在生成 AI 分析建议...")
    ai_text = generate_ai_analysis(summary, idx_data, breadth, nb, news_data, results, etf_val)
    if ai_text:
        lines.append("\n【AI 分析建议】")
        for line in ai_text.split("\n"):
            lines.append(f"  {line}" if line.strip() else "")
        lines.append("\n" + sep)

    brief = "\n".join(lines)
    return brief, {
        "results": results,
        "summary": summary,
        "indices": idx_data,
        "breadth": breadth,
        "northbound": nb,
        "news": news_data,
        "etf_val": etf_val,
        "ai_analysis": ai_text,
        "date_str": date_str,
        "weekday": weekday,
    }


# ── 腾讯文档详报（Markdown）────────────────────────
def build_detail_report(data: dict) -> str:
    """按功能说明约定结构生成腾讯文档详报"""
    now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
    results = data["results"]
    summary = data["summary"]
    idx_data = data["indices"]
    breadth = data.get("breadth", {})
    nb = data.get("northbound", {})
    news_data = data.get("news", {})
    ai_analysis = data.get("ai_analysis", "")  # 从 brief 阶段传入，避免重复调用
    etf_val = data.get("etf_val", {})

    lines = [f"# 📊 投资日报  {now}\n"]

    # ─ 零、今日总结（AI生成）─
    if ai_analysis:
        lines.append("## 📝 今日总结与建议\n")
        lines.append(ai_analysis)
        lines.append("\n---\n")

    # ─ 一、市场概览 ─
    lines.append("## 一、市场概览\n")
    lines.append("| 指数 | 收盘价 | 涨跌幅 | 涨跌额 | 成交额 | PE |")
    lines.append("|:-----|------:|------:|------:|------:|----:|")
    for idx in idx_data:
        if "error" not in idx:
            q = idx["q"]
            pe = q.get("pe")
            pe_str = f"{pe:.1f}x" if pe else "-"
            amt_str = fmt_amount(q.get("amount", 0)) if q.get("amount", 0) > 0 else "-"
            icon = "🔴" if q["change_pct"] > 0 else ("🟢" if q["change_pct"] < 0 else "⬜")
            lines.append(
                f"| {icon} {idx['name']} | {q['price']:.2f} | {fmt_pct(q['change_pct'])} "
                f"| {fmt_money(q['change'])} | {amt_str} | {pe_str} |"
            )
        else:
            lines.append(f"| ❌ {idx['name']} | - | - | - | - | - |")
    lines.append("")

    # ─ 二、估值温度 ─
    lines.append("## 二、估值温度\n")
    has_pe = False
    for idx in idx_data:
        if "error" not in idx:
            pe = idx["q"].get("pe")
            if pe:
                has_pe = True
                label = pe_label(pe)
                # 简单估值描述
                if pe < 12:
                    desc = "历史低位，较具吸引力"
                elif pe < 18:
                    desc = "估值合理偏低"
                elif pe < 25:
                    desc = "估值适中"
                elif pe < 35:
                    desc = "估值偏高，需关注"
                else:
                    desc = "估值较高，谨慎追高"
                lines.append(f"🌡️ **{idx['name']} PE: {pe:.1f}倍**{label} — {desc}")
    if not has_pe:
        lines.append("⚪ 估值数据暂不可用（非交易时间或接口限制）")
    lines.append("")

    # 市场情绪
    lines.append("### 市场情绪\n")
    if breadth and "error" not in breadth:
        total_s = breadth.get("total", 0)
        last_up = breadth.get("last_up", 0)
        last_down = breadth.get("last_down", 0)
        # 判断市场情绪
        if last_up >= 5:
            sentiment = "🔥 强势普涨"
        elif last_up >= 2:
            sentiment = "😊 偏强"
        elif last_down <= -5:
            sentiment = "😰 弱势普跌"
        elif last_down <= -2:
            sentiment = "😟 偏弱"
        else:
            sentiment = "😐 中性分化"
        lines.append(f"- 全市场 {total_s} 只个股，市场情绪：**{sentiment}**")
        lines.append(f"- 涨幅榜末位 {last_up:+.1f}%，跌幅榜末位 {last_down:+.1f}%")
    else:
        err = breadth.get("error", "未知") if breadth else "接口未返回"
        lines.append(f"- 涨跌家数：暂不可用（{err}）")

    if nb and "error" not in nb:
        total = nb.get("total", 0)
        icon = "净流入 ↑" if total >= 0 else "净流出 ↓"
        lines.append(f"- 北向资金：{icon} **{abs(total):.2f}亿元**（{nb.get('date', '')}）")
    else:
        err = nb.get("error", "未知") if nb else "接口未返回"
        lines.append(f"- 北向资金：暂不可用（{err}）")
    lines.append("")

    # ─ 三、账户总览 ─
    lines.append("## 三、账户总览\n")
    lines.append("| 指标 | 数值 |")
    lines.append("|:-----|-----:|")
    lines.append(f"| 💰 总市值 | **{summary['total_value']:,.2f} 元** |")
    day_chg = summary.get("day_change", 0)
    day_pct = day_chg / summary["total_value"] * 100 if summary["total_value"] > 0 else 0
    lines.append(f"| 📅 当日盈亏 | **{fmt_money(day_chg)} 元** ({fmt_pct(day_pct)}) |")
    if summary["total_cost"] > 0:
        lines.append(
            f"| 📈 持仓总盈亏 | **{fmt_money(summary['total_profit'])} 元** ({fmt_pct(summary['total_pct'])}) |"
        )
    else:
        lines.append("| 📈 持仓总盈亏 | 部分成本待确认 |")
    etf_r = summary.get("etf_ratio", 0)
    lines.append(f"| 🏦 ETF 市值 | {summary['etf_value']:,.2f} 元（**{etf_r:.1f}%**）|")
    lines.append(f"| 📦 个股市值 | {summary['stock_value']:,.2f} 元（{100-etf_r:.1f}%）|")

    # 仓位提醒
    if etf_r < 70:
        lines.append(
            f"\n> ⚠️ **仓位提示**：当前 ETF 占比 {etf_r:.1f}%，低于目标 70-80%，个股持仓偏重。"
        )
    lines.append("")


    # ─ 四、ETF持仓 ─
    etf_results = [r for r in results if r.get("type") == "etf" and "error" not in r]
    if etf_results:
        lines.append("## 四、ETF 持仓\n")
        lines.append("| 名称 | 代码 | 现价 | 今日涨跌 | 持仓份额 | 市值(元) | 成本 | 盈亏(元) | 盈亏% | 跟踪指数PE | 估值分位 |")
        lines.append("|:-----|:----:|-----:|--------:|---------:|---------:|-----:|---------:|------:|----------:|:--------|")
        for r in sorted(etf_results, key=lambda x: x.get("value", 0), reverse=True):
            icon = color_icon(r["change_pct"])
            profit_str = fmt_money(r["profit"]) if r.get("profit") is not None else "N/A"
            pct_str = fmt_pct(r["profit_pct"]) if r.get("profit_pct") is not None else "N/A"
            cost_str = f"{r['cost']:.3f}" if r.get("cost", 0) > 0 else "⚠️"
            ev = etf_val.get(r["code"], {})
            idx_pe = ev.get("pe")
            pe_str = f"{idx_pe:.1f}x" if idx_pe else "—"
            pe_lbl = ev.get("pe_label", "—")
            lines.append(
                f"| {icon} {r['name']} | {r['code']} | {r['price']:.3f} | {fmt_pct(r['change_pct'])} "
                f"| {r['shares']:,} | {r.get('value', 0):,.0f} | {cost_str} | {profit_str} | {pct_str} "
                f"| {pe_str} | {pe_lbl} |"
            )
        lines.append("")

    # ─ 五、个股/可转债持仓 ─
    stock_results = [r for r in results if r.get("type") in ("stock", "bond") and "error" not in r]
    if stock_results:
        lines.append("## 五、个股/可转债持仓\n")
        lines.append("| 名称 | 代码 | 类型 | 现价 | 今日涨跌 | 持仓 | 成本 | 市值(元) | 盈亏(元) | 盈亏% | PE | PB |")
        lines.append("|:-----|:----:|:----:|-----:|--------:|-----:|-----:|---------:|---------:|------:|---:|---:|")
        for r in sorted(stock_results, key=lambda x: x.get("value", 0), reverse=True):
            icon = color_icon(r["change_pct"])
            cost_str = f"{r['cost']:.3f}" if r.get("cost", 0) > 0 else "⚠️待确认"
            profit_str = fmt_money(r["profit"]) if r.get("profit") is not None else "⚠️"
            pct_str = fmt_pct(r["profit_pct"]) if r.get("profit_pct") is not None else "⚠️"
            q = r.get("q", {})
            pe_val = q.get("pe")
            pb_val = q.get("pb")
            pe_str = f"{pe_val:.1f}x" if pe_val else "—"
            pb_str = f"{pb_val:.2f}x" if pb_val else "—"
            type_label = "可转债" if r.get("type") == "bond" else "股票"
            lines.append(
                f"| {icon} {r['name']} | {r['code']} | {type_label} | {r['price']:.3f} | {fmt_pct(r['change_pct'])} "
                f"| {r['shares']:,} | {cost_str} | {r.get('value', 0):,.0f} | {profit_str} | {pct_str} "
                f"| {pe_str} | {pb_str} |"
            )
        lines.append("")

    # ─ 五-B、持仓估值汇总 ─
    lines.append("### 持仓估值一览\n")
    has_val = False
    # ETF 估值
    for r in sorted(etf_results, key=lambda x: x.get("value", 0), reverse=True):
        ev = etf_val.get(r["code"], {})
        if ev:
            idx_pe = ev.get("pe")
            pe_lbl = ev.get("pe_label", "—")
            adv = ev.get("advice", "")
            idx_name = ev.get("index_name", "")
            if idx_pe:
                icon_v = "🟢" if "低" in pe_lbl else ("🔴" if "高" in pe_lbl else "🟡")
                lines.append(f"- {icon_v} **{r['name']}**：跟踪 {idx_name}，当前 PE **{idx_pe:.1f}x**，{pe_lbl} → {adv}")
                has_val = True
    # 个股估值
    for r in sorted(stock_results, key=lambda x: x.get("value", 0), reverse=True):
        if r.get("type") == "bond":
            continue
        q = r.get("q", {})
        pe_val = q.get("pe")
        pb_val = q.get("pb")
        if pe_val or pb_val:
            pe_s = f"PE {pe_val:.1f}x" if pe_val else ""
            pb_s = f"PB {pb_val:.2f}x" if pb_val else ""
            val_s = "、".join(filter(None, [pe_s, pb_s]))
            # 简单评级
            if pe_val and pe_val < 15:
                comment = "估值偏低，有价值支撑"
                icon_v = "🟢"
            elif pe_val and pe_val > 50:
                comment = "估值较高，注意风险"
                icon_v = "🔴"
            elif pe_val and pe_val > 30:
                comment = "估值中性偏高"
                icon_v = "🟡"
            else:
                comment = "估值中性"
                icon_v = "🟡"
            lines.append(f"- {icon_v} **{r['name']}({r['code']})**：{val_s}，{comment}")
            has_val = True
    if not has_val:
        lines.append("- 估值数据获取中，请稍后刷新")
    lines.append("")



    # ─ 六、关注提醒 ─
    alerts = []
    errors = [r for r in results if "error" in r]
    cost_warns = [r for r in results if r.get("cost_error")]
    big_rises = [r for r in results if "error" not in r and r.get("change_pct", 0) >= 5]
    big_drops = [r for r in results if "error" not in r and r.get("change_pct", 0) <= -3]

    if big_rises or big_drops or cost_warns or errors:
        lines.append("## 六、关注提醒\n")
        for r in big_rises:
            lines.append(f"📌 **{r['name']}** 今日涨幅 {fmt_pct(r['change_pct'])}，注意高位风险")
        for r in big_drops:
            lines.append(f"⚠️ **{r['name']}** 今日跌幅 {fmt_pct(r['change_pct'])}，关注是否止损")
        for r in cost_warns:
            lines.append(f"🔧 **{r['name']}({r['code']})** 持仓成本未填写，请在 config.yaml 中补充 cost 字段")
        for r in errors:
            lines.append(f"❌ **{r.get('name', r['code'])}** 数据获取失败: {r['error']}")
        lines.append("")


    # ─ 七、市场消息面 ─
    lines.append("## 七、市场消息面\n")
    lines.append("> 数据来源：中证网快讯（实时宏观热点）+ 央视要闻（国内政策）\n")

    # 今日热点板块
    hot_summary = news_data.get("今日热点概要", [])
    if hot_summary:
        lines.append("### 今日热点板块\n")
        for h in hot_summary:
            lines.append(f"- 🔥 {h}")
        lines.append("")

    # 宏观热点新闻（按分类展示）
    macro_news = news_data.get("宏观热点", [])
    if macro_news:
        # 按分类分组
        from collections import defaultdict
        grouped = defaultdict(list)
        for n in macro_news:
            grouped[n["分类"]].append(n["摘要"])

        tag_order = ["今日热点", "市场洞察", "宏观", "市场动态", "华尔街原声", "周刊提前看"]
        lines.append("### 宏观热点动态\n")
        for tag in tag_order:
            items = grouped.get(tag, [])
            if items:
                lines.append(f"**{tag}**")
                for item in items[:4]:
                    lines.append(f"- {item}")
                lines.append("")

    # 央视要闻
    cctv = news_data.get("央视要闻", [])
    if cctv:
        lines.append("### 央视要闻（国内政策/重大事件）\n")
        for item in cctv:
            lines.append(f"- 📺 {item['标题']}")
        lines.append("")
    else:
        lines.append("### 央视要闻\n")
        lines.append("- 今日央视要闻暂无数据\n")

    lines.append("---")
    lines.append(f"*数据来源：腾讯财经 / 东方财富 / AKShare  |  生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

    return "\n".join(lines)


# ── 企业微信发送 ──────────────────────────────────
def send_wecom(webhook_url: str, text: str):
    """发送企微消息（支持 webhook 和应用消息两种模式）"""
    import json
    from datetime import datetime
    
    # 读取config
    try:
        config = YamlConfig.get_instance()
        wecom_cfg = config.get("wecom_app", {})
        user_id = config.get("wecom_user_id", "v")
        
        # 如果有企微应用配置，优先使用应用消息API
        if wecom_cfg.get("corp_id") and wecom_cfg.get("agent_secret"):
            print(f"[企微] 使用应用消息API推送给 {user_id}")
            return send_wecom_app_msg(wecom_cfg, user_id, text)
    except Exception as e:
        print(f"[企微] 读取配置异常: {e}")
    
    # 否则尝试webhook（兼容旧版）
    if not webhook_url or "YOUR_KEY" in webhook_url or "USE_TODO_MCP" in webhook_url:
        print("[企微] 未配置有效webhook，跳过发送")
        return
    session = _new_session()
    payload = {"msgtype": "text", "text": {"content": text}}
    resp = session.post(webhook_url, json=payload, timeout=15)
    result = resp.json()
    if result.get("errcode") == 0:
        print("✅ 企业微信Webhook发送成功")
    else:
        print(f"❌ 企业微信Webhook发送失败: {result}")


def send_wecom_app_msg(wecom_cfg: dict, user_id: str, text: str) -> bool:
    """通过企微应用API发送消息给指定用户"""
    import time, hashlib, base64, json, urllib.parse
    try:
        corp_id = wecom_cfg["corp_id"]
        agent_id = wecom_cfg["agent_id"]
        agent_secret = wecom_cfg["agent_secret"]
        
        session = _new_session()
        
        # 1. 获取access_token
        token_url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={agent_secret}"
        token_resp = session.get(token_url, timeout=10)
        token_data = token_resp.json()
        
        if token_data.get("errcode") != 0:
            print(f"❌ 获取access_token失败: {token_data}")
            return False
        
        access_token = token_data["access_token"]
        
        # 2. 发送消息
        msg_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        
        # 消息体
        payload = {
            "touser": user_id,
            "msgtype": "text",
            "agentid": agent_id,
            "text": {"content": text},
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0,
            "duplicate_check_interval": 1800
        }
        
        msg_resp = session.post(msg_url, json=payload, timeout=15)
        msg_result = msg_resp.json()
        
        if msg_result.get("errcode") == 0:
            print(f"✅ 企微应用消息发送成功（消息ID: {msg_result.get('msgid', 'N/A')}）")
            return True
        else:
            print(f"❌ 企微应用消息发送失败: {msg_result}")
            return False
            
    except Exception as e:
        print(f"❌ 企微应用消息异常: {e}")
        return False



# ── 腾讯文档写入 ──────────────────────────────────


# ── 腾讯文档写入 ──────────────────────────────────
def call_tencent_mcp(tool_name: str, args: dict) -> dict:
    import ssl
    import http.client
    token = "7bd23133a8c346008cc7b86385e1c06d"
    body = json.dumps({
        "jsonrpc": "2.0", "id": int(time.time() * 1000),
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": args}
    }).encode("utf-8")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    conn = http.client.HTTPSConnection("docs.qq.com", context=ctx, timeout=30)
    conn.request("POST", "/openapi/mcp", body=body, headers={
        "Content-Type": "application/json",
        "Authorization": token,
        "Content-Length": str(len(body))
    })
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8")
    return json.loads(raw)


def write_to_tencent_doc(mdx_content: str, title: str) -> str:
    result = call_tencent_mcp("create_smartcanvas_by_mdx", {
        "title": title,
        "mdx": mdx_content
    })
    if result.get("result") and result["result"].get("content"):
        try:
            data = json.loads(result["result"]["content"][0]["text"])
            url = data.get("url", "")
            new_id = data.get("file_id", "")
            if url:
                print(f"✅ 腾讯文档已创建: {url}")
                if new_id:
                    cfg_text = CONFIG_FILE.read_text(encoding="utf-8")
                    cfg_text = re.sub(
                        r'report_doc_id: ".*?"',
                        f'report_doc_id: "{new_id}"',
                        cfg_text
                    )
                    CONFIG_FILE.write_text(cfg_text, encoding="utf-8")
            return url
        except Exception as e:
            print(f"解析文档ID失败: {e}")
    return ""


# ── 定时任务 ──────────────────────────────────────
def job_morning():
    print(f"\n[{datetime.now()}] 执行开盘前简报...")
    try:
        cfg = load_config()
        brief = build_morning_brief(cfg)
        print(brief)
        
        # ── 推送消息 ──
        # 优先使用飞书推送
        feishu_cfg = cfg.get("feishu", {})
        if feishu_cfg.get("enabled") and FEISHU_AVAILABLE:
            send_feishu_message(cfg, brief)
        else:
            # 回退到企业微信
            send_wecom(cfg.get("webhook_url", ""), brief)
            
    except Exception as e:
        print(f"开盘简报失败: {e}")
        import traceback; traceback.print_exc()


def job_evening():
    print(f"\n[{datetime.now()}] 执行收盘后日报...")
    try:
        cfg = load_config()
        brief, detail_data = build_evening_brief(cfg)
        print(brief)
        
        # ── 推送简报消息 ──
        feishu_cfg = cfg.get("feishu", {})
        doc_url = None
        
        if feishu_cfg.get("enabled") and FEISHU_AVAILABLE:
            # 飞书推送
            send_feishu_message(cfg, brief)
        else:
            # 回退到企业微信
            send_wecom(cfg.get("webhook_url", ""), brief)
        
        # ── 生成详报文档 ──
        today = datetime.now().strftime("%Y年%m月%d日")
        detail_md = build_detail_report(detail_data)
        
        if feishu_cfg.get("enabled") and FEISHU_AVAILABLE:
            # 创建飞书云文档
            doc_url = write_to_feishu_doc(cfg, f"投资日报 · {today}", detail_md)
        else:
            # 回退到腾讯文档
            doc_url = write_to_tencent_doc(detail_md, f"投资日报 · {today}")
        
        if doc_url:
            link_msg = f"📄 今日详报已更新：{doc_url}"
            if feishu_cfg.get("enabled") and FEISHU_AVAILABLE:
                send_feishu_message(cfg, link_msg)
            else:
                send_wecom(cfg.get("webhook_url", ""), link_msg)
            print(f"\n📄 详报链接: {doc_url}")
            
            # ── 保存数据到多维表格 ──
            if feishu_cfg.get("enabled") and FEISHU_AVAILABLE:
                try:
                    print("💾 正在保存数据到飞书多维表格...")
                    
                    # 准备多维表格数据
                    bitable_data = prepare_bitable_data(cfg, detail_data, brief, doc_url)
                    
                    # 保存到飞书多维表格
                    if save_to_feishu_bitable(cfg, bitable_data):
                        print(f"✅ 数据已保存到飞书多维表格")
                    else:
                        print("⚠ 飞书多维表格保存部分失败")
                        
                except Exception as e:
                    print(f"飞书多维表格存储错误: {e}")
                    import traceback; traceback.print_exc()
            
            # ── 保存到腾讯智能表格（备选，已禁用）─
            elif SMART_SHEET_AVAILABLE and SMART_SHEET_ENABLED:
                try:
                    print("💾 正在保存数据到智能表格...")
                    # 从detail_data中提取需要的关键数据
                    total_value = detail_data.get('total_value', 0)
                    day_pnl = detail_data.get('day_pnl', 0)
                    total_pnl = detail_data.get('total_pnl', 0)
                    position_ratio = detail_data.get('position_ratio', 0)
                    
                    # 从brief中提取指数数据
                    import re
                    index_patterns = {
                        '上证指数': r'上证指数[：:]?\s*([\d\.]+)',
                        '深证成指': r'深证成指[：:]?\s*([\d\.]+)',
                        '创业板指': r'创业板指[：:]?\s*([\d\.]+)'
                    }
                    
                    index_data = {}
                    for index_name, pattern in index_patterns.items():
                        match = re.search(pattern, brief)
                        if match:
                            index_data[index_name] = match.group(1)
                    
                    # 估值温度
                    valuation_match = re.search(r'估值温度[：:]?\s*([\d\.]+)%', brief)
                    valuation_temp = valuation_match.group(1) if valuation_match else "未知"
                    
                    # 准备智能表格数据
                    smartsheet_data = {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'report_type': '收盘详报',
                        'report_time': datetime.now().strftime('%H:%M'),
                        'total_value': total_value,
                        'day_pnl': day_pnl,
                        'total_pnl': total_pnl,
                        'position_ratio': position_ratio / 100,  # 转换为百分比小数
                        'holdings_count': len([h for h in cfg.get('holdings', [])]),
                        'shangzheng_index': index_data.get('上证指数', ''),
                        'shenzheng_index': index_data.get('深证成指', ''),
                        'chuangye_index': index_data.get('创业板指', ''),
                        'valuation_temp': float(valuation_temp) / 100 if valuation_temp != "未知" else 0.5,
                        'north_fund': '等待数据',
                        'advance_decline': '等待数据',
                        'best_performer': detail_data.get('best_performer', '').split(' ')[0] if detail_data.get('best_performer') else '',
                        'ai_market_trend': '待生成',
                        'ai_operation_suggest': '待生成',
                        'doc_url': doc_url
                    }
                    
                    # 保存到智能表格（有开关控制）
                    try:
                        manager = TencentSmartSheetManager(config_path='config.yaml')
                        
                        # 提取参数
                        report_date = smartsheet_data.get('date', datetime.now().strftime('%Y-%m-%d'))
                        report_type = smartsheet_data.get('report_type', '收盘详报')
                        report_time = smartsheet_data.get('report_time', datetime.now().strftime('%H:%M'))
                        doc_url = smartsheet_data.get('doc_url', '')
                        
                        # 创建report_data字典（排除上面已提取的字段）
                        report_data = {k: v for k, v in smartsheet_data.items() 
                                      if k not in ['date', 'report_type', 'report_time', 'doc_url']}
                        
                        saved = manager.save_daily_report(report_date, report_type, report_time, report_data, doc_url)
                        if saved:
                            print(f"✅ 数据已保存到智能表格: {manager.get_sheet_url()}")
                        else:
                            print("⚠ 智能表格保存失败或已存在当日记录")
                    except Exception as e:
                        print(f"智能表格存储错误: {e}")
                        import traceback; traceback.print_exc()
                        
                except Exception as e:
                    print(f"智能表格存储错误: {e}")
                    import traceback; traceback.print_exc()
                    
    except Exception as e:
        print(f"收盘日报失败: {e}")
        import traceback; traceback.print_exc()


def prepare_bitable_data(cfg: dict, detail_data: dict, brief: str, doc_url: str) -> dict:
    """
    准备飞书多维表格数据
    
    Args:
        cfg: 配置字典
        detail_data: 详情数据
        brief: 简报文本
        doc_url: 文档URL
        
    Returns:
        多维表格数据字典
    """
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    # 提取持仓记录
    holdings_records = []
    results = detail_data.get("results", [])
    for r in results:
        if "error" not in r:
            holdings_records.append({
                "股票名称": r.get("name", ""),
                "日期": date_str,
                "持仓数": r.get("shares", 0),
                "成本价": r.get("cost", 0),
                "现价": r.get("price", 0),
                "盈亏金额": r.get("profit") or 0,
                "盈亏比例": r.get("profit_pct") or 0,
            })
    
    # 提取每日行情
    indices_records = []
    idx_data = detail_data.get("indices", [])
    for idx in idx_data:
        if "error" not in idx:
            q = idx.get("q", {})
            indices_records.append({
                "指数名称": idx.get("name", ""),
                "日期": date_str,
                "当前点位": q.get("price", 0),
                "涨跌幅": q.get("change_pct", 0),
            })
    
    # 提取资金动向
    capital_records = []
    nb = detail_data.get("northbound", {})
    if nb and "error" not in nb:
        capital_records.append({
            "资金类型": "北向资金",
            "日期": date_str,
            "净流入": nb.get("total", 0),
            "状态": "流入" if nb.get("total", 0) > 0 else "流出",
        })
    
    # 提取投资建议
    advice_records = []
    ai_analysis = detail_data.get("ai_analysis", "")
    if ai_analysis:
        # 简单解析AI建议（实际使用时可能需要更复杂的解析）
        advice_records.append({
            "日期": date_str,
            "大盘观点": extract_section(ai_analysis, "今日市场总结"),
            "仓位建议": "中性",  # 可以从AI分析中提取
            "建议买入": "",
            "建议卖出": "",
            "重点关注": "",
            "风险提示": "",
        })
    
    return {
        "holdings": holdings_records,
        "indices": indices_records,
        "capital_flow": capital_records,
        "advice": advice_records,
    }


def extract_section(text: str, section_name: str) -> str:
    """
    从文本中提取特定章节内容
    
    Args:
        text: 原始文本
        section_name: 章节名称
        
    Returns:
        章节内容
    """
    import re
    # 尝试匹配章节标题
    pattern = rf"\*\*{section_name}\*\*\s*\n(.+?)(?=\n\*\*|$)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


# ── 主程序 ────────────────────────────────────────
def main():
    cfg = load_config()
    morning_time = cfg.get("schedule", {}).get("morning", "08:00")
    evening_time = cfg.get("schedule", {}).get("evening", "15:30")

    schedule.every().day.at(morning_time).do(job_morning)
    schedule.every().day.at(evening_time).do(job_evening)

    print(f"✅ 投资日报服务已启动")
    print(f"   开盘前简报: {morning_time}")
    print(f"   收盘后日报: {evening_time}")
    print(f"   持仓标的数: {len(cfg.get('holdings', []))}")
    print(f"\n命令: now-morning  now-evening  q=退出\n")

    def scheduler_loop():
        while True:
            schedule.run_pending()
            time.sleep(30)

    threading.Thread(target=scheduler_loop, daemon=True).start()

    while True:
        try:
            cmd = input("> ").strip().lower()
            if cmd == "now-morning":
                job_morning()
            elif cmd in ("now-evening", "now"):
                job_evening()
            elif cmd in ("q", "quit", "exit"):
                print("已退出")
                break
        except EOFError:
            time.sleep(60)


if __name__ == "__main__":
    import sys
    if "--morning" in sys.argv:
        cfg = load_config()
        brief = build_morning_brief(cfg)
        print(brief)
        send_wecom(cfg.get("webhook_url", ""), brief)
    elif "--evening" in sys.argv or "--test" in sys.argv:
        cfg = load_config()
        brief, detail_data = build_evening_brief(cfg)
        print(brief)
        today = datetime.now().strftime("%Y年%m月%d日")
        detail_md = build_detail_report(detail_data)
        doc_url = write_to_tencent_doc(detail_md, f"投资日报 · {today}")
        if doc_url:
            print(f"\n📄 详报链接: {doc_url}")
            
            # 命令行模式下也存储到智能表格
            if SMART_SHEET_AVAILABLE:
                try:
                    print("💾 正在保存数据到智能表格（命令行模式）...")
                    
                    # 准备智能表格数据（复用job_evening中的逻辑）
                    total_value = detail_data.get('total_value', 0)
                    day_pnl = detail_data.get('day_pnl', 0)
                    total_pnl = detail_data.get('total_pnl', 0)
                    position_ratio = detail_data.get('position_ratio', 0)
                    
                    import re
                    index_patterns = {
                        '上证指数': r'上证指数[：:]?\s*([\d\.]+)',
                        '深证成指': r'深证成指[：:]?\s*([\d\.]+)',
                        '创业板指': r'创业板指[：:]?\s*([\d\.]+)'
                    }
                    
                    index_data = {}
                    for index_name, pattern in index_patterns.items():
                        match = re.search(pattern, brief)
                        if match:
                            index_data[index_name] = match.group(1)
                    
                    valuation_match = re.search(r'估值温度[：:]?\s*([\d\.]+)%', brief)
                    valuation_temp = valuation_match.group(1) if valuation_match else "未知"
                    
                    smartsheet_data = {
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'report_type': '收盘详报',
                        'report_time': datetime.now().strftime('%H:%M'),
                        'total_value': total_value,
                        'day_pnl': day_pnl,
                        'total_pnl': total_pnl,
                        'position_ratio': position_ratio / 100,
                        'holdings_count': len([h for h in cfg.get('holdings', [])]),
                        'shangzheng_index': index_data.get('上证指数', ''),
                        'shenzheng_index': index_data.get('深证成指', ''),
                        'chuangye_index': index_data.get('创业板指', ''),
                        'valuation_temp': float(valuation_temp) / 100 if valuation_temp != "未知" else 0.5,
                        'north_fund': '等待数据',
                        'advance_decline': '等待数据',
                        'best_performer': detail_data.get('best_performer', '').split(' ')[0] if detail_data.get('best_performer') else '',
                        'ai_market_trend': '待生成',
                        'ai_operation_suggest': '待生成',
                        'doc_url': doc_url
                    }
                    
                    manager = TencentSmartSheetManager(config_path='config.yaml')
                    
                    # 提取参数
                    report_date = smartsheet_data.get('date', datetime.now().strftime('%Y-%m-%d'))
                    report_type = smartsheet_data.get('report_type', '收盘详报')
                    report_time = smartsheet_data.get('report_time', datetime.now().strftime('%H:%M'))
                    doc_url = smartsheet_data.get('doc_url', '')
                    
                    # 创建report_data字典（排除上面已提取的字段）
                    report_data = {k: v for k, v in smartsheet_data.items() 
                                  if k not in ['date', 'report_type', 'report_time', 'doc_url']}
                    
                    saved = manager.save_daily_report(report_date, report_type, report_time, report_data, doc_url)
                    if saved:
                        print(f"✅ 数据已保存到智能表格: {manager.get_sheet_url()}")
                    else:
                        print("⚠ 智能表格保存失败或已存在当日记录")
                        
                except Exception as e:
                    print(f"智能表格存储错误: {e}")
                    import traceback; traceback.print_exc()
    else:
        main()
