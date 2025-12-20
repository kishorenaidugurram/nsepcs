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
import json
from bs4 import BeautifulSoup
import re
from io import BytesIO
import openpyxl
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="NSE F&O Options Strategy Scanner", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# PROFESSIONAL UI SYSTEM - Dynamic Theme Based on Strategy
def get_theme_css(strategy_type):
    """Get CSS theme based on strategy type"""
    if strategy_type == "Put Credit Spreads":
        primary_hue = "174"  # Teal
        primary_name = "teal"
        icon = "📈"
    else:  # Call Credit Spreads
        primary_hue = "0"    # Red
        primary_name = "red"
        icon = "📉"
    
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        /* === DYNAMIC THEME SYSTEM === */
        --primary-50: hsl({primary_hue}, 62%, 98%);
        --primary-100: hsl({primary_hue}, 62%, 95%);
        --primary-200: hsl({primary_hue}, 62%, 90%);
        --primary-300: hsl({primary_hue}, 62%, 75%);
        --primary-400: hsl({primary_hue}, 62%, 60%);
        --primary-500: hsl({primary_hue}, 62%, 47%);
        --primary-600: hsl({primary_hue}, 62%, 40%);
        --primary-700: hsl({primary_hue}, 62%, 33%);
        --primary-800: hsl({primary_hue}, 62%, 27%);
        --primary-900: hsl({primary_hue}, 62%, 20%);
        
        /* Neutral Palette */
        --neutral-50: hsl(210, 20%, 98%);
        --neutral-100: hsl(210, 20%, 96%);
        --neutral-200: hsl(210, 16%, 93%);
        --neutral-300: hsl(210, 14%, 89%);
        --neutral-400: hsl(210, 12%, 71%);
        --neutral-500: hsl(210, 10%, 53%);
        --neutral-600: hsl(210, 12%, 43%);
        --neutral-700: hsl(210, 15%, 33%);
        --neutral-800: hsl(210, 18%, 23%);
        --neutral-900: hsl(210, 20%, 15%);
        
        /* Semantic Colors */
        --success-bg: hsl(142, 76%, 96%);
        --success-text: hsl(142, 76%, 30%);
        --warning-bg: hsl(38, 92%, 95%);
        --warning-text: hsl(38, 92%, 35%);
        --error-bg: hsl(0, 86%, 97%);
        --error-text: hsl(0, 86%, 40%);
        
        /* Background System */
        --background: hsl(210, 20%, 98%);
        --surface: hsl(0, 0%, 100%);
        --border: hsl(210, 14%, 89%);
        --text-primary: hsl(210, 20%, 15%);
        --text-secondary: hsl(210, 12%, 43%);
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    }}
    
    /* Global Styles */
    * {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    
    .main {{
        background: var(--background);
        padding: 1.5rem 2rem;
    }}
    
    /* Headers */
    h1, h2, h3 {{
        color: var(--text-primary);
        font-weight: 700;
        line-height: 1.2;
    }}
    
    h1 {{
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--primary-50) 0%, var(--primary-100) 100%);
        border-right: 1px solid var(--primary-300);
        box-shadow: var(--shadow-md);
    }}
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: var(--primary-700);
    }}
    
    /* Buttons */
    .stButton > button {{
        background: var(--primary-600);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }}
    
    .stButton > button:hover {{
        background: var(--primary-700);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}
    
    /* Cards */
    .metric-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 1rem;
        padding: 1.5rem;
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    
    .metric-card:hover {{
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }}
    
    .pattern-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }}
    
    .pattern-card:hover {{
        box-shadow: var(--shadow-md);
        border-color: var(--primary-500);
    }}
    
    /* Professional Header */
    .professional-header {{
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, var(--primary-50), var(--neutral-50));
        border-radius: 1rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border);
    }}
    
    .strategy-badge {{
        background: var(--primary-600);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-size: 0.875rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 1rem;
    }}
    
    /* Status Indicators */
    .status-success {{
        background: var(--success-bg);
        color: var(--success-text);
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }}
    
    .status-warning {{
        background: var(--warning-bg);
        color: var(--warning-text);
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }}
    
    .status-error {{
        background: var(--error-bg);
        color: var(--error-text);
        padding: 0.25rem 0.75rem;
        border-radius: 0.5rem;
        font-weight: 600;
    }}
    
    /* Responsive Design */
    @media (max-width: 768px) {{
        .main {{ padding: 1rem; }}
        .professional-header {{ padding: 1.5rem 1rem; }}
    }}
