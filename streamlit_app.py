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
    page_title="NSE F&O CCS Professional Scanner", 
    page_icon="📉", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ENHANCED PROFESSIONAL UI SYSTEM - Tailwind-Inspired CSS
# ENHANCED PROFESSIONAL UI SYSTEM - Tailwind + shadcn/ui Design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        /* === PROFESSIONAL FINANCE DESIGN SYSTEM === */
        /* Modern Red Theme - Professional Finance Design for Call Credit Spreads */
        
        /* Primary Color Palette - Professional Finance Red */
        --primary-50: hsl(0, 62%, 98%);
        --primary-100: hsl(0, 62%, 95%);
        --primary-200: hsl(0, 62%, 90%);
        --primary-300: hsl(0, 62%, 75%);
        --primary-400: hsl(0, 62%, 60%);
        --primary-500: hsl(0, 62%, 47%);   /* Main brand red */
        --primary-600: hsl(0, 62%, 40%);
        --primary-700: hsl(0, 62%, 33%);
        --primary-800: hsl(0, 62%, 27%);
        --primary-900: hsl(0, 62%, 20%);
        
        /* Neutral Palette - Professional Grays */
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
        
        /* Background System */
        --background: hsl(210, 20%, 98%);
        --background-secondary: hsl(210, 20%, 96%);
        --surface: hsl(0, 0%, 100%);
        --surface-elevated: hsl(0, 0%, 100%);
        
        /* Border System */
        --border: hsl(210, 14%, 89%);
        --border-hover: hsl(210, 16%, 82%);
        --border-focus: var(--primary-500);
        
        /* Text System */
        --text-primary: hsl(210, 20%, 15%);
        --text-secondary: hsl(210, 12%, 43%);
        --text-tertiary: hsl(210, 10%, 53%);
        --text-disabled: hsl(210, 12%, 71%);
        
        /* Semantic Colors */
        --success-bg: hsl(142, 76%, 96%);
        --success-border: hsl(142, 76%, 86%);
        --success-text: hsl(142, 76%, 30%);
        
        --warning-bg: hsl(38, 92%, 95%);
        --warning-border: hsl(38, 92%, 85%);
        --warning-text: hsl(38, 92%, 35%);
        
        --error-bg: hsl(0, 86%, 97%);
        --error-border: hsl(0, 86%, 90%);
        --error-text: hsl(0, 86%, 40%);
        
        --info-bg: var(--primary-50);
        --info-border: var(--primary-200);
        --info-text: var(--primary-700);
        
        /* Shadows - Professional Depth */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1);
        --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
        
        /* Spacing Scale */
        --spacing-1: 0.25rem;
        --spacing-2: 0.5rem;
        --spacing-3: 0.75rem;
        --spacing-4: 1rem;
        --spacing-5: 1.25rem;
        --spacing-6: 1.5rem;
        --spacing-8: 2rem;
        --spacing-10: 2.5rem;
        --spacing-12: 3rem;
        
        /* Border Radius */
        --radius-sm: 0.25rem;
        --radius: 0.5rem;
        --radius-md: 0.75rem;
        --radius-lg: 1rem;
        --radius-xl: 1.5rem;
        
        /* Typography Scale */
        --font-size-xs: 0.75rem;
        --font-size-sm: 0.875rem;
        --font-size-base: 1rem;
        --font-size-lg: 1.125rem;
        --font-size-xl: 1.25rem;
        --font-size-2xl: 1.5rem;
        --font-size-3xl: 1.875rem;
        --font-size-4xl: 2.25rem;
    }
    
    /* === GLOBAL RESETS === */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Main App Container */
    .main {
        background: var(--background);
        padding: var(--spacing-6) var(--spacing-8);
    }
    
    /* === STREAMLIT COMPONENT OVERRIDES === */
    
    /* Headers with Professional Styling */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary);
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1.2;
    }
    
    h1 {
        font-size: var(--font-size-4xl);
        margin-bottom: var(--spacing-6);
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        font-size: var(--font-size-2xl);
        margin-bottom: var(--spacing-4);
        color: var(--text-primary);
        border-bottom: 2px solid var(--border);
        padding-bottom: var(--spacing-3);
    }
    
    h3 {
        font-size: var(--font-size-xl);
        margin-bottom: var(--spacing-3);
        color: var(--primary-700);
    }
    
    /* Sidebar Styling - Red Gradient */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, hsl(0, 62%, 98%) 0%, hsl(0, 62%, 95%) 100%);
        border-right: 1px solid hsl(0, 62%, 75%);
        box-shadow: var(--shadow-lg);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--primary-700);
        font-weight: 700;
        padding: var(--spacing-4) 0;
    }
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: var(--spacing-3) var(--spacing-4);
        font-size: var(--font-size-sm);
        color: var(--text-primary);
        transition: all 0.2s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--border-focus);
        outline: none;
        box-shadow: 0 0 0 3px hsla(210, 100%, 60%, 0.1);
    }
    
    /* Buttons - shadcn/ui Style */
    .stButton > button {
        background: var(--primary-600);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: var(--spacing-3) var(--spacing-6);
        font-weight: 600;
        font-size: var(--font-size-sm);
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        background: var(--primary-700);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }
    
    .stButton > button:active {
        transform: translateY(0);
        box-shadow: var(--shadow-sm);
    }
    
    /* Download Button */
    .stDownloadButton > button {
        background: var(--success-text);
        color: white;
        border: none;
        border-radius: var(--radius);
        padding: var(--spacing-3) var(--spacing-6);
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stDownloadButton > button:hover {
        background: hsl(142, 76%, 25%);
        box-shadow: var(--shadow-md);
    }
    
    /* Checkboxes & Radio */
    .stCheckbox, .stRadio {
        padding: var(--spacing-2) 0;
    }
    
    .stCheckbox > label,
    .stRadio > label {
        color: var(--text-primary);
        font-size: var(--font-size-sm);
        font-weight: 500;
    }
    
    /* Slider */
    .stSlider > div > div > div {
        background: var(--primary-500);
    }
    
    /* Metrics - Enhanced Cards */
    [data-testid="stMetricValue"] {
        font-size: var(--font-size-2xl);
        font-weight: 700;
        color: var(--text-primary);
    }
    
    [data-testid="stMetricDelta"] {
        font-size: var(--font-size-sm);
        font-weight: 600;
    }
    
    div[data-testid="stMetricValue"] > div {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* DataFrame Styling */
    .dataframe {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }
    
    .dataframe thead th {
        background: var(--primary-600);
        color: white;
        font-weight: 600;
        padding: var(--spacing-3) var(--spacing-4);
        border: none;
        text-align: left;
    }
    
    .dataframe tbody td {
        padding: var(--spacing-3) var(--spacing-4);
        border-bottom: 1px solid var(--border);
        color: var(--text-primary);
    }
    
    .dataframe tbody tr:hover {
        background: var(--neutral-50);
    }
    
    /* Expander/Accordion */
    [data-testid="stExpander"] {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
        margin-bottom: var(--spacing-4);
        box-shadow: var(--shadow-sm);
    }
    
    [data-testid="stExpander"] summary {
        background: var(--surface);
        padding: var(--spacing-4);
        cursor: pointer;
        font-weight: 600;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border);
    }
    
    [data-testid="stExpander"] summary:hover {
        background: var(--neutral-50);
    }
    
    /* Tabs */
    [data-testid="stTabs"] [role="tablist"] button {
        background: transparent;
        border: 1px solid var(--border);
        border-bottom: none;
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: var(--spacing-3) var(--spacing-6);
        color: var(--text-secondary);
        font-weight: 500;
        margin-right: var(--spacing-2);
    }
    
    [data-testid="stTabs"] [role="tablist"] button[aria-selected="true"] {
        background: var(--surface);
        color: var(--primary-600);
        border-color: var(--border);
        border-bottom: 1px solid var(--surface);
        font-weight: 600;
    }
    
    [data-testid="stTabs"] > div > div {
        border-top: 1px solid var(--border);
        background: var(--surface);
        border-radius: 0 var(--radius) var(--radius) var(--radius);
        padding: var(--spacing-6);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: var(--primary-600);
        border-radius: var(--radius-sm);
    }
    
    /* Select Box */
    .stSelectbox > div > div > div {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
    }
    
    /* Multi-Select */
    .stMultiSelect > div > div > div {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
    }
    
    /* Success/Info/Warning/Error Messages */
    .element-container:has([data-testid="stAlert"]) {
        margin-bottom: var(--spacing-4);
    }
    
    [data-testid="stAlert"] {
        padding: var(--spacing-4);
        border-radius: var(--radius);
        border: 1px solid;
        font-size: var(--font-size-sm);
    }
    
    [data-testid="stAlert"][data-baseweb="notification-success"] {
        background: var(--success-bg);
        border-color: var(--success-border);
        color: var(--success-text);
    }
    
    [data-testid="stAlert"][data-baseweb="notification-info"] {
        background: var(--info-bg);
        border-color: var(--info-border);
        color: var(--info-text);
    }
    
    [data-testid="stAlert"][data-baseweb="notification-warning"] {
        background: var(--warning-bg);
        border-color: var(--warning-border);
        color: var(--warning-text);
    }
    
    [data-testid="stAlert"][data-baseweb="notification-error"] {
        background: var(--error-bg);
        border-color: var(--error-border);
        color: var(--error-text);
    }
    
    /* Professional Card Components */
    .metric-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: var(--spacing-6);
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
        height: 150px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    .metric-card h3 {
        font-size: var(--font-size-sm);
        font-weight: 600;
        color: var(--text-secondary);
        margin: 0 0 var(--spacing-2) 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-card h2 {
        font-size: var(--font-size-2xl);
        font-weight: 700;
        margin: 0 0 var(--spacing-2) 0;
        border: none;
        padding: 0;
    }
    
    .metric-card p {
        font-size: var(--font-size-xs);
        color: var(--text-tertiary);
        margin: 0;
        line-height: 1.4;
    }
    
    /* Pattern Cards */
    .pattern-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: var(--spacing-5);
        margin-bottom: var(--spacing-4);
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }
    
    .pattern-card:hover {
        box-shadow: var(--shadow-md);
        border-color: var(--primary-500);
    }
    
    .pattern-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: var(--spacing-4);
        padding-bottom: var(--spacing-3);
        border-bottom: 1px solid var(--border);
    }
    
    .pattern-title {
        font-size: var(--font-size-lg);
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
    }
    
    .pattern-badge {
        background: var(--primary-600);
        color: white;
        padding: var(--spacing-1) var(--spacing-3);
        border-radius: var(--radius);
        font-size: var(--font-size-xs);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .pattern-metrics {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: var(--spacing-3);
        margin-top: var(--spacing-3);
    }
    
    .pattern-metric {
        text-align: center;
        padding: var(--spacing-2);
        background: var(--neutral-50);
        border-radius: var(--radius-sm);
    }
    
    .pattern-metric-value {
        font-size: var(--font-size-lg);
        font-weight: 700;
        color: var(--primary-600);
        margin: 0;
    }
    
    .pattern-metric-label {
        font-size: var(--font-size-xs);
        color: var(--text-secondary);
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Professional Header */
    .professional-header {
        text-align: center;
        padding: var(--spacing-8) 0;
        background: linear-gradient(135deg, var(--primary-50), var(--neutral-50));
        border-radius: var(--radius-lg);
        margin-bottom: var(--spacing-8);
        border: 1px solid var(--border);
    }
    
    .professional-header h1 {
        font-size: var(--font-size-4xl);
        font-weight: 800;
        margin: 0 0 var(--spacing-3) 0;
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .subtitle {
        font-size: var(--font-size-lg);
        color: var(--text-secondary);
        margin: 0 0 var(--spacing-2) 0;
        font-weight: 500;
    }
    
    .description {
        font-size: var(--font-size-sm);
        color: var(--text-tertiary);
        margin: 0;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.5;
    }
    
    /* Status Indicators */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: var(--spacing-1) var(--spacing-3);
        border-radius: var(--radius);
        font-size: var(--font-size-xs);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .status-success {
        background: var(--success-bg);
        color: var(--success-text);
        border: 1px solid var(--success-border);
    }
    
    .status-warning {
        background: var(--warning-bg);
        color: var(--warning-text);
        border: 1px solid var(--warning-border);
    }
    
    .status-error {
        background: var(--error-bg);
        color: var(--error-text);
        border: 1px solid var(--error-border);
    }
    
    /* Loading States */
    .loading-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid var(--border);
        border-radius: 50%;
        border-top-color: var(--primary-600);
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main {
            padding: var(--spacing-4);
        }
        
        .professional-header {
            padding: var(--spacing-6) var(--spacing-4);
        }
        
        .professional-header h1 {
            font-size: var(--font-size-3xl);
        }
        
        .pattern-metrics {
            grid-template-columns: 1fr;
        }
        
        .metric-card {
            height: auto;
            min-height: 120px;
        }
    }
    
    /* Enhanced Focus States */
    .stButton > button:focus,
    .stDownloadButton > button:focus {
        outline: 2px solid var(--primary-500);
        outline-offset: 2px;
    }
    
    /* Custom Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--neutral-100);
        border-radius: var(--radius-sm);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--neutral-400);
        border-radius: var(--radius-sm);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--neutral-500);
    }
    
    /* Print Styles */
    @media print {
        .stSidebar {
            display: none !important;
        }
        
        .main {
            padding: 0;
        }
        
        .professional-header,
        .metric-card,
        .pattern-card {
            box-shadow: none;
            border: 1px solid var(--neutral-300);
        }
    }
</style>
""", unsafe_allow_html=True)

def get_nse_non_fno_stocks():
    """Enhanced NSE stock list with comprehensive F&O universe"""
    try:
        # Using a more reliable endpoint for NSE F&O stocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        
        # Get main NSE page first to establish session
        session.get('https://www.nseindia.com/', timeout=10)
        
        response = session.get('https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500', timeout=15)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            return [item['symbol'] + '.NS' for item in data if 'symbol' in item][:219]
    except:
        pass
    
    return _get_comprehensive_backup_list()

def create_excel_stock_list(results):
    """Create Excel file with stock analysis results"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Main Results Sheet
        df_main = pd.DataFrame([
            {
                'Stock': result['symbol'],
                'Pattern': result['pattern'],
                'Strength': f"{result['strength']}%",
                'Success Rate': f"{result['success_rate']}%",
                'CCS Suitability': f"{result['ccs_suitability']}%",
                'Volume Ratio': f"{result.get('volume_ratio', 'N/A')}x",
                'Breakout': f"{result.get('breakout_percentage', 'N/A')}%",
                'Current Price': result.get('current_price', 'N/A')
            }
            for result in results
        ])
        df_main.to_excel(writer, sheet_name='CCS_Opportunities', index=False)
        
        # Pattern Summary Sheet
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

def _get_comprehensive_backup_list():
    """Comprehensive backup list of NSE F&O stocks - 219 stocks total"""
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
        'HINDCOPPER.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HONAUT.NS', 'HUDCO.NS',
        'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDEA.NS', 'IDFC.NS',
        'IDFCFIRSTB.NS', 'IEX.NS', 'IGL.NS', 'INDHOTEL.NS', 'INDIACEM.NS',
        'INDIAMART.NS', 'INDIGO.NS', 'INDUSINDBK.NS', 'INDUSTOWER.NS', 'INFY.NS',
        'IOC.NS', 'IPCALAB.NS', 'IRB.NS', 'IRCTC.NS', 'ITC.NS',
        'JINDALSTEL.NS', 'JKCEMENT.NS', 'JSWSTEEL.NS', 'JUBLFOOD.NS', 'KOTAKBANK.NS',
        'L&TFH.NS', 'LALPATHLAB.NS', 'LAURUSLABS.NS', 'LICHSGFIN.NS', 'LT.NS',
        'LTI.NS', 'LTIM.NS', 'LTTS.NS', 'LUPIN.NS', 'M&M.NS',
        'M&MFIN.NS', 'MANAPPURAM.NS', 'MARICO.NS', 'MARUTI.NS', 'MCX.NS',
        'METROPOLIS.NS', 'MFSL.NS', 'MGL.NS', 'MOTHERSON.NS', 'MPHASIS.NS',
        'MRF.NS', 'MUTHOOTFIN.NS', 'NATIONALUM.NS', 'NAUKRI.NS', 'NAVINFLUOR.NS',
        'NESTLEIND.NS', 'NMDC.NS', 'NTPC.NS', 'OBEROIRLTY.NS', 'OFSS.NS',
        'ONGC.NS', 'PAGEIND.NS', 'PEL.NS', 'PERSISTENT.NS', 'PETRONET.NS',
        'PFC.NS', 'PIDILITIND.NS', 'PIIND.NS', 'PNB.NS', 'POLYCAB.NS',
        'POWERGRID.NS', 'PVRINOX.NS', 'RAMCOCEM.NS', 'RBLBANK.NS', 'RECLTD.NS',
        'RELIANCE.NS', 'SAIL.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SBIN.NS',
        'SHREECEM.NS', 'SIEMENS.NS', 'SRF.NS', 'SUNPHARMA.NS', 'SUNTV.NS',
        'SUPREMEIND.NS', 'SYNGENE.NS', 'TATACHEM.NS', 'TATACOMM.NS', 'TATACONSUM.NS',
        'TATAMOTORS.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TCS.NS', 'TECHM.NS',
        'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS', 'TVSMOTOR.NS', 'UBL.NS',
        'ULTRACEMCO.NS', 'UPL.NS', 'VEDL.NS', 'VOLTAS.NS', 'WIPRO.NS',
        'ZEEL.NS', 'ZYDUSLIFE.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'ALKEM.NS',
        'ARE&M.NS', 'BAJAJHLDNG.NS', 'BALMLAWRIE.NS', 'BHARATDYN.NS', 'BHARTGEAR.NS',
        'BINANIIND.NS', 'BLUESTARCO.NS', 'BORORENEW.NS', 'BRIGADE.NS', 'CDSL.NS',
        'CENTRALBK.NS', 'CHAMBLFERT.NS', 'COALINDIA.NS', 'DCMSHRIRAM.NS', 'DELTACORP.NS',
        'DISHTV.NS', 'DMART.NS', 'EMAMILTD.NS', 'FCONSUMER.NS', 'FINEORG.NS',
        'FSL.NS', 'GAIL.NS', 'GICRE.NS', 'GILLETTE.NS', 'GLAXO.NS',
        'GODREJAGRO.NS', 'GPPL.NS', 'GSHIP.NS', 'GSPL.NS', 'GUJALKALI.NS',
        'HATHWAY.NS', 'HEG.NS', 'HFCL.NS', 'HIMATSEIDE.NS', 'HMVL.NS',
        'IBULHSGFIN.NS', 'IDBI.NS', 'IIFL.NS', 'INFIBEAM.NS', 'INOXLEISUR.NS',
        'INTELLECT.NS', 'ISEC.NS', 'J&KBANK.NS', 'JAICORPLTD.NS', 'JAMNAAUTO.NS',
        'JCHAC.NS', 'JETAIRWAYS.NS', 'JISLJALEQS.NS', 'JMFINANCIL.NS', 'JSW.NS',
        'JSWENERGY.NS', 'JYOTHYLAB.NS', 'KAJARIACER.NS', 'KALPATPOWR.NS', 'KANSAINER.NS',
        'KEI.NS', 'KNRCON.NS', 'KPITTECH.NS', 'KRBL.NS', 'KSCL.NS',
        'KTKBANK.NS', 'LINDEINDIA.NS', 'LOTUSEYE.NS', 'LOVABLE.NS', 'LPDC.NS', 'LT.NS', 'LTFOODS.NS', 'LTFH.NS',
        'LTI.NS', 'LTIM.NS', 'LTTS.NS', 'LUMAXIND.NS', 'LUMAXTECH.NS', 'LUPIN.NS',
        'LUXIND.NS', 'LYKALABS.NS', 'M&M.NS', 'M&MFIN.NS', 'MAANALU.NS', 'MACPOWER.NS'
    ]

class ProfessionalCCSScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_stock_data(self, symbol, period="3mo"):
        """Get current stock data with enhanced error handling"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            
            if data.empty:
                return None
                
            # Ensure we have volume data
            if 'Volume' not in data.columns or data['Volume'].isna().all():
                return None
                
            # Add technical indicators
            data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
            data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
            data['EMA_12'] = ta.trend.ema_indicator(data['Close'], window=12)
            data['EMA_26'] = ta.trend.ema_indicator(data['Close'], window=26)
            data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
            data['MACD'] = ta.trend.macd_diff(data['Close'])
            data['BB_upper'], data['BB_lower'] = ta.volatility.bollinger_hband(data['Close']), ta.volatility.bollinger_lband(data['Close'])
            
            # Volume indicators
            data['Volume_SMA'] = ta.trend.sma_indicator(data['Volume'], window=20)
            
            return data
            
        except Exception as e:
            return None
    
    def get_weekly_stock_data(self, symbol, period="6mo"):
        """Get weekly stock data for trend analysis"""
        try:
            ticker = yf.Ticker(symbol)
            daily_data = ticker.history(period=period)
            
            if daily_data.empty:
                return None
            
            # Resample to weekly data
            weekly_data = daily_data.resample('W').agg({
                'Open': 'first',
                'High': 'max', 
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })
            
            if weekly_data.empty or len(weekly_data) < 10:
                return None
            
            # Add weekly technical indicators
            weekly_data['SMA_10'] = ta.trend.sma_indicator(weekly_data['Close'], window=10)
            weekly_data['SMA_20'] = ta.trend.sma_indicator(weekly_data['Close'], window=20)
            weekly_data['RSI'] = ta.momentum.rsi(weekly_data['Close'], window=14)
            weekly_data['Volume_SMA'] = ta.trend.sma_indicator(weekly_data['Volume'], window=10)
            
            return weekly_data
            
        except Exception as e:
            return None
    
    def validate_weekly_strength(self, daily_data, weekly_data, pattern_type):
        """Validate pattern strength using weekly timeframe - INVERTED FOR CALL CREDIT SPREADS"""
        if daily_data is None or weekly_data is None or len(weekly_data) < 10:
            return {
                'weekly_confirmed': False,
                'weekly_strength_bonus': 0,
                'weekly_trend': 'Unknown',
                'weekly_support_resistance': 'Unknown',
                'weekly_volume_trend': 'Unknown',
                'weekly_rsi': 'Unknown'
            }
        
        try:
            # Get current weekly values
            current_weekly_close = weekly_data['Close'].iloc[-1]
            weekly_sma_10 = weekly_data['SMA_10'].iloc[-1] if not pd.isna(weekly_data['SMA_10'].iloc[-1]) else current_weekly_close
            weekly_sma_20 = weekly_data['SMA_20'].iloc[-1] if not pd.isna(weekly_data['SMA_20'].iloc[-1]) else current_weekly_close
            weekly_rsi = weekly_data['RSI'].iloc[-1] if not pd.isna(weekly_data['RSI'].iloc[-1]) else 50
            
            # Weekly trend analysis - INVERTED FOR CCS (we want bearish weekly trends)
            weekly_trend = 'Unknown'
            trend_bonus = 0
            
            if current_weekly_close < weekly_sma_10 and weekly_sma_10 < weekly_sma_20:
                weekly_trend = 'Strong Bearish'
                trend_bonus = 25  # Strong bonus for bearish trend in CCS
            elif current_weekly_close < weekly_sma_10:
                weekly_trend = 'Bearish'
                trend_bonus = 15
            elif current_weekly_close < weekly_sma_20:
                weekly_trend = 'Weak Bearish'  
                trend_bonus = 10
            elif current_weekly_close > weekly_sma_10 and weekly_sma_10 > weekly_sma_20:
                weekly_trend = 'Strong Bullish'
                trend_bonus = -15  # Penalty for bullish trend in CCS
            else:
                weekly_trend = 'Neutral'
                trend_bonus = 5
            
            # Weekly RSI analysis - INVERTED FOR CCS (we want overbought conditions)
            rsi_bonus = 0
            rsi_status = 'Neutral'
            
            if weekly_rsi >= 70:
                rsi_status = 'Overbought'
                rsi_bonus = 20  # Good for CCS - stock is overbought
            elif weekly_rsi >= 60:
                rsi_status = 'Approaching Overbought'
                rsi_bonus = 10
            elif weekly_rsi <= 30:
                rsi_status = 'Oversold'
                rsi_bonus = -10  # Not ideal for CCS
            elif weekly_rsi <= 40:
                rsi_status = 'Approaching Oversold'
                rsi_bonus = -5
            else:
                rsi_status = 'Neutral'
                rsi_bonus = 0
            
            # Support and resistance analysis
            support_resistance = self._analyze_weekly_support_resistance(weekly_data)
            
            # Volume trend analysis  
            volume_trend = self._analyze_weekly_volume_trend(weekly_data)
            
            # Pattern-specific weekly bonus - ADJUSTED FOR CCS
            pattern_bonus = self._get_pattern_specific_weekly_bonus(pattern_type, weekly_data)
            
            # Calculate total weekly strength bonus
            total_weekly_bonus = trend_bonus + rsi_bonus + pattern_bonus
            
            # Weekly confirmation logic - INVERTED FOR CCS
            weekly_confirmed = (
                (weekly_trend in ['Strong Bearish', 'Bearish', 'Weak Bearish']) and
                (weekly_rsi >= 50) and  # Prefer higher RSI for CCS
                (total_weekly_bonus >= 10)
            )
            
            return {
                'weekly_confirmed': weekly_confirmed,
                'weekly_strength_bonus': max(0, min(total_weekly_bonus, 30)),  # Cap at 30
                'weekly_trend': weekly_trend,
                'weekly_support_resistance': support_resistance,
                'weekly_volume_trend': volume_trend,
                'weekly_rsi': f"{weekly_rsi:.1f} ({rsi_status})",
                'weekly_trend_bonus': trend_bonus,
                'weekly_rsi_bonus': rsi_bonus,
                'weekly_pattern_bonus': pattern_bonus
            }
            
        except Exception as e:
            return {
                'weekly_confirmed': False,
                'weekly_strength_bonus': 0,
                'weekly_trend': 'Error',
                'weekly_support_resistance': 'Error',
                'weekly_volume_trend': 'Error', 
                'weekly_rsi': 'Error'
            }
    
    def _analyze_weekly_support_resistance(self, weekly_data):
        """Analyze weekly support and resistance levels"""
        try:
            if len(weekly_data) < 10:
                return 'Insufficient Data'
            
            # Get recent highs and lows
            recent_weeks = weekly_data.tail(12)  # Last 12 weeks
            current_price = weekly_data['Close'].iloc[-1]
            
            # Find potential resistance levels (recent highs)
            resistance_levels = []
            for i in range(2, len(recent_weeks)-2):
                if (recent_weeks['High'].iloc[i] > recent_weeks['High'].iloc[i-1] and 
                    recent_weeks['High'].iloc[i] > recent_weeks['High'].iloc[i+1] and
                    recent_weeks['High'].iloc[i] > recent_weeks['High'].iloc[i-2] and
                    recent_weeks['High'].iloc[i] > recent_weeks['High'].iloc[i+2]):
                    resistance_levels.append(recent_weeks['High'].iloc[i])
            
            # For CCS, we want to be near resistance levels
            if resistance_levels:
                nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
                distance_to_resistance = ((nearest_resistance - current_price) / current_price) * 100
                
                if abs(distance_to_resistance) <= 3:  # Within 3% of resistance
                    return f'Near Resistance ({distance_to_resistance:+.1f}%)'
                elif distance_to_resistance < -3:  # Below resistance by more than 3%
                    return f'Below Resistance ({distance_to_resistance:+.1f}%)'
                else:  # Above resistance
                    return f'Above Resistance ({distance_to_resistance:+.1f}%)'
            
            return 'No Clear Levels'
            
        except Exception:
            return 'Analysis Error'
    
    def _analyze_weekly_volume_trend(self, weekly_data):
        """Analyze weekly volume trends"""
        try:
            if len(weekly_data) < 10:
                return 'Insufficient Data'
            
            current_volume = weekly_data['Volume'].iloc[-1]
            avg_volume = weekly_data['Volume_SMA'].iloc[-1]
            
            if pd.isna(avg_volume) or avg_volume == 0:
                return 'No Volume Data'
            
            volume_ratio = current_volume / avg_volume
            
            if volume_ratio >= 1.5:
                return f'High Volume ({volume_ratio:.1f}x)'
            elif volume_ratio >= 1.2:
                return f'Above Average ({volume_ratio:.1f}x)'
            elif volume_ratio <= 0.7:
                return f'Low Volume ({volume_ratio:.1f}x)'
            else:
                return f'Average Volume ({volume_ratio:.1f}x)'
                
        except Exception:
            return 'Volume Analysis Error'
    
    def _get_pattern_specific_weekly_bonus(self, pattern_type, weekly_data):
        """Get pattern-specific weekly validation bonus - ADJUSTED FOR CCS"""
        try:
            if len(weekly_data) < 5:
                return 0
                
            current_close = weekly_data['Close'].iloc[-1]
            prev_close = weekly_data['Close'].iloc[-2]
            weekly_change = ((current_close - prev_close) / prev_close) * 100
            
            # For CCS patterns, we generally want bearish weekly momentum
            if pattern_type in ['Rectangle Top', 'Head and Shoulders', 'Triple Top']:
                # These are bearish reversal patterns - good for CCS
                if weekly_change <= -2:  # Bearish weekly move
                    return 15
                elif weekly_change <= 0:
                    return 10
                else:
                    return -5  # Bullish move reduces CCS attractiveness
            
            elif pattern_type in ['Rising Wedge', 'Double Top']:
                # Bearish patterns - good for CCS
                if weekly_change <= -1:
                    return 12
                elif weekly_change <= 0:
                    return 8
                else:
                    return -3
            
            elif pattern_type in ['Bear Flag', 'Descending Triangle']:
                # Continuation bearish patterns - excellent for CCS
                if weekly_change <= -1.5:
                    return 18
                elif weekly_change <= 0:
                    return 12
                else:
                    return -8
            
            else:
                # For other patterns, neutral approach
                if weekly_change <= -1:
                    return 8
                elif weekly_change <= 0:
                    return 5
                else:
                    return 0
                    
        except Exception:
            return 0
    
    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if volume criteria is met for pattern validation"""
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
    
    def get_fundamental_news(self, symbol, stock_name):
        """Get recent news for fundamental analysis"""
        try:
            # Clean stock name for search
            clean_name = stock_name.replace('.NS', '').replace('&', 'and')
            search_query = f"{clean_name} stock news india"
            
            # Use Google News search
            search_url = f"https://www.google.com/search?q={search_query}&tbm=nws"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = self.session.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract news headlines
                news_items = []
                
                # Try multiple selectors for news items
                selectors = [
                    'div.BNeawe.vvjwJb.AP7Wnd',
                    'div.BNeawe.UPmit.AP7Wnd',
                    'h3.LC20lb.MBeuO.DKV0Md'
                ]
                
                for selector in selectors:
                    elements = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:2]
                    if elements:
                        news_elements = soup.find_all('div', class_='BNeawe vvjwJb AP7Wnd')[:2]
                        for element in news_elements:
                            headline = element.get_text().strip()
                            if headline and len(headline) > 20:
                                news_items.append(headline)
                        break
                
                if not news_items:
                    return "No recent news found"
                
                # Analyze sentiment of headlines
                positive_words = ['surge', 'gain', 'profit', 'growth', 'rise', 'jump', 'soar', 'rally', 'boost', 'strong', 'beat', 'exceed', 'outperform']
                negative_words = ['fall', 'drop', 'decline', 'loss', 'weak', 'miss', 'disappoint', 'crash', 'plunge', 'concern', 'risk', 'trouble']
                
                sentiment_score = 0
                for headline in news_items[:3]:  # Analyze top 3 headlines
                    headline_lower = headline.lower()
                    sentiment_score += sum(1 for word in positive_words if word in headline_lower)
                    sentiment_score -= sum(1 for word in negative_words if word in headline_lower)
                
                # Determine overall news sentiment - INVERTED FOR CCS
                if sentiment_score >= 2:
                    return "Recent positive news - May reduce CCS attractiveness"
                elif sentiment_score <= -2:
                    return "Recent negative news - Favorable for CCS"
                else:
                    return "Mixed/Neutral news sentiment"
            
            return "News data unavailable"
            
        except Exception:
            return "News analysis error"
    
    def _assess_news_relevance(self, headline):
        """Assess relevance of news headline to stock performance"""
        relevant_keywords = [
            'earnings', 'quarterly', 'results', 'revenue', 'profit', 'loss',
            'acquisition', 'merger', 'partnership', 'contract', 'order',
            'regulatory', 'approval', 'launch', 'expansion', 'investment'
        ]
        
        headline_lower = headline.lower()
        relevance_score = sum(1 for keyword in relevant_keywords if keyword in headline_lower)
        
        return relevance_score >= 2  # At least 2 relevant keywords

    def detect_current_day_breakout(self, data, lookback_days=20, min_volume_ratio=2.0):
        """Detect current day breakout - INVERTED FOR CCS (looking for breakdowns)"""
        try:
            if len(data) < lookback_days + 5:
                return False, {}
            
            # Current day data
            current_close = data['Close'].iloc[-1]
            current_high = data['High'].iloc[-1] 
            current_low = data['Low'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            
            # Historical data for comparison
            lookback_data = data.iloc[-(lookback_days+1):-1]  # Exclude current day
            
            # Calculate key levels
            recent_high = lookback_data['High'].max()
            recent_low = lookback_data['Low'].min()
            avg_volume = lookback_data['Volume'].mean()
            
            # For CCS - we want breakdown below support (recent low)
            breakdown_occurred = current_low < recent_low * 0.99  # Broke below recent low by 1%
            
            # Volume confirmation
            volume_confirmed = current_volume >= (avg_volume * min_volume_ratio)
            
            # Calculate breakdown percentage
            breakdown_percentage = ((recent_low - current_low) / recent_low) * 100 if breakdown_occurred else 0
            
            # Price action confirmation - we want bearish action for CCS
            open_price = data['Open'].iloc[-1]
            bearish_close = current_close < open_price  # Closed below open
            close_strength = ((current_close - current_low) / (current_high - current_low)) * 100 if current_high != current_low else 50
            
            # Lower close strength is better for CCS (closer to day's low)
            ccs_friendly = close_strength <= 40  # Closed in lower 40% of day's range
            
            # Overall breakdown confirmation for CCS
            breakdown_confirmed = (
                breakdown_occurred and
                volume_confirmed and
                bearish_close and
                ccs_friendly
            )
            
            details = {
                'breakdown_occurred': breakdown_occurred,
                'volume_confirmed': volume_confirmed,
                'bearish_close': bearish_close,
                'breakdown_percentage': breakdown_percentage,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                'close_strength': close_strength,
                'recent_low': recent_low,
                'current_low': current_low,
                'ccs_friendly': ccs_friendly
            }
            
            return breakdown_confirmed, details
            
        except Exception as e:
            return False, {'error': str(e)}
    
    def get_market_sentiment_indicators(self):
        """Get market sentiment indicators - ADJUSTED FOR CCS"""
        sentiment_data = {}
        
        try:
            # Get Nifty 50 data
            nifty = yf.Ticker('^NSEI')
            nifty_data = nifty.history(period='5d')
            
            if not nifty_data.empty:
                nifty_change = ((nifty_data['Close'].iloc[-1] - nifty_data['Close'].iloc[-2]) / nifty_data['Close'].iloc[-2]) * 100
                
                # For CCS - bearish market is good
                if nifty_change <= -1.5:
                    nifty_sentiment = "BEARISH_STRONG"
                elif nifty_change <= -0.5:
                    nifty_sentiment = "BEARISH"
                elif nifty_change <= 0.5:
                    nifty_sentiment = "NEUTRAL"
                elif nifty_change <= 1.5:
                    nifty_sentiment = "BULLISH"
                else:
                    nifty_sentiment = "BULLISH_STRONG"
                
                sentiment_data['nifty'] = {
                    'change_pct': nifty_change,
                    'sentiment': nifty_sentiment,
                    'level': nifty_data['Close'].iloc[-1]
                }
            
            # Get Bank Nifty data
            bank_nifty = yf.Ticker('^NSEBANK')
            bank_data = bank_nifty.history(period='5d')
            
            if not bank_data.empty:
                bank_change = ((bank_data['Close'].iloc[-1] - bank_data['Close'].iloc[-2]) / bank_data['Close'].iloc[-2]) * 100
                
                # For CCS - bearish bank nifty is good
                if bank_change <= -2:
                    bank_sentiment = "BEARISH_STRONG" 
                elif bank_change <= -0.8:
                    bank_sentiment = "BEARISH"
                elif bank_change <= 0.8:
                    bank_sentiment = "NEUTRAL"
                elif bank_change <= 2:
                    bank_sentiment = "BULLISH"
                else:
                    bank_sentiment = "BULLISH_STRONG"
                    
                sentiment_data['bank_nifty'] = {
                    'change_pct': bank_change,
                    'sentiment': bank_sentiment,
                    'level': bank_data['Close'].iloc[-1]
                }
            
            # Overall sentiment calculation - INVERTED FOR CCS
            if 'nifty' in sentiment_data and 'bank_nifty' in sentiment_data:
                sentiment_scores = {
                    "BEARISH_STRONG": 4,  # Best for CCS
                    "BEARISH": 3,
                    "NEUTRAL": 2,
                    "BULLISH": 1,
                    "BULLISH_STRONG": 0   # Worst for CCS
                }
                
                nifty_score = sentiment_scores.get(sentiment_data['nifty']['sentiment'], 2)
                bank_score = sentiment_scores.get(sentiment_data['bank_nifty']['sentiment'], 2)
                overall_score = (nifty_score * 0.6) + (bank_score * 0.4)
                
                if overall_score >= 3.2:
                    overall_sentiment = "BEARISH"
                    ccs_recommendation = "Excellent for Call Credit Spreads"
                    risk_level = "LOW"
                elif overall_score >= 2.2:
                    overall_sentiment = "NEUTRAL"
                    ccs_recommendation = "Moderate CCS opportunities"
                    risk_level = "MEDIUM"
                else:
                    overall_sentiment = "BULLISH"
                    ccs_recommendation = "Avoid CCS, consider Put Credit Spreads"
                    risk_level = "HIGH"
                
                sentiment_data['overall'] = {
                    'sentiment': overall_sentiment,
                    'score': overall_score,
                    'ccs_recommendation': ccs_recommendation,
                    'risk_level': risk_level
                }
            
        except Exception as e:
            sentiment_data = {
                'error': str(e),
                'overall': {
                    'sentiment': 'UNKNOWN',
                    'ccs_recommendation': 'Data unavailable - trade with caution',
                    'risk_level': 'HIGH'
                }
            }
        
        return sentiment_data
    
    def _get_sentiment_level(self, change_pct):
        """Convert percentage change to sentiment level"""
        if change_pct <= -2:
            return "VERY_BEARISH"
        elif change_pct <= -0.5:
            return "BEARISH"
        elif change_pct <= 0.5:
            return "NEUTRAL"
        elif change_pct <= 2:
            return "BULLISH"
        else:
            return "VERY_BULLISH"
    
    def detect_patterns(self, data, symbol, filters):
        """Enhanced pattern detection with current day confirmation - ADJUSTED FOR CCS"""
        if data is None or len(data) < 30:
            return []
        
        patterns_found = []
        
        # Pattern detection methods - INVERTED FOR CCS (looking for bearish patterns)
        pattern_methods = [
            ('Rectangle Top', self.detect_rectangle_top),
            ('Head and Shoulders', self.detect_head_and_shoulders), 
            ('Triple Top', self.detect_triple_top),
            ('Double Top', self.detect_double_top),
            ('Rising Wedge', self.detect_rising_wedge),
            ('Bear Flag', self.detect_bear_flag),
            ('Descending Triangle', self.detect_descending_triangle),
            ('Evening Star', self.detect_evening_star),
            ('Dark Cloud Cover', self.detect_dark_cloud_cover),
            ('Hanging Man', self.detect_hanging_man),
            ('Shooting Star', self.detect_shooting_star),
            ('Bearish Engulfing', self.detect_bearish_engulfing)
        ]
        
        for pattern_name, detect_method in pattern_methods:
            try:
                detected, strength = detect_method(data)
                
                if detected and strength >= filters.get('min_strength', 70):
                    
                    # Get current day breakdown details
                    breakdown_confirmed, breakdown_details = self.detect_current_day_breakout(
                        data, 
                        lookback_days=filters.get('lookback_days', 20),
                        min_volume_ratio=filters.get('min_volume_ratio', 1.5)
                    )
                    
                    # Volume validation
                    volume_valid, volume_ratio = self.check_volume_criteria(
                        data, 
                        min_ratio=filters.get('volume_ratio', 1.0)
                    )
                    
                    # Calculate final strength
                    final_strength = strength
                    if breakdown_confirmed:
                        final_strength = min(98, strength + 15)
                    if volume_valid and volume_ratio >= 1.5:
                        final_strength = min(98, final_strength + 10)
                    
                    # Get pattern-specific data
                    pattern_info = self._get_pattern_data(pattern_name, data)
                    
                    pattern_result = {
                        'symbol': symbol,
                        'pattern': pattern_name,
                        'strength': final_strength,
                        'success_rate': pattern_info['success_rate'],
                        'ccs_suitability': pattern_info['ccs_suitability'],
                        'current_price': data['Close'].iloc[-1],
                        'breakdown_confirmed': breakdown_confirmed,
                        'volume_confirmed': volume_valid,
                        'volume_ratio': volume_ratio,
                        'breakdown_details': breakdown_details,
                        'pattern_details': pattern_info.get('details', {}),
                        'daily_strength': strength
                    }
                    
                    patterns_found.append(pattern_result)
                    
            except Exception as e:
                continue
        
        return patterns_found
    
    def _get_pattern_data(self, pattern_name, data):
        """Get detailed pattern data with CCS suitability scores"""
        
        # Pattern database with CCS-optimized data
        pattern_db = {
            'Rectangle Top': {
                'success_rate': 88,
                'ccs_suitability': 95,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '8-15%',
                    'timeframe': '2-4 weeks',
                    'risk_reward': '1:3'
                }
            },
            'Head and Shoulders': {
                'success_rate': 85,
                'ccs_suitability': 98,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '10-20%',
                    'timeframe': '3-6 weeks',
                    'risk_reward': '1:4'
                }
            },
            'Triple Top': {
                'success_rate': 82,
                'ccs_suitability': 95,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '12-18%',
                    'timeframe': '4-8 weeks',
                    'risk_reward': '1:3.5'
                }
            },
            'Double Top': {
                'success_rate': 79,
                'ccs_suitability': 92,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '8-16%',
                    'timeframe': '2-5 weeks',
                    'risk_reward': '1:3'
                }
            },
            'Rising Wedge': {
                'success_rate': 76,
                'ccs_suitability': 88,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '6-14%',
                    'timeframe': '2-4 weeks',
                    'risk_reward': '1:2.5'
                }
            },
            'Bear Flag': {
                'success_rate': 84,
                'ccs_suitability': 90,
                'details': {
                    'type': 'Bearish Continuation',
                    'typical_move': '10-18%',
                    'timeframe': '1-3 weeks',
                    'risk_reward': '1:3'
                }
            },
            'Descending Triangle': {
                'success_rate': 81,
                'ccs_suitability': 93,
                'details': {
                    'type': 'Bearish Continuation',
                    'typical_move': '9-17%',
                    'timeframe': '2-5 weeks',
                    'risk_reward': '1:3.2'
                }
            },
            'Evening Star': {
                'success_rate': 78,
                'ccs_suitability': 91,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '7-13%',
                    'timeframe': '1-2 weeks',
                    'risk_reward': '1:2.8'
                }
            },
            'Dark Cloud Cover': {
                'success_rate': 74,
                'ccs_suitability': 89,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '6-12%',
                    'timeframe': '1-3 weeks',
                    'risk_reward': '1:2.5'
                }
            },
            'Hanging Man': {
                'success_rate': 71,
                'ccs_suitability': 87,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '5-11%',
                    'timeframe': '1-2 weeks',
                    'risk_reward': '1:2.3'
                }
            },
            'Shooting Star': {
                'success_rate': 73,
                'ccs_suitability': 85,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '6-12%',
                    'timeframe': '1-2 weeks',
                    'risk_reward': '1:2.4'
                }
            },
            'Bearish Engulfing': {
                'success_rate': 77,
                'ccs_suitability': 88,
                'details': {
                    'type': 'Bearish Reversal',
                    'typical_move': '7-14%',
                    'timeframe': '1-3 weeks',
                    'risk_reward': '1:2.7'
                }
            }
        }
        
        return pattern_db.get(pattern_name, {
            'success_rate': 75,
            'ccs_suitability': 85,
            'details': {
                'type': 'Unknown',
                'typical_move': 'Variable',
                'timeframe': 'Variable',
                'risk_reward': '1:2'
            }
        })

    # INVERTED PATTERN DETECTION METHODS FOR CCS
    # (Previous bullish patterns now become bearish patterns for CCS)

    def detect_rectangle_top(self, data):
        """Rectangle Top pattern with CURRENT DAY confirmation (bearish pattern for CCS)"""
        if len(data) < 25:
            return False, 0
        
        # Look for consolidation at resistance level followed by breakdown
        recent_data = data.tail(20)
        
        # Find resistance level (recent highs)
        resistance_level = recent_data['High'].max()
        support_level = recent_data['Low'].min()
        
        # Rectangle formation criteria
        range_size = ((resistance_level - support_level) / support_level) * 100
        if range_size < 3 or range_size > 15:  # 3-15% range
            return False, 0
        
        # Look for breakdown and current day confirmation
        current_price = data['Close'].iloc[-1]
        current_low = data['Low'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        
        # Pattern: breakdown below support (bearish for CCS)
        breakdown_confirmed = current_low <= support_level * 0.99  # Broke below support by 1%
        bearish_close = current_price < data['Open'].iloc[-1]  # Closed below open
        
        # Volume on breakdown
        avg_volume = data['Volume'].tail(10).mean()
        volume_confirmed = current_volume > avg_volume * 1.3
        
        if breakdown_confirmed and bearish_close:
            strength = 85
            if volume_confirmed: strength += 10
            return True, min(strength, 98)
        
        return False, 0

    def detect_head_and_shoulders(self, data):
        """Head and Shoulders pattern - classic bearish reversal for CCS"""
        if len(data) < 30:
            return False, 0
        
        # Look for three peaks with middle peak being highest
        recent_data = data.tail(25)
        highs = recent_data['High']
        closes = recent_data['Close'] 
        
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
                
                # Neckline is roughly the support level
                neckline = min(recent_data['Low'])
                
                # Check for neckline break (bearish confirmation)
                neckline_broken = current_price < neckline * 1.02
                volume_surge = data['Volume'].iloc[-1] > data['Volume'].tail(10).mean() * 1.4
                
                if neckline_broken:
                    strength = 92
                    if volume_surge: strength += 6
                    return True, min(strength, 98)
        
        return False, 0

    def detect_triple_top(self, data):
        """Triple Top pattern - bearish reversal for CCS"""
        if len(data) < 25:
            return False, 0
        
        recent_data = data.tail(20)
        highs = recent_data['High']
        
        # Find three similar peaks
        peaks = []
        for i in range(2, len(highs)-2):
            if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]):
                peaks.append(highs.iloc[i])
        
        if len(peaks) >= 3:
            # Check if peaks are roughly similar (within 3%)
            max_peak = max(peaks[:3])
            min_peak = min(peaks[:3])
            
            if (max_peak - min_peak) / max_peak <= 0.03:  # Within 3%
                current_price = data['Close'].iloc[-1]
                support_level = recent_data['Low'].min()
                
                # Check for support break (bearish)
                support_broken = current_price < support_level * 1.01
                
                if support_broken:
                    return True, 89
        
        return False, 0

    def detect_double_top(self, data):
        """Double Top pattern - bearish reversal for CCS"""
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
                    return True, 86
        
        return False, 0

    def detect_rising_wedge(self, data):
        """Rising Wedge pattern - bearish reversal for CCS"""
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
        
        breakdown = current_price < recent_low * 1.005  # Small breakdown
        
        if recent_high_trend and recent_low_trend and breakdown:
            return True, 83
        
        return False, 0

    def detect_bear_flag(self, data):
        """Bear Flag pattern - bearish continuation for CCS"""
        if len(data) < 15:
            return False, 0
        
        # Look for prior decline followed by small consolidation
        recent_data = data.tail(10)
        
        # Check for prior bearish move
        price_10_ago = data['Close'].iloc[-11]
        current_price = data['Close'].iloc[-1]
        
        prior_decline = ((current_price - price_10_ago) / price_10_ago) < -0.02  # 2% decline
        
        # Small consolidation (flag)
        consolidation_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Low'].min()
        small_range = consolidation_range < 0.05  # Less than 5% range
        
        # Breakdown from flag
        flag_low = recent_data['Low'].min()
        breakdown = current_price < flag_low * 1.005
        
        if prior_decline and small_range and breakdown:
            return True, 87
        
        return False, 0

    def detect_descending_triangle(self, data):
        """Descending Triangle - bearish continuation for CCS"""
        if len(data) < 20:
            return False, 0
        
        recent_data = data.tail(15)
        
        # Horizontal support with declining resistance
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
            return True, 88
        
        return False, 0

    def detect_evening_star(self, data):
        """Evening Star candlestick pattern - bearish reversal for CCS"""
        if len(data) < 3:
            return False, 0
        
        # Three candle pattern
        candle1 = data.iloc[-3]  # Bullish candle
        candle2 = data.iloc[-2]  # Star (small body)
        candle3 = data.iloc[-1]  # Bearish candle
        
        # First candle: bullish
        bullish_1 = candle1['Close'] > candle1['Open']
        large_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.6
        
        # Second candle: small body (star)
        small_body_2 = abs(candle2['Close'] - candle2['Open']) < (candle2['High'] - candle2['Low']) * 0.3
        gap_up = candle2['Open'] > candle1['Close']
        
        # Third candle: bearish
        bearish_3 = candle3['Close'] < candle3['Open']
        large_body_3 = abs(candle3['Close'] - candle3['Open']) > (candle3['High'] - candle3['Low']) * 0.6
        penetration = candle3['Close'] < (candle1['Open'] + candle1['Close']) / 2
        
        if bullish_1 and large_body_1 and small_body_2 and bearish_3 and large_body_3 and penetration:
            return True, 85
        
        return False, 0

    def detect_dark_cloud_cover(self, data):
        """Dark Cloud Cover pattern - bearish reversal for CCS"""
        if len(data) < 2:
            return False, 0
        
        candle1 = data.iloc[-2]  # Bullish candle
        candle2 = data.iloc[-1]  # Bearish candle
        
        # First candle: strong bullish
        bullish_1 = candle1['Close'] > candle1['Open']
        strong_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.7
        
        # Second candle: bearish with gap up open and deep penetration
        bearish_2 = candle2['Close'] < candle2['Open']
        gap_up_open = candle2['Open'] > candle1['Close']
        deep_penetration = candle2['Close'] < (candle1['Open'] + candle1['Close']) / 2
        
        if bullish_1 and strong_body_1 and bearish_2 and deep_penetration:
            return True, 82
        
        return False, 0

    def detect_hanging_man(self, data):
        """Hanging Man pattern - bearish reversal for CCS"""
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
        
        # Small or no upper shadow
        upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
        small_upper_shadow = upper_shadow < body_size * 0.5
        
        # Should appear after uptrend
        uptrend = data['Close'].iloc[-5] < candle['Close']
        
        if small_body and long_lower_shadow and small_upper_shadow and uptrend:
            return True, 78
        
        return False, 0

    def detect_shooting_star(self, data):
        """Shooting Star pattern - bearish reversal for CCS"""
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
        
        # Small or no lower shadow
        lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
        small_lower_shadow = lower_shadow < body_size * 0.5
        
        # Should appear after uptrend
        uptrend = data['Close'].iloc[-5] < candle['Close']
        
        if small_body and long_upper_shadow and small_lower_shadow and uptrend:
            return True, 81
        
        return False, 0

    def detect_bearish_engulfing(self, data):
        """Bearish Engulfing pattern - bearish reversal for CCS"""
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
            strength = 84
            if volume_increase: strength += 4
            return True, min(strength, 98)
        
        return False, 0

    def _check_pattern_priority(self, pattern_data, pattern_priority):
        """Check if pattern meets the selected priority criteria"""
        if pattern_priority == "All Patterns (Comprehensive)":
            return True
        elif pattern_priority == "High Success Rate Only (>80%)":
            return pattern_data['success_rate'] > 80
        elif pattern_priority == "CCS Optimized (>90% suitability)":
            return pattern_data['ccs_suitability'] > 90
        return True
    
    def _add_weekly_validation_to_pattern(self, pattern_data, daily_strength, data, weekly_data):
        """Helper function to add weekly validation to any pattern"""
        weekly_validation = self.validate_weekly_strength(data, weekly_data, pattern_data['pattern'])
        
        pattern_data['weekly_validation'] = weekly_validation
        pattern_data['total_strength'] = min(98, daily_strength + weekly_validation['weekly_strength_bonus'])
        
        return pattern_data

