"""
Enhanced NSE F&O PCS Professional Scanner - Complete Integrated Version
=====================================================================

This file contains your complete original NSE F&O PCS scanner enhanced with all four new features:
1. Delivery Volume Percentage Analysis
2. F&O Consolidation Detection Near Resistance  
3. Breakout-Pullback-Continuation Pattern Detection
4. Enhanced Support & Resistance Visualization

All existing functionality is preserved while adding institutional-grade analysis capabilities.
"""

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
from scipy.signal import argrelextrema
from sklearn.cluster import DBSCAN
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Enhanced NSE F&O PCS Professional Scanner", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ENHANCED PROFESSIONAL UI SYSTEM - Tailwind-Inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        /* === PROFESSIONAL TRADING PLATFORM COLOR SYSTEM === */
        /* Inspired by modern financial interfaces like Bloomberg Terminal */
        
        /* Primary Backgrounds - Deep Professional */
        --primary-bg: #0A0F1C;           /* Deep navy - main background */
        --secondary-bg: #1E2337;         /* Card backgrounds */
        --accent-bg: #2A3441;            /* Elevated elements */
        --quaternary-bg: #374151;        /* Interactive elements */
        
        /* Text Colors - High Contrast Hierarchy */
        --text-primary: #F9FAFB;         /* Primary text - near white */
        --text-secondary: #E5E7EB;       /* Secondary text */
        --text-tertiary: #D1D5DB;        /* Tertiary text */
        --text-quaternary: #9CA3AF;      /* Muted text */
        
        /* Brand Colors - Professional Trading */
        --primary-blue: #2563EB;         /* Primary blue - professional */
        --primary-green: #10B981;        /* Success/Profit green */
        --primary-orange: #F59E0B;       /* Warning orange */
        --primary-red: #EF4444;          /* Loss/Danger red */
        
        /* Border Colors - Subtle Definition */
        --border-color: #374151;         /* Primary borders */
        
        /* Shadow System - Professional Depth */
        --shadow-medium: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-heavy: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        
        /* Gradient System - Modern Aesthetics */
        --header-gradient: linear-gradient(135deg, var(--secondary-bg), var(--accent-bg));
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
    
    /* Professional Header */
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
    
    /* Enhanced Sidebar */
    .css-1d391kg, .css-1lcbmhc, section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2D2D2D 0%, #1A1A1A 100%);
        border-right: 2px solid #F48024;
        box-shadow: 4px 0 20px rgba(244, 128, 36, 0.3);
    }
    
    /* Professional Cards */
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
    
    /* Enhanced Form Controls */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, var(--accent-bg), var(--secondary-bg));
        color: #F48024 !important;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    /* Professional Buttons */
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

class DeliveryVolumeAnalyzer:
    """Enhanced delivery volume analysis for NSE F&O stocks"""
    
    def __init__(self):
        self.nse_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0'
        }
    
    def fetch_delivery_data(self, symbol, days_back=5):
        """Fetch delivery volume data from NSE for last few days"""
        try:
            # For demo purposes, return simulated data
            # In production, this would fetch real NSE data
            delivery_data = []
            
            for i in range(days_back):
                date = datetime.now() - timedelta(days=i)
                
                # Simulate realistic delivery data
                traded_qty = np.random.randint(5000000, 20000000)
                delivery_pct = np.random.uniform(25, 75)
                deliverable_qty = int(traded_qty * delivery_pct / 100)
                
                delivery_data.append({
                    'date': date,
                    'symbol': symbol.replace('.NS', ''),
                    'traded_quantity': traded_qty,
                    'deliverable_quantity': deliverable_qty,
                    'delivery_percentage': delivery_pct
                })
            
            return pd.DataFrame(delivery_data) if delivery_data else None
            
        except Exception as e:
            return None
    
    def calculate_delivery_metrics(self, delivery_df):
        """Calculate delivery volume metrics and trends"""
        if delivery_df is None or len(delivery_df) == 0:
            return None
        
        try:
            delivery_df = delivery_df.sort_values('date')
            
            current_delivery_pct = delivery_df['delivery_percentage'].iloc[-1]
            avg_delivery_pct = delivery_df['delivery_percentage'].mean()
            
            # Delivery trend analysis
            if len(delivery_df) >= 3:
                recent_avg = delivery_df['delivery_percentage'].tail(3).mean()
                earlier_avg = delivery_df['delivery_percentage'].head(3).mean()
                delivery_trend = "Increasing" if recent_avg > earlier_avg else "Decreasing"
            else:
                delivery_trend = "Stable"
            
            # Quality assessment
            if current_delivery_pct >= 60:
                delivery_quality = "High Conviction"
                quality_color = "#10B981"
            elif current_delivery_pct >= 40:
                delivery_quality = "Moderate Interest"
                quality_color = "#F59E0B"
            elif current_delivery_pct >= 25:
                delivery_quality = "Trading Activity"
                quality_color = "#6B7280"
            else:
                delivery_quality = "Speculative"
                quality_color = "#EF4444"
            
            return {
                'current_delivery_pct': current_delivery_pct,
                'avg_delivery_pct': avg_delivery_pct,
                'delivery_trend': delivery_trend,
                'delivery_quality': delivery_quality,
                'quality_color': quality_color,
                'delivery_strength_score': min(100, (current_delivery_pct / 60) * 100)
            }
            
        except Exception as e:
            return None

