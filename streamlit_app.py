# streamlit_app.py
# ------------------------------------------------------------
# NSE F&O Current-Day Breakout Scanner (full, self-contained)
# - Live F&O list pulled from NSE website (MII .gz -> CSV fallback)
# - Threaded scanning over entire list with yfinance
# - Breakout conditions:
#     * Today's close > (lookback High * 1.005)
#     * Today's volume > (lookback avg volume * min_volume_ratio)
#     * Tight consolidation (< 15%) in lookback
# - Export results to Excel
# ------------------------------------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import requests, time, gzip, io, csv, re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import yfinance as yf
import openpyxl
from io import BytesIO

# ---------------------- Page & Styles -----------------------
st.set_page_config(page_title="NSE F&O — Full Universe Breakout Scanner",
                   page_icon="📈", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
body, [data-testid="stAppViewContainer"] { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

st.title("📈 NSE F&O — Live Universe Breakout Scanner (Current-Day)")

# ---------------------- NSE fetch utils ---------------------

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

LEGACY_FO_UNDERLYING_CSV = "https://archives.nseindia.com/content/fo/fo_underlyinglist.csv"
DERIV_ALL_REPORTS = "https://www.nseindia.com/all-reports-derivatives"  # Page that lists F&O-MII Contract File (.gz)

def _bootstrap_nse_session(timeout=10) -> requests.Session:
    s = requests.Session()
    s.headers.update(NSE_HEADERS)
    try:
        s.get("https://www.nseindia.com", timeout=timeout)
        s.get("https://www.nseindia.com/market-data", timeout=timeout)
    except Exception:
        pass
    return s

def _extract_gz_links_from_html(html: str):
    # Pull every .gz link; we’ll pick the first that looks like contract file
    candidates = re.findall(r'https?://[^\s"\']+\.gz', html)
    # Prefer links with 'contract' or 'mii' in path
    ranked = sorted(candidates, key=lambda u: (("contract" in u.lower()) or ("mii" in u.lower())), reverse=True)
    return ranked

def _download_gz_as_text(s: requests.Session, url: str, timeout=20) -> str:
    r = s.get(url, timeout=timeout)
    r.raise_for_status()
    raw = io.BytesIO(r.content)
    with gzip.GzipFile(fileobj=raw, mode="rb") as gz:
        return gz.read().decode("utf-8", errors="replace")

def _symbols_from_mii_csv_text(csv_text: str):
    cols_candidates = [
        "SYMBOL","UnderlyingSymbol","Underlying","UNDERLYING","TRD_SYMBOL","TRADING_SYMBOL"
    ]
    syms = set()
    try:
        df = pd.read_csv(io.StringIO(csv_text))
        df_cols = {c.strip().upper(): c for c in df.columns}
        chosen = None
        for cand in cols_candidates:
            if cand.upper() in df_cols:
                chosen = df_cols[cand.upper()]
                break
        if chosen is None:
            for c in df.columns:
                if "SYMBOL" in c.upper() or "UNDER" in c.upper():
                    chosen = c
                    break
        if chosen is None:
            return []
        for v in df[chosen].astype(str).tolist():
            sym = v.strip().upper()
            if not sym:
                continue
            if sym in ("NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY","NIFTYIT","NIFTYBANK"):
                continue
            root = re.split(r'[\-_/ ]', sym)[0]
            root = re.sub(r'\d.*$', '', root)
            root = re.sub(r'(PE|CE|FUT|OPT).*$', '', root)
            root = root.strip(".& ").upper()
            # Keep alpha-only roots typical for equities
            if 2 <= len(root) <= 15 and root.isalpha():
                syms.add(root)
    except Exception:
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            fieldnames = [f.strip() for f in (reader.fieldnames or [])]
            chosen = None
            for cand in cols_candidates:
                if cand in fieldnames or cand.upper() in [f.upper() for f in fieldnames]:
                    chosen = cand
                    break
            rows = list(reader)
            if not chosen and fieldnames:
                for f in fieldnames:
                    if "SYMBOL" in f.upper() or "UNDER" in f.upper():
                        chosen = f
                        break
            if chosen:
                for row in rows:
                    v = str(row.get(chosen, "")).strip().upper()
                    if not v:
                        continue
                    if v in ("NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY","NIFTYIT","NIFTYBANK"):
                        continue
                    root = re.split(r'[\-_/ ]', v)[0]
                    root = re.sub(r'\d.*$', '', root)
                    root = re.sub(r'(PE|CE|FUT|OPT).*$', '', root)
                    root = root.strip(".& ").upper()
                    if 2 <= len(root) <= 15 and root.isalpha():
                        syms.add(root)
        except Exception:
            return []
    out = sorted({f"{x}.NS" for x in syms})
    return out

@st.cache_data(show_spinner=False)
def fetch_current_fno_symbols_from_nse(max_age_hours=24) -> list:
    """
    Fetch live NSE F&O symbols (with .NS suffix) from NSE website.
    Cached for 24h to avoid rate-limits.
    """
    s = _bootstrap_nse_session()
    # 1) Try All Reports – Derivatives page
    try:
        r = s.get(DERIV_ALL_REPORTS, timeout=15)
        r.raise_for_status()
        gz_links = _extract_gz_links_from_html(r.text)
        for link in gz_links[:5]:  # Try a few plausible links
            try:
                text = _download_gz_as_text(s, link, timeout=25)
                syms = _symbols_from_mii_csv_text(text)
                if syms:
                    return syms
            except Exception:
                continue
    except Exception:
        pass

    # 2) Fallback to legacy CSV (still available in many regions)
    try:
        r = s.get(LEGACY_FO_UNDERLYING_CSV, timeout=15)
        if r.status_code == 200:
            df = pd.read_csv(io.StringIO(r.text))
            # Expect a column named 'SYMBOL'
            if 'SYMBOL' in df.columns:
                base = df['SYMBOL'].astype(str).str.strip().str.upper()
                base = [b for b in base if b not in ("NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY","NIFTYIT","NIFTYBANK")]
                syms = sorted({f"{x}.NS" for x in base if x})
                if syms:
                    return syms
    except Exception:
        pass

    return []  # Let caller decide a backup locally

# -------------------- Scanner: Breakout Logic ----------------

def _get_history(symbol: str, period="6mo", interval="1d"):
    try:
        data = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
        if isinstance(data.index, pd.DatetimeIndex):
            data = data.tz_localize(None)
        return data
    except Exception:
        return pd.DataFrame()

def detect_current_day_breakout(data: pd.DataFrame, lookback_days=20, min_volume_ratio=2.0):
    """
    Returns (detected: bool, strength: float, info: dict)
    """
    if data is None or data.empty or len(data) < lookback_days + 2:
        return False, 0.0, {}

    current = data.iloc[-1]
    lookback = data.iloc[-(lookback_days+1):-1]

    # Resistance & support
    resistance = float(lookback['High'].max())
    support = float(lookback['Low'].min())

    # Conditions (today only)
    price_breakout = current['Close'] > resistance * 1.005
    volume_breakout = current['Volume'] > (lookback['Volume'].mean() * min_volume_ratio)

    # Consolidation quality
    cons_range = (resistance - support) / max(support, 1e-9) * 100.0
    tight_cons = cons_range < 15

    if not (price_breakout and volume_breakout and tight_cons):
        return False, 0.0, {}

    # Strength score
    strength = 0.0
    breakout_pct = (current['Close'] - resistance) / resistance * 100.0
    if breakout_pct >= 3: strength += 35
    elif breakout_pct >= 2: strength += 25
    elif breakout_pct >= 1: strength += 20
    elif breakout_pct >= 0.5: strength += 15

    vol_ratio = current['Volume'] / max(lookback['Volume'].mean(), 1.0)
    if vol_ratio >= 4: strength += 30
    elif vol_ratio >= 3: strength += 25
    elif vol_ratio >= 2: strength += 20

    if cons_range <= 8: strength += 25
    elif cons_range <= 12: strength += 20
    elif cons_range <= 15: strength += 15

    # Close-in-range strength
    day_range = max(current['High'] - current['Low'], 1e-9)
    close_strength = (current['Close'] - current['Low']) / day_range * 100.0
    if close_strength >= 80: strength += 10
    elif close_strength >= 60: strength += 5

    info = {
        "current_date": str(current.name.date()) if hasattr(current.name, "date") else str(current.name),
        "current_close": float(current['Close']),
        "current_high": float(current['High']),
        "current_low": float(current['Low']),
        "current_volume": int(current['Volume']),
        "resistance_level": float(resistance),
        "support_level": float(support),
        "breakout_percentage": float(breakout_pct),
        "volume_ratio": float(vol_ratio),
        "consolidation_range_pct": float(cons_range),
        "close_strength_pct": float(close_strength),
        "lookback_days": int(lookback_days),
    }
    return True, strength, info

def scan_symbol(symbol: str, lookback_days=20, min_volume_ratio=2.0):
    data = _get_history(symbol, period="6mo", interval="1d")
    if data is None or data.empty:
        return None
    detected, strength, info = detect_current_day_breakout(data, lookback_days, min_volume_ratio)
    if not detected:
        return None
    row = {
        "symbol": symbol,
        "date": info["current_date"],
        "close": info["current_close"],
        "high": info["current_high"],
        "low": info["current_low"],
        "volume": info["current_volume"],
        "resistance": info["resistance_level"],
        "support": info["support_level"],
        "breakout_%": info["breakout_percentage"],
        "vol_ratio": info["volume_ratio"],
        "cons_range_%": info["consolidation_range_pct"],
        "close_strength_%": info["close_strength_pct"],
        "strength_score": strength,
    }
    return row

def to_excel_bytes(df: pd.DataFrame, sheet_name="Qualifying Stocks"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    # Header
    headers = list(df.columns)
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=c, value=h)
        cell.font = openpyxl.styles.Font(bold=True)
    # Rows
    for r_idx, (_, r) in enumerate(df.iterrows(), start=2):
        for c_idx, h in enumerate(headers, start=1):
            ws.cell(row=r_idx, column=c_idx, value=r[h])
    # Widths
    for i in range(1, len(headers)+1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = 16
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.read()

# -------------------------- UI ------------------------------

with st.sidebar:
    st.subheader("Universe & Scan Settings")
    st.caption("Symbols fetched live from NSE (MII .gz → CSV fallback). Cached 24h.")
    colA, colB = st.columns(2)
    lookback_days = colA.number_input("Lookback Days", min_value=10, max_value=60, value=20, step=1)
    min_vol_ratio = colB.number_input("Min Volume Ratio (x)", min_value=1.0, max_value=5.0, value=2.0, step=0.1)
    max_workers = st.slider("Threads", 4, 32, 16, 2)
    st.markdown("---")
    st.caption("Tip: Reduce lookback or threads if you hit rate limits.")

st.info("Fetching **current** NSE F&O universe from NSE website…")
symbols = fetch_current_fno_symbols_from_nse()  # cached
if not symbols:
    st.error("Could not fetch F&O list from NSE (both sources failed). You can retry or use a local backup list.")
else:
    st.success(f"Fetched **{len(symbols)}** live F&O symbols from NSE.")
    st.write(", ".join(symbols[:25]) + (" …" if len(symbols) > 25 else ""))

st.markdown("### Run Scan")
run = st.button("🚀 Scan Entire F&O Universe", type="primary")

if run and symbols:
    progress = st.progress(0.0, text="Scanning…")
    results = []
    errors = 0

    def _task(sym):
        try:
            return scan_symbol(sym, lookback_days=lookback_days, min_volume_ratio=min_vol_ratio)
        except Exception:
            return "ERROR"

    total = len(symbols)
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_task, s): s for s in symbols}
        for fut in as_completed(futures):
            res = fut.result()
            if res == "ERROR":
                errors += 1
            elif isinstance(res, dict):
                results.append(res)
            done += 1
            progress.progress(done/total, text=f"Scanning… {done}/{total}")

    progress.empty()

    if not results:
        st.warning("No symbols met the breakout criteria today.")
    else:
        df = pd.DataFrame(results)
        df = df.sort_values(["strength_score","breakout_%","vol_ratio"], ascending=[False, False, False]).reset_index(drop=True)
        st.subheader(f"✅ {len(df)} Symbols Passed")
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Download
        excel_bytes = to_excel_bytes(df[["symbol"]].rename(columns={"symbol":"Stock Symbol"}))
        st.download_button("💾 Download Qualifying Symbols (Excel)",
                           data=excel_bytes, file_name=f"fno_breakouts_{datetime.now().date()}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Full Results (CSV)",
                           data=csv_bytes, file_name=f"fno_breakout_results_{datetime.now().date()}.csv",
                           mime="text/csv")

        st.caption(f"Errors during scan (likely rate-limit/timeouts): {errors}")

# ----------------------- Footer Notes -----------------------
st.markdown("""
---  
**Notes**
- F&O universe source priority: **All Reports – Derivatives → F&O-MII Contract File (.gz)**, then legacy **fo_underlyinglist.csv**.
- Breakout logic uses *today’s* close & volume only (vs last `lookback_days`) to avoid stale signals.
- yfinance can rate-limit; adjust **Threads** if you see many errors.
""")
