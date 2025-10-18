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

# MODERN TAILWIND + SHADCN UI INSPIRED CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Tailwind CSS Variables */
    :root {
        /* Background Colors */
        --background: 222.2 84% 4.9%;
        --foreground: 210 40% 98%;
        
        /* Card Colors */
        --card: 222.2 84% 4.9%;
        --card-foreground: 210 40% 98%;
        
        /* Popover */
        --popover: 222.2 84% 4.9%;
        --popover-foreground: 210 40% 98%;
        
        /* Primary */
        --primary: 217.2 91.2% 59.8%;
        --primary-foreground: 222.2 47.4% 11.2%;
        
        /* Secondary */
        --secondary: 217.2 32.6% 17.5%;
        --secondary-foreground: 210 40% 98%;
        
        /* Muted */
        --muted: 217.2 32.6% 17.5%;
        --muted-foreground: 215 20.2% 65.1%;
        
        /* Accent */
        --accent: 217.2 32.6% 17.5%;
        --accent-foreground: 210 40% 98%;
        
        /* Destructive */
        --destructive: 0 62.8% 30.6%;
        --destructive-foreground: 210 40% 98%;
        
        /* Success */
        --success: 142.1 76.2% 36.3%;
        --success-foreground: 210 40% 98%;
        
        /* Warning */
        --warning: 38 92% 50%;
        --warning-foreground: 210 40% 98%;
        
        /* Border */
        --border: 217.2 32.6% 17.5%;
        --input: 217.2 32.6% 17.5%;
        
        /* Ring */
        --ring: 224.3 76.3% 48%;
        
        /* Radius */
        --radius: 0.5rem;
    }
    
    /* Base Styles */
    * {
        border-color: hsl(var(--border));
    }
    
    body {
        font-family: 'Inter', sans-serif;
        background: hsl(var(--background));
        color: hsl(var(--foreground));
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main App Container */
    .stApp {
        background: linear-gradient(to bottom, hsl(222.2, 84%, 4.9%), hsl(217.2, 32.6%, 7.5%));
    }
    
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* shadcn/ui Card Component */
    .card {
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
        padding: 1.5rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        transition: all 0.2s ease-in-out;
    }
    
    .card:hover {
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        border-color: hsl(var(--primary));
    }
    
    /* shadcn/ui Button Component */
    .stButton > button {
        background: hsl(var(--primary));
        color: hsl(var(--primary-foreground));
        border: none;
        border-radius: var(--radius);
        padding: 0.5rem 1rem;
        font-weight: 600;
        font-size: 0.875rem;
        line-height: 1.25rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    }
    
    .stButton > button:hover {
        background: hsl(217.2, 91.2%, 65%);
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Header Component */
    .header-card {
        background: linear-gradient(to right, hsl(var(--card)), hsl(217.2, 32.6%, 10%));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
        padding: 1.5rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .header-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(to right, 
            hsl(var(--primary)), 
            hsl(var(--success)), 
            hsl(var(--warning))
        );
    }
    
    .header-card h1 {
        color: hsl(var(--foreground));
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
    }
    
    .header-card .subtitle {
        color: hsl(var(--muted-foreground));
        font-size: 1rem;
        margin: 0;
    }
    
    /* Sidebar Styles */
    section[data-testid="stSidebar"] {
        background: hsl(var(--card));
        border-right: 1px solid hsl(var(--border));
    }
    
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: hsl(var(--foreground));
        font-weight: 600;
    }
    
    section[data-testid="stSidebar"] label {
        color: hsl(var(--foreground));
        font-weight: 500;
        font-size: 0.875rem;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: hsl(var(--background));
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb {
        background: hsl(var(--primary));
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: hsl(217.2, 91.2%, 65%);
    }
    
    /* Input Components */
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextInput > div > div > input {
        background: hsl(var(--background));
        border: 1px solid hsl(var(--input));
        border-radius: var(--radius);
        color: hsl(var(--foreground));
        font-size: 0.875rem;
        padding: 0.5rem 0.75rem;
        transition: all 0.2s ease-in-out;
    }
    
    .stSelectbox > div > div:hover,
    .stNumberInput > div > div > input:hover,
    .stTextInput > div > div > input:hover {
        border-color: hsl(var(--ring));
    }
    
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div > input:focus,
    .stTextInput > div > div > input:focus {
        border-color: hsl(var(--ring));
        outline: none;
        box-shadow: 0 0 0 3px hsl(var(--ring) / 0.2);
    }
    
    /* Tabs Component */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: transparent;
        border-bottom: 1px solid hsl(var(--border));
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        border-bottom: 2px solid transparent;
        color: hsl(var(--muted-foreground));
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.5rem 1rem;
        transition: all 0.2s ease-in-out;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: hsl(var(--foreground));
        border-bottom-color: hsl(var(--muted-foreground));
    }
    
    .stTabs [aria-selected="true"] {
        color: hsl(var(--primary));
        border-bottom-color: hsl(var(--primary));
    }
    
    /* Metric Cards */
    [data-testid="metric-container"] {
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
        padding: 1rem;
        transition: all 0.2s ease-in-out;
    }
    
    [data-testid="metric-container"]:hover {
        border-color: hsl(var(--primary));
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        color: hsl(var(--muted-foreground));
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: hsl(var(--foreground));
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Badge Component */
    .badge {
        display: inline-flex;
        align-items: center;
        border-radius: 9999px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        line-height: 1;
        transition: all 0.2s ease-in-out;
    }
    
    .badge-success {
        background: hsl(var(--success) / 0.15);
        color: hsl(var(--success));
        border: 1px solid hsl(var(--success) / 0.3);
    }
    
    .badge-warning {
        background: hsl(var(--warning) / 0.15);
        color: hsl(var(--warning));
        border: 1px solid hsl(var(--warning) / 0.3);
    }
    
    .badge-destructive {
        background: hsl(var(--destructive) / 0.15);
        color: hsl(0, 62.8%, 50%);
        border: 1px solid hsl(var(--destructive) / 0.3);
    }
    
    .badge-primary {
        background: hsl(var(--primary) / 0.15);
        color: hsl(var(--primary));
        border: 1px solid hsl(var(--primary) / 0.3);
    }
    
    /* Alert Component */
    .alert {
        border-radius: var(--radius);
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid;
    }
    
    .alert-success {
        background: hsl(var(--success) / 0.1);
        border-color: hsl(var(--success) / 0.3);
        color: hsl(var(--success));
    }
    
    .alert-warning {
        background: hsl(var(--warning) / 0.1);
        border-color: hsl(var(--warning) / 0.3);
        color: hsl(var(--warning));
    }
    
    .alert-destructive {
        background: hsl(var(--destructive) / 0.1);
        border-color: hsl(var(--destructive) / 0.3);
        color: hsl(0, 62.8%, 50%);
    }
    
    /* Dataframe Styling */
    .dataframe {
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
        font-size: 0.875rem;
    }
    
    .dataframe thead tr th {
        background: hsl(var(--muted));
        color: hsl(var(--foreground));
        font-weight: 600;
        padding: 0.75rem;
        border-bottom: 1px solid hsl(var(--border));
    }
    
    .dataframe tbody tr td {
        padding: 0.75rem;
        border-bottom: 1px solid hsl(var(--border));
    }
    
    .dataframe tbody tr:hover {
        background: hsl(var(--accent) / 0.5);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: hsl(var(--primary));
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
        color: hsl(var(--foreground));
        font-weight: 500;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: hsl(var(--primary));
    }
    
    /* Checkbox */
    .stCheckbox label {
        color: hsl(var(--foreground));
        font-size: 0.875rem;
    }
    
    /* Slider */
    .stSlider [data-testid="stSlider"] > div > div > div {
        background: hsl(var(--primary));
    }
    
    /* Success/Error Messages */
    .element-container .stAlert {
        background: hsl(var(--card));
        border: 1px solid hsl(var(--border));
        border-radius: var(--radius);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .header-card h1 {
            font-size: 1.5rem;
        }
        
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
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
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data with technical indicators"""
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
            
            return data
        except Exception as e:
            return None
    
    def calculate_pcs_score(self, data):
        """Calculate PCS score based on technical analysis"""
        if data is None or len(data) < 20:
            return 0
        
        try:
            current = data.iloc[-1]
            score = 0
            
            # 1. Bullish Momentum (30 points)
            rsi = current['RSI']
            if 45 <= rsi <= 65:
                score += 30
            elif 40 <= rsi < 45 or 65 < rsi <= 70:
                score += 20
            elif 30 <= rsi < 40:
                score += 15
            
            # 2. Trend Strength (25 points)
            if current['MACD'] > current['MACD_signal']:
                score += 15
            if current['Close'] > current['SMA_20']:
                score += 10
            
            # 3. Support Proximity (20 points)
            dist_to_sma20 = abs(current['Close'] - current['SMA_20']) / current['SMA_20'] * 100
            if dist_to_sma20 <= 2:
                score += 20
            elif dist_to_sma20 <= 5:
                score += 15
            elif dist_to_sma20 <= 10:
                score += 10
            
            # 4. Volatility (15 points)
            volatility = (data['Close'].pct_change().std() * np.sqrt(252)) * 100
            if 15 <= volatility <= 35:
                score += 15
            elif 10 <= volatility < 15 or 35 < volatility <= 45:
                score += 10
            
            # 5. Volume (10 points)
            avg_volume = data['Volume'].tail(20).mean()
            if current['Volume'] > avg_volume:
                score += 10
            elif current['Volume'] > avg_volume * 0.8:
                score += 5
            
            return min(score, 100)
        except:
            return 0
    
    def get_confidence_level(self, score):
        """Determine confidence level based on score"""
        if score >= 75:
            return "HIGH", "#10B981"
        elif score >= 60:
            return "MEDIUM", "#F59E0B"
        else:
            return "LOW", "#EF4444"
    
    def get_strike_recommendations(self, current_price, confidence):
        """Get strike recommendations based on confidence"""
        if confidence == "HIGH":
            short_otm = 0.05  # 5% OTM
            long_otm = 0.10   # 10% OTM
        elif confidence == "MEDIUM":
            short_otm = 0.08  # 8% OTM
            long_otm = 0.13   # 13% OTM
        else:
            short_otm = 0.12  # 12% OTM
            long_otm = 0.17   # 17% OTM
        
        short_strike = current_price * (1 - short_otm)
        long_strike = current_price * (1 - long_otm)
        
        # Round to nearest strike (typically 50 or 100)
        strike_interval = 50 if current_price < 1000 else 100
        short_strike = round(short_strike / strike_interval) * strike_interval
        long_strike = round(long_strike / strike_interval) * strike_interval
        
        return short_strike, long_strike

# Initialize scanner
scanner = ProfessionalPCSScanner()

# Header
st.markdown("""
<div class="header-card">
    <h1>📈 NSE F&O PCS Professional Scanner</h1>
    <p class="subtitle">Advanced Put Credit Spread Intelligence for NSE F&O Trading</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Configuration
with st.sidebar:
    st.markdown("## ⚙️ Scanner Configuration")
    
    # Stock Selection
    st.markdown("### 📊 Stock Selection")
    stock_source = st.selectbox(
        "Select Stock Source",
        ["All F&O Stocks", "Nifty 50", "Bank Nifty", "IT Stocks", "Pharma Stocks", 
         "Auto Stocks", "Metal Stocks", "Energy Stocks"]
    )
    
    max_stocks = st.slider("Maximum Stocks to Analyze", 5, 50, 25, 5)
    
    # Score Filters
    st.markdown("### 🎯 Score Filters")
    min_pcs_score = st.slider("Minimum PCS Score", 0, 100, 55, 5)
    
    # Technical Filters
    st.markdown("### 🔧 Technical Filters")
    min_rsi = st.slider("Minimum RSI", 0, 100, 30, 5)
    max_rsi = st.slider("Maximum RSI", 0, 100, 70, 5)
    
    # Analysis Button
    st.markdown("---")
    analyze_button = st.button("🚀 Run PCS Analysis", use_container_width=True)

# Main Content
if analyze_button:
    # Get stock list
    if stock_source == "All F&O Stocks":
        stock_list = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]
    else:
        stock_list = STOCK_CATEGORIES.get(stock_source, [])[:max_stocks]
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for idx, symbol in enumerate(stock_list):
        status_text.text(f"Analyzing {symbol}... ({idx+1}/{len(stock_list)})")
        progress_bar.progress((idx + 1) / len(stock_list))
        
        # Get data and calculate score
        data = scanner.get_stock_data(symbol)
        if data is not None:
            score = scanner.calculate_pcs_score(data)
            
            if score >= min_pcs_score:
                current = data.iloc[-1]
                rsi = current['RSI']
                
                if min_rsi <= rsi <= max_rsi:
                    confidence, color = scanner.get_confidence_level(score)
                    short_strike, long_strike = scanner.get_strike_recommendations(
                        current['Close'], confidence
                    )
                    
                    results.append({
                        'Symbol': symbol.replace('.NS', ''),
                        'Price': current['Close'],
                        'PCS_Score': score,
                        'Confidence': confidence,
                        'RSI': rsi,
                        'Short_Strike': short_strike,
                        'Long_Strike': long_strike,
                        'MACD': current['MACD'],
                        'ADX': current['ADX']
                    })
    
    progress_bar.empty()
    status_text.empty()
    
    # Display Results
    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('PCS_Score', ascending=False)
        
        st.markdown("## 📊 Analysis Results")
        
        # Summary Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Opportunities", len(df))
        with col2:
            high_conf = len(df[df['Confidence'] == 'HIGH'])
            st.metric("High Confidence", high_conf)
        with col3:
            avg_score = df['PCS_Score'].mean()
            st.metric("Average Score", f"{avg_score:.1f}")
        with col4:
            top_score = df['PCS_Score'].max()
            st.metric("Top Score", f"{top_score:.1f}")
        
        st.markdown("---")
        
        # Results Table
        st.markdown("### 📋 Detailed Results")
        
        # Format dataframe for display
        display_df = df.copy()
        display_df['Price'] = display_df['Price'].apply(lambda x: f"₹{x:.2f}")
        display_df['PCS_Score'] = display_df['PCS_Score'].apply(lambda x: f"{x:.1f}")
        display_df['RSI'] = display_df['RSI'].apply(lambda x: f"{x:.1f}")
        display_df['Short_Strike'] = display_df['Short_Strike'].apply(lambda x: f"₹{x:.0f}")
        display_df['Long_Strike'] = display_df['Long_Strike'].apply(lambda x: f"₹{x:.0f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="⬇️ Download Results as CSV",
            data=csv,
            file_name=f"pcs_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        # Detailed Cards for Top 5
        st.markdown("---")
        st.markdown("### 🌟 Top 5 Opportunities")
        
        for idx, row in df.head(5).iterrows():
            confidence, color = scanner.get_confidence_level(row['PCS_Score'])
            
            with st.expander(f"**{row['Symbol']}** - Score: {row['PCS_Score']:.1f} ({confidence})"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**Price Information**")
                    st.write(f"Current Price: ₹{row['Price']:.2f}")
                    st.write(f"Short Strike: ₹{row['Short_Strike']:.0f}")
                    st.write(f"Long Strike: ₹{row['Long_Strike']:.0f}")
                
                with col2:
                    st.markdown("**Technical Indicators**")
                    st.write(f"RSI: {row['RSI']:.1f}")
                    st.write(f"MACD: {row['MACD']:.2f}")
                    st.write(f"ADX: {row['ADX']:.1f}")
                
                with col3:
                    st.markdown("**Score Details**")
                    st.write(f"PCS Score: {row['PCS_Score']:.1f}/100")
                    st.write(f"Confidence: {confidence}")
                    
                    # Badge
                    if confidence == "HIGH":
                        badge_class = "badge-success"
                    elif confidence == "MEDIUM":
                        badge_class = "badge-warning"
                    else:
                        badge_class = "badge-destructive"
                    
                    st.markdown(f'<span class="badge {badge_class}">{confidence} CONFIDENCE</span>', 
                              unsafe_allow_html=True)
    
    else:
        st.markdown("""
        <div class="alert alert-warning">
            ⚠️ No stocks found matching the criteria. Try adjusting your filters.
        </div>
        """, unsafe_allow_html=True)

else:
    # Welcome Screen
    st.markdown("## 👋 Welcome to NSE F&O PCS Scanner")
    
    st.markdown("""
    <div class="card">
        <h3>🎯 How to Use</h3>
        <ol>
            <li>Configure your filters in the sidebar</li>
            <li>Select stock source and maximum stocks to analyze</li>
            <li>Set minimum PCS score and RSI range</li>
            <li>Click "Run PCS Analysis" to start scanning</li>
            <li>Review results and download CSV for further analysis</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>📊 Key Features</h3>
            <ul>
                <li>5-Component PCS Scoring System</li>
                <li>40+ Liquid F&O Stocks Coverage</li>
                <li>Confidence-Based Strike Recommendations</li>
                <li>Real-time Technical Analysis</li>
                <li>Risk Management Framework</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>⚠️ Important Disclaimers</h3>
            <ul>
                <li>This is NOT financial advice</li>
                <li>Options trading involves substantial risk</li>
                <li>Always verify data before trading</li>
                <li>Consult with financial advisors</li>
                <li>Start with paper trading</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="alert alert-destructive">
        <strong>⚠️ Risk Warning:</strong> Options trading involves substantial risk. 
        You can lose your entire investment. This tool is for educational purposes only.
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: hsl(var(--muted-foreground)); font-size: 0.875rem;">
    <p>Built with Streamlit • Powered by yfinance & TA-Lib</p>
    <p>⚠️ For educational purposes only • Not financial advice</p>
</div>
""", unsafe_allow_html=True)
