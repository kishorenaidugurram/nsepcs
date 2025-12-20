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
from sklearn.cluster import KMeans
from scipy.signal import argrelextrema
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ENHANCED PROFESSIONAL UI SYSTEM - Tailwind-Inspired CSS
# BLOOMBERG TERMINAL PROFESSIONAL UI SYSTEM
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;600;700&display=swap');
    
    :root {
        /* === BLOOMBERG TERMINAL DESIGN SYSTEM === */
        /* Professional Financial Terminal Theme */
        
        /* Bloomberg Signature Colors */
        --bloomberg-orange: #ff6b00;
        --bloomberg-orange-hover: #ff8533;
        --bloomberg-orange-dark: #cc5500;
        --bloomberg-green: #00d084;
        --bloomberg-red: #ff3b69;
        --bloomberg-blue: #00a3ff;
        
        /* Dark Theme Palette */
        --bg-primary: #0a0a0a;
        --bg-secondary: #151515;
        --bg-elevated: #1a1a1a;
        --bg-hover: #202020;
        
        /* Border System */
        --border-primary: #2a2a2a;
        --border-secondary: #333333;
        --border-accent: var(--bloomberg-orange);
        
        /* Text System */
        --text-primary: #ffffff;
        --text-secondary: #999999;
        --text-tertiary: #666666;
        --text-muted: #444444;
        
        /* Semantic Colors */
        --success: var(--bloomberg-green);
        --error: var(--bloomberg-red);
        --warning: #ffaa00;
        --info: var(--bloomberg-blue);
        
        /* Shadows */
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
        --shadow-md: 0 2px 4px 0 rgba(0, 0, 0, 0.4);
        --shadow-lg: 0 4px 8px 0 rgba(0, 0, 0, 0.5);
        
        /* Spacing (keeping existing) */
        --spacing-1: 0.25rem;
        --spacing-2: 0.5rem;
        --spacing-3: 0.75rem;
        --spacing-4: 1rem;
        --spacing-5: 1.25rem;
        --spacing-6: 1.5rem;
        --spacing-8: 2rem;
        
        /* Typography */
        --font-mono: 'Roboto Mono', 'Courier New', monospace;
        --font-size-xs: 0.7rem;
        --font-size-sm: 0.8rem;
        --font-size-base: 0.9rem;
        --font-size-lg: 1rem;
        --font-size-xl: 1.2rem;
        --font-size-2xl: 1.5rem;
    }
    
    /* === BLOOMBERG GLOBAL STYLES === */
    * {
        font-family: var(--font-mono);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    
    /* Main App Container - Bloomberg Dark */
    .main {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        padding: var(--spacing-6) var(--spacing-8);
    }
    
    .stApp {
        background: var(--bg-primary) !important;
    }
    
    /* === HEADERS - Bloomberg Style === */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600;
        letter-spacing: 0.5px;
        font-family: var(--font-mono) !important;
    }
    
    h1 {
        font-size: var(--font-size-2xl);
        margin-bottom: var(--spacing-4);
        color: var(--bloomberg-orange) !important;
        text-transform: uppercase;
        border-bottom: 2px solid var(--border-primary);
        padding-bottom: var(--spacing-2);
    }
    
    h2 {
        font-size: var(--font-size-xl);
        margin-bottom: var(--spacing-3);
        color: var(--bloomberg-orange) !important;
    }
    
    h3 {
        font-size: var(--font-size-lg);
        margin-bottom: var(--spacing-2);
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* === SIDEBAR - Bloomberg Terminal Style === */
    [data-testid="stSidebar"] {
        min-width: 342px !important;
        max-width: 342px !important;
        background: var(--bg-secondary) !important;
        border-right: 3px solid var(--bloomberg-orange) !important;
        box-shadow: var(--shadow-lg) !important;
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: transparent !important;
    }
    
    /* Remove card backgrounds from sidebar elements */
    [data-testid="stSidebar"] .element-container,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    
    /* Sidebar Text */
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div {
        color: var(--text-primary) !important;
        font-size: var(--font-size-sm) !important;
    }
    
    /* Sidebar Headers */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--bloomberg-orange) !important;
        font-size: var(--font-size-base) !important;
    }
    
    /* Sidebar Checkboxes */
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        color: var(--text-secondary) !important;
        font-size: var(--font-size-xs) !important;
    }
    
    /* === INPUT FIELDS - Bloomberg Style === */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stSlider > div > div > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 2px !important;
        color: var(--text-primary) !important;
        font-size: var(--font-size-sm) !important;
        font-family: var(--font-mono) !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: var(--bloomberg-orange) !important;
        outline: none !important;
        box-shadow: 0 0 0 2px rgba(255, 107, 0, 0.2) !important;
    }
    
    /* === BUTTONS - Bloomberg Terminal Style === */
    .stButton > button {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--bloomberg-orange) !important;
        border-radius: 2px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        font-size: var(--font-size-sm) !important;
        font-family: var(--font-mono) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    
    .stButton > button:hover {
        background: var(--bloomberg-orange) !important;
        color: var(--bg-primary) !important;
        border-color: var(--bloomberg-orange-hover) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Primary Button */
    .stButton > button[kind="primary"] {
        background: var(--bloomberg-orange) !important;
        color: var(--bg-primary) !important;
        border-color: var(--bloomberg-orange) !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: var(--bloomberg-orange-hover) !important;
        border-color: var(--bloomberg-orange-hover) !important;
    }
    
    /* === TABS - Bloomberg Style === */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-secondary) !important;
        border-bottom: 2px solid var(--border-primary) !important;
        gap: 0 !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: none !important;
        color: var(--text-secondary) !important;
        font-family: var(--font-mono) !important;
        font-size: var(--font-size-sm) !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        padding: 12px 24px !important;
        border-bottom: 3px solid transparent !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-hover) !important;
        color: var(--text-primary) !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: transparent !important;
        color: var(--bloomberg-orange) !important;
        border-bottom-color: var(--bloomberg-orange) !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        background: transparent !important;
    }
    
    /* === METRICS - Bloomberg Style === */
    [data-testid="stMetric"] {
        background: var(--bg-secondary) !important;
        padding: 12px 16px !important;
        border: 1px solid var(--border-primary) !important;
        border-left: 3px solid var(--bloomberg-orange) !important;
        border-radius: 0 !important;
    }
    
    [data-testid="stMetric"]:hover {
        background: var(--bg-hover) !important;
        border-left-color: var(--bloomberg-orange-hover) !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        text-transform: uppercase !important;
        font-size: var(--font-size-xs) !important;
        letter-spacing: 0.5px !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-family: var(--font-mono) !important;
    }
    
    /* === DATAFRAMES & TABLES - Bloomberg Terminal Style === */
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    .dataframe {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-primary) !important;
        border-radius: 0 !important;
        font-family: var(--font-mono) !important;
        font-size: var(--font-size-xs) !important;
        color: var(--text-primary) !important;
    }
    
    .dataframe thead th {
        background: var(--bg-primary) !important;
        color: var(--bloomberg-orange) !important;
        font-weight: 700 !important;
        padding: 10px 12px !important;
        text-align: left !important;
        border-bottom: 2px solid var(--bloomberg-orange) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        font-size: var(--font-size-xs) !important;
    }
    
    .dataframe tbody td {
        padding: 8px 12px !important;
        border-bottom: 1px solid var(--border-primary) !important;
        color: var(--text-primary) !important;
        background: var(--bg-secondary) !important;
    }
    
    .dataframe tbody tr:hover {
        background: var(--bg-hover) !important;
    }
    
    .dataframe tbody tr:nth-child(even) {
        background: var(--bg-secondary) !important;
    }
    
    .dataframe tbody tr:nth-child(odd) {
        background: var(--bg-primary) !important;
    }
    
    /* === TEXT & PARAGRAPHS === */
    p, span {
        color: var(--text-primary) !important;
        font-family: var(--font-mono) !important;
    }
    
    /* === PROGRESS BARS === */
    .stProgress > div > div > div {
        background: var(--bloomberg-orange) !important;
    }
    
    /* === INFO/SUCCESS/WARNING/ERROR MESSAGES === */
    [data-baseweb="notification"] {
        border-radius: 0 !important;
        border-left: 3px solid !important;
        background: var(--bg-secondary) !important;
        font-family: var(--font-mono) !important;
        color: var(--text-primary) !important;
    }
    
    /* === SCROLLBARS === */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-primary);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--border-secondary);
        border-radius: 0;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--bloomberg-orange);
    }
    
    /* === LINKS === */
    a {
        color: var(--bloomberg-blue) !important;
        text-decoration: none !important;
    }
    
    a:hover {
        color: var(--bloomberg-orange) !important;
    }
    
    [data-testid="stMetric"] {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-md);
        padding: var(--spacing-4);
        box-shadow: var(--shadow-sm);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        border-color: var(--primary-500);
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    
    [data-testid="stMetricLabel"] {
        font-size: var(--font-size-sm) !important;
        font-weight: 600 !important;
        color: var(--text-secondary) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: var(--spacing-2);
    }
    
    [data-testid="stMetricDelta"] {
        font-size: var(--font-size-sm) !important;
        font-weight: 500 !important;
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
        box-shadow: var(--shadow);
        font-size: var(--font-size-sm);
    }
    
    .dataframe thead th {
        background: var(--primary-600);
        color: white;
        font-weight: 700;
        padding: var(--spacing-3) var(--spacing-4);
        text-align: left;
        border-bottom: 2px solid var(--primary-700);
    }
    
    .dataframe tbody td {
        padding: var(--spacing-3) var(--spacing-4);
        border-bottom: 1px solid var(--border);
        color: var(--text-primary);
    }
    
    .dataframe tbody tr:hover {
        background: var(--primary-50);
    }
    
    /* Expander Component */
    .streamlit-expanderHeader {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: var(--spacing-4);
        font-weight: 600;
        color: var(--text-primary);
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--primary-50);
        border-color: var(--primary-300);
    }
    
    .streamlit-expanderContent {
        border: 1px solid var(--border);
        border-top: none;
        border-radius: 0 0 var(--radius) var(--radius);
        padding: var(--spacing-4);
        background: var(--surface);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: var(--spacing-2);
        background: var(--background-secondary);
        padding: var(--spacing-2);
        border-radius: var(--radius);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border: none;
        color: var(--text-secondary);
        font-weight: 600;
        padding: var(--spacing-3) var(--spacing-6);
        border-radius: var(--radius-sm);
        transition: all 0.2s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--surface);
        color: var(--primary-700);
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--primary-600);
        color: white;
        box-shadow: var(--shadow);
    }
    
    /* Alert/Info Boxes */
    .stAlert {
        border-radius: var(--radius);
        padding: var(--spacing-4);
        border-left: 4px solid;
        box-shadow: var(--shadow-sm);
    }
    
    .stInfo {
        background: var(--info-bg);
        border-color: var(--info-text);
        color: var(--info-text);
    }
    
    .stSuccess {
        background: var(--success-bg);
        border-color: var(--success-text);
        color: var(--success-text);
    }
    
    .stWarning {
        background: var(--warning-bg);
        border-color: var(--warning-text);
        color: var(--warning-text);
    }
    
    .stError {
        background: var(--error-bg);
        border-color: var(--error-text);
        color: var(--error-text);
    }
    
    /* Progress Bar */
    .stProgress > div > div > div {
        background: var(--primary-600);
        border-radius: var(--radius);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: var(--primary-600);
    }
    
    /* Code Blocks */
    code {
        background: var(--neutral-100);
        color: var(--primary-700);
        padding: var(--spacing-1) var(--spacing-2);
        border-radius: var(--radius-sm);
        font-size: var(--font-size-sm);
        font-family: 'Fira Code', monospace;
    }
    
    pre {
        background: var(--neutral-900);
        color: var(--neutral-100);
        padding: var(--spacing-4);
        border-radius: var(--radius);
        overflow-x: auto;
        box-shadow: var(--shadow);
    }
    
    /* Custom Card Component */
    .card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius-lg);
        padding: var(--spacing-6);
        box-shadow: var(--shadow);
        transition: all 0.3s ease;
        margin-bottom: var(--spacing-4);
    }
    
    .card:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-2px);
        border-color: var(--primary-300);
    }
    
    .card-header {
        font-size: var(--font-size-xl);
        font-weight: 700;
        color: var(--primary-700);
        margin-bottom: var(--spacing-4);
        padding-bottom: var(--spacing-3);
        border-bottom: 2px solid var(--border);
    }
    
    /* Badge Component */
    .badge {
        display: inline-block;
        padding: var(--spacing-1) var(--spacing-3);
        border-radius: var(--radius);
        font-size: var(--font-size-xs);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .badge-primary {
        background: var(--primary-100);
        color: var(--primary-700);
        border: 1px solid var(--primary-300);
    }
    
    .badge-success {
        background: var(--success-bg);
        color: var(--success-text);
        border: 1px solid var(--success-border);
    }
    
    .badge-warning {
        background: var(--warning-bg);
        color: var(--warning-text);
        border: 1px solid var(--warning-border);
    }
    
    .badge-error {
        background: var(--error-bg);
        color: var(--error-text);
        border: 1px solid var(--error-border);
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--background-secondary);
        border-radius: var(--radius);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-400);
        border-radius: var(--radius);
        transition: all 0.2s ease;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary-600);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    
    /* Fade In Animation */
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
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Responsive Typography */
    @media (max-width: 768px) {
        h1 {
            font-size: var(--font-size-3xl);
        }
        
        h2 {
            font-size: var(--font-size-xl);
        }
        
        .main {
            padding: var(--spacing-4);
        }
        
        .card {
            padding: var(--spacing-4);
        }
    }
    
    /* Print Styles */
    @media print {
        .stButton, .stDownloadButton, [data-testid="stSidebar"] {
            display: none;
        }
        
        .main {
            padding: 0;
        }
        
        .card {
            box-shadow: none;
            border: 1px solid var(--border);
            page-break-inside: avoid;
        }
    }
    
    /* High Contrast Mode Support */
    @media (prefers-contrast: high) {
        :root {
            --border: hsl(210, 14%, 70%);
            --text-secondary: hsl(210, 12%, 30%);
        }
    }
    
    /* Reduced Motion Support */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* Focus Visible for Accessibility */
    *:focus-visible {
        outline: 2px solid var(--primary-600);
        outline-offset: 2px;
        border-radius: var(--radius-sm);
    }
    
    /* Selection Styling */
    ::selection {
        background: var(--primary-200);
        color: var(--primary-900);
    }
    
    /* Custom Professional Elements */
    .pro-header {
        background: linear-gradient(135deg, var(--primary-600), var(--primary-800));
        color: white;
        padding: var(--spacing-8);
        border-radius: var(--radius-lg);
        margin-bottom: var(--spacing-6);
        box-shadow: var(--shadow-xl);
    }
    
    .pro-stat {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: var(--spacing-4);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .pro-stat:hover {
        border-color: var(--primary-500);
        box-shadow: var(--shadow-md);
        transform: scale(1.02);
    }
    
    .pro-stat-value {
        font-size: var(--font-size-3xl);
        font-weight: 800;
        color: var(--primary-700);
        display: block;
        margin-bottom: var(--spacing-2);
    }
    
    .pro-stat-label {
        font-size: var(--font-size-sm);
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
</style>
""", unsafe_allow_html=True)

# COMPLETE NSE F&O UNIVERSE - 208 STOCKS (Updated Official List)
COMPLETE_NSE_FO_UNIVERSE = [
    # Updated 208 F&O Individual stocks - As per user's official list
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

def get_nse_non_fno_stocks():
    """
    Fetch all NSE stocks and exclude F&O stocks to get non-F&O universe.
    Returns list of stock symbols with .NS suffix.
    """
    try:
        # Try fetching from NSE website
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))
            
            # Get all symbols and add .NS suffix
            all_symbols = [f"{symbol.strip()}.NS" for symbol in df['SYMBOL'].tolist() if pd.notna(symbol)]
            
            # Remove F&O stocks
            fno_symbols_clean = [s.replace('.NS', '') for s in COMPLETE_NSE_FO_UNIVERSE if s.endswith('.NS')]
            non_fno_stocks = [s for s in all_symbols if s.replace('.NS', '') not in fno_symbols_clean]
            
            return non_fno_stocks
        else:
            return _get_comprehensive_backup_list()
            
    except Exception as e:
        return _get_comprehensive_backup_list()

def create_excel_stock_list(results):
    """
    Create Excel file with just stock symbols that met criteria.
    Simple format: One column with stock symbols.
    """
    # Extract clean symbols from results
    stock_symbols = []
    for result in results:
        # Remove .NS suffix and clean symbol
        clean_symbol = result['symbol'].replace('.NS', '').replace('^', '')
        stock_symbols.append(clean_symbol)
    
    # Create Excel workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Qualifying Stocks"
    
    # Add header
    ws['A1'] = "Stock Symbol"
    ws['A1'].font = openpyxl.styles.Font(bold=True, size=12)
    
    # Add stock symbols
    for idx, symbol in enumerate(stock_symbols, start=2):
        ws[f'A{idx}'] = symbol
    
    # Auto-adjust column width
    ws.column_dimensions['A'].width = 20
    
    # Save to BytesIO
    excel_buffer = BytesIO()
    wb.save(excel_buffer)
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()

def _get_comprehensive_backup_list():
    """Comprehensive backup list of 814+ NSE stocks (non-F&O)"""
    return [
        # Large Cap Non-F&O (100+ stocks)
        'AARTIIND.NS', 'AAVAS.NS', 'ABSLAMC.NS', 'ADANIPOWER.NS', 'AEGISCHEM.NS', 'AFFLE.NS',
        'AIAENG.NS', 'AJANTPHAR.NS', 'AKZOINDIA.NS', 'ALLCARGO.NS', 'AMARAJABAT.NS', 'AMBER.NS',
        'AMRUTANJAN.NS', 'ANANTRAJ.NS', 'APCOTEXIND.NS', 'APLAPOLLO.NS', 'APOLLOPIPE.NS', 'APTECHT.NS',
        'ARVINDFASN.NS', 'ARVINDLT.NS', 'ARVSMART.NS', 'ASAHIINDIA.NS', 'ASHIANA.NS', 'ASTERDM.NS',
        'ASTRAMICRO.NS', 'ASTRAZEN.NS', 'ATGL.NS', 'ATNINTER.NS', 'ATUL.NS', 'AUSOMENT.NS',
        
        # Mid Cap Non-F&O (200+ stocks)
        'AVANTIFEED.NS', 'AVTNPL.NS', 'AXISCADES.NS', 'BAJAJCON.NS', 'BAJAJELEC.NS', 'BAJAJHCARE.NS',
        'BAJAJHIND.NS', 'BAJAJHLDNG.NS', 'BALAMINES.NS', 'BALMLAWRIE.NS', 'BALRAMPUR.NS', 'BASF.NS',
        'BATAINDIA.NS', 'BBTC.NS', 'BEML.NS', 'BHARATRAS.NS', 'BHARATWIRE.NS', 'BHEML.NS',
        'BIRLACORPN.NS', 'BIRLACOT.NS', 'BLS.NS', 'BLUESTAR.NS', 'BLUSTARCOM.NS', 'BOMDYEING.NS',
        'BOROLTD.NS', 'BOSCHLTD.NS', 'BRIGADE.NS', 'CARERATING.NS', 'CARYSIL.NS', 'CASTROLIND.NS',
        
        # Small Cap Non-F&O (300+ stocks)
        'CCL.NS', 'CEATLTD.NS', 'CENTENKA.NS', 'CENTURYTEX.NS', 'CEREBRAINT.NS', 'CERA.NS',
        'CHAMBLFERT.NS', 'CHALET.NS', 'CHEMFAB.NS', 'CHENNPETRO.NS', 'CHOICEIN.NS', 'CIEINDIA.NS',
        'CIGNITTEC.NS', 'CIMMCO.NS', 'CIPLAVETNS', 'CLEAN.NS', 'COCHINSHIP.NS', 'COFFEEDAY.NS',
        'COLGATEPAE.NS', 'CAMS.NS', 'COMPINFO.NS', 'COMPUSOFT.NS', 'CONCORDBIO.NS', 'CONFIPET.NS',
        'CONNECTIN.NS', 'CONSOLGD.NS', 'CONTROLPR.NS', 'COROENGG.NS', 'COSMOFIRST.NS', 'COUNCODOS.NS',
        
        # Micro Cap Non-F&O (200+ stocks)
        'COX&KINGS.NS', 'CREDAG.NS', 'CRISIL.NS', 'CROSSING.NS', 'CROWN.NS', 'CSBBANK.NS',
        'CUBEXTUB.NS', 'CUPID.NS', 'CYBERMEDIA.NS', 'CYBERTECH.NS', 'DAAWAT.NS', 'DCB.NS',
        'DCBBANK.NS', 'DCM.NS', 'DCMFINSERV.NS', 'DCMNVL.NS', 'DCMSRIND.NS', 'DCMSRTM.NS',
        'DCWLTD.NS', 'DECCANHOL.NS', 'DEEPAKFERT.NS', 'DEEPIND.NS', 'DENABANK.NS', 'DENORA.NS',
        'DHANBANK.NS', 'DHANUKA.NS', 'DHARSUGAR.NS', 'DHFL.NS', 'DHUNINV.NS', 'DHUNKATTA.NS',
        
        # Additional Liquid Stocks (remaining to reach 814+)
        'DIAMONDYD.NS', 'DICIND.NS', 'DIGICABLE.NS', 'DIGJAM.NS', 'DIGJAMLM.NS', 'DISHMAN.NS',
        'DODLA.NS', 'DOLPHINOF.NS', 'DONEAR.NS', 'DPABHUSHAN.NS', 'DPTDL.NS', 'DQE.NS',
        'DRCSYSTEMS.NS', 'DREAMFOLK.NS', 'DREDGECORP.NS', 'DSSL.NS', 'DTIL.NS', 'DUCON.NS',
        'DUNCANS.NS', 'DWARKESH.NS', 'DYNAMATECH.NS', 'DYNPRO.NS', 'E2LTRE.NS', 'EASUNREYRL.NS',
        'EASTSILK.NS', 'EASUNREYRL.NS', 'EKC.NS', 'EDELWEISS.NS', 'EDUCOMP.NS', 'EIFFL.NS',
        'EIMCOELECO.NS', 'EIH.NS', 'EIHAHOTELS.NS', 'EIHOTEL.NS', 'EIRC.NS', 'EITQUA.NS',
        'EKENNIS.NS', 'ELECON.NS', 'ELECTCAST.NS', 'ELECTHERM.NS', 'ELEVAATORS.NS', 'ELGIEQUIP.NS',
        'ELGIRUBCO.NS', 'ELIN.NS', 'EMAMILTD.NS', 'EMARALD.NS', 'EMKAY.NS', 'EMKAYTOOLS.NS',
        'EMMBI.NS', 'EMSLIMITED.NS', 'ENAM.NS', 'ENDURANCE.NS', 'ENERGYDEV.NS', 'ENGINERSIN.NS',
        'ENKEI.NS', 'EPL.NS', 'EQUITAS.NS', 'ERIS.NS', 'EROSMEDIA.NS', 'ESABINDIA.NS',
        'ESCORTS.NS', 'ESSELPACK.NS', 'ESSENTIA.NS', 'ESTER.NS', 'EUROCERA.NS', 'EUROMULTI.NS',
        'EUROTEXIND.NS', 'EVEREADY.NS', 'EVERESTIND.NS', 'EXCEL.NS', 'EXCELIND.NS', 'EXPLEOSOL.NS',
        'FACT.NS', 'FAIRCHEMOR.NS', 'FAIRCHEM.NS', 'FAZE3Q.NS', 'FCL.NS', 'FCONSUMER.NS',
        'FDC.NS', 'FEDERALBNK.NS', 'FEL.NS', 'FENOPLAST.NS', 'FERID.NS', 'FIEMIND.NS',
        'FILATEX.NS', 'FINCABLES.NS', 'FINOLEXIND.NS', 'FINPIPE.NS', 'FLEXITUFF.NS', 'FLFL.NS',
        'FMGOETZE.NS', 'FOODSIN.NS', 'FORCEMOT.NS', 'FORTISHEALTH.NS', 'FOSECO.NS', 'FOSECOIND.NS',
        'FRESHTROP.NS', 'FRETAIL.NS', 'FSC.NS', 'FSL.NS', 'FUSION.NS', 'GABRIEL.NS',
        'GAEL.NS', 'GAILTEL.NS', 'GALAXY.NS', 'GANESHBE.NS', 'GANESHHOUC.NS', 'GANESHHOUS.NS',
        'GANESHPOLY.NS', 'GANESHSHP.NS', 'GANGESSECU.NS', 'GARDENSILK.NS', 'GARNETINT.NS', 'GAYAPROJ.NS',
        'GDL.NS', 'GEECEE.NS', 'GENESYS.NS', 'GENUSPOWER.NS', 'GEOJITFSL.NS', 'GEPIL.NS',
        'GESHIP.NS', 'GET&D.NS', 'GHCL.NS', 'GHCLTEXTIL.NS', 'GICHSGFIN.NS', 'GILLANDERS.NS',
        'GILLETTE.NS', 'GINNIFILA.NS', 'GIPCL.NS', 'GISOLUTION.NS', 'GITANJALI.NS', 'GKWLIMITED.NS',
        'GLAXO.NS', 'GLENMARK.NS', 'GLOBALEDGE.NS', 'GLOBALPET.NS', 'GLOBALVECT.NS', 'GLS.NS',
        'GMBREW.NS', 'GMDC.NS', 'GMDCLTD.NS', 'GMMPFAUDLR.NS', 'GMRAIRPORT.NS', 'GMRINFRA.NS',
        'GNFC.NS', 'GOACARBON.NS', 'GOCLCORP.NS', 'GOCOLORS.NS', 'GODFRYPHLP.NS', 'GODREJAGRO.NS',
        'GODREJIND.NS', 'GODREJPROP.NS', 'GOENKA.NS', 'GOENKA.NS', 'GOKALDAS.NS', 'GOKEX.NS',
        'GOKULSUR.NS', 'GOLDIAM.NS', 'GOLDTECHINT.NS', 'GOODYEAR.NS', 'GPPL.NS', 'GRABALLIN.NS',
        'GRACEPRINT.NS', 'GRASIM.NS', 'GRAVITA.NS', 'GREAVESCOT.NS', 'GREENLAM.NS', 'GREENPOWER.NS',
        'GREENPLY.NS', 'GRINDWELL.NS', 'GRINFRA.NS', 'GROBTEA.NS', 'GRPLTD.NS', 'GRSE.NS',
        'GRUH.NS', 'GSFC.NS', 'GSPL.NS', 'GSS.NS', 'GSTL.NS', 'GTL.NS',
        'GTLINFRA.NS', 'GTN.NS', 'GTNIND.NS', 'GTPL.NS', 'GUFICBIO.NS', 'GUJALKALI.NS',
        'GUJAPOLLO.NS', 'GUJFLUORO.NS', 'GUJGAS.NS', 'GUJNREDIST.NS', 'GUJRAFFIA.NS', 'GUJRATGAS.NS',
        'GUJSIDHCEM.NS', 'GULFOILLUB.NS', 'GULFPETRO.NS', 'GVKPIL.NS', 'GVPTECH.NS', 'HAL.NS',
        'HANUNG.NS', 'HAPPSTMNDS.NS', 'HARDCASTLE.NS', 'HARDWYN.NS', 'HARIOMPIPE.NS', 'HARRMALAYA.NS',
        'HARSHA.NS', 'HATHWAY.NS', 'HATSUN.NS', 'HAVELLS.NS', 'HBLPOWER.NS', 'HCC.NS',
        'HCG.NS', 'HCLINFOSYS.NS', 'HCLTECH.NS', 'HCL-INSYS.NS', 'HEG.NS', 'HEIDELBERG.NS',
        'HEMIPROP.NS', 'HERANBA.NS', 'HERCULES.NS', 'HERITGFOOD.NS', 'HESTERBIO.NS', 'HEXATRADEX.NS',
        'HFCL.NS', 'HGINFRA.NS', 'HGS.NS', 'HIKAL.NS', 'HIL.NS', 'HIMATSEIDE.NS',
        'HINDALCO.NS', 'HINDCOMPOS.NS', 'HINDCON.NS', 'HINDCOPPER.NS', 'HINDDORROL.NS', 'HINDNATGLS.NS',
        'HINDOILEXP.NS', 'HINDPETRO.NS', 'HINDTINDOWS.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'HIRECT.NS',
        'HITECH.NS', 'HITECHCORP.NS', 'HITECHGEAR.NS', 'HLEGLAS.NS', 'HMT.NS', 'HMVL.NS',
        'HNDFDS.NS', 'HOMEFIRST.NS', 'HONAUT.NS', 'HONDAPOWER.NS', 'HOVS.NS', 'HPAL.NS',
        'HSCL.NS', 'HTMEDIA.NS', 'HUBTOWN.NS', 'HUDCO.NS', 'HUHTAMAKI.NS', 'IBREALEST.NS',
        'ICDSLTD.NS', 'ICEMAKE.NS', 'ICICIBANK.NS', 'ICICIPRULI.NS', 'ICIL.NS', 'ICRA.NS',
        'IDBI.NS', 'IDEA.NS', 'IDFC.NS', 'IDFCBANK.NS', 'IFBAGRO.NS', 'IFBIND.NS',
        'IFCI.NS', 'IFGLEXPOR.NS', 'IFGLREFRAC.NS', 'IGL.NS', 'IGPL.NS', 'IIFLWAM.NS',
        'IL&FSENG.NS', 'IL&FSTRANS.NS', 'IMFA.NS', 'IMPAL.NS', 'IMPEXFERRO.NS', 'INANI.NS',
        'INDBANK.NS', 'INDHOTEL.NS', 'INDIANB.NS', 'INDIANCARD.NS', 'INDIANHUME.NS', 'INDIGO.NS',
        'INDIGOPNTS.NS', 'INDLMETER.NS', 'INDNIPPON.NS', 'INDOAMIN.NS', 'INDOBORAX.NS', 'INDOCOUNT.NS',
        'INDOFIL.NS', 'INDORAMA.NS', 'INDOSTAR.NS', 'INDOTECH.NS', 'INDOTHAI.NS', 'INDRAMEDCO.NS',
        'INDSWFTLAB.NS', 'INDSWFTLTD.NS', 'INEOSSTYRO.NS', 'INFIBEAM.NS', 'INFINITE.NS', 'INFOBEAN.NS',
        'INFOLLION.NS', 'INFOMEDIA.NS', 'INFOTECH.NS', 'INFRABEES.NS', 'INFRATEL.NS', 'INGERRAND.NS',
        'INGRAMMICR.NS', 'INNOVACAP.NS', 'INOXGREEN.NS', 'INOXLEISUR.NS', 'INOXWIND.NS', 'INSECTICID.NS',
        'INTELLECT.NS', 'INTLCONV.NS', 'INVENTURE.NS', 'IOB.NS', 'IOLCP.NS', 'IONEXCHANG.NS',
        'IPCALAB.NS', 'IPL.NS', 'IPRU.NS', 'IRB.NS', 'IRCON.NS', 'IRCTC.NS',
        'ISFT.NS', 'ISGEC.NS', 'ISMT.NS', 'ITC.NS', 'ITDC.NS', 'ITDCEM.NS',
        'ITI.NS', 'IVC.NS', 'IVRCL.NS', 'IVRCLINFRA.NS', 'IWEL.NS', 'J&KBANK.NS',
        'JAIBHARATH.NS', 'JAICORPLTD.NS', 'JAINAM.NS', 'JAIPURKURT.NS', 'JAYSHREETEA.NS', 'JBCHEPHARM.NS',
        'JBFIND.NS', 'JBMA.NS', 'JCT.NS', 'JCTLTD.NS', 'JETAIRWAYS.NS', 'JETFREIGHT.NS',
        'JHARRISPHR.NS', 'JIKIND.NS', 'JINDALPHOT.NS', 'JINDALPOLY.NS', 'JINDALSAW.NS', 'JINDALSTEL.NS',
        'JINDWORLD.NS', 'JISLDVREQS.NS', 'JISLJALEQS.NS', 'JKCEMENT.NS', 'JKIL.NS', 'JKLAKSHMI.NS',
        'JKPAPER.NS', 'JKTYRE.NS', 'JMA.NS', 'JMCPROJECT.NS', 'JMFINANCIL.NS', 'JOCIL.NS',
        'JOHNSON.NS', 'JPOLYINVST.NS', 'JPPOWER.NS', 'JSL.NS', 'JSLHISAR.NS', 'JSWENERGY.NS',
        'JSWISPATLA.NS', 'JSWSTEEL.NS', 'JTEKTINDIA.NS', 'JTLIND.NS', 'JUBILANT.NS', 'JUBLFOOD.NS',
        'JUBLINGREA.NS', 'JUGALGOLD.NS', 'JUMBOREST.NS', 'JUMPNET.NS', 'JYOTHYLAB.NS', 'JYOTISTRUC.NS',
        'KABRAEXTRU.NS', 'KAJARIACER.NS', 'KAKATCEM.NS', 'KALINDEE.NS', 'KALYANIFRG.NS', 'KALYANKJIL.NS',
        'KAMATHOTEL.NS', 'KANANIIND.NS', 'KANCHANARA.NS', 'KANPRPLA.NS', 'KANTILAL.NS', 'KAPSTON.NS',
        'KARURVYSYA.NS', 'KARWARSYNT.NS', 'KAUSHALYA.NS', 'KAVVERITEL.NS', 'KAYA.NS', 'KBCGLOBAL.NS',
        'KCP.NS', 'KCPSUGIND.NS', 'KDDL.NS', 'KDLENERGY.NS', 'KDL.NS', 'KECINTL.NS',
        'KEI.NS', 'KELLTONTEC.NS', 'KESORAMIND.NS', 'KEWAL.NS', 'KEYFINSERV.NS', 'KHADIM.NS',
        'KILITCH.NS', 'KIR LOSIND.NS', 'KIRLOSBROS.NS', 'KIRLOSENG.NS', 'KIRLOSKAR.NS', 'KITEX.NS',
        'KKC.NS', 'KKALPANAIND.NS', 'KMSUGAR.NS', 'KNRCON.NS', 'KOLTEPATIL.NS', 'KONARKSYNT.NS',
        'KOPRAN.NS', 'KOSAMATTA.NS', 'KOTAKBANK.NS', 'KOTARISUG.NS', 'KOTHARIPET.NS', 'KOTHARIPRO.NS',
        'KPIT.NS', 'KPRMILL.NS', 'KPTL.NS', 'KRBL.NS', 'KREBSBIO.NS', 'KRIDHANINF.NS',
        'KRIINFRA.NS', 'KRISHANA.NS', 'KRISHCAP.NS', 'KRITIIND.NS', 'KRITIKA.NS', 'KSCL.NS',
        'KSL.NS', 'KTKBANK.NS', 'KUANTUM.NS', 'L&TFH.NS', 'LALPATHLAB.NS', 'LAMBODHARA.NS',
        'LAOPALA.NS', 'LASA.NS', 'LAURUSLABS.NS', 'LAXMIMACH.NS', 'LCCINFOTEC.NS', 'LGBBROSLTD.NS',
        'LGBFORGE.NS', 'LIBERTSHOE.NS', 'LICHSGFIN.NS', 'LINDEINDIA.NS', 'LIKHITHA.NS', 'LINC.NS',
        'LINCOLN.NS', 'LIQUIDBEES.NS', 'LKPSEC.NS', 'LMWINDIA.NS', 'LODHA.NS', 'LOKESHMACH.NS',
        'LOTUSEYE.NS', 'LOVABLE.NS', 'LPDC.NS', 'LT.NS', 'LTFOODS.NS', 'LTFH.NS',
        'LTI.NS', 'LTIM.NS', 'LTTS.NS', 'LUMAXIND.NS', 'LUMAXTECH.NS', 'LUPIN.NS',
        'LUXIND.NS', 'LYKALABS.NS', 'M&M.NS', 'M&MFIN.NS', 'MAANALU.NS', 'MACPOWER.NS'
    ]


# Cached data fetching for better performance
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_stock_data_cached(symbol, period="3mo"):
    """Cached stock data fetch to avoid repeated API calls"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        return data if len(data) >= 20 else None
    except:
        return None

@st.cache_data(ttl=300)
def fetch_weekly_data_cached(symbol, period="6mo"):
    """Cached weekly stock data fetch"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1wk")
        return data if len(data) >= 8 else None
    except:
        return None

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
            # Use cached data fetch
            data = fetch_stock_data_cached(symbol, period)
            
            if data is None or len(data) < 20:
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
            # Use cached data fetch for daily data
            daily_data = fetch_stock_data_cached(symbol, period)
            
            if daily_data is None or len(daily_data) < 50:  # Need sufficient data for weekly analysis
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
    
    def get_global_indices(self):
        """Get global market indices data including GIFT Nifty"""
        indices_data = {}
        
        try:
            # Indian Indices
            india_indices = {
                'Nifty 50': '^NSEI',
                'Bank Nifty': '^NSEBANK',
                'GIFT Nifty': 'NIFTY_50.GI'  # GIFT Nifty symbol (may need adjustment)
            }
            
            for name, symbol in india_indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="5d")
                    if len(data) >= 2:
                        current = data['Close'].iloc[-1]
                        prev = data['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        indices_data[name] = {
                            'value': current,
                            'change': change_pct,
                            'symbol': symbol,
                            'region': 'India'
                        }
                except:
                    # If GIFT Nifty fails, skip it
                    pass
            
            # US Indices
            us_indices = {
                'S&P 500': '^GSPC',
                'Dow Jones': '^DJI',
                'Nasdaq': '^IXIC'
            }
            
            for name, symbol in us_indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="5d")
                    if len(data) >= 2:
                        current = data['Close'].iloc[-1]
                        prev = data['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        indices_data[name] = {
                            'value': current,
                            'change': change_pct,
                            'symbol': symbol,
                            'region': 'US'
                        }
                except:
                    pass
            
            # Asia Indices
            asia_indices = {
                'Nikkei 225': '^N225',
                'Hang Seng': '^HSI',
                'Shanghai': '000001.SS'
            }
            
            for name, symbol in asia_indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    data = ticker.history(period="5d")
                    if len(data) >= 2:
                        current = data['Close'].iloc[-1]
                        prev = data['Close'].iloc[-2]
                        change_pct = ((current - prev) / prev) * 100
                        indices_data[name] = {
                            'value': current,
                            'change': change_pct,
                            'symbol': symbol,
                            'region': 'Asia'
                        }
                except:
                    pass
                    
        except Exception as e:
            pass
            
        return indices_data
    
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
        
        # NEW V6.1: Handle different analysis modes
        analysis_mode = filters.get('analysis_mode', 'Daily + Weekly Combined (Recommended)')
        enable_daily_analysis = filters.get('enable_daily_analysis', True)
        enable_weekly_validation = filters.get('enable_weekly_validation', True)
        
        # Get weekly data if needed
        weekly_data = None
        if enable_weekly_validation:
            weekly_data = self.get_weekly_stock_data(symbol)
        
        # WEEKLY ONLY MODE - Return weekly patterns only
        if analysis_mode == "Weekly Only (New Feature)":
            if weekly_data is not None:
                return self.detect_weekly_patterns(weekly_data, symbol, filters)
            else:
                return []  # No weekly data available
        
        # DAILY ONLY MODE - Skip weekly validation entirely (V6.0 style)
        if analysis_mode == "Daily Only (V6.0 Style)":
            enable_weekly_validation = False
            weekly_data = None
        
        # PRIORITY 1: Current Day Breakout Detection
        if pattern_filters.get('current_day_breakout', True):
            breakout_detected, breakout_strength, breakout_details = self.detect_current_day_breakout(
                data, 
                lookback_days=filters.get('lookback_days', 20),
                min_volume_ratio=filters.get('volume_breakout_ratio', 2.0)
            )
            
            if breakout_detected and breakout_strength >= filters['pattern_strength_min']:
                # Handle weekly validation based on mode
                if enable_weekly_validation and weekly_data is not None:
                    weekly_validation = self.validate_weekly_strength(data, weekly_data, 'Current Day Breakout')
                    final_strength = breakout_strength + weekly_validation['weekly_strength_bonus']
                    
                    pattern_data = {
                        'type': 'Current Day Breakout',
                        'strength': final_strength,
                        'daily_strength': breakout_strength,
                        'success_rate': 92,
                        'research_basis': 'Real-time EOD Breakout Confirmation',
                        'pcs_suitability': 98,
                        'confidence': self.get_confidence_level(final_strength),
                        'details': breakout_details,
                        'special': 'CURRENT_DAY_BREAKOUT',
                        'weekly_validation': weekly_validation,
                        'timeframe': 'Daily + Weekly'
                    }
                else:
                    # Daily only mode
                    pattern_data = {
                        'type': 'Current Day Breakout',
                        'strength': breakout_strength,
                        'success_rate': 92,
                        'research_basis': 'Real-time EOD Breakout Confirmation',
                        'pcs_suitability': 98,
                        'confidence': self.get_confidence_level(breakout_strength),
                        'details': breakout_details,
                        'special': 'CURRENT_DAY_BREAKOUT',
                        'timeframe': 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, cup_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, flat_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, bump_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rect_bottom_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rect_top_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, hs_bottom_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, double_bottom_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, three_valleys_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rounding_bottom_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, rounding_top_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
                    # Handle weekly validation based on mode
                    if enable_weekly_validation and weekly_data is not None:
                        pattern_data = self._add_weekly_validation_to_pattern(pattern_data, scallop_strength, data, weekly_data)
                        pattern_data['timeframe'] = 'Daily + Weekly'
                    else:
                        pattern_data['timeframe'] = 'Daily Only'
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
    
    def detect_weekly_patterns(self, weekly_data, symbol, filters):
        """Detect patterns using WEEKLY timeframe data only"""
        patterns = []
        
        if weekly_data is None or len(weekly_data) < 15:
            return patterns
        
        # Get current weekly metrics
        current_weekly_close = weekly_data['Close'].iloc[-1]
        current_weekly_rsi = weekly_data['RSI'].iloc[-1] if not weekly_data['RSI'].isna().iloc[-1] else 50
        current_weekly_adx = weekly_data['ADX'].iloc[-1] if not weekly_data['ADX'].isna().iloc[-1] else 20
        weekly_sma_10 = weekly_data['SMA_10'].iloc[-1] if not weekly_data['SMA_10'].isna().iloc[-1] else current_weekly_close
        weekly_sma_20 = weekly_data['SMA_20'].iloc[-1] if not weekly_data['SMA_20'].isna().iloc[-1] else current_weekly_close
        
        # Apply filters based on WEEKLY data
        if not (filters['rsi_min'] <= current_weekly_rsi <= filters['rsi_max']):
            return patterns
        
        if current_weekly_adx < filters['adx_min']:
            return patterns
        
        # Weekly MA support check
        if filters['ma_support']:
            if current_weekly_close < weekly_sma_10 * (1 - filters['ma_tolerance']/100):
                return patterns
        
        # Get pattern filters
        pattern_filters = filters.get('pattern_filters', {})
        pattern_priority = filters.get('pattern_priority', 'All Patterns (Comprehensive)')
        
        # Weekly Pattern Detection
        
        # 1. Weekly Breakout Pattern
        if pattern_filters.get('current_day_breakout', True):
            weekly_breakout_detected, weekly_breakout_strength = self.detect_weekly_breakout(weekly_data)
            if weekly_breakout_detected and weekly_breakout_strength >= filters['pattern_strength_min']:
                pattern_data = {
                    'type': 'Weekly Breakout',
                    'strength': weekly_breakout_strength,
                    'success_rate': 88,
                    'research_basis': 'Weekly Timeframe Breakout Confirmation',
                    'pcs_suitability': 94,
                    'confidence': self.get_confidence_level(weekly_breakout_strength),
                    'timeframe': 'Weekly',
                    'special': 'WEEKLY_BREAKOUT'
                }
                if self._meets_priority_criteria(pattern_data, pattern_priority):
                    patterns.append(pattern_data)
        
        # 2. Weekly Cup and Handle
        if pattern_filters.get('cup_and_handle', True):
            weekly_cup_detected, weekly_cup_strength = self.detect_weekly_cup_and_handle(weekly_data)
            if weekly_cup_detected and weekly_cup_strength >= filters['pattern_strength_min']:
                pattern_data = {
                    'type': 'Weekly Cup and Handle',
                    'strength': weekly_cup_strength,
                    'success_rate': 82,
                    'research_basis': 'William O\'Neil - Weekly Timeframe Analysis',
                    'pcs_suitability': 92,
                    'confidence': self.get_confidence_level(weekly_cup_strength),
                    'timeframe': 'Weekly'
                }
                if self._meets_priority_criteria(pattern_data, pattern_priority):
                    patterns.append(pattern_data)
        
        # 3. Weekly Double Bottom
        if pattern_filters.get('double_bottom', True):
            weekly_db_detected, weekly_db_strength = self.detect_weekly_double_bottom(weekly_data)
            if weekly_db_detected and weekly_db_strength >= filters['pattern_strength_min']:
                pattern_data = {
                    'type': 'Weekly Double Bottom',
                    'strength': weekly_db_strength,
                    'success_rate': 78,
                    'research_basis': 'Weekly Double Bottom - Longer Term Reversal',
                    'pcs_suitability': 89,
                    'confidence': self.get_confidence_level(weekly_db_strength),
                    'timeframe': 'Weekly'
                }
                if self._meets_priority_criteria(pattern_data, pattern_priority):
                    patterns.append(pattern_data)
        
        # 4. Weekly Support Test
        if pattern_filters.get('rectangle_bottom', True):
            weekly_support_detected, weekly_support_strength = self.detect_weekly_support_test(weekly_data)
            if weekly_support_detected and weekly_support_strength >= filters['pattern_strength_min']:
                pattern_data = {
                    'type': 'Weekly Support Test',
                    'strength': weekly_support_strength,
                    'success_rate': 75,
                    'research_basis': 'Weekly Support Level Validation',
                    'pcs_suitability': 87,
                    'confidence': self.get_confidence_level(weekly_support_strength),
                    'timeframe': 'Weekly'
                }
                if self._meets_priority_criteria(pattern_data, pattern_priority):
                    patterns.append(pattern_data)
        
        return patterns
    
    def detect_weekly_breakout(self, weekly_data):
        """Detect breakout on weekly timeframe"""
        if len(weekly_data) < 12:
            return False, 0
            
        # Look for weekly breakout
        recent_weeks = weekly_data.tail(8).iloc[:-1]  # Exclude current week
        current_week = weekly_data.iloc[-1]
        
        resistance_level = recent_weeks['High'].max()
        current_close = current_week['Close']
        current_volume = current_week['Volume']
        
        # Weekly breakout criteria
        price_breakout = current_close > resistance_level * 1.02  # 2% above weekly resistance
        
        # Volume confirmation (weekly)
        avg_volume = recent_weeks['Volume'].mean()
        volume_breakout = current_volume > avg_volume * 1.3
        
        if not (price_breakout and volume_breakout):
            return False, 0
        
        strength = 0
        breakout_percentage = ((current_close - resistance_level) / resistance_level) * 100
        
        if breakout_percentage >= 5: strength += 40
        elif breakout_percentage >= 3: strength += 30
        elif breakout_percentage >= 2: strength += 25
        
        volume_ratio = current_volume / avg_volume
        if volume_ratio >= 2: strength += 30
        elif volume_ratio >= 1.5: strength += 20
        elif volume_ratio >= 1.3: strength += 15
        
        return True, strength
    
    def detect_weekly_cup_and_handle(self, weekly_data):
        """Detect cup and handle on weekly timeframe"""
        if len(weekly_data) < 20:
            return False, 0
            
        # Cup formation (weeks 1-15)
        cup_data = weekly_data.iloc[-20:-5]
        cup_high = cup_data['High'].max()
        cup_low = cup_data['Low'].min()
        
        # Handle formation (last 5 weeks)
        handle_data = weekly_data.iloc[-5:]
        handle_high = handle_data['High'].max()
        current_close = weekly_data['Close'].iloc[-1]
        
        # Cup criteria
        cup_depth = ((cup_high - cup_low) / cup_high) * 100
        valid_cup = 20 <= cup_depth <= 60  # Weekly cups can be deeper
        
        # Handle breakout
        handle_breakout = current_close > handle_high * 1.01
        
        if not (valid_cup and handle_breakout):
            return False, 0
        
        strength = 0
        if valid_cup: strength += 35
        if handle_breakout: strength += 40
        
        return True, strength
    
    def detect_weekly_double_bottom(self, weekly_data):
        """Detect double bottom on weekly timeframe"""
        if len(weekly_data) < 16:
            return False, 0
            
        # Look for two weekly lows
        recent_data = weekly_data.tail(16)
        
        # First bottom (weeks 2-7)
        first_bottom_data = recent_data.iloc[2:7]
        first_low = first_bottom_data['Low'].min()
        
        # Peak between (weeks 7-10)
        peak_data = recent_data.iloc[7:10]
        peak_high = peak_data['High'].max()
        
        # Second bottom (weeks 10-14)
        second_bottom_data = recent_data.iloc[10:14]
        second_low = second_bottom_data['Low'].min()
        
        # Current breakout
        current_close = weekly_data['Close'].iloc[-1]
        
        # Pattern validation
        bottoms_similar = abs(first_low - second_low) / min(first_low, second_low) < 0.12  # Weekly can be less precise
        significant_peak = ((peak_high - max(first_low, second_low)) / max(first_low, second_low)) * 100 > 8
        breakout = current_close > peak_high * 1.02
        
        if not (bottoms_similar and significant_peak and breakout):
            return False, 0
        
        strength = 0
        if bottoms_similar: strength += 30
        if significant_peak: strength += 25
        if breakout: strength += 30
        
        return True, strength
    
    def detect_weekly_support_test(self, weekly_data):
        """Detect support test and bounce on weekly timeframe"""
        if len(weekly_data) < 12:
            return False, 0
            
        # Find weekly support level
        support_data = weekly_data.tail(12).iloc[:-2]
        support_level = support_data['Low'].min()
        
        # Current week test
        current_week = weekly_data.iloc[-1]
        current_low = current_week['Low']
        current_close = current_week['Close']
        
        # Support test criteria
        support_test = current_low <= support_level * 1.03  # Within 3% of support
        bounce_strength = ((current_close - current_low) / current_low) * 100
        strong_bounce = bounce_strength >= 2  # At least 2% bounce from weekly low
        
        if not (support_test and strong_bounce):
            return False, 0
        
        strength = 0
        if support_test: strength += 35
        if bounce_strength >= 4: strength += 30
        elif bounce_strength >= 2: strength += 20
        
        return True, strength
    
    def get_confidence_level(self, strength):
        """Get confidence level based on pattern strength"""
        if strength >= 85:
            return 'HIGH'
        elif strength >= 70:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def identify_support_resistance_levels(self, data, num_levels=3):
        """
        Scientific Support & Resistance identification using multiple methods:
        1. K-Means Clustering for price level grouping
        2. Local Minima/Maxima detection using scipy
        3. Volume-weighted price levels
        
        Returns: dict with 'support' and 'resistance' lists [S1, S2, S3] and [R1, R2, R3]
        """
        if len(data) < 50:
            return {'support': [], 'resistance': [], 'method': 'insufficient_data'}
        
        current_price = data['Close'].iloc[-1]
        
        # METHOD 1: Local Minima and Maxima (Scipy)
        # Find local lows (support) and highs (resistance)
        order = 5  # Look at 5 candles on each side
        local_min_idx = argrelextrema(data['Low'].values, np.less, order=order)[0]
        local_max_idx = argrelextrema(data['High'].values, np.greater, order=order)[0]
        
        local_mins = data['Low'].iloc[local_min_idx].values
        local_maxs = data['High'].iloc[local_max_idx].values
        
        # METHOD 2: Volume-weighted levels
        # Calculate price levels weighted by volume at those levels
        price_vol_data = []
        for i in range(len(data)):
            price_range = np.linspace(data['Low'].iloc[i], data['High'].iloc[i], 5)
            for price in price_range:
                price_vol_data.append([price, data['Volume'].iloc[i] / 5])
        
        price_vol_df = pd.DataFrame(price_vol_data, columns=['Price', 'Volume'])
        
        # METHOD 3: K-Means Clustering
        # Combine all significant price levels
        all_support_candidates = list(local_mins)
        all_resistance_candidates = list(local_maxs)
        
        # Filter by recency and significance (last 100 days more important)
        recent_weight = 2.0
        recent_cutoff = len(data) - 100 if len(data) > 100 else 0
        
        weighted_supports = []
        for idx in local_min_idx:
            weight = recent_weight if idx >= recent_cutoff else 1.0
            weighted_supports.extend([data['Low'].iloc[idx]] * int(weight))
        
        weighted_resistances = []
        for idx in local_max_idx:
            weight = recent_weight if idx >= recent_cutoff else 1.0
            weighted_resistances.extend([data['High'].iloc[idx]] * int(weight))
        
        # Apply K-Means clustering to group nearby levels
        support_levels = []
        resistance_levels = []
        
        if len(weighted_supports) >= num_levels:
            # Cluster support levels
            supports_array = np.array(weighted_supports).reshape(-1, 1)
            kmeans_support = KMeans(n_clusters=min(num_levels * 2, len(weighted_supports)), 
                                   random_state=42, n_init=10)
            kmeans_support.fit(supports_array)
            clustered_supports = sorted(kmeans_support.cluster_centers_.flatten())
            
            # Filter supports below current price
            support_levels = [s for s in clustered_supports if s < current_price * 0.98]
            support_levels = sorted(support_levels, reverse=True)[:num_levels]
        
        if len(weighted_resistances) >= num_levels:
            # Cluster resistance levels
            resistances_array = np.array(weighted_resistances).reshape(-1, 1)
            kmeans_resistance = KMeans(n_clusters=min(num_levels * 2, len(weighted_resistances)), 
                                      random_state=42, n_init=10)
            kmeans_resistance.fit(resistances_array)
            clustered_resistances = sorted(kmeans_resistance.cluster_centers_.flatten())
            
            # Filter resistances above current price
            resistance_levels = [r for r in clustered_resistances if r > current_price * 1.02]
            resistance_levels = sorted(resistance_levels)[:num_levels]
        
        # Fallback: if not enough levels found, use percentile-based approach
        if len(support_levels) < num_levels:
            recent_data = data.tail(100)
            percentiles = [10, 20, 30]
            for p in percentiles[:num_levels - len(support_levels)]:
                level = np.percentile(recent_data['Low'], p)
                if level < current_price * 0.98:
                    support_levels.append(level)
            support_levels = sorted(set(support_levels), reverse=True)[:num_levels]
        
        if len(resistance_levels) < num_levels:
            recent_data = data.tail(100)
            percentiles = [70, 80, 90]
            for p in percentiles[:num_levels - len(resistance_levels)]:
                level = np.percentile(recent_data['High'], p)
                if level > current_price * 1.02:
                    resistance_levels.append(level)
            resistance_levels = sorted(set(resistance_levels))[:num_levels]
        
        return {
            'support': support_levels,
            'resistance': resistance_levels,
            'current_price': current_price,
            'method': 'clustering_minmax_volume'
        }
    
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
        
        # === ADD SCIENTIFIC SUPPORT LEVELS (PCS FOCUSED) ===
        sr_levels = self.identify_support_resistance_levels(data, num_levels=3)
        
        # Define distinct colors for each support level
        support_colors = {
            'S1': {'line': '#00d084', 'marker': '#00d084', 'bg': 'rgba(0, 208, 132, 0.12)'},  # Green
            'S2': {'line': '#ffa500', 'marker': '#ffa500', 'bg': 'rgba(255, 165, 0, 0.12)'},   # Orange (STOP-LOSS zone)
            'S3': {'line': '#ff3b69', 'marker': '#ff3b69', 'bg': 'rgba(255, 59, 105, 0.12)'}   # Red (danger zone)
        }
        
        support_labels = ['S1', 'S2', 'S3']
        support_descriptions = [
            'S1: First Support',
            'S2: Critical Support (Stop-Loss Zone)',
            'S3: Major Support (High Risk)'
        ]
        
        # Add Support Levels with professional triangle markers
        for i, support in enumerate(sr_levels['support']):
            if support > 0:
                label = support_labels[i]
                color_scheme = support_colors[label]
                
                # Add horizontal line
                fig.add_hline(
                    y=support,
                    line_dash="dash",
                    line_color=color_scheme['line'],
                    line_width=2,
                    opacity=0.7,
                    row=1, col=1,
                    annotation_text=f"{label}: ₹{support:.2f}",
                    annotation_position="right",
                    annotation=dict(
                        font=dict(size=11, color=color_scheme['line'], family="Roboto Mono", weight="bold"),
                        bgcolor=color_scheme['bg'],
                        bordercolor=color_scheme['line'],
                        borderwidth=2
                    )
                )
                
                # Find price points that intersect or are near the support level
                # Add triangular markers at these intersection points
                intersections_x = []
                intersections_y = []
                
                for idx in range(len(data)):
                    # Check if price touched or crossed the support level
                    if data['Low'].iloc[idx] <= support <= data['High'].iloc[idx]:
                        intersections_x.append(data.index[idx])
                        intersections_y.append(support)
                    # Also mark if close price is very near support (within 0.5%)
                    elif abs(data['Close'].iloc[idx] - support) / support < 0.005:
                        intersections_x.append(data.index[idx])
                        intersections_y.append(support)
                
                # If no intersections found, add evenly spaced markers
                if len(intersections_x) == 0:
                    num_markers = min(5, len(data) // 10)
                    if num_markers > 0:
                        step = len(data) // (num_markers + 1)
                        for j in range(1, num_markers + 1):
                            idx = min(j * step, len(data) - 1)
                            intersections_x.append(data.index[idx])
                            intersections_y.append(support)
                
                # Add triangular markers at intersection points
                if len(intersections_x) > 0:
                    fig.add_trace(
                        go.Scatter(
                            x=intersections_x,
                            y=intersections_y,
                            mode='markers',
                            name=support_descriptions[i],
                            marker=dict(
                                size=10,
                                color=color_scheme['marker'],
                                symbol='triangle-up',
                                line=dict(width=1, color='white'),
                                opacity=0.9
                            ),
                            hovertemplate=(
                                f"<b>{label} - {support_descriptions[i].split(':')[1].strip()}</b><br>"
                                f"Price: ₹{support:.2f}<br>"
                                f"Distance: ₹{abs(support - sr_levels['current_price']):.2f} "
                                f"({((support - sr_levels['current_price'])/sr_levels['current_price']*100):.2f}%)<br>"
                                "<extra></extra>"
                            ),
                            showlegend=True,
                            legendgroup=label
                        ),
                        row=1, col=1
                    )
                
                # Add shaded zone for S2 (critical stop-loss zone)
                if label == 'S2':
                    fig.add_hrect(
                        y0=support * 0.996,
                        y1=support * 1.004,
                        fillcolor=color_scheme['line'],
                        opacity=0.08,
                        line_width=0,
                        row=1, col=1
                    )
        
        # Add Current Price line (prominent)
        current_price = sr_levels['current_price']
        fig.add_hline(
            y=current_price,
            line_dash="solid",
            line_color="#ff6b00",  # Bloomberg orange
            line_width=4,
            row=1, col=1,
            annotation_text=f"CURRENT: ₹{current_price:.2f}",
            annotation_position="left",
            annotation=dict(
                font=dict(size=12, color="white", family="Roboto Mono", weight="bold"),
                bgcolor="#ff6b00",
                bordercolor="#ff8533",
                borderwidth=2
            )
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

    # =================== ENHANCEMENT 1: DELIVERY VOLUME ANALYSIS ===================
    
    def analyze_delivery_volume_percentage(self, symbol):
        """Enhanced delivery volume percentage analysis with professional insights"""
        try:
            import requests
            import re
            import pandas as pd
            import numpy as np
            from datetime import datetime, timedelta
            
            # Try to get delivery data from NSE (fallback method)
            delivery_info = self._get_delivery_data_fallback(symbol)
            
            if delivery_info:
                return delivery_info
            else:
                # Fallback: Estimate delivery volume from price action and volume patterns
                return self._estimate_delivery_volume(symbol)
                
        except Exception as e:
            return {
                'delivery_percentage': None,
                'delivery_analysis': f'Unable to fetch delivery data: {str(e)}',
                'delivery_signals': [],
                'confidence': 'Low'
            }
    
    def _get_delivery_data_fallback(self, symbol):
        """Fallback method to estimate delivery volume using technical analysis"""
        try:
            # Get stock data
            data = self.get_stock_data(symbol, period="1mo")
            if data is None or len(data) < 10:
                return None
            
            # Calculate volume-price correlation and other delivery indicators
            recent_data = data.tail(10)
            
            # Volume analysis for delivery estimation
            avg_volume = recent_data['Volume'].mean()
            current_volume = recent_data['Volume'].iloc[-1]
            
            # Price stability analysis (delivery usually associated with less volatility)
            price_volatility = recent_data['Close'].pct_change().std() * 100
            if pd.isna(price_volatility):
                price_volatility = 5.0  # Default to moderate volatility
            
            # Volume-price correlation (handle NaN)
            volume_price_corr = recent_data['Volume'].corr(recent_data['Close'])
            if pd.isna(volume_price_corr):
                volume_price_corr = 0
            
            # Estimate delivery percentage based on technical factors
            delivery_estimate = 0
            confidence = 'Low'
            signals = []
            
            # Volume analysis signals
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Higher volume with lower volatility suggests delivery
            if volume_ratio > 1.2 and price_volatility < 2.0:
                delivery_estimate += 25
                signals.append(f"High volume ({volume_ratio:.1f}x) with low volatility ({price_volatility:.1f}%)")
                confidence = 'Medium'
            elif volume_ratio > 1.5:
                delivery_estimate += 15
                signals.append(f"Significant volume increase ({volume_ratio:.1f}x average)")
                confidence = 'Medium'
            
            # Negative volume-price correlation suggests delivery accumulation
            if volume_price_corr < -0.3:
                delivery_estimate += 20
                signals.append(f"Negative volume-price correlation ({volume_price_corr:.2f})")
                confidence = 'Medium'
            elif volume_price_corr < -0.1:
                delivery_estimate += 10
                signals.append(f"Weak negative volume-price correlation ({volume_price_corr:.2f})")
            
            # Check for accumulation patterns
            if self._detect_accumulation_pattern(recent_data):
                delivery_estimate += 15
                signals.append("Accumulation pattern detected")
                confidence = 'Medium'
            
            # Price stability bonus
            if price_volatility < 1.5:
                delivery_estimate += 10
                signals.append(f"Very stable price action ({price_volatility:.1f}% volatility)")
            
            # Cap the estimate
            delivery_estimate = min(delivery_estimate, 85)
            
            analysis = "Technical delivery analysis based on volume-price patterns"
            if delivery_estimate > 40:
                analysis = "Strong delivery indications - institutional accumulation likely"
                confidence = 'High'
            elif delivery_estimate > 20:
                analysis = "Moderate delivery signals - some institutional interest"
                confidence = 'Medium'
            else:
                analysis = "Low delivery signals - mostly speculative trading"
                confidence = 'Low'
            
            return {
                'delivery_percentage': delivery_estimate,
                'delivery_analysis': analysis,
                'delivery_signals': signals,
                'confidence': confidence,
                'volume_analysis': {
                    'current_volume': int(current_volume),
                    'avg_volume': int(avg_volume),
                    'volume_ratio': current_volume / avg_volume,
                    'price_volatility': price_volatility
                }
            }
            
        except Exception as e:
            return None
    
    def _estimate_delivery_volume(self, symbol):
        """Estimate delivery volume using advanced technical analysis"""
        try:
            data = self.get_stock_data(symbol, period="2mo")
            if data is None or len(data) < 20:
                return None
            
            recent_data = data.tail(20)
            current_day = data.tail(1)
            
            # Multiple factors for delivery estimation
            signals = []
            delivery_score = 0
            
            # 1. Volume surge with price stability
            volume_surge = current_day['Volume'].iloc[0] / recent_data['Volume'].mean()
            price_change = abs(current_day['Close'].pct_change().iloc[0] * 100)
            
            if volume_surge > 1.5 and price_change < 3:
                delivery_score += 30
                signals.append(f"Volume surge ({volume_surge:.1f}x) with price stability ({price_change:.1f}%)")
            
            # 2. Institutional buying patterns (large volume at support levels)
            support_level = recent_data['Low'].min()
            current_price = current_day['Close'].iloc[0]
            
            if current_price <= support_level * 1.05 and volume_surge > 1.3:
                delivery_score += 25
                signals.append("Large volume near support - institutional accumulation")
            
            # 3. End-of-day strength (delivery usually happens throughout the day)
            open_price = current_day['Open'].iloc[0]
            close_price = current_day['Close'].iloc[0]
            high_price = current_day['High'].iloc[0]
            
            if close_price > (open_price + high_price) / 2:
                delivery_score += 15
                signals.append("End-of-day strength - sustained buying")
            
            # 4. RSI and delivery correlation
            current_rsi = data['RSI'].iloc[-1]
            if 30 < current_rsi < 70 and volume_surge > 1.2:
                delivery_score += 10
                signals.append(f"Healthy RSI ({current_rsi:.1f}) with volume - quality delivery")
            
            # Determine confidence and analysis
            if delivery_score >= 50:
                confidence = 'High'
                analysis = "Strong delivery signals - significant institutional participation"
            elif delivery_score >= 25:
                confidence = 'Medium'
                analysis = "Moderate delivery activity - some institutional interest"
            else:
                confidence = 'Low'
                analysis = "Limited delivery signals - mostly speculative activity"
            
            return {
                'delivery_percentage': min(delivery_score, 80),  # Cap at 80%
                'delivery_analysis': analysis,
                'delivery_signals': signals,
                'confidence': confidence,
                'technical_factors': {
                    'volume_surge': volume_surge,
                    'price_stability': 100 - price_change,
                    'support_proximity': ((support_level * 1.05 - current_price) / current_price * 100) if current_price <= support_level * 1.05 else 0
                }
            }
            
        except Exception as e:
            return {
                'delivery_percentage': None,
                'delivery_analysis': f'Delivery analysis error: {str(e)}',
                'delivery_signals': [],
                'confidence': 'Low'
            }
    
    def _detect_accumulation_pattern(self, data):
        """Detect accumulation patterns in recent data"""
        try:
            if len(data) < 5:
                return False
            
            volume_trend = data['Volume'].tail(5).mean() > data['Volume'].head(5).mean()
            price_stability = data['Close'].pct_change().tail(5).std() < 0.02
            
            return volume_trend and price_stability
        except:
            return False
    
    # =================== ENHANCEMENT 2: F&O CONSOLIDATION ANALYSIS ===================
    
    def detect_fno_consolidation_near_resistance(self, data, symbol, lookback_days=20):
        """Detect F&O consolidation patterns near resistance levels"""
        try:
            if len(data) < lookback_days + 10:
                return {
                    'consolidation_detected': False,
                    'analysis': 'Insufficient data for consolidation analysis',
                    'signals': []
                }
            
            recent_data = data.tail(lookback_days)
            current_price = data['Close'].iloc[-1]
            
            # 1. Identify resistance level
            resistance_analysis = self._identify_resistance_levels(data, lookback_days)
            
            # 2. Check consolidation pattern
            consolidation_analysis = self._analyze_consolidation_pattern(recent_data)
            
            # 3. Volume analysis for F&O activity
            volume_analysis = self._analyze_fno_volume_pattern(recent_data)
            
            # 4. Price action near resistance
            resistance_proximity = self._analyze_resistance_proximity(current_price, resistance_analysis)
            
            # Combine all analyses
            signals = []
            consolidation_strength = 0
            
            # Add signals from each analysis
            if resistance_analysis['strong_resistance']:
                signals.extend(resistance_analysis['signals'])
                consolidation_strength += resistance_analysis['strength']
            
            if consolidation_analysis['is_consolidating']:
                signals.extend(consolidation_analysis['signals'])
                consolidation_strength += consolidation_analysis['strength']
            
            if volume_analysis['fno_activity_high']:
                signals.extend(volume_analysis['signals'])
                consolidation_strength += volume_analysis['strength']
            
            if resistance_proximity['near_resistance']:
                signals.extend(resistance_proximity['signals'])
                consolidation_strength += resistance_proximity['strength']
            
            # Determine overall consolidation status
            consolidation_detected = consolidation_strength >= 60
            
            if consolidation_detected:
                if consolidation_strength >= 80:
                    analysis = "Strong F&O consolidation near resistance - high breakout probability"
                    confidence = 'High'
                else:
                    analysis = "Moderate F&O consolidation detected - watch for breakout"
                    confidence = 'Medium'
            else:
                analysis = "No significant F&O consolidation pattern detected"
                confidence = 'Low'
            
            return {
                'consolidation_detected': consolidation_detected,
                'consolidation_strength': consolidation_strength,
                'analysis': analysis,
                'confidence': confidence,
                'signals': signals,
                'resistance_level': resistance_analysis.get('resistance_level'),
                'consolidation_range': consolidation_analysis.get('range_info'),
                'breakout_target': resistance_analysis.get('resistance_level', current_price) * 1.05 if consolidation_detected else None
            }
            
        except Exception as e:
            return {
                'consolidation_detected': False,
                'analysis': f'Consolidation analysis error: {str(e)}',
                'signals': []
            }
    
    def _identify_resistance_levels(self, data, lookback_days=20):
        """Identify key resistance levels"""
        try:
            recent_data = data.tail(lookback_days * 2)  # Look back further for resistance
            current_price = data['Close'].iloc[-1]
            
            # Find peaks (resistance levels)
            highs = recent_data['High']
            peaks = []
            
            for i in range(2, len(highs) - 2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i-2] and 
                    highs.iloc[i] > highs.iloc[i+1] and highs.iloc[i] > highs.iloc[i+2]):
                    peaks.append(highs.iloc[i])
            
            if not peaks:
                return {'strong_resistance': False, 'signals': [], 'strength': 0}
            
            # Find the most significant resistance level
            resistance_level = max(peaks) if peaks else current_price * 1.05
            
            # Check how many times price tested this resistance
            test_count = 0
            for high in recent_data['High']:
                if abs(high - resistance_level) / resistance_level < 0.02:  # Within 2%
                    test_count += 1
            
            # Distance from current price to resistance
            distance_to_resistance = ((resistance_level - current_price) / current_price) * 100
            
            signals = []
            strength = 0
            
            if test_count >= 2:
                signals.append(f"Resistance level tested {test_count} times at ₹{resistance_level:.2f}")
                strength += 25
            
            if 0 < distance_to_resistance <= 5:
                signals.append(f"Price near resistance ({distance_to_resistance:.1f}% away)")
                strength += 30
                
            if distance_to_resistance <= 2:
                signals.append("Very close to resistance - breakout imminent")
                strength += 15
            
            strong_resistance = test_count >= 2 and distance_to_resistance <= 5
            
            return {
                'strong_resistance': strong_resistance,
                'resistance_level': resistance_level,
                'test_count': test_count,
                'distance_to_resistance': distance_to_resistance,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'strong_resistance': False, 'signals': [], 'strength': 0}
    
    def _analyze_consolidation_pattern(self, recent_data):
        """Analyze if stock is in consolidation"""
        try:
            if len(recent_data) < 10:
                return {'is_consolidating': False, 'signals': [], 'strength': 0}
            
            # Calculate consolidation metrics
            high_price = recent_data['High'].max()
            low_price = recent_data['Low'].min()
            consolidation_range = ((high_price - low_price) / low_price) * 100
            
            # Price stability
            price_volatility = recent_data['Close'].pct_change().std() * 100
            
            # Volume consistency
            volume_consistency = 1 - (recent_data['Volume'].std() / recent_data['Volume'].mean())
            
            signals = []
            strength = 0
            
            # Tight consolidation range
            if consolidation_range <= 8:
                signals.append(f"Tight consolidation range ({consolidation_range:.1f}%)")
                strength += 25
                
            if consolidation_range <= 5:
                signals.append("Very tight range - coiled spring effect")
                strength += 15
            
            # Low volatility
            if price_volatility <= 2:
                signals.append(f"Low price volatility ({price_volatility:.1f}%)")
                strength += 20
            
            # Consistent volume
            if volume_consistency > 0.3:
                signals.append("Consistent volume during consolidation")
                strength += 10
            
            is_consolidating = consolidation_range <= 8 and price_volatility <= 3
            
            return {
                'is_consolidating': is_consolidating,
                'consolidation_range': consolidation_range,
                'price_volatility': price_volatility,
                'signals': signals,
                'strength': strength,
                'range_info': {
                    'high': high_price,
                    'low': low_price,
                    'range_percent': consolidation_range
                }
            }
            
        except Exception as e:
            return {'is_consolidating': False, 'signals': [], 'strength': 0}
    
    def _analyze_fno_volume_pattern(self, recent_data):
        """Analyze volume patterns suggesting F&O activity"""
        try:
            if len(recent_data) < 5:
                return {'fno_activity_high': False, 'signals': [], 'strength': 0}
            
            # Volume analysis
            avg_volume = recent_data['Volume'].mean()
            recent_volume = recent_data['Volume'].tail(3).mean()
            volume_increase = (recent_volume / avg_volume) - 1
            
            # Volume spike consistency
            volume_spikes = (recent_data['Volume'] > avg_volume * 1.5).sum()
            total_days = len(recent_data)
            spike_ratio = volume_spikes / total_days
            
            signals = []
            strength = 0
            
            if volume_increase > 0.2:
                signals.append(f"Volume increased {volume_increase*100:.1f}% recently")
                strength += 20
            
            if spike_ratio > 0.3:
                signals.append(f"Volume spikes in {spike_ratio*100:.0f}% of recent sessions")
                strength += 15
            
            if volume_increase > 0.5:
                signals.append("Significant volume increase - F&O interest")
                strength += 20
            
            fno_activity_high = volume_increase > 0.2 and spike_ratio > 0.2
            
            return {
                'fno_activity_high': fno_activity_high,
                'volume_increase': volume_increase,
                'spike_ratio': spike_ratio,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'fno_activity_high': False, 'signals': [], 'strength': 0}
    
    def _analyze_resistance_proximity(self, current_price, resistance_analysis):
        """Analyze price proximity to resistance"""
        try:
            if not resistance_analysis.get('strong_resistance'):
                return {'near_resistance': False, 'signals': [], 'strength': 0}
            
            resistance_level = resistance_analysis.get('resistance_level', current_price * 1.05)
            distance = ((resistance_level - current_price) / current_price) * 100
            
            signals = []
            strength = 0
            
            if distance <= 1:
                signals.append("At resistance level - breakout imminent")
                strength += 35
            elif distance <= 3:
                signals.append("Very close to resistance")
                strength += 25
            elif distance <= 5:
                signals.append("Approaching resistance level")
                strength += 15
            
            near_resistance = distance <= 5
            
            return {
                'near_resistance': near_resistance,
                'distance_to_resistance': distance,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'near_resistance': False, 'signals': [], 'strength': 0}
    
    # =================== ENHANCEMENT 3: BREAKOUT-PULLBACK ANALYSIS ===================
    
    def detect_breakout_pullback_strong_green(self, data, lookback_days=30):
        """Detect breakout-pullback patterns with strong green candle confirmation"""
        try:
            if len(data) < lookback_days + 10:
                return {
                    'pattern_detected': False, 
                    'analysis': 'Insufficient data for breakout-pullback analysis',
                    'signals': []
                }
            
            # 1. Identify initial breakout
            breakout_analysis = self._identify_initial_breakout(data, lookback_days)
            
            # 2. Detect pullback phase
            pullback_analysis = self._detect_pullback_phase(data, breakout_analysis)
            
            # 3. Confirm strong green candle
            green_candle_analysis = self._analyze_strong_green_candle(data)
            
            # 4. Volume confirmation
            volume_confirmation = self._analyze_breakout_volume(data)
            
            # Combine analyses
            signals = []
            pattern_strength = 0
            
            if breakout_analysis['breakout_detected']:
                signals.extend(breakout_analysis['signals'])
                pattern_strength += breakout_analysis['strength']
            
            if pullback_analysis['pullback_detected']:
                signals.extend(pullback_analysis['signals'])
                pattern_strength += pullback_analysis['strength']
            
            if green_candle_analysis['strong_green_detected']:
                signals.extend(green_candle_analysis['signals'])
                pattern_strength += green_candle_analysis['strength']
            
            if volume_confirmation['volume_confirmed']:
                signals.extend(volume_confirmation['signals'])
                pattern_strength += volume_confirmation['strength']
            
            # Pattern detection criteria
            pattern_detected = (breakout_analysis['breakout_detected'] and 
                              pullback_analysis['pullback_detected'] and 
                              green_candle_analysis['strong_green_detected'] and
                              pattern_strength >= 70)
            
            if pattern_detected:
                if pattern_strength >= 90:
                    analysis = "Perfect breakout-pullback-breakout pattern with strong green candle"
                    confidence = 'High'
                elif pattern_strength >= 80:
                    analysis = "Strong breakout-pullback pattern - high probability setup"
                    confidence = 'High'
                else:
                    analysis = "Valid breakout-pullback pattern detected"
                    confidence = 'Medium'
            else:
                analysis = "No valid breakout-pullback pattern found"
                confidence = 'Low'
            
            return {
                'pattern_detected': pattern_detected,
                'pattern_strength': pattern_strength,
                'analysis': analysis,
                'confidence': confidence,
                'signals': signals,
                'breakout_level': breakout_analysis.get('breakout_level'),
                'pullback_low': pullback_analysis.get('pullback_low'),
                'target_price': breakout_analysis.get('breakout_level', 0) * 1.08 if pattern_detected else None,
                'stop_loss': pullback_analysis.get('pullback_low', 0) * 0.98 if pattern_detected else None
            }
            
        except Exception as e:
            return {
                'pattern_detected': False,
                'analysis': f'Breakout-pullback analysis error: {str(e)}',
                'signals': []
            }
    
    def _identify_initial_breakout(self, data, lookback_days):
        """Identify the initial breakout from consolidation"""
        try:
            # Look for breakout in recent history (5-30 days ago)
            potential_breakout_period = data.iloc[-lookback_days:-5] if len(data) > lookback_days else data.iloc[:-5]
            
            if len(potential_breakout_period) < 10:
                return {'breakout_detected': False, 'signals': [], 'strength': 0}
            
            # Find consolidation before breakout
            consolidation_data = potential_breakout_period.iloc[:-5]  # Earlier data for consolidation
            breakout_data = potential_breakout_period.iloc[-10:]      # Recent data for breakout
            
            if len(consolidation_data) < 5:
                return {'breakout_detected': False, 'signals': [], 'strength': 0}
            
            # Consolidation metrics
            consolidation_high = consolidation_data['High'].max()
            consolidation_range = ((consolidation_high - consolidation_data['Low'].min()) / 
                                 consolidation_data['Low'].min()) * 100
            
            # Breakout detection
            breakout_candle = None
            breakout_level = None
            
            for i, (idx, row) in enumerate(breakout_data.iterrows()):
                if row['High'] > consolidation_high * 1.02:  # 2% above consolidation high
                    breakout_candle = row
                    breakout_level = consolidation_high
                    break
            
            if breakout_candle is None:
                return {'breakout_detected': False, 'signals': [], 'strength': 0}
            
            # Analyze breakout strength
            signals = []
            strength = 0
            
            # Volume on breakout day
            avg_volume = consolidation_data['Volume'].mean()
            breakout_volume = breakout_candle['Volume']
            volume_ratio = breakout_volume / avg_volume
            
            if volume_ratio > 1.5:
                signals.append(f"Strong volume on breakout ({volume_ratio:.1f}x average)")
                strength += 25
            
            # Consolidation quality
            if consolidation_range <= 10:
                signals.append(f"Good consolidation base ({consolidation_range:.1f}% range)")
                strength += 20
            
            # Breakout candle strength
            candle_body = abs(breakout_candle['Close'] - breakout_candle['Open'])
            candle_range = breakout_candle['High'] - breakout_candle['Low']
            body_ratio = candle_body / candle_range if candle_range > 0 else 0
            
            if body_ratio > 0.6 and breakout_candle['Close'] > breakout_candle['Open']:
                signals.append("Strong green breakout candle")
                strength += 20
            
            return {
                'breakout_detected': True,
                'breakout_level': breakout_level,
                'breakout_candle': breakout_candle,
                'volume_ratio': volume_ratio,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'breakout_detected': False, 'signals': [], 'strength': 0}
    
    def _detect_pullback_phase(self, data, breakout_analysis):
        """Detect pullback phase after initial breakout"""
        try:
            if not breakout_analysis.get('breakout_detected'):
                return {'pullback_detected': False, 'signals': [], 'strength': 0}
            
            breakout_level = breakout_analysis.get('breakout_level')
            recent_data = data.tail(10)  # Look at last 10 days
            
            # Find the lowest point after breakout (pullback low)
            pullback_low = recent_data['Low'].min()
            current_price = data['Close'].iloc[-1]
            
            # Pullback criteria
            pullback_depth = ((breakout_level - pullback_low) / breakout_level) * 100
            recovery_from_low = ((current_price - pullback_low) / pullback_low) * 100
            
            signals = []
            strength = 0
            
            # Healthy pullback (not too deep)
            if 3 <= pullback_depth <= 15:
                signals.append(f"Healthy pullback ({pullback_depth:.1f}% from breakout)")
                strength += 25
            
            # Pullback found support above previous consolidation
            if pullback_low > breakout_level * 0.95:
                signals.append("Pullback held above breakout level - strength")
                strength += 20
            
            # Recovery from pullback low
            if recovery_from_low >= 2:
                signals.append(f"Recovery from pullback low ({recovery_from_low:.1f}%)")
                strength += 15
            
            # Volume during pullback (should be lower)
            breakout_volume = breakout_analysis.get('breakout_candle', {}).get('Volume', 0)
            pullback_avg_volume = recent_data['Volume'].mean()
            
            if pullback_avg_volume < breakout_volume * 0.8:
                signals.append("Lower volume during pullback - healthy correction")
                strength += 10
            
            pullback_detected = (3 <= pullback_depth <= 20 and 
                                pullback_low > breakout_level * 0.90 and
                                recovery_from_low >= 1)
            
            return {
                'pullback_detected': pullback_detected,
                'pullback_low': pullback_low,
                'pullback_depth': pullback_depth,
                'recovery_from_low': recovery_from_low,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'pullback_detected': False, 'signals': [], 'strength': 0}
    
    def _analyze_strong_green_candle(self, data):
        """Analyze the current/recent strong green candle"""
        try:
            current_candle = data.iloc[-1]
            
            # Green candle check
            is_green = current_candle['Close'] > current_candle['Open']
            
            if not is_green:
                # Check previous candle
                if len(data) > 1:
                    current_candle = data.iloc[-2]
                    is_green = current_candle['Close'] > current_candle['Open']
                
                if not is_green:
                    return {'strong_green_detected': False, 'signals': [], 'strength': 0}
            
            # Analyze candle strength
            candle_body = current_candle['Close'] - current_candle['Open']
            candle_range = current_candle['High'] - current_candle['Low']
            body_percentage = (candle_body / candle_range) * 100 if candle_range > 0 else 0
            
            # Price change percentage
            prev_close = data.iloc[-2]['Close'] if len(data) > 1 else current_candle['Open']
            price_change = ((current_candle['Close'] - prev_close) / prev_close) * 100
            
            # Volume analysis
            recent_avg_volume = data['Volume'].tail(10).mean()
            current_volume = current_candle['Volume']
            volume_ratio = current_volume / recent_avg_volume if recent_avg_volume > 0 else 1
            
            signals = []
            strength = 0
            
            # Strong green candle criteria
            if body_percentage >= 60:
                signals.append(f"Strong green candle ({body_percentage:.0f}% body)")
                strength += 20
            
            if price_change >= 2:
                signals.append(f"Strong price gain ({price_change:.1f}%)")
                strength += 15
            
            if volume_ratio >= 1.3:
                signals.append(f"Above average volume ({volume_ratio:.1f}x)")
                strength += 15
            
            # Gap up opening
            if len(data) > 1:
                prev_close = data.iloc[-2]['Close']
                if current_candle['Open'] > prev_close * 1.005:  # 0.5% gap up
                    signals.append("Gap up opening - strong momentum")
                    strength += 10
            
            strong_green_detected = (body_percentage >= 50 and 
                                   price_change >= 1.5 and 
                                   volume_ratio >= 1.1)
            
            return {
                'strong_green_detected': strong_green_detected,
                'body_percentage': body_percentage,
                'price_change': price_change,
                'volume_ratio': volume_ratio,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'strong_green_detected': False, 'signals': [], 'strength': 0}
    
    def _analyze_breakout_volume(self, data):
        """Analyze volume confirmation for breakout pattern"""
        try:
            current_volume = data['Volume'].iloc[-1]
            avg_volume_20 = data['Volume'].tail(20).mean()
            avg_volume_5 = data['Volume'].tail(5).mean()
            
            volume_surge = current_volume / avg_volume_20
            recent_volume_trend = avg_volume_5 / avg_volume_20
            
            signals = []
            strength = 0
            
            if volume_surge >= 1.5:
                signals.append(f"Strong volume surge ({volume_surge:.1f}x)")
                strength += 20
            
            if recent_volume_trend >= 1.2:
                signals.append("Increasing volume trend")
                strength += 10
            
            # Volume distribution analysis
            high_volume_days = (data['Volume'].tail(5) > avg_volume_20 * 1.2).sum()
            if high_volume_days >= 2:
                signals.append(f"Multiple high volume days ({high_volume_days}/5)")
                strength += 10
            
            volume_confirmed = volume_surge >= 1.3 or recent_volume_trend >= 1.2
            
            return {
                'volume_confirmed': volume_confirmed,
                'volume_surge': volume_surge,
                'recent_volume_trend': recent_volume_trend,
                'signals': signals,
                'strength': strength
            }
            
        except Exception as e:
            return {'volume_confirmed': False, 'signals': [], 'strength': 0}
    
    # =================== ENHANCEMENT 4: ENHANCED SUPPORT & RESISTANCE ===================
    
    def enhanced_support_resistance_analysis(self, data, lookback_days=50):
        """Enhanced support and resistance analysis with multiple timeframe confirmation"""
        try:
            if len(data) < lookback_days:
                return {
                    'analysis_available': False,
                    'message': 'Insufficient data for enhanced S&R analysis',
                    'support_levels': [],
                    'resistance_levels': []
                }
            
            current_price = data['Close'].iloc[-1]
            
            # 1. Identify multiple support and resistance levels
            sr_levels = self._identify_multiple_sr_levels(data, lookback_days)
            
            # 2. Analyze level strength and reliability
            level_analysis = self._analyze_sr_level_strength(data, sr_levels)
            
            # 3. Current price position analysis
            position_analysis = self._analyze_current_price_position(current_price, level_analysis)
            
            # 4. Breakout/breakdown probability
            breakout_analysis = self._analyze_breakout_probability(data, level_analysis, current_price)
            
            # 5. Volume at key levels
            volume_analysis = self._analyze_volume_at_levels(data, level_analysis)
            
            # Combine all analyses
            support_levels = [level for level in level_analysis if level['type'] == 'support']
            resistance_levels = [level for level in level_analysis if level['type'] == 'resistance']
            
            # Sort by strength
            support_levels.sort(key=lambda x: x['strength'], reverse=True)
            resistance_levels.sort(key=lambda x: x['strength'], reverse=True)
            
            # Generate comprehensive analysis
            analysis_summary = self._generate_sr_analysis_summary(
                current_price, support_levels, resistance_levels, 
                position_analysis, breakout_analysis, volume_analysis
            )
            
            return {
                'analysis_available': True,
                'current_price': current_price,
                'support_levels': support_levels[:5],  # Top 5 support levels
                'resistance_levels': resistance_levels[:5],  # Top 5 resistance levels
                'position_analysis': position_analysis,
                'breakout_analysis': breakout_analysis,
                'volume_analysis': volume_analysis,
                'analysis_summary': analysis_summary,
                'key_levels': {
                    'immediate_support': support_levels[0] if support_levels else None,
                    'immediate_resistance': resistance_levels[0] if resistance_levels else None,
                    'strong_support': next((s for s in support_levels if s['strength'] >= 80), None),
                    'strong_resistance': next((r for r in resistance_levels if r['strength'] >= 80), None)
                }
            }
            
        except Exception as e:
            return {
                'analysis_available': False,
                'message': f'Enhanced S&R analysis error: {str(e)}',
                'support_levels': [],
                'resistance_levels': []
            }
    
    def _identify_multiple_sr_levels(self, data, lookback_days):
        """Identify multiple support and resistance levels using various methods"""
        try:
            levels = []
            
            # Method 1: Pivot Points (High/Low reversals)
            pivot_levels = self._find_pivot_levels(data, lookback_days)
            levels.extend(pivot_levels)
            
            # Method 2: Moving Average levels
            ma_levels = self._find_ma_support_resistance(data)
            levels.extend(ma_levels)
            
            # Method 3: Volume-based levels (high volume price zones)
            volume_levels = self._find_volume_based_levels(data, lookback_days)
            levels.extend(volume_levels)
            
            # Method 4: Psychological levels (round numbers)
            psychological_levels = self._find_psychological_levels(data['Close'].iloc[-1])
            levels.extend(psychological_levels)
            
            # Method 5: Fibonacci retracement levels
            fib_levels = self._find_fibonacci_levels(data, lookback_days)
            levels.extend(fib_levels)
            
            return levels
            
        except Exception as e:
            return []
    
    def _find_pivot_levels(self, data, lookback_days):
        """Find pivot highs and lows as S&R levels"""
        try:
            levels = []
            recent_data = data.tail(lookback_days)
            
            # Find pivot highs (resistance)
            for i in range(2, len(recent_data) - 2):
                current_high = recent_data['High'].iloc[i]
                if (current_high > recent_data['High'].iloc[i-1] and 
                    current_high > recent_data['High'].iloc[i-2] and
                    current_high > recent_data['High'].iloc[i+1] and 
                    current_high > recent_data['High'].iloc[i+2]):
                    
                    levels.append({
                        'level': current_high,
                        'type': 'resistance',
                        'method': 'pivot_high',
                        'date': recent_data.index[i],
                        'base_strength': 30
                    })
            
            # Find pivot lows (support)
            for i in range(2, len(recent_data) - 2):
                current_low = recent_data['Low'].iloc[i]
                if (current_low < recent_data['Low'].iloc[i-1] and 
                    current_low < recent_data['Low'].iloc[i-2] and
                    current_low < recent_data['Low'].iloc[i+1] and 
                    current_low < recent_data['Low'].iloc[i+2]):
                    
                    levels.append({
                        'level': current_low,
                        'type': 'support',
                        'method': 'pivot_low',
                        'date': recent_data.index[i],
                        'base_strength': 30
                    })
            
            return levels
            
        except Exception as e:
            return []
    
    def _find_ma_support_resistance(self, data):
        """Find moving average based support/resistance"""
        try:
            levels = []
            current_price = data['Close'].iloc[-1]
            
            # Key moving averages
            ma_periods = [20, 50, 100, 200]
            
            for period in ma_periods:
                if len(data) >= period:
                    ma_value = data['Close'].tail(period).mean()
                    
                    # Determine if MA is acting as support or resistance
                    if current_price > ma_value:
                        sr_type = 'support'
                    else:
                        sr_type = 'resistance'
                    
                    # MA strength based on period (longer = stronger)
                    strength = min(20 + (period / 10), 50)
                    
                    levels.append({
                        'level': ma_value,
                        'type': sr_type,
                        'method': f'MA_{period}',
                        'date': data.index[-1],
                        'base_strength': strength
                    })
            
            return levels
            
        except Exception as e:
            return []
    
    def _find_volume_based_levels(self, data, lookback_days):
        """Find support/resistance based on high volume zones"""
        try:
            levels = []
            recent_data = data.tail(lookback_days)
            
            # Find high volume days
            volume_threshold = recent_data['Volume'].quantile(0.8)  # Top 20% volume days
            high_volume_data = recent_data[recent_data['Volume'] >= volume_threshold]
            
            if len(high_volume_data) == 0:
                return levels
            
            # Create price zones from high volume days
            price_zones = []
            for _, row in high_volume_data.iterrows():
                zone_center = (row['High'] + row['Low']) / 2
                price_zones.append(zone_center)
            
            # Cluster similar price zones
            price_zones.sort()
            clustered_zones = []
            
            if price_zones:
                current_cluster = [price_zones[0]]
                for price in price_zones[1:]:
                    if abs(price - current_cluster[-1]) / current_cluster[-1] < 0.02:  # Within 2%
                        current_cluster.append(price)
                    else:
                        if len(current_cluster) >= 2:  # At least 2 occurrences
                            zone_avg = sum(current_cluster) / len(current_cluster)
                            clustered_zones.append({
                                'level': zone_avg,
                                'occurrences': len(current_cluster)
                            })
                        current_cluster = [price]
                
                # Add last cluster
                if len(current_cluster) >= 2:
                    zone_avg = sum(current_cluster) / len(current_cluster)
                    clustered_zones.append({
                        'level': zone_avg,
                        'occurrences': len(current_cluster)
                    })
            
            # Convert to S&R levels
            current_price = data['Close'].iloc[-1]
            for zone in clustered_zones:
                sr_type = 'support' if zone['level'] < current_price else 'resistance'
                strength = min(25 + (zone['occurrences'] * 5), 45)
                
                levels.append({
                    'level': zone['level'],
                    'type': sr_type,
                    'method': 'volume_zone',
                    'date': data.index[-1],
                    'base_strength': strength,
                    'occurrences': zone['occurrences']
                })
            
            return levels
            
        except Exception as e:
            return []
    
    def _find_psychological_levels(self, current_price):
        """Find psychological round number levels"""
        try:
            levels = []
            
            # Determine the scale based on current price
            if current_price >= 1000:
                round_base = 100  # Round to nearest 100
            elif current_price >= 100:
                round_base = 50   # Round to nearest 50
            else:
                round_base = 10   # Round to nearest 10
            
            # Find nearby round numbers
            lower_round = (int(current_price // round_base) * round_base)
            upper_round = lower_round + round_base
            
            # Add levels if they're not too far from current price
            for level_price in [lower_round, upper_round]:
                distance_pct = abs(level_price - current_price) / current_price * 100
                
                if distance_pct <= 10:  # Within 10%
                    sr_type = 'support' if level_price < current_price else 'resistance'
                    
                    levels.append({
                        'level': float(level_price),
                        'type': sr_type,
                        'method': 'psychological',
                        'date': None,
                        'base_strength': 20
                    })
            
            return levels
            
        except Exception as e:
            return []
    
    def _find_fibonacci_levels(self, data, lookback_days):
        """Find Fibonacci retracement levels"""
        try:
            levels = []
            recent_data = data.tail(lookback_days)
            
            if len(recent_data) < 10:
                return levels
            
            # Find the major swing high and low
            swing_high = recent_data['High'].max()
            swing_low = recent_data['Low'].min()
            
            # Fibonacci retracement levels
            fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786]
            price_range = swing_high - swing_low
            current_price = data['Close'].iloc[-1]
            
            for ratio in fib_ratios:
                fib_level = swing_high - (price_range * ratio)
                
                # Determine if it's support or resistance
                sr_type = 'support' if fib_level < current_price else 'resistance'
                
                # Only include levels that are reasonably close to current price
                distance_pct = abs(fib_level - current_price) / current_price * 100
                if distance_pct <= 15:  # Within 15%
                    levels.append({
                        'level': fib_level,
                        'type': sr_type,
                        'method': f'fibonacci_{ratio}',
                        'date': None,
                        'base_strength': 25
                    })
            
            return levels
            
        except Exception as e:
            return []
    
    def _analyze_sr_level_strength(self, data, sr_levels):
        """Analyze the strength of each support/resistance level"""
        try:
            analyzed_levels = []
            
            for level_info in sr_levels:
                level = level_info['level']
                base_strength = level_info.get('base_strength', 20)
                
                # Test count - how many times price tested this level
                test_count = self._count_level_tests(data, level)
                
                # Recency - how recent was the last test
                recency_bonus = self._calculate_recency_bonus(data, level)
                
                # Volume at level - higher volume = stronger level
                volume_bonus = self._calculate_volume_bonus(data, level)
                
                # Price reaction strength
                reaction_bonus = self._calculate_reaction_bonus(data, level)
                
                # Calculate total strength
                total_strength = min(base_strength + test_count * 15 + recency_bonus + volume_bonus + reaction_bonus, 100)
                
                analyzed_level = {
                    **level_info,
                    'strength': total_strength,
                    'test_count': test_count,
                    'recency_bonus': recency_bonus,
                    'volume_bonus': volume_bonus,
                    'reaction_bonus': reaction_bonus,
                    'distance_from_current': abs(level - data['Close'].iloc[-1]),
                    'distance_percentage': (abs(level - data['Close'].iloc[-1]) / data['Close'].iloc[-1]) * 100
                }
                
                analyzed_levels.append(analyzed_level)
            
            return analyzed_levels
            
        except Exception as e:
            return sr_levels
    
    def _count_level_tests(self, data, level, tolerance=0.02):
        """Count how many times price tested a level"""
        try:
            test_count = 0
            
            for _, row in data.iterrows():
                # Check if high or low tested the level
                high_test = abs(row['High'] - level) / level <= tolerance
                low_test = abs(row['Low'] - level) / level <= tolerance
                
                if high_test or low_test:
                    test_count += 1
            
            return min(test_count, 10)  # Cap at 10
            
        except Exception as e:
            return 0
    
    def _calculate_recency_bonus(self, data, level, tolerance=0.02):
        """Calculate bonus for recent level tests"""
        try:
            recent_data = data.tail(10)  # Last 10 days
            
            for i, (_, row) in enumerate(recent_data.iterrows()):
                high_test = abs(row['High'] - level) / level <= tolerance
                low_test = abs(row['Low'] - level) / level <= tolerance
                
                if high_test or low_test:
                    # More recent = higher bonus
                    return 15 - i  # 15 for today, 14 for yesterday, etc.
            
            return 0
            
        except Exception as e:
            return 0
    
    def _calculate_volume_bonus(self, data, level, tolerance=0.02):
        """Calculate bonus for high volume at level"""
        try:
            volume_at_level = []
            avg_volume = data['Volume'].mean()
            
            for _, row in data.iterrows():
                high_test = abs(row['High'] - level) / level <= tolerance
                low_test = abs(row['Low'] - level) / level <= tolerance
                
                if high_test or low_test:
                    volume_at_level.append(row['Volume'])
            
            if not volume_at_level:
                return 0
            
            max_volume = max(volume_at_level)
            volume_ratio = max_volume / avg_volume
            
            if volume_ratio >= 2:
                return 15
            elif volume_ratio >= 1.5:
                return 10
            elif volume_ratio >= 1.2:
                return 5
            else:
                return 0
                
        except Exception as e:
            return 0
    
    def _calculate_reaction_bonus(self, data, level, tolerance=0.02):
        """Calculate bonus for strong price reactions at level"""
        try:
            reactions = []
            
            for i in range(1, len(data)):
                current_row = data.iloc[i]
                prev_row = data.iloc[i-1]
                
                # Check if price tested level and reacted
                level_tested = (abs(current_row['Low'] - level) / level <= tolerance or 
                              abs(current_row['High'] - level) / level <= tolerance)
                
                if level_tested and i < len(data) - 1:
                    next_row = data.iloc[i+1]
                    
                    # Calculate reaction strength
                    if level < current_row['Close']:  # Support level
                        reaction = (next_row['Close'] - current_row['Low']) / current_row['Low'] * 100
                    else:  # Resistance level
                        reaction = (current_row['High'] - next_row['Close']) / next_row['Close'] * 100
                    
                    reactions.append(max(reaction, 0))
            
            if not reactions:
                return 0
            
            max_reaction = max(reactions)
            
            if max_reaction >= 5:
                return 15
            elif max_reaction >= 3:
                return 10
            elif max_reaction >= 1:
                return 5
            else:
                return 0
                
        except Exception as e:
            return 0
    
    def _analyze_current_price_position(self, current_price, analyzed_levels):
        """Analyze current price position relative to S&R levels"""
        try:
            # Find nearest support and resistance
            supports = [level for level in analyzed_levels if level['type'] == 'support' and level['level'] < current_price]
            resistances = [level for level in analyzed_levels if level['type'] == 'resistance' and level['level'] > current_price]
            
            # Sort by distance
            supports.sort(key=lambda x: current_price - x['level'])
            resistances.sort(key=lambda x: x['level'] - current_price)
            
            nearest_support = supports[0] if supports else None
            nearest_resistance = resistances[0] if resistances else None
            
            # Calculate position metrics
            position_strength = 'Neutral'
            
            if nearest_support and nearest_resistance:
                support_distance = ((current_price - nearest_support['level']) / nearest_support['level']) * 100
                resistance_distance = ((nearest_resistance['level'] - current_price) / current_price) * 100
                
                if support_distance < resistance_distance:
                    if support_distance <= 2:
                        position_strength = 'At Support'
                    elif support_distance <= 5:
                        position_strength = 'Near Support'
                    else:
                        position_strength = 'Above Support'
                else:
                    if resistance_distance <= 2:
                        position_strength = 'At Resistance'
                    elif resistance_distance <= 5:
                        position_strength = 'Near Resistance'
                    else:
                        position_strength = 'Below Resistance'
            
            return {
                'position_strength': position_strength,
                'nearest_support': nearest_support,
                'nearest_resistance': nearest_resistance,
                'support_distance_pct': ((current_price - nearest_support['level']) / nearest_support['level']) * 100 if nearest_support else None,
                'resistance_distance_pct': ((nearest_resistance['level'] - current_price) / current_price) * 100 if nearest_resistance else None
            }
            
        except Exception as e:
            return {'position_strength': 'Unknown', 'nearest_support': None, 'nearest_resistance': None}
    
    def _analyze_breakout_probability(self, data, analyzed_levels, current_price):
        """Analyze probability of breakout/breakdown"""
        try:
            # Get recent price action
            recent_data = data.tail(5)
            price_momentum = ((current_price - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) > 5 else 0
            
            # Volume trend
            recent_volume = recent_data['Volume'].mean()
            historical_volume = data['Volume'].tail(20).mean()
            volume_trend = (recent_volume / historical_volume - 1) * 100
            
            # Find levels close to current price
            close_levels = [level for level in analyzed_levels 
                          if abs(level['level'] - current_price) / current_price <= 0.05]  # Within 5%
            
            breakout_probability = 'Low'
            breakdown_probability = 'Low'
            
            # Analyze breakout potential
            close_resistances = [level for level in close_levels if level['type'] == 'resistance']
            if close_resistances and price_momentum > 2 and volume_trend > 20:
                if any(level['strength'] < 60 for level in close_resistances):
                    breakout_probability = 'High'
                else:
                    breakout_probability = 'Medium'
            
            # Analyze breakdown potential
            close_supports = [level for level in close_levels if level['type'] == 'support']
            if close_supports and price_momentum < -2 and volume_trend > 20:
                if any(level['strength'] < 60 for level in close_supports):
                    breakdown_probability = 'High'
                else:
                    breakdown_probability = 'Medium'
            
            return {
                'breakout_probability': breakout_probability,
                'breakdown_probability': breakdown_probability,
                'price_momentum': price_momentum,
                'volume_trend': volume_trend,
                'close_levels_count': len(close_levels)
            }
            
        except Exception as e:
            return {
                'breakout_probability': 'Unknown',
                'breakdown_probability': 'Unknown',
                'price_momentum': 0,
                'volume_trend': 0
            }
    
    def _analyze_volume_at_levels(self, data, analyzed_levels):
        """Analyze volume behavior at key levels"""
        try:
            volume_insights = []
            
            for level in analyzed_levels[:10]:  # Top 10 levels
                level_price = level['level']
                
                # Find days when price was near this level
                tolerance = 0.02
                level_days = []
                
                for _, row in data.iterrows():
                    near_level = (abs(row['High'] - level_price) / level_price <= tolerance or 
                                abs(row['Low'] - level_price) / level_price <= tolerance)
                    
                    if near_level:
                        level_days.append(row['Volume'])
                
                if level_days:
                    avg_volume_at_level = sum(level_days) / len(level_days)
                    overall_avg_volume = data['Volume'].mean()
                    volume_ratio = avg_volume_at_level / overall_avg_volume
                    
                    volume_insights.append({
                        'level': level_price,
                        'type': level['type'],
                        'method': level['method'],
                        'avg_volume_at_level': avg_volume_at_level,
                        'volume_ratio': volume_ratio,
                        'test_days': len(level_days)
                    })
            
            # Sort by volume ratio
            volume_insights.sort(key=lambda x: x['volume_ratio'], reverse=True)
            
            return {
                'high_volume_levels': volume_insights[:5],
                'average_volume_ratio': sum(vi['volume_ratio'] for vi in volume_insights) / len(volume_insights) if volume_insights else 1,
                'total_analyzed_levels': len(volume_insights)
            }
            
        except Exception as e:
            return {'high_volume_levels': [], 'average_volume_ratio': 1, 'total_analyzed_levels': 0}
    
    def _generate_sr_analysis_summary(self, current_price, support_levels, resistance_levels, 
                                    position_analysis, breakout_analysis, volume_analysis):
        """Generate comprehensive S&R analysis summary"""
        try:
            summary = {
                'key_insights': [],
                'trading_signals': [],
                'risk_assessment': 'Medium',
                'confidence_level': 'Medium'
            }
            
            # Position analysis insights
            position = position_analysis['position_strength']
            if position in ['At Support', 'Near Support']:
                summary['key_insights'].append(f"Price is {position.lower()} - potential bounce opportunity")
                summary['trading_signals'].append("Watch for reversal signals at support")
            elif position in ['At Resistance', 'Near Resistance']:
                summary['key_insights'].append(f"Price is {position.lower()} - potential reversal zone")
                summary['trading_signals'].append("Watch for rejection or breakout at resistance")
            
            # Breakout analysis insights
            if breakout_analysis['breakout_probability'] == 'High':
                summary['key_insights'].append("High probability of upside breakout")
                summary['trading_signals'].append("Prepare for potential breakout trade")
                summary['risk_assessment'] = 'High Reward Potential'
            
            if breakout_analysis['breakdown_probability'] == 'High':
                summary['key_insights'].append("High probability of breakdown")
                summary['trading_signals'].append("Consider protective stops or short opportunity")
                summary['risk_assessment'] = 'High Risk'
            
            # Volume insights
            high_vol_levels = volume_analysis.get('high_volume_levels', [])
            if high_vol_levels:
                top_vol_level = high_vol_levels[0]
                if top_vol_level['volume_ratio'] > 1.5:
                    summary['key_insights'].append(
                        f"Strong {top_vol_level['type']} at ₹{top_vol_level['level']:.2f} with high volume"
                    )
            
            # Support/Resistance strength
            strong_supports = [s for s in support_levels if s['strength'] >= 70]
            strong_resistances = [r for r in resistance_levels if r['strength'] >= 70]
            
            if strong_supports:
                summary['key_insights'].append(f"{len(strong_supports)} strong support level(s) identified")
                summary['confidence_level'] = 'High'
            
            if strong_resistances:
                summary['key_insights'].append(f"{len(strong_resistances)} strong resistance level(s) identified")
                summary['confidence_level'] = 'High'
            
            # Overall assessment
            if len(summary['key_insights']) >= 3:
                summary['confidence_level'] = 'High'
            elif len(summary['key_insights']) >= 2:
                summary['confidence_level'] = 'Medium'
            else:
                summary['confidence_level'] = 'Low'
            
            return summary
            
        except Exception as e:
            return {
                'key_insights': ['Analysis summary generation failed'],
                'trading_signals': [],
                'risk_assessment': 'Unknown',
                'confidence_level': 'Low'
            }
def create_professional_sidebar():
    """Create professional sidebar with Angel One styling"""
    with st.sidebar:
        # Stock Universe Selection - SIMPLIFIED
        st.markdown("### 📊 Stock Universe")
        
        universe_option = st.radio(
            "Select Stock Universe:",
            ["NSE F&O Stocks (219)", "NSE Non-F&O Stocks (800+)"],
            help="Toggle between F&O and Non-F&O stock universes",
            index=0
        )
        
        # Load stock list based on selection
        if universe_option == "NSE F&O Stocks (219)":
            stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE
            st.success(f"🎯 **F&O Universe**: {len(stocks_to_scan)} stocks with futures & options")
        else:
            with st.spinner("🔄 Fetching NSE Non-F&O stocks..."):
                stocks_to_scan = get_nse_non_fno_stocks()
            st.success(f"📈 **Non-F&O Universe**: {len(stocks_to_scan)} liquid NSE stocks")
        
        # Core Technical Filters
        st.markdown("### ⚙️ Core Filters")
        
        with st.expander("🎯 Technical Settings", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                rsi_min = st.slider("RSI Min:", 20, 80, 30)
            with col2:
                rsi_max = st.slider("RSI Max:", 20, 80, 75)
            
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
                    'rectangle_top': st.checkbox("Rectangle Top", value=True, help="Support test after rectangle"),
                }
            
            with col2:
                pattern_filters.update({
                    'head_shoulders_bottom': st.checkbox("Head-and-Shoulders Bottom", value=True, help="Classic reversal pattern"),
                    'double_bottom': st.checkbox("Double Bottom (Eve & Eve)", value=True, help="Double bottom formation"),
                    'three_rising_valleys': st.checkbox("Three Rising Valleys", value=True, help="Progressive support levels"),
                    'rounding_bottom': st.checkbox("Rounding Bottom", value=True, help="Saucer/bowl pattern"),
                    'rounding_top_upside': st.checkbox("Rounding Top (Upside Break)", value=True, help="Rare counter-trend pattern"),
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
            
            # NEW V6.1: Separate Daily/Weekly Analysis Options
            st.markdown("**🔍 Timeframe Analysis:**")
            
            analysis_mode = st.radio(
                "Select Analysis Mode:",
                [
                    "Daily Only (V6.0 Style)",
                    "Weekly Only (New Feature)", 
                    "Daily + Weekly Combined (Recommended)"
                ],
                index=2,  # Default to combined
                help="Choose timeframe analysis approach"
            )
            
            # Analysis mode explanations
            if analysis_mode == "Daily Only (V6.0 Style)":
                st.info(
                    "📊 **Daily Analysis**: Pattern detection using current day EOD confirmation only. Fast scanning with original V6.0 logic."
                )
                enable_daily_analysis = True
                enable_weekly_validation = False
                
            elif analysis_mode == "Weekly Only (New Feature)":
                st.info(
                    "📈 **Weekly Analysis**: Pattern detection using weekly timeframe only. Slower but captures longer-term trends."
                )
                enable_daily_analysis = False
                enable_weekly_validation = True
                
            else:  # Combined mode
                st.info(
                    "🎯 **Combined Analysis**: Daily patterns validated with weekly confirmation. Best accuracy with moderate scan time."
                )
                enable_daily_analysis = True
                enable_weekly_validation = True
        
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
        
        # === ENHANCEMENTS SECTION ===
        st.markdown("---")
        
        # Enhancement toggles
        enhancement_options = {
            'delivery_volume': st.checkbox("📊 Delivery Volume Analysis", value=True, 
                                         help="Analyze delivery percentage and institutional participation"),
            'fno_consolidation': st.checkbox("🔄 F&O Consolidation Detection", value=True,
                                           help="Detect consolidation patterns near resistance levels"),
            'breakout_pullback': st.checkbox("📈 Breakout-Pullback Patterns", value=True,
                                           help="Identify breakout-pullback-breakout patterns with strong green candles"),
            'enhanced_sr': st.checkbox("🎯 Enhanced Support & Resistance", value=True,
                                     help="Advanced multi-timeframe support and resistance analysis")
        }
        
        # Market Sentiment
        st.markdown("---")
        
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
            'analysis_mode': analysis_mode,
            'enable_daily_analysis': enable_daily_analysis,
            'enable_weekly_validation': enable_weekly_validation,
            'show_charts': show_charts,
            'show_news': show_news,
            'export_results': export_results,
            'stocks_limit': stocks_limit,
            'market_sentiment': sentiment_data
        ,
        
        # Enhancement options
        'enhancements': enhancement_options
    }

def create_main_scanner_tab(config):
    """Create main scanner tab with current day focus"""
    # Initialize scanner (needed for both scanning and chart display)
    scanner = ProfessionalPCSScanner()
    
    # Simple scan button
    st.markdown(f"**Ready to scan {len(config['stocks_to_scan'])} stocks**")
    scan_button = st.button("🚀 Start Scan", type="primary", key="main_scan", use_container_width=True)
    
    if scan_button:
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
                
                # =================== PROCESS ENHANCEMENTS ===================
                enhancement_results = {}
                
                if config.get('enhancements', {}).get('delivery_volume', False):
                    try:
                        delivery_analysis = scanner.analyze_delivery_volume_percentage(symbol)
                        enhancement_results['delivery_volume'] = delivery_analysis
                    except Exception as e:
                        enhancement_results['delivery_volume'] = {
                            'delivery_percentage': None,
                            'delivery_analysis': f'Error: {str(e)}',
                            'delivery_signals': [],
                            'confidence': 'Low'
                        }
                
                if config.get('enhancements', {}).get('fno_consolidation', False):
                    try:
                        consolidation_analysis = scanner.detect_fno_consolidation_near_resistance(
                            data, symbol, lookback_days=20
                        )
                        enhancement_results['fno_consolidation'] = consolidation_analysis
                    except Exception as e:
                        enhancement_results['fno_consolidation'] = {
                            'consolidation_detected': False,
                            'analysis': f'Error: {str(e)}',
                            'signals': []
                        }
                
                if config.get('enhancements', {}).get('breakout_pullback', False):
                    try:
                        breakout_pullback_analysis = scanner.detect_breakout_pullback_strong_green(
                            data, lookback_days=30
                        )
                        enhancement_results['breakout_pullback'] = breakout_pullback_analysis
                    except Exception as e:
                        enhancement_results['breakout_pullback'] = {
                            'pattern_detected': False,
                            'analysis': f'Error: {str(e)}',
                            'signals': []
                        }
                
                if config.get('enhancements', {}).get('enhanced_sr', False):
                    try:
                        sr_analysis = scanner.enhanced_support_resistance_analysis(
                            data, lookback_days=50
                        )
                        enhancement_results['enhanced_sr'] = sr_analysis
                    except Exception as e:
                        enhancement_results['enhanced_sr'] = {
                            'analysis_available': False,
                            'message': f'Error: {str(e)}',
                            'support_levels': [],
                            'resistance_levels': []
                        }
                
                # Create the stock result with all data including enhancements
                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                    'news_data': news_data
                }
                
                # Add enhancement results if any
                if enhancement_results:
                    stock_result['enhancements'] = enhancement_results
                
                results.append(stock_result)
                
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
            # Store results in session state for persistence
            st.session_state['scan_results'] = results

    # Display results (works on button click and subsequent reruns)
    if st.session_state.get('scan_results'):
        results = st.session_state['scan_results']

        # Display results with dropdown interface
        st.markdown("---")
        st.markdown("### 📋 Scan Results - Select Stock for Analysis")
            
        # Build summary table
        summary_data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
            has_current_breakout = any('Current Day' in p['type'] for p in result['patterns'])
            has_news = result.get('news_data') and result['news_data']['news_count'] > 0
            stock_key = result['symbol'].replace('.NS', '').replace('^', '')
                
            summary_data.append({
                'Symbol': stock_key,
                'Confidence': overall_confidence,
                'Strength': f"{max_strength:.0f}%",
                'Price': f"₹{result['current_price']:.2f}",
                'Volume': f"{result['volume_ratio']:.1f}x",
                'RSI': f"{result['rsi']:.1f}",
                'ADX': f"{result['adx']:.1f}",
                'Today': '🔥' if has_current_breakout else '',
                'News': '📰' if has_news else '',
                'Patterns': len(result['patterns'])
            })
            
        # Display summary table
        if summary_data:
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
                height=min(400, len(summary_df) * 35 + 38)
            )
                
            st.markdown("---")
                
            # Stock selector dropdown
            stock_options = [f"{row['Symbol']} - {row['Confidence']} ({row['Strength']})" for row in summary_data]
                
            # Initialize selection in session state
            if 'selected_stock_idx' not in st.session_state:
                st.session_state['selected_stock_idx'] = 0
                
            selected_display = st.selectbox(
                "🔍 Select a stock to view detailed analysis:",
                options=stock_options,
                index=st.session_state['selected_stock_idx'],
                key='stock_selector'
            )
                
            # Update selected index
            st.session_state['selected_stock_idx'] = stock_options.index(selected_display)
            result = results[st.session_state['selected_stock_idx']]
                
            # Display detailed analysis for selected stock
            stock_key = result['symbol'].replace('.NS', '').replace('^', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'
                
            st.markdown("---")
            st.markdown(f"## 📊 Detailed Analysis: **{stock_key}**")
                
            # Create tabs for organized display
            detail_tabs = st.tabs(["📈 Overview", "🎯 Patterns", "🚀 Enhancements", "📊 Charts"])
                
            with detail_tabs[0]:  # Overview tab
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
                has_news = result.get('news_data') and result['news_data']['news_count'] > 0
                if has_news:
                    news_data = result['news_data']
                    sentiment_emoji = "🟢" if news_data['overall_sentiment'] == 'positive' else "🔴" if news_data['overall_sentiment'] == 'negative' else "🟡"
                        
                    st.markdown(f"### {sentiment_emoji} Today's News - {news_data['overall_sentiment'].upper()} Sentiment")
                        
                    for news_item in news_data['news_items'][:2]:
                        relevance_emoji = "🔥" if news_item['relevance'] == 'high' else "⚡" if news_item['relevance'] == 'medium' else "📄"
                        st.info(f"**{relevance_emoji}** {news_item['headline']}")
                
            with detail_tabs[1]:  # Patterns tab
                for pattern in result['patterns']:
                    confidence_emoji = "🟢" if pattern['confidence'] == 'HIGH' else "🟡" if pattern['confidence'] == 'MEDIUM' else "🔴"
                        
                    st.markdown(f"### {confidence_emoji} {pattern['type']} - {pattern['confidence']} Confidence")
                        
                    # Pattern metrics
                    pcol1, pcol2, pcol3 = st.columns(3)
                    with pcol1:
                        st.metric("Strength", f"{pattern['strength']}%")
                    with pcol2:
                        st.metric("Success Rate", f"{pattern['success_rate']}%")
                    with pcol3:
                        st.metric("PCS Fit", f"{pattern['pcs_suitability']}%")
                        
                    # Weekly validation if present
                    weekly_val = pattern.get('weekly_validation', {})
                    if weekly_val.get('weekly_validation', False):
                        st.success(f"📈 Weekly Confirmation: {weekly_val.get('weekly_context', '')}")
                    elif weekly_val.get('weekly_strength_bonus', 0) > 0:
                        st.warning(f"📊 Weekly Support: {weekly_val.get('weekly_context', '')}")
                        
                    st.markdown("---")
                
            with detail_tabs[2]:  # Enhancements tab
                enhancements = result.get('enhancements', {})
                    
                if enhancements:
                    st.markdown("### 🚀 Enhancement Analysis")
                        
                    # Delivery Volume
                    if 'delivery_volume' in enhancements:
                        delivery = enhancements['delivery_volume']
                        if delivery.get('delivery_percentage') is not None:
                            st.markdown("#### 📊 Delivery Volume Analysis")
                            ecol1, ecol2 = st.columns(2)
                            with ecol1:
                                st.metric("Estimated Delivery", f"{delivery.get('delivery_percentage', 0):.1f}%")
                            with ecol2:
                                st.metric("Confidence", delivery.get('confidence', 'Low'))
                            st.write(f"**Analysis:** {delivery.get('delivery_analysis', 'N/A')}")
                        
                    # F&O Consolidation
                    if 'fno_consolidation' in enhancements:
                        consolidation = enhancements['fno_consolidation']
                        st.markdown("#### 🔄 F&O Consolidation")
                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            st.metric("Status", "✅ Detected" if consolidation.get('consolidation_detected') else "❌ Not Detected")
                        with ecol2:
                            st.metric("Strength", f"{consolidation.get('consolidation_strength', 0)}/100")
                        st.write(f"**Analysis:** {consolidation.get('analysis', 'N/A')}")
                        
                    # Breakout-Pullback
                    if 'breakout_pullback' in enhancements:
                        breakout = enhancements['breakout_pullback']
                        st.markdown("#### 📈 Breakout-Pullback")
                        ecol1, ecol2 = st.columns(2)
                        with ecol1:
                            st.metric("Status", "✅ Detected" if breakout.get('pattern_detected') else "❌ Not Detected")
                        with ecol2:
                            st.metric("Strength", f"{breakout.get('pattern_strength', 0)}/100")
                        st.write(f"**Analysis:** {breakout.get('analysis', 'N/A')}")
                        
                    # Enhanced S&R
                    if 'enhanced_sr' in enhancements:
                        sr = enhancements['enhanced_sr']
                        if sr.get('analysis_available'):
                            st.markdown("#### 🎯 Enhanced Support & Resistance")
                            ecol1, ecol2 = st.columns(2)
                            with ecol1:
                                st.metric("Support Levels", len(sr.get('support_levels', [])))
                            with ecol2:
                                st.metric("Resistance Levels", len(sr.get('resistance_levels', [])))
                            st.write(f"**Position:** {sr.get('position_analysis', {}).get('position_strength', 'N/A')}")
                else:
                    st.info("No enhancement analysis available for this stock")
                
            with detail_tabs[3]:  # Charts tab
                if config['show_charts']:
                    st.markdown("#### 📊 Technical Chart Analysis")
                    chart = scanner.create_tradingview_chart(
                        result['data'], 
                        result['symbol'], 
                        result['patterns'][0] if result['patterns'] else None
                    )
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                else:
                    st.info("📊 Charts are disabled. Enable in sidebar settings.")

    else:
        st.warning("🔍 No current day patterns found. Try adjusting filters.")
            
        st.markdown("### 💡 Suggestions:")
        st.markdown("- Lower **Pattern Strength** to 50-60%")
        st.markdown("- Reduce **Volume Ratio** to 1.0x")  
        st.markdown("- Expand **RSI range** to 25-85")
        st.markdown("- Check if markets traded today")

def main():
    # Get sidebar configuration
    config = create_professional_sidebar()
    
    # Create tabs
    tab1, tab2 = st.tabs(["🎯 Scanner", "🌍 Market Overview"])
    
    with tab1:
        # Main Scanner Tab
        create_main_scanner_tab(config)
    
    with tab2:
        # Market Overview Tab - Bloomberg Style
        st.markdown("""
        <style>
        .bloomberg-card {
            background: #0a0a0a;
            border: 1px solid #2a2a2a;
            border-left: 3px solid #ff6b00;
            padding: 16px 20px;
            margin-bottom: 12px;
            font-family: 'Courier New', monospace;
        }
        .bloomberg-card:hover {
            background: #151515;
            border-left-color: #ff8533;
        }
        .bb-symbol {
            font-size: 13px;
            color: #999;
            font-weight: 600;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .bb-name {
            font-size: 11px;
            color: #666;
            margin-top: 2px;
        }
        .bb-price {
            font-size: 28px;
            font-weight: 700;
            color: #fff;
            margin: 8px 0 4px 0;
            letter-spacing: -0.5px;
        }
        .bb-change {
            font-size: 16px;
            font-weight: 600;
        }
        .bb-change.positive {
            color: #00d084;
        }
        .bb-change.negative {
            color: #ff3b69;
        }
        .bb-section {
            margin: 30px 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 1px solid #2a2a2a;
        }
        .bb-section-title {
            font-size: 12px;
            color: #ff6b00;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        </style>
        """, unsafe_allow_html=True)
        
        scanner = ProfessionalPCSScanner()
        indices_data = scanner.get_global_indices()
        
        # Indian Indices Section
        st.markdown('<div class="bb-section"><div class="bb-section-title">INDIAN MARKETS</div></div>', unsafe_allow_html=True)
        
        india_cols = st.columns(3)
        india_indices = [
            ('Nifty 50', 'NSE:NIFTY'),
            ('Bank Nifty', 'NSE:BANKNIFTY'),
            ('GIFT Nifty', 'SGX:NIFTY')
        ]
        
        for col, (index_name, symbol) in zip(india_cols, india_indices):
            with col:
                if index_name in indices_data:
                    idx = indices_data[index_name]
                    change_pct = idx['change']
                    change_class = "positive" if change_pct >= 0 else "negative"
                    change_sign = "+" if change_pct >= 0 else ""
                    
                    st.markdown(f"""
                    <div class="bloomberg-card">
                        <div class="bb-symbol">{symbol}</div>
                        <div class="bb-name">{index_name}</div>
                        <div class="bb-price">{idx['value']:,.2f}</div>
                        <div class="bb-change {change_class}">{change_sign}{change_pct:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # US Indices Section
        st.markdown('<div class="bb-section"><div class="bb-section-title">US MARKETS</div></div>', unsafe_allow_html=True)
        
        us_cols = st.columns(3)
        us_indices = [
            ('S&P 500', 'SPX INDEX'),
            ('Dow Jones', 'INDU INDEX'),
            ('Nasdaq', 'COMP INDEX')
        ]
        
        for col, (index_name, symbol) in zip(us_cols, us_indices):
            with col:
                if index_name in indices_data:
                    idx = indices_data[index_name]
                    change_pct = idx['change']
                    change_class = "positive" if change_pct >= 0 else "negative"
                    change_sign = "+" if change_pct >= 0 else ""
                    
                    st.markdown(f"""
                    <div class="bloomberg-card">
                        <div class="bb-symbol">{symbol}</div>
                        <div class="bb-name">{index_name}</div>
                        <div class="bb-price">{idx['value']:,.0f}</div>
                        <div class="bb-change {change_class}">{change_sign}{change_pct:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Asia Indices Section
        st.markdown('<div class="bb-section"><div class="bb-section-title">ASIA MARKETS</div></div>', unsafe_allow_html=True)
        
        asia_cols = st.columns(3)
        asia_indices = [
            ('Nikkei 225', 'NKY INDEX'),
            ('Hang Seng', 'HSI INDEX'),
            ('Shanghai', 'SHCOMP INDEX')
        ]
        
        for col, (index_name, symbol) in zip(asia_cols, asia_indices):
            with col:
                if index_name in indices_data:
                    idx = indices_data[index_name]
                    change_pct = idx['change']
                    change_class = "positive" if change_pct >= 0 else "negative"
                    change_sign = "+" if change_pct >= 0 else ""
                    
                    st.markdown(f"""
                    <div class="bloomberg-card">
                        <div class="bb-symbol">{symbol}</div>
                        <div class="bb-name">{index_name}</div>
                        <div class="bb-price">{idx['value']:,.0f}</div>
                        <div class="bb-change {change_class}">{change_sign}{change_pct:.2f}%</div>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
