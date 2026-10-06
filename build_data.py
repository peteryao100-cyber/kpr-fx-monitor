import json,datetime,os
from zoneinfo import ZoneInfo
LON=ZoneInfo('Europe/London'); SH=ZoneInfo('Asia/Shanghai')
START='2025-08-01'
# The 18 grid pairs, in display order (Page 1 = first 9, Page 2 = last 9)
PAIRS="EURUSD USDJPY USDCHF GBPUSD AUDUSD NZDUSD USDCAD AUDJPY EURJPY EURGBP EURAUD EURNZD GBPJPY AUDNZD AUDCAD NZDJPY NZDCAD CADJPY".split()
BIZ="USDCAD USDCNY USDMYR USDIDR USDSGD USDTWD".split()
cols=PAIRS+[b for b in BIZ if b not in PAIRS]
series={}; src={}; asof={}
for p in cols:
    r=json.load(open(f'raw/{p}.json'))['chart']['result'][0]
    s={}
    for t,c in zip(r['timestamp'],r['indicators']['quote'][0]['close']):
        if c is None: continue
        d=datetime.datetime.fromtimestamp(t,LON).date()
        if d.weekday()>=5 or str(d)<START: continue
        s[str(d)]=c
    series[p]=s; src[p]='Yahoo Finance'
    asof[p]=datetime.datetime.fromtimestamp(r['meta']['regularMarketTime'],SH).strftime('%Y-%m-%d %H:%M')
dates=sorted(set(d for p in series for d in series[p]))
rows=[[d]+[(round(series[p][d],6) if d in series[p] else None) for p in cols] for d in dates]
for p in cols:
    m=[d for d in dates if d not in series[p]]
    if m: print('missing',p,len(m),m[:8])
now=datetime.datetime.now(datetime.timezone.utc)
lon_today=str(now.astimezone(LON).date())
live=lon_today if dates and dates[-1]==lon_today else None   # Yahoo FX daily bar for the current London day is still forming
out={'generated':now.astimezone(SH).strftime('%Y-%m-%d %H:%M'),'generated_utc':now.strftime('%Y-%m-%dT%H:%M:%SZ'),'live':live,'cols':cols,'pairs':PAIRS,'biz':BIZ,'rows':rows,'src':src,'asof':asof}
json.dump(out,open('data.json','w'),separators=(',',':'))
print(len(dates),dates[0],dates[-1],os.path.getsize('data.json'))
