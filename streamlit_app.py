# NSE F&O PCS Professional Scanner — Enhanced App (v6.2)
# -------------------------------------------------------
# Single-file Streamlit app that embeds the refactored PCSScannerPro + UI
# Focus: correctness, robustness, speed, and PCS-first signal quality

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import yfinance as yf
import ta
import streamlit as st
from io import BytesIO
import openpyxl
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz

# -------------------------------------------------------
# Streamlit Page Config + Styling
# -------------------------------------------------------
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
/* keep things lightweight; rely on Streamlit theme and add only minor polish */
.block-container{padding-top:1rem;padding-bottom:1rem;}
h1,h2,h3{letter-spacing:-.01em}
.dataframe td{font-size:.9rem}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------
# Universe/Lists (trimmed; feel free to expand)
# -------------------------------------------------------
COMPLETE_NSE_FO_UNIVERSE = [
    'RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS','ICICIBANK.NS','BHARTIARTL.NS','ITC.NS','SBIN.NS',
    'LT.NS','KOTAKBANK.NS','AXISBANK.NS','MARUTI.NS','ASIANPAINT.NS','WIPRO.NS','ONGC.NS','NTPC.NS',
    'POWERGRID.NS','TATAMOTORS.NS','TECHM.NS','ULTRACEMCO.NS','SUNPHARMA.NS','TITAN.NS','COALINDIA.NS',
    'BAJFINANCE.NS','HCLTECH.NS','JSWSTEEL.NS','INDUSINDBK.NS','BRITANNIA.NS','CIPLA.NS','DRREDDY.NS',
    'EICHERMOT.NS','GRASIM.NS','HEROMOTOCO.NS','HINDALCO.NS','TATASTEEL.NS','BPCL.NS','M&M.NS',
    'BAJAJ-AUTO.NS','SHRIRAMFIN.NS','ADANIPORTS.NS','APOLLOHOSP.NS','BAJAJFINSV.NS','DIVISLAB.NS',
    'NESTLEIND.NS','TRENT.NS','HDFCLIFE.NS','SBILIFE.NS','LTIM.NS','ADANIENT.NS','HINDUNILVR.NS'
]

STOCK_CATEGORIES = {
    'Nifty 50': [
        'RELIANCE.NS','TCS.NS','HDFCBANK.NS','INFY.NS','ICICIBANK.NS','BHARTIARTL.NS','ITC.NS','SBIN.NS',
        'LT.NS','KOTAKBANK.NS','AXISBANK.NS','MARUTI.NS','ASIANPAINT.NS','WIPRO.NS','ONGC.NS','NTPC.NS',
        'POWERGRID.NS','TATAMOTORS.NS','TECHM.NS','ULTRACEMCO.NS','SUNPHARMA.NS','TITAN.NS','COALINDIA.NS',
        'BAJFINANCE.NS','HCLTECH.NS','JSWSTEEL.NS','INDUSINDBK.NS','BRITANNIA.NS','CIPLA.NS','DRREDDY.NS',
        'EICHERMOT.NS','GRASIM.NS','HEROMOTOCO.NS','HINDALCO.NS','TATASTEEL.NS','BPCL.NS','M&M.NS',
        'BAJAJ-AUTO.NS','SHRIRAMFIN.NS','ADANIPORTS.NS','APOLLOHOSP.NS','BAJAJFINSV.NS','DIVISLAB.NS',
        'NESTLEIND.NS','TRENT.NS','HDFCLIFE.NS','SBILIFE.NS','LTIM.NS','ADANIENT.NS','HINDUNILVR.NS'
    ],
    'Bank Nifty': ['HDFCBANK.NS','ICICIBANK.NS','SBIN.NS','KOTAKBANK.NS','AXISBANK.NS','INDUSINDBK.NS','BANKBARODA.NS','CANBK.NS','FEDERALBNK.NS','PNB.NS','IDFCFIRSTB.NS','AUBANK.NS'],
    'IT Stocks': ['TCS.NS','INFY.NS','WIPRO.NS','HCLTECH.NS','TECHM.NS','LTIM.NS','MPHASIS.NS','COFORGE.NS','PERSISTENT.NS','LTTS.NS'],
    'Pharma Stocks': ['SUNPHARMA.NS','CIPLA.NS','DRREDDY.NS','DIVISLAB.NS','LUPIN.NS','BIOCON.NS','AUROPHARMA.NS','ALKEM.NS','TORNTPHARM.NS','GLENMARK.NS'],
}