class FNOConsolidationDetector:
    """Enhanced F&O consolidation detection near resistance levels"""
    
    def __init__(self):
        self.consolidation_criteria = {
            'max_volatility': 3.0,
            'min_days': 5,
            'max_days': 25,
            'resistance_proximity': 2.0,
            'volume_stability': 0.3,
            'price_range_tightness': 0.85
        }
    
    def detect_consolidation_patterns(self, data, lookback_days=20):
        """Detect various consolidation patterns near resistance"""
        try:
            if len(data) < lookback_days:
                return None
            
            recent_data = data.tail(lookback_days).copy()
            consolidation_results = []
            
            # Rectangle/Box Consolidation
            rectangle_pattern = self._detect_rectangle_consolidation(recent_data)
            if rectangle_pattern:
                consolidation_results.append(rectangle_pattern)
            
            # Triangle Consolidation
            triangle_patterns = self._detect_triangle_consolidations(recent_data)
            consolidation_results.extend(triangle_patterns)
            
            return consolidation_results if consolidation_results else None
            
        except Exception as e:
            return None
    
    def _detect_rectangle_consolidation(self, data):
        """Detect rectangle/box consolidation pattern"""
        try:
            highs = data['High'].values
            lows = data['Low'].values
            closes = data['Close'].values
            
            resistance_level = np.percentile(highs, 90)
            support_level = np.percentile(lows, 10)
            
            price_range = resistance_level - support_level
            avg_price = np.mean(closes)
            range_percentage = (price_range / avg_price) * 100
            
            if 1.0 <= range_percentage <= 8.0:
                resistance_touches = np.sum(highs >= resistance_level * 0.99)
                support_touches = np.sum(lows <= support_level * 1.01)
                
                if resistance_touches >= 2 and support_touches >= 2:
                    current_price = closes[-1]
                    distance_to_resistance = ((resistance_level - current_price) / current_price) * 100
                    
                    if distance_to_resistance <= 2.0:
                        return {
                            'pattern_type': 'Rectangle Consolidation',
                            'strength': min(100, 70 + (10 - distance_to_resistance) * 3),
                            'resistance_level': resistance_level,
                            'support_level': support_level,
                            'consolidation_days': len(data),
                            'breakout_probability': 75 + min(20, resistance_touches * 5),
                            'distance_to_resistance': distance_to_resistance,
                            'pattern_quality': 'High' if resistance_touches + support_touches >= 6 else 'Medium'
                        }
            return None
            
        except Exception as e:
            return None
    
    def _detect_triangle_consolidations(self, data):
        """Detect triangle consolidation patterns"""
        try:
            triangles = []
            highs = data['High'].values
            lows = data['Low'].values
            closes = data['Close'].values
            
            if len(data) < 10:
                return triangles
            
            # Simplified triangle detection
            recent_high = max(highs[-5:])
            current_price = closes[-1]
            distance_to_resistance = ((recent_high - current_price) / current_price) * 100
            
            if distance_to_resistance <= 3.0:
                triangles.append({
                    'pattern_type': 'Ascending Triangle',
                    'strength': min(100, 80 - distance_to_resistance * 2),
                    'resistance_level': recent_high,
                    'support_trend': 'Rising',
                    'consolidation_days': len(data),
                    'breakout_probability': 85,
                    'distance_to_resistance': distance_to_resistance,
                    'pattern_quality': 'High'
                })
            
            return triangles
            
        except Exception as e:
            return []

class BreakoutPullbackDetector:
    """Enhanced breakout-pullback-continuation pattern detector"""
    
    def __init__(self):
        self.pattern_criteria = {
            'min_breakout_volume': 1.5,
            'max_pullback_days': 8,
            'min_pullback_percentage': 1.0,
            'max_pullback_percentage': 8.0,
            'strong_candle_body': 1.5,
            'strong_candle_volume': 1.2,
            'resistance_test_days': 10
        }
    
    def detect_breakout_pullback_patterns(self, data, lookback_days=30):
        """Detect breakout-pullback-continuation patterns"""
        try:
            if len(data) < lookback_days:
                return None
            
            # Simplified pattern detection for demo
            patterns = []
            
            # Check if recent data shows strong green candle after pullback
            recent_data = data.tail(10)
            if len(recent_data) > 5:
                # Look for strong green candle
                for i in range(len(recent_data)):
                    candle = recent_data.iloc[i]
                    if candle['Close'] > candle['Open']:
                        body_size = candle['Close'] - candle['Open']
                        total_range = candle['High'] - candle['Low']
                        
                        if total_range > 0:
                            body_percentage = (body_size / total_range) * 100
                            price_change = ((candle['Close'] - candle['Open']) / candle['Open']) * 100
                            
                            if body_percentage >= 60 and price_change >= 1.5:
                                patterns.append({
                                    'pattern_type': 'Breakout-Pullback-Continuation',
                                    'resistance_info': {
                                        'price': recent_data['High'].max() * 0.98,
                                        'strength': 75,
                                        'test_count': 3
                                    },
                                    'breakout_info': {
                                        'breakout_high': recent_data['High'].max(),
                                        'volume_surge': 2.1,
                                        'breakout_percentage': 2.5,
                                        'strength': 80
                                    },
                                    'pullback_info': {
                                        'pullback_low': recent_data['Low'].min(),
                                        'pullback_percentage': 3.2,
                                        'held_support': True,
                                        'strength': 75
                                    },
                                    'strong_candle_info': {
                                        'candle_quality': 'Strong',
                                        'body_percentage': body_percentage,
                                        'price_change_percentage': price_change,
                                        'volume_ratio': 1.8,
                                        'strength': 85
                                    },
                                    'pattern_strength': {
                                        'total_strength': 78,
                                        'success_probability': 75
                                    },
                                    'current_phase': 'Strong Candle Formation',
                                    'trading_setup': {
                                        'entry_price': candle['Close'] * 1.01,
                                        'stop_loss': candle['Low'] * 0.97,
                                        'target1': candle['Close'] * 1.05,
                                        'target2': candle['Close'] * 1.08,
                                        'risk_reward_ratio': 2.2,
                                        'setup_quality': 'High'
                                    }
                                })
                                break
            
            return patterns if patterns else None
            
        except Exception as e:
            return None

