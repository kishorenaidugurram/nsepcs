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
import logging
from functools import wraps
import hashlib
warnings.filterwarnings('ignore')

# ============================================================================
# ENHANCED LOGGING SYSTEM
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nse_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# ENHANCED CACHING DECORATORS
# ============================================================================
def smart_cache(ttl_seconds=300):
    """Smart caching decorator with TTL support"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hashlib.md5(str(args).encode()).hexdigest()}"
            
            # Check if cached result exists and is valid
            if cache_key in st.session_state:
                cached_time, cached_result = st.session_state[cache_key]
                if time.time() - cached_time < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}, executing...")
            result = func(*args, **kwargs)
            st.session_state[cache_key] = (time.time(), result)
            return result
        return wrapper
    return decorator

# ============================================================================
# ERROR RECOVERY & RETRY LOGIC
# ============================================================================
def retry_with_backoff(max_retries=3, backoff_factor=2):
    """Retry decorator with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    wait_time = backoff_factor ** attempt
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}), "
                                     f"retrying in {wait_time}s: {str(e)}")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts: {str(e)}")
                        raise
        return wrapper
    return decorator

# Set page config
st.set_page_config(
    page_title="NSE F&O PCS Professional Scanner v2.0", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ENHANCED PROFESSIONAL UI SYSTEM
# ============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {
        /* Professional Finance Design System */
        --primary-50: hsl(174, 62%, 98%);
        --primary-100: hsl(174, 62%, 95%);
        --primary-500: hsl(174, 62%, 47%);
        --primary-600: hsl(174, 62%, 40%);
        --primary-700: hsl(174, 62%, 33%);
        
        --neutral-100: hsl(210, 20%, 96%);
        --neutral-600: hsl(210, 12%, 43%);
        --neutral-800: hsl(210, 18%, 23%);
        
        --success-bg: hsl(142, 76%, 96%);
        --success-text: hsl(142, 76%, 30%);
        --error-bg: hsl(0, 86%, 97%);
        --error-text: hsl(0, 86%, 40%);
        
        --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    * {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    .main {
        background: var(--neutral-100);
        padding: 1.5rem 2rem;
    }
    
    h1 {
        color: var(--primary-700);
        font-weight: 700;
    }
    
    .stButton > button {
        background: var(--primary-600);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: var(--primary-700);
        transform: translateY(-1px);
    }
    
    /* Enhanced Alert Boxes */
    .alert-success {
        background: var(--success-bg);
        border-left: 4px solid var(--success-text);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .alert-error {
        background: var(--error-bg);
        border-left: 4px solid var(--error-text);
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .main {
            padding: 1rem;
        }
        
        h1 {
            font-size: 1.5rem;
        }
        
        .stButton > button {
            width: 100%;
            margin: 0.5rem 0;
        }
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# COMPLETE NSE F&O UNIVERSE - ALL 219 STOCKS
# ============================================================================
COMPLETE_NSE_FO_UNIVERSE = [
    # Indices (4)
    '^NSEI', '^NSEBANK', '^CNXFINANCE', '^CNXMIDCAP',
    
    # ALL NSE F&O Individual stocks (215 stocks)
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

# Stock categories
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

# ============================================================================
# ENHANCED DATA FETCHING WITH CACHING & RETRY
# ============================================================================
@smart_cache(ttl_seconds=300)  # 5-minute cache
@retry_with_backoff(max_retries=3)
def fetch_stock_data_enhanced(symbol, period='3mo', interval='1d'):
    """Enhanced stock data fetching with caching and error recovery"""
    try:
        logger.info(f"Fetching data for {symbol}")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return None
            
        # Add volume validation
        if 'Volume' in df.columns and df['Volume'].sum() == 0:
            logger.warning(f"Zero volume data for {symbol}")
            return None
            
        logger.info(f"Successfully fetched {len(df)} records for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching {symbol}: {str(e)}")
        return None

# ============================================================================
# ENHANCED PATTERN DETECTION WITH CONFIDENCE SCORES
# ============================================================================
def detect_patterns_enhanced(df, symbol):
    """Enhanced pattern detection with confidence scoring"""
    try:
        if df is None or df.empty or len(df) < 20:
            return None
        
        patterns = []
        confidence_score = 0
        
        # Calculate indicators with error handling
        try:
            df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
            df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
            df['EMA_12'] = ta.trend.ema_indicator(df['Close'], window=12)
            df['EMA_26'] = ta.trend.ema_indicator(df['Close'], window=26)
            
            # RSI
            df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
            
            # MACD
            macd = ta.trend.MACD(df['Close'])
            df['MACD'] = macd.macd()
            df['MACD_Signal'] = macd.macd_signal()
            df['MACD_Hist'] = macd.macd_diff()
            
            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(df['Close'])
            df['BB_High'] = bollinger.bollinger_hband()
            df['BB_Low'] = bollinger.bollinger_lband()
            df['BB_Mid'] = bollinger.bollinger_mavg()
            
            # Volume indicators
            df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
            
        except Exception as e:
            logger.error(f"Indicator calculation error for {symbol}: {str(e)}")
            return None
        
        # Get latest values with null checks
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # Check for None/NaN values
        required_fields = ['Close', 'RSI', 'MACD', 'MACD_Signal', 'SMA_20', 'SMA_50']
        if any(pd.isna(latest.get(field)) for field in required_fields):
            logger.warning(f"Missing indicator values for {symbol}")
            return None
        
        # PATTERN DETECTION WITH CONFIDENCE SCORING
        
        # 1. Bullish Crossover (Enhanced)
        if latest['SMA_20'] > latest['SMA_50'] and prev['SMA_20'] <= prev['SMA_50']:
            patterns.append('Bullish SMA Crossover')
            confidence_score += 25
            
        # 2. RSI Oversold Recovery
        if 30 < latest['RSI'] < 40 and prev['RSI'] <= 30:
            patterns.append('RSI Oversold Recovery')
            confidence_score += 20
            
        # 3. MACD Bullish Crossover
        if latest['MACD'] > latest['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
            patterns.append('MACD Bullish Cross')
            confidence_score += 20
            
        # 4. Bollinger Band Bounce
        if latest['Close'] > latest['BB_Low'] and prev['Close'] <= prev['BB_Low']:
            patterns.append('BB Lower Band Bounce')
            confidence_score += 15
            
        # 5. Volume Surge
        if latest['Volume'] > latest['Volume_SMA'] * 1.5:
            patterns.append('High Volume')
            confidence_score += 10
            
        # 6. Price above key moving averages
        if latest['Close'] > latest['SMA_20'] and latest['Close'] > latest['SMA_50']:
            patterns.append('Above Key MAs')
            confidence_score += 10
            
        if not patterns:
            return None
            
        # Calculate price metrics
        price_change = ((latest['Close'] - prev['Close']) / prev['Close']) * 100
        week_high = df['Close'].tail(5).max()
        week_low = df['Close'].tail(5).min()
        
        return {
            'symbol': symbol,
            'patterns': patterns,
            'confidence_score': min(confidence_score, 100),  # Cap at 100
            'current_price': round(latest['Close'], 2),
            'price_change_pct': round(price_change, 2),
            'rsi': round(latest['RSI'], 2),
            'macd': round(latest['MACD'], 4),
            'volume': int(latest['Volume']),
            'volume_ratio': round(latest['Volume'] / latest['Volume_SMA'], 2) if latest['Volume_SMA'] > 0 else 0,
            'week_high': round(week_high, 2),
            'week_low': round(week_low, 2),
            'sma_20': round(latest['SMA_20'], 2),
            'sma_50': round(latest['SMA_50'], 2),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        logger.error(f"Pattern detection error for {symbol}: {str(e)}")
        return None

# ============================================================================
# OPTIMIZED PARALLEL PROCESSING
# ============================================================================
def scan_stocks_parallel_enhanced(symbols, max_workers=10, batch_size=20):
    """Enhanced parallel scanning with batching and progress tracking"""
    results = []
    total_symbols = len(symbols)
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Process in batches for better resource management
    for batch_start in range(0, total_symbols, batch_size):
        batch_end = min(batch_start + batch_size, total_symbols)
        batch = symbols[batch_start:batch_end]
        
        status_text.text(f"Processing batch {batch_start//batch_size + 1}/{(total_symbols + batch_size - 1)//batch_size}...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_symbol = {
                executor.submit(fetch_stock_data_enhanced, symbol): symbol 
                for symbol in batch
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    df = future.result(timeout=30)
                    if df is not None:
                        result = detect_patterns_enhanced(df, symbol)
                        if result:
                            results.append(result)
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {str(e)}")
                
                # Update progress
                progress = (batch_end) / total_symbols
                progress_bar.progress(min(progress, 1.0))
        
        # Small delay between batches to prevent rate limiting
        if batch_end < total_symbols:
            time.sleep(1)
    
    progress_bar.empty()
    status_text.empty()
    
    # Sort by confidence score
    results.sort(key=lambda x: x['confidence_score'], reverse=True)
    logger.info(f"Scan completed: {len(results)} stocks with patterns found")
    
    return results

# ============================================================================
# EXCEL EXPORT FUNCTION
# ============================================================================
def create_excel_stock_list(results):
    """Create Excel file with enhanced formatting"""
    try:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Pattern Stocks"
        
        # Headers
        headers = ['Symbol', 'Confidence Score', 'Patterns', 'Current Price', 
                  'RSI', 'MACD', 'Volume Ratio', 'Scan Time']
        ws.append(headers)
        
        # Style headers
        for cell in ws[1]:
            cell.font = openpyxl.styles.Font(bold=True, size=12)
            cell.fill = openpyxl.styles.PatternFill(start_color="4472C4", 
                                                    end_color="4472C4", 
                                                    fill_type="solid")
            cell.font = openpyxl.styles.Font(bold=True, color="FFFFFF")
        
        # Add data
        for result in results:
            clean_symbol = result['symbol'].replace('.NS', '')
            patterns_str = ', '.join(result['patterns'])
            ws.append([
                clean_symbol,
                result['confidence_score'],
                patterns_str,
                result['current_price'],
                result['rsi'],
                result['macd'],
                result['volume_ratio'],
                result['timestamp']
            ])
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)
        
        return excel_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Excel creation error: {str(e)}")
        st.error(f"Error creating Excel file: {str(e)}")
        return None

# ============================================================================
# ENHANCED CHARTING FUNCTION
# ============================================================================
def create_enhanced_chart(symbol):
    """Create enhanced technical analysis chart"""
    try:
        df = fetch_stock_data_enhanced(symbol, period='3mo', interval='1d')
        
        if df is None or df.empty:
            st.error(f"No data available for {symbol}")
            return
        
        # Calculate indicators
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_50'] = ta.trend.sma_indicator(df['Close'], window=50)
        df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
        
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Hist'] = macd.macd_diff()
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(f'{symbol} - Price & Moving Averages', 'RSI', 'MACD')
        )
        
        # Price and MAs
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_20'],
            name='SMA 20',
            line=dict(color='orange', width=1.5)
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_50'],
            name='SMA 50',
            line=dict(color='blue', width=1.5)
        ), row=1, col=1)
        
        # RSI
        fig.add_trace(go.Scatter(
            x=df.index, y=df['RSI'],
            name='RSI',
            line=dict(color='purple', width=2)
        ), row=2, col=1)
        
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=2, col=1)
        
        # MACD
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'],
            name='MACD',
            line=dict(color='blue', width=2)
        ), row=3, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD_Signal'],
            name='Signal',
            line=dict(color='red', width=2)
        ), row=3, col=1)
        
        # Update layout
        fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        logger.error(f"Chart creation error for {symbol}: {str(e)}")
        st.error(f"Error creating chart: {str(e)}")

# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application with enhanced UI and features"""
    
    # Header with version info
    st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #0891b2, #0e7490); 
                border-radius: 1rem; margin-bottom: 2rem;'>
        <h1 style='color: white; margin: 0;'>📈 NSE F&O Scanner Professional v2.0</h1>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;'>
            Enhanced with Smart Caching • Error Recovery • Confidence Scoring
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("### ⚙️ Scanner Configuration")
        
        # Stock selection
        scan_option = st.radio(
            "Select Scan Universe:",
            ['Complete F&O Universe (219 stocks)', 
             'Nifty 50 Only', 
             'Bank Nifty', 
             'Sector-wise',
             'Custom Symbols'],
            help="Choose which stocks to scan for patterns"
        )
        
        if scan_option == 'Complete F&O Universe (219 stocks)':
            symbols_to_scan = COMPLETE_NSE_FO_UNIVERSE
        elif scan_option == 'Nifty 50 Only':
            symbols_to_scan = STOCK_CATEGORIES['Nifty 50']
        elif scan_option == 'Bank Nifty':
            symbols_to_scan = STOCK_CATEGORIES['Bank Nifty']
        elif scan_option == 'Sector-wise':
            sector = st.selectbox('Select Sector:', list(STOCK_CATEGORIES.keys()))
            symbols_to_scan = STOCK_CATEGORIES[sector]
        else:
            custom_input = st.text_area(
                "Enter symbols (one per line):",
                placeholder="RELIANCE.NS\nTCS.NS\nINFY.NS"
            )
            symbols_to_scan = [s.strip() for s in custom_input.split('\n') if s.strip()]
        
        st.markdown(f"**Stocks to scan:** {len(symbols_to_scan)}")
        
        st.markdown("---")
        
        # Performance settings
        st.markdown("### 🚀 Performance Settings")
        max_workers = st.slider("Parallel Workers", 5, 20, 10,
                               help="More workers = faster scanning (but higher resource usage)")
        
        # Filter settings
        st.markdown("### 🎯 Filter Settings")
        min_confidence = st.slider("Minimum Confidence Score", 0, 100, 40,
                                  help="Only show stocks with confidence score above this threshold")
        
        # Refresh interval
        auto_refresh = st.checkbox("Auto Refresh", value=False)
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 60, 600, 300)
    
    # Main content area
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        scan_button = st.button("🔍 Start Scan", type="primary", use_container_width=True)
    
    with col2:
        clear_cache_button = st.button("🗑️ Clear Cache", use_container_width=True)
    
    with col3:
        if 'scan_results' in st.session_state and st.session_state.scan_results:
            excel_data = create_excel_stock_list(st.session_state.scan_results)
            if excel_data:
                st.download_button(
                    label="📥 Download Results",
                    data=excel_data,
                    file_name=f"nse_patterns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    # Clear cache functionality
    if clear_cache_button:
        st.session_state.clear()
        st.success("✅ Cache cleared successfully!")
        st.rerun()
    
    # Run scan
    if scan_button:
        if not symbols_to_scan:
            st.error("⚠️ Please select stocks to scan")
            return
        
        st.info(f"🔄 Scanning {len(symbols_to_scan)} stocks with {max_workers} parallel workers...")
        
        start_time = time.time()
        
        try:
            results = scan_stocks_parallel_enhanced(symbols_to_scan, max_workers=max_workers)
            
            # Filter by confidence score
            filtered_results = [r for r in results if r['confidence_score'] >= min_confidence]
            
            elapsed_time = time.time() - start_time
            
            # Store in session state
            st.session_state.scan_results = filtered_results
            st.session_state.scan_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            st.success(f"✅ Scan completed in {elapsed_time:.2f} seconds! Found {len(filtered_results)} stocks with patterns.")
            
        except Exception as e:
            logger.error(f"Scan error: {str(e)}")
            st.error(f"❌ Scan error: {str(e)}")
            return
    
    # Display results
    if 'scan_results' in st.session_state and st.session_state.scan_results:
        st.markdown("---")
        st.markdown("## 📊 Scan Results")
        st.caption(f"Last scan: {st.session_state.get('scan_timestamp', 'N/A')}")
        
        results = st.session_state.scan_results
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Stocks Found", len(results))
        
        with col2:
            avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
            st.metric("Avg Confidence", f"{avg_confidence:.1f}")
        
        with col3:
            high_conf = len([r for r in results if r['confidence_score'] >= 70])
            st.metric("High Confidence (≥70)", high_conf)
        
        with col4:
            avg_rsi = sum(r['rsi'] for r in results) / len(results)
            st.metric("Avg RSI", f"{avg_rsi:.1f}")
        
        # Results table
        st.markdown("### 📋 Detailed Results")
        
        # Convert to DataFrame for display
        df_display = pd.DataFrame(results)
        df_display['symbol'] = df_display['symbol'].str.replace('.NS', '')
        df_display['patterns'] = df_display['patterns'].apply(lambda x: ', '.join(x))
        
        # Select columns to display
        display_cols = ['symbol', 'confidence_score', 'patterns', 'current_price', 
                       'price_change_pct', 'rsi', 'volume_ratio']
        
        st.dataframe(
            df_display[display_cols].style.background_gradient(
                subset=['confidence_score'], 
                cmap='RdYlGn'
            ),
            use_container_width=True,
            height=400
        )
        
        # Chart section
        st.markdown("### 📈 Technical Analysis Charts")
        
        # Stock selector for charts
        selected_symbol = st.selectbox(
            "Select stock for detailed chart:",
            options=[r['symbol'] for r in results],
            format_func=lambda x: x.replace('.NS', '')
        )
        
        if selected_symbol:
            with st.spinner(f'Loading chart for {selected_symbol}...'):
                create_enhanced_chart(selected_symbol)
    
    else:
        # Welcome screen
        st.info("""
        ### 👋 Welcome to NSE F&O Scanner Professional v2.0
        
        **New Features:**
        - ✨ Smart caching for faster scans
        - 🔄 Automatic retry with exponential backoff
        - 🎯 Confidence scoring for patterns
        - 📊 Enhanced technical analysis
        - 🚀 Optimized parallel processing
        - 📱 Mobile-responsive design
        
        **How to use:**
        1. Select stocks to scan from the sidebar
        2. Adjust performance and filter settings
        3. Click "Start Scan" to begin
        4. View results and download Excel report
        
        Click the **Start Scan** button above to begin!
        """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; font-size: 0.875rem;'>
        <p>NSE F&O Scanner v2.0 | Enhanced with Smart Caching & Error Recovery</p>
        <p>⚠️ For educational purposes only. Not financial advice.</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