# -------------------------------------------------------
# Helpers (symbol cleaning, export)
# -------------------------------------------------------
_SYMBOL_CLEAN_RE = re.compile(r"[^A-Z0-9\.-]")

def clean_symbol(sym: str) -> str:
    sym = sym.strip().upper()
    sym = _SYMBOL_CLEAN_RE.sub("", sym)
    sym = sym.replace("IIFLWAM.NS", "360ONE.NS")
    return sym


def create_excel_stock_list(symbols: List[str]) -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Qualifying Stocks"
    ws['A1'] = "Stock Symbol"
    ws['A1'].font = openpyxl.styles.Font(bold=True, size=12)
    for i, s in enumerate(symbols, start=2):
        ws[f"A{i}"] = s.replace('.NS','')
    ws.column_dimensions['A'].width = 20
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.getvalue()

# -------------------------------------------------------
# Data Class
# -------------------------------------------------------
@dataclass
class WeeklyValidation:
    ok: bool
    bonus: float
    signals: List[str]
    context: str

# -------------------------------------------------------
# Core Scanner (Refactor v6.2)
# -------------------------------------------------------
class PCSScannerPro:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    @staticmethod
    def _safe_history(symbol: str, period: str="6mo", interval: str="1d") -> Optional[pd.DataFrame]:
        symbol = clean_symbol(symbol)
        try:
            df = yf.Ticker(symbol).history(period=period, interval=interval, auto_adjust=False)
            if isinstance(df, pd.DataFrame) and not df.empty:
                df = df.dropna(subset=["Open","High","Low","Close"]).copy()
                if not isinstance(df.index, pd.DatetimeIndex):
                    df.index = pd.to_datetime(df.index)
                return df
        except Exception:
            return None
        return None

    @st.cache_data(ttl=600, show_spinner=False)
    def get_daily(self, symbol: str, period: str="6mo") -> Optional[pd.DataFrame]:
        df = self._safe_history(symbol, period=period, interval="1d")
        if df is None or len(df) < 30:
            return None
        c,h,l = df["Close"], df["High"], df["Low"]
        rsi = ta.momentum.RSIIndicator(c).rsi()
        sma20 = ta.trend.SMAIndicator(c, window=20).sma_indicator()
        sma50 = ta.trend.SMAIndicator(c, window=50).sma_indicator()
        ema20 = ta.trend.EMAIndicator(c, window=20).ema_indicator()
        bb = ta.volatility.BollingerBands(c)
        macd_obj = ta.trend.MACD(c)
        adx = ta.trend.ADXIndicator(h,l,c).adx()
        atr = ta.volatility.AverageTrueRange(h,l,c).average_true_range()
        stoch = ta.momentum.StochasticOscillator(h,l,c).stoch()
        willr = ta.momentum.WilliamsRIndicator(h,l,c).williams_r()
        out = df.assign(
            RSI=rsi, SMA_20=sma20, SMA_50=sma50, EMA_20=ema20,
            BB_upper=bb.bollinger_hband(), BB_middle=bb.bollinger_mavg(), BB_lower=bb.bollinger_lband(),
            MACD=macd_obj.macd(), MACD_signal=macd_obj.macd_signal(), MACD_hist=macd_obj.macd_diff(),
            ADX=adx, ATR=atr, Stoch_K=stoch, Williams_R=willr
        )
        return out.dropna().copy()

    @st.cache_data(ttl=1200, show_spinner=False)
    def get_weekly(self, symbol: str, period: str="18mo") -> Optional[pd.DataFrame]:
        d = self._safe_history(symbol, period=period, interval="1d")
        if d is None or len(d) < 60:
            return None
        w = d.resample('W-FRI').agg({"Open":"first","High":"max","Low":"min","Close":"last","Volume":"sum"}).dropna()
        if len(w) < 15:
            return None
        c,h,l = w['Close'], w['High'], w['Low']
        rsi = ta.momentum.RSIIndicator(c).rsi()
        sma10 = ta.trend.SMAIndicator(c, window=10).sma_indicator()
        sma20 = ta.trend.SMAIndicator(c, window=20).sma_indicator()
        ema10 = ta.trend.EMAIndicator(c, window=10).ema_indicator()
        macd_obj = ta.trend.MACD(c)
        adx = ta.trend.ADXIndicator(h,l,c).adx()
        w = w.assign(RSI=rsi, SMA_10=sma10, SMA_20=sma20, EMA_10=ema10,
                     MACD=macd_obj.macd(), MACD_signal=macd_obj.macd_signal(), MACD_hist=macd_obj.macd_diff(), ADX=adx)
        return w.dropna().copy()

    # ---------- Weekly Validation ----------
    def validate_weekly(self, weekly: pd.DataFrame) -> WeeklyValidation:
        if weekly is None or len(weekly) < 10:
            return WeeklyValidation(False, 0, [], "Insufficient weekly data")
        c = weekly['Close'].iloc[-1]
        rsi = weekly['RSI'].iloc[-1]
        macd = weekly['MACD'].iloc[-1]; macd_sig = weekly['MACD_signal'].iloc[-1]
        sma10 = weekly['SMA_10'].iloc[-1]; sma20 = weekly['SMA_20'].iloc[-1]
        adx = weekly['ADX'].iloc[-1]
        signals, bonus = [], 0
        if c > sma10 > sma20: signals.append("Weekly uptrend (Close>SMA10>SMA20)"); bonus += 15
        elif c > sma10: signals.append("Close above SMA10"); bonus += 8
        if 40 <= rsi <= 70: signals.append(f"RSI healthy ({rsi:.1f})"); bonus += 10
        if macd > macd_sig and macd > 0: signals.append("MACD bullish >0 & >signal"); bonus += 12
        if adx >= 25: signals.append(f"ADX {adx:.1f} strong"); bonus += 8
        ok = bonus >= 20 and len(signals) >= 2
        ctx = "Strong weekly alignment" if bonus >= 30 else ("Moderate weekly support" if bonus >= 20 else "Weak weekly")
        return WeeklyValidation(ok, bonus, signals, ctx)

    # ---------- Current-Day Breakout ----------
    def current_day_breakout(self, df: pd.DataFrame, lookback: int=20, vol_ratio: float=2.0) -> Tuple[bool,float,Dict]:
        if df is None or len(df) < lookback + 2:
            return False, 0, {}
        cur = df.iloc[-1]
        lb = df.iloc[-(lookback+1):-1]
        res = float(lb['High'].max()); sup = float(lb['Low'].min())
        avgv = float(lb['Volume'].mean()) if lb['Volume'].mean() > 0 else 1.0
        price_break = cur['Close'] > res * 1.005
        vol_ok = cur['Volume'] > avgv * vol_ratio
        cons_range = (res - sup) / max(sup, 1e-9) * 100
        if not (price_break and vol_ok and cons_range < 15):
            return False, 0, {}
        strength = 0
        brk_pct = (cur['Close'] - res) / res * 100
        strength += 35 if brk_pct >= 3 else 25 if brk_pct >= 2 else 20 if brk_pct >= 1 else 15
        vratio = cur['Volume'] / avgv
        strength += 30 if vratio >= 4 else 25 if vratio >= 3 else 20
        strength += 25 if cons_range <= 8 else 20 if cons_range <= 12 else 15
        rng = cur['High'] - cur['Low']
        close_pos = (cur['Close'] - cur['Low']) / rng * 100 if rng > 0 else 50
        strength += 10 if close_pos >= 80 else 5 if close_pos >= 60 else 0
        details = {
            'current_close': float(cur['Close']), 'current_high': float(cur['High']), 'current_volume': int(cur['Volume']),
            'resistance_level': res, 'support_level': sup, 'breakout_percentage': brk_pct,
            'volume_ratio': vratio, 'consolidation_range': cons_range, 'lookback_days': lookback,
        }
        return True, float(strength), details

    # ---------- Enhanced Support/Resistance ----------
    def enhanced_sr(self, df: pd.DataFrame, lookback: int=50) -> Dict:
        if df is None or len(df) < lookback:
            return {"analysis_available": False, "message": "Insufficient data"}
        cur = float(df['Close'].iloc[-1])
        levels = []
        levels += self._pivot_levels(df, lookback)
        levels += self._ma_levels(df)
        levels += self._volume_zones(df, lookback)
        levels += self._psych_levels(cur)
        levels += self._fib_levels(df, lookback)
        out = []
        for L in levels:
            strength = L.get('base_strength', 20)
            dist = abs(L['level'] - cur) / cur * 100
            if dist <= 1: strength += 25
            elif dist <= 3: strength += 15
            elif dist <= 5: strength += 8
            out.append({**L, "strength": min(100, round(strength,2))})
        supports = sorted([x for x in out if x['type']=="support"], key=lambda x: x['strength'], reverse=True)
        resists  = sorted([x for x in out if x['type']=="resistance"], key=lambda x: x['strength'], reverse=True)
        return {"analysis_available": True, "current_price": cur, "support_levels": supports[:5], "resistance_levels": resists[:5]}

    def _pivot_levels(self, df: pd.DataFrame, lookback: int) -> List[Dict]:
        lev = []; r = df.tail(lookback)
        H, L = r['High'].values, r['Low'].values
        for i in range(2, len(r)-2):
            if H[i] > H[i-1] and H[i] > H[i-2] and H[i] > H[i+1] and H[i] > H[i+2]:
                lev.append({"level": float(H[i]), "type":"resistance", "method":"pivot_high", "base_strength": 30})
            if L[i] < L[i-1] and L[i] < L[i-2] and L[i] < L[i+1] and L[i] < L[i+2]:
                lev.append({"level": float(L[i]), "type":"support", "method":"pivot_low", "base_strength": 30})
        return lev

    def _ma_levels(self, df: pd.DataFrame) -> List[Dict]:
        lev, cur = [], float(df['Close'].iloc[-1])
        for p in (20, 50, 100, 200):
            if len(df) >= p:
                ma = float(df['Close'].tail(p).mean())
                lev.append({"level": ma, "type": "support" if cur > ma else "resistance", "method": f"MA_{p}", "base_strength": min(20 + p/10, 50)})
        return lev

    def _volume_zones(self, df: pd.DataFrame, lookback: int) -> List[Dict]:
        r = df.tail(lookback)
        if r.empty: return []
        thresh = r['Volume'].quantile(0.8)
        hv = r[r['Volume'] >= thresh]
        if hv.empty: return []
        centers = [float((row['High']+row['Low'])/2.0) for _, row in hv.iterrows()]
        centers.sort()
        clusters: List[List[float]] = []
        for z in centers:
            if not clusters: clusters.append([z])
            else:
                last = clusters[-1]
                if abs(z - last[-1]) / last[-1] < 0.02: last.append(z)
                else: clusters.append([z])
        out = []
        for cl in clusters:
            lvl = float(np.mean(cl)); base = 35 if len(cl) >= 3 else 25
            out.append({"level": lvl, "type": "resistance", "method": "volume_zone", "base_strength": base})
            out.append({"level": lvl, "type": "support", "method": "volume_zone", "base_strength": base})
        return out

    def _psych_levels(self, price: float) -> List[Dict]:
        lev = []
        for step in (100, 50, 25):
            lvl = round(price / step) * step
            if lvl > 0:
                lev.append({"level": float(lvl), "type": "resistance", "method": f"psych_{step}", "base_strength": 18})
                lev.append({"level": float(lvl), "type": "support", "method": f"psych_{step}", "base_strength": 18})
        return lev

    def _fib_levels(self, df: pd.DataFrame, lookback: int) -> List[Dict]:
        r = df.tail(lookback)
        hi, lo = float(r['High'].max()), float(r['Low'].min())
        if hi <= 0 or lo <= 0 or hi <= lo: return []
        span = hi - lo; fibs = [0.236, 0.382, 0.5, 0.618]
        out = []
        for f in fibs:
            lvl = lo + span * f
            out.append({"level": float(lvl), "type":"support", "method": f"fib_{f}", "base_strength": 20})
            out.append({"level": float(lvl), "type":"resistance", "method": f"fib_{f}", "base_strength": 20})
        return out

    # ---------- PCS helpers ----------
    def pcs_context(self, df: pd.DataFrame) -> Dict:
        cur = df.iloc[-1]
        atr = float(cur.get('ATR', np.nan))
        close = float(cur['Close'])
        atr_pct = (atr/close*100) if (atr and close) else np.nan
        return {"rsi": float(cur.get('RSI', np.nan)), "adx": float(cur.get('ADX', np.nan)), "atr_pct": atr_pct}

    def pcs_pick_put_delta_stub(self, underlying: float, target_delta: float=0.20) -> float:
        T = 20/252; vol = 0.22; z = 0.8416
        return round(underlying * (1 - z*vol*math.sqrt(T)), 1)

    def fundamental_news_hook(self, symbol: str) -> Dict:
        return {"items": [], "sentiment": "neutral"}