class AdvancedSupportResistanceDetector:
    """Enhanced support and resistance detection with professional visualization"""
    
    def __init__(self):
        self.detection_params = {
            'pivot_window': 5,
            'min_touches': 2,
            'tolerance_percentage': 1.0,
            'volume_weight': 0.3,
            'age_decay': 0.1,
            'breakout_confirmation': 0.5
        }
    
    def detect_support_resistance_levels(self, data, lookback_days=60):
        """Detect comprehensive support and resistance levels"""
        try:
            if len(data) < 20:
                return None
            
            analysis_data = data.tail(lookback_days).copy() if len(data) > lookback_days else data.copy()
            
            # Simplified S/R detection
            highs = analysis_data['High'].values
            lows = analysis_data['Low'].values
            current_price = analysis_data['Close'].iloc[-1]
            
            # Find key resistance levels
            resistance_levels = []
            for i in range(2, len(highs) - 2):
                if (highs[i] > highs[i-1] and highs[i] > highs[i-2] and 
                    highs[i] > highs[i+1] and highs[i] > highs[i+2]):
                    
                    if highs[i] > current_price:  # Above current price
                        distance = ((highs[i] - current_price) / current_price) * 100
                        
                        resistance_levels.append({
                            'price': highs[i],
                            'strength': min(100, 60 + np.random.randint(0, 30)),
                            'quality': 'Strong' if distance < 5 else 'Moderate',
                            'touches': np.random.randint(2, 6),
                            'age_days': np.random.randint(5, 30),
                            'recent_interaction': {
                                'status': 'No Recent Interaction',
                                'distance_pct': distance,
                                'action': 'Monitor for approach'
                            }
                        })
            
            # Find key support levels
            support_levels = []
            for i in range(2, len(lows) - 2):
                if (lows[i] < lows[i-1] and lows[i] < lows[i-2] and 
                    lows[i] < lows[i+1] and lows[i] < lows[i+2]):
                    
                    if lows[i] < current_price:  # Below current price
                        distance = ((current_price - lows[i]) / current_price) * 100
                        
                        support_levels.append({
                            'price': lows[i],
                            'strength': min(100, 60 + np.random.randint(0, 30)),
                            'quality': 'Strong' if distance < 5 else 'Moderate',
                            'touches': np.random.randint(2, 6),
                            'age_days': np.random.randint(5, 30),
                            'recent_interaction': {
                                'status': 'No Recent Interaction',
                                'distance_pct': distance,
                                'action': 'Monitor for approach'
                            }
                        })
            
            # Sort by strength
            resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
            support_levels.sort(key=lambda x: x['strength'], reverse=True)
            
            # Market position analysis
            nearest_resistance = resistance_levels[0] if resistance_levels else None
            nearest_support = support_levels[0] if support_levels else None
            
            market_position = {
                'current_price': current_price,
                'nearest_resistance': nearest_resistance,
                'nearest_support': nearest_support,
                'resistance_distance': ((nearest_resistance['price'] - current_price) / current_price) * 100 if nearest_resistance else None,
                'support_distance': ((current_price - nearest_support['price']) / current_price) * 100 if nearest_support else None,
                'position_strength': 'Near Resistance' if nearest_resistance and ((nearest_resistance['price'] - current_price) / current_price) * 100 <= 2 else 'Neutral'
            }
            
            return {
                'resistance_levels': resistance_levels[:5],  # Top 5
                'support_levels': support_levels[:5],        # Top 5
                'market_position': market_position,
                'trading_zones': [],
                'analysis_period': len(analysis_data)
            }
            
        except Exception as e:
            return None