def get_stock_universe():
    """Get the stock universe based on user selection"""
    try:
        return get_nse_non_fno_stocks()
    except:
        return _get_comprehensive_backup_list()[:219]

def scan_stocks_parallel(stocks, filters, include_weekly=True, max_workers=15):
    """Scan stocks in parallel with progress tracking"""
    
    scanner = ProfessionalCCSScanner()
    all_results = []
    processed_count = 0
    
    def scan_single_stock(symbol):
        """Scan a single stock"""
        try:
            # Get daily data
            daily_data = scanner.get_stock_data(symbol)
            if daily_data is None or len(daily_data) < 30:
                return []
            
            # Get weekly data if requested
            weekly_data = None
            if include_weekly:
                weekly_data = scanner.get_weekly_stock_data(symbol)
            
            # Detect patterns
            patterns = scanner.detect_patterns(daily_data, symbol, filters)
            
            # Add weekly validation to each pattern
            validated_patterns = []
            for pattern in patterns:
                if include_weekly and weekly_data is not None:
                    pattern = scanner._add_weekly_validation_to_pattern(
                        pattern, pattern['daily_strength'], daily_data, weekly_data
                    )
                
                validated_patterns.append(pattern)
            
            return validated_patterns
            
        except Exception as e:
            return []
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_stock = {executor.submit(scan_single_stock, stock): stock for stock in stocks}
        
        # Process completed futures
        for future in as_completed(future_to_stock):
            stock = future_to_stock[future]
            processed_count += 1
            
            try:
                result = future.result(timeout=30)
                if result:
                    all_results.extend(result)
                    
            except Exception as e:
                continue
    
    return all_results