# -------------------------------------------------------
# Chart helper (light TradingView-style)
# -------------------------------------------------------
def make_chart(df: pd.DataFrame, title: str, mark_resistance: Optional[float]=None) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    if 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], name='EMA 20', mode='lines'), row=1, col=1)
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], name='SMA 50', mode='lines'), row=1, col=1)
    if mark_resistance:
        fig.add_hline(y=mark_resistance, line_dash='dash', line_color='orange', row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name='Volume', opacity=0.7), row=2, col=1)
    fig.update_layout(title=title, height=560, template='plotly_dark', xaxis_rangeslider_visible=False)
    return fig

# -------------------------------------------------------
# Sidebar Controls
# -------------------------------------------------------
st.title("📈 NSE F&O PCS Professional Scanner — v6.2")
scanner = PCSScannerPro()

with st.sidebar:
    st.header("Universe & Filters")
    universe_choice = st.selectbox("Universe", ["Nifty 50","Bank Nifty","IT Stocks","Pharma Stocks","Custom Selection","All (short list)"])
    custom_syms = st.text_area("Custom (comma-separated .NS)", placeholder="RELIANCE.NS, TCS.NS") if universe_choice=="Custom Selection" else ""
    rsi_min, rsi_max = st.slider("RSI range (daily)", 10, 90, (35, 70))
    adx_min = st.slider("ADX minimum (daily)", 5, 40, 15)
    ma_support = st.checkbox("Require price above EMA20", value=True)
    lookback = st.slider("Lookback (days) for resistance", 10, 60, 20)
    vol_ratio = st.slider("Min volume ratio vs avg", 1.0, 4.0, 2.0, 0.1)
    min_strength = st.slider("Min pattern strength", 40, 95, 65)
    max_workers = st.slider("Parallel scans", 2, 16, 8)
    run_scan = st.button("🔎 Scan Now", use_container_width=True)