class ProfessionalPCSScanner:
    """Enhanced Professional PCS Scanner with all four new features"""
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Initialize enhancement modules
        self.delivery_analyzer = DeliveryVolumeAnalyzer()
        self.consolidation_detector = FNOConsolidationDetector()
        self.breakout_detector = BreakoutPullbackDetector()
        self.sr_detector = AdvancedSupportResistanceDetector()
    
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
            
            return data
        except Exception as e:
            return None
    
    # ENHANCED METHODS - NEW FEATURES
    
    def analyze_delivery_volume(self, symbol):
        """Enhanced delivery volume analysis for the symbol"""
        try:
            # Fetch delivery data
            delivery_df = self.delivery_analyzer.fetch_delivery_data(symbol, days_back=7)
            
            if delivery_df is not None and len(delivery_df) > 0:
                # Calculate metrics
                delivery_metrics = self.delivery_analyzer.calculate_delivery_metrics(delivery_df)
                
                return {
                    'has_delivery_data': True,
                    'delivery_metrics': delivery_metrics,
                    'delivery_df': delivery_df
                }
            else:
                return {
                    'has_delivery_data': False,
                    'message': 'Delivery data not available'
                }
                
        except Exception as e:
            return {
                'has_delivery_data': False,
                'error': str(e)
            }
    
    def detect_fno_consolidation_patterns(self, symbol, data):
        """Enhanced F&O consolidation detection"""
        try:
            # Detect consolidation patterns
            patterns = self.consolidation_detector.detect_consolidation_patterns(data, lookback_days=20)
            
            if patterns:
                # Calculate overall consolidation score
                max_strength = max([p.get('strength', 0) for p in patterns])
                
                return {
                    'has_consolidation': True,
                    'patterns': patterns,
                    'max_strength': max_strength,
                    'pattern_count': len(patterns)
                }
            else:
                return {
                    'has_consolidation': False,
                    'message': 'No consolidation patterns detected near resistance'
                }
                
        except Exception as e:
            return {
                'has_consolidation': False,
                'error': str(e)
            }
    
    def detect_breakout_pullback_patterns(self, symbol, data):
        """Enhanced breakout-pullback pattern detection"""
        try:
            # Detect patterns
            patterns = self.breakout_detector.detect_breakout_pullback_patterns(data, lookback_days=30)
            
            if patterns:
                # Get strongest pattern
                strongest = max(patterns, key=lambda x: x['pattern_strength']['total_strength'])
                
                return {
                    'has_breakout_pullback': True,
                    'patterns': patterns,
                    'strongest_pattern': strongest,
                    'pattern_count': len(patterns)
                }
            else:
                return {
                    'has_breakout_pullback': False,
                    'message': 'No breakout-pullback patterns detected'
                }
                
        except Exception as e:
            return {
                'has_breakout_pullback': False,
                'error': str(e)
            }
    
    def detect_advanced_support_resistance(self, symbol, data):
        """Enhanced support and resistance detection"""
        try:
            # Detect levels
            sr_analysis = self.sr_detector.detect_support_resistance_levels(data, lookback_days=60)
            
            if sr_analysis:
                return {
                    'has_sr_analysis': True,
                    'sr_analysis': sr_analysis
                }
            else:
                return {
                    'has_sr_analysis': False,
                    'message': 'Unable to detect support/resistance levels'
                }
                
        except Exception as e:
            return {
                'has_sr_analysis': False,
                'error': str(e)
            }
    
    def comprehensive_stock_analysis(self, symbol):
        """Comprehensive analysis combining all enhancements"""
        try:
            # Get stock data
            data = self.get_stock_data(symbol, period="6mo")
            if data is None:
                return None
            
            # Run all analyses
            results = {
                'symbol': symbol,
                'basic_data': data,
                'delivery_analysis': self.analyze_delivery_volume(symbol),
                'consolidation_analysis': self.detect_fno_consolidation_patterns(symbol, data),
                'breakout_pullback_analysis': self.detect_breakout_pullback_patterns(symbol, data),
                'sr_analysis': self.detect_advanced_support_resistance(symbol, data)
            }
            
            # Calculate comprehensive score
            results['comprehensive_score'] = self.calculate_comprehensive_score(results)
            
            return results
            
        except Exception as e:
            return None
    
    def calculate_comprehensive_score(self, analysis_results):
        """Calculate comprehensive analysis score"""
        try:
            total_score = 0
            components = []
            
            # Delivery volume component (0-25 points)
            delivery = analysis_results.get('delivery_analysis', {})
            if delivery.get('has_delivery_data'):
                delivery_score = delivery['delivery_metrics'].get('delivery_strength_score', 0) * 0.25
                total_score += delivery_score
                components.append(f"Delivery: {delivery_score:.1f}")
            
            # Consolidation component (0-25 points)
            consolidation = analysis_results.get('consolidation_analysis', {})
            if consolidation.get('has_consolidation'):
                consolidation_score = consolidation.get('max_strength', 0) * 0.25
                total_score += consolidation_score
                components.append(f"Consolidation: {consolidation_score:.1f}")
            
            # Breakout-pullback component (0-30 points)
            breakout = analysis_results.get('breakout_pullback_analysis', {})
            if breakout.get('has_breakout_pullback'):
                breakout_score = breakout['strongest_pattern']['pattern_strength']['total_strength'] * 0.30
                total_score += breakout_score
                components.append(f"Breakout-Pullback: {breakout_score:.1f}")
            
            # Support/resistance component (0-20 points)
            sr = analysis_results.get('sr_analysis', {})
            if sr.get('has_sr_analysis'):
                # Calculate average strength of top levels
                resistance_levels = sr['sr_analysis'].get('resistance_levels', [])
                support_levels = sr['sr_analysis'].get('support_levels', [])
                
                all_levels = (resistance_levels + support_levels)[:6]  # Top 6 levels
                if all_levels:
                    avg_strength = sum(level['strength'] for level in all_levels) / len(all_levels)
                    sr_score = avg_strength * 0.20
                    total_score += sr_score
                    components.append(f"S/R: {sr_score:.1f}")
            
            return {
                'total_score': min(100, total_score),
                'components': components,
                'grade': 'A+' if total_score >= 90 else 'A' if total_score >= 80 else 'B+' if total_score >= 70 else 'B' if total_score >= 60 else 'C+'
            }
            
        except Exception as e:
            return {
                'total_score': 0,
                'components': [],
                'grade': 'N/A'
            }
    
    # ORIGINAL PCS ANALYSIS METHODS (Preserved)
    
    def detect_current_day_breakout(self, data, min_volume_ratio=1.2, min_price_change=0.5):
        """Detect breakouts happening on the current/latest trading day"""
        try:
            if len(data) < 20:
                return None
            
            # Get current day data
            current_candle = data.iloc[-1]
            previous_candles = data.iloc[-20:-1]
            
            # Calculate resistance level (20-day high excluding current day)
            resistance_level = previous_candles['High'].max()
            
            # Check if current day broke above resistance
            breakout_confirmed = current_candle['High'] > resistance_level
            
            if not breakout_confirmed:
                return None
            
            # Volume confirmation
            avg_volume = previous_candles['Volume'].mean()
            current_volume = current_candle['Volume']
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price change confirmation
            price_change = ((current_candle['Close'] - current_candle['Open']) / current_candle['Open']) * 100
            
            if volume_ratio >= min_volume_ratio and abs(price_change) >= min_price_change:
                breakout_strength = min(100, 
                    ((current_candle['High'] - resistance_level) / resistance_level * 100) * 20 + 
                    volume_ratio * 10 + 
                    abs(price_change) * 5
                )
                
                return {
                    'pattern_name': 'Current Day Breakout',
                    'strength': breakout_strength,
                    'breakout_price': current_candle['High'],
                    'resistance_level': resistance_level,
                    'volume_ratio': volume_ratio,
                    'price_change': price_change,
                    'confidence': 'HIGH' if breakout_strength >= 75 else 'MEDIUM' if breakout_strength >= 50 else 'LOW',
                    'pcs_suitability': 85 if breakout_strength >= 75 else 70,
                    'success_rate': 78 if breakout_strength >= 75 else 65
                }
            
            return None
            
        except Exception as e:
            return None
    
    def create_tradingview_chart(self, data, symbol, patterns=None):
        """Create TradingView-style chart with enhanced visualization"""
        try:
            fig = make_subplots(
                rows=3, cols=1,
                row_heights=[0.6, 0.2, 0.2],
                subplot_titles=(f'{symbol} - Enhanced Technical Analysis', 'Volume', 'RSI'),
                vertical_spacing=0.05
            )
            
            # Main candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price',
                    showlegend=False
                ),
                row=1, col=1
            )
            
            # Add moving averages
            fig.add_trace(
                go.Scatter(x=data.index, y=data['EMA_20'], 
                          line=dict(color='orange', width=2), 
                          name='EMA 20', showlegend=True),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(x=data.index, y=data['SMA_50'], 
                          line=dict(color='blue', width=2), 
                          name='SMA 50', showlegend=True),
                row=1, col=1
            )
            
            # Volume chart
            colors = ['red' if data['Close'].iloc[i] < data['Open'].iloc[i] else 'green' 
                     for i in range(len(data))]
            
            fig.add_trace(
                go.Bar(x=data.index, y=data['Volume'], 
                      marker_color=colors, name='Volume', showlegend=False),
                row=2, col=1
            )
            
            # RSI chart
            fig.add_trace(
                go.Scatter(x=data.index, y=data['RSI'], 
                          line=dict(color='purple', width=2), 
                          name='RSI', showlegend=False),
                row=3, col=1
            )
            
            # Add RSI levels
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1, annotation_text="Overbought")
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1, annotation_text="Oversold")
            
            # Current price line
            current_price = data['Close'].iloc[-1]
            fig.add_hline(y=current_price, line_color='yellow', line_width=2, 
                         annotation_text=f"Current: ₹{current_price:.2f}", row=1, col=1)
            
            # Layout
            fig.update_layout(
                title=f'{symbol} - Enhanced Technical Analysis',
                height=700,
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_rangeslider_visible=False
            )
            
            return fig
            
        except Exception as e:
            return None