</style>
""", icon

# CACHING SYSTEM FOR PERFORMANCE OPTIMIZATION
@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def get_nse_fno_stocks_cached():
    """Cached NSE F&O stock list retrieval"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get main NSE page first
        session.get('https://www.nseindia.com/', timeout=10)
        
        response = session.get('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500', timeout=15)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            stocks = [item['symbol'] + '.NS' for item in data if 'symbol' in item][:219]
            return stocks
            
    except Exception as e:
        st.warning(f"API fetch failed, using backup list: {str(e)}")
    
    # Comprehensive backup list
    return [
        '3MINDIA.NS', 'ABB.NS', 'ACC.NS', 'AIAENG.NS', 'APLAPOLLO.NS', 'AUBANK.NS',
        'AAVAS.NS', 'ABBOTINDIA.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'AJANTPHARM.NS',
        'APOLLOHOSP.NS', 'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS',
        'ATUL.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS',
        'BAJFINANCE.NS', 'BALKRISIND.NS', 'BALRAMCHIN.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS',
        'BATAINDIA.NS', 'BEL.NS', 'BERGEPAINT.NS', 'BHARATFORG.NS', 'BHARTIARTL.NS',
        'BHEL.NS', 'BIOCON.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS',
        'BSOFT.NS', 'CANFINHOME.NS', 'CANBK.NS', 'CHOLAFIN.NS', 'CIPLA.NS',
        'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS',
        'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 'DABUR.NS', 'DALBHARAT.NS',
        'DEEPAKNTR.NS', 'DIVISLAB.NS', 'DLF.NS', 'DRREDDY.NS', 'EICHERMOT.NS',
        'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'GAIL.NS', 'GLENMARK.NS',
        'GMRINFRA.NS', 'GNFC.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRANULES.NS',
        'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS',
        'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
        'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS',
        'ICICIPRULI.NS', 'IDEA.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS',
        'INDHOTEL.NS', 'INDIACEM.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS',
        'INDUSTOWER.NS', 'INFY.NS', 'IOC.NS', 'IPCALAB.NS', 'IRB.NS',
        'IRCTC.NS', 'ITC.NS', 'JINDALSTEL.NS', 'JKCEMENT.NS', 'JSWSTEEL.NS',
        'JUBLFOOD.NS', 'KOTAKBANK.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS',
        'LT.NS', 'LTIM.NS', 'LTTS.NS', 'LUPIN.NS', 'M&M.NS',
        'M&MFIN.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MARUTI.NS', 'MCX.NS',
        'METROPOLIS.NS', 'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS',
        'MUTHOOTFIN.NS', 'NATIONALUM.NS', 'NAUKRI.NS', 'NAVINFLUOR.NS', 'NESTLEIND.NS',
        'NMDC.NS', 'NTPC.NS', 'OBEROIRLTY.NS', 'OFSS.NS', 'ONGC.NS',
        'PAGEIND.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS',
        'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 'POLYCAB.NS', 'POWERGRID.NS',
        'RAMCOCEM.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RELIANCE.NS', 'SAIL.NS',
        'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SIEMENS.NS',
        'SRF.NS', 'SUNPHARMA.NS', 'SUNTV.NS', 'SUPREMEIND.NS', 'SYNGENE.NS',
        'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS',
        'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 'TORNTPHARM.NS',
        'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS', 'ULTRACEMCO.NS', 'UPL.NS',
        'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS'
    ]

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_stock_data_cached(symbol, period="3mo"):
    """Cached stock data retrieval with technical indicators"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        
        if data.empty or len(data) < 30:
            return None
            
        # Ensure volume data exists
        if 'Volume' not in data.columns or data['Volume'].isna().all():
            return None
            
        # Add technical indicators
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
        data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
        data['EMA_12'] = ta.trend.ema_indicator(data['Close'], window=12)
        data['EMA_26'] = ta.trend.ema_indicator(data['Close'], window=26)
        data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
        data['MACD'] = ta.trend.macd_diff(data['Close'])
        data['BB_upper'] = ta.volatility.bollinger_hband(data['Close'])
        data['BB_lower'] = ta.volatility.bollinger_lband(data['Close'])
        data['Volume_SMA'] = ta.trend.sma_indicator(data['Volume'], window=20)
        
        return data
        
    except Exception:
        return None

@st.cache_data(ttl=900, show_spinner=False)  # Cache for 15 minutes
def get_weekly_stock_data_cached(symbol, period="6mo"):
    """Cached weekly stock data for trend analysis"""
    try:
        ticker = yf.Ticker(symbol)
        daily_data = ticker.history(period=period)
        
        if daily_data.empty:
            return None
        
        # Resample to weekly
        weekly_data = daily_data.resample('W').agg({
            'Open': 'first',
            'High': 'max', 
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum'
        }).dropna()
        
        if len(weekly_data) < 10:
            return None
        
        # Add weekly indicators
        weekly_data['SMA_10'] = ta.trend.sma_indicator(weekly_data['Close'], window=10)
        weekly_data['SMA_20'] = ta.trend.sma_indicator(weekly_data['Close'], window=20)
        weekly_data['RSI'] = ta.momentum.rsi(weekly_data['Close'], window=14)
        weekly_data['Volume_SMA'] = ta.trend.sma_indicator(weekly_data['Volume'], window=10)
        
        return weekly_data
        
    except Exception:
        return None

@st.cache_data(ttl=1800, show_spinner=False)  # Cache for 30 minutes
def get_market_sentiment_cached():
    """Cached market sentiment indicators"""
    sentiment_data = {}
    
    try:
        # Get Nifty 50 data
        nifty = yf.Ticker('^NSEI')
        nifty_data = nifty.history(period='5d')
        
        if not nifty_data.empty and len(nifty_data) >= 2:
            nifty_change = ((nifty_data['Close'].iloc[-1] - nifty_data['Close'].iloc[-2]) / nifty_data['Close'].iloc[-2]) * 100
            sentiment_data['nifty'] = {
                'change_pct': nifty_change,
                'level': nifty_data['Close'].iloc[-1]
            }
        
        # Get Bank Nifty data
        bank_nifty = yf.Ticker('^NSEBANK')
        bank_data = bank_nifty.history(period='5d')
        
        if not bank_data.empty and len(bank_data) >= 2:
            bank_change = ((bank_data['Close'].iloc[-1] - bank_data['Close'].iloc[-2]) / bank_data['Close'].iloc[-2]) * 100
            sentiment_data['bank_nifty'] = {
                'change_pct': bank_change,
                'level': bank_data['Close'].iloc[-1]
            }
        
        return sentiment_data
        
    except Exception:
        return {}

def create_excel_export(results, strategy_type):
    """Create Excel file with results"""
    output = BytesIO()
    strategy_short = "PCS" if strategy_type == "Put Credit Spreads" else "CCS"
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main Results
        df_main = pd.DataFrame([
            {
                'Stock': result['symbol'],
                'Pattern': result['pattern'],
                'Strength': f"{result['strength']}%",
                'Success Rate': f"{result['success_rate']}%",
                f'{strategy_short} Suitability': f"{result['suitability']}%",
                'Volume Ratio': f"{result.get('volume_ratio', 'N/A')}x",
                'Current Price': result.get('current_price', 'N/A')
            }
            for result in results
        ])
        df_main.to_excel(writer, sheet_name=f'{strategy_short}_Opportunities', index=False)
        
        # Pattern Summary
        pattern_counts = {}
        for result in results:
            pattern = result['pattern']
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        df_summary = pd.DataFrame([
            {'Pattern': pattern, 'Count': count}
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        df_summary.to_excel(writer, sheet_name='Pattern_Summary', index=False)
    
    output.seek(0)
    return output

class UniversalOptionsScanner:
    """Universal scanner for both PCS and CCS strategies"""
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_market_sentiment(self, strategy_type):
        """Analyze market sentiment for chosen strategy"""
        sentiment_data = get_market_sentiment_cached()
        
        if not sentiment_data:
            return {
                'overall': {
                    'sentiment': 'UNKNOWN',
                    'recommendation': 'Data unavailable - trade with caution',
                    'risk_level': 'HIGH'
                }
            }
        
        # Calculate sentiment scores
        sentiment_scores = {
            "BEARISH_STRONG": 4 if strategy_type == "Call Credit Spreads" else 0,
            "BEARISH": 3 if strategy_type == "Call Credit Spreads" else 1,
            "NEUTRAL": 2,
            "BULLISH": 1 if strategy_type == "Call Credit Spreads" else 3,
            "BULLISH_STRONG": 0 if strategy_type == "Call Credit Spreads" else 4
        }
        
        # Determine sentiment levels
        def get_sentiment_level(change_pct):
            if change_pct <= -1.5:
                return "BEARISH_STRONG"
            elif change_pct <= -0.5:
                return "BEARISH"
            elif change_pct <= 0.5:
                return "NEUTRAL"
            elif change_pct <= 1.5:
                return "BULLISH"
            else:
                return "BULLISH_STRONG"
        
        nifty_sentiment = "NEUTRAL"
        bank_sentiment = "NEUTRAL"
        
        if 'nifty' in sentiment_data:
            nifty_sentiment = get_sentiment_level(sentiment_data['nifty']['change_pct'])
            sentiment_data['nifty']['sentiment'] = nifty_sentiment
        
        if 'bank_nifty' in sentiment_data:
            bank_sentiment = get_sentiment_level(sentiment_data['bank_nifty']['change_pct'])
            sentiment_data['bank_nifty']['sentiment'] = bank_sentiment
        
        # Overall assessment
        nifty_score = sentiment_scores.get(nifty_sentiment, 2)
        bank_score = sentiment_scores.get(bank_sentiment, 2)
        overall_score = (nifty_score * 0.6) + (bank_score * 0.4)
        
        if overall_score >= 3.2:
            overall_sentiment = "BULLISH" if strategy_type == "Put Credit Spreads" else "BEARISH"
            recommendation = f"Excellent for {strategy_type}"
            risk_level = "LOW"
        elif overall_score >= 2.2:
            overall_sentiment = "NEUTRAL"
            recommendation = f"Moderate {strategy_type.split()[0]} opportunities"
            risk_level = "MEDIUM"
        else:
            overall_sentiment = "BEARISH" if strategy_type == "Put Credit Spreads" else "BULLISH"
            opposite_strategy = "Call Credit Spreads" if strategy_type == "Put Credit Spreads" else "Put Credit Spreads"
            recommendation = f"Avoid {strategy_type.split()[0]}, consider {opposite_strategy}"
            risk_level = "HIGH"
        
        sentiment_data['overall'] = {
            'sentiment': overall_sentiment,
            'score': overall_score,
            'recommendation': recommendation,
            'risk_level': risk_level
        }
        
        return sentiment_data
    
    def detect_patterns(self, data, symbol, strategy_type, filters):
        """Unified pattern detection for both strategies"""
        if data is None or len(data) < 30:
            return []
        
        patterns_found = []
        
        if strategy_type == "Put Credit Spreads":
            # Bullish patterns for PCS
            pattern_methods = [
                ('Cup and Handle', self._detect_cup_and_handle),
                ('Ascending Triangle', self._detect_ascending_triangle),
                ('Bull Flag', self._detect_bull_flag),
                ('Double Bottom', self._detect_double_bottom),
                ('Inverse Head and Shoulders', self._detect_inverse_head_shoulders),
                ('Bullish Engulfing', self._detect_bullish_engulfing),
                ('Morning Star', self._detect_morning_star),
                ('Hammer', self._detect_hammer)
            ]
        else:
            # Bearish patterns for CCS
            pattern_methods = [
                ('Head and Shoulders', self._detect_head_shoulders),
                ('Descending Triangle', self._detect_descending_triangle),
                ('Bear Flag', self._detect_bear_flag),
                ('Double Top', self._detect_double_top),
                ('Rising Wedge', self._detect_rising_wedge),
                ('Bearish Engulfing', self._detect_bearish_engulfing),
                ('Evening Star', self._detect_evening_star),
                ('Shooting Star', self._detect_shooting_star)
            ]
        
        for pattern_name, detect_method in pattern_methods:
            try:
                detected, strength = detect_method(data)
                
                if detected and strength >= filters.get('min_strength', 70):
                    # Volume validation
                    volume_valid, volume_ratio = self._check_volume_criteria(data, filters.get('volume_ratio', 1.0))
                    
                    # Get pattern-specific data
                    pattern_info = self._get_pattern_data(pattern_name, strategy_type)
                    
                    # Breakout/breakdown confirmation
                    direction_confirmed, direction_details = self._detect_current_day_direction(
                        data, strategy_type, filters.get('lookback_days', 20)
                    )
                    
                    final_strength = strength
                    if direction_confirmed:
                        final_strength = min(98, strength + 15)
                    if volume_valid and volume_ratio >= 1.5:
                        final_strength = min(98, final_strength + 10)
                    
                    pattern_result = {
                        'symbol': symbol,
                        'pattern': pattern_name,
                        'strength': final_strength,
                        'success_rate': pattern_info['success_rate'],
                        'suitability': pattern_info['suitability'],
                        'current_price': data['Close'].iloc[-1],
                        'direction_confirmed': direction_confirmed,
                        'volume_confirmed': volume_valid,
                        'volume_ratio': volume_ratio,
                        'direction_details': direction_details,
                        'pattern_details': pattern_info.get('details', {}),
                        'daily_strength': strength
                    }
                    
                    patterns_found.append(pattern_result)
                    
            except Exception:
                continue
        
        return patterns_found
    
    def _detect_current_day_direction(self, data, strategy_type, lookback_days=20):
        """Detect breakout (PCS) or breakdown (CCS) based on strategy"""
        try:
            if len(data) < lookback_days + 5:
                return False, {}
            
            current_close = data['Close'].iloc[-1]
            current_high = data['High'].iloc[-1]
            current_low = data['Low'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            current_open = data['Open'].iloc[-1]
            
            lookback_data = data.iloc[-(lookback_days+1):-1]
            recent_high = lookback_data['High'].max()
            recent_low = lookback_data['Low'].min()
            avg_volume = lookback_data['Volume'].mean()
            
            if strategy_type == "Put Credit Spreads":
                # Look for breakout above resistance
                breakout_occurred = current_high > recent_high * 1.01
                bullish_close = current_close > current_open
                close_strength = ((current_close - current_low) / (current_high - current_low)) * 100 if current_high != current_low else 50
                direction_friendly = close_strength >= 60  # Closed in upper 40% of range
                move_percentage = ((current_high - recent_high) / recent_high) * 100 if breakout_occurred else 0
            else:
                # Look for breakdown below support
                breakout_occurred = current_low < recent_low * 0.99
                bullish_close = current_close < current_open  # Bearish close
                close_strength = ((current_close - current_low) / (current_high - current_low)) * 100 if current_high != current_low else 50
                direction_friendly = close_strength <= 40  # Closed in lower 40% of range
                move_percentage = ((recent_low - current_low) / recent_low) * 100 if breakout_occurred else 0
            
            volume_confirmed = current_volume >= (avg_volume * 1.5)
            
            direction_confirmed = (
                breakout_occurred and
                volume_confirmed and
                (bullish_close if strategy_type == "Put Credit Spreads" else not bullish_close) and
                direction_friendly
            )
            
            details = {
                'breakout_occurred': breakout_occurred,
                'volume_confirmed': volume_confirmed,
                'direction_close': bullish_close if strategy_type == "Put Credit Spreads" else not bullish_close,
                'move_percentage': move_percentage,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                'close_strength': close_strength,
                'recent_level': recent_high if strategy_type == "Put Credit Spreads" else recent_low,
                'current_level': current_high if strategy_type == "Put Credit Spreads" else current_low
            }
            
            return direction_confirmed, details
            
        except Exception:
            return False, {}
    
    def _check_volume_criteria(self, data, min_ratio=1.0):
        """Check volume criteria"""
        try:
            if len(data) < 20:
                return False, 0
            
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume_SMA'].iloc[-1]
            
            if pd.isna(avg_volume) or avg_volume == 0:
                avg_volume = data['Volume'].rolling(20).mean().iloc[-1]
                if pd.isna(avg_volume) or avg_volume == 0:
                    return False, 0
            
            volume_ratio = current_volume / avg_volume
            return volume_ratio >= min_ratio, volume_ratio
            
        except Exception:
            return False, 0
    
    def _get_pattern_data(self, pattern_name, strategy_type):
        """Get pattern data based on strategy type"""
        
        # Pattern database for PCS (bullish patterns)
        pcs_patterns = {
            'Cup and Handle': {'success_rate': 89, 'suitability': 95},
            'Ascending Triangle': {'success_rate': 85, 'suitability': 92},
            'Bull Flag': {'success_rate': 87, 'suitability': 90},
            'Double Bottom': {'success_rate': 82, 'suitability': 88},
            'Inverse Head and Shoulders': {'success_rate': 84, 'suitability': 94},
            'Bullish Engulfing': {'success_rate': 78, 'suitability': 85},
            'Morning Star': {'success_rate': 81, 'suitability': 87},
            'Hammer': {'success_rate': 75, 'suitability': 83}
        }
        
        # Pattern database for CCS (bearish patterns)
        ccs_patterns = {
            'Head and Shoulders': {'success_rate': 85, 'suitability': 98},
            'Descending Triangle': {'success_rate': 81, 'suitability': 93},
            'Bear Flag': {'success_rate': 84, 'suitability': 90},
            'Double Top': {'success_rate': 79, 'suitability': 92},
            'Rising Wedge': {'success_rate': 76, 'suitability': 88},
            'Bearish Engulfing': {'success_rate': 77, 'suitability': 88},
            'Evening Star': {'success_rate': 78, 'suitability': 91},
            'Shooting Star': {'success_rate': 73, 'suitability': 85}
        }
        
        patterns_db = pcs_patterns if strategy_type == "Put Credit Spreads" else ccs_patterns
        
        return patterns_db.get(pattern_name, {'success_rate': 75, 'suitability': 85})
    
    # SIMPLIFIED PATTERN DETECTION METHODS
    def _detect_cup_and_handle(self, data):
        """Simplified cup and handle detection"""
        if len(data) < 30:
            return False, 0
        
        recent_data = data.tail(25)
        
        # Look for U-shaped recovery
        mid_point = len(recent_data) // 2
        early_high = recent_data['High'].iloc[:5].max()
        mid_low = recent_data['Low'].iloc[mid_point-3:mid_point+3].min()
        late_high = recent_data['High'].iloc[-5:].max()
        
        # Cup formation
        cup_depth = ((early_high - mid_low) / early_high) * 100
        if cup_depth < 10 or cup_depth > 40:
            return False, 0
        
        # Handle (small pullback)
        handle_pullback = ((late_high - recent_data['Close'].iloc[-1]) / late_high) * 100
        if handle_pullback > 0 and handle_pullback < 8:
            return True, 88
        
        return False, 0
    
    def _detect_ascending_triangle(self, data):
        """Simplified ascending triangle detection"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        resistance_level = recent_data['High'].max()
        
        # Check if highs are relatively flat (resistance)
        high_variance = recent_data['High'].std() / recent_data['High'].mean()
        flat_resistance = high_variance < 0.02
        
        # Check for rising lows
        early_lows = recent_data['Low'].iloc[:5].mean()
        late_lows = recent_data['Low'].iloc[-5:].mean()
        rising_support = late_lows > early_lows
        
        # Breakout above resistance
        current_price = data['Close'].iloc[-1]
        resistance_broken = current_price > resistance_level * 1.005
        
        if flat_resistance and rising_support and resistance_broken:
            return True, 85
        
        return False, 0
    
    def _detect_bull_flag(self, data):
        """Simplified bull flag detection"""
        if len(data) < 15:
            return False, 0
        
        # Prior bullish move
        price_10_ago = data['Close'].iloc[-11]
        current_price = data['Close'].iloc[-1]
        prior_rally = ((current_price - price_10_ago) / price_10_ago) > 0.02
        
        # Small consolidation (flag)
        recent_data = data.tail(8)
        consolidation_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Low'].min()
        small_range = consolidation_range < 0.05
        
        # Breakout from flag
        flag_high = recent_data['High'].max()
        breakout = current_price > flag_high * 1.005
        
        if prior_rally and small_range and breakout:
            return True, 87
        
        return False, 0
    
    def _detect_double_bottom(self, data):
        """Simplified double bottom detection"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        
        # Find two valleys of similar depth
        valleys = []
        lows = recent_data['Low']
        
        for i in range(1, len(lows)-1):
            if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                valleys.append(lows.iloc[i])
        
        if len(valleys) >= 2:
            first_valley, second_valley = valleys[0], valleys[1]
            
            # Valleys should be similar (within 3%)
            if abs(first_valley - second_valley) / min(first_valley, second_valley) <= 0.03:
                current_price = data['Close'].iloc[-1]
                peak = recent_data['High'].max()
                
                # Check for breakout above peak
                peak_broken = current_price > peak * 1.01
                
                if peak_broken:
                    return True, 83
        
        return False, 0
    
    def _detect_inverse_head_shoulders(self, data):
        """Simplified inverse head and shoulders"""
        if len(data) < 25:
            return False, 0
        
        recent_data = data.tail(20)
        lows = recent_data['Low']
        
        # Find potential shoulders and head
        valleys = []
        for i in range(2, len(lows)-2):
            if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and
                lows.iloc[i] < lows.iloc[i-2] and lows.iloc[i] < lows.iloc[i+2]):
                valleys.append((i, lows.iloc[i]))
        
        if len(valleys) >= 3:
            # Sort by depth (lowest first)
            valleys.sort(key=lambda x: x[1])
            head_idx, head_price = valleys[0]
            
            # Find shoulders
            left_shoulders = [v for v in valleys[1:] if v[0] < head_idx]
            right_shoulders = [v for v in valleys[1:] if v[0] > head_idx]
            
            if left_shoulders and right_shoulders:
                current_price = data['Close'].iloc[-1]
                neckline = recent_data['High'].max()
                
                # Check for neckline break (bullish confirmation)
                neckline_broken = current_price > neckline * 1.02
                
                if neckline_broken:
                    return True, 91
        
        return False, 0
    
    def _detect_bullish_engulfing(self, data):
        """Simplified bullish engulfing pattern"""
        if len(data) < 2:
            return False, 0
        
        candle1 = data.iloc[-2]  # Bearish candle
        candle2 = data.iloc[-1]  # Bullish candle
        
        # First candle: bearish
        bearish_1 = candle1['Close'] < candle1['Open']
        
        # Second candle: bullish and engulfs first
        bullish_2 = candle2['Close'] > candle2['Open']
        engulfs = (candle2['Open'] < candle1['Close'] and 
                  candle2['Close'] > candle1['Open'])
        
        # Volume confirmation
        volume_increase = data['Volume'].iloc[-1] > data['Volume'].iloc[-2]
        
        if bearish_1 and bullish_2 and engulfs:
            strength = 79
            if volume_increase: strength += 6
            return True, min(strength, 85)
        
        return False, 0
    
    def _detect_morning_star(self, data):
        """Simplified morning star pattern"""
        if len(data) < 3:
            return False, 0
        
        candle1 = data.iloc[-3]  # Bearish candle
        candle2 = data.iloc[-2]  # Star (small body)
        candle3 = data.iloc[-1]  # Bullish candle
        
        # First candle: bearish
        bearish_1 = candle1['Close'] < candle1['Open']
        large_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.6
        
        # Second candle: small body (star)
        small_body_2 = abs(candle2['Close'] - candle2['Open']) < (candle2['High'] - candle2['Low']) * 0.3
        
        # Third candle: bullish
        bullish_3 = candle3['Close'] > candle3['Open']
        large_body_3 = abs(candle3['Close'] - candle3['Open']) > (candle3['High'] - candle3['Low']) * 0.6
        
        if bearish_1 and large_body_1 and small_body_2 and bullish_3 and large_body_3:
            return True, 82
        
        return False, 0
    
    def _detect_hammer(self, data):
        """Simplified hammer pattern"""
        if len(data) < 1:
            return False, 0
        
        candle = data.iloc[-1]
        
        # Small body at top of range
        body_size = abs(candle['Close'] - candle['Open'])
        total_range = candle['High'] - candle['Low']
        
        if total_range == 0:
            return False, 0
        
        small_body = body_size < total_range * 0.25
        
        # Long lower shadow
        lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
        long_lower_shadow = lower_shadow > body_size * 2
        
        # Small upper shadow
        upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
        small_upper_shadow = upper_shadow < body_size * 0.5
        
        if small_body and long_lower_shadow and small_upper_shadow:
            return True, 76
        
        return False, 0
    
    # BEARISH PATTERNS FOR CCS
    def _detect_head_shoulders(self, data):
        """Simplified head and shoulders pattern"""
        if len(data) < 25:
            return False, 0
        
        recent_data = data.tail(20)
        highs = recent_data['High']
        
        # Find potential head and shoulders
        peaks = []
        for i in range(2, len(highs)-2):
            if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1] and
                highs.iloc[i] > highs.iloc[i-2] and highs.iloc[i] > highs.iloc[i+2]):
                peaks.append((i, highs.iloc[i]))
        
        if len(peaks) >= 3:
            # Check if middle peak is highest (head)
            peaks.sort(key=lambda x: x[1], reverse=True)
            head_idx, head_price = peaks[0]
            
            # Find left and right shoulders
            left_shoulders = [p for p in peaks[1:] if p[0] < head_idx]
            right_shoulders = [p for p in peaks[1:] if p[0] > head_idx]
            
            if left_shoulders and right_shoulders:
                current_price = data['Close'].iloc[-1]
                neckline = recent_data['Low'].min()
                
                # Check for neckline break (bearish confirmation)
                neckline_broken = current_price < neckline * 1.02
                
                if neckline_broken:
                    return True, 89
        
        return False, 0
    
    def _detect_descending_triangle(self, data):
        """Simplified descending triangle"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        support_level = recent_data['Low'].min()
        
        # Check if lows are relatively flat
        low_variance = recent_data['Low'].std() / recent_data['Low'].mean()
        flat_support = low_variance < 0.02
        
        # Check for declining highs
        early_highs = recent_data['High'].iloc[:5].mean()
        late_highs = recent_data['High'].iloc[-5:].mean()
        declining_resistance = late_highs < early_highs
        
        # Breakdown below support
        current_price = data['Close'].iloc[-1]
        support_broken = current_price < support_level * 0.995
        
        if flat_support and declining_resistance and support_broken:
            return True, 86
        
        return False, 0
    
    def _detect_bear_flag(self, data):
        """Simplified bear flag pattern"""
        if len(data) < 15:
            return False, 0
        
        # Prior bearish move
        price_10_ago = data['Close'].iloc[-11]
        current_price = data['Close'].iloc[-1]
        prior_decline = ((current_price - price_10_ago) / price_10_ago) < -0.02
        
        # Small consolidation (flag)
        recent_data = data.tail(8)
        consolidation_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Low'].min()
        small_range = consolidation_range < 0.05
        
        # Breakdown from flag
        flag_low = recent_data['Low'].min()
        breakdown = current_price < flag_low * 1.005
        
        if prior_decline and small_range and breakdown:
            return True, 84
        
        return False, 0
    
    def _detect_double_top(self, data):
        """Simplified double top pattern"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        
        # Find two peaks of similar height
        peaks = []
        highs = recent_data['High']
        
        for i in range(1, len(highs)-1):
            if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                peaks.append(highs.iloc[i])
        
        if len(peaks) >= 2:
            first_peak, second_peak = peaks[0], peaks[1]
            
            # Peaks should be similar (within 3%)
            if abs(first_peak - second_peak) / max(first_peak, second_peak) <= 0.03:
                current_price = data['Close'].iloc[-1]
                valley = recent_data['Low'].min()
                
                # Check for valley break (bearish)
                valley_broken = current_price < valley * 1.01
                
                if valley_broken:
                    return True, 81
        
        return False, 0
    
    def _detect_rising_wedge(self, data):
        """Simplified rising wedge pattern"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        
        # Check for converging trend lines with upward bias
        highs = recent_data['High']
        lows = recent_data['Low']
        
        # Rising wedge: both highs and lows trending up but converging
        recent_high_trend = (highs.iloc[-1] - highs.iloc[-10]) > 0
        recent_low_trend = (lows.iloc[-1] - lows.iloc[-10]) > 0
        
        # Check for breakdown
        current_price = data['Close'].iloc[-1]
        recent_low = recent_data['Low'].min()
        
        breakdown = current_price < recent_low * 1.005
        
        if recent_high_trend and recent_low_trend and breakdown:
            return True, 78
        
        return False, 0
    
    def _detect_bearish_engulfing(self, data):
        """Simplified bearish engulfing pattern"""
        if len(data) < 2:
            return False, 0
        
        candle1 = data.iloc[-2]  # Bullish candle
        candle2 = data.iloc[-1]  # Bearish candle
        
        # First candle: bullish
        bullish_1 = candle1['Close'] > candle1['Open']
        
        # Second candle: bearish and engulfs first
        bearish_2 = candle2['Close'] < candle2['Open']
        engulfs = (candle2['Open'] > candle1['Close'] and 
                  candle2['Close'] < candle1['Open'])
        
        # Volume confirmation
        volume_increase = data['Volume'].iloc[-1] > data['Volume'].iloc[-2]
        
        if bullish_1 and bearish_2 and engulfs:
            strength = 82
            if volume_increase: strength += 5
            return True, min(strength, 87)
        
        return False, 0
    
    def _detect_evening_star(self, data):
        """Simplified evening star pattern"""
        if len(data) < 3:
            return False, 0
        
        candle1 = data.iloc[-3]  # Bullish candle
        candle2 = data.iloc[-2]  # Star (small body)
        candle3 = data.iloc[-1]  # Bearish candle
        
        # First candle: bullish
        bullish_1 = candle1['Close'] > candle1['Open']
        large_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.6
        
        # Second candle: small body (star)
        small_body_2 = abs(candle2['Close'] - candle2['Open']) < (candle2['High'] - candle2['Low']) * 0.3
        
        # Third candle: bearish
        bearish_3 = candle3['Close'] < candle3['Open']
        large_body_3 = abs(candle3['Close'] - candle3['Open']) > (candle3['High'] - candle3['Low']) * 0.6
        
        if bullish_1 and large_body_1 and small_body_2 and bearish_3 and large_body_3:
            return True, 85
        
        return False, 0
    
    def _detect_shooting_star(self, data):
        """Simplified shooting star pattern"""
        if len(data) < 1:
            return False, 0
        
        candle = data.iloc[-1]
        
        # Small body at bottom of range
        body_size = abs(candle['Close'] - candle['Open'])
        total_range = candle['High'] - candle['Low']
        
        if total_range == 0:
            return False, 0
        
        small_body = body_size < total_range * 0.25
        
        # Long upper shadow
        upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
        long_upper_shadow = upper_shadow > body_size * 2
        
        # Small lower shadow
        lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
        small_lower_shadow = lower_shadow < body_size * 0.5
        
        if small_body and long_upper_shadow and small_lower_shadow:
            return True, 77
        
        return False, 0

