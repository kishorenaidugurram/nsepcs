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
from urllib.parse import quote, urljoin
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner V5", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ENHANCED: Angel One Dark Theme with IMPROVED SIDEBAR LEGIBILITY
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
        --text-secondary: #E2E8F0;
        --text-muted: #CBD5E0;
        --text-sidebar: #48BB78;  /* FIXED: Green text for sidebar */
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
    
    /* ENHANCED: Sidebar with GREEN TEXT for better legibility */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--sidebar-bg) 0%, var(--accent-bg) 100%);
        border-right: 2px solid var(--border-color);
        box-shadow: 4px 0 20px var(--shadow-medium);
    }
    
    /* FIXED: Sidebar text legibility - GREEN text instead of milky white */
    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stNumberInput label,
    section[data-testid="stSidebar"] div[data-testid="stExpander"] summary {
        color: var(--text-sidebar) !important;
        font-weight: 500 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }
    
    /* Sidebar headers - brighter green */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: var(--primary-green) !important;
        font-weight: 600 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
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
        background: linear-gradient(180deg, var(--primary-blue), var(--primary-green));
        border-radius: 6px;
        border: 2px solid var(--accent-bg);
    }
    
    section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--primary-green), var(--primary-blue));
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
    
    @keyframes scanning {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    
    .scanning-progress {
        background: linear-gradient(90deg, transparent, var(--primary-blue), transparent);
        animation: scanning 2s infinite;
        height: 2px;
        margin: 4px 0;
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
    
    @media (max-width: 480px) {
        .metric-card { 
            padding: 12px; 
        }
        .professional-header h1 { 
            font-size: 1.2rem; 
        }
    }
</style>
""", unsafe_allow_html=True)

class DynamicNSEDataFetcher:
    """Enhanced class to fetch NSE F&O list dynamically from NSE website"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_nse_fo_stocks(self):
        """Fetch complete NSE F&O stock list dynamically"""
        try:
            # Primary NSE API endpoint for derivatives
            nse_url = "https://www.nseindia.com/api/master-quote"
            
            # Get NSE cookies first
            self.session.get("https://www.nseindia.com", headers=self.headers, timeout=10)
            
            # Fetch derivatives data
            response = self.session.get(nse_url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                fo_stocks = []
                
                # Extract F&O stocks from response
                if 'data' in data:
                    for stock in data['data']:
                        symbol = stock.get('symbol', '')
                        if symbol and len(symbol) > 0:
                            fo_stocks.append(f"{symbol}.NS")
                
                if len(fo_stocks) > 100:  # Valid response
                    return sorted(list(set(fo_stocks)))
                    
        except Exception as e:
            st.warning(f"NSE API error: {str(e)[:100]}...")
        
        # Fallback to alternative method
        return self._get_fallback_fo_list()
    
    def _get_fallback_fo_list(self):
        """Fallback method to get F&O list from alternative sources"""
        try:
            # Alternative: Scrape from NSE derivatives page
            url = "https://www.nseindia.com/products-services/equity-derivatives-list"
            response = self.session.get(url, headers=self.headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                fo_stocks = []
                
                # Extract stock symbols from tables
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows[1:]:  # Skip header
                        cells = row.find_all('td')
                        if len(cells) > 0:
                            symbol = cells[0].get_text(strip=True)
                            if symbol and symbol.isalpha():
                                fo_stocks.append(f"{symbol}.NS")
                
                if len(fo_stocks) > 50:
                    return sorted(list(set(fo_stocks)))
                    
        except Exception as e:
            st.warning(f"Fallback method error: {str(e)[:100]}...")
        
        # Final fallback - comprehensive static list
        return self._get_comprehensive_static_list()
    
    def _get_comprehensive_static_list(self):
        """Comprehensive static F&O list as final fallback"""
        return [
            # Indices
            '^NSEI', '^NSEBANK', '^CNXFINANCE', '^CNXMIDCAP',
            
            # Major stocks - Comprehensive list
            '360ONE.NS', 'ABB.NS', 'ABCAPITAL.NS', 'ABFRL.NS', 'ACC.NS', 'ADANIENSOL.NS', 
            'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ADANITRANS.NS', 'AJANTPHARM.NS', 
            'ALKEM.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APLAPOLLO.NS', 'APOLLOHOSP.NS', 
            'APOLLOTYRE.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'ATUL.NS', 
            'AUBANK.NS', 'AUROPHARMA.NS', 'AXISBANK.NS', 'BAJAJ-AUTO.NS', 'BAJAJFINSV.NS', 
            'BAJFINANCE.NS', 'BALKRISIND.NS', 'BALRAMCHIN.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS',
            'BANKINDIA.NS', 'BATAINDIA.NS', 'BDL.NS', 'BEL.NS', 'BERGEPAINT.NS', 'BHARATFORG.NS',
            'BHARTIARTL.NS', 'BHEL.NS', 'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BPCL.NS',
            'BRITANNIA.NS', 'BSE.NS', 'BSOFT.NS', 'CAMS.NS', 'CANBK.NS', 'CANFINHOME.NS',
            'CDSL.NS', 'CESC.NS', 'CGCL.NS', 'CGPOWER.NS', 'CHAMBLFERT.NS', 'CHOLAFIN.NS',
            'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CONCOR.NS', 'COROMANDEL.NS',
            'CROMPTON.NS', 'CUB.NS', 'CUMMINS.NS', 'CYIENT.NS', 'DABUR.NS', 'DALBHARAT.NS',
            'DEEPAKNTR.NS', 'DELHIVERY.NS', 'DELTACORP.NS', 'DIVISLAB.NS', 'DIXON.NS', 'DLF.NS',
            'DMART.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'ESCORTS.NS', 'ETERNAL.NS', 'EXIDEIND.NS',
            'FEDERALBNK.NS', 'FORTIS.NS', 'GAIL.NS', 'GLENMARK.NS', 'GMRAIRPORT.NS', 'GMRINFRA.NS',
            'GNFC.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRANULES.NS', 'GRASIM.NS', 'GUJGASLTD.NS',
            'HAL.NS', 'HAVELLS.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
            'HEROMOTOCO.NS', 'HFCL.NS', 'HINDALCO.NS', 'HINDCOPPER.NS', 'HINDPETRO.NS', 
            'HINDUNILVR.NS', 'HINDZINC.NS', 'HONAUT.NS', 'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS',
            'ICICIPRULI.NS', 'IDEA.NS', 'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 'IIFL.NS',
            'INDHOTEL.NS', 'INDIANB.NS', 'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS',
            'INFY.NS', 'INOXWIND.NS', 'IOC.NS', 'IPCALAB.NS', 'IRCTC.NS', 'IREDA.NS', 'IRFC.NS',
            'ITC.NS', 'JINDALSTEL.NS', 'JIOFIN.NS', 'JKCEMENT.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
            'JUBLFOOD.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KEI.NS', 'KFINTECH.NS', 'KOTAKBANK.NS',
            'KPITTECH.NS', 'KPRMILL.NS', 'KRBL.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS',
            'LICHSGFIN.NS', 'LICI.NS', 'LODHA.NS', 'LT.NS', 'LTF.NS', 'LTIM.NS', 'LTTS.NS',
            'LUPIN.NS', 'M&M.NS', 'M&MFIN.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS',
            'MARUTI.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MCX.NS', 'METROPOLIS.NS', 'MFSL.NS',
            'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS', 'MRF.NS', 'MUTHOOTFIN.NS', 'NATIONALUM.NS',
            'NAUKRI.NS', 'NAVINFLUOR.NS', 'NBCC.NS', 'NCC.NS', 'NESTLEIND.NS', 'NHPC.NS',
            'NMDC.NS', 'NTPC.NS', 'NUVAMA.NS', 'NYKAA.NS', 'OBEROIRLTY.NS', 'OFSS.NS', 'OIL.NS',
            'ONGC.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PAYTM.NS', 'PERSISTENT.NS', 'PETRONET.NS',
            'PFC.NS', 'PGEL.NS', 'PHOENIXLTD.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS',
            'PNBHOUSING.NS', 'POLICYBZR.NS', 'POLYCAB.NS', 'POWERGRID.NS', 'POWERINDIA.NS',
            'PPLPHARMA.NS', 'PRESTIGE.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECLTD.NS',
            'RELIANCE.NS', 'RVNL.NS', 'SAIL.NS', 'SAMMAANCAP.NS', 'SBICARD.NS', 'SBILIFE.NS',
            'SBIN.NS', 'SHREECEM.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS',
            'SRF.NS', 'STAR.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUNTV.NS', 'SUZLON.NS',
            'SYNGENE.NS', 'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSUM.NS', 'TATAELXSI.NS', 
            'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TCS.NS', 'TECHM.NS',
            'TIINDIA.NS', 'TITAGARH.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS',
            'TVSMOTOR.NS', 'UBL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'UNOMINDA.NS',
            'UPL.NS', 'VBL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZEEL.NS', 
            'ZYDUSLIFE.NS'
        ]

class GoogleNewsParser:
    """Enhanced class to fetch Google News for specific stocks"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_stock_news(self, symbol, company_name=None, max_articles=3):
        """Fetch recent news for a specific stock"""
        try:
            # Clean symbol for search
            clean_symbol = symbol.replace('.NS', '').replace('.BO', '')
            
            # Create search query
            if company_name:
                search_query = f"{company_name} stock {clean_symbol} India"
            else:
                search_query = f"{clean_symbol} stock India NSE"
            
            # Google News search URL
            news_url = f"https://news.google.com/rss/search?q={quote(search_query)}&hl=en-IN&gl=IN&ceid=IN:en"
            
            response = requests.get(news_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return self._parse_news_rss(response.content, max_articles)
            else:
                return self._get_fallback_news(clean_symbol, max_articles)
                
        except Exception as e:
            return [{
                'title': f'News fetch error for {symbol}',
                'summary': f'Unable to fetch news: {str(e)[:100]}',
                'sentiment': 'NEUTRAL',
                'url': '#',
                'published': datetime.now().strftime('%Y-%m-%d %H:%M')
            }]
    
    def _parse_news_rss(self, rss_content, max_articles):
        """Parse RSS content from Google News"""
        try:
            soup = BeautifulSoup(rss_content, 'xml')
            items = soup.find_all('item')[:max_articles]
            
            news_articles = []
            for item in items:
                title = item.find('title').text if item.find('title') else 'No title'
                description = item.find('description').text if item.find('description') else 'No description'
                pub_date = item.find('pubDate').text if item.find('pubDate') else ''
                link = item.find('link').text if item.find('link') else '#'
                
                # Clean description from HTML
                clean_desc = BeautifulSoup(description, 'html.parser').get_text()
                
                # Simple sentiment analysis
                sentiment = self._analyze_sentiment(title + ' ' + clean_desc)
                
                news_articles.append({
                    'title': title[:100] + '...' if len(title) > 100 else title,
                    'summary': clean_desc[:200] + '...' if len(clean_desc) > 200 else clean_desc,
                    'sentiment': sentiment,
                    'url': link,
                    'published': self._format_date(pub_date)
                })
            
            return news_articles if news_articles else self._get_no_news_placeholder()
            
        except Exception as e:
            return self._get_no_news_placeholder()
    
    def _get_fallback_news(self, symbol, max_articles):
        """Fallback method for news fetching"""
        try:
            # Alternative: Try direct Google search
            search_url = f"https://www.google.com/search?q={quote(symbol + ' stock news India')}&tbm=nws"
            response = requests.get(search_url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_items = soup.find_all('div', {'class': 'g'})[:max_articles]
                
                articles = []
                for item in news_items:
                    title_elem = item.find('h3')
                    desc_elem = item.find('span', {'class': 'st'})
                    
                    if title_elem:
                        title = title_elem.get_text()
                        description = desc_elem.get_text() if desc_elem else 'No description available'
                        
                        articles.append({
                            'title': title[:100] + '...' if len(title) > 100 else title,
                            'summary': description[:200] + '...' if len(description) > 200 else description,
                            'sentiment': self._analyze_sentiment(title + ' ' + description),
                            'url': '#',
                            'published': 'Recent'
                        })
                
                return articles if articles else self._get_no_news_placeholder()
                
        except Exception:
            return self._get_no_news_placeholder()
    
    def _analyze_sentiment(self, text):
        """Simple sentiment analysis based on keywords"""
        text_lower = text.lower()
        
        positive_words = ['gains', 'profit', 'rise', 'surge', 'bull', 'positive', 'growth', 'up', 'high', 'strong', 'buy', 'upgrade']
        negative_words = ['loss', 'fall', 'drop', 'bear', 'negative', 'decline', 'down', 'low', 'weak', 'sell', 'downgrade']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'BULLISH'
        elif negative_count > positive_count:
            return 'BEARISH'
        else:
            return 'NEUTRAL'
    
    def _format_date(self, date_str):
        """Format publication date"""
        try:
            if date_str:
                # Parse and format date
                from dateutil import parser
                dt = parser.parse(date_str)
                return dt.strftime('%Y-%m-%d %H:%M')
        except:
            pass
        return datetime.now().strftime('%Y-%m-%d %H:%M')
    
    def _get_no_news_placeholder(self):
        """Placeholder when no news is found"""
        return [{
            'title': 'No recent news found',
            'summary': 'No specific news available for this stock at the moment',
            'sentiment': 'NEUTRAL',
            'url': '#',
            'published': datetime.now().strftime('%Y-%m-%d %H:%M')
        }]

class ProfessionalPCSScanner:
    """Enhanced Professional PCS Scanner with dynamic data and news integration"""
    
    def __init__(self):
        self.nse_fetcher = DynamicNSEDataFetcher()
        self.news_parser = GoogleNewsParser()
        
        # Company name mapping for better news search
        self.company_names = {
            'RELIANCE.NS': 'Reliance Industries',
            'TCS.NS': 'Tata Consultancy Services',
            'HDFCBANK.NS': 'HDFC Bank',
            'INFY.NS': 'Infosys',
            'ICICIBANK.NS': 'ICICI Bank',
            'BHARTIARTL.NS': 'Bharti Airtel',
            'ITC.NS': 'ITC Limited',
            'SBIN.NS': 'State Bank of India',
            'LT.NS': 'Larsen & Toubro',
            'KOTAKBANK.NS': 'Kotak Mahindra Bank',
            'AXISBANK.NS': 'Axis Bank',
            'MARUTI.NS': 'Maruti Suzuki',
            'ASIANPAINT.NS': 'Asian Paints',
            'WIPRO.NS': 'Wipro',
            'ONGC.NS': 'Oil & Natural Gas Corporation',
            'NTPC.NS': 'NTPC Limited',
            'POWERGRID.NS': 'Power Grid Corporation',
            'TATAMOTORS.NS': 'Tata Motors',
            'TECHM.NS': 'Tech Mahindra',
            'ULTRACEMCO.NS': 'UltraTech Cement'
        }
    
    def get_dynamic_fo_stocks(self):
        """Get NSE F&O stocks dynamically"""
        with st.spinner("🔄 Fetching latest NSE F&O stock list..."):
            return self.nse_fetcher.get_nse_fo_stocks()
    
    def detect_current_day_breakout(self, df, resistance_level, support_level, min_volume_ratio=1.2):
        """Enhanced current day breakout detection with better logic"""
        if len(df) < 20:
            return False, 0, {}
        
        # Get current day data (latest trading day)
        current_day = df.iloc[-1]
        lookback_data = df.iloc[-20:]  # Last 20 days for context
        
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
        
        # Price momentum
        if breakout_percentage >= 2:
            strength += 10
        
        return True, min(strength, 100), {
            'breakout_percentage': breakout_percentage,
            'volume_ratio': volume_ratio,
            'consolidation_range': consolidation_range,
            'current_price': current_close,
            'resistance_level': resistance_level,
            'support_level': support_level
        }

    def detect_cup_and_handle(self, df, min_volume_ratio=1.2, adx_threshold=20):
        """Detect Cup and Handle pattern with current day confirmation"""
        if len(df) < 50:
            return False, 0, {}
        
        try:
            # Calculate technical indicators
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
            df['EMA_20'] = ta.trend.EMAIndicator(df['Close'], window=20).ema_indicator()
            df['Volume_MA'] = df['Volume'].rolling(window=20).mean()
            
            current_day = df.iloc[-1]
            current_rsi = current_day['RSI']
            current_adx = current_day['ADX']
            
            # RSI and ADX filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return False, 0, {}
                
            if not (40 <= current_rsi <= 70) or current_adx < adx_threshold:
                return False, 0, {}
            
            # Look for cup formation (30-50 days)
            cup_period = min(50, len(df))
            cup_data = df.iloc[-cup_period:]
            
            if len(cup_data) < 30:
                return False, 0, {}
            
            # Find cup high and low
            cup_high = cup_data['High'].max()
            cup_low = cup_data['Low'].min()
            cup_depth = (cup_high - cup_low) / cup_high
            
            # Cup should be 10-50% deep
            if not (0.10 <= cup_depth <= 0.50):
                return False, 0, {}
            
            # Look for handle formation (last 5-15 days)
            handle_period = min(15, max(5, len(df) // 4))
            handle_data = df.iloc[-handle_period:]
            
            handle_high = handle_data['High'].max()
            handle_low = handle_data['Low'].min()
            
            # Handle should be in upper half of cup
            if handle_low < (cup_low + (cup_high - cup_low) * 0.5):
                return False, 0, {}
            
            # Current day breakout confirmation
            resistance_level = max(cup_high, handle_high)
            support_level = handle_low
            
            breakout_confirmed, strength, details = self.detect_current_day_breakout(
                df, resistance_level, support_level, min_volume_ratio
            )
            
            if not breakout_confirmed:
                return False, 0, {}
            
            # Additional pattern-specific scoring
            pattern_score = strength
            
            # Cup symmetry bonus
            cup_left = cup_data.iloc[:len(cup_data)//2]
            cup_right = cup_data.iloc[len(cup_data)//2:]
            
            left_slope = (cup_left['Close'].iloc[-1] - cup_left['Close'].iloc[0]) / len(cup_left)
            right_slope = (cup_right['Close'].iloc[-1] - cup_right['Close'].iloc[0]) / len(cup_right)
            
            if abs(left_slope + right_slope) < abs(max(left_slope, right_slope)) * 0.5:
                pattern_score += 10
            
            details.update({
                'pattern_type': 'Cup and Handle',
                'cup_depth': cup_depth * 100,
                'handle_days': handle_period,
                'cup_high': cup_high,
                'cup_low': cup_low,
                'rsi': current_rsi,
                'adx': current_adx
            })
            
            return True, min(pattern_score, 100), details
            
        except Exception as e:
            return False, 0, {}

    def detect_flat_base(self, df, min_volume_ratio=1.2, adx_threshold=20):
        """Detect Flat Base pattern with current day confirmation"""
        if len(df) < 30:
            return False, 0, {}
        
        try:
            # Calculate technical indicators
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
            
            current_day = df.iloc[-1]
            current_rsi = current_day['RSI']
            current_adx = current_day['ADX']
            
            # RSI and ADX filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return False, 0, {}
                
            if not (40 <= current_rsi <= 70) or current_adx < adx_threshold:
                return False, 0, {}
            
            # Look for flat base (15-25 days)
            base_period = min(25, max(15, len(df)))
            base_data = df.iloc[-base_period:]
            
            base_high = base_data['High'].max()
            base_low = base_data['Low'].min()
            base_range = (base_high - base_low) / base_high
            
            # Flat base should be tight (less than 15% range)
            if base_range > 0.15:
                return False, 0, {}
            
            # Check for consolidation
            price_volatility = base_data['Close'].std() / base_data['Close'].mean()
            if price_volatility > 0.08:  # Too volatile
                return False, 0, {}
            
            # Current day breakout confirmation
            resistance_level = base_high
            support_level = base_low
            
            breakout_confirmed, strength, details = self.detect_current_day_breakout(
                df, resistance_level, support_level, min_volume_ratio
            )
            
            if not breakout_confirmed:
                return False, 0, {}
            
            # Pattern-specific scoring
            pattern_score = strength
            
            # Tight consolidation bonus
            if base_range < 0.08:
                pattern_score += 15
            elif base_range < 0.12:
                pattern_score += 10
            
            details.update({
                'pattern_type': 'Flat Base',
                'base_range': base_range * 100,
                'base_days': base_period,
                'consolidation_tightness': (1 - price_volatility) * 100,
                'rsi': current_rsi,
                'adx': current_adx
            })
            
            return True, min(pattern_score, 100), details
            
        except Exception as e:
            return False, 0, {}

    def detect_vcp(self, df, min_volume_ratio=1.2, adx_threshold=20):
        """Detect Volatility Contraction Pattern with current day confirmation"""
        if len(df) < 40:
            return False, 0, {}
        
        try:
            # Calculate technical indicators
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
            df['ATR'] = ta.volatility.AverageTrueRange(df['High'], df['Low'], df['Close']).average_true_range()
            
            current_day = df.iloc[-1]
            current_rsi = current_day['RSI']
            current_adx = current_day['ADX']
            
            # RSI and ADX filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return False, 0, {}
                
            if not (40 <= current_rsi <= 70) or current_adx < adx_threshold:
                return False, 0, {}
            
            # Analyze volatility contraction over multiple periods
            periods = [10, 20, 30]
            contractions = []
            
            for period in periods:
                if len(df) >= period:
                    period_data = df.iloc[-period:]
                    period_range = (period_data['High'].max() - period_data['Low'].min()) / period_data['Close'].mean()
                    contractions.append(period_range)
            
            if len(contractions) < 2:
                return False, 0, {}
            
            # Check for progressive contraction
            contraction_trend = all(contractions[i] > contractions[i+1] for i in range(len(contractions)-1))
            
            if not contraction_trend:
                return False, 0, {}
            
            # Current day breakout confirmation
            recent_data = df.iloc[-20:]
            resistance_level = recent_data['High'].max()
            support_level = recent_data['Low'].min()
            
            breakout_confirmed, strength, details = self.detect_current_day_breakout(
                df, resistance_level, support_level, min_volume_ratio
            )
            
            if not breakout_confirmed:
                return False, 0, {}
            
            # Pattern-specific scoring
            pattern_score = strength
            
            # Contraction quality bonus
            contraction_ratio = contractions[-1] / contractions[0] if contractions[0] > 0 else 1
            if contraction_ratio < 0.5:
                pattern_score += 20
            elif contraction_ratio < 0.7:
                pattern_score += 15
            elif contraction_ratio < 0.85:
                pattern_score += 10
            
            details.update({
                'pattern_type': 'VCP (Volatility Contraction)',
                'contraction_stages': len(contractions),
                'contraction_ratio': contraction_ratio,
                'final_contraction': contractions[-1] * 100,
                'rsi': current_rsi,
                'adx': current_adx
            })
            
            return True, min(pattern_score, 100), details
            
        except Exception as e:
            return False, 0, {}

    def detect_high_tight_flag(self, df, min_volume_ratio=1.2, adx_threshold=20):
        """Detect High Tight Flag pattern with current day confirmation"""
        if len(df) < 30:
            return False, 0, {}
        
        try:
            # Calculate technical indicators
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
            
            current_day = df.iloc[-1]
            current_rsi = current_day['RSI']
            current_adx = current_day['ADX']
            
            # RSI and ADX filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return False, 0, {}
                
            if not (40 <= current_rsi <= 70) or current_adx < adx_threshold:
                return False, 0, {}
            
            # Look for prior strong move (20-40% in 4-8 weeks)
            lookback_period = min(40, len(df))
            lookback_data = df.iloc[-lookback_period:]
            
            if len(lookback_data) < 20:
                return False, 0, {}
            
            # Find the low point for the strong move
            period_low = lookback_data['Low'].min()
            period_high = lookback_data['High'].max()
            
            # Calculate the move strength
            move_strength = (period_high - period_low) / period_low
            
            # Must have strong prior move (at least 20%)
            if move_strength < 0.20:
                return False, 0, {}
            
            # Look for tight flag formation (3-5 weeks)
            flag_period = min(25, max(15, len(df) // 2))
            flag_data = df.iloc[-flag_period:]
            
            flag_high = flag_data['High'].max()
            flag_low = flag_data['Low'].min()
            flag_range = (flag_high - flag_low) / flag_high
            
            # Flag should be tight (less than 25% of prior move)
            max_flag_range = move_strength * 0.25
            if flag_range > max_flag_range:
                return False, 0, {}
            
            # Current day breakout confirmation
            resistance_level = flag_high
            support_level = flag_low
            
            breakout_confirmed, strength, details = self.detect_current_day_breakout(
                df, resistance_level, support_level, min_volume_ratio
            )
            
            if not breakout_confirmed:
                return False, 0, {}
            
            # Pattern-specific scoring
            pattern_score = strength
            
            # Strong prior move bonus
            if move_strength > 0.50:
                pattern_score += 20
            elif move_strength > 0.35:
                pattern_score += 15
            elif move_strength > 0.25:
                pattern_score += 10
            
            # Tight flag bonus
            flag_tightness = 1 - (flag_range / max_flag_range)
            pattern_score += int(flag_tightness * 15)
            
            details.update({
                'pattern_type': 'High Tight Flag',
                'prior_move_strength': move_strength * 100,
                'flag_range': flag_range * 100,
                'flag_days': flag_period,
                'flag_tightness': flag_tightness * 100,
                'rsi': current_rsi,
                'adx': current_adx
            })
            
            return True, min(pattern_score, 100), details
            
        except Exception as e:
            return False, 0, {}

    def detect_ascending_triangle(self, df, min_volume_ratio=1.2, adx_threshold=20):
        """Detect Ascending Triangle pattern with current day confirmation"""
        if len(df) < 30:
            return False, 0, {}
        
        try:
            # Calculate technical indicators
            df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
            df['ADX'] = ta.trend.ADXIndicator(df['High'], df['Low'], df['Close']).adx()
            
            current_day = df.iloc[-1]
            current_rsi = current_day['RSI']
            current_adx = current_day['ADX']
            
            # RSI and ADX filters
            if pd.isna(current_rsi) or pd.isna(current_adx):
                return False, 0, {}
                
            if not (40 <= current_rsi <= 70) or current_adx < adx_threshold:
                return False, 0, {}
            
            # Look for triangle formation (20-30 days)
            triangle_period = min(30, max(20, len(df)))
            triangle_data = df.iloc[-triangle_period:]
            
            # Find horizontal resistance (multiple highs at similar level)
            highs = triangle_data['High'].values
            resistance_candidates = []
            
            # Look for at least 2 highs within 2% of each other
            for i in range(len(highs)):
                similar_highs = [highs[i]]
                for j in range(i+1, len(highs)):
                    if abs(highs[j] - highs[i]) / highs[i] <= 0.02:
                        similar_highs.append(highs[j])
                
                if len(similar_highs) >= 2:
                    resistance_candidates.append(np.mean(similar_highs))
            
            if not resistance_candidates:
                return False, 0, {}
            
            resistance_level = max(resistance_candidates)
            
            # Check for ascending support (rising lows)
            lows = triangle_data['Low'].values
            support_points = [lows[0]]
            
            for i in range(1, len(lows)):
                if lows[i] > support_points[-1] * 0.98:  # Allow small tolerance
                    support_points.append(lows[i])
            
            if len(support_points) < 2:
                return False, 0, {}
            
            # Calculate support trend
            support_slope = (support_points[-1] - support_points[0]) / len(support_points)
            
            # Support should be ascending
            if support_slope <= 0:
                return False, 0, {}
            
            support_level = support_points[-1]
            
            # Current day breakout confirmation
            breakout_confirmed, strength, details = self.detect_current_day_breakout(
                df, resistance_level, support_level, min_volume_ratio
            )
            
            if not breakout_confirmed:
                return False, 0, {}
            
            # Pattern-specific scoring
            pattern_score = strength
            
            # Triangle quality bonus
            triangle_range = (resistance_level - support_level) / resistance_level
            if triangle_range < 0.10:
                pattern_score += 20  # Very tight triangle
            elif triangle_range < 0.15:
                pattern_score += 15
            elif triangle_range < 0.20:
                pattern_score += 10
            
            # Ascending support bonus
            support_strength = support_slope / support_level
            pattern_score += min(int(support_strength * 1000), 15)
            
            details.update({
                'pattern_type': 'Ascending Triangle',
                'triangle_range': triangle_range * 100,
                'support_slope': support_slope,
                'triangle_days': triangle_period,
                'resistance_touches': len(resistance_candidates),
                'rsi': current_rsi,
                'adx': current_adx
            })
            
            return True, min(pattern_score, 100), details
            
        except Exception as e:
            return False, 0, {}

    def get_market_sentiment_indicators(self):
        """Get comprehensive market sentiment indicators"""
        try:
            # Fetch major indices
            indices = ['^NSEI', '^NSEBANK']
            sentiment_data = {}
            
            for index in indices:
                try:
                    data = yf.download(index, period='5d', interval='1d', progress=False)
                    if not data.empty:
                        latest = data.iloc[-1]
                        prev = data.iloc[-2] if len(data) > 1 else latest
                        
                        change_pct = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
                        
                        if change_pct > 1:
                            sentiment = 'BULLISH'
                        elif change_pct < -1:
                            sentiment = 'BEARISH'
                        else:
                            sentiment = 'NEUTRAL'
                        
                        sentiment_data[index] = {
                            'sentiment': sentiment,
                            'change_pct': change_pct,
                            'price': latest['Close']
                        }
                except:
                    continue
            
            # Overall market sentiment
            if sentiment_data:
                avg_change = np.mean([data['change_pct'] for data in sentiment_data.values()])
                
                if avg_change > 0.5:
                    overall_sentiment = 'BULLISH'
                    pcs_recommendation = 'Favorable conditions for PCS patterns'
                elif avg_change < -0.5:
                    overall_sentiment = 'BEARISH'
                    pcs_recommendation = 'Cautious approach recommended'
                else:
                    overall_sentiment = 'NEUTRAL'
                    pcs_recommendation = 'Selective opportunities available'
                
                sentiment_data['overall'] = {
                    'sentiment': overall_sentiment,
                    'pcs_recommendation': pcs_recommendation,
                    'avg_change': avg_change
                }
            
            return sentiment_data
            
        except Exception as e:
            return {
                'overall': {
                    'sentiment': 'NEUTRAL',
                    'pcs_recommendation': 'Unable to fetch market data',
                    'avg_change': 0
                }
            }

    def scan_stock_for_patterns(self, symbol, config):
        """Enhanced stock scanning with news integration"""
        try:
            # Download stock data
            stock = yf.Ticker(symbol)
            df = stock.history(period='6mo', interval='1d')
            
            if df.empty or len(df) < 30:
                return None
            
            # Clean data
            df = df.dropna()
            df.reset_index(inplace=True)
            
            patterns_found = []
            
            # Pattern detection methods
            pattern_methods = [
                self.detect_cup_and_handle,
                self.detect_flat_base,
                self.detect_vcp,
                self.detect_high_tight_flag,
                self.detect_ascending_triangle
            ]
            
            for method in pattern_methods:
                try:
                    detected, strength, details = method(
                        df.copy(),
                        min_volume_ratio=config['min_volume_ratio'],
                        adx_threshold=config['adx_min']
                    )
                    
                    if detected and strength >= config['pattern_strength_min']:
                        # Get news for this stock
                        company_name = self.company_names.get(symbol, None)
                        news_articles = self.news_parser.get_stock_news(symbol, company_name, max_articles=2)
                        
                        patterns_found.append({
                            'symbol': symbol,
                            'pattern_type': details['pattern_type'],
                            'strength': strength,
                            'current_price': details['current_price'],
                            'resistance_level': details.get('resistance_level', 0),
                            'support_level': details.get('support_level', 0),
                            'breakout_percentage': details.get('breakout_percentage', 0),
                            'volume_ratio': details.get('volume_ratio', 0),
                            'rsi': details.get('rsi', 0),
                            'adx': details.get('adx', 0),
                            'details': details,
                            'news': news_articles,
                            'timestamp': datetime.now()
                        })
                        
                except Exception as e:
                    continue
            
            return patterns_found if patterns_found else None
            
        except Exception as e:
            return None

def create_professional_header():
    """Create enhanced professional header"""
    st.markdown("""
    <div class="professional-header">
        <h1>🚀 NSE F&O PCS Professional Scanner V5</h1>
        <div class="subtitle">⚡ Enhanced with Dynamic NSE Data & Google News Integration</div>
        <div class="description">🎯 Current-Day EOD Pattern Detection | 📰 Real-Time News Analysis | 🔄 Dynamic Stock Universe</div>
    </div>
    """, unsafe_allow_html=True)

def create_enhanced_sidebar():
    """Create enhanced sidebar with improved legibility"""
    with st.sidebar:
        st.markdown("### 🎛️ Scanner Controls")
        
        # Dynamic stock fetching option
        st.markdown("### 📊 Stock Universe")
        use_dynamic_list = st.checkbox("🔄 Fetch Latest NSE F&O List", 
                                     value=True, 
                                     help="Dynamically fetch the most current NSE F&O stock list")
        
        if use_dynamic_list:
            scanner = ProfessionalPCSScanner()
            stocks_to_scan = scanner.get_dynamic_fo_stocks()
            st.success(f"✅ Loaded {len(stocks_to_scan)} F&O stocks dynamically")
        else:
            # Use static comprehensive list
            nse_fetcher = DynamicNSEDataFetcher()
            stocks_to_scan = nse_fetcher._get_comprehensive_static_list()
            st.info(f"📋 Using static list: {len(stocks_to_scan)} stocks")
        
        # Enhanced stock selection
        with st.expander("🎯 Stock Selection", expanded=True):
            selected_category = st.selectbox(
                "Choose Category:",
                ["All F&O Stocks", "Custom Selection", "Top 100", "Nifty 50 Only"],
                help="Select which stocks to scan"
            )
            
            if selected_category == "Custom Selection":
                stocks_to_scan = st.multiselect(
                    "Select Stocks:",
                    options=stocks_to_scan,
                    default=stocks_to_scan[:20],
                    help="Choose specific stocks to scan"
                )
            elif selected_category == "Top 100":
                stocks_to_scan = stocks_to_scan[:100]
            elif selected_category == "Nifty 50 Only":
                nifty_50 = ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
                           'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS']
                stocks_to_scan = [s for s in stocks_to_scan if s in nifty_50]
        
        # Technical Filters
        with st.expander("📈 Technical Filters", expanded=True):
            rsi_min, rsi_max = st.slider("RSI Range:", 0, 100, (40, 70), 5)
            adx_min = st.slider("ADX Minimum:", 15, 50, 20, 5)
            
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
        
        # Pattern strength filter
        pattern_strength_min = st.slider("Pattern Strength Min:", 50, 100, 65, 5)
        
        # Enhanced Scanning Options  
        with st.expander("🚀 Enhanced Scan Settings", expanded=True):
            max_stocks = st.selectbox(
                "Stocks to Scan:",
                ["All Stocks", "First 50", "First 100", "Custom Limit"],
                index=0,
                help="Choose how many stocks to scan"
            )
            
            if max_stocks == "Custom Limit":
                custom_limit = st.number_input("Custom Limit:", min_value=10, max_value=len(stocks_to_scan), value=50)
                stocks_limit = custom_limit
            elif max_stocks == "First 50":
                stocks_limit = 50
            elif max_stocks == "First 100":
                stocks_limit = 100
            else:
                stocks_limit = len(stocks_to_scan)
            
            show_charts = st.checkbox("Show Charts", value=True)
            show_news = st.checkbox("📰 Show News Analysis", value=True, help="Display Google News for matched stocks")
            export_results = st.checkbox("Export Results", value=False)
        
        # Market Sentiment
        st.markdown("### 🌍 Market Sentiment")
        
        scanner = ProfessionalPCSScanner()
        sentiment_data = scanner.get_market_sentiment_indicators()
        
        overall_sentiment = sentiment_data.get('overall', {})
        sentiment_level = overall_sentiment.get('sentiment', 'NEUTRAL')
        pcs_recommendation = overall_sentiment.get('pcs_recommendation', 'Moderate opportunities')
        
        if sentiment_level == 'BULLISH':
            st.success(f"🟢 **{sentiment_level}** Market")
        elif sentiment_level == 'BEARISH':
            st.error(f"🔴 **{sentiment_level}** Market")
        else:
            st.warning(f"🟡 **{sentiment_level}** Market")
        
        st.info(f"💡 {pcs_recommendation}")
        
        # Real-time update
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
            'show_charts': show_charts,
            'show_news': show_news,
            'export_results': export_results,
            'stocks_limit': stocks_limit,
            'market_sentiment': sentiment_data,
            'use_dynamic_list': use_dynamic_list
        }

def display_pattern_result_with_news(result):
    """Enhanced result display with news integration"""
    symbol = result['symbol']
    pattern_type = result['pattern_type']
    strength = result['strength']
    news_articles = result.get('news', [])
    
    # Determine confidence level
    if strength >= 80:
        confidence_class = 'high-confidence'
        confidence_text = 'HIGH'
        confidence_color = 'green'
    elif strength >= 65:
        confidence_class = 'medium-confidence'
        confidence_text = 'MEDIUM'
        confidence_color = 'orange'
    else:
        confidence_class = 'low-confidence'
        confidence_text = 'LOW'
        confidence_color = 'red'
    
    # Main pattern card
    st.markdown(f"""
    <div class="pattern-card {confidence_class}">
        <h3 style="margin: 0 0 8px 0; color: #48BB78;">
            📈 {symbol} - {pattern_type}
        </h3>
        <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
            <span><strong>Strength:</strong> {strength}%</span>
            <span style="color: {confidence_color};"><strong>Confidence:</strong> {confidence_text}</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9em;">
            <div><strong>Current Price:</strong> ₹{result['current_price']:.2f}</div>
            <div><strong>Breakout:</strong> {result['breakout_percentage']:.2f}%</div>
            <div><strong>Volume Ratio:</strong> {result['volume_ratio']:.1f}x</div>
            <div><strong>RSI:</strong> {result['rsi']:.1f}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # News section
    if news_articles:
        st.markdown("#### 📰 Latest News Analysis")
        
        for i, article in enumerate(news_articles):
            sentiment = article['sentiment']
            sentiment_color = {
                'BULLISH': '#48BB78',
                'BEARISH': '#E53E3E', 
                'NEUTRAL': '#DD6B20'
            }.get(sentiment, '#DD6B20')
            
            sentiment_class = f"sentiment-{sentiment.lower()}"
            
            st.markdown(f"""
            <div class="news-card {sentiment_class}" style="margin: 8px 0; padding: 12px;">
                <div style="display: flex; justify-content: between; margin-bottom: 6px;">
                    <h5 style="margin: 0; color: #E2E8F0;">{article['title']}</h5>
                    <span style="color: {sentiment_color}; font-weight: bold; font-size: 0.8em;">
                        {sentiment}
                    </span>
                </div>
                <p style="margin: 4px 0; color: #CBD5E0; font-size: 0.85em;">
                    {article['summary']}
                </p>
                <div style="font-size: 0.75em; color: #A0AEC0;">
                    📅 {article['published']}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")

def create_enhanced_main_scanner_tab(config):
    """Enhanced main scanner tab with news integration"""
    st.markdown("### 🎯 Enhanced Current Day EOD Pattern Scanner")
    st.info("🔥 **V5 Features**: Dynamic NSE data, Google News integration, improved pattern detection")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button("🚀 Start Enhanced PCS Scan", type="primary", key="enhanced_scan")
    
    with col2:
        if config['export_results']:
            export_button = st.button("📊 Export", key="export")
        else:
            st.markdown("*Enable export*")
    
    with col3:
        st.markdown(f"**Scanning: {len(config['stocks_to_scan'])} stocks**")
    
    if scan_button:
        scanner = ProfessionalPCSScanner()
        
        # Progress tracking with enhanced display
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        # Status metrics
        metrics_container = st.container()
        with metrics_container:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                scanned_metric = st.empty()
            with col2:
                patterns_metric = st.empty()
            with col3:
                news_metric = st.empty()
            with col4:
                time_metric = st.empty()
        
        results = []
        total_stocks = len(config['stocks_to_scan'])
        start_time = time.time()
        
        # Add scanning progress animation
        st.markdown('<div class="scanning-progress"></div>', unsafe_allow_html=True)
        
        # Parallel processing for better performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_symbol = {
                executor.submit(scanner.scan_stock_for_patterns, symbol, config): symbol
                for symbol in config['stocks_to_scan']
            }
            
            for i, future in enumerate(as_completed(future_to_symbol), 1):
                symbol = future_to_symbol[future]
                
                try:
                    patterns = future.result(timeout=30)
                    if patterns:
                        results.extend(patterns)
                    
                    # Update progress
                    progress = i / total_stocks
                    progress_bar.progress(progress)
                    
                    elapsed_time = time.time() - start_time
                    eta = (elapsed_time / i) * (total_stocks - i) if i > 0 else 0
                    
                    status_container.info(f"📊 Scanning: {symbol} ({i}/{total_stocks}) | ETA: {eta:.0f}s")
                    
                    # Update metrics
                    scanned_metric.metric("Scanned", f"{i}/{total_stocks}")
                    patterns_metric.metric("Patterns Found", len(results))
                    news_metric.metric("News Articles", sum(len(r.get('news', [])) for r in results))
                    time_metric.metric("Elapsed", f"{elapsed_time:.0f}s")
                    
                except Exception as e:
                    continue
        
        # Final results
        progress_bar.progress(1.0)
        status_container.success(f"✅ Scan Complete! Found {len(results)} patterns with news analysis")
        
        if results:
            # Sort by strength
            results.sort(key=lambda x: x['strength'], reverse=True)
            
            st.markdown("### 🎯 Pattern Detection Results with News Analysis")
            
            # Results summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Patterns", len(results))
            with col2:
                avg_strength = np.mean([r['strength'] for r in results])
                st.metric("Avg Strength", f"{avg_strength:.1f}%")
            with col3:
                news_count = sum(len(r.get('news', [])) for r in results)
                st.metric("News Articles", news_count)
            
            # Display results with news
            for result in results:
                display_pattern_result_with_news(result)
                
        else:
            st.warning("🔍 No patterns found matching current criteria. Try adjusting the filters.")

def main():
    """Enhanced main application"""
    create_professional_header()
    
    # Sidebar configuration
    config = create_enhanced_sidebar()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Enhanced Scanner", "📊 Pattern Library", "⚙️ Settings"])
    
    with tab1:
        create_enhanced_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📚 PCS Pattern Library")
        st.info("**V5 Enhancement**: All patterns now include Google News analysis and dynamic NSE data")
        
        patterns_info = {
            "Cup and Handle": {
                "description": "Classic continuation pattern with cup formation followed by handle breakout",
                "success_rate": "85%",
                "timeframe": "4-12 weeks",
                "key_features": "Rounded bottom, tight handle, volume confirmation"
            },
            "Flat Base": {
                "description": "Tight consolidation pattern showing institutional accumulation", 
                "success_rate": "82%",
                "timeframe": "3-8 weeks",
                "key_features": "Low volatility, tight range, volume breakout"
            },
            "VCP (Volatility Contraction)": {
                "description": "Progressive volatility reduction leading to explosive breakout",
                "success_rate": "78%", 
                "timeframe": "6-15 weeks",
                "key_features": "Contracting ranges, diminishing volume, final squeeze"
            },
            "High Tight Flag": {
                "description": "Strong move followed by tight sideways consolidation",
                "success_rate": "88%",
                "timeframe": "1-4 weeks", 
                "key_features": "Prior 20%+ move, tight flag, low volume"
            },
            "Ascending Triangle": {
                "description": "Bullish pattern with horizontal resistance and rising support",
                "success_rate": "76%",
                "timeframe": "4-8 weeks",
                "key_features": "Flat top, rising lows, volume expansion"
            }
        }
        
        for pattern, info in patterns_info.items():
            with st.expander(f"📈 {pattern} - Success Rate: {info['success_rate']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Description:** {info['description']}")
                    st.write(f"**Timeframe:** {info['timeframe']}")
                with col2:
                    st.write(f"**Key Features:** {info['key_features']}")
                    st.success(f"**Enhanced in V5:** Now includes real-time news sentiment analysis")
    
    with tab3:
        st.markdown("### ⚙️ Scanner Settings & Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔧 Current Configuration")
            st.json({
                "Stocks to scan": len(config['stocks_to_scan']),
                "RSI Range": f"{config['rsi_min']}-{config['rsi_max']}",
                "ADX Minimum": config['adx_min'],
                "Volume Ratio": config['min_volume_ratio'],
                "Pattern Strength": f"{config['pattern_strength_min']}%",
                "Dynamic NSE List": config['use_dynamic_list'],
                "News Analysis": config['show_news']
            })
        
        with col2:
            st.markdown("#### 📊 V5 Enhancements")
            st.success("✅ Dynamic NSE F&O list fetching")
            st.success("✅ Google News integration") 
            st.success("✅ Improved sidebar legibility")
            st.success("✅ Enhanced pattern detection")
            st.success("✅ Real-time sentiment analysis")
            st.success("✅ Better error handling")
        
        st.markdown("#### 🚀 Version History")
        versions = {
            "V5.0": "Dynamic NSE data, Google News, Enhanced UI",
            "V4.0": "Current-day EOD confirmation, Angel One theme", 
            "V3.0": "Complete stock universe, Professional UI",
            "V2.0": "Fixed false negatives, Better filters",
            "V1.0": "Basic PCS pattern detection"
        }
        
        for version, features in versions.items():
            st.info(f"**{version}**: {features}")

if __name__ == "__main__":
    main()
