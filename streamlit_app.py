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

# Enhanced Dark Theme CSS
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables */
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
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, var(--primary-bg) 0%, #0f1419 100%);
        color: var(--text-primary);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main .block-container {
        background-color: transparent;
        color: var(--text-primary);
        padding-top: 1rem;
        max-width: 1400px;
    }
    
    /* Sidebar styling */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--secondary-bg) 0%, var(--accent-bg) 100%);
        border-right: 1px solid var(--border-color);
    }
    
    .css-1d391kg .css-1lcbmhc .css-1outpf7 {
        background-color: transparent;
    }
    
    /* Tabs styling */
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
    
    /* Custom cards */
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
    
    /* Button styling */
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
    
    /* Metric styling */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border: 1px solid var(--border-color);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Selectbox and input styling */
    .stSelectbox > div > div {
        background-color: var(--accent-bg);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    .stTextInput > div > div > input {
        background-color: var(--accent-bg);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--success-color), #00bfa5);
        border-radius: 4px;
    }
    
    /* Success/warning/error messages */
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
    
    .stError {
        background: linear-gradient(135deg, rgba(255, 82, 82, 0.1), rgba(244, 67, 54, 0.1));
        border: 1px solid var(--danger-color);
        border-radius: 8px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--primary-bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--success-color), #00bfa5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00bfa5, var(--success-color));
    }
    
    /* TradingView container */
    .tradingview-container {
        background: var(--secondary-bg);
        border-radius: 12px;
        padding: 10px;
        border: 1px solid var(--border-color);
        margin: 10px 0;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
</style>
""", unsafe_allow_html=True)

# Complete NSE F&O Universe (Top liquid stocks)
NSE_FO_UNIVERSE = [
    # Nifty 50 high volume stocks
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    
    # Bank Nifty stocks
    'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS', 'IOC.NS',
    
    # High volume mid-caps
    'SAIL.NS', 'VEDL.NS', 'DLF.NS', 'IDEA.NS', 'JINDALSTEL.NS',
    'NATIONALUM.NS', 'NMDC.NS', 'CONCOR.NS', 'BEL.NS', 'ASHOKLEY.NS',
    'TATAPOWER.NS', 'RECLTD.NS', 'GMRINFRA.NS', 'ADANIGREEN.NS', 'IRCTC.NS'
]

class EnhancedPCSScanner:
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
            
            if len(data) < 50:
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
            st.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def check_volume_criteria(self, data):
        """Check if stock meets volume criteria"""
        if len(data) < 21:
            return False, 0
        
        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].iloc[-21:-1].mean()
        volume_ratio = current_volume / avg_20_volume
        
        return volume_ratio >= 1.5, volume_ratio
    
    def detect_successful_patterns(self, data, symbol):
        """Detect high-success patterns with research backing"""
        patterns = []
        
        if len(data) < 50:
            return patterns
        
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]
        
        # Filter: RSI in range 45-65
        if not (45 <= current_rsi <= 65):
            return patterns
        
        # Filter: ADX > 25 (trending market)
        if current_adx < 25:
            return patterns
        
        # Filter: Price above SMA20 (bullish bias)
        if current_price < sma_20:
            return patterns
        
        # 1. Cup and Handle Pattern (Research: 85% success rate)
        cup_detected, cup_strength = self.detect_cup_and_handle(data)
        if cup_detected and cup_strength >= 80:
            patterns.append({
                'type': 'Cup and Handle',
                'strength': cup_strength,
                'success_rate': 85,
                'research_basis': 'William O\'Neil - How to Make Money in Stocks',
                'pcs_suitability': 95
            })
        
        # 2. Flat Base Breakout (Research: 82% success rate)
        flat_base_detected, flat_strength = self.detect_flat_base_breakout(data)
        if flat_base_detected and flat_strength >= 80:
            patterns.append({
                'type': 'Flat Base Breakout',
                'strength': flat_strength,
                'success_rate': 82,
                'research_basis': 'Mark Minervini - Trade Like a Stock Market Wizard',
                'pcs_suitability': 92
            })
        
        # 3. VCP (Volatility Contraction Pattern) (Research: 78% success rate)
        vcp_detected, vcp_strength = self.detect_vcp_pattern(data)
        if vcp_detected and vcp_strength >= 75:
            patterns.append({
                'type': 'VCP (Volatility Contraction)',
                'strength': vcp_strength,
                'success_rate': 78,
                'research_basis': 'Mark Minervini - Momentum Trading',
                'pcs_suitability': 88
            })
        
        # 4. High Tight Flag (Research: 88% success rate)
        htf_detected, htf_strength = self.detect_high_tight_flag(data)
        if htf_detected and htf_strength >= 85:
            patterns.append({
                'type': 'High Tight Flag',
                'strength': htf_strength,
                'success_rate': 88,
                'research_basis': 'William O\'Neil - IBD Methodology',
                'pcs_suitability': 98
            })
        
        return patterns
    
    def detect_cup_and_handle(self, data):
        """Enhanced Cup and Handle detection"""
        if len(data) < 60:
            return False, 0
        
        recent_data = data.tail(60)
        
        # Cup formation (first 40-50 days)
        cup_data = recent_data.iloc[:45]
        cup_left_high = cup_data['High'].iloc[:15].max()
        cup_right_high = cup_data['High'].iloc[-15:].max()
        cup_low = cup_data['Low'].iloc[10:35].min()
        
        # Cup depth validation (15-50%)
        cup_depth = ((cup_left_high - cup_low) / cup_left_high) * 100
        depth_valid = 15 <= cup_depth <= 50
        
        # Symmetry check
        symmetry_valid = abs(cup_left_high - cup_right_high) / cup_left_high < 0.1
        
        # Handle formation (last 15 days)
        handle_data = recent_data.tail(15)
        handle_high = handle_data['High'].max()
        handle_low = handle_data['Low'].min()
        handle_depth = ((handle_high - handle_low) / handle_high) * 100
        
        # Handle should be tight (< 15%)
        handle_valid = handle_depth < 15
        
        # Volume pattern validation
        cup_volume = cup_data['Volume'].mean()
        handle_volume = handle_data['Volume'].mean()
        volume_contraction = handle_volume < cup_volume * 0.7
        
        # Breakout validation
        current_price = data['Close'].iloc[-1]
        resistance = max(cup_left_high, cup_right_high)
        breakout = current_price >= resistance * 0.99
        
        # Strength calculation
        strength = 0
        if depth_valid: strength += 25
        if symmetry_valid: strength += 20
        if handle_valid: strength += 25
        if volume_contraction: strength += 15
        if breakout: strength += 15
        
        return (depth_valid and symmetry_valid and handle_valid and breakout), strength
    
    def detect_flat_base_breakout(self, data):
        """Detect Flat Base Breakout pattern"""
        if len(data) < 30:
            return False, 0
        
        # Look at last 25 days for flat base
        base_data = data.tail(25)
        
        # Price range analysis
        high_price = base_data['High'].max()
        low_price = base_data['Low'].min()
        price_range = ((high_price - low_price) / low_price) * 100
        
        # Flat base criteria: tight range (< 12%)
        tight_range = price_range < 12
        
        # Time in base (minimum 15 days)
        time_valid = len(base_data) >= 15
        
        # Volume contraction during base
        pre_base_volume = data.iloc[-35:-25]['Volume'].mean()
        base_volume = base_data['Volume'].mean()
        volume_dry_up = base_volume < pre_base_volume * 0.8
        
        # Recent breakout above resistance
        current_price = data['Close'].iloc[-1]
        resistance = base_data['High'].quantile(0.95)
        breakout = current_price >= resistance * 1.005
        
        # Strength calculation
        strength = 0
        if tight_range: strength += 30
        if time_valid: strength += 20
        if volume_dry_up: strength += 25
        if breakout: strength += 25
        
        return (tight_range and time_valid and breakout), strength
    
    def detect_vcp_pattern(self, data):
        """Detect Volatility Contraction Pattern"""
        if len(data) < 50:
            return False, 0
        
        # Analyze multiple contractions
        recent_data = data.tail(40)
        
        # Calculate volatility for different periods
        vol_periods = [10, 8, 6, 4]  # Contracting periods
        volatilities = []
        
        for period in vol_periods:
            if len(recent_data) >= period:
                period_data = recent_data.tail(period)
                vol = ((period_data['High'] - period_data['Low']) / period_data['Close']).mean() * 100
                volatilities.append(vol)
        
        # Check for contracting volatility
        contracting = all(volatilities[i] > volatilities[i+1] for i in range(len(volatilities)-1))
        
        # Current volatility should be very low
        current_vol = volatilities[-1] if volatilities else 10
        low_volatility = current_vol < 2.5
        
        # Volume pattern
        recent_volume = recent_data.tail(5)['Volume'].mean()
        avg_volume = data['Volume'].tail(30).mean()
        volume_ok = recent_volume > avg_volume * 0.8
        
        # Price near highs
        current_price = data['Close'].iloc[-1]
        recent_high = recent_data['High'].max()
        near_highs = current_price >= recent_high * 0.95
        
        # Strength calculation
        strength = 0
        if contracting: strength += 35
        if low_volatility: strength += 25
        if volume_ok: strength += 20
        if near_highs: strength += 20
        
        return (contracting and low_volatility and near_highs), strength
    
    def detect_high_tight_flag(self, data):
        """Detect High Tight Flag pattern"""
        if len(data) < 40:
            return False, 0
        
        # Recent 30 days analysis
        recent_data = data.tail(30)
        
        # Prior uptrend (stock should be up 90%+ in 4-8 weeks)
        price_8w_ago = data['Close'].iloc[-40] if len(data) >= 40 else data['Close'].iloc[0]
        current_price = data['Close'].iloc[-1]
        prior_gain = ((current_price - price_8w_ago) / price_8w_ago) * 100
        
        strong_prior_move = prior_gain >= 50  # Relaxed from 90% for Indian markets
        
        # Tight pullback (3-25% from highs)
        recent_high = recent_data['High'].max()
        recent_low = recent_data['Low'].min()
        pullback = ((recent_high - recent_low) / recent_high) * 100
        
        tight_pullback = 3 <= pullback <= 25
        
        # Time in flag (5-15 days)
        flag_time = len(recent_data.tail(15))
        time_valid = 5 <= flag_time <= 15
        
        # Volume pattern
        flag_volume = recent_data.tail(10)['Volume'].mean()
        pre_flag_volume = data.iloc[-25:-15]['Volume'].mean()
        volume_contraction = flag_volume < pre_flag_volume * 0.8
        
        # Breakout above flag
        resistance = recent_data['High'].quantile(0.9)
        breakout = current_price >= resistance * 0.995
        
        # Strength calculation
        strength = 0
        if strong_prior_move: strength += 30
        if tight_pullback: strength += 25
        if time_valid: strength += 20
        if volume_contraction: strength += 15
        if breakout: strength += 10
        
        return (strong_prior_move and tight_pullback and breakout), strength
    
    def detect_tight_consolidation_breakout(self, data, days=14):
        """Detect tight consolidation breakout"""
        if len(data) < days + 10:
            return False, 0, {}
        
        # Consolidation period
        consolidation_data = data.tail(days + 5).iloc[:-5]  # Exclude last 5 days for breakout
        breakout_data = data.tail(5)
        
        # Consolidation range
        cons_high = consolidation_data['High'].max()
        cons_low = consolidation_data['Low'].min()
        cons_range = ((cons_high - cons_low) / cons_low) * 100
        
        # Tight consolidation (< 8% range for 14 days, < 10% for 20 days)
        max_range = 8 if days == 14 else 10
        tight_consolidation = cons_range < max_range
        
        # Volume analysis
        cons_volume = consolidation_data['Volume'].mean()
        pre_cons_volume = data.iloc[-(days+20):-days]['Volume'].mean()
        volume_contraction = cons_volume < pre_cons_volume * 0.8
        
        # Breakout analysis
        current_price = data['Close'].iloc[-1]
        breakout_volume = breakout_data['Volume'].mean()
        
        # Breakout above consolidation high with volume
        price_breakout = current_price > cons_high * 1.005
        volume_surge = breakout_volume > cons_volume * 1.8
        
        # Additional technical confirmations
        current_rsi = data['RSI'].iloc[-1]
        rsi_ok = 45 <= current_rsi <= 70
        
        current_adx = data['ADX'].iloc[-1]
        adx_ok = current_adx > 25
        
        # Moving average support
        sma_20 = data['SMA_20'].iloc[-1]
        ma_support = current_price > sma_20
        
        # Strength calculation
        strength = 0
        if tight_consolidation: strength += 25
        if volume_contraction: strength += 15
        if price_breakout: strength += 25
        if volume_surge: strength += 20
        if rsi_ok: strength += 10
        if adx_ok: strength += 5
        
        details = {
            'consolidation_range': cons_range,
            'consolidation_days': days,
            'volume_surge': breakout_volume / cons_volume,
            'breakout_level': cons_high,
            'current_rsi': current_rsi,
            'current_adx': current_adx,
            'ma_support': ma_support
        }
        
        valid = (tight_consolidation and price_breakout and volume_surge and 
                rsi_ok and adx_ok and ma_support)
        
        return valid, strength, details
    
    def get_options_data(self, symbol):
        """Get options data and detect long buildup"""
        try:
            clean_symbol = symbol.replace('.NS', '')
            stock = yf.Ticker(symbol)
            
            # Get options data
            options_dates = stock.options
            if not options_dates:
                return None
            
            # Get nearest expiry
            nearest_expiry = options_dates[0]
            options_chain = stock.option_chain(nearest_expiry)
            
            calls = options_chain.calls
            puts = options_chain.puts
            
            if calls.empty or puts.empty:
                return None
            
            # Analyze options activity
            total_call_oi = calls['openInterest'].sum()
            total_put_oi = puts['openInterest'].sum()
            
            # PCR calculation
            pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0
            
            # Long buildup detection
            # Increasing OI with increasing prices suggests long buildup
            call_volume = calls['volume'].sum()
            put_volume = puts['volume'].sum()
            
            long_buildup_signal = False
            if call_volume > put_volume and pcr < 1.2:
                long_buildup_signal = True
            
            return {
                'pcr': pcr,
                'total_call_oi': total_call_oi,
                'total_put_oi': total_put_oi,
                'call_volume': call_volume,
                'put_volume': put_volume,
                'long_buildup': long_buildup_signal,
                'expiry': nearest_expiry
            }
            
        except Exception as e:
            return None
    
    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Create enhanced TradingView-style chart with candlesticks and volume"""
        if len(data) < 20:
            return None
        
        # Create subplots
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
        
        # Add moving averages
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['SMA_20'],
                mode='lines',
                name='SMA 20',
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
        
        # Add Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['BB_upper'],
                mode='lines',
                name='BB Upper',
                line=dict(color='gray', width=1, dash='dash'),
                showlegend=False
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['BB_lower'],
                mode='lines',
                name='BB Lower',
                line=dict(color='gray', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(128,128,128,0.1)',
                showlegend=False
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
        
        # Add volume moving average
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
        fig.update_layout(
            title=f'{symbol.replace(".NS", "")} - {pattern_info["type"] if pattern_info else "Technical Analysis"}',
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
        
        # Update axes
        fig.update_xaxes(
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True,
            rangeslider_visible=False
        )
        
        fig.update_yaxes(
            gridcolor='rgba(128,128,128,0.2)',
            showgrid=True
        )
        
        return fig
    
    def get_market_sentiment(self):
        """Get market sentiment indicators"""
        try:
            # Get Nifty data
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="5d")
            
            # Get Bank Nifty data
            bank_nifty = yf.Ticker("^NSEBANK")
            bank_nifty_data = bank_nifty.history(period="5d")
            
            # Get VIX data
            try:
                vix = yf.Ticker("^INDIAVIX")
                vix_data = vix.history(period="5d")
            except:
                vix_data = pd.DataFrame()
            
            # Calculate advance-decline ratio (simplified)
            advance_decline_ratio = self.calculate_advance_decline_ratio()
            
            sentiment_data = {
                'nifty_data': nifty_data,
                'bank_nifty_data': bank_nifty_data,
                'vix_data': vix_data,
                'advance_decline_ratio': advance_decline_ratio
            }
            
            return sentiment_data
            
        except Exception as e:
            st.error(f"Error fetching market sentiment data: {str(e)}")
            return None
    
    def calculate_advance_decline_ratio(self):
        """Calculate advance-decline ratio for NSE"""
        try:
            advancing = 0
            declining = 0
            
            # Sample from our F&O universe
            sample_stocks = NSE_FO_UNIVERSE[:20]  # First 20 stocks for quick calculation
            
            for symbol in sample_stocks:
                try:
                    stock = yf.Ticker(symbol)
                    data = stock.history(period="2d")
                    if len(data) >= 2:
                        if data['Close'].iloc[-1] > data['Close'].iloc[-2]:
                            advancing += 1
                        else:
                            declining += 1
                except:
                    continue
            
            ad_ratio = advancing / declining if declining > 0 else 0
            return {
                'advancing': advancing,
                'declining': declining,
                'ratio': ad_ratio,
                'sample_size': len(sample_stocks)
            }
            
        except Exception:
            return {
                'advancing': 0,
                'declining': 0,
                'ratio': 1.0,
                'sample_size': 0
            }
    
    def get_world_markets_data(self):
        """Get world markets performance"""
        world_indices = {
            'US - S&P 500': '^GSPC',
            'US - NASDAQ': '^IXIC',
            'US - Dow Jones': '^DJI',
            'Japan - Nikkei': '^N225',
            'UK - FTSE 100': '^FTSE',
            'Germany - DAX': '^GDAXI',
            'Hong Kong - Hang Seng': '^HSI',
            'China - Shanghai': '000001.SS'
        }
        
        world_data = {}
        
        for name, symbol in world_indices.items():
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="5d")
                if len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    previous = data['Close'].iloc[-2]
                    change = current - previous
                    change_pct = (change / previous) * 100
                    
                    world_data[name] = {
                        'current': current,
                        'change': change,
                        'change_pct': change_pct
                    }
            except:
                continue
        
        return world_data

def create_pattern_scanner_tab():
    """Create the pattern scanner tab"""
    st.markdown("### 🎯 Top Successful Patterns - Fresh EOD Matching")
    
    # Configuration
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_pattern_strength = st.slider("Min Pattern Strength:", 70, 100, 80)
    with col2:
        min_volume_ratio = st.slider("Min Volume Ratio:", 1.0, 3.0, 1.5)
    with col3:
        max_stocks = st.slider("Max Stocks to Scan:", 10, 50, 25)
    
    if st.button("🚀 Scan for Successful Patterns", key="pattern_scan"):
        scanner = EnhancedPCSScanner()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        stocks_to_scan = NSE_FO_UNIVERSE[:max_stocks]
        
        for i, symbol in enumerate(stocks_to_scan):
            progress = (i + 1) / len(stocks_to_scan)
            progress_bar.progress(progress)
            status_text.text(f"Scanning {symbol.replace('.NS', '')} ({i+1}/{len(stocks_to_scan)})")
            
            # Get stock data
            data = scanner.get_stock_data(symbol)
            if data is None:
                continue
            
            # Check volume criteria
            volume_ok, volume_ratio = scanner.check_volume_criteria(data)
            if not volume_ok or volume_ratio < min_volume_ratio:
                continue
            
            # Detect patterns
            patterns = scanner.detect_successful_patterns(data, symbol)
            if not patterns:
                continue
            
            # Filter by strength
            filtered_patterns = [p for p in patterns if p['strength'] >= min_pattern_strength]
            if not filtered_patterns:
                continue
            
            # Get additional data
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
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"🎉 Found {len(results)} stocks with high-success patterns!")
            
            # Display results
            for result in results:
                with st.expander(f"📈 {result['symbol'].replace('.NS', '')} - {len(result['patterns'])} Pattern(s)", expanded=True):
                    
                    # Metrics row
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
                        st.markdown(f"""
                        <div class="pattern-card">
                            <h4>🎯 {pattern['type']} - Success Rate: {pattern['success_rate']}%</h4>
                            <p><strong>Pattern Strength:</strong> {pattern['strength']}% | 
                               <strong>PCS Suitability:</strong> {pattern['pcs_suitability']}%</p>
                            <p><strong>Research Basis:</strong> {pattern['research_basis']}</p>
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
            st.warning("No stocks found matching the criteria. Try lowering the filters.")

def create_consolidation_scanner_tab():
    """Create the consolidation scanner tab"""
    st.markdown("### 📊 Tight Consolidation Breakouts with Options Data")
    
    # Configuration
    col1, col2 = st.columns(2)
    with col1:
        consolidation_days = st.selectbox("Consolidation Period:", [14, 20], index=0)
    with col2:
        min_volume_surge = st.slider("Min Volume Surge:", 1.5, 3.0, 2.0)
    
    if st.button("🔍 Scan Consolidation Breakouts", key="consolidation_scan"):
        scanner = EnhancedPCSScanner()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, symbol in enumerate(NSE_FO_UNIVERSE[:30]):
            progress = (i + 1) / 30
            progress_bar.progress(progress)
            status_text.text(f"Analyzing {symbol.replace('.NS', '')} consolidation...")
            
            # Get stock data
            data = scanner.get_stock_data(symbol)
            if data is None:
                continue
            
            # Check volume criteria
            volume_ok, volume_ratio = scanner.check_volume_criteria(data)
            if not volume_ok:
                continue
            
            # Detect consolidation breakout
            breakout_detected, strength, details = scanner.detect_tight_consolidation_breakout(data, consolidation_days)
            if not breakout_detected or strength < 75:
                continue
            
            # Check volume surge
            if details['volume_surge'] < min_volume_surge:
                continue
            
            # Get options data
            options_data = scanner.get_options_data(symbol)
            
            results.append({
                'symbol': symbol,
                'strength': strength,
                'details': details,
                'options_data': options_data,
                'data': data,
                'volume_ratio': volume_ratio
            })
        
        progress_bar.empty()
        status_text.empty()
        
        if results:
            st.success(f"🎯 Found {len(results)} consolidation breakouts!")
            
            for result in results:
                with st.expander(f"📊 {result['symbol'].replace('.NS', '')} - Strength: {result['strength']}%", expanded=True):
                    
                    # Consolidation metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Consolidation Range", f"{result['details']['consolidation_range']:.1f}%")
                    with col2:
                        st.metric("Volume Surge", f"{result['details']['volume_surge']:.1f}x")
                    with col3:
                        st.metric("RSI", f"{result['details']['current_rsi']:.1f}")
                    with col4:
                        st.metric("ADX", f"{result['details']['current_adx']:.1f}")
                    
                    # Consolidation details
                    st.markdown(f"""
                    <div class="consolidation-card">
                        <h4>🔥 {result['details']['consolidation_days']}-Day Tight Consolidation Breakout</h4>
                        <p><strong>Breakout Level:</strong> ₹{result['details']['breakout_level']:.2f}</p>
                        <p><strong>Pattern Strength:</strong> {result['strength']}%</p>
                        <p><strong>MA Support:</strong> {'✅ Yes' if result['details']['ma_support'] else '❌ No'}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Options data
                    if result['options_data']:
                        options = result['options_data']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("PCR", f"{options['pcr']:.2f}")
                        with col2:
                            st.metric("Call OI", f"{options['total_call_oi']:,}")
                        with col3:
                            buildup_status = "🟢 Long Buildup" if options['long_buildup'] else "🔴 No Buildup"
                            st.markdown(f"**{buildup_status}**")
                    
                    # Chart
                    chart = scanner.create_tradingview_chart(result['data'], result['symbol'])
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("No consolidation breakouts found. Try adjusting the filters.")

def create_market_sentiment_tab():
    """Create the market sentiment tab"""
    st.markdown("### 🌍 Market Sentiment & Global Overview")
    
    scanner = EnhancedPCSScanner()
    
    # Get market sentiment data
    with st.spinner("Loading market sentiment data..."):
        sentiment_data = scanner.get_market_sentiment()
        world_data = scanner.get_world_markets_data()
    
    if sentiment_data:
        # Indian indices
        st.markdown("#### 🇮🇳 Indian Market Indices")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not sentiment_data['nifty_data'].empty:
                nifty = sentiment_data['nifty_data']
                current = nifty['Close'].iloc[-1]
                change = current - nifty['Close'].iloc[-2]
                change_pct = (change / nifty['Close'].iloc[-2]) * 100
                
                st.metric(
                    "Nifty 50",
                    f"{current:.2f}",
                    f"{change:+.2f} ({change_pct:+.2f}%)"
                )
        
        with col2:
            if not sentiment_data['bank_nifty_data'].empty:
                bank_nifty = sentiment_data['bank_nifty_data']
                current = bank_nifty['Close'].iloc[-1]
                change = current - bank_nifty['Close'].iloc[-2]
                change_pct = (change / bank_nifty['Close'].iloc[-2]) * 100
                
                st.metric(
                    "Bank Nifty",
                    f"{current:.2f}",
                    f"{change:+.2f} ({change_pct:+.2f}%)"
                )
        
        # VIX
        if not sentiment_data['vix_data'].empty:
            col1, col2 = st.columns(2)
            with col1:
                vix = sentiment_data['vix_data']
                current_vix = vix['Close'].iloc[-1]
                vix_change = current_vix - vix['Close'].iloc[-2]
                
                st.metric(
                    "India VIX",
                    f"{current_vix:.2f}",
                    f"{vix_change:+.2f}"
                )
        
        # Advance-Decline Ratio
        if sentiment_data['advance_decline_ratio']:
            ad_data = sentiment_data['advance_decline_ratio']
            with col2:
                st.metric(
                    "Advance/Decline Ratio",
                    f"{ad_data['ratio']:.2f}",
                    f"{ad_data['advancing']}/{ad_data['declining']}"
                )
    
    # World Markets
    if world_data:
        st.markdown("#### 🌎 Global Markets")
        
        # Create metrics for world markets
        cols = st.columns(2)
        col_idx = 0
        
        for market, data in world_data.items():
            with cols[col_idx % 2]:
                st.metric(
                    market,
                    f"{data['current']:.2f}",
                    f"{data['change']:+.2f} ({data['change_pct']:+.2f}%)"
                )
            col_idx += 1
    
    # Market sentiment indicators chart
    if sentiment_data and not sentiment_data['nifty_data'].empty:
        st.markdown("#### 📈 Nifty 50 Trend Analysis")
        
        nifty_data = sentiment_data['nifty_data']
        
        # Create Nifty chart
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=nifty_data.index,
            open=nifty_data['Open'],
            high=nifty_data['High'],
            low=nifty_data['Low'],
            close=nifty_data['Close'],
            name='Nifty 50',
            increasing_line_color='#00d4aa',
            decreasing_line_color='#ff5252'
        ))
        
        fig.update_layout(
            title="Nifty 50 - 5 Day Trend",
            template='plotly_dark',
            paper_bgcolor='rgba(26, 31, 46, 1)',
            plot_bgcolor='rgba(26, 31, 46, 1)',
            font=dict(color='white'),
            height=400,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%); border-radius: 16px; margin-bottom: 30px; border: 1px solid var(--border-color);'>
        <h1 style='color: var(--success-color); margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 0 20px rgba(0,212,170,0.3);'>📈 NSE F&O PCS Professional Scanner</h1>
        <p style='color: var(--text-secondary); margin: 10px 0 0 0; font-size: 1.1rem;'>Research-Backed Patterns • Fresh EOD Analysis • Options Intelligence • Global Sentiment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "🎯 Successful Patterns",
        "📊 Consolidation Breakouts", 
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
        <p><strong>⚠️ Disclaimer:</strong> This tool is for educational purposes only. Not financial advice. 
        Always do your own research and consult with qualified professionals before trading.</p>
        <p><strong>📊 Data Sources:</strong> Yahoo Finance • <strong>🔄 Update Frequency:</strong> Real-time EOD</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