def create_professional_sidebar():
    """Create professional sidebar with Call Credit Spread styling"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 14px; background: linear-gradient(135deg, hsl(0, 62%, 47%), hsl(0, 62%, 40%)); border-radius: 8px; margin-bottom: 14px;'>
            <h2 style='color: #FFFFFF; margin: 0; font-weight: 700; font-size: 1.3rem;'>📉 CCS Scanner V6.2</h2>
            <p style='color: #FFFFFF; margin: 3px 0 0 0; opacity: 0.9; font-size: 0.85rem;'>Professional Red Edition</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Stock Universe Selection - SIMPLIFIED
        st.markdown("### 📊 **Scan Configuration**")
        
        with st.expander("⚙️ **Advanced Settings**", expanded=False):
            
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
            
            # Lookback period
            lookback_days = st.slider(
                "Breakdown Lookback Period (Days)",
                min_value=10,
                max_value=30,
                value=20,
                step=5,
                help="Period to look back for breakdown detection"
            )
            
            # Pattern priority setting
            st.markdown("**Pattern Detection Priority:**")
            pattern_priority = st.radio(
                "Choose detection approach:",
                ["All Patterns (Comprehensive)", "High Success Rate Only (>80%)", "CCS Optimized (>90% suitability)"],
                index=0,
                help="Filter patterns by success rate or CCS suitability"
            )
            
            # NEW V6.1: Separate Daily/Weekly Analysis Options
            st.markdown("**🔍 Timeframe Analysis:**")
            
            analysis_mode = st.radio(
                "Analysis Approach:",
                ["Daily Only (Fast)", "Daily + Weekly Validation (Comprehensive)"],
                index=1,
                help="Choose between fast daily-only scan or comprehensive dual-timeframe analysis"
            )
        
        return {
            'min_strength': min_strength,
            'min_volume_ratio': min_volume_ratio,
            'lookback_days': lookback_days,
            'pattern_priority': pattern_priority,
            'include_weekly': analysis_mode == "Daily + Weekly Validation (Comprehensive)",
            'stocks_to_scan': get_stock_universe()
        }

def create_main_scanner_tab(config):
    """Create the main scanner tab with professional styling"""
    
    # Professional scan controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        scan_button = st.button(
            "🎯 **Start CCS Pattern Scan**", 
            type="primary",
            help="Begin comprehensive Call Credit Spread pattern analysis"
        )
    
    with col2:
        analysis_type = "Weekly Enhanced" if config['include_weekly'] else "Daily Only"
        st.markdown(f"**Mode:** {analysis_type}")
    
    with col3:
        st.markdown(f"**Scanning: {len(config['stocks_to_scan'])} stocks**")
    
    if scan_button:
        scanner = ProfessionalCCSScanner()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_container = st.empty()
        
        start_time = time.time()
        
        # Create filters dictionary
        filters = {
            'min_strength': config['min_strength'],
            'volume_ratio': config['min_volume_ratio'],
            'lookback_days': config['lookback_days'],
            'min_volume_ratio': config['min_volume_ratio']
        }
        
        status_container.info(f"🔄 Initializing scan of {len(config['stocks_to_scan'])} stocks...")
        progress_bar.progress(5)
        
        # Perform parallel scanning
        try:
            results = scan_stocks_parallel(
                config['stocks_to_scan'], 
                filters,
                include_weekly=config['include_weekly'],
                max_workers=15
            )
            
            progress_bar.progress(90)
            status_container.info("🔄 Processing results...")
            
            # Filter results by pattern priority
            filtered_results = []
            for result in results:
                pattern_data = scanner._get_pattern_data(result['pattern'], None)
                if scanner._check_pattern_priority(pattern_data, config['pattern_priority']):
                    filtered_results.append(result)
            
            # Sort by total strength (including weekly bonus if available)
            filtered_results.sort(
                key=lambda x: x.get('total_strength', x['strength']), 
                reverse=True
            )
            
            progress_bar.progress(100)
            end_time = time.time()
            scan_duration = end_time - start_time
            
            status_container.success(f"✅ Scan completed in {scan_duration:.1f} seconds. Found {len(filtered_results)} opportunities!")
            
            if filtered_results:
                
                # Summary metrics
                st.markdown("### 📈 **Scan Results Summary**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Opportunities", len(filtered_results))
                
                with col2:
                    high_strength = sum(1 for r in filtered_results if r.get('total_strength', r['strength']) >= 85)
                    st.metric("High Strength (>85%)", high_strength)
                
                with col3:
                    breakdown_confirmed = sum(1 for r in filtered_results if r.get('breakdown_confirmed', False))
                    st.metric("Breakdown Confirmed", breakdown_confirmed)
                
                with col4:
                    avg_strength = sum(r.get('total_strength', r['strength']) for r in filtered_results) / len(filtered_results)
                    st.metric("Avg Strength", f"{avg_strength:.1f}%")
                
                # Create tabs for different views
                result_tab1, result_tab2, result_tab3 = st.tabs([
                    "🎯 **Top Opportunities**",
                    "📊 **Detailed Analysis**", 
                    "📱 **Export Results**"
                ])
                
                with result_tab1:
                    st.markdown("### 🎯 **Premium CCS Opportunities**")
                    
                    # Show top 10 results with enhanced cards
                    top_results = filtered_results[:10]
                    
                    for i, pattern in enumerate(top_results, 1):
                        # Determine if weekly validation is available
                        has_weekly = 'weekly_validation' in pattern
                        weekly_val = pattern.get('weekly_validation', {})
                        
                        # Create enhanced pattern card
                        strength_color = "#dc2626" if pattern.get('total_strength', pattern['strength']) >= 90 else "#ea580c" if pattern.get('total_strength', pattern['strength']) >= 80 else "#ca8a04"
                        breakdown_status = "✅ Confirmed" if pattern.get('breakdown_confirmed', False) else "⏳ Pending"
                        volume_status = "🔊 Strong" if pattern.get('volume_ratio', 0) >= 2.0 else "📈 Moderate"
                        
                        # Get pattern details for display
                        details = pattern.get('breakdown_details', {})
                        
                        # Weekly validation info
                        weekly_info = ""
                        if has_weekly and weekly_val.get('weekly_confirmed', False):
                            weekly_info = f"""
                            <div style='background: #fef3c7; border-left: 4px solid #f59e0b; padding: 8px; margin: 8px 0; border-radius: 4px;'>
                                <strong>📅 Weekly Validation:</strong> {weekly_val.get('weekly_trend', 'Unknown')} trend, RSI: {weekly_val.get('weekly_rsi', 'N/A')}
                            </div>
                            """
                        
                        st.markdown(f"""
                        <div style='background: white; border: 2px solid #e5e7eb; border-radius: 12px; padding: 20px; margin: 16px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                            <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>
                                <h3 style='margin: 0; color: #dc2626; font-size: 1.4rem;'>#{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']}</h3>
                                <span style='background: {strength_color}; color: white; padding: 6px 12px; border-radius: 20px; font-weight: bold; font-size: 0.9rem;'>
                                    {pattern.get('total_strength', pattern['strength']):.0f}%
                                </span>
                            </div>
                            
                            <div style='display: flex; justify-content: space-between; margin: 8px 0; color: #4b5563;'>
                                <span><strong>Current Price:</strong> ₹{pattern['current_price']:.2f}</span>
                                <span><strong>Breakdown:</strong> {breakdown_status}</span>
                                <span><strong>Volume:</strong> {volume_status}</span>
                            </div>
                            
                            <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; margin: 12px 0;'>
                                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>Daily Strength</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: #dc2626;'>{pattern.get('daily_strength', pattern['strength'])}%</div>
                                </div>
                                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>Success Rate</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: #16a34a;'>{pattern['success_rate']}%</div>
                                </div>
                                <div style='text-align: center; padding: 8px; background: #f9fafb; border-radius: 8px;'>
                                    <div style='font-size: 0.85rem; color: #6b7280;'>CCS Fit</div>
                                    <div style='font-size: 1.1rem; font-weight: bold; color: #dc2626;'>{pattern['ccs_suitability']}%</div>
                                </div>
                            </div>
                            
                            {weekly_info}
                            
                        </div>
                        """, unsafe_allow_html=True)
                
                with result_tab2:
                    st.markdown("### 📊 **Complete Analysis Results**")
                    
                    # Show all results with weekly validation details
                    for i, pattern in enumerate(filtered_results, 1):
                        
                        with st.expander(f"#{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']} ({pattern.get('total_strength', pattern['strength']):.0f}%)", expanded=i<=3):
                            
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.markdown("#### Pattern Details")
                                st.write(f"**Pattern:** {pattern['pattern']}")
                                st.write(f"**Current Price:** ₹{pattern['current_price']:.2f}")
                                st.write(f"**Pattern Strength:** {pattern['strength']}%")
                                st.write(f"**Success Rate:** {pattern['success_rate']}%")
                                st.write(f"**CCS Suitability:** {pattern['ccs_suitability']}%")
                                
                                # Breakdown details
                                details = pattern.get('breakdown_details', {})
                                if details:
                                    st.markdown("#### Breakdown Analysis")
                                    st.write(f"**Breakdown Confirmed:** {'✅ Yes' if details.get('breakdown_occurred', False) else '❌ No'}")
                                    st.write(f"**Volume Confirmed:** {'✅ Yes' if details.get('volume_confirmed', False) else '❌ No'}")
                                    st.write(f"**Breakdown %:** {details.get('breakdown_percentage', 0):.2f}%")
                                    st.write(f"**Volume Ratio:** {details.get('volume_ratio', 0):.1f}x")
                                    st.write(f"**Close Strength:** {details.get('close_strength', 0):.0f}%")
                            
                            with col2:
                                # Weekly validation details
                                if 'weekly_validation' in pattern:
                                    weekly_val = pattern['weekly_validation']
                                    st.markdown("#### Weekly Validation")
                                    st.write(f"**Weekly Confirmed:** {'✅ Yes' if weekly_val.get('weekly_confirmed', False) else '❌ No'}")
                                    st.write(f"**Weekly Trend:** {weekly_val.get('weekly_trend', 'Unknown')}")
                                    st.write(f"**Weekly RSI:** {weekly_val.get('weekly_rsi', 'Unknown')}")
                                    st.write(f"**Weekly Bonus:** +{weekly_val.get('weekly_strength_bonus', 0)}%")
                                    
                                    if weekly_val.get('weekly_confirmed', False):
                                        st.success("Weekly timeframe confirms the pattern!")
                                    else:
                                        st.warning("Weekly timeframe shows mixed signals")
                                else:
                                    st.info("Weekly analysis not performed for this scan")
                
                with result_tab3:
                    st.markdown("### 📱 **Export & Share Results**")
                    
                    # Create Excel export
                    excel_data = create_excel_stock_list(filtered_results)
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.download_button(
                            label="📊 **Download Excel Report**",
                            data=excel_data,
                            file_name=f"CCS_Opportunities_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    
                    with col2:
                        # Summary statistics
                        pattern_summary = {}
                        for result in filtered_results:
                            pattern = result['pattern']
                            pattern_summary[pattern] = pattern_summary.get(pattern, 0) + 1
                        
                        st.markdown("**Pattern Distribution:**")
                        for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"• {pattern}: {count}")
            
            else:
                st.warning("🔍 No patterns found matching your criteria. Try adjusting the filters for broader results.")
                
                # Suggestions for no results
                st.markdown("""
                ### 💡 **Suggestions:**
                - Lower the minimum strength threshold
                - Reduce the minimum volume ratio requirement  
                - Choose "All Patterns" for comprehensive detection
                - Market conditions might not be favorable for Call Credit Spreads
                """)
        
        except Exception as e:
            st.error(f"❌ Scanning error: {str(e)}")
            progress_bar.empty()
            status_container.empty()

def main():
    # FIXED: Call Credit Spread Style Compact Header
    st.markdown("""
    <div class="professional-header">
        <h1>📉 NSE F&O CCS Scanner</h1>
        <p class="subtitle">Current Day EOD Analysis • Complete 219 Stock Universe • Call Credit Spread Style</p>
        <p class="description">Real-time Pattern Confirmation with Latest Trading Day Data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create sidebar configuration
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
        scanner = ProfessionalCCSScanner()
        sentiment_data = scanner.get_market_sentiment_indicators()
        
        # Market Overview
        col1, col2, col3 = st.columns(3)
        
        overall_sentiment = sentiment_data.get('overall', {})
        
        with col1:
            sentiment_level = overall_sentiment.get('sentiment', 'NEUTRAL')
            sentiment_emoji = "🔴" if sentiment_level == 'BEARISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🟢"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>{sentiment_emoji} Market Sentiment</h3>
                <h2 style="color: var(--primary-red);">{sentiment_level}</h2>
                <p>{overall_sentiment.get('ccs_recommendation', 'Moderate opportunities')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            risk_level = overall_sentiment.get('risk_level', 'MEDIUM')
            risk_color = "var(--primary-green)" if risk_level == 'LOW' else "var(--primary-orange)" if risk_level == 'MEDIUM' else "var(--primary-red)"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚠️ Risk Level</h3>
                <h2 style="color: {risk_color};">{risk_level}</h2>
                <p>Current CCS risk assessment</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            ist = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist)
            is_trading_day = current_time.weekday() < 5  # Monday=0, Friday=4
            trading_status = "🟢 Active" if is_trading_day and 9 <= current_time.hour <= 15 else "🔴 Closed"
            
            st.markdown(f"""
            <div class="metric-card">
                <h3>🕐 Market Status</h3>
                <h2 style="color: var(--primary-blue);">{trading_status}</h2>
                <p>{current_time.strftime('%I:%M %p IST')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Detailed sentiment breakdown
        st.markdown("### 📈 **Detailed Market Analysis**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'nifty' in sentiment_data:
                nifty_data = sentiment_data['nifty']
                st.markdown(f"""
                **🎯 Nifty 50 Analysis**
                - **Current Level:** {nifty_data['level']:.2f}
                - **Daily Change:** {nifty_data['change_pct']:.2f}%
                - **Sentiment:** {nifty_data['sentiment']}
                """)
        
        with col2:
            if 'bank_nifty' in sentiment_data:
                bank_data = sentiment_data['bank_nifty']
                st.markdown(f"""
                **🏦 Bank Nifty Analysis**
                - **Current Level:** {bank_data['level']:.2f}
                - **Daily Change:** {bank_data['change_pct']:.2f}%
                - **Sentiment:** {bank_data['sentiment']}
                """)
        
        # CCS Strategy recommendations based on sentiment
        st.markdown("### 📋 **CCS Strategy Recommendations**")
        
        ccs_recommendation = overall_sentiment.get('ccs_recommendation', 'Moderate opportunities')
        
        if "Excellent" in ccs_recommendation:
            st.success(f"✅ **{ccs_recommendation}** - Bearish market conditions favor Call Credit Spreads")
            st.markdown("""
            **Recommended Actions:**
            - Focus on high-probability bearish reversal patterns
            - Consider out-of-the-money call spreads
            - Target stocks showing weakness with high implied volatility
            - Look for stocks at or near resistance levels
            """)
        elif "Moderate" in ccs_recommendation:
            st.warning(f"⚠️ **{ccs_recommendation}** - Mixed market conditions require selective approach")
            st.markdown("""
            **Recommended Actions:**
            - Be selective with pattern quality (>85% strength)
            - Ensure weekly timeframe confirmation
            - Consider tighter strike selections
            - Monitor for breakdown confirmations before entry
            """)
        else:
            st.error(f"❌ **{ccs_recommendation}** - Market conditions not favorable for CCS")
            st.markdown("""
            **Recommended Actions:**
            - Avoid new CCS positions
            - Consider Put Credit Spreads instead
            - Wait for market sentiment to shift bearish
            - Focus on risk management of existing positions
            """)

if __name__ == "__main__":
    main()