# Select symbols
if universe_choice == "Custom Selection":
    symbols = [clean_symbol(s) for s in custom_syms.split(',') if s.strip()]
elif universe_choice == "All (short list)":
    symbols = COMPLETE_NSE_FO_UNIVERSE
else:
    symbols = STOCK_CATEGORIES.get(universe_choice, COMPLETE_NSE_FO_UNIVERSE)

st.caption(f"Scanning {len(symbols)} symbols…")

# -------------------------------------------------------
# Scanner Logic (parallel)
# -------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def scan_symbol(symbol: str, rsi_min: int, rsi_max: int, adx_min: int, ma_support: bool, lookback: int, vol_ratio: float, min_strength: int):
    d = scanner.get_daily(symbol)
    if d is None or len(d) < 30:
        return None
    # Daily filters
    cur = d.iloc[-1]
    if not (rsi_min <= float(cur.get('RSI', np.nan)) <= rsi_max):
        return None
    if float(cur.get('ADX', 0)) < adx_min:
        return None
    if ma_support and float(cur['Close']) < float(cur.get('EMA_20', cur['Close'])):
        return None
    ok, score, det = scanner.current_day_breakout(d, lookback=lookback, vol_ratio=vol_ratio)
    if not ok or score < min_strength:
        return None
    w = scanner.get_weekly(symbol)
    wv = scanner.validate_weekly(w) if w is not None else WeeklyValidation(False,0,[],"no weekly")
    sr = scanner.enhanced_sr(d)
    ctx = scanner.pcs_context(d)
    total = score + (wv.bonus if wv else 0)
    return {
        'symbol': symbol,
        'daily_strength': score,
        'weekly_bonus': (wv.bonus if wv else 0),
        'final_strength': total,
        'breakout': det,
        'weekly_ok': (wv.ok if wv else False),
        'weekly_ctx': (wv.context if wv else ""),
        'sr': sr,
        'ctx': ctx,
    }

