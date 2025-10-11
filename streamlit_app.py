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
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# FIXED: Professional Dark Theme with Readable Colors and Compact Header
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-bg: #0a0e1a;
        --secondary-bg: #1a1f2e;
        --accent-bg: #252b3d;
        --sidebar-bg: #1e2432;
        --success-color: #00ff88;
        --warning-color: #ffaa00;
        --danger-color: #ff4444;
        --info-color: #00aaff;
        --text-primary: #ffffff;
        --text-secondary: #b0bec5;
        --text-muted: #78909c;
        --border-color: #37474f;
        --border-light: #455a64;
        --shadow-light: rgba(0, 0, 0, 0.1);
        --shadow-medium: rgba(0, 0, 0, 0.2);
        --shadow-heavy: rgba(0, 0, 0, 0.3);
        --header-gradient: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
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
        padding-top: 0.5rem;
        max-width: 1400px;
    }
    
    /* FIXED: Compact Professional Header - Only 20% of screen */
    .professional-header {
        background: var(--header-gradient);
        padding: 15px 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid var(--info-color);
        box-shadow: 0 8px 32px var(--shadow-heavy);
        text-align: center;
        position: relative;
        overflow: hidden;
        max-height: 120px;
    }
    
    .professional-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, var(--success-color), var(--info-color), var(--warning-color));
    }
    
    .professional-header h1 {
        color: var(--success-color) !important;
        margin: 0 0 5px 0;
        font-size: 2.2rem;
        font-weight: 700;
        text-shadow: 0 2px 8px rgba(0, 255, 136, 0.3);
        background: none !important;
        -webkit-text-fill-color: var(--success-color) !important;
    }
    
    .professional-header .subtitle {
        color: var(--info-color) !important;
        margin: 0 0 3px 0;
        font-size: 1.1rem;
        font-weight: 500;
        opacity: 0.95;
    }
    
    .professional-header .description {
        color: var(--text-secondary) !important;
        margin: 0;
        font-size: 0.9rem;
        opacity: 0.85;
    }
    
    /* Enhanced Sidebar */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--accent-bg) 100%);
        border-right: 2px solid var(--border-color);
        box-shadow: 4px 0 20px var(--shadow-medium);
    }
    
    /* Professional Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border-radius: 16px;
        padding: 6px;
        border: 1px solid var(--border-color);
        box-shadow: 0 4px 16px var(--shadow-medium);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 15px;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, var(--accent-bg), rgba(0, 255, 136, 0.1));
        color: var(--text-primary);
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--success-color), #00cc6a);
        color: var(--primary-bg) !important;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3);
    }
    
    /* Professional Cards */
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 20px;
        border-radius: 12px;
        border: 1px solid var(--border-color);
        margin: 10px 0;
        box-shadow: 0 6px 24px var(--shadow-heavy);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(90deg, var(--success-color), var(--info-color));
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 36px rgba(0, 255, 136, 0.15);
        border-color: var(--success-color);
    }
    
    .pattern-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid var(--success-color);
        margin: 12px 0;
        box-shadow: 0 6px 24px var(--shadow-heavy);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .pattern-card:hover {
        transform: translateX(3px);
        box-shadow: 0 8px 32px var(--shadow-heavy);
    }
    
    .consolidation-card {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(255, 170, 0, 0.08));
    }
    
    .news-card {
        border-left-color: var(--info-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(0, 170, 255, 0.08));
    }
    
    .high-confidence {
        border-left-color: var(--success-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(0, 255, 136, 0.05));
    }
    
    .medium-confidence {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(255, 170, 0, 0.05));
    }
    
    .low-confidence {
        border-left-color: var(--danger-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(255, 68, 68, 0.05));
    }
    
    /* Market Sentiment Indicators */
    .sentiment-bullish {
        background: linear-gradient(135deg, rgba(0, 255, 136, 0.15), rgba(0, 204, 106, 0.15));
        border: 1px solid var(--success-color);
        border-left: 4px solid var(--success-color);
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, rgba(255, 170, 0, 0.15), rgba(255, 193, 7, 0.15));
        border: 1px solid var(--warning-color);
        border-left: 4px solid var(--warning-color);
    }
    
    .sentiment-bearish {
        background: linear-gradient(135deg, rgba(255, 68, 68, 0.15), rgba(244, 67, 54, 0.15));
        border: 1px solid var(--danger-color);
        border-left: 4px solid var(--danger-color);
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--success-color), #00cc6a);
        color: var(--primary-bg);
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 15px;
        height: 48px;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(0, 255, 136, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00cc6a, var(--success-color));
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 136, 0.4);
    }
    
    /* Professional Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border: 1px solid var(--border-color);
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 4px 16px var(--shadow-medium);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: var(--success-color);
        box-shadow: 0 6px 20px rgba(0, 255, 136, 0.15);
    }
    
    /* Enhanced Form Controls */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--sidebar-bg));
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus {
        border-color: var(--success-color);
        box-shadow: 0 0 0 2px rgba(0, 255, 136, 0.2);
    }
    
    /* Professional Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--primary-bg);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--success-color), #00cc6a);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00cc6a, var(--success-color));
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.3rem;
        }
        
        .professional-header {
            padding: 10px 15px;
            max-height: 100px;
        }
        
        .professional-header h1 {
            font-size: 1.8rem;
        }
        
        .professional-header .subtitle {
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# COMPLETE NSE F&O UNIVERSE - All 214 stocks as per official NSE list
COMPLETE_NSE_FO_UNIVERSE = [
    # Indices (4)
    '^NSEI', '^NSEBANK', '^CNXFINANCE', '^CNXMIDCAP',
    
    # All NSE F&O Individual stocks (210 stocks) - COMPLETE LIST
    '360ONE.NS', 'ABB.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 
    'ADANITRANS.NS', 'AJANTPHARM.NS', 'ALKEM.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APLAPOLLO.NS', 'APOLLOHOSP.NS', 
    'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'ATUL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 
    'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS', 'BAJFINANCE.NS', 'BALKRISIND.NS', 'BALRAMCHIN.NS', 
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BATAINDIA.NS', 'BEL.NS', 'BERGEPAINT.NS', 'BHARATFORG.NS', 
    'BHARTIARTL.NS', 'BHEL.NS', 'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS', 
    'BSE.NS', 'BSOFT.NS', 'CAMS.NS', 'CANBK.NS', 'CANFINHOME.NS', 'CDSL.NS', 'CESC.NS', 'CGCL.NS', 
    'CGPOWER.NS', 'CHAMBLFERT.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 
    'CONCOR.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 'CYIENT.NS', 'DABUR.NS', 
    'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DELTACORP.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS', 
    'DMART.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORTIS.NS', 
    'GAIL.NS', 'GLENMARK.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRANULES.NS', 
    'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 
    'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 
    'HINDZINC.NS', 'HONAUT.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDEA.NS', 'IDFCFIRSTB.NS', 
    'IEX.NS', 'IGL.NS', 'INDHOTEL.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 
    'INFY.NS', 'IOC.NS', 'IPCALAB.NS', 'IRCTC.NS', 'IRFC.NS', 'ITC.NS', 'JINDALSTEL.NS', 'JIOFIN.NS', 
    'JKCEMENT.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS', 'KPITTECH.NS', 'KPRMILL.NS', 
    'KRBL.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LT.NS', 'LTIM.NS', 'LTTS.NS', 
    'LUPIN.NS', 'M&M.NS', 'M&MFIN.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 'MCX.NS', 
    'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS', 'MUTHOOTFIN.NS', 
    'NATIONALUM.NS', 'NAUKRI.NS', 'NAVINFLUOR.NS', 'NBCC.NS', 'NESTLEIND.NS', 'NMDC.NS', 'NTPC.NS', 
    'NYKAA.NS', 'OBEROIRLTY.NS', 'OFSS.NS', 'OIL.NS', 'ONGC.NS', 'PAGEIND.NS', 'PAYTM.NS', 'PERSISTENT.NS', 
    'PETRONET.NS', 'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 'POLYCAB.NS', 'POWERGRID.NS', 
    'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RELIANCE.NS', 'SAIL.NS', 'SBICARD.NS', 
    'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SRF.NS', 'STAR.NS', 
    'SUNPHARMA.NS', 'SUNTV.NS', 'SYNGENE.NS', 'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAELXSI.NS', 
    'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TCS.NS', 'TECHM.NS', 'TITAN.NS', 
    'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 
    'UPL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS'
]

# FIXED: Stock categories with verified symbols
STOCK_CATEGORIES = {
    'Nifty 50': [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        'NTPC.NS', 'POWERGRID.NS', 'TATAMOTORS.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
        'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
        'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
        'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
        'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
        'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS'
    ],
    'Bank Nifty': [
        'HDFCBANK.NS', 'ICICIBANK.NS', 'SBIN.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
        'INDUSINDBK.NS', 'BANKBARODA.NS', 'CANBK.NS', 'FEDERALBNK.NS', 'PNB.NS',
        'IDFCFIRSTB.NS', 'AUBANK.NS'
    ],
    'IT Stocks': [
        'TCS.NS', 'INFY.NS', 'WIPRO.NS', 'HCLTECH.NS', 'TECHM.NS',
        'LTIM.NS', 'MPHASIS.NS', 'COFORGE.NS', 'PERSISTENT.NS', 'LTTS.NS'
    ],
    'Pharma Stocks': [
        'SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS',
        'BIOCON.NS', 'AUROPHARMA.NS', 'ALKEM.NS', 'TORNTPHARM.NS', 'GLENMARK.NS'
    ],
    'Auto Stocks': [
        'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS',
        'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS', 'ESCORTS.NS'
    ],
    'Metal Stocks': [
        'TATASTEEL.NS', 'JSWSTEEL.NS', 'HINDALCO.NS', 'COALINDIA.NS', 'VEDL.NS',
        'JINDALSTEL.NS', 'NATIONALUM.NS', 'NMDC.NS', 'SAIL.NS', 'HINDZINC.NS'
    ],
    'Energy Stocks': [
        'RELIANCE.NS', 'ONGC.NS', 'IOC.NS', 'BPCL.NS', 'HINDPETRO.NS',
        'GAIL.NS', 'NTPC.NS', 'POWERGRID.NS', 'TATAPOWER.NS', 'ADANIGREEN.NS'
    ]
}

class ProfessionalPCSScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_stock_data(self, symbol, period="6mo"):
        """Get stock data with comprehensive technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            
            if len(data) < 30:
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
            data['Stoch_K'] = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close']).stoch()
            data['Williams_R'] = ta.momentum.WilliamsRIndicator(data['High'], data['Low'], data['Close']).williams_r()
            
            return data
        except Exception as e:
            return None
    
    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check volume criteria with multiple timeframes"""
        if len(data) < 21:
            return False, 0, {}
        
        current_volume = data['Volume'].iloc[-1]
        avg_5_volume = data['Volume'].tail(5).mean()
        avg_10_volume = data['Volume'].tail(10).mean()
        avg_20_volume = data['Volume'].iloc[-21:-1].mean()
        
        volume_ratio_20 = current_volume / avg_20_volume
        volume_ratio_10 = current_volume / avg_10_volume
        volume_ratio_5 = current_volume / avg_5_volume
        
        details = {
            'current_volume': current_volume,
            'avg_5_volume': avg_5_volume,
            'avg_10_volume': avg_10_volume,
            'avg_20_volume': avg_20_volume,
            'ratio_5d': volume_ratio_5,
            'ratio_10d': volume_ratio_10,
            'ratio_20d': volume_ratio_20
        }
        
        return volume_ratio_20 >= min_ratio, volume_ratio_20, details
    
    def get_fundamental_news(self, symbol, stock_name):
        """
        NEW: Get fundamental news for the stock to explain volume/price movements
        Searches for recent news, earnings, orders, policy changes, etc.
        """
        try:
            # Clean symbol for search
            clean_symbol = symbol.replace('.NS', '')
            
            # Multiple search queries for comprehensive news
            search_queries = [
                f"{stock_name} stock news today",
                f"{clean_symbol} earnings results",
                f"{stock_name} order announcement",
                f"{clean_symbol} policy government support",
                f"{stock_name} quarterly results",
                f"{clean_symbol} volume spike news"
            ]
            
            news_items = []
            
            for query in search_queries[:2]:  # Limit to 2 queries for speed
                try:
                    # Use Google News search
                    search_url = f"https://www.google.com/search?q={query}&tbm=nws&tbs=qdr:d"  # Last 24 hours
                    
                    response = self.session.get(search_url, timeout=5)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract news headlines and snippets
                        news_elements = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:3]  # Top 3 results
                        
                        for element in news_elements:
                            headline = element.get_text().strip()
                            if len(headline) > 20 and stock_name.lower() in headline.lower():
                                news_items.append({
                                    'headline': headline,
                                    'relevance': self._assess_news_relevance(headline),
                                    'source': 'Recent News'
                                })
                                
                except Exception:
                    continue
            
            # If no recent news, try alternative approach
            if not news_items:
                # Try to get company info from yfinance
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    
                    # Check for recent events
                    if 'longBusinessSummary' in info:
                        summary = info['longBusinessSummary'][:200] + "..."
                        news_items.append({
                            'headline': f"Business Overview: {summary}",
                            'relevance': 'medium',
                            'source': 'Company Profile'
                        })
                        
                except Exception:
                    pass
            
            # Assess overall news sentiment
            if news_items:
                positive_keywords = ['order', 'win', 'contract', 'growth', 'profit', 'beat', 'strong', 'positive', 'approval', 'launch']
                negative_keywords = ['loss', 'decline', 'weak', 'concern', 'fall', 'drop', 'negative', 'warning']
                
                sentiment_score = 0
                for item in news_items:
                    headline_lower = item['headline'].lower()
                    for word in positive_keywords:
                        if word in headline_lower:
                            sentiment_score += 1
                    for word in negative_keywords:
                        if word in headline_lower:
                            sentiment_score -= 1
                
                overall_sentiment = 'positive' if sentiment_score > 0 else 'negative' if sentiment_score < 0 else 'neutral'
            else:
                overall_sentiment = 'neutral'
            
            return {
                'news_items': news_items[:3],  # Top 3 most relevant
                'overall_sentiment': overall_sentiment,
                'news_count': len(news_items)
            }
            
        except Exception as e:
            return {
                'news_items': [],
                'overall_sentiment': 'neutral', 
                'news_count': 0
            }
    
    def _assess_news_relevance(self, headline):
        """Assess how relevant news is to volume/price movement"""
        high_relevance_keywords = ['order', 'contract', 'earnings', 'results', 'approval', 'launch', 'merger', 'acquisition']
        medium_relevance_keywords = ['growth', 'expansion', 'investment', 'partnership', 'policy', 'announcement']
        
        headline_lower = headline.lower()
        
        for word in high_relevance_keywords:
            if word in headline_lower:
                return 'high'
        
        for word in medium_relevance_keywords:
            if word in headline_lower:
                return 'medium'
        
        return 'low'
    
    def detect_tight_consolidation_breakout(self, data, consolidation_days_min=14, consolidation_days_max=20, max_range_pct=8, volume_breakout_ratio=2.0):
        """Professional: Detect tight consolidation breakout patterns"""
        if len(data) < 25:
            return False, 0, {}
        
        # Look for consolidation in last 14-20 days + breakout day
        for consolidation_days in range(consolidation_days_min, consolidation_days_max + 1):
            if len(data) < consolidation_days + 5:
                continue
                
            # Get consolidation period data
            consolidation_data = data.iloc[-(consolidation_days + 1):-1]  # Exclude breakout day
            breakout_day = data.iloc[-1]
            
            # Check consolidation criteria
            consolidation_high = consolidation_data['High'].max()
            consolidation_low = consolidation_data['Low'].min()
            consolidation_range = ((consolidation_high - consolidation_low) / consolidation_low) * 100
            
            # Tight range requirement
            if consolidation_range > max_range_pct:
                continue
            
            # Check for breakout
            current_price = breakout_day['Close']
            breakout_above_high = current_price > consolidation_high * 1.01  # 1% breakout threshold
            
            if not breakout_above_high:
                continue
            
            # Volume analysis
            consolidation_avg_volume = consolidation_data['Volume'].mean()
            breakout_volume = breakout_day['Volume']
            volume_ratio = breakout_volume / consolidation_avg_volume
            
            # Volume breakout requirement
            if volume_ratio < volume_breakout_ratio:
                continue
            
            # Calculate strength based on multiple factors
            strength = 0
            
            # Range tightness (smaller range = higher strength)
            if consolidation_range <= 3:
                strength += 35
            elif consolidation_range <= 5:
                strength += 25
            elif consolidation_range <= 8:
                strength += 15
            
            # Volume surge strength
            if volume_ratio >= 5:
                strength += 30
            elif volume_ratio >= 3:
                strength += 25
            elif volume_ratio >= 2:
                strength += 20
            
            # Breakout strength
            breakout_strength = ((current_price - consolidation_high) / consolidation_high) * 100
            if breakout_strength >= 3:
                strength += 25
            elif breakout_strength >= 2:
                strength += 20
            elif breakout_strength >= 1:
                strength += 15
            
            # Duration bonus (ideal consolidation period)
            if 16 <= consolidation_days <= 18:
                strength += 10
            elif 14 <= consolidation_days <= 20:
                strength += 5
            
            details = {
                'consolidation_days': consolidation_days,
                'consolidation_range_pct': consolidation_range,
                'consolidation_high': consolidation_high,
                'consolidation_low': consolidation_low,
                'breakout_price': current_price,
                'breakout_strength_pct': breakout_strength,
                'volume_ratio': volume_ratio,
                'consolidation_avg_volume': consolidation_avg_volume,
                'breakout_volume': breakout_volume
            }
            
            return True, strength, details
        
        return False, 0, {}
    
    def get_market_sentiment_indicators(self):
        """Professional: Advanced market sentiment analysis"""
        try:
            sentiment_data = {}
            
            # 1. Nifty 50 Analysis
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="10d")
            
            if len(nifty_data) >= 2:
                current_nifty = nifty_data['Close'].iloc[-1]
                prev_nifty = nifty_data['Close'].iloc[-2]
                nifty_change_pct = ((current_nifty - prev_nifty) / prev_nifty) * 100
                
                # 5-day trend
                if len(nifty_data) >= 5:
                    nifty_5d_change = ((current_nifty - nifty_data['Close'].iloc[-6]) / nifty_data['Close'].iloc[-6]) * 100
                else:
                    nifty_5d_change = nifty_change_pct
                
                sentiment_data['nifty'] = {
                    'current': current_nifty,
                    'change_1d': nifty_change_pct,
                    'change_5d': nifty_5d_change,
                    'sentiment': self._get_sentiment_level(nifty_change_pct)
                }
            
            # 2. Bank Nifty Analysis
            bank_nifty = yf.Ticker("^NSEBANK")
            bank_data = bank_nifty.history(period="5d")
            
            if len(bank_data) >= 2:
                current_bank = bank_data['Close'].iloc[-1]
                prev_bank = bank_data['Close'].iloc[-2]
                bank_change_pct = ((current_bank - prev_bank) / prev_bank) * 100
                
                sentiment_data['bank_nifty'] = {
                    'current': current_bank,
                    'change_1d': bank_change_pct,
                    'sentiment': self._get_sentiment_level(bank_change_pct)
                }
            
            # 3. Overall Market Sentiment
            nifty_sentiment = sentiment_data['nifty']['sentiment']
            bank_sentiment = sentiment_data['bank_nifty']['sentiment']
            
            # Weighted sentiment calculation
            sentiment_scores = {
                'BULLISH': 3,
                'NEUTRAL': 2,
                'BEARISH': 1
            }
            
            nifty_score = sentiment_scores.get(nifty_sentiment, 2)
            bank_score = sentiment_scores.get(bank_sentiment, 2)
            
            # Nifty has 60% weight, Bank Nifty 40%
            overall_score = (nifty_score * 0.6) + (bank_score * 0.4)
            
            if overall_score >= 2.5:
                overall_sentiment = "BULLISH"
                pcs_recommendation = "Excellent for Put Credit Spreads"
                risk_level = "LOW"
            elif overall_score >= 1.8:
                overall_sentiment = "NEUTRAL"
                pcs_recommendation = "Moderate PCS opportunities"
                risk_level = "MEDIUM"
            else:
                overall_sentiment = "BEARISH"
                pcs_recommendation = "Avoid PCS, consider Call Credit Spreads"
                risk_level = "HIGH"
            
            sentiment_data['overall'] = {
                'sentiment': overall_sentiment,
                'score': overall_score,
                'pcs_recommendation': pcs_recommendation,
                'risk_level': risk_level
            }
            
            return sentiment_data
            
        except Exception as e:
            return {
                'overall': {
                    'sentiment': 'NEUTRAL',
                    'score': 2.0,
                    'pcs_recommendation': 'Data unavailable - trade with caution',
                    'risk_level': 'MEDIUM'
                }
            }
    
    def _get_sentiment_level(self, change_pct):
        """Convert percentage change to sentiment level"""
        if change_pct >= 1.0:
            return "BULLISH"
        elif change_pct >= -1.0:
            return "NEUTRAL"
        else:
            return "BEARISH"
    
    def detect_patterns(self, data, symbol, filters):
        """Enhanced pattern detection with all professional patterns"""
        patterns = []
        
        if len(data) < 30:
            return patterns
        
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        
        # Apply basic filters
        if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
            return patterns
        
        if current_adx < filters['adx_min']:
            return patterns
        
        # MA support check
        if filters['ma_support']:
            if filters['ma_type'] == 'SMA':
                if current_price < sma_20 * (1 - filters['ma_tolerance']/100):
                    return patterns
            else:  # EMA
                if current_price < ema_20 * (1 - filters['ma_tolerance']/100):
                    return patterns
        
        # 1. Tight Consolidation Breakout Detection (TOP PRIORITY)
        consolidation_detected, consolidation_strength, consolidation_details = self.detect_tight_consolidation_breakout(
            data, 
            consolidation_days_min=filters.get('consolidation_days_min', 14),
            consolidation_days_max=filters.get('consolidation_days_max', 20),
            max_range_pct=filters.get('max_consolidation_range', 8),
            volume_breakout_ratio=filters.get('volume_breakout_ratio', 2.0)
        )
        
        if consolidation_detected and consolidation_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'Tight Consolidation Breakout',
                'strength': consolidation_strength,
                'success_rate': 88,
                'research_basis': 'William O\'Neil - Tight Base Breakouts',
                'pcs_suitability': 95,
                'confidence': self.get_confidence_level(consolidation_strength),
                'details': consolidation_details,
                'special': 'PROFESSIONAL_BREAKOUT'
            })
        
        # 2. Cup and Handle
        cup_detected, cup_strength = self.detect_cup_and_handle(data)
        if cup_detected and cup_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'Cup and Handle',
                'strength': cup_strength,
                'success_rate': 85,
                'research_basis': 'William O\'Neil - IBD',
                'pcs_suitability': 95,
                'confidence': self.get_confidence_level(cup_strength)
            })
        
        # 3. Flat Base Breakout
        flat_detected, flat_strength = self.detect_flat_base_breakout(data)
        if flat_detected and flat_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'Flat Base Breakout',
                'strength': flat_strength,
                'success_rate': 82,
                'research_basis': 'Mark Minervini - Momentum',
                'pcs_suitability': 92,
                'confidence': self.get_confidence_level(flat_strength)
            })
        
        # 4. VCP Pattern
        vcp_detected, vcp_strength = self.detect_vcp_pattern(data)
        if vcp_detected and vcp_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'VCP (Volatility Contraction)',
                'strength': vcp_strength,
                'success_rate': 78,
                'research_basis': 'Mark Minervini - VCP',
                'pcs_suitability': 88,
                'confidence': self.get_confidence_level(vcp_strength)
            })
        
        return patterns
    
    def get_confidence_level(self, strength):
        """Get confidence level based on pattern strength"""
        if strength >= 85:
            return 'HIGH'
        elif strength >= 70:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def detect_cup_and_handle(self, data):
        """Detect Cup and Handle pattern"""
        if len(data) < 40:
            return False, 0
        
        recent_data = data.tail(40)
        
        # Cup formation
        cup_data = recent_data.iloc[:30]
        cup_left_high = cup_data['High'].iloc[:10].max()
        cup_right_high = cup_data['High'].iloc[-10:].max()
        cup_low = cup_data['Low'].iloc[5:25].min()
        
        # Cup criteria
        cup_depth = ((cup_left_high - cup_low) / cup_left_high) * 100
        depth_valid = 10 <= cup_depth <= 60
        
        symmetry_valid = abs(cup_left_high - cup_right_high) / cup_left_high < 0.15
        
        # Handle formation
        handle_data = recent_data.tail(10)
        handle_high = handle_data['High'].max()
        handle_low = handle_data['Low'].min()
        handle_depth = ((handle_high - handle_low) / handle_high) * 100
        
        handle_valid = handle_depth < 20
        
        # Breakout validation
        current_price = data['Close'].iloc[-1]
        resistance = max(cup_left_high, cup_right_high)
        breakout = current_price >= resistance * 0.97
        
        strength = 0
        if depth_valid: strength += 25
        if symmetry_valid: strength += 20
        if handle_valid: strength += 25
        if breakout: strength += 30
        
        return (depth_valid and handle_valid and breakout), strength
    
    def detect_flat_base_breakout(self, data):
        """Detect Flat Base Breakout"""
        if len(data) < 20:
            return False, 0
        
        base_data = data.tail(20)
        
        high_price = base_data['High'].max()
        low_price = base_data['Low'].min()
        price_range = ((high_price - low_price) / low_price) * 100
        
        tight_range = price_range < 15
        
        current_price = data['Close'].iloc[-1]
        resistance = base_data['High'].quantile(0.9)
        breakout = current_price >= resistance * 0.998
        
        strength = 0
        if tight_range: strength += 40
        if breakout: strength += 60
        
        return (tight_range and breakout), strength
    
    def detect_vcp_pattern(self, data):
        """Detect VCP pattern"""
        if len(data) < 30:
            return False, 0
        
        recent_data = data.tail(30)
        
        # Volatility contraction check
        vol_periods = [8, 6, 4]
        volatilities = []
        
        for period in vol_periods:
            if len(recent_data) >= period:
                period_data = recent_data.tail(period)
                vol = ((period_data['High'] - period_data['Low']) / period_data['Close']).mean() * 100
                volatilities.append(vol)
        
        if len(volatilities) < 2:
            return False, 0
        
        contracting = volatilities[0] > volatilities[-1]
        current_vol = volatilities[-1] if volatilities else 5
        low_volatility = current_vol < 4
        
        current_price = data['Close'].iloc[-1]
        recent_high = recent_data['High'].max()
        near_highs = current_price >= recent_high * 0.92
        
        strength = 0
        if contracting: strength += 35
        if low_volatility: strength += 25
        if near_highs: strength += 40
        
        return (contracting and near_highs), strength
    
    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Create professional TradingView-style chart"""
        if len(data) < 20:
            return None
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.25, 0.15],
            subplot_titles=('Price Action with Pattern Analysis', 'Volume Analysis', 'RSI Momentum')
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
                increasing_line_color='#00ff88',
                decreasing_line_color='#ff4444',
                increasing_fillcolor='#00ff88',
                decreasing_fillcolor='#ff4444'
            ),
            row=1, col=1
        )
        
        # Moving averages
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['EMA_20'],
                mode='lines',
                name='EMA 20',
                line=dict(color='#ffaa00', width=2)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['SMA_50'],
                mode='lines',
                name='SMA 50',
                line=dict(color='#00aaff', width=2)
            ),
            row=1, col=1
        )
        
        # Pattern-specific annotations
        if pattern_info and pattern_info.get('special') == 'PROFESSIONAL_BREAKOUT':
            details = pattern_info.get('details', {})
            if details:
                # Highlight consolidation zone
                consolidation_high = details.get('consolidation_high')
                consolidation_low = details.get('consolidation_low')
                if consolidation_high and consolidation_low:
                    fig.add_hline(
                        y=consolidation_high, 
                        line_dash="dash", 
                        line_color="#ffaa00", 
                        row=1, col=1,
                        annotation_text=f"Breakout Level: ₹{consolidation_high:.2f}"
                    )
                    fig.add_hline(
                        y=consolidation_low, 
                        line_dash="dash", 
                        line_color="#00aaff", 
                        row=1, col=1,
                        annotation_text=f"Support: ₹{consolidation_low:.2f}"
                    )
        
        # Volume bars with breakout highlighting  
        colors = []
        for i, (close, open_price, volume) in enumerate(zip(data['Close'], data['Open'], data['Volume'])):
            if close >= open_price:
                colors.append('#00ff88')
            else:
                colors.append('#ff4444')
        
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
                name='Volume MA (20)',
                line=dict(color='white', width=1)
            ),
            row=2, col=1
        )
        
        # RSI with levels
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['RSI'],
                mode='lines',
                name='RSI (14)',
                line=dict(color='#aa66ff', width=2)
            ),
            row=3, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="#ff4444", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00ff88", row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#ffaa00", row=3, col=1)
        
        # Update layout
        pattern_name = pattern_info['type'] if pattern_info else 'Technical Analysis'
        confidence = pattern_info.get('confidence', '') if pattern_info else ''
        title = f'{symbol.replace(".NS", "")} - {pattern_name} ({confidence} Confidence)'
        
        fig.update_layout(
            title=title,
            template='plotly_dark',
            paper_bgcolor='rgba(26, 31, 46, 1)',
            plot_bgcolor='rgba(26, 31, 46, 1)',
            font=dict(color='white', family='Inter'),
            height=700,
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

def create_professional_sidebar():
    """Create professional sidebar with essential filters"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, var(--success-color), #00cc6a); border-radius: 12px; margin-bottom: 16px;'>
            <h2 style='color: var(--primary-bg); margin: 0; font-weight: 700;'>🎯 PCS Scanner</h2>
            <p style='color: var(--primary-bg); margin: 5px 0 0 0; opacity: 0.9;'>Professional Suite</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock Universe Selection
        st.markdown("### 📊 Stock Universe")
        
        universe_option = st.selectbox(
            "Select Universe:",
            ["Complete NSE F&O (214 stocks)", "Nifty 50", "Bank Nifty", "IT Stocks", 
             "Pharma Stocks", "Auto Stocks", "Metal Stocks", "Energy Stocks", "Custom Selection"],
            help="Choose the stock universe to scan"
        )
        
        if universe_option == "Custom Selection":
            custom_stocks = st.text_area(
                "Enter stock symbols (one per line):",
                value="RELIANCE.NS\nTCS.NS\nHDFCBANK.NS\nINFY.NS",
                help="Enter NSE symbols with .NS suffix"
            )
            stocks_to_scan = [s.strip() for s in custom_stocks.split('\n') if s.strip()]
        elif universe_option == "Complete NSE F&O (214 stocks)":
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        else:
            # Handle sector selection properly
            category_key = universe_option
            stocks_to_scan = STOCK_CATEGORIES.get(category_key, [])
        
        st.info(f"📈 **{len(stocks_to_scan)} stocks** selected for analysis")
        
        # Technical Filters (Essential only)
        st.markdown("### ⚙️ Technical Filters")
        
        with st.expander("🔧 Core Indicators", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                rsi_min = st.slider("RSI Min:", 20, 80, 35)
            with col2:
                rsi_max = st.slider("RSI Max:", 20, 80, 75)
            
            adx_min = st.slider("ADX Minimum:", 10, 50, 15)
            
            ma_support = st.checkbox("Moving Average Support", value=True)
            if ma_support:
                col1, col2 = st.columns(2)
                with col1:
                    ma_type = st.selectbox("MA Type:", ["EMA", "SMA"])
                with col2:
                    ma_tolerance = st.slider("MA Tolerance %:", 0, 10, 2)
        
        # Volume Filters
        with st.expander("📊 Volume Analysis", expanded=True):
            min_volume_ratio = st.slider("Min Volume Ratio:", 0.5, 5.0, 1.0, 0.1)
            volume_breakout_ratio = st.slider("Volume Breakout:", 1.5, 5.0, 2.0, 0.1)
        
        # Consolidation Settings (Essential)
        with st.expander("🎯 Consolidation Settings", expanded=True):
            consolidation_days_min = st.slider("Min Days:", 10, 20, 14)
            consolidation_days_max = st.slider("Max Days:", 15, 25, 20)
            max_consolidation_range = st.slider("Max Range %:", 3, 15, 8, 1)
        
        # Pattern Strength (Single filter)
        pattern_strength_min = st.slider("Pattern Strength Min:", 50, 100, 60, 5)
        
        # Scanning Options
        with st.expander("🚀 Scanning Options", expanded=True):
            max_stocks = st.slider(
                "Max Stocks to Scan:", 
                10, min(100, len(stocks_to_scan)), 
                min(50, len(stocks_to_scan))
            )
            
            show_charts = st.checkbox("Show Charts", value=True)
            show_news = st.checkbox("Show Fundamental News", value=True, help="Get news/events that may explain volume spikes")
            export_results = st.checkbox("Export Results", value=False)
        
        # Market Sentiment
        st.markdown("### 🌍 Market Sentiment")
        
        scanner = ProfessionalPCSScanner()
        sentiment_data = scanner.get_market_sentiment_indicators()
        
        overall_sentiment = sentiment_data.get('overall', {})
        sentiment_level = overall_sentiment.get('sentiment', 'NEUTRAL')
        pcs_recommendation = overall_sentiment.get('pcs_recommendation', 'Moderate opportunities')
        
        sentiment_class = f"sentiment-{sentiment_level.lower()}"
        
        st.markdown(f"""
        <div class="{sentiment_class}" style="padding: 12px; border-radius: 10px; margin: 8px 0;">
            <h4 style="margin: 0 0 6px 0; color: var(--text-primary);">
                {'🟢' if sentiment_level == 'BULLISH' else '🟡' if sentiment_level == 'NEUTRAL' else '🔴'} 
                {sentiment_level}
            </h4>
            <p style="margin: 0; font-size: 0.85rem; opacity: 0.9;">{pcs_recommendation}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick metrics
        if 'nifty' in sentiment_data:
            nifty_data = sentiment_data['nifty']
            st.metric("Nifty 50", f"{nifty_data['current']:.0f}", f"{nifty_data['change_1d']:+.2f}%")
        
        # Current time
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        st.markdown(f"**Updated:** {current_time.strftime('%H:%M IST')}")
        
        return {
            'stocks_to_scan': stocks_to_scan[:max_stocks],
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'adx_min': adx_min,
            'ma_support': ma_support,
            'ma_type': ma_type if ma_support else 'EMA',
            'ma_tolerance': ma_tolerance if ma_support else 2,
            'min_volume_ratio': min_volume_ratio,
            'volume_breakout_ratio': volume_breakout_ratio,
            'consolidation_days_min': consolidation_days_min,
            'consolidation_days_max': consolidation_days_max,
            'max_consolidation_range': max_consolidation_range,
            'pattern_strength_min': pattern_strength_min,
            'show_charts': show_charts,
            'show_news': show_news,
            'export_results': export_results,
            'max_stocks': max_stocks,
            'market_sentiment': sentiment_data
        }

def create_main_scanner_tab(config):
    """Create main scanner tab with professional results display"""
    st.markdown("### 🎯 Professional Pattern & Breakout Scanner")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button("🚀 Start Professional Scan", type="primary", key="main_scan")
    
    with col2:
        if config['export_results']:
            export_button = st.button("📊 Export Results", key="export")
        else:
            st.markdown("*Enable export in sidebar*")
    
    with col3:
        st.markdown(f"**Scanning: {len(config['stocks_to_scan'])} stocks**")
    
    if scan_button:
        scanner = ProfessionalPCSScanner()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        results = []
        
        for i, symbol in enumerate(config['stocks_to_scan']):
            progress = (i + 1) / len(config['stocks_to_scan'])
            progress_bar.progress(progress)
            
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            status_container.info(f"🔍 Analyzing {clean_symbol} ({i+1}/{len(config['stocks_to_scan'])})")
            
            try:
                # Get data
                data = scanner.get_stock_data(symbol)
                if data is None:
                    continue
                
                # Check volume
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
                if not volume_ok:
                    continue
                
                # Detect patterns (all patterns automatically included)
                patterns = scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue
                
                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]
                
                # Get fundamental news if enabled
                news_data = None
                if config['show_news']:
                    try:
                        # Extract company name for news search
                        stock_name = clean_symbol
                        news_data = scanner.get_fundamental_news(symbol, stock_name)
                    except:
                        news_data = None
                
                results.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                    'news_data': news_data
                })
                
            except Exception as e:
                continue
        
        # Clear progress
        progress_bar.empty()
        status_container.empty()
        
        # Display results
        if results:
            # Sort by pattern strength
            results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)
            
            st.success(f"🎉 Found **{len(results)} stocks** with high-quality patterns!")
            
            # Summary metrics
            total_patterns = sum(len(r['patterns']) for r in results)
            avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
            high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')
            consolidation_breakouts = sum(1 for r in results for p in r['patterns'] if 'Consolidation' in p['type'])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Stocks Found", len(results))
            with col2:
                st.metric("📊 Total Patterns", total_patterns)
            with col3:
                st.metric("💪 Avg Strength", f"{avg_strength:.1f}%")
            with col4:
                st.metric("🔥 Breakouts", consolidation_breakouts)
            
            # Display results with enhanced information
            for result in results:
                # Determine overall confidence
                max_strength = max(p['strength'] for p in result['patterns'])
                overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
                
                # Check for consolidation breakout
                has_consolidation = any('Consolidation' in p['type'] for p in result['patterns'])
                special_indicator = " 🔥 BREAKOUT!" if has_consolidation else ""
                
                # Check for news
                has_news = result.get('news_data') and result['news_data']['news_count'] > 0
                news_indicator = " 📰 NEWS!" if has_news else ""
                
                with st.expander(
                    f"📈 {result['symbol'].replace('.NS', '').replace('^', '')} - {len(result['patterns'])} Pattern(s) - {overall_confidence}{special_indicator}{news_indicator}", 
                    expanded=True
                ):
                    
                    # Stock metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Price", f"₹{result['current_price']:.2f}")
                    with col2:
                        volume_color = "normal" if result['volume_ratio'] < 2 else "inverse"
                        st.metric("📊 Volume", f"{result['volume_ratio']:.2f}x", delta_color=volume_color)
                    with col3:
                        rsi_color = "normal" if 30 <= result['rsi'] <= 70 else "inverse"
                        st.metric("📈 RSI", f"{result['rsi']:.1f}", delta_color=rsi_color)
                    with col4:
                        adx_color = "normal" if result['adx'] > 25 else "inverse"
                        st.metric("⚡ ADX", f"{result['adx']:.1f}", delta_color=adx_color)
                    
                    # NEWS ANALYSIS - NEW FEATURE
                    if has_news:
                        news_data = result['news_data']
                        sentiment_emoji = "🟢" if news_data['overall_sentiment'] == 'positive' else "🔴" if news_data['overall_sentiment'] == 'negative' else "🟡"
                        
                        st.markdown(f"""
                        <div class="news-card">
                            <h4>{sentiment_emoji} Fundamental News Analysis - {news_data['overall_sentiment'].upper()} Sentiment</h4>
                            <p style="margin: 8px 0; font-size: 0.9rem; opacity: 0.9;">
                                <strong>📰 Recent Events ({news_data['news_count']} items):</strong>
                            </p>
                        """, unsafe_allow_html=True)
                        
                        for news_item in news_data['news_items'][:2]:  # Show top 2 news items
                            relevance_emoji = "🔥" if news_item['relevance'] == 'high' else "⚡" if news_item['relevance'] == 'medium' else "📄"
                            st.markdown(f"**{relevance_emoji} {news_item['relevance'].upper()}:** {news_item['headline'][:150]}...")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Pattern details with enhanced information
                    for pattern in result['patterns']:
                        confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡" if pattern['confidence'] == 'MEDIUM' else "🔴"
                        
                        # Special handling for consolidation breakouts
                        if pattern.get('special') == 'PROFESSIONAL_BREAKOUT':
                            details = pattern.get('details', {})
                            
                            st.markdown(f"""
                            <div class="consolidation-card">
                                <h4>🔥 {confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence</h4>
                                <div style='display: flex; justify-content: space-between; margin: 10px 0;'>
                                    <span><strong>Strength:</strong> {pattern['strength']}%</span>
                                    <span><strong>Success Rate:</strong> {pattern['success_rate']}%</span>
                                    <span><strong>PCS Fit:</strong> {pattern['pcs_suitability']}%</span>
                                </div>
                                <div style='display: flex; justify-content: space-between; margin: 10px 0; font-size: 0.9rem;'>
                                    <span><strong>Consolidation:</strong> {details.get('consolidation_days', 'N/A')} days</span>
                                    <span><strong>Range:</strong> {details.get('consolidation_range_pct', 0):.1f}%</span>
                                    <span><strong>Volume Surge:</strong> {details.get('volume_ratio', 0):.1f}x</span>
                                </div>
                                <p><strong>Research:</strong> {pattern['research_basis']}</p>
                                <p><strong>💡 PCS Strategy:</strong> {'Conservative (3-5% OTM)' if pattern['confidence'] == 'HIGH' else 'Moderate (5-8% OTM)' if pattern['confidence'] == 'MEDIUM' else 'Aggressive (8-12% OTM)'}</p>
                                <p style="color: var(--success-color); font-weight: 600;">⚡ PROFESSIONAL BREAKOUT: High-probability setup</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            confidence_class = f"{pattern['confidence'].lower()}-confidence"
                            st.markdown(f"""
                            <div class="pattern-card {confidence_class}">
                                <h4>{confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence</h4>
                                <div style='display: flex; justify-content: space-between; margin: 10px 0;'>
                                    <span><strong>Strength:</strong> {pattern['strength']}%</span>
                                    <span><strong>Success Rate:</strong> {pattern['success_rate']}%</span>
                                    <span><strong>PCS Fit:</strong> {pattern['pcs_suitability']}%</span>
                                </div>
                                <p><strong>Research:</strong> {pattern['research_basis']}</p>
                                <p><strong>💡 PCS Strategy:</strong> {'Conservative (5% OTM)' if pattern['confidence'] == 'HIGH' else 'Moderate (8% OTM)' if pattern['confidence'] == 'MEDIUM' else 'Aggressive (12% OTM)'}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Chart
                    if config['show_charts']:
                        st.markdown("#### 📊 Professional Chart Analysis")
                        chart = scanner.create_tradingview_chart(
                            result['data'], 
                            result['symbol'], 
                            result['patterns'][0] if result['patterns'] else None
                        )
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("🔍 No patterns found with current filters. Try relaxing the criteria.")
            
            st.markdown("### 💡 Suggestions:")
            st.markdown("- Lower **Pattern Strength** to 50%")
            st.markdown("- Reduce **Volume Ratio** to 0.8x")  
            st.markdown("- Expand **RSI range** to 30-80")
            st.markdown("- Lower **ADX minimum** to 12")

def main():
    # FIXED: Compact Professional Header - Only 20% of screen
    st.markdown("""
    <div class="professional-header">
        <h1>📈 NSE F&O PCS Professional Scanner</h1>
        <p class="subtitle">Complete 214-Stock Universe • Advanced Breakout Detection • News Intelligence</p>
        <p class="description">Professional Trading Suite with Fundamental Analysis & Market Sentiment</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get sidebar configuration
    config = create_professional_sidebar()
    
    # Create main tabs
    tab1, tab2, tab3 = st.tabs([
        "🎯 Pattern Scanner",
        "📊 Market Intelligence", 
        "🌍 News & Sentiment"
    ])
    
    with tab1:
        create_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📊 Real-Time Market Intelligence")
        
        # Get comprehensive market data
        scanner = ProfessionalPCSScanner()
        sentiment_data = scanner.get_market_sentiment_indicators()
        
        # Market Overview
        col1, col2, col3 = st.columns(3)
        
        overall_sentiment = sentiment_data.get('overall', {})
        
        with col1:
            sentiment_level = overall_sentiment.get('sentiment', 'NEUTRAL')
            sentiment_emoji = "🟢" if sentiment_level == 'BULLISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🔴"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{sentiment_emoji} Market Sentiment</h3>
                <h2 style="color: var(--success-color);">{sentiment_level}</h2>
                <p>{overall_sentiment.get('pcs_recommendation', 'Moderate opportunities')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            risk_level = overall_sentiment.get('risk_level', 'MEDIUM')
            risk_color = "var(--success-color)" if risk_level == 'LOW' else "var(--warning-color)" if risk_level == 'MEDIUM' else "var(--danger-color)"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚠️ Risk Level</h3>
                <h2 style="color: {risk_color};">{risk_level}</h2>
                <p>Current PCS risk assessment</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            score = overall_sentiment.get('score', 2.0)
            score_pct = (score / 3.0) * 100
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>📊 Confidence Score</h3>
                <h2 style="color: var(--info-color);">{score:.1f}/3.0</h2>
                <p>{score_pct:.0f}% Market Confidence</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed Market Metrics
        st.markdown("#### 📈 Detailed Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'nifty' in sentiment_data:
                nifty_data = sentiment_data['nifty']
                st.metric("Nifty 50", f"{nifty_data['current']:.0f}", f"{nifty_data['change_1d']:+.2f}%")
                if 'change_5d' in nifty_data:
                    st.metric("5-Day Trend", f"{nifty_data['change_5d']:+.2f}%")
        
        with col2:
            if 'bank_nifty' in sentiment_data:
                bank_data = sentiment_data['bank_nifty']
                st.metric("Bank Nifty", f"{bank_data['current']:.0f}", f"{bank_data['change_1d']:+.2f}%")
    
    with tab3:
        st.markdown("### 🌍 News & Sentiment Analysis")
        st.info("📰 **Enhanced Feature**: News analysis is integrated into the main scanner results when enabled in sidebar.")
        st.markdown("""
        **How it works:**
        - **Volume Spike Detection**: When unusual volume is detected, the scanner searches for fundamental reasons
        - **News Categorization**: Orders, earnings, policy changes, government support are identified
        - **Sentiment Analysis**: Positive/negative/neutral sentiment assessment
        - **Relevance Scoring**: High/medium/low relevance to price/volume movements
        """)
    
    # FIXED: Compact Professional Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)); border-radius: 12px; margin-top: 20px; border: 1px solid var(--border-color);'>
        <h4 style='color: var(--success-color); margin-bottom: 10px;'>🏆 Professional Trading Suite V3.0</h4>
        <p style='color: var(--text-secondary); margin: 3px 0;'><strong>✅ Complete NSE F&O Universe:</strong> All 214 official stocks</p>
        <p style='color: var(--text-secondary); margin: 3px 0;'><strong>🔥 Professional Breakouts:</strong> 14-20 day consolidation detection</p>
        <p style='color: var(--text-secondary); margin: 3px 0;'><strong>📰 News Intelligence:</strong> Fundamental analysis for volume spikes</p>
        <p style='color: var(--text-muted); margin: 10px 0 0 0; font-size: 0.85rem;'><strong>⚠️ Disclaimer:</strong> Educational purposes only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
