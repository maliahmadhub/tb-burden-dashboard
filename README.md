# Global Tuberculosis Burden Dashboard

A consulting-grade healthcare analytics dashboard that turns the WHO Global
Tuberculosis Programme database into decision support for a TB control programme.
Built with Python + Streamlit.

**Course:** MSBA 382 — Healthcare Analytics · **Author:** Mohamad Ali Ahmad

---

## What it does
Executive KPIs, trend analysis, an interactive world map, age/sex distribution,
drug-resistance & TB/HIV views, a TB care-cascade funnel, a transparent incidence
forecast, and a methodology + recommendations narrative — all filterable by WHO
region, year and country.

## Quick start (local)
```bash
pip install -r requirements.txt
python prepare_data.py        # downloads the full real WHO dataset into ./data  (run once)
streamlit run app.py
```
Demo access code: **tb2024** (change `APP_PASSWORD` in `app.py`, or wire it to
`st.secrets` for production).

## Data
All figures come from the **WHO Global Tuberculosis Programme** public CSV database
— no data is fabricated. The app loads data in this order:
1. **Bundled** files in `./data/` (created by `prepare_data.py`) — makes the repo
   self-contained for GitHub / the Moodle submission zip.
2. **Live** download from WHO at runtime (cached 24h) if no bundled file is present.
3. A small committed **sample** so the app always renders offline.

## Deploy (Streamlit Community Cloud)
1. Push this folder to a public GitHub repo (include `./data/`).
2. On https://share.streamlit.io → New app → point to `app.py`.
3. Done — Streamlit Cloud installs `requirements.txt` and serves the app.

## Files
```
app.py              # the dashboard (multi-page, password-gated)
prepare_data.py     # one-shot real-data fetcher -> ./data
requirements.txt    # dependencies
.streamlit/config.toml  # theme
data/               # bundled WHO CSVs (+ committed sample)
```

## Source
WHO Global Tuberculosis Programme — data:
https://www.who.int/teams/global-programme-on-tuberculosis-and-lung-health/data
