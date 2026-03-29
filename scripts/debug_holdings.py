import sys
sys.path.insert(0, r'c:\Users\Administrator\Desktop\investment-daily')
import main

cfg = main.load_config()
results = main.calc_holdings(cfg['holdings'])
summary = main.calc_summary(results)

etf = [(r['name'], r.get('value',0)) for r in results if r.get('type')=='etf' and 'error' not in r]
stock = [(r['name'], r.get('value',0)) for r in results if r.get('type') in ('stock','bond') and 'error' not in r]

print('== ETF ==')
for n, v in sorted(etf, key=lambda x: -x[1]):
    print(f'  {n}: {v:,.0f}')
print(f'  小计: {sum(v for _,v in etf):,.0f}')

print('\n== 个股/可转债 ==')
for n, v in sorted(stock, key=lambda x: -x[1]):
    print(f'  {n}: {v:,.0f}')
print(f'  小计: {sum(v for _,v in stock):,.0f}')

print(f'\n总市值: {summary["total_value"]:,.0f}')
print(f'ETF比例: {summary["etf_ratio"]:.1f}%')
