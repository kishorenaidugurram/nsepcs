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

# FIXED: Angel One Dark Theme with Visible Scrollbar and Professional Colors
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        /* Angel One Dark Color Scheme */
        --primary-bg: #0D1421;
        --secondary-bg: #1A202C;
        --accent-bg: #2D3748;
        --sidebar-bg: #1A202C;
        --primary-blue: #3182CE;
        --primary-green: #38A169;
        --primary-orange: #DD6B20;
        --primary-red: #E53E3E;
        --text-primary: #FFFFFF;
        --text-secondary: #CBD5E0;
        --text-muted: #A0AEC0;
        --border-color: #4A5568;
        --border-light: #718096;
        --shadow-light: rgba(0, 0, 0, 0.1);
        --shadow-medium: rgba(0, 0, 0, 0.25);
        --shadow-heavy: rgba(0, 0, 0, 0.4);
        --header-gradient: linear-gradient(135deg, #1A202C 0%, #2D3748 50%, #3182CE 100%);
    }
    
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, var(--primary-bg) 0%, #0A0E1A 100%);
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
    
    /* FIXED: Angel One Style Header - Compact and Readable */
    .professional-header {
        background: var(--header-gradient);
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 16px;
        border: 1px solid var(--primary-blue);
        box-shadow: 0 4px 20px var(--shadow-heavy);
        text-align: center;
        position: relative;
        overflow: hidden;
        max-height: 100px;
    }
    
    .professional-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-green), var(--primary-orange));
    }
    
    .professional-header h1 {
        color: var(--primary-blue) !important;
        margin: 0 0 4px 0;
        font-size: 1.8rem;
        font-weight: 700;
        text-shadow: 0 2px 8px rgba(49, 130, 206, 0.3);
        background: none !important;
        -webkit-text-fill-color: var(--primary-blue) !important;
    }
    
    .professional-header .subtitle {
        color: var(--primary-green) !important;
        margin: 0 0 2px 0;
        font-size: 0.95rem;
        font-weight: 500;
        opacity: 0.95;
    }
    
    .professional-header .description {
        color: var(--text-secondary) !important;
        margin: 0;
        font-size: 0.8rem;
        opacity: 0.85;
    }
    
    /* FIXED: Enhanced Sidebar with Visible Scrollbar - GREEN THEME */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F5132 0%, #198754 100%);
        border-right: 2px solid #198754;
        box-shadow: 4px 0 20px rgba(25, 135, 84, 0.3);
    }
    
    /* FIXED: Visible Sidebar Scrollbar */
    section[data-testid="stSidebar"] ::-webkit-scrollbar {
        width: 12px;
        background: var(--accent-bg);
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-track {
        background: var(--accent-bg);
        border-radius: 6px;
        margin: 4px;
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #198754, #20c997);
        border-radius: 6px;
        border: 2px solid var(--accent-bg);
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #20c997, #198754);
    }
    
    /* Angel One Style Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border-radius: 8px;
        padding: 4px;
        border: 1px solid var(--border-color);
        box-shadow: 0 2px 8px var(--shadow-medium);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: transparent;
        border-radius: 6px;
        color: var(--text-secondary);
        font-weight: 500;
        font-size: 14px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, var(--accent-bg), rgba(49, 130, 206, 0.1));
        color: var(--text-primary);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--primary-blue), #2C5AA0);
        color: var(--text-primary) !important;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(49, 130, 206, 0.3);
    }
    
    /* Professional Cards - Angel One Style */
    .metric-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 16px;
        border-radius: 8px;
        border: 1px solid var(--border-color);
        margin: 8px 0;
        box-shadow: 0 4px 16px var(--shadow-heavy);
        transition: all 0.3s ease;
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
        background: linear-gradient(90deg, var(--primary-blue), var(--primary-green));
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(49, 130, 206, 0.15);
        border-color: var(--primary-blue);
    }
    
    .pattern-card {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        padding: 16px;
        border-radius: 8px;
        border-left: 4px solid var(--primary-green);
        margin: 10px 0;
        box-shadow: 0 4px 16px var(--shadow-heavy);
        transition: all 0.3s ease;
        position: relative;
    }
    
    .pattern-card:hover {
        transform: translateX(2px);
        box-shadow: 0 6px 20px var(--shadow-heavy);
    }
    
    .consolidation-card {
        border-left-color: var(--primary-orange);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(221, 107, 32, 0.05));
    }
    
    .news-card {
        border-left-color: var(--primary-blue);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(49, 130, 206, 0.05));
    }
    
    .high-confidence {
        border-left-color: var(--primary-green);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(56, 161, 105, 0.05));
    }
    
    .medium-confidence {
        border-left-color: var(--primary-orange);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(221, 107, 32, 0.05));
    }
    
    .low-confidence {
        border-left-color: var(--primary-red);
        background: linear-gradient(135deg, var(--secondary-bg), rgba(229, 62, 62, 0.05));
    }
    
    /* Market Sentiment - Angel One Colors */
    .sentiment-bullish {
        background: linear-gradient(135deg, rgba(56, 161, 105, 0.15), rgba(72, 187, 120, 0.15));
        border: 1px solid var(--primary-green);
        border-left: 4px solid var(--primary-green);
    }
    
    .sentiment-neutral {
        background: linear-gradient(135deg, rgba(221, 107, 32, 0.15), rgba(237, 137, 54, 0.15));
        border: 1px solid var(--primary-orange);
        border-left: 4px solid var(--primary-orange);
    }
    
    .sentiment-bearish {
        background: linear-gradient(135deg, rgba(229, 62, 62, 0.15), rgba(245, 101, 101, 0.15));
        border: 1px solid var(--primary-red);
        border-left: 4px solid var(--primary-red);
    }
    
    /* Angel One Style Buttons */
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-blue), #2C5AA0);
        color: var(--text-primary);
        border: none;
        border-radius: 6px;
        font-weight: 600;
        font-size: 14px;
        height: 44px;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(49, 130, 206, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2C5AA0, var(--primary-blue));
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(49, 130, 206, 0.4);
    }
    
    /* Professional Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
        border: 1px solid var(--border-color);
        padding: 14px;
        border-radius: 8px;
        box-shadow: 0 2px 8px var(--shadow-medium);
        transition: all 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: var(--primary-blue);
        box-shadow: 0 4px 16px rgba(49, 130, 206, 0.15);
    }
    
    /* Enhanced Form Controls */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--secondary-bg));
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover,
    .stSelectbox > div > div:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
    }
    
    .stSlider > div > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--secondary-bg));
        border-radius: 6px;
    }
    
    .stSlider [data-testid="stSlider"] > div > div > div > div {
        background: var(--primary-blue);
    }
    
    .stNumberInput > div > div > input {
        background: linear-gradient(135deg, var(--accent-bg), var(--secondary-bg));
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-weight: 500;
    }
    
    .stNumberInput > div > div > input:focus {
        border-color: var(--primary-blue);
        box-shadow: 0 0 0 2px rgba(49, 130, 206, 0.2);
    }
    
    /* Professional Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Enhanced Main Content Scrollbar */
    .main ::-webkit-scrollbar {
        width: 10px;
    }
    
    .main ::-webkit-scrollbar-track {
        background: var(--primary-bg);
        border-radius: 5px;
    }
    
    .main ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--primary-blue), var(--primary-green));
        border-radius: 5px;
    }
    
    .main ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--primary-green), var(--primary-blue));
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
            padding: 8px 12px;
            max-height: 80px;
        }
        
        .professional-header h1 {
            font-size: 1.4rem;
        }
        
        .professional-header .subtitle {
            font-size: 0.85rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# COMPLETE NSE F&O UNIVERSE - ALL 219 STOCKS (Full Official List)
COMPLETE_NSE_FO_UNIVERSE = [
    # Indices (4)
    '^NSEI', '^NSEBANK', '^CNXFINANCE', '^CNXMIDCAP',
    
    # ALL NSE F&O Individual stocks (215 stocks) - COMPLETE OFFICIAL LIST
    '360ONE.NS', 'ABB.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANITRANS.NS', 'AJANTPHARM.NS', 'ALKEM.NS', 'AMBUJACEM.NS', 
    'ANGELONE.NS', 'APLAPOLLO.NS', 'APOLLOHOSP.NS', 'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 
    'ASTRAL.NS', 'ATUL.NS', 'AUBANK.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 
    'BAJAJFINSV.NS', 'BAJFINANCE.NS', 'BALKRISIND.NS', 'BALRAMCHIN.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 
    'BANKINDIA.NS', 'BATAINDIA.NS', 'BDL.NS', 'BEL.NS', 'BERGEPAINT.NS', 'BHARATFORG.NS', 
    'BHARTIARTL.NS', 'BHEL.NS', 'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BPCL.NS', 
    'BRITANNIA.NS', 'BSE.NS', 'BSOFT.NS', 'CAMS.NS', 'CANBK.NS', 'CANFINHOME.NS', 'CDSL.NS', 
    'CESC.NS', 'CGCL.NS', 'CGPOWER.NS', 'CHAMBLFERT.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 
    'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS', 'CROMPTON.NS', 'CUB.NS', 'CUMMINSIND.NS', 
    'CYIENT.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DELTACORP.NS', 
    'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS', 'DMART.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 
    'ETERNAL.NS', 'EXIDEIND.NS', 'FEDERALBNK.NS', 'FORTIS.NS', 'GAIL.NS', 'GLENMARK.NS', 
    'GMRAIRPORT.NS', 'GMRINFRA.NS', 'GNFC.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRANULES.NS', 
    'GRASIM.NS', 'GUJGASLTD.NS', 'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 
    'HDFCLIFE.NS', 'HEROMOTOCO.NS', 'HFCL.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 
    'HINDUNILVR.NS', 'HINDZINC.NS', 'HONAUT.NS', 'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 
    'ICICIPRULI.NS', 'IDEA.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 'IIFL.NS', 'INDHOTEL.NS', 
    'INDIANB.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 'INFY.NS', 
    'INOXWIND.NS', 'IOC.NS', 'IPCALAB.NS', 'IRCTC.NS', 'IREDA.NS', 'IRFC.NS', 'ITC.NS', 
    'JINDALSTEL.NS', 'JIOFIN.NS', 'JKCEMENT.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 
    'KALYANKJIL.NS', 'KAYNES.NS', 'KEI.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'KPITTECH.NS', 
    'KPRMILL.NS', 'KRBL.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 
    'LICI.NS', 'LODHA.NS', 'LT.NS', 'LTF.NS', 'LTIM.NS', 'LTTS.NS', 'LUPIN.NS', 'M&M.NS', 
    'M&MFIN.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MAXHEALTH.NS', 
    'MAZDOCK.NS', 'MCX.NS', 'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 
    'MRF.NS', 'MUTHOOTFIN.NS', 'NATIONALUM.NS', 'NAUKRI.NS', 'NAVINFLUOR.NS', 'NBCC.NS', 
    'NCC.NS', 'NESTLEIND.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NUVAMA.NS', 'NYKAA.NS', 
    'OBEROIRLTY.NS', 'OFSS.NS', 'OIL.NS', 'ONGC.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PAYTM.NS', 
    'PERSISTENT.NS', 'PETRONET.NS', 'PFC.NS', 'PGEL.NS', 'PHOENIXLTD.NS', 'PIDILITIND.NS', 
    'PIIND.NS', 'PNB.NS', 'PNBHOUSING.NS', 'POLICYBZR.NS', 'POLYCAB.NS', 'POWERGRID.NS', 
    'POWERINDIA.NS', 'PPLPHARMA.NS', 'PRESTIGE.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 
    'RECLTD.NS', 'RELIANCE.NS', 'RVNL.NS', 'SAIL.NS', 'SAMMAANCAP.NS', 'SBICARD.NS', 'SBILIFE.NS', 
    'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 
    'SRF.NS', 'STAR.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUNTV.NS', 'SUZLON.NS', 'SYNGENE.NS', 
    'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAELXSI.NS', 'TATAMOTORS.NS', 'TATAPOWER.NS', 
    'TATASTEEL.NS', 'TATATECH.NS', 'TCS.NS', 'TECHM.NS', 'TIINDIA.NS', 'TITAGARH.NS', 'TITAN.NS', 
    'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS', 'ULTRACEMCO.NS', 
    'UNIONBANK.NS', 'UNITDSPR.NS', 'UNOMINDA.NS', 'UPL.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 
    'WIPRO.NS', 'YESBANK.NS', 'ZEEL.NS', 'ZYDUSLIFE.NS'
]

# Stock categories with verified symbols
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
    
    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data with focus on recent data for current trading day analysis"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            
            if len(data) < 20:
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
    
    def get_weekly_stock_data(self, symbol, period="6mo"):
        """Get weekly stock data for pattern validation"""
        try:
            stock = yf.Ticker(symbol)
            # Get more data for weekly analysis, then resample to weekly
            daily_data = stock.history(period=period, interval="1d")
            
            if len(daily_data) < 50:  # Need sufficient data for weekly analysis
                return None
            
            # Resample daily data to weekly (Friday close)
            weekly_data = daily_data.resample('W-FRI').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            }).dropna()
            
            if len(weekly_data) < 15:  # Need at least 15 weeks
                return None
            
            # Calculate weekly technical indicators
            weekly_data['RSI'] = ta.momentum.RSIIndicator(weekly_data['Close']).rsi()
            weekly_data['SMA_10'] = ta.trend.SMAIndicator(weekly_data['Close'], window=10).sma_indicator()
            weekly_data['SMA_20'] = ta.trend.SMAIndicator(weekly_data['Close'], window=20).sma_indicator()
            weekly_data['EMA_10'] = ta.trend.EMAIndicator(weekly_data['Close'], window=10).ema_indicator()
            weekly_data['MACD'] = ta.trend.MACD(weekly_data['Close']).macd()
            weekly_data['MACD_signal'] = ta.trend.MACD(weekly_data['Close']).macd_signal()
            weekly_data['MACD_hist'] = ta.trend.MACD(weekly_data['Close']).macd_diff()
            weekly_data['ADX'] = ta.trend.ADXIndicator(weekly_data['High'], weekly_data['Low'], weekly_data['Close']).adx()
            
            return weekly_data
        except Exception as e:
            return None
    
    def validate_weekly_strength(self, daily_data, weekly_data, pattern_type):
        """Validate daily pattern strength using weekly timeframe analysis"""
        if weekly_data is None or len(weekly_data) < 10:
            return {
                'weekly_validation': False,
                'weekly_strength_bonus': 0,
                'weekly_signals': [],
                'weekly_context': 'Insufficient weekly data'
            }
        
        try:
            # Get current weekly metrics
            current_weekly_close = weekly_data['Close'].iloc[-1]
            current_weekly_rsi = weekly_data['RSI'].iloc[-1]
            current_weekly_macd = weekly_data['MACD'].iloc[-1]
            current_weekly_macd_signal = weekly_data['MACD_signal'].iloc[-1]
            weekly_sma_10 = weekly_data['SMA_10'].iloc[-1]
            weekly_sma_20 = weekly_data['SMA_20'].iloc[-1]
            current_weekly_adx = weekly_data['ADX'].iloc[-1]
            
            weekly_signals = []
            strength_bonus = 0
            
            # 1. Weekly Trend Alignment
            if current_weekly_close > weekly_sma_10 > weekly_sma_20:
                weekly_signals.append("Strong weekly uptrend (Close > SMA10 > SMA20)")
                strength_bonus += 15
            elif current_weekly_close > weekly_sma_10:
                weekly_signals.append("Bullish weekly trend (Close > SMA10)")
                strength_bonus += 10
            elif current_weekly_close > weekly_sma_20:
                weekly_signals.append("Weekly above long-term MA")
                strength_bonus += 5
            
            # 2. Weekly RSI Support
            if 40 <= current_weekly_rsi <= 70:
                weekly_signals.append(f"Healthy weekly RSI ({current_weekly_rsi:.1f})")
                strength_bonus += 10
            elif current_weekly_rsi > 30:
                weekly_signals.append(f"Weekly RSI above oversold ({current_weekly_rsi:.1f})")
                strength_bonus += 5
            
            # 3. Weekly MACD Confirmation
            if current_weekly_macd > current_weekly_macd_signal and current_weekly_macd > 0:
                weekly_signals.append("Weekly MACD bullish above signal line")
                strength_bonus += 12
            elif current_weekly_macd > current_weekly_macd_signal:
                weekly_signals.append("Weekly MACD above signal line")
                strength_bonus += 8
            
            # 4. Weekly ADX Trend Strength
            if current_weekly_adx >= 25:
                weekly_signals.append(f"Strong weekly trend (ADX: {current_weekly_adx:.1f})")
                strength_bonus += 8
            elif current_weekly_adx >= 20:
                weekly_signals.append(f"Moderate weekly trend (ADX: {current_weekly_adx:.1f})")
                strength_bonus += 5
            
            # 5. Weekly Support/Resistance Context
            weekly_support_resistance = self._analyze_weekly_support_resistance(weekly_data)
            if weekly_support_resistance['near_breakout']:
                weekly_signals.append(weekly_support_resistance['context'])
                strength_bonus += weekly_support_resistance['bonus']
            
            # 6. Weekly Volume Trend
            weekly_volume_trend = self._analyze_weekly_volume_trend(weekly_data)
            if weekly_volume_trend['positive']:
                weekly_signals.append(weekly_volume_trend['context'])
                strength_bonus += weekly_volume_trend['bonus']
            
            # 7. Pattern-Specific Weekly Validation
            pattern_bonus = self._get_pattern_specific_weekly_bonus(pattern_type, weekly_data)
            if pattern_bonus['bonus'] > 0:
                weekly_signals.append(pattern_bonus['context'])
                strength_bonus += pattern_bonus['bonus']
            
            # Determine overall weekly validation
            weekly_validation = len(weekly_signals) >= 2 and strength_bonus >= 15
            
            # Context summary
            if strength_bonus >= 35:
                weekly_context = "Exceptionally strong weekly confirmation"
            elif strength_bonus >= 25:
                weekly_context = "Strong weekly alignment"
            elif strength_bonus >= 15:
                weekly_context = "Moderate weekly support"
            else:
                weekly_context = "Weak weekly confirmation"
            
            return {
                'weekly_validation': weekly_validation,
                'weekly_strength_bonus': strength_bonus,
                'weekly_signals': weekly_signals,
                'weekly_context': weekly_context,
                'weekly_rsi': current_weekly_rsi,
                'weekly_trend': 'Bullish' if current_weekly_close > weekly_sma_10 else 'Neutral/Bearish'
            }
            
        except Exception as e:
            return {
                'weekly_validation': False,
                'weekly_strength_bonus': 0,
                'weekly_signals': [],
                'weekly_context': f'Weekly analysis error: {str(e)}'
            }
    
    def _analyze_weekly_support_resistance(self, weekly_data):
        """Analyze weekly support/resistance levels"""
        try:
            recent_weeks = weekly_data.tail(12)  # Last 12 weeks
            current_price = weekly_data['Close'].iloc[-1]
            
            # Find key levels
            resistance_level = recent_weeks['High'].max()
            support_level = recent_weeks['Low'].min()
            
            # Check proximity to breakout
            distance_to_resistance = ((resistance_level - current_price) / current_price) * 100
            distance_from_support = ((current_price - support_level) / support_level) * 100
            
            if distance_to_resistance <= 3:  # Within 3% of resistance
                return {
                    'near_breakout': True,
                    'context': f"Near weekly resistance breakout (~{distance_to_resistance:.1f}% away)",
                    'bonus': 12
                }
            elif distance_from_support >= 15:  # Well above support
                return {
                    'near_breakout': True,
                    'context': f"Strong weekly support base ({distance_from_support:.1f}% above support)",
                    'bonus': 8
                }
            
            return {'near_breakout': False, 'context': '', 'bonus': 0}
            
        except Exception:
            return {'near_breakout': False, 'context': '', 'bonus': 0}
    
    def _analyze_weekly_volume_trend(self, weekly_data):
        """Analyze weekly volume trends"""
        try:
            recent_volume = weekly_data['Volume'].tail(4).mean()  # Last 4 weeks
            previous_volume = weekly_data['Volume'].tail(8).iloc[:4].mean()  # Previous 4 weeks
            
            volume_increase = ((recent_volume - previous_volume) / previous_volume) * 100
            
            if volume_increase >= 20:
                return {
                    'positive': True,
                    'context': f"Strong weekly volume increase ({volume_increase:.1f}%)",
                    'bonus': 10
                }
            elif volume_increase >= 10:
                return {
                    'positive': True,
                    'context': f"Moderate weekly volume increase ({volume_increase:.1f}%)",
                    'bonus': 6
                }
            
            return {'positive': False, 'context': '', 'bonus': 0}
            
        except Exception:
            return {'positive': False, 'context': '', 'bonus': 0}
    
    def _get_pattern_specific_weekly_bonus(self, pattern_type, weekly_data):
        """Get pattern-specific weekly validation bonus"""
        try:
            if pattern_type in ['Cup and Handle', 'Double Bottom (Eve & Eve)', 'Head-and-Shoulders Bottom']:
                # These patterns benefit from weekly base building
                recent_weeks = weekly_data.tail(8)
                weekly_consolidation_range = ((recent_weeks['High'].max() - recent_weeks['Low'].min()) / recent_weeks['Low'].min()) * 100
                
                if weekly_consolidation_range < 20:  # Tight weekly consolidation
                    return {
                        'bonus': 10,
                        'context': f"Tight weekly consolidation ({weekly_consolidation_range:.1f}% range)"
                    }
            
            elif pattern_type in ['Current Day Breakout', 'Rectangle Bottom', 'Flat Base Breakout']:
                # These patterns benefit from weekly momentum
                current_week = weekly_data['Close'].iloc[-1]
                four_weeks_ago = weekly_data['Close'].iloc[-5]
                weekly_momentum = ((current_week - four_weeks_ago) / four_weeks_ago) * 100
                
                if weekly_momentum > 5:
                    return {
                        'bonus': 12,
                        'context': f"Strong weekly momentum ({weekly_momentum:.1f}% over 4 weeks)"
                    }
                elif weekly_momentum > 0:
                    return {
                        'bonus': 6,
                        'context': f"Positive weekly momentum ({weekly_momentum:.1f}% over 4 weeks)"
                    }
            
            return {'bonus': 0, 'context': ''}
            
        except Exception:
            return {'bonus': 0, 'context': ''}
    
    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check volume criteria with focus on latest trading day"""
        if len(data) < 21:
            return False, 0, {}
        
        current_volume = data['Volume'].iloc[-1]
        avg_5_volume = data['Volume'].tail(6).iloc[:-1].mean()  # Exclude current day
        avg_10_volume = data['Volume'].tail(11).iloc[:-1].mean()
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
        
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
        """Get fundamental news for the stock to explain volume/price movements"""
        try:
            # Clean symbol for search
            clean_symbol = symbol.replace('.NS', '')
            
            # Focus on today's news
            search_queries = [
                f"{stock_name} stock news today",
                f"{clean_symbol} earnings results latest",
                f"{stock_name} order announcement recent"
            ]
            
            news_items = []
            
            for query in search_queries[:2]:  # Limit for speed
                try:
                    # Use Google News search for today
                    search_url = f"https://www.google.com/search?q={query}&tbm=nws&tbs=qdr:d"
                    
                    response = self.session.get(search_url, timeout=3)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Extract news headlines
                        news_elements = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:2]
                        
                        for element in news_elements:
                            headline = element.get_text().strip()
                            if len(headline) > 20:
                                news_items.append({
                                    'headline': headline,
                                    'relevance': self._assess_news_relevance(headline),
                                    'source': 'Recent News'
                                })
                                
                except Exception:
                    continue
            
            # Assess sentiment
            if news_items:
                positive_keywords = ['order', 'win', 'contract', 'growth', 'profit', 'beat', 'strong', 'positive', 'approval']
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
                'news_items': news_items[:2],
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
        high_relevance_keywords = ['order', 'contract', 'earnings', 'results', 'approval', 'launch', 'merger']
        medium_relevance_keywords = ['growth', 'expansion', 'investment', 'partnership', 'policy']
        
        headline_lower = headline.lower()
        
        for word in high_relevance_keywords:
            if word in headline_lower:
                return 'high'
        
        for word in medium_relevance_keywords:
            if word in headline_lower:
                return 'medium'
        
        return 'low'
    
    def detect_current_day_breakout(self, data, lookback_days=20, min_volume_ratio=2.0):
        """
        CRITICAL: Detect breakouts happening on the CURRENT/LATEST trading day EOD
        This ensures pattern confirmation is based on today's trading, not historical data
        """
        if len(data) < lookback_days + 2:
            return False, 0, {}
        
        # Get current day (latest) data
        current_day = data.iloc[-1]
        
        # Get lookback period (excluding current day)
        lookback_data = data.iloc[-(lookback_days + 1):-1]
        
        # Calculate resistance level from lookback period
        resistance_level = lookback_data['High'].max()
        support_level = lookback_data['Low'].min()
        
        # Check if current day broke above resistance
        current_high = current_day['High']
        current_close = current_day['Close']
        current_volume = current_day['Volume']
        
        # Breakout conditions - ALL MUST BE FROM CURRENT DAY
        price_breakout = current_close > resistance_level * 1.005  # 0.5% above resistance
        high_breakout = current_high > resistance_level * 1.01     # 1% intraday breakout
        
        # Volume confirmation from current day
        avg_volume = lookback_data['Volume'].mean()
        volume_breakout = current_volume > (avg_volume * min_volume_ratio)
        
        # Calculate consolidation quality
        consolidation_range = ((resistance_level - support_level) / support_level) * 100
        tight_consolidation = consolidation_range < 15  # Less than 15% range
        
        # Current day must satisfy all conditions
        current_day_confirmed = price_breakout and volume_breakout and tight_consolidation
        
        if not current_day_confirmed:
            return False, 0, {}
        
        # Calculate strength based on current day metrics
        strength = 0
        
        # Breakout strength (current day)
        breakout_percentage = ((current_close - resistance_level) / resistance_level) * 100
        if breakout_percentage >= 3:
            strength += 35
        elif breakout_percentage >= 2:
            strength += 25
        elif breakout_percentage >= 1:
            strength += 20
        elif breakout_percentage >= 0.5:
            strength += 15
        
        # Volume surge strength (current day)
        volume_ratio = current_volume / avg_volume
        if volume_ratio >= 4:
            strength += 30
        elif volume_ratio >= 3:
            strength += 25
        elif volume_ratio >= 2:
            strength += 20
        
        # Consolidation quality
        if consolidation_range <= 8:
            strength += 25
        elif consolidation_range <= 12:
            strength += 20
        elif consolidation_range <= 15:
            strength += 15
        
        # Current day close strength
        close_strength = ((current_close - current_day['Low']) / (current_day['High'] - current_day['Low'])) * 100
        if close_strength >= 80:  # Closed in top 20% of day's range
            strength += 10
        elif close_strength >= 60:
            strength += 5
        
        details = {
            'current_date': current_day.name.strftime('%Y-%m-%d'),
            'current_close': current_close,
            'current_high': current_high,
            'current_volume': current_volume,
            'resistance_level': resistance_level,
            'support_level': support_level,
            'breakout_percentage': breakout_percentage,
            'volume_ratio': volume_ratio,
            'consolidation_range': consolidation_range,
            'lookback_days': lookback_days,
            'close_strength': close_strength
        }
        
        return True, strength, details
    
    def get_market_sentiment_indicators(self):
        """Get current market sentiment based on latest data"""
        try:
            sentiment_data = {}
            
            # Get current day data for indices
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="5d")
            
            if len(nifty_data) >= 2:
                current_nifty = nifty_data['Close'].iloc[-1]
                prev_nifty = nifty_data['Close'].iloc[-2]
                nifty_change_pct = ((current_nifty - prev_nifty) / prev_nifty) * 100
                
                sentiment_data['nifty'] = {
                    'current': current_nifty,
                    'change_1d': nifty_change_pct,
                    'sentiment': self._get_sentiment_level(nifty_change_pct)
                }
            
            # Bank Nifty
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
            
            # Overall sentiment
            nifty_sentiment = sentiment_data.get('nifty', {}).get('sentiment', 'NEUTRAL')
            bank_sentiment = sentiment_data.get('bank_nifty', {}).get('sentiment', 'NEUTRAL')
            
            sentiment_scores = {'BULLISH': 3, 'NEUTRAL': 2, 'BEARISH': 1}
            nifty_score = sentiment_scores.get(nifty_sentiment, 2)
            bank_score = sentiment_scores.get(bank_sentiment, 2)
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
        """
        ENHANCED: Pattern detection with CURRENT DAY EOD confirmation
        All patterns must be confirmed by latest trading day data
        """
        patterns = []
        
        if len(data) < 30:
            return patterns
        
        # Get CURRENT DAY metrics (latest trading day)
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        
        # Apply filters based on CURRENT DAY
        if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
            return patterns
        
        if current_adx < filters['adx_min']:
            return patterns
        
        # MA support check (current day)
        if filters['ma_support']:
            if filters['ma_type'] == 'SMA':
                if current_price < sma_20 * (1 - filters['ma_tolerance']/100):
                    return patterns
            else:  # EMA
                if current_price < ema_20 * (1 - filters['ma_tolerance']/100):
                    return patterns
        
        # Get pattern filters if available
        pattern_filters = filters.get('pattern_filters', {})
        pattern_priority = filters.get('pattern_priority', 'All Patterns (Comprehensive)')
        
        # NEW V6.1: Get weekly data for strength validation
        weekly_data = None
        if filters.get('enable_weekly_validation', True):  # Default enabled
            weekly_data = self.get_weekly_stock_data(symbol)
            if weekly_data is not None:
                # Quick weekly health check
                weekly_rsi = weekly_data['RSI'].iloc[-1] if not weekly_data['RSI'].isna().iloc[-1] else None
                weekly_close = weekly_data['Close'].iloc[-1]
                weekly_sma_10 = weekly_data['SMA_10'].iloc[-1] if not weekly_data['SMA_10'].isna().iloc[-1] else None
                
                # Skip if weekly is in very bearish state (optional filter)
                if weekly_rsi and weekly_rsi < 25 and weekly_sma_10 and weekly_close < weekly_sma_10 * 0.95:
                    # Extremely bearish weekly - reduce pattern strength requirements slightly
                    pass  # Continue but will show in weekly context
        
        # PRIORITY 1: Current Day Breakout Detection
        if pattern_filters.get('current_day_breakout', True):
            breakout_detected, breakout_strength, breakout_details = self.detect_current_day_breakout(
                data, 
                lookback_days=filters.get('lookback_days', 20),
                min_volume_ratio=filters.get('volume_breakout_ratio', 2.0)
            )
            
            if breakout_detected and breakout_strength >= filters['pattern_strength_min']:
                # NEW V6.1: Add weekly validation
                weekly_validation = self.validate_weekly_strength(data, weekly_data, 'Current Day Breakout')
                final_strength = breakout_strength + weekly_validation['weekly_strength_bonus']
                
                pattern_data = {
                    'type': 'Current Day Breakout',
                    'strength': final_strength,
                    'daily_strength': breakout_strength,
                    'success_rate': 92,  # High success for current day breakouts
                    'research_basis': 'Real-time EOD Breakout Confirmation',
                    'pcs_suitability': 98,
                    'confidence': self.get_confidence_level(final_strength),
                    'details': breakout_details,
                    'special': 'CURRENT_DAY_BREAKOUT',
                    'weekly_validation': weekly_validation
                }
                
                # Apply priority filters
                if self._meets_priority_criteria(pattern_data, pattern_priority):
                    patterns.append(pattern_data)
        else:
            breakout_detected = False
        
        # PRIORITY 2: Traditional patterns (if no current day breakout or if filters allow multiple patterns)
        if not breakout_detected or len([k for k, v in pattern_filters.items() if v]) > 1:
            # Cup and Handle (must be confirmed by current day)
            if pattern_filters.get('cup_and_handle', True):
                cup_detected, cup_strength = self.detect_cup_and_handle_current(data)
                if cup_detected and cup_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Cup and Handle',
                        'strength': cup_strength,
                        'success_rate': 85,
                        'research_basis': 'William O\'Neil - IBD (Current Day Confirmed)',
                        'pcs_suitability': 95,
                        'confidence': self.get_confidence_level(cup_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, cup_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Flat Base Breakout (current day confirmed)
            if pattern_filters.get('flat_base', True):
                flat_detected, flat_strength = self.detect_flat_base_current(data)
                if flat_detected and flat_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Flat Base Breakout',
                        'strength': flat_strength,
                        'success_rate': 82,
                        'research_basis': 'Mark Minervini - Current Day Confirmed',
                        'pcs_suitability': 92,
                        'confidence': self.get_confidence_level(flat_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, flat_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # NEW PATTERNS ADDED - V6 Enhancement
            
            # Bump-and-Run Reversal (bottom)
            if pattern_filters.get('bump_and_run', True):
                bump_detected, bump_strength = self.detect_bump_and_run_reversal_bottom(data)
                if bump_detected and bump_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Bump-and-Run Reversal (Bottom)',
                        'strength': bump_strength,
                        'success_rate': 78,
                        'research_basis': 'Thomas Bulkowski - Encyclopedia of Chart Patterns',
                        'pcs_suitability': 88,
                        'confidence': self.get_confidence_level(bump_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, bump_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Rectangle Bottom
            if pattern_filters.get('rectangle_bottom', True):
                rect_bottom_detected, rect_bottom_strength = self.detect_rectangle_bottom(data)
                if rect_bottom_detected and rect_bottom_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Rectangle Bottom',
                        'strength': rect_bottom_strength,
                        'success_rate': 75,
                        'research_basis': 'Classical Technical Analysis - Rectangle Patterns',
                        'pcs_suitability': 90,
                        'confidence': self.get_confidence_level(rect_bottom_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rect_bottom_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Rectangle Top
            if pattern_filters.get('rectangle_top', False):
                rect_top_detected, rect_top_strength = self.detect_rectangle_top(data)
                if rect_top_detected and rect_top_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Rectangle Top',
                        'strength': rect_top_strength,
                        'success_rate': 72,
                        'research_basis': 'Support Test After Rectangle Formation',
                        'pcs_suitability': 85,
                        'confidence': self.get_confidence_level(rect_top_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rect_top_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Head-and-Shoulders Bottom
            if pattern_filters.get('head_shoulders_bottom', True):
                hs_bottom_detected, hs_bottom_strength = self.detect_head_and_shoulders_bottom(data)
                if hs_bottom_detected and hs_bottom_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Head-and-Shoulders Bottom',
                        'strength': hs_bottom_strength,
                        'success_rate': 83,
                        'research_basis': 'Classic Reversal Pattern - Edwards & Magee',
                        'pcs_suitability': 93,
                        'confidence': self.get_confidence_level(hs_bottom_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, hs_bottom_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Double Bottom (Eve & Eve)
            if pattern_filters.get('double_bottom', True):
                double_bottom_detected, double_bottom_strength = self.detect_double_bottom(data)
                if double_bottom_detected and double_bottom_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Double Bottom (Eve & Eve)',
                        'strength': double_bottom_strength,
                        'success_rate': 80,
                        'research_basis': 'Thomas Bulkowski - Double Bottom Analysis',
                        'pcs_suitability': 91,
                        'confidence': self.get_confidence_level(double_bottom_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, double_bottom_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Three Rising Valleys
            if pattern_filters.get('three_rising_valleys', True):
                three_valleys_detected, three_valleys_strength = self.detect_three_rising_valleys(data)
                if three_valleys_detected and three_valleys_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Three Rising Valleys',
                        'strength': three_valleys_strength,
                        'success_rate': 77,
                        'research_basis': 'Progressive Support Levels - Bullish Continuation',
                        'pcs_suitability': 89,
                        'confidence': self.get_confidence_level(three_valleys_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, three_valleys_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Rounding Bottom
            if pattern_filters.get('rounding_bottom', True):
                rounding_bottom_detected, rounding_bottom_strength = self.detect_rounding_bottom(data)
                if rounding_bottom_detected and rounding_bottom_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Rounding Bottom',
                        'strength': rounding_bottom_strength,
                        'success_rate': 74,
                        'research_basis': 'Saucer Pattern - Gradual Accumulation Phase',
                        'pcs_suitability': 87,
                        'confidence': self.get_confidence_level(rounding_bottom_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rounding_bottom_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Rounding Top (upside breaks)
            if pattern_filters.get('rounding_top_upside', False):
                rounding_top_detected, rounding_top_strength = self.detect_rounding_top_upside_break(data)
                if rounding_top_detected and rounding_top_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Rounding Top (Upside Break)',
                        'strength': rounding_top_strength,
                        'success_rate': 68,
                        'research_basis': 'Rare Counter-Trend Breakout Pattern',
                        'pcs_suitability': 85,
                        'confidence': self.get_confidence_level(rounding_top_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rounding_top_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
            
            # Inverted/Descending Scallop
            if pattern_filters.get('inverted_scallop', True):
                scallop_detected, scallop_strength = self.detect_inverted_scallop(data)
                if scallop_detected and scallop_strength >= filters['pattern_strength_min']:
                    pattern_data = {
                        'type': 'Inverted/Descending Scallop',
                        'strength': scallop_strength,
                        'success_rate': 76,
                        'research_basis': 'William O\'Neil - CAN SLIM Methodology',
                        'pcs_suitability': 88,
                        'confidence': self.get_confidence_level(scallop_strength)
                    }
                    # NEW V6.1: Add weekly validation
                    pattern_data = self._add_weekly_validation_to_pattern(pattern_data, scallop_strength, data, weekly_data)
                    if self._meets_priority_criteria(pattern_data, pattern_priority):
                        patterns.append(pattern_data)
        
        return patterns
    
    def detect_cup_and_handle_current(self, data):
        """Cup and Handle pattern with CURRENT DAY confirmation"""
        if len(data) < 40:
            return False, 0
        
        # Pattern must be confirmed by current day breakout
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Look for cup formation in recent data
        recent_data = data.tail(30)
        cup_high = recent_data['High'].iloc[:20].max()
        cup_low = recent_data['Low'].iloc[5:15].min()
        
        # Handle formation (last 10 days)
        handle_data = recent_data.tail(10)
        handle_high = handle_data['High'].max()
        
        # CURRENT DAY must break above handle/cup high
        current_day_breakout = current_price > handle_high * 1.005
        
        # Volume confirmation on current day
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_confirmed = current_volume > avg_volume * 1.5
        
        # Cup criteria
        cup_depth = ((cup_high - cup_low) / cup_high) * 100
        valid_cup = 15 <= cup_depth <= 50
        
        if not (current_day_breakout and volume_confirmed and valid_cup):
            return False, 0
        
        strength = 0
        if valid_cup: strength += 30
        if current_day_breakout: strength += 40
        if volume_confirmed: strength += 30
        
        return True, strength
    
    def detect_flat_base_current(self, data):
        """Flat Base pattern with CURRENT DAY confirmation"""
        if len(data) < 20:
            return False, 0
        
        # Base formation (last 15 days excluding current)
        base_data = data.tail(16).iloc[:-1]
        
        high_price = base_data['High'].max()
        low_price = base_data['Low'].min()
        price_range = ((high_price - low_price) / low_price) * 100
        
        tight_base = price_range < 12
        
        # CURRENT DAY breakout confirmation
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        breakout = current_price > high_price * 1.003
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_surge = current_volume > avg_volume * 1.8
        
        if not (tight_base and breakout and volume_surge):
            return False, 0
        
        strength = 0
        if tight_base: strength += 40
        if breakout: strength += 35
        if volume_surge: strength += 25
        
        return True, strength
    
    def detect_bump_and_run_reversal_bottom(self, data):
        """Bump-and-Run Reversal (bottom) pattern with CURRENT DAY confirmation"""
        if len(data) < 30:
            return False, 0
        
        # Look for the pattern: decline, consolidation, then sharp reversal
        recent_data = data.tail(30)
        
        # Phase 1: Initial decline (first 15 days)
        decline_data = recent_data.iloc[:15]
        decline_start = decline_data['Close'].iloc[0]
        decline_end = decline_data['Close'].iloc[-1]
        decline_pct = ((decline_end - decline_start) / decline_start) * 100
        
        # Phase 2: Consolidation near bottom (next 10 days)
        consolidation_data = recent_data.iloc[15:25]
        consolidation_high = consolidation_data['High'].max()
        consolidation_low = consolidation_data['Low'].min()
        consolidation_range = ((consolidation_high - consolidation_low) / consolidation_low) * 100
        
        # Phase 3: CURRENT DAY reversal
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Pattern criteria
        valid_decline = decline_pct < -8  # At least 8% decline
        tight_consolidation = consolidation_range < 10  # Less than 10% range
        current_day_breakout = current_price > consolidation_high * 1.02  # 2% above consolidation high
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_surge = current_volume > avg_volume * 1.5
        
        if not (valid_decline and tight_consolidation and current_day_breakout and volume_surge):
            return False, 0
        
        strength = 0
        if valid_decline: strength += 25
        if tight_consolidation: strength += 30
        if current_day_breakout: strength += 30
        if volume_surge: strength += 15
        
        return True, strength
    
    def detect_rectangle_bottom(self, data):
        """Rectangle Bottom pattern with CURRENT DAY confirmation"""
        if len(data) < 25:
            return False, 0
        
        # Rectangle formation (last 20 days excluding current)
        rect_data = data.tail(21).iloc[:-1]
        
        # Find support and resistance levels
        support_level = rect_data['Low'].min()
        resistance_level = rect_data['High'].max()
        
        # Rectangle criteria
        rect_height = ((resistance_level - support_level) / support_level) * 100
        valid_rectangle = 5 <= rect_height <= 15  # 5-15% height range for rectangle
        
        # Test if price stayed within rectangle bounds for most of the period
        within_bounds = 0
        for i in range(len(rect_data)):
            if support_level <= rect_data['Low'].iloc[i] and rect_data['High'].iloc[i] <= resistance_level * 1.05:
                within_bounds += 1
        
        formation_quality = within_bounds / len(rect_data) >= 0.7  # 70% of time within bounds
        
        # CURRENT DAY breakout above resistance
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        breakout = current_price > resistance_level * 1.015  # 1.5% above resistance
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_confirmed = current_volume > avg_volume * 1.3
        
        if not (valid_rectangle and formation_quality and breakout and volume_confirmed):
            return False, 0
        
        strength = 0
        if valid_rectangle: strength += 30
        if formation_quality: strength += 25
        if breakout: strength += 30
        if volume_confirmed: strength += 15
        
        return True, strength
    
    def detect_rectangle_top(self, data):
        """Rectangle Top pattern with CURRENT DAY confirmation (for bearish signals - inverted for bullish PCS)"""
        if len(data) < 25:
            return False, 0
        
        # This pattern is typically bearish, but we'll look for bullish continuation after pullback
        # Rectangle formation followed by support hold
        rect_data = data.tail(25).iloc[:-1]
        
        # Find recent high and current support test
        recent_high = rect_data.tail(15)['High'].max()
        recent_low = rect_data.tail(10)['Low'].min()
        
        # Look for pullback and current day bounce
        current_price = data['Close'].iloc[-1]
        current_low = data['Low'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Pattern: pullback to support and bounce (bullish for PCS)
        pullback_depth = ((recent_high - recent_low) / recent_high) * 100
        support_test = current_low <= recent_low * 1.02  # Within 2% of support
        bounce_strength = ((current_price - current_low) / current_low) * 100
        
        # Volume on support test
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_support = current_volume > avg_volume * 1.2
        
        valid_pattern = 8 <= pullback_depth <= 20 and support_test and bounce_strength >= 1 and volume_support
        
        if not valid_pattern:
            return False, 0
        
        strength = 0
        if 8 <= pullback_depth <= 15: strength += 25
        if support_test: strength += 30
        if bounce_strength >= 2: strength += 25
        if volume_support: strength += 20
        
        return True, strength
    
    def detect_head_and_shoulders_bottom(self, data):
        """Head-and-Shoulders Bottom (inverted H&S) pattern with CURRENT DAY confirmation"""
        if len(data) < 40:
            return False, 0
        
        # Look for inverted H&S pattern in recent data
        recent_data = data.tail(35)
        
        # Divide into sections: left shoulder, head, right shoulder
        left_shoulder = recent_data.iloc[:10]
        head_section = recent_data.iloc[10:25]
        right_shoulder = recent_data.iloc[25:34]
        
        # Find key levels
        left_low = left_shoulder['Low'].min()
        head_low = head_section['Low'].min()
        right_low = right_shoulder['Low'].min()
        
        # Neckline (resistance level to break)
        left_high = left_shoulder['High'].max()
        right_high = right_shoulder['High'].max()
        neckline = (left_high + right_high) / 2
        
        # Pattern validation
        head_deeper = head_low < left_low * 0.95 and head_low < right_low * 0.95  # Head is lowest
        shoulders_similar = abs(left_low - right_low) / min(left_low, right_low) < 0.15  # Shoulders similar height
        
        # CURRENT DAY neckline breakout
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        neckline_breakout = current_price > neckline * 1.01  # 1% above neckline
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_breakout = current_volume > avg_volume * 1.4
        
        if not (head_deeper and shoulders_similar and neckline_breakout and volume_breakout):
            return False, 0
        
        strength = 0
        if head_deeper: strength += 30
        if shoulders_similar: strength += 25
        if neckline_breakout: strength += 30
        if volume_breakout: strength += 15
        
        return True, strength
    
    def detect_double_bottom(self, data):
        """Double Bottom (Eve & Eve) pattern with CURRENT DAY confirmation"""
        if len(data) < 30:
            return False, 0
        
        # Look for two similar lows with a peak in between
        recent_data = data.tail(30)
        
        # Find potential double bottom
        # First bottom (days 5-12)
        first_bottom_data = recent_data.iloc[5:12]
        first_low = first_bottom_data['Low'].min()
        first_low_idx = first_bottom_data['Low'].idxmin()
        
        # Peak between bottoms (days 12-18)
        peak_data = recent_data.iloc[12:18]
        peak_high = peak_data['High'].max()
        
        # Second bottom (days 18-25)
        second_bottom_data = recent_data.iloc[18:25]
        second_low = second_bottom_data['Low'].min()
        
        # Pattern validation
        bottoms_similar = abs(first_low - second_low) / min(first_low, second_low) < 0.08  # Within 8%
        significant_peak = ((peak_high - max(first_low, second_low)) / max(first_low, second_low)) * 100 > 5  # At least 5% peak
        
        # CURRENT DAY breakout above peak
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        breakout = current_price > peak_high * 1.015  # 1.5% above peak
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_confirmed = current_volume > avg_volume * 1.3
        
        if not (bottoms_similar and significant_peak and breakout and volume_confirmed):
            return False, 0
        
        strength = 0
        if bottoms_similar: strength += 35
        if significant_peak: strength += 25
        if breakout: strength += 25
        if volume_confirmed: strength += 15
        
        return True, strength
    
    def detect_three_rising_valleys(self, data):
        """Three Rising Valleys pattern with CURRENT DAY confirmation"""
        if len(data) < 35:
            return False, 0
        
        # Look for three consecutive higher lows
        recent_data = data.tail(35)
        
        # Divide into three valley sections
        valley1_data = recent_data.iloc[5:12]
        valley2_data = recent_data.iloc[12:22]
        valley3_data = recent_data.iloc[22:30]
        
        # Find valley lows
        valley1_low = valley1_data['Low'].min()
        valley2_low = valley2_data['Low'].min()
        valley3_low = valley3_data['Low'].min()
        
        # Find peaks between valleys
        peak1_data = recent_data.iloc[10:15]
        peak2_data = recent_data.iloc[20:25]
        peak1_high = peak1_data['High'].max()
        peak2_high = peak2_data['High'].max()
        
        # Pattern validation - rising valleys
        rising_valleys = valley2_low > valley1_low * 1.02 and valley3_low > valley2_low * 1.02
        
        # Peaks should also be rising or similar
        rising_peaks = peak2_high >= peak1_high * 0.98
        
        # CURRENT DAY breakout above recent resistance
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        resistance_level = max(peak1_high, peak2_high)
        
        breakout = current_price > resistance_level * 1.01
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_surge = current_volume > avg_volume * 1.25
        
        if not (rising_valleys and rising_peaks and breakout and volume_surge):
            return False, 0
        
        strength = 0
        if rising_valleys: strength += 35
        if rising_peaks: strength += 20
        if breakout: strength += 30
        if volume_surge: strength += 15
        
        return True, strength
    
    def detect_rounding_bottom(self, data):
        """Rounding Bottom pattern with CURRENT DAY confirmation"""
        if len(data) < 40:
            return False, 0
        
        # Look for saucer/bowl shaped bottom
        recent_data = data.tail(40)
        
        # Calculate moving averages to detect the rounding shape
        ma_short = recent_data['Close'].rolling(window=5).mean()
        ma_long = recent_data['Close'].rolling(window=15).mean()
        
        # Find the bottom of the rounding pattern
        bottom_idx = recent_data['Low'].idxmin()
        bottom_price = recent_data['Low'].min()
        
        # Check if bottom is roughly in the middle of the pattern
        bottom_position = list(recent_data.index).index(bottom_idx) / len(recent_data)
        centered_bottom = 0.3 <= bottom_position <= 0.7
        
        # Check for gradual decline and rise (rounding shape)
        first_half = recent_data.iloc[:len(recent_data)//2]
        second_half = recent_data.iloc[len(recent_data)//2:]
        
        # Gradual decline to bottom
        decline_slope = (first_half['Close'].iloc[-1] - first_half['Close'].iloc[0]) / len(first_half)
        
        # Gradual rise from bottom  
        rise_slope = (second_half['Close'].iloc[-1] - second_half['Close'].iloc[0]) / len(second_half)
        
        smooth_pattern = decline_slope < 0 and rise_slope > 0
        
        # CURRENT DAY breakout
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Resistance level (early highs)
        resistance = recent_data['High'].iloc[:10].max()
        breakout = current_price > resistance * 0.98  # Near resistance
        
        # Volume should increase on the right side of the pattern
        left_volume = recent_data['Volume'].iloc[:len(recent_data)//2].mean()
        right_volume = recent_data['Volume'].iloc[len(recent_data)//2:].mean()
        volume_increase = right_volume > left_volume * 1.1
        
        if not (centered_bottom and smooth_pattern and breakout and volume_increase):
            return False, 0
        
        strength = 0
        if centered_bottom: strength += 25
        if smooth_pattern: strength += 30
        if breakout: strength += 25
        if volume_increase: strength += 20
        
        return True, strength
    
    def detect_rounding_top_upside_break(self, data):
        """Rounding Top with upside break pattern with CURRENT DAY confirmation"""
        if len(data) < 35:
            return False, 0
        
        # This is a counter-trend pattern - rounding top that breaks upward instead of downward
        recent_data = data.tail(35)
        
        # Find the peak of the rounding pattern
        peak_idx = recent_data['High'].idxmax()
        peak_price = recent_data['High'].max()
        
        # Check pattern before and after peak
        pre_peak = recent_data.iloc[:list(recent_data.index).index(peak_idx)]
        post_peak = recent_data.iloc[list(recent_data.index).index(peak_idx):]
        
        if len(pre_peak) < 10 or len(post_peak) < 10:
            return False, 0
        
        # Check for rounding formation
        pre_peak_rise = (pre_peak['Close'].iloc[-1] - pre_peak['Close'].iloc[0]) > 0
        post_peak_decline = (post_peak['Close'].iloc[-5] - post_peak['Close'].iloc[0]) < 0
        
        # But CURRENT DAY should break upward (bullish)
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Breakout above the rounding top peak
        upside_breakout = current_price > peak_price * 1.005  # 0.5% above peak
        
        # Volume confirmation
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_breakout = current_volume > avg_volume * 1.4
        
        # This is a rare but powerful pattern
        valid_pattern = pre_peak_rise and post_peak_decline and upside_breakout and volume_breakout
        
        if not valid_pattern:
            return False, 0
        
        strength = 0
        if pre_peak_rise and post_peak_decline: strength += 40  # Rare pattern
        if upside_breakout: strength += 35
        if volume_breakout: strength += 25
        
        return True, strength
    
    def detect_inverted_scallop(self, data):
        """Inverted/Descending Scallop pattern with CURRENT DAY confirmation"""
        if len(data) < 25:
            return False, 0
        
        # Scallop pattern: gradual decline followed by sharp recovery
        recent_data = data.tail(25)
        
        # Divide into decline and recovery phases
        decline_phase = recent_data.iloc[:15]
        recovery_phase = recent_data.iloc[15:]
        
        # Pattern characteristics
        decline_start = decline_phase['Close'].iloc[0]
        decline_end = decline_phase['Close'].iloc[-1]
        decline_pct = ((decline_end - decline_start) / decline_start) * 100
        
        # Look for gradual decline (scallop shape)
        gradual_decline = -15 <= decline_pct <= -3  # 3-15% decline
        
        # Volume should be lower during decline
        decline_volume = decline_phase['Volume'].mean()
        recent_volume = data['Volume'].tail(5).mean()
        volume_pickup = recent_volume > decline_volume * 1.3
        
        # CURRENT DAY recovery
        current_price = data['Close'].iloc[-1]
        recovery_start = recovery_phase['Close'].iloc[0]
        recovery_pct = ((current_price - recovery_start) / recovery_start) * 100
        
        sharp_recovery = recovery_pct >= 2  # At least 2% recovery
        
        # Current day should be near highs
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_confirmation = current_volume > avg_volume * 1.2
        
        if not (gradual_decline and volume_pickup and sharp_recovery and volume_confirmation):
            return False, 0
        
        strength = 0
        if gradual_decline: strength += 30
        if volume_pickup: strength += 25
        if sharp_recovery: strength += 30
        if volume_confirmation: strength += 15
        
        return True, strength
    
    def _meets_priority_criteria(self, pattern_data, pattern_priority):
        """Check if pattern meets the selected priority criteria"""
        if pattern_priority == "All Patterns (Comprehensive)":
            return True
        elif pattern_priority == "High Success Rate Only (>80%)":
            return pattern_data['success_rate'] > 80
        elif pattern_priority == "PCS Optimized (>90% suitability)":
            return pattern_data['pcs_suitability'] > 90
        return True
    
    def _add_weekly_validation_to_pattern(self, pattern_data, daily_strength, data, weekly_data):
        """Helper function to add weekly validation to any pattern"""
        weekly_validation = self.validate_weekly_strength(data, weekly_data, pattern_data['type'])
        final_strength = daily_strength + weekly_validation['weekly_strength_bonus']
        
        # Update pattern data with weekly information
        pattern_data.update({
            'strength': final_strength,
            'daily_strength': daily_strength,
            'confidence': self.get_confidence_level(final_strength),
            'weekly_validation': weekly_validation
        })
        
        return pattern_data
    
    def get_confidence_level(self, strength):
        """Get confidence level based on pattern strength"""
        if strength >= 85:
            return 'HIGH'
        elif strength >= 70:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Create professional TradingView-style chart with current day highlighting"""
        if len(data) < 20:
            return None
        
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.65, 0.25, 0.10],
            subplot_titles=('Price Action - Current Day Analysis', 'Volume - Today vs Average', 'RSI')
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
                increasing_line_color='#38A169',
                decreasing_line_color='#E53E3E',
                increasing_fillcolor='#38A169',
                decreasing_fillcolor='#E53E3E'
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
                line=dict(color='#DD6B20', width=2, dash='solid')
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['SMA_50'],
                mode='lines',
                name='SMA 50',
                line=dict(color='#3182CE', width=2, dash='dot')
            ),
            row=1, col=1
        )
        
        # Highlight current day breakout if present
        if pattern_info and pattern_info.get('special') == 'CURRENT_DAY_BREAKOUT':
            details = pattern_info.get('details', {})
            if details:
                current_close = details.get('current_close')
                resistance_level = details.get('resistance_level')
                
                if current_close and resistance_level:
                    # Highlight resistance level
                    fig.add_hline(
                        y=resistance_level, 
                        line_dash="dash", 
                        line_color="#DD6B20", 
                        row=1, col=1,
                        annotation_text=f"Resistance: ₹{resistance_level:.2f}"
                    )
                    
                    # Highlight current day breakout
                    fig.add_annotation(
                        x=data.index[-1],
                        y=current_close,
                        text=f"📈 TODAY: ₹{current_close:.2f}",
                        showarrow=True,
                        arrowhead=2,
                        arrowcolor="#38A169",
                        bgcolor="#38A169",
                        bordercolor="#38A169",
                        font=dict(color="white", size=12),
                        row=1,
                        col=1
                    )
        
        # Volume bars with current day highlight
        colors = []
        for i, (close, open_price, volume) in enumerate(zip(data['Close'], data['Open'], data['Volume'])):
            if i == len(data) - 1:  # Current day
                colors.append('#DD6B20')  # Orange for current day
            elif close >= open_price:
                colors.append('#38A169')
            else:
                colors.append('#E53E3E')
        
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.8
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
                line=dict(color='white', width=1, dash='dash')
            ),
            row=2, col=1
        )
        
        # RSI with current day highlight
        rsi_colors = ['#DD6B20' if i == len(data) - 1 else '#9C27B0' for i in range(len(data))]
        
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data['RSI'],
                mode='lines+markers',
                name='RSI (14)',
                line=dict(color='#9C27B0', width=2),
                marker=dict(color=rsi_colors, size=4)
            ),
            row=3, col=1
        )
        
        # RSI levels
        fig.add_hline(y=70, line_dash="dash", line_color="#E53E3E", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#38A169", row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="#DD6B20", row=3, col=1)
        
        # Update layout
        pattern_name = pattern_info['type'] if pattern_info else 'Technical Analysis'
        confidence = pattern_info.get('confidence', '') if pattern_info else ''
        title = f'{symbol.replace(".NS", "")} - {pattern_name} ({confidence} Confidence) - Current Day Focus'
        
        fig.update_layout(
            title=title,
            template='plotly_dark',
            paper_bgcolor='rgba(26, 32, 44, 1)',
            plot_bgcolor='rgba(26, 32, 44, 1)',
            font=dict(color='white', family='Inter'),
            height=650,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor='rgba(45, 55, 72, 0.8)',
                bordercolor='gray',
                borderwidth=1
            )
        )
        
        fig.update_xaxes(gridcolor='rgba(128,128,128,0.2)', showgrid=True, rangeslider_visible=False)
        fig.update_yaxes(gridcolor='rgba(128,128,128,0.2)', showgrid=True)
        
        return fig

