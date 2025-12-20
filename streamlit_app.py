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
from typing import Dict, List, Tuple, Optional
warnings.filterwarnings('ignore')

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="NSE F&O Options Strategy Scanner Pro", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# PRODUCTION-READY THEME SYSTEM
def get_theme_css(strategy_type: str) -> Tuple[str, str]:
    """Get CSS theme based on strategy type with production styling"""
    if strategy_type == "Put Credit Spreads":
        primary_hue = "174"  # Teal
        icon = "📈"
    else:  # Call Credit Spreads
        primary_hue = "0"    # Red
        icon = "📉"
    
    return f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    :root {{
        --primary-50: hsl({primary_hue}, 62%, 98%);
        --primary-100: hsl({primary_hue}, 62%, 95%);
        --primary-500: hsl({primary_hue}, 62%, 47%);
        --primary-600: hsl({primary_hue}, 62%, 40%);
        --primary-700: hsl({primary_hue}, 62%, 33%);
        --primary-800: hsl({primary_hue}, 62%, 27%);
        --neutral-50: hsl(210, 20%, 98%);
        --neutral-100: hsl(210, 20%, 96%);
        --neutral-400: hsl(210, 12%, 71%);
        --neutral-600: hsl(210, 12%, 43%);
        --neutral-800: hsl(210, 18%, 23%);
        --surface: hsl(0, 0%, 100%);
        --border: hsl(210, 14%, 89%);
        --text-primary: hsl(210, 20%, 15%);
        --text-secondary: hsl(210, 12%, 43%);
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1);
    }}
    
    * {{ font-family: 'Inter', sans-serif; }}
    .main {{ background: var(--neutral-50); padding: 1.5rem 2rem; }}
    
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, var(--primary-50) 0%, var(--primary-100) 100%);
        border-right: 1px solid var(--primary-500);
        box-shadow: var(--shadow-md);
    }}
    
    .stButton > button {{
        background: var(--primary-600);
        color: white;
        border: none;
        border-radius: 0.5rem;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: var(--shadow-sm);
    }}
    
    .stButton > button:hover {{
        background: var(--primary-700);
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }}
    
    .quality-card {{
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        padding: 1.25rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-sm);
        transition: all 0.2s ease;
    }}
    
    .quality-card:hover {{
        box-shadow: var(--shadow-md);
        border-color: var(--primary-500);
    }}
    
    .quality-badge {{
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }}
    
    .quality-high {{ background: #dcfce7; color: #166534; }}
    .quality-medium {{ background: #fef3c7; color: #92400e; }}
    .quality-low {{ background: #fecaca; color: #991b1b; }}
    
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
    }}
    
    .metric-item {{
        text-align: center;
        padding: 0.75rem;
        background: var(--neutral-50);
        border-radius: 0.5rem;
        border: 1px solid var(--border);
    }}
</style>
""", icon

# ADVANCED CACHING SYSTEM WITH ERROR HANDLING
@st.cache_data(ttl=300, show_spinner=False)
def get_nse_fno_stocks_cached() -> List[str]:
    """Production-ready F&O stock list with fallback"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Connection': 'keep-alive',
            'Referer': 'https://www.nseindia.com/'
        }
        
        session = requests.Session()
        session.headers.update(headers)
        session.get('https://www.nseindia.com/', timeout=10)
        
        response = session.get(
            'https://www.nseindia.com/api/equity-stockIndices?index=NIFTY%20500', 
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            stocks = [item['symbol'] + '.NS' for item in data if 'symbol' in item][:200]
            logger.info(f"Successfully fetched {len(stocks)} F&O stocks from NSE API")
            return stocks
            
    except Exception as e:
        logger.warning(f"NSE API failed: {e}, using backup list")
    
    # Comprehensive backup - top 200 F&O stocks
    backup_stocks = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'HINDUNILVR.NS', 'SBIN.NS', 'BHARTIARTL.NS', 'ITC.NS', 'KOTAKBANK.NS',
        'LT.NS', 'AXISBANK.NS', 'ASIANPAINT.NS', 'MARUTI.NS', 'BAJFINANCE.NS',
        'HCLTECH.NS', 'WIPRO.NS', 'ULTRACEMCO.NS', 'TITAN.NS', 'NESTLEIND.NS',
        'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'TATAMOTORS.NS', 'JSWSTEEL.NS',
        'TECHM.NS', 'SUNPHARMA.NS', 'INDUSINDBK.NS', 'M&M.NS', 'BAJAJ-AUTO.NS',
        'COALINDIA.NS', 'TATASTEEL.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'GRASIM.NS',
        'CIPLA.NS', 'DRREDDY.NS', 'EICHERMOT.NS', 'BPCL.NS', 'BRITANNIA.NS',
        'TATACONSUM.NS', 'IOC.NS', 'HINDALCO.NS', 'UPL.NS', 'APOLLOHOSP.NS',
        'DIVISLAB.NS', 'HEROMOTOCO.NS', 'SHREECEM.NS', 'PIDILITIND.NS', 'GODREJCP.NS',
        'BAJAJFINSV.NS', 'HDFCLIFE.NS', 'SBILIFE.NS', 'ICICIPRULI.NS', 'LTIM.NS',
        'LTTS.NS', 'MINDTREE.NS', 'MPHASIS.NS', 'PERSISTENT.NS', 'COFORGE.NS',
        'OFSS.NS', 'BANKBARODA.NS', 'PNB.NS', 'CANBK.NS', 'IDFCFIRSTB.NS',
        'FEDERALBNK.NS', 'AUBANK.NS', 'BANDHANBNK.NS', 'RBLBANK.NS', 'PFC.NS',
        'RECLTD.NS', 'IRCTC.NS', 'CONCOR.NS', 'SIEMENS.NS', 'ABB.NS',
        'BOSCHLTD.NS', 'HAVELLS.NS', 'VOLTAS.NS', 'WHIRLPOOL.NS', 'CROMPTON.NS',
        'DIXON.NS', 'AMBER.NS', 'POLYCAB.NS', 'KEI.NS', 'CUMMINSIND.NS',
        'ASHOKLEY.NS', 'ESCORTS.NS', 'TVSMOTOR.NS', 'BALKRISIND.NS', 'MRF.NS',
        'APOLLOTYRE.NS', 'CEAT.NS', 'JK.NS', 'MOTHERSON.NS', 'RAMCOCEM.NS',
        'ACC.NS', 'AMBUJACEM.NS', 'JKCEMENT.NS', 'DALMIA.NS', 'HEIDELBERG.NS',
        'SAIL.NS', 'JINDALSTEL.NS', 'VEDL.NS', 'NMDC.NS', 'NATIONALUM.NS',
        'HINDZINC.NS', 'RATNAMANI.NS', 'APL.NS', 'WELCORP.NS', 'WELSPUNIND.NS',
        'DEEPAKNTR.NS', 'GNFC.NS', 'BALRAMCHIN.NS', 'NOCIL.NS', 'AAVAS.NS',
        'LICHSGFIN.NS', 'CHOLAFIN.NS', 'L&TFH.NS', 'SRTRANSFIN.NS', 'MUTHOOTFIN.NS',
        'MANAPPURAM.NS', 'PEL.NS', 'WHIRLPOOL.NS', 'BLUESTARCO.NS', 'CROMPTON.NS',
        'KANSAINER.NS', 'THERMAX.NS', 'CUMMINSIND.NS', 'BHEL.NS', 'BEL.NS',
        'HAL.NS', 'BEML.NS', 'COCHINSHIP.NS', 'GRINDWELL.NS', 'SKFINDIA.NS',
        'TIMKEN.NS', 'SCHAEFFLER.NS', 'FINEORG.NS', 'NAVINFLUOR.NS', 'SRF.NS',
        'ATUL.NS', 'LALPATHLAB.NS', 'METROPOLIS.NS', 'THYROCARE.NS', 'FORTIS.NS',
        'MAXHEALTH.NS', 'NARAYANA.NS', 'ZYDUSLIFE.NS', 'TORNTPHARM.NS', 'ALKEM.NS',
        'LUPIN.NS', 'CADILAHC.NS', 'GLENMARK.NS', 'BIOCON.NS', 'AUROPHARMA.NS',
        'REDDY.NS', 'PFIZER.NS', 'GSK.NS', 'ABBOTT.NS', 'SANOFI.NS',
        'NOVARTIS.NS', 'CIPLA.NS', 'SUNPHARMA.NS', 'DRREDDY.NS', 'DIVISLAB.NS',
        'JUBLFOOD.NS', 'TATACONSUM.NS', 'MARICO.NS', 'GODREJCP.NS', 'EMAMILTD.NS',
        'DABUR.NS', 'COLPAL.NS', 'PGHH.NS', 'GILLETTE.NS', 'VBL.NS',
        'CCL.NS', 'RADICO.NS', 'UBL.NS', 'GLOBUSSPR.NS', 'RELAXO.NS',
        'BATA.NS', 'CENTRALBK.NS', 'UNIONBANK.NS', 'INDIANB.NS', 'CANBK.NS',
        'BANKINDIA.NS', 'MAHABANK.NS', 'JKBANK.NS', 'SOUTHBANK.NS', 'IDBI.NS',
        'ORIENTBANK.NS', 'IOB.NS', 'SYNDIBANK.NS', 'ALLAHABAD.NS', 'CORPBANK.NS',
        'DENABANK.NS', 'VIJAYABANK.NS', 'ANDHRABANK.NS', 'CANARABANK.NS', 'UCOBANK.NS',
        'INDIANHUME.NS', 'BERGEPAINT.NS', 'KANSAINER.NS', 'ASTRAL.NS', 'INDIGO.NS',
        'SPICEJET.NS', 'JETAIRWAYS.NS', 'FEDERALBNK.NS', 'SOUTHBANK.NS', 'DMART.NS'
    ]
    
    logger.info(f"Using backup list with {len(backup_stocks)} F&O stocks")
    return backup_stocks

@st.cache_data(ttl=900, show_spinner=False)
def get_stock_data_cached(symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """Enhanced stock data with comprehensive technical indicators"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)
        
        if data.empty or len(data) < 50:
            return None
            
        if 'Volume' not in data.columns or data['Volume'].isna().all():
            return None
            
        # Enhanced technical indicators
        data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
        data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
        data['SMA_200'] = ta.trend.sma_indicator(data['Close'], window=200)
        data['EMA_12'] = ta.trend.ema_indicator(data['Close'], window=12)
        data['EMA_26'] = ta.trend.ema_indicator(data['Close'], window=26)
        data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
        data['MACD'] = ta.trend.macd_diff(data['Close'])
        data['BB_upper'] = ta.volatility.bollinger_hband(data['Close'])
        data['BB_lower'] = ta.volatility.bollinger_lband(data['Close'])
        data['Volume_SMA'] = ta.trend.sma_indicator(data['Volume'], window=20)
        
        # PRODUCTION ENHANCEMENT: ATR and Volatility Metrics
        data['ATR'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'], window=20)
        data['ATR_14'] = ta.volatility.average_true_range(data['High'], data['Low'], data['Close'], window=14)
        
        # Enhanced volume indicators
        data['Volume_Ratio'] = data['Volume'] / data['Volume_SMA']
        data['Price_Volume_Trend'] = ta.volume.volume_price_trend(data['Close'], data['Volume'])
        
        # Volatility indicators
        data['Volatility_20'] = data['Close'].rolling(20).std()
        data['Volatility_Ratio'] = data['Volatility_20'] / data['Volatility_20'].rolling(60).mean()
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def get_market_sentiment_cached() -> Dict:
    """Enhanced market sentiment with VIX and multiple indices"""
    sentiment_data = {}
    
    try:
        # Get multiple indices for comprehensive sentiment
        indices = {
            'nifty': '^NSEI',
            'bank_nifty': '^NSEBANK',
            'vix': '^INDIAVIX'
        }
        
        for name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period='10d')
                
                if not data.empty and len(data) >= 2:
                    current = data['Close'].iloc[-1]
                    previous = data['Close'].iloc[-2]
                    change_pct = ((current - previous) / previous) * 100
                    
                    # Calculate 5-day and 10-day changes
                    change_5d = ((current - data['Close'].iloc[-6]) / data['Close'].iloc[-6]) * 100 if len(data) >= 6 else change_pct
                    change_10d = ((current - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
                    
                    sentiment_data[name] = {
                        'level': current,
                        'change_1d': change_pct,
                        'change_5d': change_5d,
                        'change_10d': change_10d,
                        'volatility': data['Close'].rolling(10).std().iloc[-1]
                    }
            except Exception as e:
                logger.warning(f"Failed to fetch {name}: {e}")
                continue
        
        logger.info(f"Market sentiment data retrieved for {len(sentiment_data)} indices")
        return sentiment_data
        
    except Exception as e:
        logger.error(f"Market sentiment fetch failed: {e}")
        return {}

# ADVANCED QUALITY FILTERS
class AdvancedQualityFilters:
    """Production-ready quality filters for noise reduction"""
    
    def __init__(self):
        self.min_market_cap = 500  # Crores
        self.min_volume_threshold = 100000  # Shares
        self.max_volatility_ratio = 3.0  # vs historical
        
    def liquidity_quality_check(self, data: pd.DataFrame) -> Tuple[bool, Dict]:
        """Comprehensive liquidity validation"""
        try:
            if len(data) < 20:
                return False, {'reason': 'Insufficient data'}
            
            # Average volume check
            avg_volume_20d = data['Volume'].tail(20).mean()
            current_volume = data['Volume'].iloc[-1]
            
            # Volume consistency check
            volume_consistency = (data['Volume'].tail(10) > 50000).sum() >= 8  # 8 out of 10 days
            
            # Price stability (not penny stock behavior)
            price_stability = data['Close'].iloc[-1] > 10  # Above ₹10
            
            quality_metrics = {
                'avg_volume_20d': avg_volume_20d,
                'current_volume': current_volume,
                'volume_consistency': volume_consistency,
                'price_stability': price_stability,
                'min_volume_met': avg_volume_20d >= self.min_volume_threshold
            }
            
            liquidity_score = 0
            if avg_volume_20d >= self.min_volume_threshold: liquidity_score += 30
            if volume_consistency: liquidity_score += 25
            if price_stability: liquidity_score += 20
            if current_volume > avg_volume_20d * 0.5: liquidity_score += 25  # Not too low volume
            
            quality_metrics['liquidity_score'] = liquidity_score
            
            return liquidity_score >= 70, quality_metrics
            
        except Exception as e:
            logger.error(f"Liquidity check failed: {e}")
            return False, {'reason': 'Error in liquidity check'}
    
    def volatility_significance_filter(self, data: pd.DataFrame, move_percentage: float) -> Tuple[bool, Dict]:
        """Filter based on volatility significance"""
        try:
            if len(data) < 20:
                return False, {'reason': 'Insufficient data'}
            
            atr_20 = data['ATR'].iloc[-1] if 'ATR' in data.columns else None
            current_price = data['Close'].iloc[-1]
            
            if atr_20 is None or pd.isna(atr_20):
                return False, {'reason': 'ATR calculation failed'}
            
            # Convert ATR to percentage
            atr_percentage = (atr_20 / current_price) * 100
            
            # Move must be at least 1.5x ATR to be significant
            significance_threshold = atr_percentage * 1.5
            is_significant = abs(move_percentage) >= significance_threshold
            
            # Volatility regime check
            volatility_ratio = data['Volatility_Ratio'].iloc[-1] if 'Volatility_Ratio' in data.columns else 1.0
            normal_volatility = volatility_ratio <= self.max_volatility_ratio
            
            quality_metrics = {
                'atr_percentage': atr_percentage,
                'move_percentage': abs(move_percentage),
                'significance_threshold': significance_threshold,
                'is_significant': is_significant,
                'volatility_ratio': volatility_ratio,
                'normal_volatility': normal_volatility
            }
            
            significance_score = 0
            if is_significant: significance_score += 50
            if normal_volatility: significance_score += 30
            if abs(move_percentage) >= atr_percentage * 2: significance_score += 20  # Very significant move
            
            quality_metrics['significance_score'] = significance_score
            
            return significance_score >= 70, quality_metrics
            
        except Exception as e:
            logger.error(f"Volatility significance check failed: {e}")
            return False, {'reason': 'Error in volatility check'}
    
    def pattern_maturity_check(self, data: pd.DataFrame, pattern_name: str, pattern_start_idx: int) -> Tuple[bool, Dict]:
        """Ensure pattern had sufficient time to develop"""
        try:
            min_formation_days = {
                'Cup and Handle': 15,
                'Ascending Triangle': 12,
                'Bull Flag': 5,
                'Double Bottom': 10,
                'Inverse Head and Shoulders': 12,
                'Head and Shoulders': 12,
                'Descending Triangle': 12,
                'Bear Flag': 5,
                'Double Top': 10,
                'Rising Wedge': 8
            }
            
            required_days = min_formation_days.get(pattern_name, 8)
            current_idx = len(data) - 1
            formation_days = current_idx - pattern_start_idx
            
            is_mature = formation_days >= required_days
            
            # Pattern quality based on formation time
            if formation_days >= required_days * 1.5:
                maturity_score = 100
            elif formation_days >= required_days:
                maturity_score = 80
            else:
                maturity_score = max(0, (formation_days / required_days) * 60)
            
            quality_metrics = {
                'required_days': required_days,
                'formation_days': formation_days,
                'is_mature': is_mature,
                'maturity_score': maturity_score
            }
            
            return is_mature, quality_metrics
            
        except Exception as e:
            logger.error(f"Pattern maturity check failed: {e}")
            return False, {'reason': 'Error in maturity check'}
    
    def multi_timeframe_alignment(self, daily_data: pd.DataFrame, weekly_data: Optional[pd.DataFrame], 
                                strategy_type: str) -> Tuple[bool, Dict]:
        """Multi-timeframe trend alignment validation"""
        try:
            alignment_metrics = {}
            
            # Daily trend
            current_price = daily_data['Close'].iloc[-1]
            sma_20 = daily_data['SMA_20'].iloc[-1]
            sma_50 = daily_data['SMA_50'].iloc[-1]
            sma_200 = daily_data['SMA_200'].iloc[-1] if 'SMA_200' in daily_data.columns else sma_50
            
            daily_trend = 'NEUTRAL'
            if current_price > sma_20 > sma_50:
                daily_trend = 'BULLISH'
            elif current_price < sma_20 < sma_50:
                daily_trend = 'BEARISH'
            
            alignment_metrics['daily_trend'] = daily_trend
            
            # Weekly trend if available
            weekly_trend = 'UNKNOWN'
            if weekly_data is not None and len(weekly_data) >= 10:
                try:
                    weekly_current = weekly_data['Close'].iloc[-1]
                    weekly_sma_10 = weekly_data['SMA_10'].iloc[-1] if 'SMA_10' in weekly_data.columns else weekly_current
                    
                    if not pd.isna(weekly_sma_10):
                        if weekly_current > weekly_sma_10:
                            weekly_trend = 'BULLISH'
                        elif weekly_current < weekly_sma_10:
                            weekly_trend = 'BEARISH'
                        else:
                            weekly_trend = 'NEUTRAL'
                except Exception:
                    weekly_trend = 'UNKNOWN'
            
            alignment_metrics['weekly_trend'] = weekly_trend
            
            # Alignment scoring based on strategy
            alignment_score = 0
            
            if strategy_type == "Put Credit Spreads":
                # Want bullish alignment
                if daily_trend == 'BULLISH': alignment_score += 40
                elif daily_trend == 'NEUTRAL': alignment_score += 20
                
                if weekly_trend == 'BULLISH': alignment_score += 35
                elif weekly_trend == 'NEUTRAL': alignment_score += 15
                elif weekly_trend == 'UNKNOWN': alignment_score += 10
                
                # Long-term trend bonus
                if not pd.isna(sma_200) and current_price > sma_200: alignment_score += 25
                
            else:  # Call Credit Spreads
                # Want bearish alignment
                if daily_trend == 'BEARISH': alignment_score += 40
                elif daily_trend == 'NEUTRAL': alignment_score += 20
                
                if weekly_trend == 'BEARISH': alignment_score += 35
                elif weekly_trend == 'NEUTRAL': alignment_score += 15
                elif weekly_trend == 'UNKNOWN': alignment_score += 10
                
                # Long-term trend bonus
                if not pd.isna(sma_200) and current_price < sma_200: alignment_score += 25
            
            alignment_metrics['alignment_score'] = alignment_score
            alignment_metrics['is_aligned'] = alignment_score >= 60
            
            return alignment_score >= 60, alignment_metrics
            
        except Exception as e:
            logger.error(f"Multi-timeframe alignment check failed: {e}")
            return False, {'reason': 'Error in alignment check'}
    
    def market_regime_filter(self, strategy_type: str, sentiment_data: Dict) -> Tuple[bool, Dict]:
        """Market regime-based filtering"""
        try:
            regime_metrics = {}
            
            # VIX-based regime detection
            vix_level = 20  # Default
            if 'vix' in sentiment_data:
                vix_level = sentiment_data['vix']['level']
            
            # Market direction from indices
            market_direction = 'NEUTRAL'
            if 'nifty' in sentiment_data:
                nifty_5d = sentiment_data['nifty'].get('change_5d', 0)
                if nifty_5d > 2:
                    market_direction = 'BULLISH'
                elif nifty_5d < -2:
                    market_direction = 'BEARISH'
            
            regime_metrics['vix_level'] = vix_level
            regime_metrics['market_direction'] = market_direction
            
            # Regime suitability scoring
            regime_score = 0
            
            if strategy_type == "Put Credit Spreads":
                # Prefer low VIX and bullish/neutral market
                if vix_level <= 20: regime_score += 30
                elif vix_level <= 25: regime_score += 15
                
                if market_direction == 'BULLISH': regime_score += 40
                elif market_direction == 'NEUTRAL': regime_score += 25
                elif market_direction == 'BEARISH': regime_score += 5
                
                # Additional VIX scoring for PCS
                if vix_level <= 15: regime_score += 30  # Very low VIX is excellent for PCS
                
            else:  # Call Credit Spreads
                # Prefer higher VIX and bearish/neutral market
                if vix_level >= 20: regime_score += 30
                elif vix_level >= 15: regime_score += 15
                
                if market_direction == 'BEARISH': regime_score += 40
                elif market_direction == 'NEUTRAL': regime_score += 25
                elif market_direction == 'BULLISH': regime_score += 5
                
                # Additional VIX scoring for CCS
                if vix_level >= 25: regime_score += 30  # High VIX is excellent for CCS
            
            regime_metrics['regime_score'] = regime_score
            regime_metrics['regime_suitable'] = regime_score >= 50
            
            return regime_score >= 50, regime_metrics
            
        except Exception as e:
            logger.error(f"Market regime filter failed: {e}")
            return False, {'reason': 'Error in regime filter'}
    
    def calculate_comprehensive_quality_score(self, pattern_data: Dict, all_metrics: Dict) -> Dict:
        """Calculate comprehensive quality score from all factors"""
        try:
            quality_factors = {
                'pattern_strength': pattern_data.get('strength', 0) * 0.20,  # 20%
                'liquidity_score': all_metrics.get('liquidity', {}).get('liquidity_score', 0) * 0.20,  # 20%
                'significance_score': all_metrics.get('volatility', {}).get('significance_score', 0) * 0.20,  # 20%
                'alignment_score': all_metrics.get('timeframe', {}).get('alignment_score', 0) * 0.20,  # 20%
                'regime_score': all_metrics.get('regime', {}).get('regime_score', 0) * 0.10,  # 10%
                'maturity_score': all_metrics.get('maturity', {}).get('maturity_score', 80) * 0.10   # 10%
            }
            
            total_quality_score = sum(quality_factors.values())
            
            # Quality classification
            if total_quality_score >= 85:
                quality_grade = 'PREMIUM'
            elif total_quality_score >= 75:
                quality_grade = 'HIGH'
            elif total_quality_score >= 65:
                quality_grade = 'MEDIUM'
            else:
                quality_grade = 'LOW'
            
            return {
                'total_score': total_quality_score,
                'grade': quality_grade,
                'factors': quality_factors,
                'passed_filters': sum(1 for metrics in all_metrics.values() 
                                    if isinstance(metrics, dict) and metrics.get('is_aligned', False) or 
                                       metrics.get('regime_suitable', False) or 
                                       metrics.get('is_significant', False))
            }
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return {
                'total_score': 0,
                'grade': 'ERROR',
                'factors': {},
                'passed_filters': 0
            }

# ENHANCED SCANNER CLASS WITH QUALITY FILTERS
class ProductionOptionsScanner:
    """Production-ready scanner with comprehensive quality filters"""
    
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.quality_filters = AdvancedQualityFilters()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def analyze_market_sentiment(self, strategy_type: str) -> Dict:
        """Enhanced market sentiment analysis"""
        sentiment_data = get_market_sentiment_cached()
        
        if not sentiment_data:
            return {
                'overall': {
                    'sentiment': 'UNKNOWN',
                    'recommendation': 'Data unavailable - trade with caution',
                    'risk_level': 'HIGH',
                    'confidence': 0
                }
            }
        
        # Enhanced sentiment scoring
        sentiment_scores = {
            "BEARISH_STRONG": 4 if strategy_type == "Call Credit Spreads" else 0,
            "BEARISH": 3 if strategy_type == "Call Credit Spreads" else 1,
            "NEUTRAL": 2,
            "BULLISH": 1 if strategy_type == "Call Credit Spreads" else 3,
            "BULLISH_STRONG": 0 if strategy_type == "Call Credit Spreads" else 4
        }
        
        def get_sentiment_level(change_1d: float, change_5d: float) -> str:
            # Enhanced sentiment using multiple timeframes
            if change_5d <= -3 and change_1d <= -1:
                return "BEARISH_STRONG"
            elif change_5d <= -1.5 or change_1d <= -0.8:
                return "BEARISH"
            elif -1.5 < change_5d < 1.5 and -0.8 < change_1d < 0.8:
                return "NEUTRAL"
            elif change_5d >= 1.5 or change_1d >= 0.8:
                return "BULLISH"
            else:
                return "BULLISH_STRONG"
        
        # Process sentiment data
        for index_name, data in sentiment_data.items():
            if 'change_1d' in data and 'change_5d' in data:
                sentiment_level = get_sentiment_level(data['change_1d'], data['change_5d'])
                data['sentiment'] = sentiment_level
        
        # Overall assessment
        nifty_sentiment = sentiment_data.get('nifty', {}).get('sentiment', 'NEUTRAL')
        bank_sentiment = sentiment_data.get('bank_nifty', {}).get('sentiment', 'NEUTRAL')
        
        nifty_score = sentiment_scores.get(nifty_sentiment, 2)
        bank_score = sentiment_scores.get(bank_sentiment, 2)
        overall_score = (nifty_score * 0.6) + (bank_score * 0.4)
        
        # Enhanced recommendations with confidence
        confidence = 0
        if overall_score >= 3.5:
            overall_sentiment = "BULLISH" if strategy_type == "Put Credit Spreads" else "BEARISH"
            recommendation = f"Excellent for {strategy_type}"
            risk_level = "LOW"
            confidence = 90
        elif overall_score >= 2.8:
            overall_sentiment = "BULLISH" if strategy_type == "Put Credit Spreads" else "BEARISH"
            recommendation = f"Good for {strategy_type}"
            risk_level = "LOW-MEDIUM"
            confidence = 75
        elif overall_score >= 2.2:
            overall_sentiment = "NEUTRAL"
            recommendation = f"Moderate {strategy_type.split()[0]} opportunities"
            risk_level = "MEDIUM"
            confidence = 60
        else:
            overall_sentiment = "BEARISH" if strategy_type == "Put Credit Spreads" else "BULLISH"
            opposite_strategy = "Call Credit Spreads" if strategy_type == "Put Credit Spreads" else "Put Credit Spreads"
            recommendation = f"Consider {opposite_strategy} instead"
            risk_level = "HIGH"
            confidence = 40
        
        sentiment_data['overall'] = {
            'sentiment': overall_sentiment,
            'score': overall_score,
            'recommendation': recommendation,
            'risk_level': risk_level,
            'confidence': confidence
        }
        
        return sentiment_data
    
    def detect_patterns_with_quality_filters(self, data: pd.DataFrame, symbol: str, 
                                          strategy_type: str, filters: Dict) -> List[Dict]:
        """Enhanced pattern detection with comprehensive quality filtering"""
        if data is None or len(data) < 50:
            return []
        
        patterns_found = []
        
        # Get weekly data for multi-timeframe analysis
        weekly_data = get_weekly_stock_data_cached(symbol)
        
        # Pattern selection based on strategy
        if strategy_type == "Put Credit Spreads":
            pattern_methods = [
                ('Cup and Handle', self._detect_cup_and_handle),
                ('Ascending Triangle', self._detect_ascending_triangle),
                ('Bull Flag', self._detect_bull_flag),
                ('Double Bottom', self._detect_double_bottom),
                ('Inverse Head and Shoulders', self._detect_inverse_head_shoulders),
                ('Bullish Engulfing', self._detect_bullish_engulfing),
                ('Morning Star', self._detect_morning_star),
                ('Hammer', self._detect_hammer)
            ]
        else:
            pattern_methods = [
                ('Head and Shoulders', self._detect_head_shoulders),
                ('Descending Triangle', self._detect_descending_triangle),
                ('Bear Flag', self._detect_bear_flag),
                ('Double Top', self._detect_double_top),
                ('Rising Wedge', self._detect_rising_wedge),
                ('Bearish Engulfing', self._detect_bearish_engulfing),
                ('Evening Star', self._detect_evening_star),
                ('Shooting Star', self._detect_shooting_star)
            ]
        
        for pattern_name, detect_method in pattern_methods:
            try:
                detected, strength, pattern_start_idx = detect_method(data)
                
                if not detected or strength < filters.get('min_strength', 70):
                    continue
                
                # COMPREHENSIVE QUALITY FILTERING
                all_quality_metrics = {}
                quality_passed = True
                
                # 1. Liquidity Quality Check
                liquidity_passed, liquidity_metrics = self.quality_filters.liquidity_quality_check(data)
                all_quality_metrics['liquidity'] = liquidity_metrics
                if not liquidity_passed and filters.get('strict_quality', True):
                    continue
                
                # 2. Pattern Maturity Check
                maturity_passed, maturity_metrics = self.quality_filters.pattern_maturity_check(
                    data, pattern_name, pattern_start_idx
                )
                all_quality_metrics['maturity'] = maturity_metrics
                
                # 3. Multi-timeframe Alignment
                alignment_passed, alignment_metrics = self.quality_filters.multi_timeframe_alignment(
                    data, weekly_data, strategy_type
                )
                all_quality_metrics['timeframe'] = alignment_metrics
                
                # 4. Market Regime Filter
                sentiment_data = get_market_sentiment_cached()
                regime_passed, regime_metrics = self.quality_filters.market_regime_filter(
                    strategy_type, sentiment_data
                )
                all_quality_metrics['regime'] = regime_metrics
                
                # 5. Volume and Direction Confirmation
                volume_valid, volume_ratio = self._check_volume_criteria(data, filters.get('volume_ratio', 1.2))
                direction_confirmed, direction_details = self._detect_current_day_direction(
                    data, strategy_type, filters.get('lookback_days', 20)
                )
                
                # 6. Volatility Significance Filter
                move_percentage = direction_details.get('move_percentage', 0)
                significance_passed, significance_metrics = self.quality_filters.volatility_significance_filter(
                    data, move_percentage
                )
                all_quality_metrics['volatility'] = significance_metrics
                
                # Calculate final strength with quality adjustments
                base_strength = strength
                
                # Quality bonuses
                if liquidity_passed: base_strength += 5
                if maturity_passed: base_strength += 3
                if alignment_passed: base_strength += 8
                if regime_passed: base_strength += 5
                if significance_passed: base_strength += 4
                if direction_confirmed: base_strength += 10
                if volume_valid and volume_ratio >= 2.0: base_strength += 8
                
                final_strength = min(98, base_strength)
                
                # Get pattern-specific data
                pattern_info = self._get_pattern_data(pattern_name, strategy_type)
                
                # Calculate comprehensive quality score
                pattern_data_for_quality = {
                    'strength': final_strength,
                    'success_rate': pattern_info['success_rate'],
                    'suitability': pattern_info['suitability']
                }
                
                quality_assessment = self.quality_filters.calculate_comprehensive_quality_score(
                    pattern_data_for_quality, all_quality_metrics
                )
                
                # Apply quality threshold - only include high-quality patterns
                min_quality_score = filters.get('min_quality_score', 65)
                if quality_assessment['total_score'] < min_quality_score:
                    continue
                
                # Create comprehensive pattern result
                pattern_result = {
                    'symbol': symbol,
                    'pattern': pattern_name,
                    'strength': final_strength,
                    'success_rate': pattern_info['success_rate'],
                    'suitability': pattern_info['suitability'],
                    'current_price': data['Close'].iloc[-1],
                    'direction_confirmed': direction_confirmed,
                    'volume_confirmed': volume_valid,
                    'volume_ratio': volume_ratio,
                    
                    # Enhanced quality metrics
                    'quality_score': quality_assessment['total_score'],
                    'quality_grade': quality_assessment['grade'],
                    'quality_factors': quality_assessment['factors'],
                    
                    # Detailed analysis
                    'direction_details': direction_details,
                    'liquidity_metrics': liquidity_metrics,
                    'volatility_metrics': significance_metrics,
                    'timeframe_metrics': alignment_metrics,
                    'regime_metrics': regime_metrics,
                    'maturity_metrics': maturity_metrics,
                    
                    # Risk assessment
                    'risk_score': self._calculate_risk_score(data, pattern_name, direction_details),
                    'confidence_level': self._calculate_confidence_level(quality_assessment, all_quality_metrics),
                    
                    # Additional context
                    'daily_strength': strength,
                    'pattern_details': pattern_info.get('details', {})
                }
                
                patterns_found.append(pattern_result)
                
            except Exception as e:
                logger.error(f"Pattern detection error for {pattern_name} on {symbol}: {e}")
                continue
        
        return patterns_found
    
    def _calculate_risk_score(self, data: pd.DataFrame, pattern_name: str, direction_details: Dict) -> int:
        """Calculate risk score for the pattern (0-100, lower is better)"""
        try:
            risk_score = 50  # Base risk
            
            # Volatility risk
            volatility_ratio = data.get('Volatility_Ratio', pd.Series([1.0])).iloc[-1]
            if volatility_ratio > 2: risk_score += 20
            elif volatility_ratio > 1.5: risk_score += 10
            elif volatility_ratio < 0.8: risk_score -= 10
            
            # Volume risk
            volume_ratio = direction_details.get('volume_ratio', 1.0)
            if volume_ratio < 1: risk_score += 15
            elif volume_ratio > 3: risk_score -= 10
            
            # Pattern-specific risk
            pattern_risk = {
                'Cup and Handle': -10,  # Generally reliable
                'Head and Shoulders': -5,
                'Flag': -5,
                'Engulfing': 5,  # More risky single candle pattern
                'Hammer': 10,
                'Shooting Star': 10
            }
            
            for pattern_key, risk_adj in pattern_risk.items():
                if pattern_key.lower() in pattern_name.lower():
                    risk_score += risk_adj
                    break
            
            return max(0, min(100, risk_score))
            
        except Exception:
            return 50  # Default medium risk
    
    def _calculate_confidence_level(self, quality_assessment: Dict, all_metrics: Dict) -> str:
        """Calculate confidence level based on quality metrics"""
        try:
            quality_score = quality_assessment.get('total_score', 0)
            passed_filters = quality_assessment.get('passed_filters', 0)
            
            if quality_score >= 90 and passed_filters >= 4:
                return "VERY HIGH"
            elif quality_score >= 80 and passed_filters >= 3:
                return "HIGH"
            elif quality_score >= 70 and passed_filters >= 2:
                return "MEDIUM"
            elif quality_score >= 60:
                return "LOW"
            else:
                return "VERY LOW"
                
        except Exception:
            return "UNKNOWN"
    
    # Pattern detection methods (simplified versions for production)
    def _detect_cup_and_handle(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect cup and handle pattern"""
        if len(data) < 30:
            return False, 0, 0
        
        try:
            recent_data = data.tail(25)
            pattern_start = len(data) - 25
            
            # Simple cup and handle detection
            mid_point = len(recent_data) // 2
            early_high = recent_data['High'].iloc[:5].max()
            mid_low = recent_data['Low'].iloc[mid_point-3:mid_point+3].min()
            late_high = recent_data['High'].iloc[-5:].max()
            current_price = data['Close'].iloc[-1]
            
            # Cup depth validation
            cup_depth = ((early_high - mid_low) / early_high) * 100
            if cup_depth < 8 or cup_depth > 35:
                return False, 0, pattern_start
            
            # Handle formation
            handle_pullback = ((late_high - current_price) / late_high) * 100
            if 0 < handle_pullback < 10:
                strength = 85 + min(10, int((35 - cup_depth) / 2))
                return True, strength, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_ascending_triangle(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect ascending triangle pattern"""
        if len(data) < 15:
            return False, 0, 0
        
        try:
            recent_data = data.tail(12)
            pattern_start = len(data) - 12
            
            resistance_level = recent_data['High'].max()
            current_price = data['Close'].iloc[-1]
            
            # Flat resistance check
            high_variance = recent_data['High'].std() / recent_data['High'].mean()
            flat_resistance = high_variance < 0.025
            
            # Rising lows check
            early_lows = recent_data['Low'].iloc[:4].mean()
            late_lows = recent_data['Low'].iloc[-4:].mean()
            rising_support = late_lows > early_lows * 1.02
            
            # Breakout confirmation
            resistance_broken = current_price > resistance_level * 1.008
            
            if flat_resistance and rising_support and resistance_broken:
                strength = 82
                if current_price > resistance_level * 1.015: strength += 8
                return True, strength, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_bull_flag(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect bull flag pattern"""
        if len(data) < 12:
            return False, 0, 0
        
        try:
            pattern_start = len(data) - 10
            
            # Prior bullish move
            price_8_ago = data['Close'].iloc[-9]
            current_price = data['Close'].iloc[-1]
            prior_rally = ((current_price - price_8_ago) / price_8_ago) > 0.025
            
            # Flag consolidation
            recent_data = data.tail(6)
            consolidation_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Low'].min()
            small_range = consolidation_range < 0.06
            
            # Breakout
            flag_high = recent_data['High'].max()
            breakout = current_price > flag_high * 1.005
            
            if prior_rally and small_range and breakout:
                return True, 84, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_double_bottom(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect double bottom pattern"""
        if len(data) < 15:
            return False, 0, 0
        
        try:
            recent_data = data.tail(12)
            pattern_start = len(data) - 12
            
            # Find valleys
            lows = recent_data['Low']
            valleys = []
            
            for i in range(1, len(lows)-1):
                if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1]:
                    valleys.append(lows.iloc[i])
            
            if len(valleys) >= 2:
                first_valley, second_valley = valleys[0], valleys[-1]
                
                # Similar valleys
                if abs(first_valley - second_valley) / min(first_valley, second_valley) <= 0.04:
                    current_price = data['Close'].iloc[-1]
                    peak = recent_data['High'].max()
                    
                    # Breakout confirmation
                    if current_price > peak * 1.01:
                        return True, 81, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    # Add other pattern detection methods with similar structure...
    def _detect_inverse_head_shoulders(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect inverse head and shoulders"""
        if len(data) < 20:
            return False, 0, 0
        
        try:
            recent_data = data.tail(15)
            pattern_start = len(data) - 15
            
            # Simple inverse H&S detection
            lows = recent_data['Low']
            valleys = []
            
            for i in range(2, len(lows)-2):
                if (lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and
                    lows.iloc[i] < lows.iloc[i-2] and lows.iloc[i] < lows.iloc[i+2]):
                    valleys.append((i, lows.iloc[i]))
            
            if len(valleys) >= 3:
                valleys.sort(key=lambda x: x[1])  # Sort by price (lowest first)
                head_idx, head_price = valleys[0]
                
                current_price = data['Close'].iloc[-1]
                neckline = recent_data['High'].max()
                
                if current_price > neckline * 1.02:
                    return True, 88, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_bullish_engulfing(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect bullish engulfing pattern"""
        if len(data) < 2:
            return False, 0, 0
        
        try:
            candle1 = data.iloc[-2]
            candle2 = data.iloc[-1]
            pattern_start = len(data) - 2
            
            # Pattern criteria
            bearish_1 = candle1['Close'] < candle1['Open']
            bullish_2 = candle2['Close'] > candle2['Open']
            engulfs = (candle2['Open'] < candle1['Close'] and candle2['Close'] > candle1['Open'])
            
            volume_increase = data['Volume'].iloc[-1] > data['Volume'].iloc[-2] * 1.2
            
            if bearish_1 and bullish_2 and engulfs:
                strength = 76
                if volume_increase: strength += 8
                return True, strength, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_morning_star(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect morning star pattern"""
        if len(data) < 3:
            return False, 0, 0
        
        try:
            candle1 = data.iloc[-3]
            candle2 = data.iloc[-2]
            candle3 = data.iloc[-1]
            pattern_start = len(data) - 3
            
            # Pattern criteria
            bearish_1 = candle1['Close'] < candle1['Open']
            large_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.6
            
            small_body_2 = abs(candle2['Close'] - candle2['Open']) < (candle2['High'] - candle2['Low']) * 0.3
            
            bullish_3 = candle3['Close'] > candle3['Open']
            large_body_3 = abs(candle3['Close'] - candle3['Open']) > (candle3['High'] - candle3['Low']) * 0.6
            
            if bearish_1 and large_body_1 and small_body_2 and bullish_3 and large_body_3:
                return True, 79, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_hammer(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect hammer pattern"""
        if len(data) < 1:
            return False, 0, 0
        
        try:
            candle = data.iloc[-1]
            pattern_start = len(data) - 1
            
            body_size = abs(candle['Close'] - candle['Open'])
            total_range = candle['High'] - candle['Low']
            
            if total_range == 0:
                return False, 0, pattern_start
            
            small_body = body_size < total_range * 0.3
            lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
            long_lower_shadow = lower_shadow > body_size * 2
            upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
            small_upper_shadow = upper_shadow < body_size * 0.5
            
            if small_body and long_lower_shadow and small_upper_shadow:
                return True, 73, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    # BEARISH PATTERNS FOR CCS
    def _detect_head_shoulders(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect head and shoulders pattern"""
        if len(data) < 20:
            return False, 0, 0
        
        try:
            recent_data = data.tail(15)
            pattern_start = len(data) - 15
            
            highs = recent_data['High']
            peaks = []
            
            for i in range(2, len(highs)-2):
                if (highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1] and
                    highs.iloc[i] > highs.iloc[i-2] and highs.iloc[i] > highs.iloc[i+2]):
                    peaks.append((i, highs.iloc[i]))
            
            if len(peaks) >= 3:
                peaks.sort(key=lambda x: x[1], reverse=True)
                head_idx, head_price = peaks[0]
                
                current_price = data['Close'].iloc[-1]
                neckline = recent_data['Low'].min()
                
                if current_price < neckline * 1.02:
                    return True, 86, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_descending_triangle(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect descending triangle"""
        if len(data) < 15:
            return False, 0, 0
        
        try:
            recent_data = data.tail(12)
            pattern_start = len(data) - 12
            
            support_level = recent_data['Low'].min()
            current_price = data['Close'].iloc[-1]
            
            # Flat support
            low_variance = recent_data['Low'].std() / recent_data['Low'].mean()
            flat_support = low_variance < 0.025
            
            # Declining highs
            early_highs = recent_data['High'].iloc[:4].mean()
            late_highs = recent_data['High'].iloc[-4:].mean()
            declining_resistance = late_highs < early_highs * 0.98
            
            # Breakdown
            support_broken = current_price < support_level * 0.995
            
            if flat_support and declining_resistance and support_broken:
                return True, 83, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_bear_flag(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect bear flag pattern"""
        if len(data) < 12:
            return False, 0, 0
        
        try:
            pattern_start = len(data) - 10
            
            # Prior bearish move
            price_8_ago = data['Close'].iloc[-9]
            current_price = data['Close'].iloc[-1]
            prior_decline = ((current_price - price_8_ago) / price_8_ago) < -0.025
            
            # Flag consolidation
            recent_data = data.tail(6)
            consolidation_range = (recent_data['High'].max() - recent_data['Low'].min()) / recent_data['Low'].min()
            small_range = consolidation_range < 0.06
            
            # Breakdown
            flag_low = recent_data['Low'].min()
            breakdown = current_price < flag_low * 1.005
            
            if prior_decline and small_range and breakdown:
                return True, 81, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_double_top(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect double top pattern"""
        if len(data) < 15:
            return False, 0, 0
        
        try:
            recent_data = data.tail(12)
            pattern_start = len(data) - 12
            
            highs = recent_data['High']
            peaks = []
            
            for i in range(1, len(highs)-1):
                if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1]:
                    peaks.append(highs.iloc[i])
            
            if len(peaks) >= 2:
                first_peak, second_peak = peaks[0], peaks[-1]
                
                if abs(first_peak - second_peak) / max(first_peak, second_peak) <= 0.04:
                    current_price = data['Close'].iloc[-1]
                    valley = recent_data['Low'].min()
                    
                    if current_price < valley * 1.01:
                        return True, 78, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_rising_wedge(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect rising wedge pattern"""
        if len(data) < 15:
            return False, 0, 0
        
        try:
            recent_data = data.tail(12)
            pattern_start = len(data) - 12
            
            highs = recent_data['High']
            lows = recent_data['Low']
            
            # Both rising but converging
            recent_high_trend = (highs.iloc[-1] - highs.iloc[-8]) > 0
            recent_low_trend = (lows.iloc[-1] - lows.iloc[-8]) > 0
            
            current_price = data['Close'].iloc[-1]
            recent_low = recent_data['Low'].min()
            
            breakdown = current_price < recent_low * 1.005
            
            if recent_high_trend and recent_low_trend and breakdown:
                return True, 75, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_bearish_engulfing(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect bearish engulfing pattern"""
        if len(data) < 2:
            return False, 0, 0
        
        try:
            candle1 = data.iloc[-2]
            candle2 = data.iloc[-1]
            pattern_start = len(data) - 2
            
            bullish_1 = candle1['Close'] > candle1['Open']
            bearish_2 = candle2['Close'] < candle2['Open']
            engulfs = (candle2['Open'] > candle1['Close'] and candle2['Close'] < candle1['Open'])
            
            volume_increase = data['Volume'].iloc[-1] > data['Volume'].iloc[-2] * 1.2
            
            if bullish_1 and bearish_2 and engulfs:
                strength = 79
                if volume_increase: strength += 6
                return True, strength, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_evening_star(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect evening star pattern"""
        if len(data) < 3:
            return False, 0, 0
        
        try:
            candle1 = data.iloc[-3]
            candle2 = data.iloc[-2]
            candle3 = data.iloc[-1]
            pattern_start = len(data) - 3
            
            bullish_1 = candle1['Close'] > candle1['Open']
            large_body_1 = abs(candle1['Close'] - candle1['Open']) > (candle1['High'] - candle1['Low']) * 0.6
            
            small_body_2 = abs(candle2['Close'] - candle2['Open']) < (candle2['High'] - candle2['Low']) * 0.3
            
            bearish_3 = candle3['Close'] < candle3['Open']
            large_body_3 = abs(candle3['Close'] - candle3['Open']) > (candle3['High'] - candle3['Low']) * 0.6
            
            if bullish_1 and large_body_1 and small_body_2 and bearish_3 and large_body_3:
                return True, 82, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_shooting_star(self, data: pd.DataFrame) -> Tuple[bool, int, int]:
        """Detect shooting star pattern"""
        if len(data) < 1:
            return False, 0, 0
        
        try:
            candle = data.iloc[-1]
            pattern_start = len(data) - 1
            
            body_size = abs(candle['Close'] - candle['Open'])
            total_range = candle['High'] - candle['Low']
            
            if total_range == 0:
                return False, 0, pattern_start
            
            small_body = body_size < total_range * 0.3
            upper_shadow = candle['High'] - max(candle['Open'], candle['Close'])
            long_upper_shadow = upper_shadow > body_size * 2
            lower_shadow = min(candle['Open'], candle['Close']) - candle['Low']
            small_lower_shadow = lower_shadow < body_size * 0.5
            
            if small_body and long_upper_shadow and small_lower_shadow:
                return True, 74, pattern_start
            
            return False, 0, pattern_start
            
        except Exception:
            return False, 0, 0
    
    def _detect_current_day_direction(self, data: pd.DataFrame, strategy_type: str, lookback_days: int = 20) -> Tuple[bool, Dict]:
        """Enhanced direction detection with better filtering"""
        try:
            if len(data) < lookback_days + 5:
                return False, {}
            
            current_close = data['Close'].iloc[-1]
            current_high = data['High'].iloc[-1]
            current_low = data['Low'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            current_open = data['Open'].iloc[-1]
            
            lookback_data = data.iloc[-(lookback_days+1):-1]
            recent_high = lookback_data['High'].max()
            recent_low = lookback_data['Low'].min()
            avg_volume = lookback_data['Volume'].mean()
            
            if strategy_type == "Put Credit Spreads":
                # Breakout above resistance
                breakout_occurred = current_high > recent_high * 1.012  # More significant breakout
                bullish_close = current_close > current_open
                close_strength = ((current_close - current_low) / (current_high - current_low)) * 100 if current_high != current_low else 50
                direction_friendly = close_strength >= 65  # Stronger requirement
                move_percentage = ((current_high - recent_high) / recent_high) * 100 if breakout_occurred else 0
            else:
                # Breakdown below support
                breakout_occurred = current_low < recent_low * 0.988  # More significant breakdown
                bullish_close = current_close < current_open
                close_strength = ((current_close - current_low) / (current_high - current_low)) * 100 if current_high != current_low else 50
                direction_friendly = close_strength <= 35  # Stronger requirement
                move_percentage = ((recent_low - current_low) / recent_low) * 100 if breakout_occurred else 0
            
            volume_confirmed = current_volume >= (avg_volume * 1.3)  # Higher volume requirement
            
            # Enhanced confirmation criteria
            direction_confirmed = (
                breakout_occurred and
                volume_confirmed and
                (bullish_close if strategy_type == "Put Credit Spreads" else not bullish_close) and
                direction_friendly and
                move_percentage >= 0.8  # Minimum significant move
            )
            
            details = {
                'breakout_occurred': breakout_occurred,
                'volume_confirmed': volume_confirmed,
                'direction_close': bullish_close if strategy_type == "Put Credit Spreads" else not bullish_close,
                'move_percentage': move_percentage,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
                'close_strength': close_strength,
                'recent_level': recent_high if strategy_type == "Put Credit Spreads" else recent_low,
                'current_level': current_high if strategy_type == "Put Credit Spreads" else current_low,
                'significance_met': move_percentage >= 0.8
            }
            
            return direction_confirmed, details
            
        except Exception as e:
            logger.error(f"Direction detection failed: {e}")
            return False, {}
    
    def _check_volume_criteria(self, data: pd.DataFrame, min_ratio: float = 1.2) -> Tuple[bool, float]:
        """Enhanced volume validation"""
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
            
            # Additional volume quality checks
            recent_volume_consistency = (data['Volume'].tail(5) > avg_volume * 0.3).sum() >= 3
            
            return (volume_ratio >= min_ratio and recent_volume_consistency), volume_ratio
            
        except Exception:
            return False, 0
    
    def _get_pattern_data(self, pattern_name: str, strategy_type: str) -> Dict:
        """Enhanced pattern data with updated success rates"""
        
        pcs_patterns = {
            'Cup and Handle': {'success_rate': 87, 'suitability': 94},
            'Ascending Triangle': {'success_rate': 83, 'suitability': 90},
            'Bull Flag': {'success_rate': 85, 'suitability': 88},
            'Double Bottom': {'success_rate': 79, 'suitability': 85},
            'Inverse Head and Shoulders': {'success_rate': 82, 'suitability': 92},
            'Bullish Engulfing': {'success_rate': 75, 'suitability': 82},
            'Morning Star': {'success_rate': 78, 'suitability': 84},
            'Hammer': {'success_rate': 72, 'suitability': 80}
        }
        
        ccs_patterns = {
            'Head and Shoulders': {'success_rate': 84, 'suitability': 96},
            'Descending Triangle': {'success_rate': 80, 'suitability': 91},
            'Bear Flag': {'success_rate': 82, 'suitability': 87},
            'Double Top': {'success_rate': 76, 'suitability': 89},
            'Rising Wedge': {'success_rate': 73, 'suitability': 85},
            'Bearish Engulfing': {'success_rate': 74, 'suitability': 86},
            'Evening Star': {'success_rate': 77, 'suitability': 88},
            'Shooting Star': {'success_rate': 70, 'suitability': 82}
        }
        
        patterns_db = pcs_patterns if strategy_type == "Put Credit Spreads" else ccs_patterns
        
        return patterns_db.get(pattern_name, {'success_rate': 75, 'suitability': 85})

# PRODUCTION SCANNING FUNCTION
def scan_stocks_production_ready(stocks: List[str], filters: Dict, strategy_type: str, 
                                include_weekly: bool = True, max_workers: int = 25) -> List[Dict]:
    """Production-ready parallel scanning with comprehensive error handling"""
    
    scanner = ProductionOptionsScanner()
    all_results = []
    
    def scan_single_stock(symbol: str) -> List[Dict]:
        """Scan individual stock with full error handling"""
        try:
            # Get cached daily data
            daily_data = get_stock_data_cached(symbol)
            if daily_data is None or len(daily_data) < 50:
                return []
            
            # Enhanced pattern detection with quality filters
            patterns = scanner.detect_patterns_with_quality_filters(
                daily_data, symbol, strategy_type, filters
            )
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error scanning {symbol}: {e}")
            return []
    
    # Optimized parallel processing
    successful_scans = 0
    failed_scans = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_stock = {executor.submit(scan_single_stock, stock): stock for stock in stocks}
        
        for future in as_completed(future_to_stock):
            stock = future_to_stock[future]
            try:
                result = future.result(timeout=45)
                if result:
                    all_results.extend(result)
                    successful_scans += 1
                else:
                    failed_scans += 1
                    
            except Exception as e:
                logger.warning(f"Failed to scan {stock}: {e}")
                failed_scans += 1
                continue
    
    logger.info(f"Scan completed: {successful_scans} successful, {failed_scans} failed, {len(all_results)} patterns found")
    
    return all_results

# ENHANCED UI FUNCTIONS
def create_production_sidebar() -> Dict:
    """Production-ready sidebar with comprehensive controls"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style='text-align: center; padding: 16px; background: linear-gradient(135deg, #6366f1, #4338ca); border-radius: 10px; margin-bottom: 24px;'>
            <h2 style='color: #FFFFFF; margin: 0; font-weight: 700; font-size: 1.4rem;'>⚡ Options Strategy Scanner</h2>
            <p style='color: #FFFFFF; margin: 6px 0 0 0; opacity: 0.95; font-size: 0.9rem;'>Production v8.0</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Strategy Selection
        st.markdown("### 🎯 **Strategy Selection**")
        strategy_type = st.radio(
            "Choose your options strategy:",
            ["Put Credit Spreads", "Call Credit Spreads"],
            index=0,
            help="Strategy determines which patterns to scan for"
        )
        
        if strategy_type == "Put Credit Spreads":
            st.success("📈 **Bullish patterns** - Profit from upward moves")
        else:
            st.error("📉 **Bearish patterns** - Profit from downward moves")
        
        st.markdown("---")
        
        # Quality Settings
        st.markdown("### 🔧 **Quality Settings**")
        
        quality_mode = st.selectbox(
            "Quality Filter Mode:",
            ["PREMIUM (Strictest)", "HIGH (Recommended)", "MEDIUM (Balanced)", "LOW (Permissive)"],
            index=1,
            help="Higher quality = fewer but better signals"
        )
        
        # Map quality mode to settings
        quality_settings = {
            "PREMIUM (Strictest)": {
                'min_strength': 85,
                'min_quality_score': 80,
                'min_volume_ratio': 1.8,
                'strict_quality': True
            },
            "HIGH (Recommended)": {
                'min_strength': 80,
                'min_quality_score': 70,
                'min_volume_ratio': 1.5,
                'strict_quality': True
            },
            "MEDIUM (Balanced)": {
                'min_strength': 75,
                'min_quality_score': 60,
                'min_volume_ratio': 1.3,
                'strict_quality': False
            },
            "LOW (Permissive)": {
                'min_strength': 70,
                'min_quality_score': 50,
                'min_volume_ratio': 1.1,
                'strict_quality': False
            }
        }
        
        current_settings = quality_settings[quality_mode]
        
        # Advanced Controls
        with st.expander("🔬 Advanced Controls", expanded=False):
            
            # Override quality settings
            st.markdown("**Manual Overrides:**")
            
            min_strength = st.slider(
                "Pattern Strength (%)",
                min_value=60,
                max_value=95,
                value=current_settings['min_strength'],
                step=5
            )
            
            min_quality_score = st.slider(
                "Quality Score (%)",
                min_value=40,
                max_value=95,
                value=current_settings['min_quality_score'],
                step=5,
                help="Comprehensive quality score from all filters"
            )
            
            min_volume_ratio = st.slider(
                "Volume Ratio",
                min_value=1.0,
                max_value=3.0,
                value=current_settings['min_volume_ratio'],
                step=0.1
            )
            
            # Technical settings
            st.markdown("**Technical Settings:**")
            
            lookback_days = st.selectbox(
                "Lookback Period:",
                [15, 20, 25, 30],
                index=1,
                help="Days to look back for pattern formation"
            )
            
            max_workers = st.slider(
                "Parallel Workers:",
                min_value=15,
                max_value=40,
                value=25,
                step=5,
                help="More workers = faster but more CPU usage"
            )
            
            # Analysis mode
            include_weekly = st.checkbox(
                "Multi-timeframe Analysis",
                value=True,
                help="Include weekly timeframe validation (slower but higher quality)"
            )
        
        # Cache Management
        st.markdown("---")
        st.markdown("### 📊 **System Status**")
        
        # Cache status
        stocks_count = len(get_nse_fno_stocks_cached())
        st.success(f"✅ {stocks_count} F&O stocks cached")
        
        # Market status
        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)
        market_open = (9 <= current_time.hour <= 15) and (current_time.weekday() < 5)
        
        if market_open:
            st.success("🟢 Market is OPEN")
        else:
            st.error("🔴 Market is CLOSED")
        
        # System controls
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Cache", help="Clear all cached data"):
                st.cache_data.clear()
                st.success("Cache cleared!")
                st.rerun()
        
        with col2:
            if st.button("🔄 Refresh", help="Refresh page"):
                st.rerun()
        
        return {
            'strategy_type': strategy_type,
            'min_strength': min_strength,
            'min_quality_score': min_quality_score,
            'min_volume_ratio': min_volume_ratio,
            'lookback_days': lookback_days,
            'strict_quality': current_settings['strict_quality'],
            'include_weekly': include_weekly,
            'max_workers': max_workers,
            'stocks_to_scan': get_nse_fno_stocks_cached()
        }

def create_enhanced_results_display(results: List[Dict], strategy_type: str, scan_time: float):
    """Enhanced results display with quality metrics"""
    
    if not results:
        st.warning(f"🔍 No high-quality {strategy_type.split()[0]} patterns found.")
        st.markdown("""
        ### 💡 **Try These Adjustments:**
        - Lower the Quality Filter Mode to "MEDIUM" or "LOW"
        - Reduce minimum strength and quality score requirements
        - Check if market conditions favor the opposite strategy
        - Scan during different market sessions
        """)
        return
    
    # Enhanced Summary Metrics
    st.markdown(f"### 📈 **{strategy_type} Results Summary**")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Opportunities", len(results))
    
    with col2:
        premium_count = sum(1 for r in results if r.get('quality_grade') == 'PREMIUM')
        st.metric("Premium Quality", premium_count)
    
    with col3:
        high_confidence = sum(1 for r in results if r.get('confidence_level') in ['HIGH', 'VERY HIGH'])
        st.metric("High Confidence", high_confidence)
    
    with col4:
        avg_quality = sum(r.get('quality_score', 0) for r in results) / len(results)
        st.metric("Avg Quality Score", f"{avg_quality:.1f}%")
    
    with col5:
        st.metric("Scan Time", f"{scan_time:.1f}s")
    
    # Quality Distribution
    quality_dist = {}
    for result in results:
        grade = result.get('quality_grade', 'UNKNOWN')
        quality_dist[grade] = quality_dist.get(grade, 0) + 1
    
    st.markdown("**Quality Distribution:**")
    quality_cols = st.columns(len(quality_dist))
    for i, (grade, count) in enumerate(quality_dist.items()):
        with quality_cols[i]:
            color = {
                'PREMIUM': '🟢',
                'HIGH': '🟡', 
                'MEDIUM': '🟠',
                'LOW': '🔴'
            }.get(grade, '⚪')
            st.write(f"{color} {grade}: {count}")
    
    # Results Tabs
    tab1, tab2, tab3 = st.tabs([
        "🏆 **Premium Opportunities**",
        "📊 **Complete Analysis**",
        "📱 **Export & Analytics**"
    ])
    
    with tab1:
        st.markdown(f"### 🏆 **Premium {strategy_type} Opportunities**")
        
        # Sort by quality score and show top opportunities
        premium_results = [r for r in results if r.get('quality_grade') in ['PREMIUM', 'HIGH']]
        if not premium_results:
            premium_results = sorted(results, key=lambda x: x.get('quality_score', 0), reverse=True)[:10]
        
        for i, pattern in enumerate(premium_results[:12], 1):
            
            # Quality indicators
            quality_score = pattern.get('quality_score', 0)
            quality_grade = pattern.get('quality_grade', 'UNKNOWN')
            confidence = pattern.get('confidence_level', 'UNKNOWN')
            risk_score = pattern.get('risk_score', 50)
            
            # Color coding
            grade_colors = {
                'PREMIUM': '#10b981',
                'HIGH': '#f59e0b', 
                'MEDIUM': '#ef4444',
                'LOW': '#6b7280'
            }
            grade_color = grade_colors.get(quality_grade, '#6b7280')
            
            # Risk color
            risk_color = '#10b981' if risk_score < 30 else '#f59e0b' if risk_score < 60 else '#ef4444'
            
            st.markdown(f"""
            <div class="quality-card">
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;'>
                    <h3 style='margin: 0; color: var(--primary-700); font-size: 1.3rem;'>
                        #{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']}
                    </h3>
                    <div style='display: flex; gap: 8px; align-items: center;'>
                        <span class='quality-badge' style='background: {grade_color}; color: white;'>{quality_grade}</span>
                        <span style='background: var(--primary-600); color: white; padding: 6px 12px; border-radius: 16px; font-weight: bold; font-size: 0.9rem;'>
                            {pattern['strength']:.0f}%
                        </span>
                    </div>
                </div>
                
                <div class='metric-grid'>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>PRICE</div>
                        <div style='font-size: 1rem; font-weight: bold;'>₹{pattern['current_price']:.2f}</div>
                    </div>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>QUALITY</div>
                        <div style='font-size: 1rem; font-weight: bold; color: {grade_color};'>{quality_score:.0f}%</div>
                    </div>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>CONFIDENCE</div>
                        <div style='font-size: 1rem; font-weight: bold;'>{confidence}</div>
                    </div>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>RISK</div>
                        <div style='font-size: 1rem; font-weight: bold; color: {risk_color};'>{risk_score}</div>
                    </div>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>SUCCESS RATE</div>
                        <div style='font-size: 1rem; font-weight: bold; color: #10b981;'>{pattern['success_rate']}%</div>
                    </div>
                    <div class='metric-item'>
                        <div style='font-size: 0.75rem; color: #6b7280; margin-bottom: 4px;'>VOLUME</div>
                        <div style='font-size: 1rem; font-weight: bold;'>{pattern.get('volume_ratio', 0):.1f}x</div>
                    </div>
                </div>
                
                <div style='margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border); display: flex; justify-content: space-between; font-size: 0.85rem; color: #6b7280;'>
                    <span><strong>Movement:</strong> {'✅ Confirmed' if pattern.get('direction_confirmed') else '⏳ Pending'}</span>
                    <span><strong>Timeframe:</strong> {'✅ Aligned' if pattern.get('timeframe_metrics', {}).get('is_aligned') else '❌ Mixed'}</span>
                    <span><strong>Regime:</strong> {'✅ Suitable' if pattern.get('regime_metrics', {}).get('regime_suitable') else '❌ Unfavorable'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with tab2:
        st.markdown(f"### 📊 **Complete {strategy_type} Analysis**")
        
        for i, pattern in enumerate(results, 1):
            with st.expander(f"#{i} {pattern['symbol'].replace('.NS', '')} - {pattern['pattern']} "
                           f"(Q: {pattern.get('quality_score', 0):.0f}% | S: {pattern['strength']:.0f}%)", 
                           expanded=i<=2):
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📈 Pattern Analysis")
                    st.write(f"**Symbol:** {pattern['symbol'].replace('.NS', '')}")
                    st.write(f"**Pattern:** {pattern['pattern']}")
                    st.write(f"**Current Price:** ₹{pattern['current_price']:.2f}")
                    st.write(f"**Strength:** {pattern['strength']}%")
                    st.write(f"**Success Rate:** {pattern['success_rate']}%")
                    st.write(f"**Strategy Suitability:** {pattern['suitability']}%")
                    
                    st.markdown("#### 🎯 Quality Metrics")
                    st.write(f"**Overall Quality:** {pattern.get('quality_score', 0):.1f}%")
                    st.write(f"**Quality Grade:** {pattern.get('quality_grade', 'UNKNOWN')}")
                    st.write(f"**Confidence Level:** {pattern.get('confidence_level', 'UNKNOWN')}")
                    st.write(f"**Risk Score:** {pattern.get('risk_score', 50)}")
                
                with col2:
                    st.markdown("#### 📊 Technical Analysis")
                    
                    direction_details = pattern.get('direction_details', {})
                    if direction_details:
                        move_type = "Breakout" if strategy_type == "Put Credit Spreads" else "Breakdown"
                        st.write(f"**{move_type}:** {'✅ Confirmed' if direction_details.get('breakout_occurred') else '❌ No'}")
                        st.write(f"**Volume Confirmed:** {'✅ Yes' if direction_details.get('volume_confirmed') else '❌ No'}")
                        st.write(f"**Move Percentage:** {direction_details.get('move_percentage', 0):.2f}%")
                        st.write(f"**Volume Ratio:** {direction_details.get('volume_ratio', 0):.1f}x")
                        st.write(f"**Close Strength:** {direction_details.get('close_strength', 0):.0f}%")
                    
                    # Multi-timeframe analysis
                    tf_metrics = pattern.get('timeframe_metrics', {})
                    if tf_metrics:
                        st.markdown("#### ⏱️ Timeframe Analysis")
                        st.write(f"**Daily Trend:** {tf_metrics.get('daily_trend', 'Unknown')}")
                        st.write(f"**Weekly Trend:** {tf_metrics.get('weekly_trend', 'Unknown')}")
                        st.write(f"**Alignment Score:** {tf_metrics.get('alignment_score', 0):.0f}%")
                        
                    # Liquidity metrics
                    liq_metrics = pattern.get('liquidity_metrics', {})
                    if liq_metrics:
                        st.markdown("#### 💧 Liquidity Analysis")
                        st.write(f"**Avg Volume (20D):** {liq_metrics.get('avg_volume_20d', 0):,.0f}")
                        st.write(f"**Liquidity Score:** {liq_metrics.get('liquidity_score', 0):.0f}%")
    
    with tab3:
        st.markdown("### 📱 **Export & Analytics**")
        
        # Export functionality
        excel_data = create_excel_export_enhanced(results, strategy_type)
        
        col1, col2 = st.columns(2)
        
        with col1:
            strategy_short = "PCS" if strategy_type == "Put Credit Spreads" else "CCS"
            st.download_button(
                label="📊 **Download Detailed Report**",
                data=excel_data,
                file_name=f"{strategy_short}_Quality_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            # Analytics summary
            st.markdown("**📈 Pattern Analytics:**")
            
            pattern_summary = {}
            for result in results:
                pattern = result['pattern']
                pattern_summary[pattern] = pattern_summary.get(pattern, 0) + 1
            
            for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
                st.write(f"• **{pattern}:** {count} opportunities")
        
        # Quality distribution chart
        st.markdown("**📊 Quality Distribution:**")
        
        quality_data = {}
        for result in results:
            grade = result.get('quality_grade', 'UNKNOWN')
            quality_data[grade] = quality_data.get(grade, 0) + 1
        
        # Simple bar chart representation
        for grade, count in quality_data.items():
            percentage = (count / len(results)) * 100
            st.write(f"**{grade}:** {count} patterns ({percentage:.1f}%)")

def create_excel_export_enhanced(results: List[Dict], strategy_type: str) -> BytesIO:
    """Create enhanced Excel export with quality metrics"""
    output = BytesIO()
    strategy_short = "PCS" if strategy_type == "Put Credit Spreads" else "CCS"
    
    try:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main results with quality metrics
            main_data = []
            for result in results:
                main_data.append({
                    'Symbol': result['symbol'].replace('.NS', ''),
                    'Pattern': result['pattern'],
                    'Strength': f"{result['strength']}%",
                    'Quality Score': f"{result.get('quality_score', 0):.1f}%",
                    'Quality Grade': result.get('quality_grade', 'UNKNOWN'),
                    'Success Rate': f"{result['success_rate']}%",
                    f'{strategy_short} Suitability': f"{result['suitability']}%",
                    'Confidence': result.get('confidence_level', 'UNKNOWN'),
                    'Risk Score': result.get('risk_score', 50),
                    'Current Price': f"₹{result['current_price']:.2f}",
                    'Volume Ratio': f"{result.get('volume_ratio', 0):.1f}x",
                    'Direction Confirmed': 'Yes' if result.get('direction_confirmed') else 'No',
                    'Timeframe Aligned': 'Yes' if result.get('timeframe_metrics', {}).get('is_aligned') else 'No',
                    'Market Regime': 'Suitable' if result.get('regime_metrics', {}).get('regime_suitable') else 'Unfavorable'
                })
            
            df_main = pd.DataFrame(main_data)
            df_main.to_excel(writer, sheet_name=f'{strategy_short}_Quality_Analysis', index=False)
            
            # Quality summary
            quality_summary = []
            quality_dist = {}
            for result in results:
                grade = result.get('quality_grade', 'UNKNOWN')
                quality_dist[grade] = quality_dist.get(grade, 0) + 1
            
            for grade, count in quality_dist.items():
                quality_summary.append({
                    'Quality Grade': grade,
                    'Count': count,
                    'Percentage': f"{(count/len(results)*100):.1f}%"
                })
            
            df_quality = pd.DataFrame(quality_summary)
            df_quality.to_excel(writer, sheet_name='Quality_Distribution', index=False)
            
            # Pattern summary
            pattern_summary = {}
            for result in results:
                pattern = result['pattern']
                pattern_summary[pattern] = pattern_summary.get(pattern, 0) + 1
            
            pattern_data = []
            for pattern, count in sorted(pattern_summary.items(), key=lambda x: x[1], reverse=True):
                pattern_data.append({
                    'Pattern': pattern,
                    'Count': count,
                    'Percentage': f"{(count/len(results)*100):.1f}%"
                })
            
            df_patterns = pd.DataFrame(pattern_data)
            df_patterns.to_excel(writer, sheet_name='Pattern_Summary', index=False)
        
        output.seek(0)
        return output
        
    except Exception as e:
        logger.error(f"Excel export failed: {e}")
        # Return empty BytesIO if export fails
        output.seek(0)
        return output

# MAIN APPLICATION
def main():
    """Production-ready main application"""
    try:
        # Initialize configuration
        config = create_production_sidebar()
        strategy_type = config['strategy_type']
        
        # Apply dynamic theme
        theme_css, strategy_icon = get_theme_css(strategy_type)
        st.markdown(theme_css, unsafe_allow_html=True)
        
        # Enhanced header
        st.markdown(f"""
        <div style='text-align: center; padding: 32px 16px; background: linear-gradient(135deg, var(--primary-50), var(--neutral-50)); border-radius: 16px; margin-bottom: 32px; border: 2px solid var(--primary-500);'>
            <div style='background: var(--primary-600); color: white; padding: 8px 24px; border-radius: 24px; display: inline-block; margin-bottom: 16px; font-weight: 600;'>
                {strategy_icon} {strategy_type}
            </div>
            <h1 style='margin: 16px 0 8px 0; font-size: 2.5rem; font-weight: 800;'>Professional Options Scanner</h1>
            <p style='color: var(--text-secondary); margin: 8px 0 4px 0; font-size: 1.1rem; font-weight: 500;'>Advanced Pattern Recognition • Quality Filtering • Risk Assessment</p>
            <p style='color: var(--text-tertiary); margin: 0; font-size: 0.95rem;'>Production v8.0 • NSE F&O Universe • Real-time Analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Main scanning interface
        st.markdown("### 🎯 **Pattern Scanner**")
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            scan_button = st.button(
                f"{strategy_icon} **Start Professional Scan**",
                type="primary",
                use_container_width=True,
                help=f"Begin comprehensive {strategy_type} analysis with quality filtering"
            )
        
        with col2:
            mode = "Multi-TF" if config['include_weekly'] else "Daily Only"
            quality = config['min_quality_score']
            st.markdown(f"**Mode:** {mode} | **Quality:** {quality}%")
        
        with col3:
            stock_count = len(config['stocks_to_scan'])
            st.markdown(f"**Scanning:** {stock_count} stocks")
        
        if scan_button:
            # Initialize scanner and tracking
            scanner = ProductionOptionsScanner()
            
            progress_bar = st.progress(0)
            status_container = st.empty()
            metrics_container = st.empty()
            
            start_time = time.time()
            
            # Show scan configuration
            status_container.info(f"""
            🚀 **Starting {strategy_type} scan...**
            - **Quality Mode:** {config['min_quality_score']}% minimum
            - **Pattern Strength:** {config['min_strength']}% minimum  
            - **Volume Requirement:** {config['min_volume_ratio']}x minimum
            - **Parallel Workers:** {config['max_workers']}
            - **Multi-timeframe:** {'✅ Enabled' if config['include_weekly'] else '❌ Disabled'}
            """)
            
            progress_bar.progress(10)
            
            # Create comprehensive filters
            filters = {
                'min_strength': config['min_strength'],
                'min_quality_score': config['min_quality_score'],
                'volume_ratio': config['min_volume_ratio'],
                'lookback_days': config['lookback_days'],
                'strict_quality': config['strict_quality']
            }
            
            status_container.info(f"🔄 Scanning {len(config['stocks_to_scan'])} stocks with advanced quality filters...")
            progress_bar.progress(20)
            
            try:
                # Execute production scan
                results = scan_stocks_production_ready(
                    config['stocks_to_scan'],
                    filters,
                    strategy_type,
                    include_weekly=config['include_weekly'],
                    max_workers=config['max_workers']
                )
                
                progress_bar.progress(90)
                status_container.info("🔄 Processing quality metrics and final ranking...")
                
                # Sort by quality score, then by strength
                results.sort(key=lambda x: (x.get('quality_score', 0), x['strength']), reverse=True)
                
                progress_bar.progress(100)
                end_time = time.time()
                scan_duration = end_time - start_time
                
                # Success message with detailed metrics
                if results:
                    premium_count = sum(1 for r in results if r.get('quality_grade') == 'PREMIUM')
                    high_count = sum(1 for r in results if r.get('quality_grade') == 'HIGH')
                    avg_quality = sum(r.get('quality_score', 0) for r in results) / len(results)
                    
                    status_container.success(f"""
                    ✅ **Scan completed successfully!**
                    - **Total Opportunities:** {len(results)}
                    - **Premium Quality:** {premium_count}
                    - **High Quality:** {high_count}  
                    - **Average Quality Score:** {avg_quality:.1f}%
                    - **Scan Time:** {scan_duration:.1f} seconds
                    """)
                    
                    # Display enhanced results
                    create_enhanced_results_display(results, strategy_type, scan_duration)
                    
                else:
                    status_container.warning(f"""
                    ⚠️ **No patterns found matching quality criteria**
                    - Try lowering the quality requirements
                    - Check if market conditions favor the opposite strategy
                    - Consider scanning during different market hours
                    - **Scan Time:** {scan_duration:.1f} seconds
                    """)
                
            except Exception as e:
                logger.error(f"Scan execution failed: {e}")
                status_container.error(f"❌ **Scan failed:** {str(e)}")
                progress_bar.empty()
        
        # Market Intelligence Tab
        st.markdown("---")
        st.markdown("### 📊 **Market Intelligence**")
        
        # Get enhanced market sentiment
        sentiment_data = scanner.analyze_market_sentiment(strategy_type) if 'scanner' in locals() else {}
        
        if sentiment_data:
            overall_sentiment = sentiment_data.get('overall', {})
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                sentiment_level = overall_sentiment.get('sentiment', 'UNKNOWN')
                confidence = overall_sentiment.get('confidence', 0)
                
                if strategy_type == "Put Credit Spreads":
                    emoji = "🟢" if sentiment_level == 'BULLISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🔴"
                else:
                    emoji = "🔴" if sentiment_level == 'BEARISH' else "🟡" if sentiment_level == 'NEUTRAL' else "🟢"
                
                st.markdown(f"""
                <div class="quality-card" style="text-align: center;">
                    <h3 style="margin: 0 0 8px 0; color: var(--text-secondary);">{emoji} Market Sentiment</h3>
                    <h2 style="margin: 0 0 8px 0; color: var(--primary-600); font-size: 1.8rem;">{sentiment_level}</h2>
                    <p style="margin: 0; color: var(--text-tertiary); font-size: 0.9rem;">Confidence: {confidence}%</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                risk_level = overall_sentiment.get('risk_level', 'MEDIUM')
                risk_colors = {'LOW': '#10b981', 'LOW-MEDIUM': '#f59e0b', 'MEDIUM': '#ef4444', 'HIGH': '#dc2626'}
                risk_color = risk_colors.get(risk_level, '#6b7280')
                
                st.markdown(f"""
                <div class="quality-card" style="text-align: center;">
                    <h3 style="margin: 0 0 8px 0; color: var(--text-secondary);">⚠️ Risk Assessment</h3>
                    <h2 style="margin: 0 0 8px 0; color: {risk_color}; font-size: 1.8rem;">{risk_level}</h2>
                    <p style="margin: 0; color: var(--text-tertiary); font-size: 0.9rem;">Current strategy risk</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                recommendation = overall_sentiment.get('recommendation', 'Neutral outlook')
                
                st.markdown(f"""
                <div class="quality-card" style="text-align: center;">
                    <h3 style="margin: 0 0 8px 0; color: var(--text-secondary);">💡 Recommendation</h3>
                    <p style="margin: 0; color: var(--primary-600); font-weight: 600; font-size: 1rem;">{recommendation}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Detailed market analysis
            if 'nifty' in sentiment_data or 'bank_nifty' in sentiment_data:
                st.markdown("### 📈 **Index Analysis**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'nifty' in sentiment_data:
                        nifty = sentiment_data['nifty']
                        st.markdown(f"""
                        **🎯 Nifty 50 Analysis**
                        - **Level:** {nifty['level']:.2f}
                        - **1D Change:** {nifty['change_1d']:+.2f}%
                        - **5D Change:** {nifty.get('change_5d', 0):+.2f}%
                        - **Sentiment:** {nifty.get('sentiment', 'Unknown')}
                        """)
                
                with col2:
                    if 'bank_nifty' in sentiment_data:
                        bank = sentiment_data['bank_nifty']
                        st.markdown(f"""
                        **🏦 Bank Nifty Analysis**
                        - **Level:** {bank['level']:.2f}
                        - **1D Change:** {bank['change_1d']:+.2f}%
                        - **5D Change:** {bank.get('change_5d', 0):+.2f}%
                        - **Sentiment:** {bank.get('sentiment', 'Unknown')}
                        """)
                
                # VIX Analysis
                if 'vix' in sentiment_data:
                    vix_data = sentiment_data['vix']
                    st.markdown(f"""
                    **📊 India VIX Analysis**
                    - **Current Level:** {vix_data['level']:.2f}
                    - **1D Change:** {vix_data['change_1d']:+.2f}%
                    - **Interpretation:** {"High Fear" if vix_data['level'] > 25 else "Moderate Volatility" if vix_data['level'] > 15 else "Low Volatility"}
                    """)
        
        # Footer with system info
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; padding: 16px; color: var(--text-tertiary); font-size: 0.85rem;'>
            <p><strong>Professional Options Scanner v8.0</strong> | Production Ready | Advanced Quality Filtering</p>
            <p>Real-time NSE F&O Analysis • Multi-timeframe Validation • Risk Assessment • Pattern Recognition</p>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        st.error(f"❌ **Application Error:** {str(e)}")
        st.info("Please refresh the page or contact support if the issue persists.")

if __name__ == "__main__":
    main()
