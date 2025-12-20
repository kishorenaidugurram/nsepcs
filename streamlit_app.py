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
    page_title="NSE F&O PCS Professional Scanner V7.0", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# =================== PROFESSIONAL THEME SYSTEM ===================

def inject_professional_theme():
    """Professional Financial Platform Theme - Bloomberg/Refinitiv Style"""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            /* Professional Teal Theme */
            --primary-50: #f0fdfa;
            --primary-100: #ccfbf1;
            --primary-200: #99f6e4;
            --primary-500: #14b8a6;
            --primary-600: #0d9488;
            --primary-700: #0f766e;
            --primary-800: #115e59;
            
            /* Neutral Grays */
            --gray-50: #f9fafb;
            --gray-100: #f3f4f6;
            --gray-200: #e5e7eb;
            --gray-300: #d1d5db;
            --gray-400: #9ca3af;
            --gray-500: #6b7280;
            --gray-600: #4b5563;
            --gray-700: #374151;
            --gray-800: #1f2937;
            --gray-900: #111827;
            
            /* Semantic Colors */
            --success: #059669;
            --success-light: #d1fae5;
            --warning: #d97706;
            --warning-light: #fef3c7;
            --error: #dc2626;
            --error-light: #fee2e2;
            --info: #0284c7;
            --info-light: #e0f2fe;
            
            /* Shadows */
            --shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
            --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
            
            /* Spacing & Border Radius */
            --space-4: 1rem;
            --space-6: 1.5rem;
            --space-8: 2rem;
            --radius-md: 0.5rem;
            --radius-lg: 0.75rem;
            --radius-xl: 1rem;
        }
        
        /* Global Styles */
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }
        
        .stApp {
            background-color: var(--gray-50);
        }
        
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }
        
        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700;
            color: var(--gray-900);
            letter-spacing: -0.025em;
        }
        
        /* Sidebar */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--primary-50) 0%, #ecfdf5 100%);
            border-right: 1px solid var(--gray-200);
        }
        
        [data-testid="stSidebar"] h3 {
            color: var(--primary-700);
            font-size: 1rem;
            font-weight: 700;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--primary-200);
        }
        
        /* Buttons */
        .stButton > button {
            background: var(--primary-600);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.625rem 1.5rem;
            font-weight: 600;
            font-size: 0.875rem;
            transition: all 0.2s ease;
            box-shadow: var(--shadow-sm);
            width: 100%;
        }
        
        .stButton > button:hover {
            background: var(--primary-700);
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }
        
        .stDownloadButton > button {
            background: var(--success);
            color: white;
            border: none;
            border-radius: var(--radius-md);
            padding: 0.625rem 1.5rem;
            font-weight: 600;
            font-size: 0.875rem;
        }
        
        /* Metrics */
        div[data-testid="stMetric"] {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: var(--radius-lg);
            padding: 1rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.2s ease;
        }
        
        div[data-testid="stMetric"]:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 1.75rem;
            font-weight: 700;
            color: var(--gray-900);
        }
        
        div[data-testid="stMetricLabel"] {
            font-size: 0.875rem;
            font-weight: 500;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: var(--radius-md);
            padding: 0.875rem 1rem;
            font-weight: 600;
            color: var(--gray-900);
            transition: all 0.2s ease;
        }
        
        .streamlit-expanderHeader:hover {
            background: var(--primary-50);
            border-color: var(--primary-500);
        }
        
        .streamlit-expanderContent {
            border: 1px solid var(--gray-200);
            border-top: none;
            border-radius: 0 0 var(--radius-md) var(--radius-md);
            padding: 1rem;
            background: white;
        }
        
        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {
            background: white;
            border: 1px solid var(--gray-300);
            border-radius: var(--radius-md);
            padding: 0.625rem 0.875rem;
            font-size: 0.875rem;
            color: var(--gray-900);
            transition: all 0.2s ease;
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {
            border-color: var(--primary-500);
            box-shadow: 0 0 0 3px var(--primary-100);
            outline: none;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: white;
            padding: 0.5rem;
            border-radius: var(--radius-lg);
            border: 1px solid var(--gray-200);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            color: var(--gray-600);
            font-weight: 600;
            padding: 0.625rem 1.25rem;
            border-radius: var(--radius-md);
            transition: all 0.2s ease;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: var(--gray-100);
            color: var(--gray-900);
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--primary-600);
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        /* Professional Header */
        .professional-header {
            background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
            color: white;
            padding: 2rem;
            border-radius: var(--radius-xl);
            margin-bottom: 2rem;
            box-shadow: var(--shadow-xl);
            text-align: center;
        }
        
        .professional-header h1 {
            color: white;
            margin: 0;
            font-size: 2.5rem;
            font-weight: 800;
        }
        
        .professional-header .subtitle {
            font-size: 1rem;
            opacity: 0.95;
            margin-top: 0.5rem;
            font-weight: 500;
        }
        
        .professional-header .description {
            font-size: 0.875rem;
            opacity: 0.85;
            margin-top: 0.25rem;
        }
        
        /* Stock Card */
        .stock-card {
            background: white;
            border: 1px solid var(--gray-200);
            border-radius: var(--radius-xl);
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
        }
        
        .stock-card:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-lg);
            border-color: var(--primary-300);
        }
        
        .stock-symbol {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--gray-900);
            margin: 0;
        }
        
        .signal-badge {
            background: var(--info-light);
            color: #1e40af;
            padding: 0.25rem 0.625rem;
            border-radius: var(--radius-md);
            font-size: 0.75rem;
            font-weight: 600;
            margin-right: 0.25rem;
            display: inline-block;
        }
        
        .signal-badge.today {
            background: linear-gradient(135deg, #f59e0b, #dc2626);
            color: white;
        }
        
        .signal-badge.news {
            background: #dbeafe;
            color: #1e40af;
        }
        
        .signal-badge.volume {
            background: #fef3c7;
            color: #92400e;
        }
        
        .confidence-badge {
            padding: 0.375rem 0.875rem;
            border-radius: var(--radius-md);
            font-size: 0.875rem;
            font-weight: 700;
            text-align: center;
        }
        
        .confidence-badge.high {
            background: var(--success);
            color: white;
        }
        
        .confidence-badge.medium {
            background: var(--warning);
            color: white;
        }
        
        .confidence-badge.low {
            background: var(--gray-400);
            color: white;
        }
        
        .pattern-info {
            background: var(--gray-50);
            padding: 0.875rem;
            border-radius: var(--radius-md);
            margin-bottom: 1rem;
        }
        
        .pattern-name {
            font-weight: 600;
            color: var(--gray-800);
            margin-bottom: 0.25rem;
        }
        
        .pattern-stats {
            font-size: 0.875rem;
            color: var(--gray-600);
        }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .metric-item {
            text-align: center;
        }
        
        .metric-value {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--gray-900);
        }
        
        .metric-label {
            font-size: 0.75rem;
            color: var(--gray-600);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-top: 0.25rem;
        }
        
        /* Enhancement Cards */
        .enhancement-card {
            background: white;
            border: 1px solid var(--gray-200);
            border-left: 4px solid var(--primary-500);
            border-radius: var(--radius-md);
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .enhancement-card h4 {
            margin: 0 0 0.5rem 0;
            font-size: 1rem;
            color: var(--gray-900);
        }
        
        .enhancement-card.success {
            border-left-color: var(--success);
            background: var(--success-light);
        }
        
        .enhancement-card.warning {
            border-left-color: var(--warning);
            background: var(--warning-light);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .professional-header h1 {
                font-size: 1.75rem;
            }
            
            .stock-card {
                padding: 1rem;
            }
            
            .metrics-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 0.75rem;
            }
            
            .stButton > button {
                width: 100%;
                margin-bottom: 0.5rem;
            }
        }
        
        @media (max-width: 480px) {
            .metrics-grid {
                grid-template-columns: 1fr;
            }
            
            .professional-header {
                padding: 1.5rem;
            }
            
            .professional-header h1 {
                font-size: 1.5rem;
            }
        }
        
        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .fade-in {
            animation: fadeIn 0.4s ease-out;
        }
    </style>
    """, unsafe_allow_html=True)

# =================== DATA STRUCTURES (Keep your existing) ===================

COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS', 'ADANIENT.NS', 
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS', 
    'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 
    'DMART.NS', 'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS', 'BHARATFORG.NS', 
    'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BLUESTARCO.NS', 'BOSCHLTD.NS', 
    'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 
    'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 
    'CUMMINSIND.NS', 'CYIENT.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 
    'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS', 
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODREJCP.NS', 
    'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 
    'HFCL.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HAL.NS', 'HINDPETRO.NS', 
    'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS', 'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 
    'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 
    'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 
    'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 
    'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 
    'LT.NS', 'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 
    'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 
    'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NCC.NS', 
    'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS', 
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 
    'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 
    'PETRONET.NS', 'PIDILITIND.NS', 'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 
    'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS', 
    'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 
    'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TITAGARH.NS', 
    'TVSMOTOR.NS', 'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 
    'TATATECH.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 
    'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 
    'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'IDEA.NS', 
    'VOLTAS.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def get_nse_non_fno_stocks():
    """Get NSE non-F&O stocks - implement your existing logic"""
    # Simplified for demo - replace with your full implementation
    return ['AARTIIND.NS', 'AAVAS.NS'] * 400  # Simulate 800 stocks

def create_excel_stock_list(results):
    """Create Excel file with stock symbols"""
    stock_symbols = [result['symbol'].replace('.NS', '').replace('^', '') for result in results]
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Qualifying Stocks"
    
    ws['A1'] = "Stock Symbol"
    ws['A1'].font = openpyxl.styles.Font(bold=True, size=12)
    
    for idx, symbol in enumerate(stock_symbols, start=2):
        ws[f'A{idx}'] = symbol
    
    ws.column_dimensions['A'].width = 20
    
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()

# =================== PROFESSIONAL STOCK CARD COMPONENT ===================

def create_professional_stock_card(result, index=0):
    """Create professional stock card with all metrics visible"""
    
    symbol = result['symbol'].replace('.NS', '').replace('^', '')
    top_pattern = max(result['patterns'], key=lambda p: p['strength'])
    
    # Create signal badges
    signals = []
    if 'Current Day' in top_pattern['type']:
        signals.append('<span class="signal-badge today">🔥 TODAY</span>')
    if result.get('news_data', {}).get('news_count', 0) > 0:
        signals.append('<span class="signal-badge news">📰 NEWS</span>')
    if result['volume_ratio'] >= 2:
        signals.append('<span class="signal-badge volume">⚡ HIGH VOL</span>')
    
    # Enhancement signals
    enhancements = result.get('enhancements', {})
    if enhancements.get('fno_consolidation', {}).get('consolidation_detected'):
        signals.append('<span class="signal-badge">🔄 CONSOLIDATION</span>')
    if enhancements.get('breakout_pullback', {}).get('pattern_detected'):
        signals.append('<span class="signal-badge">📈 BREAKOUT-PULLBACK</span>')
    
    # Confidence styling
    confidence = top_pattern['confidence'].lower()
    strength = top_pattern['strength']
    
    # Weekly validation info
    weekly_val = top_pattern.get('weekly_validation', {})
    weekly_bonus = weekly_val.get('weekly_strength_bonus', 0)
    daily_strength = top_pattern.get('daily_strength', strength)
    
    weekly_info = ""
    if weekly_bonus > 0:
        weekly_info = f'''
        <div style="background: #d1fae5; color: #065f46; padding: 0.5rem; border-radius: 0.5rem; margin-top: 0.5rem; font-size: 0.875rem;">
            📈 <strong>Weekly Confirmation:</strong> +{weekly_bonus} pts | {weekly_val.get('weekly_context', 'Strong alignment')}
        </div>
        '''
    
    card_html = f"""
    <div class="stock-card fade-in" style="animation-delay: {index * 0.05}s;">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 1rem;">
            <div>
                <h3 class="stock-symbol">{symbol}</h3>
                <div style="margin-top: 0.5rem;">
                    {' '.join(signals)}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.5rem; font-weight: 700; color: var(--gray-900);">
                    ₹{result['current_price']:.2f}
                </div>
                <div class="confidence-badge {confidence}" style="margin-top: 0.5rem;">
                    {strength}% {confidence.upper()}
                </div>
            </div>
        </div>
        
        <div class="pattern-info">
            <div class="pattern-name">{top_pattern['type']}</div>
            <div class="pattern-stats">
                Success Rate: {top_pattern['success_rate']}% | 
                PCS Suitability: {top_pattern['pcs_suitability']}% | 
                Daily: {daily_strength}% + Weekly: +{weekly_bonus}
            </div>
        </div>
        
        {weekly_info}
        
        <div class="metrics-grid">
            <div class="metric-item">
                <div class="metric-value" style="color: {'var(--success)' if result['volume_ratio'] >= 1.5 else 'var(--gray-900)'}">
                    {result['volume_ratio']:.1f}x
                </div>
                <div class="metric-label">Volume</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{result['rsi']:.0f}</div>
                <div class="metric-label">RSI</div>
            </div>
            <div class="metric-item">
                <div class="metric-value">{result['adx']:.0f}</div>
                <div class="metric-label">ADX</div>
            </div>
            <div class="metric-item">
                <div class="metric-value" style="color: var(--success);">✓</div>
                <div class="metric-label">Signal</div>
            </div>
        </div>
    </div>
    """
    
    return card_html

# =================== SMART FILTER SYSTEM ===================

def create_smart_filter_system():
    """Professional preset-based filtering with custom override"""
    
    st.markdown("### ⚙️ Scan Configuration")
    
    # Strategy Presets
    preset = st.selectbox(
        "🎯 Trading Strategy:",
        [
            "⚖️ Balanced Opportunities (Recommended)", 
            "🔥 High Confidence PCS (Strict)",
            "🎣 Opportunity Hunter (Relaxed)",
            "🛠️ Custom Configuration"
        ],
        index=0,
        help="Presets automatically optimize all filters for your strategy"
    )
    
    # Preset configurations
    if preset == "🔥 High Confidence PCS (Strict)":
        config = {
            'rsi_min': 35, 'rsi_max': 70,
            'adx_min': 25,
            'min_volume_ratio': 1.8,
            'volume_breakout_ratio': 2.2,
            'lookback_days': 20,
            'pattern_strength_min': 75,
            'pattern_priority': 'High Success Rate Only (>80%)',
            'ma_support': True,
            'ma_type': 'EMA',
            'ma_tolerance': 2
        }
        st.success("✅ **Strict Filters Applied**: Fewer results, highest quality setups")
        
    elif preset == "🎣 Opportunity Hunter (Relaxed)":
        config = {
            'rsi_min': 25, 'rsi_max': 80,
            'adx_min': 15,
            'min_volume_ratio': 1.0,
            'volume_breakout_ratio': 1.6,
            'lookback_days': 20,
            'pattern_strength_min': 55,
            'pattern_priority': 'All Patterns (Comprehensive)',
            'ma_support': False,
            'ma_type': 'EMA',
            'ma_tolerance': 5
        }
        st.warning("⚠️ **Relaxed Filters**: More results, requires additional validation")
        
    elif preset == "⚖️ Balanced Opportunities (Recommended)":
        config = {
            'rsi_min': 30, 'rsi_max': 75,
            'adx_min': 20,
            'min_volume_ratio': 1.2,
            'volume_breakout_ratio': 2.0,
            'lookback_days': 20,
            'pattern_strength_min': 65,
            'pattern_priority': 'All Patterns (Comprehensive)',
            'ma_support': True,
            'ma_type': 'EMA',
            'ma_tolerance': 3
        }
        st.info("ℹ️ **Balanced Approach**: Optimal mix of quality and quantity")
        
    else:  # Custom
        with st.expander("🛠️ Custom Filter Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                rsi_min = st.slider("RSI Min", 20, 80, 30, help="Minimum RSI value")
                adx_min = st.slider("ADX Min", 10, 50, 20, help="Minimum trend strength")
                min_volume_ratio = st.slider("Volume Ratio", 0.8, 5.0, 1.2, 0.1, help="Current vs average volume")
                lookback_days = st.slider("Lookback Days", 15, 45, 20, help="Pattern formation period")
            with col2:
                rsi_max = st.slider("RSI Max", 20, 80, 80, help="Maximum RSI value")
                pattern_strength_min = st.slider("Pattern Strength", 50, 100, 65, 5, help="Minimum pattern score")
                volume_breakout_ratio = st.slider("Breakout Volume", 1.5, 5.0, 2.0, 0.1, help="Breakout volume multiplier")
                ma_support = st.checkbox("MA Support", value=True, help="Price above moving average")
            
            if ma_support:
                col1, col2 = st.columns(2)
                with col1:
                    ma_type = st.selectbox("MA Type", ["EMA", "SMA"])
                with col2:
                    ma_tolerance = st.slider("MA Tolerance %", 0, 10, 3)
            else:
                ma_type = 'EMA'
                ma_tolerance = 3
            
            pattern_priority = st.selectbox(
                "Pattern Focus",
                ["All Patterns (Comprehensive)", "High Success Rate Only (>80%)", "PCS Optimized (>90% suitability)"]
            )
        
        config = {
            'rsi_min': rsi_min, 'rsi_max': rsi_max,
            'adx_min': adx_min,
            'min_volume_ratio': min_volume_ratio,
            'volume_breakout_ratio': volume_breakout_ratio,
            'lookback_days': lookback_days,
            'pattern_strength_min': pattern_strength_min,
            'pattern_priority': pattern_priority,
            'ma_support': ma_support,
            'ma_type': ma_type,
            'ma_tolerance': ma_tolerance
        }
    
    return config

# =================== COMPARISON DASHBOARD ===================

def create_stock_comparison_view(results):
    """Professional side-by-side stock comparison"""
    
    if len(results) < 2:
        return
    
    st.markdown("---")
    st.markdown("### 🔄 Compare Top Opportunities")
    
    # Select stocks for comparison
    stock_options = [
        f"{r['symbol'].replace('.NS', '')} ({max(p['strength'] for p in r['patterns'])}%)" 
        for r in results[:10]
    ]
    
    selected = st.multiselect(
        "Select stocks to compare (up to 3):",
        stock_options,
        default=stock_options[:min(2, len(stock_options))],
        max_selections=3,
        help="Compare key metrics side-by-side"
    )
    
    if len(selected) >= 2:
        # Create comparison data
        comparison_data = []
        for stock_name in selected:
            idx = stock_options.index(stock_name)
            result = results[idx]
            top_pattern = max(result['patterns'], key=lambda p: p['strength'])
            
            comparison_data.append({
                'Stock': result['symbol'].replace('.NS', ''),
                'Price': f"₹{result['current_price']:.2f}",
                'Pattern': top_pattern['type'][:25] + ('...' if len(top_pattern['type']) > 25 else ''),
                'Strength': top_pattern['strength'],
                'Confidence': top_pattern['confidence'],
                'Volume': f"{result['volume_ratio']:.1f}x",
                'RSI': result['rsi'],
                'ADX': result['adx'],
                'Success Rate': top_pattern['success_rate'],
                'PCS Fit': top_pattern['pcs_suitability']
            })
        
        # Display styled comparison
        df = pd.DataFrame(comparison_data)
        
        # Style the dataframe
        styled_df = df.style.background_gradient(
            cmap='RdYlGn',
            subset=['Strength', 'Success Rate', 'PCS Fit']
        ).format({
            'Strength': '{:.0f}%',
            'Success Rate': '{:.0f}%',
            'PCS Fit': '{:.0f}%',
            'RSI': '{:.0f}',
            'ADX': '{:.0f}'
        })
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Mini charts
        st.markdown("#### 📊 Price Trends (Last 30 Days)")
        cols = st.columns(len(selected))
        
        for col, stock_name in zip(cols, selected):
            with col:
                idx = stock_options.index(stock_name)
                result = results[idx]
                
                mini_data = result['data'].tail(30)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=mini_data.index,
                    y=mini_data['Close'],
                    mode='lines',
                    line=dict(color='#14b8a6', width=2),
                    fill='tonexty',
                    fillcolor='rgba(20, 184, 166, 0.1)',
                    showlegend=False
                ))
                
                fig.update_layout(
                    height=180,
                    margin=dict(l=10, r=10, t=30, b=10),
                    xaxis=dict(showgrid=False, showticklabels=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.05)'),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    title=dict(
                        text=result['symbol'].replace('.NS', ''),
                        font=dict(size=14, weight='bold')
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)

# =================== KEEP YOUR EXISTING ProfessionalPCSScanner CLASS ===================
# Insert your complete ProfessionalPCSScanner class here with all methods:
# - get_stock_data
# - get_weekly_stock_data  
# - check_volume_criteria
# - detect_patterns (with all 12 patterns)
# - validate_weekly_strength
# - detect_current_day_breakout
# - All enhancement methods
# - create_tradingview_chart
# - get_market_sentiment_indicators
# etc.

class ProfessionalPCSScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    # INSERT ALL YOUR EXISTING METHODS HERE
    # This is just a placeholder - use your complete implementation
    
    def get_stock_data(self, symbol, period="3mo"):
        """Your existing implementation"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            if len(data) < 20: return None
            
            # Add all your technical indicators
            data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
            data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
            data['EMA_20'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
            data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
            data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
            # Add all other indicators...
            
            return data
        except: return None

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Your existing implementation"""
        if len(data) < 21: return False, 0, {}
        current_vol = data['Volume'].iloc[-1]
        avg_20 = data['Volume'].tail(21).iloc[:-1].mean()
        if avg_20 == 0: return False, 0, {}
        ratio = current_vol / avg_20
        details = {'current_volume': current_vol, 'avg_20_volume': avg_20, 'ratio_20d': ratio}
        return ratio >= min_ratio, ratio, details

    def detect_patterns(self, data, symbol, filters):
        """Your existing complete pattern detection with all 12 patterns"""
        # Use your complete implementation here
        patterns = []
        # ... your pattern detection logic
        return patterns

    def get_market_sentiment_indicators(self):
        """Your existing implementation"""
        # Use your complete market sentiment logic
        return {
            'overall': {'sentiment': 'BULLISH', 'pcs_recommendation': 'Good for PCS', 'risk_level': 'LOW'},
            'nifty': {'current': 24500, 'change_1d': 0.75}
        }

    def create_tradingview_chart(self, data, symbol, pattern_info=None):
        """Your existing chart creation"""
        # Use your complete chart implementation
        fig = make_subplots(rows=3, cols=1, shared_xaxes=True)
        # ... your complete chart logic
        return fig

    # ADD ALL OTHER METHODS FROM YOUR EXISTING CLASS

# =================== PROFESSIONAL SIDEBAR ===================

def create_professional_sidebar():
    """Create professional sidebar with smart presets"""
    
    with st.sidebar:
        # Professional Header
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, var(--primary-600), var(--primary-800)); border-radius: var(--radius-lg); margin-bottom: 1.5rem;'>
            <h2 style='color: white; margin: 0; font-weight: 800; font-size: 1.5rem;'>📈 PCS Scanner</h2>
            <p style='color: white; margin: 0.5rem 0 0 0; opacity: 0.95; font-size: 0.875rem;'>Professional V7.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock Universe
        st.markdown("### 📊 Stock Universe")
        universe_option = st.radio(
            "Select Universe:",
            ["NSE F&O (219)", "NSE Non-F&O (800+)"],
            index=0,
            help="Choose between F&O and non-F&O stocks"
        )
        
        if universe_option == "NSE F&O (219)":
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
            st.success(f"🎯 **{len(stocks_to_scan)} F&O stocks** loaded")
        else:
            stocks_to_scan = get_nse_non_fno_stocks()
            st.success(f"📈 **{len(stocks_to_scan)} Non-F&O stocks** loaded")
        
        # Smart Filter System
        filter_config = create_smart_filter_system()
        
        # Pattern Selection
        st.markdown("### 📈 Pattern Selection")
        with st.expander("🎯 Choose Patterns", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                pattern_filters = {
                    'current_day_breakout': st.checkbox("Current Day Breakout", True),
                    'cup_and_handle': st.checkbox("Cup with Handle", True),
                    'flat_base': st.checkbox("Flat Base", True),
                    'bump_and_run': st.checkbox("Bump-and-Run", True),
                    'rectangle_bottom': st.checkbox("Rectangle Bottom", True),
                    'rectangle_top': st.checkbox("Rectangle Top", False),
                }
            with col2:
                pattern_filters.update({
                    'head_shoulders_bottom': st.checkbox("Head & Shoulders Bottom", True),
                    'double_bottom': st.checkbox("Double Bottom", True),
                    'three_rising_valleys': st.checkbox("Three Rising Valleys", True),
                    'rounding_bottom': st.checkbox("Rounding Bottom", True),
                    'rounding_top_upside': st.checkbox("Rounding Top Upside", False),
                    'inverted_scallop': st.checkbox("Inverted Scallop", True),
                })
        
        # Timeframe Analysis
        st.markdown("### ⏱ Timeframe Analysis")
        analysis_mode = st.radio(
            "Analysis Mode:",
            [
                "Daily + Weekly Combined (Recommended)",
                "Daily Only (Fast)",
                "Weekly Only (Trends)"
            ],
            index=0,
            help="Choose analysis timeframe"
        )
        
        # Scan Options
        st.markdown("### 🚀 Scan Options")
        max_stocks = st.selectbox(
            "Stocks to Scan:",
            ["All Stocks", "First 50", "First 100"],
            index=1,  # Default to First 50 for speed
            help="Choose scan size"
        )
        
        if max_stocks == "First 50":
            stocks_limit = 50
        elif max_stocks == "First 100":
            stocks_limit = 100
        else:
            stocks_limit = len(stocks_to_scan)
        
        show_charts = st.checkbox("Show Charts", value=True, help="Display technical charts")
        show_comparison = st.checkbox("Enable Comparison", value=True, help="Compare multiple stocks")
        
        # Enhancement Options
        st.markdown("### 🚀 Enhancements")
        with st.expander("Advanced Features", expanded=False):
            enhancement_options = {
                'delivery_volume': st.checkbox("📊 Delivery Volume Analysis", True),
                'fno_consolidation': st.checkbox("🔄 F&O Consolidation Detection", True),
                'breakout_pullback': st.checkbox("📈 Breakout-Pullback Patterns", True),
                'enhanced_sr': st.checkbox("🎯 Enhanced Support & Resistance", True)
            }
        
        # Market Sentiment
        st.markdown("### 🌍 Market Sentiment")
        
        scanner = ProfessionalPCSScanner()
        sentiment_data = scanner.get_market_sentiment_indicators()
        
        overall = sentiment_data.get('overall', {})
        sentiment = overall.get('sentiment', 'NEUTRAL')
        
        sentiment_colors = {
            'BULLISH': '#059669',
            'NEUTRAL': '#d97706',
            'BEARISH': '#dc2626'
        }
        
        st.markdown(f"""
        <div style='background: white; padding: 1rem; border-radius: var(--radius-md); border-left: 4px solid {sentiment_colors.get(sentiment, "#d97706")};'>
            <h4 style='margin: 0 0 0.5rem 0; color: {sentiment_colors.get(sentiment, "#d97706")};'>
                {'🟢' if sentiment == 'BULLISH' else '🟡' if sentiment == 'NEUTRAL' else '🔴'} {sentiment}
            </h4>
            <p style='margin: 0; font-size: 0.875rem; color: var(--gray-600);'>
                {overall.get('pcs_recommendation', 'Moderate opportunities')}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if 'nifty' in sentiment_data:
            nifty = sentiment_data['nifty']
            st.metric("Nifty 50", f"{nifty['current']:.0f}", f"{nifty['change_1d']:+.2f}%")
        
        # Timestamp
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        st.markdown(f"**Updated:** {current_time.strftime('%H:%M IST')}")
    
    return {
        'stocks_to_scan': stocks_to_scan[:stocks_limit],
        'filter_config': filter_config,
        'pattern_filters': pattern_filters,
        'analysis_mode': analysis_mode,
        'show_charts': show_charts,
        'show_comparison': show_comparison,
        'stocks_limit': stocks_limit,
        'market_sentiment': sentiment_data,
        'enhancements': enhancement_options
    }

# =================== MAIN SCANNER TAB ===================

def create_main_scanner_tab(config):
    """Create main scanner tab with professional UI"""
    
    st.markdown("### 🎯 Professional Stock Scanner")
    st.info(f"💡 **Mode**: {config['analysis_mode']} | **Scanning**: {config['stocks_limit']} stocks | **Universe**: {len(config['stocks_to_scan'])} stocks loaded")
    
    # Action buttons
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button("🚀 Start Professional Scan", type="primary", use_container_width=True)
    
    with col2:
        if st.button("📊 Quick Scan (Top 20)", use_container_width=True):
            # Quick scan with reduced scope
            config['stocks_to_scan'] = config['stocks_to_scan'][:20]
            scan_button = True
    
    with col3:
        st.markdown(f"**Ready to scan**")
    
    if scan_button:
        scanner = ProfessionalPCSScanner()
        filter_config = config['filter_config']
        
        # Merge all config into filter_config for compatibility
        filter_config.update({
            'pattern_filters': config['pattern_filters'],
            'analysis_mode': config['analysis_mode'],
            'enable_daily_analysis': 'Daily' in config['analysis_mode'],
            'enable_weekly_validation': 'Weekly' in config['analysis_mode'],
            'show_charts': config['show_charts'],
            'show_news': True,
            'enhancements': config['enhancements']
        })
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        
        for i, symbol in enumerate(config['stocks_to_scan']):
            progress = (i + 1) / len(config['stocks_to_scan'])
            progress_bar.progress(progress)
            
            clean_symbol = symbol.replace('.NS', '').replace('^', '')
            status_text.info(f"🔍 Analyzing **{clean_symbol}** ({i+1}/{len(config['stocks_to_scan'])})")
            
            try:
                # Get data
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue
                
                # Check volume
                volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                    data, 
                    filter_config['min_volume_ratio']
                )
                if not volume_ok:
                    continue
                
                # Detect patterns
                patterns = scanner.detect_patterns(data, symbol, filter_config)
                if not patterns:
                    continue
                
                # Get current metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]
                
                # Get news if enabled
                news_data = None
                try:
                    news_data = scanner.get_fundamental_news(symbol, clean_symbol)
                except:
                    news_data = None
                
                # Run enhancements (use your existing methods)
                enhancement_results = {}
                enh_cfg = config.get('enhancements', {})
                
                # Add your existing enhancement calls here
                if enh_cfg.get('delivery_volume'):
                    try:
                        enhancement_results['delivery_volume'] = scanner.analyze_delivery_volume_percentage(symbol)
                    except:
                        enhancement_results['delivery_volume'] = {'delivery_percentage': None}
                
                if enh_cfg.get('fno_consolidation'):
                    try:
                        enhancement_results['fno_consolidation'] = scanner.detect_fno_consolidation_near_resistance(data, symbol)
                    except:
                        enhancement_results['fno_consolidation'] = {'consolidation_detected': False}
                
                if enh_cfg.get('breakout_pullback'):
                    try:
                        enhancement_results['breakout_pullback'] = scanner.detect_breakout_pullback_strong_green(data)
                    except:
                        enhancement_results['breakout_pullback'] = {'pattern_detected': False}
                
                if enh_cfg.get('enhanced_sr'):
                    try:
                        enhancement_results['enhanced_sr'] = scanner.enhanced_support_resistance_analysis(data)
                    except:
                        enhancement_results['enhanced_sr'] = {'analysis_available': False}
                
                # Create result
                result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                    'news_data': news_data,
                    'enhancements': enhancement_results
                }
                
                results.append(result)
                
            except Exception as e:
                continue
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Display results
        if results:
            # Sort by strength
            results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)
            
            st.success(f"🎉 Found **{len(results)} stocks** with qualifying patterns!")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🎯 Stocks Found", len(results))
            with col2:
                avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])
                st.metric("💪 Avg Strength", f"{avg_strength:.0f}%")
            with col3:
                high_conf = sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')
                st.metric("🏆 High Confidence", high_conf)
            with col4:
                current_day = sum(1 for r in results for p in r['patterns'] if 'Current Day' in p['type'])
                st.metric("🔥 Current Day", current_day)
            
            # Comparison view
            if config['show_comparison'] and len(results) >= 2:
                create_stock_comparison_view(results)
            
            st.markdown("---")
            
            # Display stock cards
            st.markdown("### 📋 Professional Stock Analysis")
            
            for idx, result in enumerate(results):
                st.markdown(create_professional_stock_card(result, idx), unsafe_allow_html=True)
                
                # Detailed analysis in expander
                with st.expander("📊 Detailed Analysis & Charts", expanded=False):
                    
                    # Tabs for different views
                    tab1, tab2, tab3 = st.tabs(["📈 Technical Chart", "🧠 Pattern Analysis", "🚀 Enhancements"])
                    
                    with tab1:
                        if config['show_charts']:
                            chart = scanner.create_tradingview_chart(
                                result['data'], 
                                result['symbol'], 
                                result['patterns'][0] if result['patterns'] else None
                            )
                            if chart:
                                st.plotly_chart(chart, use_container_width=True)
                        else:
                            st.info("Enable 'Show Charts' in sidebar to view technical analysis")
                    
                    with tab2:
                        # Pattern details
                        for pattern in result['patterns']:
                            weekly_val = pattern.get('weekly_validation', {})
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown(f"""
                                **Pattern Details:**
                                - **Type:** {pattern['type']}
                                - **Total Strength:** {pattern['strength']}%
                                - **Daily Strength:** {pattern.get('daily_strength', pattern['strength'])}%
                                - **Weekly Bonus:** +{weekly_val.get('weekly_strength_bonus', 0)}
                                - **Success Rate:** {pattern['success_rate']}%
                                - **PCS Suitability:** {pattern['pcs_suitability']}%
                                - **Confidence:** {pattern['confidence']}
                                """)
                            
                            with col2:
                                # Current day metrics
                                current_day_data = result['data'].iloc[-1]
                                trading_date = current_day_data.name.strftime('%Y-%m-%d')
                                
                                st.markdown(f"""
                                **Current Day Metrics:**
                                - **Date:** {trading_date}
                                - **Price:** ₹{result['current_price']:.2f}
                                - **Volume Ratio:** {result['volume_ratio']:.2f}x
                                - **RSI:** {result['rsi']:.1f}
                                - **ADX:** {result['adx']:.1f}
                                - **Day Range:** ₹{current_day_data['Low']:.2f} - ₹{current_day_data['High']:.2f}
                                """)
                        
                        # News Analysis
                        if result.get('news_data') and result['news_data'].get('news_count', 0) > 0:
                            st.markdown("---")
                            news_data = result['news_data']
                            sentiment_emoji = "🟢" if news_data['overall_sentiment'] == 'positive' else "🔴" if news_data['overall_sentiment'] == 'negative' else "🟡"
                            
                            st.markdown(f"**{sentiment_emoji} News Sentiment:** {news_data['overall_sentiment'].upper()}")
                            for news_item in news_data['news_items'][:2]:
                                st.markdown(f"• {news_item['headline']}")
                    
                    with tab3:
                        # Enhancement results
                        enhancements = result.get('enhancements', {})
                        
                        if not enhancements:
                            st.info("No enhancements enabled. Enable them in the sidebar for deeper analysis.")
                        else:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                # Delivery Volume
                                if 'delivery_volume' in enhancements:
                                    delivery = enhancements['delivery_volume']
                                    if delivery.get('delivery_percentage') is not None:
                                        st.markdown(f"""
                                        <div class="enhancement-card success">
                                            <h4>📊 Delivery Volume Analysis</h4>
                                            <p><strong>Estimated Delivery:</strong> {delivery.get('delivery_percentage', 0):.1f}%</p>
                                            <p><strong>Analysis:</strong> {delivery.get('delivery_analysis', 'N/A')}</p>
                                            <p><strong>Confidence:</strong> {delivery.get('confidence', 'Low')}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
                                
                                # Breakout-Pullback
                                if 'breakout_pullback' in enhancements:
                                    bp = enhancements['breakout_pullback']
                                    status_class = "success" if bp.get('pattern_detected') else "warning"
                                    st.markdown(f"""
                                    <div class="enhancement-card {status_class}">
                                        <h4>📈 Breakout-Pullback Pattern</h4>
                                        <p><strong>Status:</strong> {'Detected' if bp.get('pattern_detected') else 'Not Detected'}</p>
                                        <p><strong>Analysis:</strong> {bp.get('analysis', 'N/A')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            with col2:
                                # F&O Consolidation
                                if 'fno_consolidation' in enhancements:
                                    consolidation = enhancements['fno_consolidation']
                                    status_class = "success" if consolidation.get('consolidation_detected') else "warning"
                                    st.markdown(f"""
                                    <div class="enhancement-card {status_class}">
                                        <h4>🔄 F&O Consolidation</h4>
                                        <p><strong>Status:</strong> {'Detected' if consolidation.get('consolidation_detected') else 'Not Detected'}</p>
                                        <p><strong>Analysis:</strong> {consolidation.get('analysis', 'N/A')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                # Enhanced S&R
                                if 'enhanced_sr' in enhancements:
                                    sr = enhancements['enhanced_sr']
                                    if sr.get('analysis_available'):
                                        key_levels = sr.get('key_levels', {})
                                        st.markdown(f"""
                                        <div class="enhancement-card">
                                            <h4>🎯 Enhanced Support & Resistance</h4>
                                            <p><strong>Support Levels:</strong> {len(sr.get('support_levels', []))}</p>
                                            <p><strong>Resistance Levels:</strong> {len(sr.get('resistance_levels', []))}</p>
                                        </div>
                                        """, unsafe_allow_html=True)
            
            # Export
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                excel_data = create_excel_stock_list(results)
                st.download_button(
                    label="📊 Download Stock List (Excel)",
                    data=excel_data,
                    file_name=f"pcs_stocks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            with col2:
                st.info(f"📋 {len(results)} qualifying stocks will be exported with clean symbols")
            
        else:
            st.warning("🔍 No patterns found with current filters.")
            
            with st.expander("💡 Optimization Suggestions", expanded=True):
                st.markdown("""
                **Try these adjustments:**
                - Switch to **"Opportunity Hunter"** preset for broader search
                - Lower **Pattern Strength** to 50-60%
                - Reduce **Volume Ratio** to 1.0x
                - Expand **RSI range** to 25-85
                - Disable **MA Support** temporarily
                - Check if markets are open today
                - Try **"Quick Scan (Top 20)"** for faster testing
                """)

# =================== MAIN APPLICATION ===================

def main():
    """Main application entry point"""
    
    # Apply professional theme
    inject_professional_theme()
    
    # Professional header
    st.markdown("""
    <div class="professional-header">
        <h1>📈 NSE F&O PCS Scanner</h1>
        <p class="subtitle">Professional Trading Platform • Multi-Timeframe Analysis • Real-Time Pattern Recognition</p>
        <p class="description">Bloomberg-Style Interface with Current Day EOD Confirmation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get configuration from sidebar
    config = create_professional_sidebar()
    
    # Main tabs
    tab1, tab2 = st.tabs(["🎯 Stock Scanner", "📊 Market Intelligence"])
    
    with tab1:
        create_main_scanner_tab(config)
    
    with tab2:
        st.markdown("### 📊 Market Intelligence Dashboard")
        
        # Display current sentiment
        sentiment = config['market_sentiment']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            overall = sentiment.get('overall', {})
            sentiment_level = overall.get('sentiment', 'NEUTRAL')
            st.markdown(f"""
            <div class="enhancement-card">
                <h4>🌍 Market Sentiment</h4>
                <p><strong>Status:</strong> {sentiment_level}</p>
                <p><strong>PCS Outlook:</strong> {overall.get('pcs_recommendation', 'Moderate')}</p>
                <p><strong>Risk Level:</strong> {overall.get('risk_level', 'MEDIUM')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if 'nifty' in sentiment:
                nifty = sentiment['nifty']
                st.metric("Nifty 50", f"{nifty['current']:.0f}", f"{nifty['change_1d']:+.2f}%")
            
            if 'bank_nifty' in sentiment:
                bank = sentiment['bank_nifty']
                st.metric("Bank Nifty", f"{bank['current']:.0f}", f"{bank['change_1d']:+.2f}%")
        
        with col3:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            is_trading_day = current_time.weekday() < 5
            
            st.markdown(f"""
            <div class="enhancement-card">
                <h4>🕐 Market Status</h4>
                <p><strong>Time:</strong> {current_time.strftime('%H:%M IST')}</p>
                <p><strong>Day:</strong> {'Trading Day' if is_trading_day else 'Non-Trading Day'}</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.info("📈 Advanced market intelligence features will be added in future updates")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: var(--gray-500); font-size: 0.875rem; padding: 1rem;'>
        <p>NSE F&O PCS Professional Scanner V7.0 | Built with Streamlit & Python</p>
        <p>⚠️ For educational purposes only. Not financial advice. Always do your own research.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
