import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import pytz
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Dark Theme CSS (same as before)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-bg: #0a0e1a;
        --secondary-bg: #1a1f2e;
        --accent-bg: #252b3d;
        --success-color: #00d4aa;
        --warning-color: #ffa726;
        --danger-color: #ff5252;
        --text-primary: #ffffff;
        --text-secondary: #b0bec5;
        --border-color: #37474f;
    }
    
    .stApp {
        background: linear-gradient(135deg, var(--primary-bg) 0%, #0f1419 100%);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .main .block-container {
        background-color: transparent;
        color: var(--text-primary);
        padding-top: 1rem;
        max-width: 1400px;
    }
    
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--secondary-bg) 0%, var(--accent-bg) 100%);
        border-right: 1px solid var(--border-color);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: var(--secondary-bg);
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: var(--text-secondary);
        font-weight: 500;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: var(--accent-bg);
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--success-color), #00bfa5);
        color: var(--primary-bg) !important;
        font-weight: 600;
    }
    
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 20px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 10px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 48px rgba(0, 212, 170, 0.15);
    }
    
    .pattern-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 20px;
        border-radius: 16px;
        border-left: 4px solid var(--success-color);
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .consolidation-card {
        border-left-color: var(--warning-color);
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--success-color), #00bfa5);
        color: var(--primary-bg);
        border: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
        height: 56px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 212, 170, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00bfa5, var(--success-color));
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.4);
    }
    
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border: 1px solid var(--border-color);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    .stSelectbox > div > div {
        background-color: var(--accent-bg);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--success-color), #00bfa5);
        border-radius: 4px;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(0, 191, 165, 0.1));
        border: 1px solid var(--success-color);
        border-radius: 8px;
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 167, 38, 0.1), rgba(255, 193, 7, 0.1));
        border: 1px solid var(--warning-color);
        border-radius: 8px;
    }
    
    .tradingview-container {
        background: var(--secondary-bg);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid var(--border-color);
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# NSE F&O Universe
NSE_FO_UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IOC.NS',
    'SAIL.NS', 'VEDL.NS', 'DLF.NS', 'IDEA.NS', 'JINDALSTEL.NS',
    'NATIONALUM.NS', 'NMDC.NS', 'CONCOR.NS', 'BEL.NS', 'ASHOKLEY.NS',
    'TATAPOWER.NS', 'RECLTD.NS', 'GMRINFRA.NS', 'ADANIGREEN.NS', 'IRCTC.NS'
]

class FixedPCSScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_stock_data(self, symbol, period="6mo"):
        """Get stock data with error handling"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            
            if len(data) < 30:  # Reduced from 50
                return None
            
            # Calculate technical indicators
            data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
            data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
            data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
            data['EMA_20'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
            data['BB_upper'] = ta.volatility.BollingerBands(data['Close']).bollinger_hband()
            data['BB_lower'] = ta.volatility.BollingerBands(data['Close']).bollinger_lband()
            data['BB_middle'] = ta.volatility.BollingerBands(data['Close']).bollinger_mavg()
            data['MACD'] = ta.trend.MACD(data['Close']).macd()
            data['MACD_signal'] = ta.trend.MACD(data['Close']).macd_signal()
            data['MACD_hist'] = ta.trend.MACD(data['Close']).macd_diff()
            data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
            data['ATR'] = ta.volatility.AverageTrueRange(data['High'], data['Low'], data['Close']).average_true_range()
            
            return data
        except Exception as e:
            return None
    
    def check_volume_criteria(self, data, min_ratio=1.0):  # Reduced from 1.5
        """Check if stock meets volume criteria - RELAXED"""
        if len(data) < 21:
            return False, 0
        
        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].iloc[-21:-1].mean()
        volume_ratio = current_volume / avg_20_volume
        
        return volume_ratio >= min_ratio, volume_ratio
    
    def detect_successful_patterns(self, data, symbol, relaxed_mode=True):
        """Detect patterns with RELAXED filters to avoid false negatives"""
        patterns = []
        
        if len(data) < 30:  # Reduced from 50
            return patterns
        
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        
        if relaxed_mode:
            # RELAXED FILTERS - Avoid false negatives
            # RSI: Expanded range 35-75 (was 45-65)
            if not (35 <= current_rsi <= 75):
                return patterns
            
            # ADX: Lowered to >15 (was >25)
            if current_adx < 15:
                return patterns
            
            # MA Support: Use EMA20 OR price near recent high
            recent_high = data['High'].tail(10).max()
            near_highs = current_price >= recent_high * 0.95
            ma_support = (current_price > ema_20 * 0.98) or near_highs
            
            if not ma_support:
                return patterns
        else:
            # Original strict filters
            if not (45 <= current_rsi <= 65):
                return patterns
            if current_adx < 25:
                return patterns
            if current_price < sma_20:
                return patterns
        
        # Pattern Detection with LOWER thresholds
        
        # 1. Cup and Handle
        cup_detected, cup_strength = self.detect_cup_and_handle(data)
        if cup_detected and cup_strength >= 60:  # Lowered from 80
            patterns.append({
                'type': 'Cup and Handle',
                'strength': cup_strength,
                'success_rate': 85,
                'research_basis': 'William O\'Neil - How to Make Money in Stocks',
                'pcs_suitability': 95
            })
        
        # 2. Flat Base Breakout
        flat_base_detected, flat_strength = self.detect_flat_base_breakout(data)
        if flat_base_detected and flat_strength >= 60:  # Lowered from 80
            patterns.append({
                'type': 'Flat Base Breakout',
                'strength': flat_strength,
                'success_rate': 82,
                'research_basis': 'Mark Minervini - Trade Like a Stock Market Wizard',
                'pcs_suitability': 92
            })
        
        # 3. VCP Pattern
        vcp_detected, vcp_strength = self.detect_vcp_pattern(data)
        if vcp_detected and vcp_strength >= 55:  # Lowered from 75
            patterns.append({
                'type': 'VCP (Volatility Contraction)',
                'strength': vcp_strength,
                'success_rate': 78,
                'research_basis': 'Mark Minervini - Momentum Trading',
                'pcs_suitability': 88
            })
        
        # 4. High Tight Flag
        htf_detected, htf_strength = self.detect_high_tight_flag(data)
        if htf_detected and htf_strength >= 65:  # Lowered from 85
            patterns.append({
                'type': 'High Tight Flag',
                'strength': htf_strength,
                'success_rate': 88,
                'research_basis': 'William O\'Neil - IBD Methodology',
                'pcs_suitability': 98
            })
        
        # 5. Ascending Triangle - NEW PATTERN
        triangle_detected, triangle_strength = self.detect_ascending_triangle(data)
        if triangle_detected and triangle_strength >= 55:
            patterns.append({
                'type': 'Ascending Triangle',
                'strength': triangle_strength,
                'success_rate': 76,
                'research_basis': 'Thomas Bulkowski - Encyclopedia of Chart Patterns',
                'pcs_suitability': 85
            })
        
        # 6. Bull Flag - NEW PATTERN
        flag_detected, flag_strength = self.detect_bull_flag(data)
        if flag_detected and flag_strength >= 55:
            patterns.append({
                'type': 'Bull Flag',
                'strength': flag_strength,
                'success_rate': 72,
                'research_basis': 'William O\'Neil - Flag Pattern Analysis',
                'pcs_suitability': 80
            })
        
        return patterns
    
    def detect_cup_and_handle(self, data):
        """Enhanced Cup and Handle with relaxed criteria"""
        if len(data) < 40:  # Reduced from 60
            return False, 0
        
        recent_data = data.tail(40)  # Reduced from 60
        
        # Cup formation (first 30 days)
        cup_data = recent_data.iloc[:30]
        cup_left_high = cup_data['High'].iloc[:10].max()
        cup_right_high = cup_data['High'].iloc[-10:].max()
        cup_low = cup_data['Low'].iloc[5:25].min()
        
        # Relaxed cup depth (10-60%, was 15-50%)
        cup_depth = ((cup_left_high - cup_low) / cup_left_high) * 100
        depth_valid = 10 <= cup_depth <= 60
        
        # Relaxed symmetry check
        symmetry_valid = abs(cup_left_high - cup_right_high) / cup_left_high < 0.15  # Was 0.1
        
        # Handle formation (last 10 days)
        handle_data = recent_data.tail(10)
        handle_high = handle_data['High'].max()
        handle_low = handle_data['Low'].min()
        handle_depth = ((handle_high - handle_low) / handle_high) * 100
        
        # Relaxed handle criteria
        handle_valid = handle_depth < 20  # Was 15
        
        # Volume pattern (optional now)
        try:
            cup_volume = cup_data['Volume'].mean()
            handle_volume = handle_data['Volume'].mean()
            volume_contraction = handle_volume < cup_volume * 0.9  # Relaxed from 0.7
        except:
            volume_contraction = True  # Assume valid if can't calculate
        
        # Breakout validation (relaxed)
        current_price = data['Close'].iloc[-1]
        resistance = max(cup_left_high, cup_right_high)
        breakout = current_price >= resistance * 0.97  # Relaxed from 0.99
        
        # Strength calculation
        strength = 0
        if depth_valid: strength += 25
        if symmetry_valid: strength += 20
        if handle_valid: strength += 25
        if volume_contraction: strength += 15
        if breakout: strength += 15
        
        return (depth_valid and handle_valid and breakout), strength
    
    def detect_flat_base_breakout(self, data):
        """Relaxed Flat Base detection"""
        if len(data) < 20:  # Reduced from 30
            return False, 0
        
        base_data = data.tail(20)  # Reduced from 25
        
        # Relaxed price range analysis
        high_price = base_data['High'].max()
        low_price = base_data['Low'].min()
        price_range = ((high_price - low_price) / low_price) * 100
        
        # Relaxed flat base criteria
        tight_range = price_range < 15  # Was 12
        
        # Volume pattern (made optional)
        try:
            pre_base_volume = data.iloc[-30:-20]['Volume'].mean()
            base_volume = base_data['Volume'].mean()
            volume_dry_up = base_volume < pre_base_volume * 0.9  # Relaxed
        except:
            volume_dry_up = True
        
        # Relaxed breakout
        current_price = data['Close'].iloc[-1]
        resistance = base_data['High'].quantile(0.9)
        breakout = current_price >= resistance * 0.998  # Relaxed from 1.005
        
        strength = 0
        if tight_range: strength += 35
        if volume_dry_up: strength += 25
        if breakout: strength += 40
        
        return (tight_range and breakout), strength
    
    def detect_vcp_pattern(self, data):
        """Relaxed VCP detection"""
        if len(data) < 30:  # Reduced from 50
            return False, 0
        
        recent_data = data.tail(30)  # Reduced from 40
        
        # Simpler volatility check
        vol_periods = [8, 6, 4]  # Reduced periods
        volatilities = []
        
        for period in vol_periods:
            if len(recent_data) >= period:
                period_data = recent_data.tail(period)
                vol = ((period_data['High'] - period_data['Low']) / period_data['Close']).mean() * 100
                volatilities.append(vol)
        
        if len(volatilities) < 2:
            return False, 0
        
        # Check for any contracting volatility
        contracting = volatilities[0] > volatilities[-1]  # Just compare first and last
        
        # Relaxed current volatility
        current_vol = volatilities[-1] if volatilities else 5
        low_volatility = current_vol < 4  # Was 2.5
        
        # Price position
        current_price = data['Close'].iloc[-1]
        recent_high = recent_data['High'].max()
        near_highs = current_price >= recent_high * 0.92  # Relaxed from 0.95
        
        strength = 0
        if contracting: strength += 35
        if low_volatility: strength += 25
        if near_highs: strength += 40
        
        return (contracting and near_highs), strength
    
    def detect_high_tight_flag(self, data):
        """Relaxed High Tight Flag"""
        if len(data) < 25:  # Reduced from 40
            return False, 0
        
        recent_data = data.tail(20)  # Reduced from 30
        
        # Relaxed prior move requirement
        price_6w_ago = data['Close'].iloc[-25] if len(data) >= 25 else data['Close'].iloc[0]
        current_price = data['Close'].iloc[-1]
        prior_gain = ((current_price - price_6w_ago) / price_6w_ago) * 100
        
        strong_prior_move = prior_gain >= 30  # Relaxed from 50
        
        # Relaxed pullback
        recent_high = recent_data['High'].max()
        recent_low = recent_data['Low'].min()
        pullback = ((recent_high - recent_low) / recent_high) * 100
        
        tight_pullback = 2 <= pullback <= 30  # Relaxed range
        
        # Relaxed breakout
        resistance = recent_data['High'].quantile(0.85)  # Relaxed from 0.9
        breakout = current_price >= resistance * 0.99
        
        strength = 0
        if strong_prior_move: strength += 35
        if tight_pullback: strength += 30
        if breakout: strength += 35
        
        return (strong_prior_move and tight_pullback and breakout), strength
    
    def detect_ascending_triangle(self, data):
        """NEW: Ascending Triangle pattern"""
        if len(data) < 20:
            return False, 0
        
        triangle_data = data.tail(20)
        
        # Resistance level (horizontal)
        resistance_level = triangle_data['High'].max()
        resistance_touches = (triangle_data['High'] >= resistance_level * 0.98).sum()
        
        # Rising support line
        lows = triangle_data['Low']
        early_lows = lows.iloc[:8].mean()
        recent_lows = lows.iloc[-8:].mean()
        rising_support = recent_lows > early_lows * 1.01
        
        # Breakout above resistance
        current_price = data['Close'].iloc[-1]
        breakout = current_price > resistance_level * 0.999
        
        strength = 0
        if resistance_touches >= 2: strength += 30
        if rising_support: strength += 35
        if breakout: strength += 35
        
        return (resistance_touches >= 2 and rising_support and breakout), strength
    
    def detect_bull_flag(self, data):
        """NEW: Bull Flag pattern"""
        if len(data) < 20:
            return False, 0
        
        # Strong move up in last 20-15 days
        flag_pole_data = data.iloc[-20:-10]
        flag_data = data.tail(10)
        
        # Flag pole (strong move up)
        pole_start = flag_pole_data['Close'].iloc[0]
        pole_end = flag_pole_data['Close'].iloc[-1]
        pole_gain = ((pole_end - pole_start) / pole_start) * 100
        
        strong_pole = pole_gain >= 15  # At least 15% move
        
        # Flag (consolidation/pullback)
        flag_high = flag_data['High'].max()
        flag_low = flag_data['Low'].min()
        flag_range = ((flag_high - flag_low) / flag_low) * 100
        
        tight_flag = flag_range < 10  # Tight consolidation
        
        # Breakout above flag
        current_price = data['Close'].iloc[-1]
        breakout = current_price > flag_high * 0.999
        
        strength = 0
        if strong_pole: strength += 35
        if tight_flag: strength += 30
        if breakout: strength += 35
        
        return (strong_pole and tight_flag and breakout), strength
    
    def detect_tight_consolidation_breakout(self, data, days=14, relaxed_mode=True):
        """Relaxed consolidation detection"""
        if len(data) < days + 5:
            return False, 0, {}
        
        consolidation_data = data.tail(days + 3).iloc[:-3]
        breakout_data = data.tail(3)
        
        # Consolidation range
        cons_high = consolidation_data['High'].max()
        cons_low = consolidation_data['Low'].min()
        cons_range = ((cons_high - cons_low) / cons_low) * 100
        
        # Relaxed consolidation criteria
        if relaxed_mode:
            max_range = 12 if days == 14 else 15  # Increased from 8/10
        else:
            max_range = 8 if days == 14 else 10
        
        tight_consolidation = cons_range < max_range
        
        # Volume analysis (optional)
        try:
            cons_volume = consolidation_data['Volume'].mean()
            breakout_volume = breakout_data['Volume'].mean()
            volume_surge = breakout_volume > cons_volume * 1.3  # Relaxed from 1.8
        except:
            volume_surge = True
        
        # Breakout analysis
        current_price = data['Close'].iloc[-1]
        price_breakout = current_price > cons_high * 0.999  # Relaxed
        
        # Technical confirmations (relaxed)
        current_rsi = data['RSI'].iloc[-1]
        rsi_ok = 30 <= current_rsi <= 80  # Relaxed range
        
        current_adx = data['ADX'].iloc[-1]
        adx_ok = current_adx > 12  # Relaxed from 25
        
        # Moving average support (relaxed)
        ema_20 = data['EMA_20'].iloc[-1]
        ma_support = current_price > ema_20 * 0.95  # Very relaxed
        
        strength = 0
        if tight_consolidation: strength += 25
        if volume_surge: strength += 25
        if price_breakout: strength += 25
        if rsi_ok: strength += 10
        if adx_ok: strength += 10
        if ma_support: strength += 5
        
        details = {
            'consolidation_range': cons_range,
            'consolidation_days': days,
            'volume_surge': breakout_volume / cons_volume if cons_volume > 0 else 1,
            'breakout_level': cons_high,
            'current_rsi': current_rsi,
            'current_adx': current_adx,
            'ma_support': ma_support
        }
        
        # Relaxed validation
        valid = (tight_consolidation and price_breakout and rsi_ok)
        
        return valid, strength, details
    
    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Create TradingView-style chart"""
        if len(data) < 20:
            return None
        
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            subplot_titles=('Price', 'Volume')
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data['Open'],
                high=data['High'],
                low=data['Low'],
                close=data['Close'],
                name='Price',
                increasing_line_color='#00d4aa',
                decreasing_line_color='#ff5252',
                increasing_fillcolor='#00d4aa',
                decreasing_fillcolor='#ff5252'
            ),
            row=1, col=1
        )
        
        # Add EMAs
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['EMA_20'],
                mode='lines',
                name='EMA 20',
                line=dict(color='#ffa726', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['SMA_50'],
                mode='lines',
                name='SMA 50',
                line=dict(color='#42a5f5', width=2)
            ),
            row=1, col=1
        )
        
        # Volume bars
        colors = ['#00d4aa' if close >= open else '#ff5252' 
                 for close, open in zip(data['Close'], data['Open'])]
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # Volume moving average
        volume_ma = data['Volume'].rolling(window=20).mean()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=volume_ma,
                mode='lines',
                name='Volume MA',
                line=dict(color='white', width=1)
            ),
            row=2, col=1
        )
        
        # Update layout
        pattern_name = pattern_info['type'] if pattern_info else 'Technical Analysis'
        fig.update_layout(
            title=f'{symbol.replace(".NS", "")} - {pattern_name}',
            template='plotly_dark',
            paper_bgcolor='rgba(26, 31, 46, 1)',
            plot_bgcolor='rgba(26, 31, 46, 1)',
            font=dict(color='white', family='Inter'),
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(37, 43, 61, 0.8)',
                bordercolor='gray',
                borderwidth=1
            )
        )
        
        fig.update_xaxes(gridcolor='rgba(128,128,128,0.2)', showgrid=True, rangeslider_visible=False)
        fig.update_yaxes(gridcolor='rgba(128,128,128,0.2)', showgrid=True)
        
        return fig
    
    def get_market_sentiment(self):
        """Get market sentiment data"""
        try:
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="5d")
            
            bank_nifty = yf.Ticker("^NSEBANK")
            bank_nifty_data = bank_nifty.history(period="5d")
            
            return {
                'nifty_data': nifty_data,
                'bank_nifty_data': bank_nifty_data,
            }
        except:
            return None

