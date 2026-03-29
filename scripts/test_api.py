import requests, json, re

s = requests.Session()
s.trust_env = False
s.verify = False
s.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://quote.eastmoney.com/'
})

# 东方财富全市场涨跌统计
print('=== 东财全市场涨跌统计 ===')
try:
    url = 'https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50000&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs=m%3A0+t%3A6%2Cm%3A0+t%3A80%2Cm%3A1+t%3A2%2Cm%3A1+t%3A23%2Cm%3A0+t%3A81+s%3A2048&fields=f3,f20'
    r = s.get(url, timeout=10)
    print('status:', r.status_code, 'len:', len(r.text))
    d = r.json()
    items = d.get('data', {}).get('diff', [])
    if items:
        up = sum(1 for x in items if x.get('f3', -9999) > 0)
        down = sum(1 for x in items if x.get('f3', 0) < 0)
        flat = sum(1 for x in items if x.get('f3', -1) == 0)
        print(f'涨: {up}  跌: {down}  平: {flat}  共: {len(items)}')
    else:
        print('空数据:', r.text[:200])
except Exception as e:
    print('ERROR:', e)

print()
print('=== 东财指数PE接口 ===')
for code, name in [('000300','沪深300'), ('000905','中证500'), ('399006','创业板')]:
    try:
        market = '1' if code.startswith('0') else '0'
        url = f'https://push2.eastmoney.com/api/qt/stock/get?secid={market}.{code}&fields=f9,f23,f116,f117'
        r = s.get(url, timeout=8)
        d = r.json().get('data', {})
        pe_raw = d.get('f9', 0)
        pb_raw = d.get('f23', 0)
        pe = pe_raw / 100 if pe_raw and pe_raw > 0 else None
        pb = pb_raw / 100 if pb_raw and pb_raw > 0 else None
        print(f'{name}({code}): PE={pe}x PB={pb}x  raw f9={pe_raw} f23={pb_raw}')
    except Exception as e:
        print(f'{name} ERROR: {e}')

print()
print('=== 北向资金 kamt 实际字段 ===')
try:
    r = s.get('https://push2.eastmoney.com/api/qt/kamt/get?fields1=f1,f2,f3,f4&fields2=f51,f52,f53,f54,f55,f56&cb=', timeout=8)
    d = r.json()
    data = d.get('data', {})
    # hk2sh = 沪股通（北向），hk2sz = 深股通（北向）
    hk2sh = data.get('hk2sh', {})
    hk2sz = data.get('hk2sz', {})
    net_sh = hk2sh.get('dayNetAmtIn', 0)   # 单位：万元
    net_sz = hk2sz.get('dayNetAmtIn', 0)
    total = net_sh + net_sz
    print(f'沪股通净流入: {net_sh/1e4:.2f}亿元')
    print(f'深股通净流入: {net_sz/1e4:.2f}亿元')
    print(f'北向合计: {total/1e4:.2f}亿元  date={hk2sh.get("date2","")}')
    print(f'raw net_sh={net_sh} net_sz={net_sz}')
except Exception as e:
    print('ERROR:', e)