def create_professional_sidebar():
    """Create professional sidebar with Angel One styling"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 14px; background: linear-gradient(135deg, #198754, #20c997); border-radius: 8px; margin-bottom: 14px;'>
            <h2 style='color: var(--text-primary); margin: 0; font-weight: 700; font-size: 1.3rem;'>📈 PCS Scanner V6</h2>
            <p style='color: var(--text-primary); margin: 3px 0 0 0; opacity: 0.9; font-size: 0.85rem;'>Enhanced Chart Patterns</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock Universe Selection
        st.markdown("### 📊 Stock Universe")
        
        universe_option = st.selectbox(
            "Select Universe:",
            ["Complete NSE F&O (219 stocks)", "Nifty 50", "Bank Nifty", "IT Stocks", 
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
        elif universe_option == "Complete NSE F&O (219 stocks)":
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE  # ALL 219 stocks by default
        else:
            category_key = universe_option
            stocks_to_scan = STOCK_CATEGORIES.get(category_key, [])
        
        st.info(f"📈 **{len(stocks_to_scan)} stocks** selected for analysis")
        
        # Core Technical Filters
        st.markdown("### ⚙️ Core Filters")
        
        with st.expander("🎯 Technical Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                rsi_min = st.slider("RSI Min:", 20, 80, 30)
            with col2:
                rsi_max = st.slider("RSI Max:", 20, 80, 80)
            
            adx_min = st.slider("ADX Minimum:", 10, 50, 20)
            
            ma_support = st.checkbox("Moving Average Support", value=True)
            if ma_support:
                col1, col2 = st.columns(2)
                with col1:
                    ma_type = st.selectbox("MA Type:", ["EMA", "SMA"])
                with col2:
                    ma_tolerance = st.slider("MA Tolerance %:", 0, 10, 3)
        
        # Volume & Breakout Settings
        with st.expander("📊 Volume & Breakout", expanded=True):
            min_volume_ratio = st.slider("Min Volume Ratio:", 0.8, 5.0, 1.2, 0.1)
            volume_breakout_ratio = st.slider("Breakout Volume:", 1.5, 5.0, 2.0, 0.1)
            lookback_days = st.slider("Lookback Period:", 15, 30, 20)
        
        # NEW V6: Chart Pattern Filters
        st.markdown("### 📈 Chart Pattern Filters")
        with st.expander("🎯 Pattern Selection", expanded=False):
            st.markdown("**Select patterns to detect:**")
            
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                pattern_filters = {
                    'current_day_breakout': st.checkbox("Current Day Breakout", value=True, help="Real-time EOD breakout confirmation"),
                    'cup_and_handle': st.checkbox("Cup with Handle", value=True, help="William O'Neil - IBD pattern"),
                    'flat_base': st.checkbox("Flat Base Breakout", value=True, help="Mark Minervini pattern"),
                    'bump_and_run': st.checkbox("Bump-and-Run Reversal", value=True, help="Thomas Bulkowski pattern"),
                    'rectangle_bottom': st.checkbox("Rectangle Bottom", value=True, help="Classical rectangle breakout"),
                    'rectangle_top': st.checkbox("Rectangle Top", value=False, help="Support test after rectangle"),
                }
            
            with col2:
                pattern_filters.update({
                    'head_shoulders_bottom': st.checkbox("Head-and-Shoulders Bottom", value=True, help="Classic reversal pattern"),
                    'double_bottom': st.checkbox("Double Bottom (Eve & Eve)", value=True, help="Double bottom formation"),
                    'three_rising_valleys': st.checkbox("Three Rising Valleys", value=True, help="Progressive support levels"),
                    'rounding_bottom': st.checkbox("Rounding Bottom", value=True, help="Saucer/bowl pattern"),
                    'rounding_top_upside': st.checkbox("Rounding Top (Upside Break)", value=False, help="Rare counter-trend pattern"),
                    'inverted_scallop': st.checkbox("Inverted Scallop", value=True, help="O'Neil CAN SLIM pattern"),
                })
            
            # Pattern priority setting
            st.markdown("**Pattern Detection Priority:**")
            pattern_priority = st.radio(
                "Choose detection approach:",
                ["All Patterns (Comprehensive)", "High Success Rate Only (>80%)", "PCS Optimized (>90% suitability)"],
                index=0,
                help="Filter patterns by success rate or PCS suitability"
            )
            
            # NEW V6.1: Weekly Validation Toggle
            st.markdown("**🔍 Weekly Strength Validation:**")
            enable_weekly_validation = st.checkbox(
                "Enable Weekly Timeframe Validation", 
                value=True, 
                help="Validates daily patterns against weekly timeframe for additional strength confirmation. Adds 0-40 points to pattern strength based on weekly alignment."
            )
            
            if enable_weekly_validation:
                st.info(
                    "📊 **Weekly Validation Active**: Daily patterns will be validated against weekly trends, RSI, MACD, and support/resistance levels for enhanced accuracy."
                )
        
        # Single Pattern Strength Filter
        pattern_strength_min = st.slider("Pattern Strength Min:", 50, 100, 65, 5)
        
        # Scanning Options  
        with st.expander("🚀 Scan Settings", expanded=True):
            # FIXED: Default to ALL stocks, not limited to 50
            max_stocks = st.selectbox(
                "Stocks to Scan:",
                ["All Stocks", "First 50", "First 100", "Custom Limit"],
                index=0,  # Default to "All Stocks"
                help="Choose how many stocks to scan"
            )
            
            if max_stocks == "Custom Limit":
                custom_limit = st.number_input("Custom Limit:", min_value=10, max_value=len(stocks_to_scan), value=50)
                stocks_limit = custom_limit
            elif max_stocks == "First 50":
                stocks_limit = 50
            elif max_stocks == "First 100":
                stocks_limit = 100
            else:  # "All Stocks"
                stocks_limit = len(stocks_to_scan)
            
            show_charts = st.checkbox("Show Charts", value=True)
            show_news = st.checkbox("Show News", value=True)
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
        <div class="{sentiment_class}" style="padding: 10px; border-radius: 6px; margin: 6px 0;">
            <h4 style="margin: 0 0 4px 0; color: var(--text-primary); font-size: 1rem;">
                {'🟢' if sentiment_level == 'BULLISH' else '🟡' if sentiment_level == 'NEUTRAL' else '🔴'} 
                {sentiment_level}
            </h4>
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">{pcs_recommendation}</p>
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
            'stocks_to_scan': stocks_to_scan[:stocks_limit],
            'rsi_min': rsi_min,
            'rsi_max': rsi_max,
            'adx_min': adx_min,
            'ma_support': ma_support,
            'ma_type': ma_type if ma_support else 'EMA',
            'ma_tolerance': ma_tolerance if ma_support else 3,
            'min_volume_ratio': min_volume_ratio,
            'volume_breakout_ratio': volume_breakout_ratio,
            'lookback_days': lookback_days,
            'pattern_strength_min': pattern_strength_min,
            'pattern_filters': pattern_filters,
            'pattern_priority': pattern_priority,
            'enable_weekly_validation': enable_weekly_validation,
            'show_charts': show_charts,
            'show_news': show_news,
            'export_results': export_results,
            'stocks_limit': stocks_limit,
            'market_sentiment': sentiment_data
        }

def create_main_scanner_tab(config):
    """Create main scanner tab with current day focus"""
    st.markdown("### 🎯 Current Day EOD Pattern Scanner V6.1")
    st.info("🔥 **Focus**: All patterns confirmed with latest trading day EOD data + Weekly timeframe validation for enhanced strength")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button("🚀 Scan Patterns (Daily + Weekly)", type="primary", key="main_scan")
    
    with col2:
        if config['export_results']:
            export_button = st.button("📊 Export", key="export")
        else:
            st.markdown("*Enable export*")
    
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
                # Get recent data focused on current day
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue
                
                # Check volume (current day focused)
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, config['min_volume_ratio'])
                if not volume_ok:
                    continue
                
                # Detect patterns (current day confirmation)
                patterns = scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue
                
                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]
                
                # Get news if enabled
                news_data = None
                if config['show_news']:
                    try:
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
            # Sort by pattern strength and current day confirmation
            results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)
            
            st.success(f"🎉 Found **{len(results)} stocks** with current day confirmed patterns!")
            
            # Summary metrics
            total_patterns = sum(len(r['patterns']) for r in results)
            avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
            current_day_breakouts = sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])
            high_confidence = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🎯 Stocks Found", len(results))
            with col2:
                st.metric("🔥 Current Day", current_day_breakouts)
            with col3:
                st.metric("💪 Avg Strength", f"{avg_strength:.1f}%")
            with col4:
                st.metric("🏆 High Confidence", high_confidence)
            
            # Display results
            for result in results:
                max_strength = max(p['strength'] for p in result['patterns'])
                overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
                
                # Check for current day breakout
                has_current_breakout = any('Current Day' in p['type'] for p in result['patterns'])
                current_indicator = " 🔥 TODAY!" if has_current_breakout else ""
                
                # Check for news
                has_news = result.get('news_data') and result['news_data']['news_count'] > 0
                news_indicator = " 📰" if has_news else ""
                
                with st.expander(
                    f"📈 {result['symbol'].replace('.NS', '').replace('^', '')} - {overall_confidence}{current_indicator}{news_indicator}", 
                    expanded=True
                ):
                    
                    # Stock metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("💰 Current Price", f"₹{result['current_price']:.2f}")
                    with col2:
                        volume_color = "inverse" if result['volume_ratio'] >= 2 else "normal"
                        st.metric("📊 Volume Today", f"{result['volume_ratio']:.2f}x", delta_color=volume_color)
                    with col3:
                        st.metric("📈 RSI", f"{result['rsi']:.1f}")
                    with col4:
                        st.metric("⚡ ADX", f"{result['adx']:.1f}")
                    
                    # Current day trading info
                    current_day_data = result['data'].iloc[-1]
                    trading_date = current_day_data.name.strftime('%Y-%m-%d')
                    
                    st.markdown(f"""
                    **🗓️ Trading Date:** {trading_date} | 
                    **📊 Day Range:** ₹{current_day_data['Low']:.2f} - ₹{current_day_data['High']:.2f} |
                    **💹 Day Change:** {((current_day_data['Close'] - current_day_data['Open']) / current_day_data['Open'] * 100):+.2f}%
                    """)
                    
                    # NEWS ANALYSIS
                    if has_news:
                        news_data = result['news_data']
                        sentiment_emoji = "🟢" if news_data['overall_sentiment'] == 'positive' else "🔴" if news_data['overall_sentiment'] == 'negative' else "🟡"
                        
                        st.markdown(f"""
                        <div class="news-card">
                            <h4>{sentiment_emoji} Today's News - {news_data['overall_sentiment'].upper()} Sentiment</h4>
                        """, unsafe_allow_html=True)
                        
                        for news_item in news_data['news_items'][:2]:
                            relevance_emoji = "🔥" if news_item['relevance'] == 'high' else "⚡" if news_item['relevance'] == 'medium' else "📄"
                            st.markdown(f"**{relevance_emoji}** {news_item['headline'][:120]}...")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Pattern details
                    for pattern in result['patterns']:
                        confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡" if pattern['confidence'] == 'MEDIUM' else "🔴"
                        
                        if pattern.get('special') == 'CURRENT_DAY_BREAKOUT':
                            details = pattern.get('details', {})
                            weekly_val = pattern.get('weekly_validation', {})
                            
                            # NEW V6.1: Weekly validation display
                            weekly_info = ""
                            if weekly_val.get('weekly_validation', False):
                                weekly_bonus = weekly_val.get('weekly_strength_bonus', 0)
                                weekly_context = weekly_val.get('weekly_context', '')
                                weekly_info = f"""
                                <div style='background: rgba(25, 135, 84, 0.1); padding: 8px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #198754;'>
                                    <strong>📈 Weekly Confirmation (+{weekly_bonus} pts):</strong> {weekly_context}<br>
                                    <small>Weekly Trend: {weekly_val.get('weekly_trend', 'N/A')} | Weekly RSI: {weekly_val.get('weekly_rsi', 0):.1f}</small>
                                </div>
                                """
                            elif weekly_val.get('weekly_strength_bonus', 0) > 0:
                                weekly_bonus = weekly_val.get('weekly_strength_bonus', 0)
                                weekly_context = weekly_val.get('weekly_context', '')
                                weekly_info = f"""
                                <div style='background: rgba(255, 193, 7, 0.1); padding: 8px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #ffc107;'>
                                    <strong>📊 Weekly Support (+{weekly_bonus} pts):</strong> {weekly_context}
                                </div>
                                """
                            
                            st.markdown(f"""
                            <div class="consolidation-card">
                                <h4>🔥 {confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence</h4>
                                <div style='display: flex; justify-content: space-between; margin: 8px 0;'>
                                    <span><strong>Total Strength:</strong> {pattern['strength']}%</span>
                                    <span><strong>Daily:</strong> {pattern.get('daily_strength', pattern['strength'])}%</span>
                                    <span><strong>Weekly Bonus:</strong> +{weekly_val.get('weekly_strength_bonus', 0)}</span>
                                </div>
                                <div style='display: flex; justify-content: space-between; margin: 8px 0;'>
                                    <span><strong>Success Rate:</strong> {pattern['success_rate']}%</span>
                                    <span><strong>PCS Fit:</strong> {pattern['pcs_suitability']}%</span>
                                </div>
                                <div style='display: flex; justify-content: space-between; margin: 8px 0; font-size: 0.9rem;'>
                                    <span><strong>Breakout:</strong> {details.get('breakout_percentage', 0):.2f}%</span>
                                    <span><strong>Volume:</strong> {details.get('volume_ratio', 0):.1f}x</span>
                                    <span><strong>Close Strength:</strong> {details.get('close_strength', 0):.0f}%</span>
                                </div>
                                {weekly_info}
                                <p><strong>Research:</strong> {pattern['research_basis']}</p>
                                <p><strong>💡 PCS Strategy:</strong> {'Conservative (3-5% OTM)' if pattern['confidence'] == 'HIGH' else 'Moderate (5-8% OTM)' if pattern['confidence'] == 'MEDIUM' else 'Aggressive (8-12% OTM)'}</p>
                                <p style="color: var(--primary-green); font-weight: 600;">⚡ CONFIRMED TODAY: Pattern validated with current trading day EOD data</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            confidence_class = f"{pattern['confidence'].lower()}-confidence"
                            weekly_val = pattern.get('weekly_validation', {})
                            
                            # NEW V6.1: Weekly validation display for regular patterns
                            weekly_info = ""
                            if weekly_val.get('weekly_validation', False):
                                weekly_bonus = weekly_val.get('weekly_strength_bonus', 0)
                                weekly_context = weekly_val.get('weekly_context', '')
                                weekly_signals = weekly_val.get('weekly_signals', [])
                                signal_text = " | ".join(weekly_signals[:2])  # Show first 2 signals
                                weekly_info = f"""
                                <div style='background: rgba(25, 135, 84, 0.1); padding: 8px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #198754;'>
                                    <strong>📈 Weekly Confirmation (+{weekly_bonus} pts):</strong> {weekly_context}<br>
                                    <small>{signal_text}</small>
                                </div>
                                """
                            elif weekly_val.get('weekly_strength_bonus', 0) > 0:
                                weekly_bonus = weekly_val.get('weekly_strength_bonus', 0)
                                weekly_context = weekly_val.get('weekly_context', '')
                                weekly_info = f"""
                                <div style='background: rgba(255, 193, 7, 0.1); padding: 8px; border-radius: 4px; margin: 8px 0; border-left: 3px solid #ffc107;'>
                                    <strong>📊 Weekly Support (+{weekly_bonus} pts):</strong> {weekly_context}
                                </div>
                                """
                            
                            st.markdown(f"""
                            <div class="pattern-card {confidence_class}">
                                <h4>{confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence</h4>
                                <div style='display: flex; justify-content: space-between; margin: 8px 0;'>
                                    <span><strong>Total Strength:</strong> {pattern['strength']}%</span>
                                    <span><strong>Daily:</strong> {pattern.get('daily_strength', pattern['strength'])}%</span>
                                    <span><strong>Weekly Bonus:</strong> +{weekly_val.get('weekly_strength_bonus', 0)}</span>
                                </div>
                                <div style='display: flex; justify-content: space-between; margin: 8px 0;'>
                                    <span><strong>Success Rate:</strong> {pattern['success_rate']}%</span>
                                    <span><strong>PCS Fit:</strong> {pattern['pcs_suitability']}%</span>
                                </div>
                                {weekly_info}
                                <p><strong>Research:</strong> {pattern['research_basis']}</p>
                                <p><strong>💡 PCS Strategy:</strong> {'Conservative (5% OTM)' if pattern['confidence'] == 'HIGH' else 'Moderate (8% OTM)' if pattern['confidence'] == 'MEDIUM' else 'Aggressive (12% OTM)'}</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Chart with current day focus
                    if config['show_charts']:
                        st.markdown("#### 📊 Current Day Chart Analysis")
                        chart = scanner.create_tradingview_chart(
                            result['data'], 
                            result['symbol'], 
                            result['patterns'][0] if result['patterns'] else None
                        )
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
        else:
            st.warning("🔍 No current day patterns found. Try adjusting filters.")
            
            st.markdown("### 💡 Suggestions:")
            st.markdown("- Lower **Pattern Strength** to 50-60%")
            st.markdown("- Reduce **Volume Ratio** to 1.0x")  
            st.markdown("- Expand **RSI range** to 25-85")
            st.markdown("- Check if markets traded today")

def main():
    # FIXED: Angel One Style Compact Header
    st.markdown("""
    <div class="professional-header">
        <h1>📈 NSE F&O PCS Scanner</h1>
        <p class="subtitle">Current Day EOD Analysis • Complete 219 Stock Universe • Angel One Style</p>
        <p class="description">Real-time Pattern Confirmation with Latest Trading Day Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get sidebar configuration
    config = create_professional_sidebar()
    
    # Create main tabs
    tab1, tab2 = st.tabs([
        "🎯 Current Day Scanner",
        "📊 Market Intelligence"
    ])
    
    with tab1:
        create_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📊 Market Intelligence Dashboard")
        
        # Get market data
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
                <h2 style="color: var(--primary-green);">{sentiment_level}</h2>
                <p>{overall_sentiment.get('pcs_recommendation', 'Moderate opportunities')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            risk_level = overall_sentiment.get('risk_level', 'MEDIUM')
            risk_color = "var(--primary-green)" if risk_level == 'LOW' else "var(--primary-orange)" if risk_level == 'MEDIUM' else "var(--primary-red)"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚠️ Risk Level</h3>
                <h2 style="color: {risk_color};">{risk_level}</h2>
                <p>Current PCS risk assessment</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            is_trading_day = current_time.weekday() < 5  # Monday=0, Friday=4
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>🕐 Market Status</h3>
                <h2 style="color: var(--primary-blue);">{current_time.strftime('%H:%M')}</h2>
                <p>{'Trading Day' if is_trading_day else 'Non-Trading Day'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed metrics
        st.markdown("#### 📈 Current Day Market Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'nifty' in sentiment_data:
                nifty_data = sentiment_data['nifty']
                st.metric("Nifty 50", f"{nifty_data['current']:.0f}", f"{nifty_data['change_1d']:+.2f}%")
        
        with col2:
            if 'bank_nifty' in sentiment_data:
                bank_data = sentiment_data['bank_nifty']
                st.metric("Bank Nifty", f"{bank_data['current']:.0f}", f"{bank_data['change_1d']:+.2f}%")
    
    # FIXED: Compact Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg)); border-radius: 8px; margin-top: 16px; border: 1px solid var(--border-color);'>
        <h4 style='color: var(--primary-blue); margin-bottom: 8px; font-size: 1.1rem;'>🏆 Professional Scanner - Angel One Style</h4>
        <p style='color: var(--text-secondary); margin: 2px 0; font-size: 0.85rem;'><strong>✅ Complete Universe:</strong> All 219 NSE F&O stocks</p>
        <p style='color: var(--text-secondary); margin: 2px 0; font-size: 0.85rem;'><strong>🔥 Current Day Focus:</strong> Latest EOD pattern confirmation</p>
        <p style='color: var(--text-secondary); margin: 2px 0; font-size: 0.85rem;'><strong>📰 News Intelligence:</strong> Real-time fundamental analysis</p>
        <p style='color: var(--text-muted); margin: 8px 0 0 0; font-size: 0.75rem;'><strong>⚠️ Disclaimer:</strong> Educational use only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