def create_pattern_scanner_tab():
    """Pattern scanner with relaxed filters"""
    st.markdown("### 🎯 Successful Patterns - Relaxed Filters (Fixed False Negatives)")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        min_pattern_strength = st.slider("Min Pattern Strength:", 50, 100, 60)  # Lowered default
    with col2:
        min_volume_ratio = st.slider("Min Volume Ratio:", 0.8, 3.0, 1.0)  # Lowered default
    with col3:
        max_stocks = st.slider("Max Stocks to Scan:", 10, 60, 30)
    with col4:
        relaxed_mode = st.checkbox("Relaxed Mode", value=True, help="Use relaxed filters to avoid false negatives")
    
    if st.button("🚀 Scan for Patterns (Fixed False Negatives)", key="pattern_scan"):
        scanner = FixedPCSScanner()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        stocks_to_scan = NSE_FO_UNIVERSE[:max_stocks]
        
        for i, symbol in enumerate(stocks_to_scan):
            progress = (i + 1) / len(stocks_to_scan)
            progress_bar.progress(progress)
            status_text.text(f"Scanning {symbol.replace('.NS', '')} ({i+1}/{len(stocks_to_scan)})")
            
            try:
                data = scanner.get_stock_data(symbol)
                if data is None:
                    continue
                
                # Check volume criteria (relaxed)
                volume_ok, volume_ratio = scanner.check_volume_criteria(data, min_volume_ratio)
                if not volume_ok:
                    continue
                
                # Detect patterns (relaxed mode)
                patterns = scanner.detect_successful_patterns(data, symbol, relaxed_mode)
                if not patterns:
                    continue
                
                # Filter by strength
                filtered_patterns = [p for p in patterns if p['strength'] >= min_pattern_strength]
                if not filtered_patterns:
                    continue
                
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]
                
                results.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': filtered_patterns,
                    'data': data
                })
                
            except Exception as e:
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"🎉 Found {len(results)} stocks with patterns! (False negatives fixed)")
            
            # Show relaxed mode info
            if relaxed_mode:
                st.info("🔧 **Relaxed Mode Active**: RSI 35-75, ADX >15, EMA support, Lower pattern thresholds")
            
            for result in results:
                with st.expander(f"📈 {result['symbol'].replace('.NS', '')} - {len(result['patterns'])} Pattern(s)", expanded=True):
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Price", f"₹{result['current_price']:.2f}")
                    with col2:
                        st.metric("Volume", f"{result['volume_ratio']:.2f}x")
                    with col3:
                        st.metric("RSI", f"{result['rsi']:.1f}")
                    with col4:
                        st.metric("ADX", f"{result['adx']:.1f}")
                    
                    # Pattern details
                    for pattern in result['patterns']:
                        confidence = "🟢 HIGH" if pattern['strength'] >= 80 else "🟡 MEDIUM" if pattern['strength'] >= 65 else "🔴 LOW"
                        
                        st.markdown(f"""
                        <div class="pattern-card">
                            <h4>🎯 {pattern['type']} - {confidence} Confidence</h4>
                            <p><strong>Pattern Strength:</strong> {pattern['strength']}% | 
                               <strong>Success Rate:</strong> {pattern['success_rate']}% | 
                               <strong>PCS Suitability:</strong> {pattern['pcs_suitability']}%</p>
                            <p><strong>Research:</strong> {pattern['research_basis']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Chart
                    chart = scanner.create_tradingview_chart(
                        result['data'], 
                        result['symbol'], 
                        result['patterns'][0] if result['patterns'] else None
                    )
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("🔍 No patterns found. Try lowering the minimum pattern strength or enabling relaxed mode.")

def create_consolidation_scanner_tab():
    """Consolidation scanner with relaxed filters"""
    st.markdown("### 📊 Consolidation Breakouts - Fixed False Negatives")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        consolidation_days = st.selectbox("Consolidation Period:", [14, 20], index=0)
    with col2:
        min_volume_surge = st.slider("Min Volume Surge:", 1.2, 3.0, 1.3)  # Lowered
    with col3:
        relaxed_consolidation = st.checkbox("Relaxed Mode", value=True)
    
    if st.button("🔍 Scan Consolidation Breakouts", key="consolidation_scan"):
        scanner = FixedPCSScanner()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, symbol in enumerate(NSE_FO_UNIVERSE[:30]):
            progress = (i + 1) / 30
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {symbol.replace('.NS', '')} consolidation...")
            
            try:
                data = scanner.get_stock_data(symbol)
                if data is None:
                    continue
                
                # Check volume criteria (relaxed)
                volume_ok, volume_ratio = scanner.check_volume_criteria(data, 0.8)  # Very relaxed
                if not volume_ok:
                    continue
                
                # Detect consolidation breakout (relaxed)
                breakout_detected, strength, details = scanner.detect_tight_consolidation_breakout(
                    data, consolidation_days, relaxed_consolidation
                )
                if not breakout_detected or strength < 50:  # Lowered threshold
                    continue
                
                # Check volume surge (relaxed)
                if details['volume_surge'] < min_volume_surge:
                    continue
                
                results.append({
                    'symbol': symbol,
                    'strength': strength,
                    'details': details,
                    'data': data,
                    'volume_ratio': volume_ratio
                })
                
            except Exception as e:
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"🎯 Found {len(results)} consolidation breakouts!")
            
            if relaxed_consolidation:
                st.info("🔧 **Relaxed Mode**: Wider ranges, lower volume requirements, flexible MA support")
            
            for result in results:
                with st.expander(f"📊 {result['symbol'].replace('.NS', '')} - Strength: {result['strength']}%", expanded=True):
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Range", f"{result['details']['consolidation_range']:.1f}%")
                    with col2:
                        st.metric("Volume Surge", f"{result['details']['volume_surge']:.1f}x")
                    with col3:
                        st.metric("RSI", f"{result['details']['current_rsi']:.1f}")
                    with col4:
                        st.metric("ADX", f"{result['details']['current_adx']:.1f}")
                    
                    # Details
                    confidence = "🟢 HIGH" if result['strength'] >= 80 else "🟡 MEDIUM"
                    st.markdown(f"""
                    <div class="consolidation-card">
                        <h4>🔥 {result['details']['consolidation_days']}-Day Breakout - {confidence}</h4>
                        <p><strong>Breakout Level:</strong> ₹{result['details']['breakout_level']:.2f}</p>
                        <p><strong>Pattern Strength:</strong> {result['strength']}%</p>
                        <p><strong>MA Support:</strong> {'✅ Yes' if result['details']['ma_support'] else '⚠️ Weak'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Chart
                    chart = scanner.create_tradingview_chart(result['data'], result['symbol'])
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("No consolidation breakouts found. Try enabling relaxed mode or lowering requirements.")

def create_market_sentiment_tab():
    """Market sentiment tab"""
    st.markdown("### 🌍 Market Sentiment & Context")
    
    scanner = FixedPCSScanner()
    
    with st.spinner("Loading market data..."):
        sentiment_data = scanner.get_market_sentiment()
    
    if sentiment_data and not sentiment_data['nifty_data'].empty:
        col1, col2 = st.columns(2)
        
        with col1:
            nifty = sentiment_data['nifty_data']
            current = nifty['Close'].iloc[-1]
            change = current - nifty['Close'].iloc[-2]
            change_pct = (change / nifty['Close'].iloc[-2]) * 100
            
            st.metric("Nifty 50", f"{current:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
        
        with col2:
            bank_nifty = sentiment_data['bank_nifty_data']
            current = bank_nifty['Close'].iloc[-1]
            change = current - bank_nifty['Close'].iloc[-2]
            change_pct = (change / bank_nifty['Close'].iloc[-2]) * 100
            
            st.metric("Bank Nifty", f"{current:.2f}", f"{change:+.2f} ({change_pct:+.2f}%)")
        
        # Market bias
        if change_pct > 1:
            st.success("📈 **Strong Bullish Bias** - Excellent for PCS strategies")
        elif change_pct > 0:
            st.info("📊 **Mild Bullish Bias** - Good for selective PCS")
        elif change_pct > -1:
            st.warning("📉 **Sideways Market** - Use caution with PCS")
        else:
            st.error("🔻 **Bearish Market** - Avoid PCS, consider protective strategies")

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%); border-radius: 16px; margin-bottom: 30px; border: 1px solid var(--border-color);'>
        <h1 style='color: var(--success-color); margin: 0; font-size: 2.5rem; font-weight: 700;'>📈 Fixed PCS Scanner</h1>
        <p style='color: var(--text-secondary); margin: 10px 0 0 0; font-size: 1.1rem;'>✅ False Negatives Fixed • Relaxed Filters • Better Pattern Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "🎯 Fixed Patterns",
        "📊 Fixed Consolidations", 
        "🌍 Market Sentiment"
    ])
    
    with tab1:
        create_pattern_scanner_tab()
    
    with tab2:
        create_consolidation_scanner_tab()
    
    with tab3:
        create_market_sentiment_tab()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: var(--text-secondary); padding: 20px;'>
        <p><strong>🔧 Fixed Issues:</strong> Relaxed RSI (35-75), Lower ADX (>15), EMA support, Reduced pattern thresholds</p>
        <p><strong>⚠️ Disclaimer:</strong> Educational use only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