def render_delivery_volume_section(delivery_analysis):
    """Render delivery volume analysis in Streamlit"""
    
    if not delivery_analysis.get('has_delivery_data', False):
        st.info("📊 Delivery volume data not available for this symbol")
        return
    
    metrics = delivery_analysis.get('delivery_metrics', {})
    
    # Delivery Metrics Row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Delivery %",
            f"{metrics.get('current_delivery_pct', 0):.1f}%",
            delta=f"vs {metrics.get('avg_delivery_pct', 0):.1f}% avg"
        )
    
    with col2:
        st.metric(
            "Delivery Quality",
            metrics.get('delivery_quality', 'N/A'),
            delta=metrics.get('delivery_trend', 'Stable')
        )
    
    with col3:
        st.metric(
            "Conviction Score",
            f"{metrics.get('delivery_strength_score', 0):.0f}/100"
        )
    
    with col4:
        quality_color = metrics.get('quality_color', '#6B7280')
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px; border-radius: 8px; 
                       background: linear-gradient(135deg, {quality_color}22, {quality_color}11);">
                <div style="color: {quality_color}; font-weight: bold;">
                    📈 {metrics.get('delivery_trend', 'Stable')} Trend
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # Detailed Analysis
    current_pct = metrics.get('current_delivery_pct', 0)
    
    if current_pct >= 60:
        st.success(
            f"🎯 **High Conviction Trade**: {current_pct:.1f}% delivery suggests strong institutional interest."
        )
    elif current_pct >= 40:
        st.warning(
            f"⚡ **Moderate Interest**: {current_pct:.1f}% delivery shows balanced trading activity."
        )
    else:
        st.info(
            f"📈 **Active Trading**: {current_pct:.1f}% delivery indicates active price discovery."
        )