def scan_stocks_optimized(stocks, filters, strategy_type, include_weekly=True, max_workers=20):
    """Optimized parallel stock scanning with caching"""
    
    scanner = UniversalOptionsScanner()
    all_results = []
    
    def scan_single_stock(symbol):
        """Scan a single stock with caching"""
        try:
            # Get cached daily data
            daily_data = get_stock_data_cached(symbol)
            if daily_data is None or len(daily_data) < 30:
                return []
            
            # Get cached weekly data if requested
            weekly_data = None
            if include_weekly:
                weekly_data = get_weekly_stock_data_cached(symbol)
            
            # Detect patterns
            patterns = scanner.detect_patterns(daily_data, symbol, strategy_type, filters)
            
            # Add weekly validation if available
            if include_weekly and weekly_data is not None:
                for pattern in patterns:
                    # Simple weekly trend check
                    weekly_trend = "Unknown"
                    if len(weekly_data) >= 5:
                        weekly_close_5_ago = weekly_data['Close'].iloc[-5]
                        weekly_close_current = weekly_data['Close'].iloc[-1]
                        weekly_change = ((weekly_close_current - weekly_close_5_ago) / weekly_close_5_ago) * 100
                        
                        if strategy_type == "Put Credit Spreads":
                            if weekly_change > 2:
                                weekly_trend = "Strong Bullish"
                                pattern['strength'] = min(98, pattern['strength'] + 10)
                            elif weekly_change > 0:
                                weekly_trend = "Bullish" 
                                pattern['strength'] = min(98, pattern['strength'] + 5)
                        else:
                            if weekly_change < -2:
                                weekly_trend = "Strong Bearish"
                                pattern['strength'] = min(98, pattern['strength'] + 10)
                            elif weekly_change < 0:
                                weekly_trend = "Bearish"
                                pattern['strength'] = min(98, pattern['strength'] + 5)
                    
                    pattern['weekly_trend'] = weekly_trend
            
            return patterns
            
        except Exception:
            return []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_stock = {executor.submit(scan_single_stock, stock): stock for stock in stocks}
        
        for future in as_completed(future_to_stock):
            try:
                result = future.result(timeout=30)
                if result:
                    all_results.extend(result)
            except Exception:
                continue
    
    return all_results