results: List[Dict] = []

if run_scan:
    progress = st.progress(0.0, text="Scanning…")
    collected = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(scan_symbol, s, rsi_min, rsi_max, adx_min, ma_support, lookback, vol_ratio, min_strength): s for s in symbols}
        for i, fut in enumerate(as_completed(futs)):
            res = fut.result()
            if res: collected.append(res)
            progress.progress((i+1)/len(symbols))
    progress.empty()
    if not collected:
        st.warning("No matches with the current filters.")
    else:
        # sort by final_strength desc
        results = sorted(collected, key=lambda x: x['final_strength'], reverse=True)

# -------------------------------------------------------
# Results Table + Actions
# -------------------------------------------------------
if results:
    st.subheader("Qualified Breakouts (Current-Day Confirmed)")
    table = pd.DataFrame([
        {
            'Symbol': r['symbol'].replace('.NS',''),
            'Final Score': int(r['final_strength']),
            'Daily Strength': int(r['daily_strength']),
            'Weekly Bonus': int(r['weekly_bonus']),
            'Res(lookback)': round(r['breakout']['resistance_level'],2),
            'Vol xAvg': round(r['breakout']['volume_ratio'],2),
            'Cons%': round(r['breakout']['consolidation_range'],1),
            'RSI': round(r['ctx']['rsi'],1) if r['ctx']['rsi']==r['ctx']['rsi'] else None,
            'ADX': round(r['ctx']['adx'],1) if r['ctx']['adx']==r['ctx']['adx'] else None,
            'ATR%': round(r['ctx']['atr_pct'],1) if r['ctx']['atr_pct']==r['ctx']['atr_pct'] else None,
        } for r in results
    ])
    st.dataframe(table, use_container_width=True)

    dl = st.download_button(
        "⬇️ Download symbols (.xlsx)",
        data=create_excel_stock_list([r['symbol'] for r in results]),
        file_name="pcs_breakouts.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    # Detailed cards with charts
    st.subheader("Details & Charts")
    for r in results:
        with st.expander(f"{r['symbol']} — Score {int(r['final_strength'])} | Weekly: {r['weekly_ctx']}"):
            cols = st.columns(3)
            cols[0].metric("Vol xAvg", f"{r['breakout']['volume_ratio']:.2f}")
            cols[1].metric("Consolidation %", f"{r['breakout']['consolidation_range']:.1f}%")
            cols[2].metric("ATR %", f"{r['ctx']['atr_pct']:.1f}%" if r['ctx']['atr_pct']==r['ctx']['atr_pct'] else "—")

            d = scanner.get_daily(r['symbol'])
            fig = make_chart(d, f"{r['symbol'].replace('.NS','')} — Current-Day Breakout", r['breakout']['resistance_level'])
            st.plotly_chart(fig, use_container_width=True)

            # Support/Resistance snapshot
            sr = r['sr']
            if sr.get('analysis_available'):
                s_levels = sr['support_levels'][:3]
                r_levels = sr['resistance_levels'][:3]
                st.markdown("**Top Supports**: " + ", ".join([f"{x['level']:.2f} ({x['method']})" for x in s_levels]))
                st.markdown("**Top Resistances**: " + ", ".join([f"{x['level']:.2f} ({x['method']})" for x in r_levels]))

else:
    st.info("Set your filters and click **Scan Now** to search for current-day breakouts across your chosen universe.")