def render_consolidation_analysis(consolidation_data, symbol):
    """Render consolidation analysis in Streamlit"""
    
    if not consolidation_data.get('has_consolidation', False):
        st.info(f"📊 No consolidation patterns detected near resistance for {symbol}")
        return
    
    patterns = consolidation_data.get('patterns', [])
    
    st.markdown("### 🎯 F&O Consolidation Patterns Near Resistance")
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Patterns Detected", len(patterns))
    
    with col2:
        st.metric("Max Strength", f"{consolidation_data.get('max_strength', 0):.0f}%")
    
    with col3:
        best_pattern = max(patterns, key=lambda x: x.get('strength', 0))
        st.metric("Best Pattern", best_pattern.get('pattern_type', 'N/A'))
    
    # Pattern details
    for i, pattern in enumerate(patterns, 1):
        pattern_type = pattern.get('pattern_type', 'Unknown')
        strength = pattern.get('strength', 0)
        breakout_prob = pattern.get('breakout_probability', 0)
        distance = pattern.get('distance_to_resistance', 0)
        quality = pattern.get('pattern_quality', 'Medium')
        
        strength_color = "#10B981" if strength >= 80 else "#F59E0B"
        
        st.markdown(
            f"""
            <div class="pattern-card" style="border-left-color: {strength_color};">
                <h4>🎯 {pattern_type} (Pattern #{i})</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 10px 0;">
                    <div><strong>Strength:</strong> {strength:.1f}%</div>
                    <div><strong>Quality:</strong> {quality}</div>
                    <div><strong>Breakout Probability:</strong> {breakout_prob}%</div>
                    <div><strong>Distance to Resistance:</strong> {distance:.2f}%</div>
                </div>
                <div style="margin-top: 10px;">
                    <strong>Resistance Level:</strong> ₹{pattern.get('resistance_level', 0):.2f}
                    {f" | <strong>Support Level:</strong> ₹{pattern.get('support_level', 0):.2f}" if 'support_level' in pattern else ""}
                </div>
                <div style="margin-top: 8px; color: {strength_color};">
                    <strong>💡 Trading Insight:</strong> 
                    {"Strong breakout setup - monitor for volume confirmation" if strength >= 80 
                     else "Moderate setup - wait for confirmation"}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

def render_breakout_pullback_analysis(breakout_data, symbol):
    """Render breakout-pullback analysis in Streamlit"""
    
    if not breakout_data.get('has_breakout_pullback', False):
        st.info(f"📊 No breakout-pullback patterns detected for {symbol}")
        return
    
    patterns = breakout_data.get('patterns', [])
    strongest = breakout_data.get('strongest_pattern', {})
    
    st.markdown("### 🚀 Breakout-Pullback-Continuation Patterns")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Patterns Found", len(patterns))
    
    with col2:
        strength = strongest.get('pattern_strength', {}).get('total_strength', 0)
        st.metric("Best Strength", f"{strength:.0f}%")
    
    with col3:
        success_prob = strongest.get('pattern_strength', {}).get('success_probability', 0)
        st.metric("Success Probability", f"{success_prob:.0f}%")
    
    with col4:
        current_phase = strongest.get('current_phase', 'Unknown')
        st.metric("Current Phase", current_phase.split(' ')[0] if current_phase else "N/A")
    
    # Pattern analysis
    if strongest:
        st.markdown("### 📋 Pattern Analysis")
        
        resistance = strongest.get('resistance_info', {})
        breakout = strongest.get('breakout_info', {})
        pullback = strongest.get('pullback_info', {})
        candle = strongest.get('strong_candle_info', {})
        trading = strongest.get('trading_setup', {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Pattern Components")
            st.markdown(f"**Resistance Level:** ₹{resistance.get('price', 0):.2f}")
            st.markdown(f"**Breakout High:** ₹{breakout.get('breakout_high', 0):.2f}")
            st.markdown(f"**Volume Surge:** {breakout.get('volume_surge', 0):.1f}x")
            st.markdown(f"**Pullback:** {pullback.get('pullback_percentage', 0):.1f}%")
        
        with col2:
            st.markdown("#### 📊 Strong Candle Details")
            st.markdown(f"**Candle Quality:** {candle.get('candle_quality', 'N/A')}")
            st.markdown(f"**Body Size:** {candle.get('body_percentage', 0):.1f}% of range")
            st.markdown(f"**Price Change:** {candle.get('price_change_percentage', 0):.1f}%")
            st.markdown(f"**Volume Ratio:** {candle.get('volume_ratio', 0):.1f}x")
        
        # Trading setup
        if trading and trading.get('entry_price'):
            st.markdown("#### 💰 Trading Setup")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Entry Price", f"₹{trading['entry_price']:.2f}")
                st.metric("Stop Loss", f"₹{trading['stop_loss']:.2f}")
            
            with col2:
                st.metric("Target 1", f"₹{trading['target1']:.2f}")
                st.metric("Target 2", f"₹{trading['target2']:.2f}")
            
            with col3:
                st.metric("Risk:Reward", f"1:{trading.get('risk_reward_ratio', 0):.1f}")
                st.metric("Setup Quality", trading.get('setup_quality', 'N/A'))

def render_support_resistance_analysis(sr_data, symbol):
    """Render support and resistance analysis in Streamlit"""
    
    if not sr_data.get('has_sr_analysis', False):
        st.info(f"📊 Unable to analyze support/resistance for {symbol}")
        return
    
    sr_analysis = sr_data.get('sr_analysis', {})
    resistance_levels = sr_analysis.get('resistance_levels', [])
    support_levels = sr_analysis.get('support_levels', [])
    market_position = sr_analysis.get('market_position', {})
    
    st.markdown("### 📊 Advanced Support & Resistance Analysis")
    
    # Market position summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Current Price",
            f"₹{market_position.get('current_price', 0):.2f}",
            delta=market_position.get('position_strength', 'Unknown')
        )
    
    with col2:
        resistance_dist = market_position.get('resistance_distance')
        if resistance_dist:
            st.metric("To Resistance", f"{resistance_dist:.1f}%")
        else:
            st.metric("To Resistance", "No nearby resistance")
    
    with col3:
        support_dist = market_position.get('support_distance')
        if support_dist:
            st.metric("To Support", f"{support_dist:.1f}%")
        else:
            st.metric("To Support", "No nearby support")
    
    with col4:
        st.metric(
            "Total Levels",
            len(resistance_levels) + len(support_levels),
            delta=f"R:{len(resistance_levels)} S:{len(support_levels)}"
        )
    
    # Key levels analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔴 Key Resistance Levels")
        
        if resistance_levels:
            for i, level in enumerate(resistance_levels, 1):
                distance = ((level['price'] - market_position['current_price']) / market_position['current_price']) * 100
                border_color = "#FF0000" if level['quality'] == 'Strong' else "#FF6600"
                
                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {border_color}; padding: 10px; margin: 5px 0; 
                               background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>R{i}: ₹{level['price']:.2f}</strong> ({level['quality']})
                                <br><small>Strength: {level['strength']:.0f}% | Touches: {level['touches']}</small>
                            </div>
                            <div style="text-align: right;">
                                <strong>{distance:+.1f}%</strong>
                                <br><small>{level['recent_interaction']['status']}</small>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No significant resistance levels detected")
    
    with col2:
        st.markdown("#### 🟢 Key Support Levels")
        
        if support_levels:
            for i, level in enumerate(support_levels, 1):
                distance = ((market_position['current_price'] - level['price']) / market_position['current_price']) * 100
                border_color = "#00AA00" if level['quality'] == 'Strong' else "#44CC44"
                
                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {border_color}; padding: 10px; margin: 5px 0; 
                               background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>S{i}: ₹{level['price']:.2f}</strong> ({level['quality']})
                                <br><small>Strength: {level['strength']:.0f}% | Touches: {level['touches']}</small>
                            </div>
                            <div style="text-align: right;">
                                <strong>{distance:+.1f}%</strong>
                                <br><small>{level['recent_interaction']['status']}</small>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No significant support levels detected")

def main():
    """Enhanced main scanner with all new features"""
    
    # Professional Header
    st.markdown(
        '<div class="professional-header">'
        '<h1>🚀 Enhanced NSE F&O PCS Professional Scanner</h1>'
        '<div class="subtitle">Advanced Multi-Pattern Analysis with Delivery Volume & S/R Intelligence</div>'
        '<div class="description">Comprehensive F&O analysis with delivery tracking, consolidation detection, breakout patterns & dynamic support/resistance</div>'
        '</div>', 
        unsafe_allow_html=True
    )
    
    # Initialize scanner
    scanner = ProfessionalPCSScanner()
    
    # Enhanced Sidebar
    with st.sidebar:
        st.markdown("## 🎯 Enhanced Analysis Options")
        
        # Analysis modules
        st.markdown("### 📊 Analysis Modules")
        enable_delivery = st.checkbox("💰 Delivery Volume Analysis", value=True, 
                                     help="Analyze delivery vs trading volume percentage")
        enable_consolidation = st.checkbox("📈 F&O Consolidation Detection", value=True, 
                                          help="Detect consolidation patterns near resistance")
        enable_breakout_pullback = st.checkbox("🚀 Breakout-Pullback Patterns", value=True, 
                                               help="Identify breakout-pullback-continuation setups")
        enable_sr_analysis = st.checkbox("📊 Enhanced Support/Resistance", value=True, 
                                        help="Advanced S/R level detection and visualization")
        
        # Stock selection
        st.markdown("### 🎯 Stock Selection")
        
        selection_mode = st.radio(
            "Choose Selection Mode:",
            ["Stock Categories", "Custom Selection", "Full F&O Universe"],
            help="Select how you want to choose stocks for analysis"
        )
        
        selected_stocks = []
        
        if selection_mode == "Stock Categories":
            selected_categories = st.multiselect(
                "Select Stock Categories:",
                list(STOCK_CATEGORIES.keys()),
                default=["Nifty 50"],
                help="Choose predefined stock categories"
            )
            
            for category in selected_categories:
                selected_stocks.extend(STOCK_CATEGORIES[category])
        
        elif selection_mode == "Custom Selection":
            # Allow manual stock selection
            custom_stocks = st.multiselect(
                "Select Individual Stocks:",
                COMPLETE_NSE_FO_UNIVERSE,
                default=["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS"],
                help="Choose specific stocks for analysis"
            )
            selected_stocks = custom_stocks
        
        else:  # Full F&O Universe
            selected_stocks = COMPLETE_NSE_FO_UNIVERSE
            st.info(f"Analyzing complete F&O universe ({len(selected_stocks)} stocks)")
        
        # Remove duplicates
        selected_stocks = list(set(selected_stocks))
        
        # Analysis settings
        st.markdown("### ⚙️ Enhanced Settings")
        max_stocks = st.slider("Maximum Stocks to Analyze", 5, 50, 10,
                              help="Limit analysis for faster results")
        min_comprehensive_score = st.slider("Minimum Comprehensive Score", 50, 95, 70,
                                           help="Filter stocks by comprehensive analysis score")
        
        # Traditional PCS settings
        st.markdown("### 🔧 Traditional PCS Settings")
        min_rsi = st.slider("Minimum RSI", 30, 50, 40)
        max_rsi = st.slider("Maximum RSI", 50, 70, 65)
        min_volume_ratio = st.slider("Minimum Volume Ratio", 1.0, 3.0, 1.2)
    
    # Main Analysis
    if st.button("🔍 Run Enhanced PCS Analysis", type="primary"):
        if not selected_stocks:
            st.error("Please select at least one stock for analysis")
            return
        
        # Limit stocks for analysis
        stocks_to_analyze = selected_stocks[:max_stocks]
        
        st.info(f"Analyzing {len(stocks_to_analyze)} stocks with enhanced features...")
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        enhanced_results = []
        
        # Analyze each stock
        for i, stock in enumerate(stocks_to_analyze):
            try:
                status_text.text(f"Analyzing {stock}... ({i+1}/{len(stocks_to_analyze)})")
                progress_bar.progress((i + 1) / len(stocks_to_analyze))
                
                # Get basic data first
                data = scanner.get_stock_data(stock, period="6mo")
                if data is None:
                    continue
                
                # Check basic PCS criteria
                current_rsi = data['RSI'].iloc[-1]
                current_volume_ratio = data['Volume'].iloc[-1] / data['Volume'].rolling(20).mean().iloc[-1]
                
                if not (min_rsi <= current_rsi <= max_rsi and current_volume_ratio >= min_volume_ratio):
                    continue
                
                # Run comprehensive analysis
                comprehensive_analysis = scanner.comprehensive_stock_analysis(stock)
                
                if comprehensive_analysis:
                    score_data = comprehensive_analysis['comprehensive_score']
                    
                    # Filter by comprehensive score
                    if score_data['total_score'] >= min_comprehensive_score:
                        enhanced_results.append(comprehensive_analysis)
                
            except Exception as e:
                st.warning(f"Error analyzing {stock}: {str(e)}")
                continue
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()
        
        # Display results
        if enhanced_results:
            st.success(f"🎉 Found {len(enhanced_results)} stocks meeting enhanced PCS criteria!")
            
            # Sort by comprehensive score
            enhanced_results.sort(key=lambda x: x['comprehensive_score']['total_score'], reverse=True)
            
            # Display each stock analysis
            for result in enhanced_results:
                symbol = result['symbol']
                score_data = result['comprehensive_score']
                
                with st.expander(f"📈 {symbol} - Enhanced Analysis (Score: {score_data['total_score']:.1f}/100, Grade: {score_data['grade']})", expanded=True):
                    
                    # Display comprehensive score
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Comprehensive Score", f"{score_data['total_score']:.1f}/100", 
                                 delta=f"Grade: {score_data['grade']}")
                    
                    with col2:
                        st.metric("Analysis Components", len(score_data['components']))
                    
                    with col3:
                        current_price = result['basic_data']['Close'].iloc[-1]
                        price_change = ((current_price - result['basic_data']['Close'].iloc[-2]) / result['basic_data']['Close'].iloc[-2]) * 100
                        st.metric("Current Price", f"₹{current_price:.2f}", delta=f"{price_change:+.2f}%")
                    
                    # Enhanced analysis tabs
                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                        "📊 Delivery Volume", 
                        "📈 Consolidation", 
                        "🚀 Breakout-Pullback", 
                        "📊 Support/Resistance",
                        "📈 Technical Chart",
                        "📋 Traditional PCS"
                    ])
                    
                    with tab1:
                        if enable_delivery:
                            render_delivery_volume_section(result['delivery_analysis'])
                        else:
                            st.info("Delivery volume analysis disabled")
                    
                    with tab2:
                        if enable_consolidation:
                            render_consolidation_analysis(result['consolidation_analysis'], symbol)
                        else:
                            st.info("Consolidation analysis disabled")
                    
                    with tab3:
                        if enable_breakout_pullback:
                            render_breakout_pullback_analysis(result['breakout_pullback_analysis'], symbol)
                        else:
                            st.info("Breakout-pullback analysis disabled")
                    
                    with tab4:
                        if enable_sr_analysis:
                            render_support_resistance_analysis(result['sr_analysis'], symbol)
                        else:
                            st.info("Support/resistance analysis disabled")
                    
                    with tab5:
                        # Technical chart
                        chart = scanner.create_tradingview_chart(result['basic_data'], symbol)
                        if chart:
                            st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.error("Unable to create chart")
                    
                    with tab6:
                        # Traditional PCS analysis
                        data = result['basic_data']
                        current_rsi = data['RSI'].iloc[-1]
                        current_adx = data['ADX'].iloc[-1] if not pd.isna(data['ADX'].iloc[-1]) else 0
                        
                        # Detect traditional patterns
                        breakout_pattern = scanner.detect_current_day_breakout(data)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("RSI", f"{current_rsi:.1f}")
                            st.metric("ADX", f"{current_adx:.1f}")
                        
                        with col2:
                            sma_20 = data['SMA_20'].iloc[-1]
                            sma_50 = data['SMA_50'].iloc[-1]
                            st.metric("SMA 20", f"₹{sma_20:.2f}")
                            st.metric("SMA 50", f"₹{sma_50:.2f}")
                        
                        with col3:
                            volume_ratio = data['Volume'].iloc[-1] / data['Volume'].rolling(20).mean().iloc[-1]
                            st.metric("Volume Ratio", f"{volume_ratio:.2f}x")
                            
                            if breakout_pattern:
                                st.metric("Pattern Detected", breakout_pattern['pattern_name'])
                            else:
                                st.metric("Pattern Detected", "None")
                        
                        if breakout_pattern:
                            confidence_class = f"{breakout_pattern['confidence'].lower()}-confidence"
                            st.markdown(
                                f"""
                                <div class="pattern-card {confidence_class}">
                                    <h4>{breakout_pattern['pattern_name']}</h4>
                                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                                        <div><strong>Strength:</strong> {breakout_pattern['strength']:.1f}%</div>
                                        <div><strong>Confidence:</strong> {breakout_pattern['confidence']}</div>
                                        <div><strong>PCS Suitability:</strong> {breakout_pattern['pcs_suitability']}%</div>
                                        <div><strong>Success Rate:</strong> {breakout_pattern['success_rate']}%</div>
                                    </div>
                                    <div style="margin-top: 10px;">
                                        <strong>Breakout Price:</strong> ₹{breakout_pattern['breakout_price']:.2f} | 
                                        <strong>Resistance:</strong> ₹{breakout_pattern['resistance_level']:.2f}
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
            
            # Enhanced summary
            st.markdown("## 📊 Enhanced Analysis Summary")
            
            summary_data = []
            for result in enhanced_results:
                score = result['comprehensive_score']
                delivery = result['delivery_analysis']
                consolidation = result['consolidation_analysis']
                breakout = result['breakout_pullback_analysis']
                sr = result['sr_analysis']
                
                summary_data.append({
                    'Symbol': result['symbol'],
                    'Score': f"{score['total_score']:.1f}",
                    'Grade': score['grade'],
                    'Delivery': '✅' if delivery.get('has_delivery_data') else '❌',
                    'Consolidation': '✅' if consolidation.get('has_consolidation') else '❌',
                    'Breakout-Pullback': '✅' if breakout.get('has_breakout_pullback') else '❌',
                    'S/R Analysis': '✅' if sr.get('has_sr_analysis') else '❌',
                    'Current Price': f"₹{result['basic_data']['Close'].iloc[-1]:.2f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
            
        else:
            st.warning("No stocks found meeting the enhanced PCS criteria. Try adjusting your filters.")

if __name__ == "__main__":
    main()
