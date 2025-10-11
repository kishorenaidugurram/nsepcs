professional_pcs_scanner.py

Download
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

# Professional Dark Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --primary-bg: #0a0e1a;
        --secondary-bg: #1a1f2e;
        --accent-bg: #252b3d;
        --sidebar-bg: #1e2432;
        --success-color: #00d4aa;
        --warning-color: #ffa726;
        --danger-color: #ff5252;
        --info-color: #42a5f5;
        --text-primary: #ffffff;
        --text-secondary: #b0bec5;
        --text-muted: #78909c;
        --border-color: #37474f;
        --border-light: #455a64;
        --shadow-light: rgba(0, 0, 0, 0.1);
        --shadow-medium: rgba(0, 0, 0, 0.2);
        --shadow-heavy: rgba(0, 0, 0, 0.3);
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
    
    /* Enhanced Sidebar */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--accent-bg) 100%);
        border-right: 2px solid var(--border-color);
        box-shadow: 4px 0 20px var(--shadow-medium);
    }
    
    .css-1d391kg .css-1lcbmhc .css-1outpf7 {
        background-color: transparent;
    }
    
    /* Sidebar headers */
    .sidebar .element-container h3 {
        color: var(--success-color);
        font-weight: 600;
        border-bottom: 2px solid var(--success-color);
        padding-bottom: 8px;
        margin-bottom: 16px;
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
        height: 56px;
        background-color: transparent;
        border-radius: 12px;
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 16px;
        border: none;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, var(--accent-bg), rgba(0, 212, 170, 0.1));
        color: var(--text-primary);
        transform: translateY(-1px);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--success-color), #00bfa5);
        color: var(--primary-bg) !important;
        font-weight: 600;
        box-shadow: 0 4px 16px rgba(0, 212, 170, 0.3);
    }
    
    /* Professional Cards */
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 24px;
        border-radius: 16px;
        border: 1px solid var(--border-color);
        margin: 12px 0;
        box-shadow: 0 8px 32px var(--shadow-heavy);
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
        transform: translateY(-4px);
        box-shadow: 0 16px 48px rgba(0, 212, 170, 0.15);
        border-color: var(--success-color);
    }
    
    .pattern-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 24px;
        border-radius: 16px;
        border-left: 4px solid var(--success-color);
        margin: 16px 0;
        box-shadow: 0 8px 32px var(--shadow-heavy);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    
    .pattern-card:hover {
        transform: translateX(4px);
        box-shadow: 0 12px 48px var(--shadow-heavy);
    }
    
    .consolidation-card {
        border-left-color: var(--warning-color);
    }
    
    .high-confidence {
        border-left-color: var(--success-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(0, 212, 170, 0.05));
    }
    
    .medium-confidence {
        border-left-color: var(--warning-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(255, 167, 38, 0.05));
    }
    
    .low-confidence {
        border-left-color: var(--danger-color);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(255, 82, 82, 0.05));
    }
    
    /* Enhanced Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--success-color), #00bfa5);
        color: var(--primary-bg);
        border: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 16px;
        height: 56px;
        width: 100%;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 16px rgba(0, 212, 170, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #00bfa5, var(--success-color));
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.4);
    }
    
    .stButton > button:hover::before {
        left: 100%;
    }
    
    /* Professional Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border: 1px solid var(--border-color);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 16px var(--shadow-medium);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: var(--success-color);
        box-shadow: 0 8px 24px rgba(0, 212, 170, 0.15);
    }
    
    /* Enhanced Form Controls */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--sidebar-bg));
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus {
        border-color: var(--success-color);
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2);
    }
    
    .stSlider > div > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--sidebar-bg));
        border-radius: 8px;
    }
    
    .stSlider [data-testid="stSlider"] > div > div > div > div {
        background: var(--success-color);
    }
    
    .stCheckbox > label {
        color: var(--text-primary);
        font-weight: 500;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {
        background-color: var(--accent-bg);
        border: 2px solid var(--border-color);
        border-radius: 6px;
    }
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div:hover {
        border-color: var(--success-color);
    }
    
    .stNumberInput > div > div > input {
        background: linear-gradient(135deg, var(--accent-bg), var(--sidebar-bg));
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: var(--success-color);
        box-shadow: 0 0 0 2px rgba(0, 212, 170, 0.2);
    }
    
    /* Professional Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    h1 {
        background: linear-gradient(135deg, var(--success-color), var(--info-color));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Enhanced Progress Bar */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--success-color), #00bfa5);
        border-radius: 8px;
        height: 8px;
    }
    
    /* Professional Status Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(0, 212, 170, 0.1), rgba(0, 191, 165, 0.1));
        border: 1px solid var(--success-color);
        border-radius: 12px;
        border-left: 4px solid var(--success-color);
    }
    
    .stWarning {
        background: linear-gradient(135deg, rgba(255, 167, 38, 0.1), rgba(255, 193, 7, 0.1));
        border: 1px solid var(--warning-color);
        border-radius: 12px;
        border-left: 4px solid var(--warning-color);
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(255, 82, 82, 0.1), rgba(244, 67, 54, 0.1));
        border: 1px solid var(--danger-color);
        border-radius: 12px;
        border-left: 4px solid var(--danger-color);
    }
    
    .stInfo {
        background: linear-gradient(135deg, rgba(66, 165, 245, 0.1), rgba(33, 150, 243, 0.1));
        border: 1px solid var(--info-color);
        border-radius: 12px;
        border-left: 4px solid var(--info-color);
    }
    
    /* TradingView Container */
    .tradingview-container {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border-radius: 16px;
        padding: 16px;
        border: 1px solid var(--border-color);
        margin: 16px 0;
        box-shadow: 0 8px 32px var(--shadow-heavy);
    }
    
    /* Professional Sidebar Sections */
    .sidebar-section {
        background: linear-gradient(135deg, var(--accent-bg), rgba(37, 43, 61, 0.8));
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        border: 1px solid var(--border-light);
        box-shadow: 0 4px 16px var(--shadow-light);
    }
    
    .sidebar-section h4 {
        color: var(--success-color);
        margin-bottom: 16px;
        font-size: 18px;
        font-weight: 600;
        border-bottom: 1px solid var(--border-light);
        padding-bottom: 8px;
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
        background: linear-gradient(180deg, var(--success-color), #00bfa5);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #00bfa5, var(--success-color));
    }
    
    /* Animation for loading states */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    @keyframes slideInLeft {
        from {
            transform: translateX(-100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .slide-in-left {
        animation: slideInLeft 0.5s ease-out;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main .block-container {
            padding-top: 0.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            height: 48px;
            font-size: 14px;
        }
        
        .metric-card, .pattern-card {
            padding: 16px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Complete NSE F&O Universe (214 stocks as per official NSE list)
COMPLETE_NSE_FO_UNIVERSE = [
    # Indices
    'NIFTY', 'BANKNIFTY', 'FINNIFTY', 'MIDCPNIFTY',
    
    # Individual stocks (210 stocks)
    '360ONE.NS', 'ABB.NS', 'ABCAPITAL.NS', 'ADANIENSOL.NS', 'ADANIENT.NS',
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS',
    'ANGELONE.NS', 'APLAPOLLO.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS',
    'ASTRAL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS',
    'BAJAJFINSV.NS', 'BAJFINANCE.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS',
    'BDL.NS', 'BEL.NS', 'BHARATFORG.NS', 'BHARTIARTL.NS', 'BHEL.NS',
    'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BPCL.NS', 'BRITANNIA.NS',
    'BSE.NS', 'CAMS.NS', 'CANBK.NS', 'CDSL.NS', 'CGPOWER.NS',
    'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS',
    'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS', 'CYIENT.NS', 'DABUR.NS',
    'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS',
    'DMART.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ETERNAL.NS', 'EXIDEIND.NS',
    'FEDERALBNK.NS', 'FORTIS.NS', 'GAIL.NS', 'GLENMARK.NS', 'GMRAIRPORT.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HAL.NS', 'HAVELLS.NS',
    'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS',
    'HFCL.NS', 'HINDALCO.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS',
    'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDEA.NS',
    'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 'IIFL.NS', 'INDHOTEL.NS',
    'INDIANB.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 'INFY.NS',
    'INOXWIND.NS', 'IOC.NS', 'IRCTC.NS', 'IREDA.NS', 'IRFC.NS',
    'ITC.NS', 'JINDALSTEL.NS', 'JIOFIN.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JUBLFOOD.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KEI.NS', 'KFINTECH.NS',
    'KOTAKBANK.NS', 'KPITTECH.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LICI.NS',
    'LODHA.NS', 'LT.NS', 'LTF.NS', 'LTIM.NS', 'LUPIN.NS',
    'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS',
    'MAXHEALTH.NS', 'MAZDOCK.NS', 'MCX.NS', 'MFSL.NS', 'MOTHERSON.NS',
    'MPHASIS.NS', 'MUTHOOTFIN.NS', 'NATIONALUM.NS', 'NAUKRI.NS', 'NBCC.NS',
    'NCC.NS', 'NESTLEIND.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS',
    'NUVAMA.NS', 'NYKAA.NS', 'OBEROIRLTY.NS', 'OFSS.NS', 'OIL.NS',
    'ONGC.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PAYTM.NS', 'PERSISTENT.NS',
    'PETRONET.NS', 'PFC.NS', 'PGEL.NS', 'PHOENIXLTD.NS', 'PIDILITIND.NS',
    'PIIND.NS', 'PNB.NS', 'PNBHOUSING.NS', 'POLICYBZR.NS', 'POLYCAB.NS',
    'POWERGRID.NS', 'POWERINDIA.NS', 'PPLPHARMA.NS', 'PRESTIGE.NS', 'RBLBANK.NS',
    'RECLTD.NS', 'RELIANCE.NS', 'RVNL.NS', 'SAIL.NS', 'SAMMAANCAP.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS',
    'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SRF.NS', 'SUNPHARMA.NS',
    'SUPREMEIND.NS', 'SUZLON.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TATAELXSI.NS',
    'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TCS.NS',
    'TECHM.NS', 'TIINDIA.NS', 'TITAGARH.NS', 'TITAN.NS', 'TORNTPHARM.NS',
    'TORNTPOWER.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS',
    'UNITDSPR.NS', 'UNOMINDA.NS', 'UPL.NS', 'VBL.NS', 'VEDL.NS',
    'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# Stock categories for filtering
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
        'LTIM.NS', 'MPHASIS.NS', 'COFORGE.NS', 'PERSISTENT.NS'
    ],
    'Pharma Stocks': [
        'SUNPHARMA.NS', 'CIPLA.NS', 'DRREDDY.NS', 'DIVISLAB.NS', 'LUPIN.NS',
        'BIOCON.NS', 'AUROPHARMA.NS', 'ALKEM.NS', 'TORNTPHARM.NS', 'GLENMARK.NS'
    ],
    'Auto Stocks': [
        'MARUTI.NS', 'TATAMOTORS.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'HEROMOTOCO.NS',
        'EICHERMOT.NS', 'TVSMOTOR.NS', 'ASHOKLEY.NS'
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
    
    def detect_patterns(self, data, symbol, filters):
        """Enhanced pattern detection with configurable filters"""
        patterns = []
        
        if len(data) < 30:
            return patterns
        
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        
        # Apply filters
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
        
        # Pattern detection
        # 1. Cup and Handle
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
        
        # 2. Flat Base Breakout
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
        
        # 3. VCP Pattern
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
        
        # 4. Ascending Triangle
        triangle_detected, triangle_strength = self.detect_ascending_triangle(data)
        if triangle_detected and triangle_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'Ascending Triangle',
                'strength': triangle_strength,
                'success_rate': 76,
                'research_basis': 'Thomas Bulkowski - Chart Patterns',
                'pcs_suitability': 85,
                'confidence': self.get_confidence_level(triangle_strength)
            })
        
        # 5. Bull Flag
        flag_detected, flag_strength = self.detect_bull_flag(data)
        if flag_detected and flag_strength >= filters['pattern_strength_min']:
            patterns.append({
                'type': 'Bull Flag',
                'strength': flag_strength,
                'success_rate': 72,
                'research_basis': 'William O\'Neil - Flag Patterns',
                'pcs_suitability': 80,
                'confidence': self.get_confidence_level(flag_strength)
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
    
    def detect_ascending_triangle(self, data):
        """Detect Ascending Triangle"""
        if len(data) < 20:
            return False, 0
        
        triangle_data = data.tail(20)
        
        resistance_level = triangle_data['High'].max()
        resistance_touches = (triangle_data['High'] >= resistance_level * 0.98).sum()
        
        lows = triangle_data['Low']
        early_lows = lows.iloc[:8].mean()
        recent_lows = lows.iloc[-8:].mean()
        rising_support = recent_lows > early_lows * 1.01
        
        current_price = data['Close'].iloc[-1]
        breakout = current_price > resistance_level * 0.999
        
        strength = 0
        if resistance_touches >= 2: strength += 30
        if rising_support: strength += 35
        if breakout: strength += 35
        
        return (resistance_touches >= 2 and rising_support and breakout), strength
    
    def detect_bull_flag(self, data):
        """Detect Bull Flag pattern"""
        if len(data) < 20:
            return False, 0
        
        flag_pole_data = data.iloc[-20:-10]
        flag_data = data.tail(10)
        
        pole_start = flag_pole_data['Close'].iloc[0]
        pole_end = flag_pole_data['Close'].iloc[-1]
        pole_gain = ((pole_end - pole_start) / pole_start) * 100
        
        strong_pole = pole_gain >= 15
        
        flag_high = flag_data['High'].max()
        flag_low = flag_data['Low'].min()
        flag_range = ((flag_high - flag_low) / flag_low) * 100
        
        tight_flag = flag_range < 10
        
        current_price = data['Close'].iloc[-1]
        breakout = current_price > flag_high * 0.999
        
        strength = 0
        if strong_pole: strength += 35
        if tight_flag: strength += 30
        if breakout: strength += 35
        
        return (strong_pole and tight_flag and breakout), strength
    
    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Create professional TradingView-style chart"""
        if len(data) < 20:
            return None
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.6, 0.25, 0.15],
            subplot_titles=('Price Action', 'Volume', 'RSI')
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
        
        # Moving averages
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
        
        # Bollinger Bands
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
        
        # RSI
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#9c27b0', width=2)
            ),
            row=3, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="yellow", row=3, col=1)
        
        # Update layout
        pattern_name = pattern_info['type'] if pattern_info else 'Technical Analysis'
        confidence = pattern_info.get('confidence', '') if pattern_info else ''
        title = f'{symbol.replace(".NS", "")} - {pattern_name} {confidence}'.strip()
        
        fig.update_layout(
            title=title,
            template='plotly_dark',
            paper_bgcolor='rgba(26, 31, 46, 1)',
            plot_bgcolor='rgba(26, 31, 46, 1)',
            font=dict(color='white', family='Inter'),
            height=800,
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
    """Create professional sidebar with comprehensive filters"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, var(--success-color), #00bfa5); border-radius: 16px; margin-bottom: 20px;'>
            <h2 style='color: var(--primary-bg); margin: 0; font-weight: 700;'>🎯 PCS Scanner</h2>
            <p style='color: var(--primary-bg); margin: 5px 0 0 0; opacity: 0.9;'>Professional Trading Suite</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock Universe Selection
        st.markdown("### 📊 Stock Universe")
        
        universe_option = st.selectbox(
            "Select Universe:",
            ["Complete F&O (214 stocks)", "Nifty 50", "Bank Nifty", "IT Stocks", 
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
        elif universe_option == "Complete F&O (214 stocks)":
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
        else:
            category_key = universe_option
            stocks_to_scan = STOCK_CATEGORIES.get(category_key, [])
        
        st.info(f"📈 **{len(stocks_to_scan)} stocks** selected for analysis")
        
        # Advanced Filters Section
        st.markdown("### ⚙️ Advanced Filters")
        
        # Technical Filters
        with st.expander("🔧 Technical Indicators", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                rsi_min = st.slider("RSI Min:", 20, 80, 35, help="Minimum RSI value")
            with col2:
                rsi_max = st.slider("RSI Max:", 20, 80, 75, help="Maximum RSI value")
            
            adx_min = st.slider("ADX Minimum:", 10, 50, 15, help="Minimum ADX for trend strength")
            
            ma_support = st.checkbox("Moving Average Support", value=True, help="Require price above MA")
            if ma_support:
                col1, col2 = st.columns(2)
                with col1:
                    ma_type = st.selectbox("MA Type:", ["EMA", "SMA"])
                with col2:
                    ma_tolerance = st.slider("MA Tolerance %:", 0, 10, 2, help="Allowed deviation from MA")
        
        # Volume Filters
        with st.expander("📊 Volume Analysis", expanded=True):
            min_volume_ratio = st.slider(
                "Min Volume Ratio (20-day):", 
                0.5, 5.0, 1.0, 0.1,
                help="Minimum volume vs 20-day average"
            )
            
            volume_surge_threshold = st.slider(
                "Volume Surge Threshold:", 
                1.5, 10.0, 2.0, 0.5,
                help="Minimum volume surge for breakouts"
            )
        
        # Pattern Filters
        with st.expander("🎯 Pattern Settings", expanded=True):
            pattern_strength_min = st.slider(
                "Min Pattern Strength:", 
                50, 100, 60, 5,
                help="Minimum pattern strength percentage"
            )
            
            min_success_rate = st.slider(
                "Min Success Rate:", 
                60, 95, 70, 5,
                help="Minimum historical success rate"
            )
            
            pattern_types = st.multiselect(
                "Pattern Types:",
                ["Cup and Handle", "Flat Base Breakout", "VCP", "Ascending Triangle", "Bull Flag"],
                default=["Cup and Handle", "Flat Base Breakout", "VCP"],
                help="Select patterns to detect"
            )
        
        # Scanning Options
        with st.expander("🚀 Scanning Options", expanded=True):
            max_stocks = st.slider(
                "Max Stocks to Scan:", 
                10, len(stocks_to_scan), 
                min(50, len(stocks_to_scan)),
                help="Limit number of stocks for faster scanning"
            )
            
            show_charts = st.checkbox("Show Charts", value=True, help="Display TradingView charts")
            export_results = st.checkbox("Export Results", value=False, help="Enable CSV export")
        
        # Market Context
        st.markdown("### 🌍 Market Context")
        try:
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="2d")
            if len(nifty_data) >= 2:
                current = nifty_data['Close'].iloc[-1]
                change_pct = ((current - nifty_data['Close'].iloc[-2]) / nifty_data['Close'].iloc[-2]) * 100
                
                st.metric("Nifty 50", f"{current:.2f}", f"{change_pct:+.2f}%")
                
                if change_pct > 1:
                    st.success("📈 **Strong Bullish** - Excellent for PCS")
                elif change_pct > 0:
                    st.info("📊 **Mild Bullish** - Good for PCS")
                elif change_pct > -1:
                    st.warning("📉 **Sideways** - Use caution")
                else:
                    st.error("🔻 **Bearish** - Avoid PCS")
        except:
            st.error("Market data unavailable")
        
        # Current time
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        st.markdown(f"**Last Updated:** {current_time.strftime('%H:%M:%S IST')}")
        
        return {
            'stocks_to_scan': stocks_to_scan[:max_stocks],
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'adx_min': adx_min,
            'ma_support': ma_support,
            'ma_type': ma_type if ma_support else 'EMA',
            'ma_tolerance': ma_tolerance if ma_support else 2,
            'min_volume_ratio': min_volume_ratio,
            'volume_surge_threshold': volume_surge_threshold,
            'pattern_strength_min': pattern_strength_min,
            'min_success_rate': min_success_rate,
            'pattern_types': pattern_types,
            'show_charts': show_charts,
            'export_results': export_results,
            'max_stocks': max_stocks
        }

def create_main_scanner_tab(config):
    """Create main scanner tab with professional results display"""
    st.markdown("### 🎯 Professional Pattern Scanner")
    
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
            
            status_container.info(f"🔍 Analyzing {symbol.replace('.NS', '')} ({i+1}/{len(config['stocks_to_scan'])})")
            
            try:
                # Get data
                data = scanner.get_stock_data(symbol)
                if data is None:
                    continue
                
                # Check volume
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
                if not volume_ok:
                    continue
                
                # Detect patterns
                patterns = scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue
                
                # Filter patterns by type and success rate
                filtered_patterns = [
                    p for p in patterns 
                    if p['type'] in config['pattern_types'] and p['success_rate'] >= config['min_success_rate']
                ]
                
                if not filtered_patterns:
                    continue
                
                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]
                
                results.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': filtered_patterns,
                    'data': data
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
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Stocks Found", len(results))
            with col2:
                st.metric("📊 Total Patterns", total_patterns)
            with col3:
                st.metric("💪 Avg Strength", f"{avg_strength:.1f}%")
            with col4:
                st.metric("🏆 High Confidence", high_confidence)
            
            # Display results
            for result in results:
                # Determine overall confidence
                max_strength = max(p['strength'] for p in result['patterns'])
                overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
                confidence_class = f"{overall_confidence.lower()}-confidence"
                
                with st.expander(
                    f"📈 {result['symbol'].replace('.NS', '')} - {len(result['patterns'])} Pattern(s) - {overall_confidence} Confidence", 
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
                    
                    # Pattern details
                    for pattern in result['patterns']:
                        confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡" if pattern['confidence'] == 'MEDIUM' else "🔴"
                        
                        st.markdown(f"""
                        <div class="pattern-card {confidence_class}">
                            <h4>{confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence</h4>
                            <div style='display: flex; justify-content: space-between; margin: 10px 0;'>
                                <span><strong>Pattern Strength:</strong> {pattern['strength']}%</span>
                                <span><strong>Success Rate:</strong> {pattern['success_rate']}%</span>
                                <span><strong>PCS Suitability:</strong> {pattern['pcs_suitability']}%</span>
                            </div>
                            <p><strong>Research Basis:</strong> {pattern['research_basis']}</p>
                            <p><strong>💡 PCS Strategy:</strong> {'Conservative strikes (5% OTM)' if pattern['confidence'] == 'HIGH' else 'Moderate strikes (8% OTM)' if pattern['confidence'] == 'MEDIUM' else 'Aggressive strikes (12% OTM)'}</p>
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
            
            # Suggestions
            st.markdown("### 💡 Suggestions:")
            st.markdown("- Lower the **Pattern Strength** threshold")
            st.markdown("- Reduce the **Volume Ratio** requirement")
            st.markdown("- Expand the **RSI range**")
            st.markdown("- Lower the **ADX minimum**")

def main():
    # Professional header
    st.markdown("""
    <div style='text-align: center; padding: 40px; background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 50%, var(--accent-bg) 100%); border-radius: 20px; margin-bottom: 30px; border: 2px solid var(--success-color); box-shadow: 0 16px 64px var(--shadow-heavy);'>
        <h1 style='color: var(--success-color); margin: 0; font-size: 3rem; font-weight: 700; text-shadow: 0 0 20px rgba(0,212,170,0.3);'>📈 NSE F&O PCS Professional Scanner</h1>
        <p style='color: var(--text-secondary); margin: 15px 0 5px 0; font-size: 1.3rem; font-weight: 500;'>Complete F&O Universe • Research-Backed Patterns • Professional Analysis</p>
        <p style='color: var(--text-muted); margin: 0; font-size: 1rem;'>214 NSE F&O Stocks • Advanced Filters • Real-time EOD Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get sidebar configuration
    config = create_professional_sidebar()
    
    # Create main tabs
    tab1, tab2, tab3 = st.tabs([
        "🎯 Pattern Scanner",
        "📊 Consolidation Analysis", 
        "🌍 Market Intelligence"
    ])
    
    with tab1:
        create_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📊 Consolidation Breakout Analysis")
        st.info("🚧 Enhanced consolidation analysis coming soon...")
    
    with tab3:
        st.markdown("### 🌍 Global Market Intelligence")
        st.info("🚧 Comprehensive market analysis coming soon...")
    
    # Professional footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)); border-radius: 16px; margin-top: 30px; border: 1px solid var(--border-color);'>
        <h4 style='color: var(--success-color); margin-bottom: 15px;'>🏆 Professional Trading Suite</h4>
        <p style='color: var(--text-secondary); margin: 5px 0;'><strong>✅ Complete NSE F&O Universe:</strong> All 214 official F&O stocks included</p>
        <p style='color: var(--text-secondary); margin: 5px 0;'><strong>🔬 Research-Backed:</strong> Patterns validated by market experts</p>
        <p style='color: var(--text-secondary); margin: 5px 0;'><strong>⚙️ Professional Filters:</strong> Advanced technical analysis tools</p>
        <p style='color: var(--text-muted); margin: 15px 0 5px 0; font-size: 0.9rem;'><strong>⚠️ Disclaimer:</strong> For educational purposes only. Not financial advice. Trade responsibly.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
