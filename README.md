# FX Monitor 汇率监测

Static, self-contained FX monitor (18 currency pairs, weekly grid, cross check, monthly averages).

- Live page: https://peteryao100-cyber.github.io/kpr-fx-monitor/
- Data: Yahoo Finance daily chart API (prototype sample source; target official source is FX678 at a fixed daily time, TBD).
- Updated automatically by GitHub Actions (`.github/workflows/update.yml`): hourly on weekdays plus shortly after the New York close.
- Build locally: `python3 build.py --fetch --out index.html`