def create_professional_sidebar():
    """Create optimized sidebar with strategy selection"""
    with st.sidebar:
        # Strategy Selection Header
        st.markdown("""
        <div style='text-align: center; padding: 14px; background: linear-gradient(135deg, #6366f1, #4338ca); border-radius: 8px; margin-bottom: 20px;'>
            <h2 style='color: #FFFFFF; margin: 0; font-weight: 700;'>⚡ Options Strategy Scanner</h2>
            <p style='color: #FFFFFF; margin: 5px 0 0 0; opacity: 0.9; font-size: 0.85rem;'>Professional v7.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        # MAIN STRATEGY SELECTION
        st.markdown("### 🎯 **Strategy Selection**")
        strategy_type = st.radio(
            "Choose your options strategy:",
            ["Put Credit Spreads", "Call Credit Spreads"],
            index=0,
            help="Put Credit Spreads benefit from bullish patterns, Call Credit Spreads from bearish patterns"
        )
        
        # Dynamic strategy info
        if strategy_type == "Put Credit Spreads":
            st.info("📈 **Put Credit Spreads** - Profit from bullish moves and time decay")
        else:
            st.info("📉 **Call Credit Spreads** - Profit from bearish moves and time decay")
        
        st.markdown("---")
        
        # SCAN CONFIGURATION
        st.markdown("### ⚙️ **Scan Configuration**")
        
        # Minimum strength filter
        min_strength = st.slider(
            "Minimum Pattern Strength (%)",
            min_value=60,
            max_value=95,
            value=75,
            step=5,
            help="Filter patterns by minimum strength threshold"
        )
        
        # Volume criteria
        min_volume_ratio = st.slider(
            "Minimum Volume Ratio",
            min_value=1.0,
            max_value=3.0,
            value=1.5,
            step=0.1,
            help="Current volume vs 20-day average"
        )
        
        # Analysis mode
        st.markdown("**Analysis Mode:**")
        analysis_mode = st.radio(
            "Choose analysis depth:",
            ["Daily Only (Fast)", "Daily + Weekly (Comprehensive)"],
            index=1,
            help="Weekly analysis provides better confirmation but takes longer"
        )
        
        # Advanced settings in expander
        with st.expander("🔧 Advanced Settings", expanded=False):
            lookback_days = st.slider(
                "Lookback Period (Days)",
                min_value=10,
                max_value=30,
                value=20,
                step=5
            )
            
            max_workers = st.slider(
                "Parallel Workers",
                min_value=10,
                max_value=30,
                value=20,
                step=5,
                help="Higher values = faster scanning but more CPU usage"
            )
        
        # Cache status
        st.markdown("---")
        st.markdown("### 📊 **System Status**")
        
        # Cache info
        cache_info = st.empty()
        stocks_cached = len(get_nse_fno_stocks_cached())
        cache_info.success(f"✅ {stocks_cached} F&O stocks cached")
        
        # Clear cache button
        if st.button("🗑️ Clear Cache", help="Clear all cached data to fetch fresh information"):
            st.cache_data.clear()
            st.success("Cache cleared! Next scan will fetch fresh data.")
            st.rerun()
        
        return {
            'strategy_type': strategy_type,
            'min_strength': min_strength,
            'min_volume_ratio': min_volume_ratio,
            'lookback_days': lookback_days,
            'include_weekly': analysis_mode == "Daily + Weekly (Comprehensive)",
            'max_workers': max_workers,
            'stocks_to_scan': get_nse_fno_stocks_cached()
        }

def create_main_scanner_tab(config):
    """Create optimized main scanner tab"""
    strategy_type = config['strategy_type']
    
    # Dynamic theme application
    theme_css, strategy_icon = get_theme_css(strategy_type)
    st.markdown(theme_css, unsafe_allow_html=True)
    
    # Professional scan controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button(
            f"{strategy_icon} **Start {strategy_type.split()[0]} Scan**", 
            type="primary",
            help=f"Begin comprehensive {strategy_type} pattern analysis"
        )
    
    with col2:
        analysis_type = "Weekly Enhanced" if config['include_weekly'] else "Daily Only"
        st.markdown(f"**Mode:** {analysis_type}")
    
    with col3:
        st.markdown(f"**Stocks:** {len(config['stocks_to_scan'])}")
    
    if scan_button:
        scanner = UniversalOptionsScanner()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        start_time = time.time()
        
        # Create filters dictionary
        filters = {
            'min_strength': config['min_strength'],
            'volume_ratio': config['min_volume_ratio'],
            'lookback_days': config['lookback_days']
        }
        
        status_container.info(f"🔄 Scanning {len(config['stocks_to_scan'])} stocks with {config['max_workers']} parallel workers...")
        progress_bar.progress(5)
        
        # Perform optimized scanning
        try:
            results = scan_stocks_optimized(
                config['stocks_to_scan'], 
                filters,
                strategy_type,
                include_weekly=config['include_weekly'],
                max_workers=config['max_workers']
            )
            
            progress_bar.progress(90)
            status_container.info("🔄 Processing and ranking results...")
            
            # Sort by strength
            results.sort(key=lambda x: x['strength'], reverse=True)
            
            progress_bar.progress(100)
            end_time = time.time()
            scan_duration = end_time - start_time
            
            status_container.success(f"✅ Scan completed in {scan_duration:.1f}s. Found {len(results)} {strategy_type.split()[0]} opportunities!")
            
            if results:
                
                # Summary metrics
                st.markdown(f"### 📈 **{strategy_type} Results Summary**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Opportunities", len(results))
                
                with col2:
                    high_strength = sum(1 for r in results if r['strength'] >= 85)
                    st.metric("High Strength (≥85%)", high_strength)
                
                with col3:
                    direction_confirmed = sum(1 for r in results if r.get('direction_confirmed', False))
                    st.metric("Movement Confirmed", direction_confirmed)
                
                with col4:
                    avg_strength = sum(r['strength'] for r in results) / len(results)
                    st.metric("Average Strength", f"{avg_strength:.1f}%")
                
                # Results tabs
                result_tab1, result_tab2, result_tab3 = st.tabs([
                    "🎯 **Top Opportunities**",
                    "📊 **Complete Analysis**", 
                    "📱 **Export Data**"
                ])
                
                with result_tab1:
                    st.markdown(f"### 🎯 **Premium {strategy_type} Opportunities**")
                    
                    # Show top 10 results
                    top_results = results[:10]
                    
                    for i, pattern in enumerate(top_results, 1):
                        strength_color = "#dc2626" if pattern['strength'] >= 90 else "#ea580c" if pattern['strength'] >= 80 else "#ca8a04"
                        direction_status = "✅ Confirmed" if pattern.get('direction_confirmed', False) else "⏳ Pending"
                        volume_status = "🔊 Strong" if pattern.get('volume_ratio', 0) >= 2.0 else "📈 Moderate"
                        
                        weekly_info = ""
                        if 'weekly_trend' in pattern and pattern['weekly_trend'] != "Unknown":
                            weekly_info = f"""
                            <div style='background: #f0f9ff; border-left: 4px solid #0ea5e9; padding: 8px; margin: 8px 0; border-radius: 4px;'>
                                <strong>📅 Weekly Trend:</strong> {pattern['weekly_trend']}
                            </div>
                            """
                        
                        st.markdown(f"""
                        <div class="pattern-card">
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                                <h3 style='margin: 0; color: var(--primary-700); font-size: 1.4rem;'>#{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']}</h3>
                                <span style='background: {strength_color}; color: white; padding: 6px 12px; border-radius: 20px; font-weight: bold;'>
                                    {pattern['strength']:.0f}%
                                </span>
                            </div>
                            
                            <div style='display: flex; justify-content: space-between; margin: 8px 0; color: #4b5563;'>
                                <span><strong>Price:</strong> ₹{pattern['current_price']:.2f}</span>
                                <span><strong>Movement:</strong> {direction_status}</span>
                                <span><strong>Volume:</strong> {volume_status}</span>
                            </div>
                            
                            <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 12px 0;'>
                                <div style='text-align: center; padding: 8px; background: var(--neutral-50); border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>Success Rate</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: #16a34a;'>{pattern['success_rate']}%</div>
                                </div>
                                <div style='text-align: center; padding: 8px; background: var(--neutral-50); border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>Suitability</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: var(--primary-600);'>{pattern['suitability']}%</div>
                                </div>
                                <div style='text-align: center; padding: 8px; background: var(--neutral-50); border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>Volume Ratio</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: #0891b2;'>{pattern.get('volume_ratio', 0):.1f}x</div>
                                </div>
                            </div>
                            
                            {weekly_info}
                        </div>
                        """, unsafe_allow_html=True)
                
                with result_tab2:
                    st.markdown(f"### 📊 **Complete {strategy_type} Analysis**")
                    
                    # Show all results with details
                    for i, pattern in enumerate(results, 1):
                        with st.expander(f"#{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']} ({pattern['strength']:.0f}%)", expanded=i<=3):
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### Pattern Details")
                                st.write(f"**Symbol:** {pattern['symbol'].replace('.NS', '')}")
                                st.write(f"**Pattern:** {pattern['pattern']}")
                                st.write(f"**Current Price:** ₹{pattern['current_price']:.2f}")
                                st.write(f"**Strength:** {pattern['strength']}%")
                                st.write(f"**Success Rate:** {pattern['success_rate']}%")
                                st.write(f"**Suitability:** {pattern['suitability']}%")
                            
                            with col2:
                                st.markdown("#### Movement Analysis")
                                direction_details = pattern.get('direction_details', {})
                                if direction_details:
                                    movement_type = "Breakout" if strategy_type == "Put Credit Spreads" else "Breakdown"
                                    st.write(f"**{movement_type}:** {'✅ Yes' if direction_details.get('breakout_occurred', False) else '❌ No'}")
                                    st.write(f"**Volume Confirmed:** {'✅ Yes' if direction_details.get('volume_confirmed', False) else '❌ No'}")
                                    st.write(f"**Move %:** {direction_details.get('move_percentage', 0):.2f}%")
                                    st.write(f"**Volume Ratio:** {direction_details.get('volume_ratio', 0):.1f}x")
                                
                                # Weekly trend if available
                                if 'weekly_trend' in pattern:
                                    st.write(f"**Weekly Trend:** {pattern['weekly_trend']}")
                
                with result_tab3:
                    st.markdown("### 📱 **Export & Share Results**")
                    
                    # Create Excel export
                    excel_data = create_excel_export(results, strategy_type)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        strategy_short = "PCS" if strategy_type == "Put Credit Spreads" else "CCS"
                        st.download_button(
                            label="📊 **Download Excel Report**",
                            data=excel_data,
                            file_name=f"{strategy_short}_Opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col2:
                        # Pattern distribution
                        pattern_summary = {}
                        for result in results:
                            pattern = result['pattern']
                            pattern_summary[pattern] = pattern_summary.get(pattern, 0) + 1
                        
                        st.markdown("**Pattern Distribution:**")
                        for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"• {pattern}: {count}")
            
            else:
                st.warning(f"🔍 No {strategy_type.split()[0]} patterns found. Try adjusting the filters or check market conditions.")
                
                # Dynamic suggestions
                opposite_strategy = "Call Credit Spreads" if strategy_type == "Put Credit Spreads" else "Put Credit Spreads"
                st.markdown(f"""
                ### 💡 **Suggestions:**
                - Lower the minimum strength threshold
                - Reduce the minimum volume ratio
                - Market conditions might favor **{opposite_strategy}** instead
                - Try scanning during different market hours
                """)
        
        except Exception as e:
            st.error(f"❌ Scanning error: {str(e)}")
            progress_bar.empty()
            status_container.empty()

def main():
    # Get configuration first to determine theme
    config = create_professional_sidebar()
    strategy_type = config['strategy_type']
    
    # Apply dynamic theme
    theme_css, strategy_icon = get_theme_css(strategy_type)
    st.markdown(theme_css, unsafe_allow_html=True)
    
    # Dynamic header
    strategy_color = "#14b8a6" if strategy_type == "Put Credit Spreads" else "#dc2626"
    st.markdown(f"""
    <div class="professional-header">
        <div class="strategy-badge">{strategy_icon} {strategy_type}</div>
        <h1>NSE F&O Options Strategy Scanner</h1>
        <p class="subtitle">Real-time Pattern Analysis • 219 F&O Universe • Professional Trading Insights</p>
        <p class="description">Optimized with caching and parallel processing for maximum performance</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create main tabs
    tab1, tab2 = st.tabs([
        "🎯 Pattern Scanner",
        "📊 Market Intelligence"
    ])
    
    with tab1:
        create_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📊 Market Intelligence Dashboard")
        
        # Get cached market sentiment
        scanner = UniversalOptionsScanner()
        sentiment_data = scanner.analyze_market_sentiment(strategy_type)
        
        # Market Overview
        col1, col2, col3 = st.columns(3)
        
        overall_sentiment = sentiment_data.get('overall', {})
        
        with col1:
            sentiment_level = overall_sentiment.get('sentiment', 'NEUTRAL')
            if strategy_type == "Put Credit Spreads":
                sentiment_emoji = "🟢" if sentiment_level == 'BULLISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🔴"
            else:
                sentiment_emoji = "🔴" if sentiment_level == 'BEARISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🟢"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{sentiment_emoji} Market Sentiment</h3>
                <h2 style="color: var(--primary-600);">{sentiment_level}</h2>
                <p>{overall_sentiment.get('recommendation', 'Moderate opportunities')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            risk_level = overall_sentiment.get('risk_level', 'MEDIUM')
            risk_color = "#16a34a" if risk_level == 'LOW' else "#ea580c" if risk_level == 'MEDIUM' else "#dc2626"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚠️ Risk Level</h3>
                <h2 style="color: {risk_color};">{risk_level}</h2>
                <p>Current {strategy_type.split()[0]} risk assessment</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            is_trading_hours = (9 <= current_time.hour <= 15) and current_time.weekday() < 5
            market_status = "🟢 Active" if is_trading_hours else "🔴 Closed"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>🕐 Market Status</h3>
                <h2 style="color: var(--primary-600);">{market_status}</h2>
                <p>{current_time.strftime('%I:%M %p IST')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed sentiment breakdown
        if 'nifty' in sentiment_data or 'bank_nifty' in sentiment_data:
            st.markdown("### 📈 **Index Analysis**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'nifty' in sentiment_data:
                    nifty = sentiment_data['nifty']
                    st.markdown(f"""
                    **🎯 Nifty 50**
                    - Level: {nifty['level']:.2f}
                    - Change: {nifty['change_pct']:+.2f}%
                    - Sentiment: {nifty.get('sentiment', 'Unknown')}
                    """)
            
            with col2:
                if 'bank_nifty' in sentiment_data:
                    bank = sentiment_data['bank_nifty']
                    st.markdown(f"""
                    **🏦 Bank Nifty**
                    - Level: {bank['level']:.2f}
                    - Change: {bank['change_pct']:+.2f}%
                    - Sentiment: {bank.get('sentiment', 'Unknown')}
                    """)
        
        # Strategy recommendations
        st.markdown(f"### 📋 **{strategy_type} Strategy Guide**")
        
        recommendation = overall_sentiment.get('recommendation', 'Moderate opportunities')
        
        if "Excellent" in recommendation:
            st.success(f"✅ **{recommendation}**")
            if strategy_type == "Put Credit Spreads":
                st.markdown("""
                **Optimal Conditions for Put Credit Spreads:**
                - Bullish market sentiment supports upward moves
                - Look for high-quality bullish reversal patterns
                - Target oversold stocks with strong fundamentals
                - Consider strikes below current support levels
                """)
            else:
                st.markdown("""
                **Optimal Conditions for Call Credit Spreads:**
                - Bearish market sentiment supports downward moves
                - Focus on high-quality bearish reversal patterns
                - Target overbought stocks at resistance levels
                - Consider strikes above current resistance levels
                """)
        
        elif "Moderate" in recommendation:
            st.warning(f"⚠️ **{recommendation}**")
            st.markdown("""
            **Selective Approach Recommended:**
            - Wait for high-strength patterns (>85%)
            - Ensure strong volume confirmation
            - Consider smaller position sizes
            - Monitor market sentiment closely
            """)
        
        else:
            st.error(f"❌ **{recommendation}**")
            opposite = "Put Credit Spreads" if strategy_type == "Call Credit Spreads" else "Call Credit Spreads"
            st.markdown(f"""
            **Current Market Not Favorable:**
            - Consider switching to **{opposite}**
            - Wait for sentiment to improve
            - Focus on risk management
            - Avoid new positions in current strategy
            """)

if __name__ == "__main__":
    main()
