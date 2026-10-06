#!/usr/bin/env python3
"""Build the FX monitor (single self-contained HTML).

Usage:
  python3 build.py            # rebuild data.json from raw/ + inject into template -> fx_monitor.html
  python3 build.py --fetch    # first re-download raw data (Yahoo Finance daily chart API)
  python3 build.py --out index.html   # write to another file (used by the GitHub Actions workflow)
  python3 build.py --shots    # also take 1440-wide screenshots of every page + print PDF
"""
import sys, os, json, time, datetime, subprocess, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
CHROME = 'google-chrome'
YAHOO = ("EURUSD USDJPY USDCHF GBPUSD AUDUSD NZDUSD USDCAD AUDJPY EURJPY EURGBP EURAUD EURNZD GBPJPY AUDNZD AUDCAD NZDJPY NZDCAD CADJPY "
         "USDCNY USDMYR USDIDR USDSGD USDTWD").split()
UA = {'User-Agent': 'Mozilla/5.0'}

UAS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36',
       'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
       'Mozilla/5.0']

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UAS[0], 'Accept': 'application/json'}), timeout=30).read()

def get_chart(sym):
    """Yahoo chart JSON with retries across hosts / user agents. Returns bytes or raises."""
    last = None
    for attempt in range(6):
        host = ('query1', 'query2')[attempt % 2]
        url = f'https://{host}.finance.yahoo.com/v8/finance/chart/{sym}=X?range=2y&interval=1d'
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UAS[attempt % len(UAS)], 'Accept': 'application/json'})
            body = urllib.request.urlopen(req, timeout=30).read()
            j = json.loads(body)
            r = j['chart']['result'][0]
            if len(r.get('timestamp', [])) > 100:
                return body
            last = f'short series ({len(r.get("timestamp", []))})'
        except Exception as e:
            last = repr(e)
        time.sleep(2 + attempt * 3)
    raise RuntimeError(f'{sym}: {last}')

def fetch():
    os.makedirs('raw', exist_ok=True)
    fails = []
    for s in YAHOO:
        try:
            open(f'raw/{s}.json', 'wb').write(get_chart(s))
        except Exception as e:
            fails.append(str(e)); print('FETCH FAIL', e)
        time.sleep(0.5)
    if fails:
        # keep going only if we still have a (possibly older) file for every symbol
        missing = [s for s in YAHOO if not os.path.exists(f'raw/{s}.json')]
        if missing or len(fails) > len(YAHOO) // 2:
            raise SystemExit('fetch failed: ' + '; '.join(fails))

def build(out='fx_monitor.html'):
    subprocess.run([sys.executable, 'build_data.py'], check=True)
    t = open('template.html', encoding='utf-8').read(); d = open('data.json', encoding='utf-8').read()
    assert '/*DATA*/' in t
    open(out, 'w', encoding='utf-8').write(t.replace('/*DATA*/', d.replace('</', '<\\/')))
    print('wrote', out, os.path.getsize(out), 'bytes')

def shots():
    from PIL import Image
    url = 'file://' + os.path.join(HERE, 'fx_monitor.html')
    for h, name in [('p1', 'fx_page1'), ('p2', 'fx_page2'), ('cross', 'fx_cross'), ('monthly', 'fx_monthly')]:
        tmp = f'/tmp/fxshot_{h}.png'
        subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--window-size=1440,3000',
                        f'--screenshot={tmp}', f'{url}#{h}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        im = Image.open(tmp).convert('RGB'); w, hh = im.size; px = im.load(); bg = px[5, hh - 5]; y = hh - 1
        while y > 0 and all(px[x, y] == bg for x in range(0, w, 4)): y -= 1
        im.crop((0, 0, w, min(hh, y + 20))).save(f'{name}.png'); print(name + '.png', w, y + 20)
    subprocess.run(['cp', 'fx_page1.png', 'fx_monitor.png'])
    subprocess.run([CHROME, '--headless=new', '--no-sandbox', '--disable-gpu', '--no-pdf-header-footer',
                    '--print-to-pdf=' + os.path.join(HERE, 'fx_monitor_print.pdf'), url + '#p1'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(subprocess.run(['pdfinfo', 'fx_monitor_print.pdf'], capture_output=True, text=True).stdout)

if __name__ == '__main__':
    if '--fetch' in sys.argv: fetch()
    out = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else 'fx_monitor.html'
    build(out)
    if '--shots' in sys.argv: shots()
