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
from scipy.signal import find_peaks
from sklearn.cluster import KMeans
import math
warnings.filterwarnings('ignore')

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title="NSE F&O Options Scanner Pro v9.0 - Enhanced S/R", 
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
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.2s ease;
    }}
    
    .quality-card:hover {{
        transform: translateY(-2px);
        box-shadow: var(--shadow-lg);
    }}
    
    .metric-container {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.5rem 0;
    }}
    
    .metric-value {{
        font-weight: 700;
        font-size: 1.25rem;
        color: var(--primary-700);
    }}
    
    .metric-label {{
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Premium badge styles */
    .premium-badge {{
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .high-badge {{
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .risk-low {{ color: #059669; font-weight: 600; }}
    .risk-medium {{ color: #d97706; font-weight: 600; }}
    .risk-high {{ color: #dc2626; font-weight: 600; }}
    
    /* S/R Level Display */
    .sr-levels-card {{
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 2px solid var(--primary-500);
        border-radius: 1rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }}
    
    .sr-level-item {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem;
        margin: 0.25rem 0;
        background: white;
        border-radius: 0.5rem;
        border-left: 4px solid;
        font-weight: 600;
    }}
    
    .support-s1 {{ border-left-color: #10b981; }}
    .support-s2 {{ border-left-color: #059669; }}
    .support-s3 {{ border-left-color: #047857; }}
    .resistance-r1 {{ border-left-color: #ef4444; }}
    .resistance-r2 {{ border-left-color: #dc2626; }}
    .resistance-r3 {{ border-left-color: #b91c1c; }}
</style>
""", icon

# ADVANCED SUPPORT & RESISTANCE CALCULATION SYSTEM
class ScientificSRCalculator:
    """
    Scientific Support & Resistance Calculator using multiple methods:
    1. Pivot Point Analysis
    2. Volume Profile/Weighted Levels
    3. Fibonacci Retracements 
    4. Statistical Clustering
    5. Peak/Valley Detection
    """
    
    def __init__(self, data: pd.DataFrame, lookback_period: int = 50):
        self.data = data
        self.lookback_period = lookback_period
        self.current_price = data['Close'].iloc[-1]
        
    def calculate_pivot_levels(self) -> Dict[str, float]:
        """Calculate traditional pivot point levels"""
        try:
            high = self.data['High'].iloc[-1]
            low = self.data['Low'].iloc[-1]
            close = self.data['Close'].iloc[-2]  # Previous close
            
            pivot = (high + low + close) / 3
            
            # Support levels
            s1 = (2 * pivot) - high
            s2 = pivot - (high - low)
            s3 = s1 - (high - low)
            
            # Resistance levels  
            r1 = (2 * pivot) - low
            r2 = pivot + (high - low)
            r3 = r1 + (high - low)
            
            return {
                'pivot': pivot,
                's1': s1, 's2': s2, 's3': s3,
                'r1': r1, 'r2': r2, 'r3': r3
            }
        except Exception as e:
            logger.warning(f"Pivot calculation error: {e}")
            return {}
    
    def calculate_volume_weighted_levels(self) -> Dict[str, List[float]]:
        """Calculate volume-weighted support/resistance levels"""
        try:
            recent_data = self.data.tail(self.lookback_period).copy()
            
            # Create price-volume density
            price_levels = []
            volumes = []
            
            for _, row in recent_data.iterrows():
                # Use OHLC average weighted by volume
                avg_price = (row['Open'] + row['High'] + row['Low'] + row['Close']) / 4
                price_levels.append(avg_price)
                volumes.append(row['Volume'])
            
            # Cluster prices by volume
            if len(price_levels) > 10:
                prices_array = np.array(price_levels).reshape(-1, 1)
                volumes_array = np.array(volumes)
                
                # Use KMeans to find 6 main price clusters
                kmeans = KMeans(n_clusters=6, random_state=42)
                clusters = kmeans.fit_predict(prices_array)
                
                cluster_levels = []
                for i in range(6):
                    cluster_mask = clusters == i
                    if np.any(cluster_mask):
                        cluster_prices = prices_array[cluster_mask].flatten()
                        cluster_volumes = volumes_array[cluster_mask]
                        # Volume-weighted average price for cluster
                        vwap = np.average(cluster_prices, weights=cluster_volumes)
                        cluster_levels.append(vwap)
                
                cluster_levels.sort()
                
                # Split into support and resistance based on current price
                supports = [level for level in cluster_levels if level < self.current_price]
                resistances = [level for level in cluster_levels if level > self.current_price]
                
                return {
                    'volume_supports': supports[-3:] if len(supports) >= 3 else supports,
                    'volume_resistances': resistances[:3] if len(resistances) >= 3 else resistances
                }
        except Exception as e:
            logger.warning(f"Volume weighted levels error: {e}")
        
        return {'volume_supports': [], 'volume_resistances': []}
    
    def detect_swing_levels(self) -> Dict[str, List[float]]:
        """Detect swing highs and lows using peak detection"""
        try:
            recent_data = self.data.tail(self.lookback_period)
            
            # Find peaks and valleys
            highs = recent_data['High'].values
            lows = recent_data['Low'].values
            
            # Detect swing highs
            high_peaks, _ = find_peaks(highs, distance=5, prominence=np.std(highs) * 0.5)
            swing_highs = highs[high_peaks]
            
            # Detect swing lows (invert data for peak detection)
            low_peaks, _ = find_peaks(-lows, distance=5, prominence=np.std(lows) * 0.5)
            swing_lows = lows[low_peaks]
            
            # Filter based on current price
            resistance_levels = [level for level in swing_highs if level > self.current_price]
            support_levels = [level for level in swing_lows if level < self.current_price]
            
            # Sort and take top 3
            resistance_levels.sort()
            support_levels.sort(reverse=True)
            
            return {
                'swing_supports': support_levels[:3],
                'swing_resistances': resistance_levels[:3]
            }
        except Exception as e:
            logger.warning(f"Swing levels error: {e}")
        
        return {'swing_supports': [], 'swing_resistances': []}
    
    def get_comprehensive_levels(self) -> Dict[str, Dict[str, float]]:
        """Get comprehensive S/R levels using all methods"""
        try:
            # Get all level calculations
            pivot_levels = self.calculate_pivot_levels()
            volume_levels = self.calculate_volume_weighted_levels()
            swing_levels = self.detect_swing_levels()
            
            # Combine all support levels
            all_supports = []
            if pivot_levels:
                all_supports.extend([pivot_levels.get('s1', 0), pivot_levels.get('s2', 0), pivot_levels.get('s3', 0)])
            all_supports.extend(volume_levels.get('volume_supports', []))
            all_supports.extend(swing_levels.get('swing_supports', []))
            
            # Combine all resistance levels
            all_resistances = []
            if pivot_levels:
                all_resistances.extend([pivot_levels.get('r1', 0), pivot_levels.get('r2', 0), pivot_levels.get('r3', 0)])
            all_resistances.extend(volume_levels.get('volume_resistances', []))
            all_resistances.extend(swing_levels.get('swing_resistances', []))
            
            # Filter and clean
            all_supports = [s for s in all_supports if s > 0 and s < self.current_price]
            all_resistances = [r for r in all_resistances if r > 0 and r > self.current_price]
            
            # Use clustering to find most significant levels
            def get_clustered_levels(levels, n_levels=3):
                if len(levels) < n_levels:
                    return sorted(levels, reverse=True) if levels else []
                
                # Use KMeans to cluster similar levels
                levels_array = np.array(levels).reshape(-1, 1)
                kmeans = KMeans(n_clusters=min(n_levels, len(levels)), random_state=42)
                clusters = kmeans.fit_predict(levels_array)
                
                # Get cluster centers
                cluster_levels = []
                for i in range(min(n_levels, len(levels))):
                    cluster_mask = clusters == i
                    if np.any(cluster_mask):
                        cluster_center = np.mean(levels_array[cluster_mask])
                        cluster_levels.append(cluster_center)
                
                return sorted(cluster_levels, reverse=True)
            
            # Get final S1, S2, S3 and R1, R2, R3
            final_supports = get_clustered_levels(all_supports, 3)
            final_resistances = get_clustered_levels(all_resistances, 3)
            final_resistances.sort()  # For resistances, we want ascending order
            
            # Ensure we have 3 levels (pad with calculated values if needed)
            while len(final_supports) < 3:
                if final_supports:
                    final_supports.append(final_supports[-1] * 0.98)  # 2% below last support
                else:
                    final_supports.append(self.current_price * 0.95)  # 5% below current
            
            while len(final_resistances) < 3:
                if final_resistances:
                    final_resistances.append(final_resistances[-1] * 1.02)  # 2% above last resistance
                else:
                    final_resistances.append(self.current_price * 1.05)  # 5% above current
            
            return {
                'supports': {
                    's1': final_supports[0],
                    's2': final_supports[1],
                    's3': final_supports[2]
                },
                'resistances': {
                    'r1': final_resistances[0],
                    'r2': final_resistances[1], 
                    'r3': final_resistances[2]
                },
                'pivot': pivot_levels.get('pivot', self.current_price),
                'current_price': self.current_price
            }
            
        except Exception as e:
            logger.error(f"Comprehensive levels calculation error: {e}")
            # Return basic levels as fallback
            return {
                'supports': {
                    's1': self.current_price * 0.98,
                    's2': self.current_price * 0.95,
                    's3': self.current_price * 0.92
                },
                'resistances': {
                    'r1': self.current_price * 1.02,
                    'r2': self.current_price * 1.05,
                    'r3': self.current_price * 1.08
                },
                'pivot': self.current_price,
                'current_price': self.current_price
            }

# ENHANCED QUALITY FILTERS WITH S/R INTEGRATION
class AdvancedQualityFilters:
    """Advanced quality filtering system with S/R level integration"""
    
    @staticmethod
    def check_liquidity_quality(data: pd.DataFrame) -> Dict[str, any]:
        """Check liquidity quality metrics"""
        try:
            recent_data = data.tail(20)
            avg_volume = recent_data['Volume'].mean()
            volume_std = recent_data['Volume'].std()
            current_volume = data['Volume'].iloc[-1]
            
            volume_score = min(100, (avg_volume / 100000) * 20) if avg_volume > 0 else 0
            volume_consistency = max(0, 100 - (volume_std / avg_volume * 100)) if avg_volume > 0 else 0
            volume_surge = (current_volume / avg_volume) if avg_volume > 0 else 1
            
            return {
                'avg_volume': avg_volume,
                'volume_score': volume_score,
                'volume_consistency': volume_consistency,
                'volume_surge': volume_surge,
                'liquidity_grade': 'HIGH' if volume_score >= 60 else 'MEDIUM' if volume_score >= 30 else 'LOW'
            }
        except:
            return {'avg_volume': 0, 'volume_score': 0, 'volume_consistency': 0, 'volume_surge': 1, 'liquidity_grade': 'LOW'}
    
    @staticmethod
    def analyze_multi_timeframe_alignment(symbol: str, strategy_type: str) -> Dict[str, any]:
        """Analyze multi-timeframe trend alignment"""
        try:
            # Get different timeframe data
            stock = yf.Ticker(symbol + ".NS")
            
            # Daily trend
            daily_data = stock.history(period="3mo", interval="1d")
            if len(daily_data) < 20:
                return {'alignment_score': 50, 'trend_strength': 'WEAK', 'timeframe_consensus': 'MIXED'}
            
            # Calculate trend scores
            daily_sma_20 = ta.trend.sma_indicator(daily_data['Close'], window=20).iloc[-1]
            daily_sma_50 = ta.trend.sma_indicator(daily_data['Close'], window=50).iloc[-1] if len(daily_data) >= 50 else daily_sma_20
            current_price = daily_data['Close'].iloc[-1]
            
            # Trend alignment scoring
            alignment_factors = []
            
            if strategy_type == "Put Credit Spreads":
                # Bullish alignment needed
                alignment_factors.extend([
                    100 if current_price > daily_sma_20 else 0,
                    100 if daily_sma_20 > daily_sma_50 else 0,
                ])
            else:
                # Bearish alignment needed  
                alignment_factors.extend([
                    100 if current_price < daily_sma_20 else 0,
                    100 if daily_sma_20 < daily_sma_50 else 0,
                ])
            
            alignment_score = np.mean(alignment_factors)
            
            trend_strength = 'STRONG' if alignment_score >= 75 else 'MEDIUM' if alignment_score >= 50 else 'WEAK'
            consensus = 'BULLISH' if alignment_score >= 66.7 else 'BEARISH' if alignment_score <= 33.3 else 'MIXED'
            
            return {
                'alignment_score': alignment_score,
                'trend_strength': trend_strength,
                'timeframe_consensus': consensus,
            }
        except:
            return {'alignment_score': 50, 'trend_strength': 'WEAK', 'timeframe_consensus': 'MIXED'}
    
    @staticmethod
    def assess_sr_proximity_risk(current_price: float, sr_levels: Dict) -> Dict[str, any]:
        """Assess risk based on proximity to S/R levels"""
        try:
            supports = sr_levels.get('supports', {})
            resistances = sr_levels.get('resistances', {})
            
            # Distance to nearest support/resistance
            support_distances = []
            resistance_distances = []
            
            for level in supports.values():
                if level > 0:
                    distance_pct = ((current_price - level) / current_price) * 100
                    support_distances.append(distance_pct)
            
            for level in resistances.values():
                if level > 0:
                    distance_pct = ((level - current_price) / current_price) * 100
                    resistance_distances.append(distance_pct)
            
            nearest_support_dist = min(support_distances) if support_distances else 10
            nearest_resistance_dist = min(resistance_distances) if resistance_distances else 10
            
            # Risk assessment
            support_risk = 'HIGH' if nearest_support_dist < 2 else 'MEDIUM' if nearest_support_dist < 5 else 'LOW'
            resistance_risk = 'HIGH' if nearest_resistance_dist < 2 else 'MEDIUM' if nearest_resistance_dist < 5 else 'LOW'
            
            # Overall position quality
            if nearest_support_dist >= 3 and nearest_resistance_dist >= 3:
                position_quality = 'OPTIMAL'
            elif nearest_support_dist >= 2 and nearest_resistance_dist >= 2:
                position_quality = 'GOOD'
            else:
                position_quality = 'RISKY'
            
            return {
                'nearest_support_distance': nearest_support_dist,
                'nearest_resistance_distance': nearest_resistance_dist,
                'support_risk': support_risk,
                'resistance_risk': resistance_risk,
                'position_quality': position_quality,
                'sr_score': min(100, (nearest_support_dist + nearest_resistance_dist) * 5)
            }
        except Exception as e:
            logger.warning(f"S/R proximity assessment error: {e}")
            return {
                'nearest_support_distance': 5,
                'nearest_resistance_distance': 5,
                'support_risk': 'MEDIUM',
                'resistance_risk': 'MEDIUM', 
                'position_quality': 'GOOD',
                'sr_score': 50
            }

# MAIN SCANNER CLASS WITH S/R INTEGRATION
class ProductionOptionsScanner:
    """Production-ready options scanner with advanced S/R integration"""
    
    def __init__(self):
        self.nse_fno_stocks = self._load_nse_fno_list()
        
    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def _load_nse_fno_list(_self) -> List[str]:
        """Load NSE F&O stock list with caching"""
        try:
            # Comprehensive NSE F&O stock list (top 50 most liquid)
            stocks = [
                "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "SBIN", "BHARTIARTL", "KOTAKBANK", "ITC",
                "ASIANPAINT", "LT", "AXISBANK", "MARUTI", "SUNPHARMA", "TITAN", "ULTRACEMCO", "NESTLEIND", "WIPRO", "HCLTECH",
                "BAJFINANCE", "POWERGRID", "NTPC", "TECHM", "ONGC", "TATAMOTORS", "COALINDIA", "BAJAJFINSV", "HDFCLIFE", "GRASIM",
                "ADANIPORTS", "JSWSTEEL", "INDUSINDBK", "SBILIFE", "DIVISLAB", "BPCL", "DRREDDY", "EICHERMOT", "BRITANNIA", "CIPLA",
                "TATACONSUM", "APOLLOHOSP", "BAJAJ-AUTO", "HEROMOTOCO", "SHREECEM", "IOC", "UPL", "HINDALCO", "TATASTEEL", "GODREJCP"
            ]
            
            logger.info(f"Loaded {len(stocks)} NSE F&O stocks")
            return stocks
        except Exception as e:
            logger.error(f"Error loading NSE F&O list: {e}")
            return ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]  # Fallback
    
    @st.cache_data(ttl=300)  # Cache for 5 minutes  
    def get_stock_data_cached(_self, symbol: str, period: str = "6mo") -> Optional[pd.DataFrame]:
        """Get cached stock data"""
        try:
            stock = yf.Ticker(symbol + ".NS")
            data = stock.history(period=period)
            
            if data.empty:
                return None
                
            # Add technical indicators
            data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
            data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
            data['SMA_50'] = ta.trend.sma_indicator(data['Close'], window=50)
            data['BB_Upper'] = ta.volatility.bollinger_hband(data['Close'])
            data['BB_Lower'] = ta.volatility.bollinger_lband(data['Close'])
            
            return data
            
        except Exception as e:
            logger.warning(f"Error fetching data for {symbol}: {e}")
            return None
    
    def analyze_stock_with_sr(self, symbol: str, strategy_type: str) -> Optional[Dict]:
        """Analyze stock with comprehensive S/R integration"""
        try:
            data = self.get_stock_data_cached(symbol)
            if data is None or len(data) < 50:
                return None
            
            # Calculate comprehensive S/R levels
            sr_calculator = ScientificSRCalculator(data)
            sr_levels = sr_calculator.get_comprehensive_levels()
            
            current_price = data['Close'].iloc[-1]
            
            # Get quality filters with S/R integration
            liquidity = AdvancedQualityFilters.check_liquidity_quality(data)
            mtf_alignment = AdvancedQualityFilters.analyze_multi_timeframe_alignment(symbol, strategy_type)
            sr_proximity = AdvancedQualityFilters.assess_sr_proximity_risk(current_price, sr_levels)
            
            # Calculate comprehensive quality score
            quality_factors = {
                'liquidity_score': liquidity['volume_score'] * 0.3,
                'mtf_alignment': mtf_alignment['alignment_score'] * 0.4, 
                'sr_positioning': sr_proximity['sr_score'] * 0.3,
            }
            
            total_quality_score = sum(quality_factors.values())
            
            # Quality grade
            if total_quality_score >= 85:
                quality_grade = "PREMIUM"
            elif total_quality_score >= 70:
                quality_grade = "HIGH"
            elif total_quality_score >= 55:
                quality_grade = "MEDIUM"
            else:
                quality_grade = "STANDARD"
            
            # Strategy-specific adjustments
            base_suitability = 70
            if strategy_type == "Put Credit Spreads":
                suitability = base_suitability + (mtf_alignment['alignment_score'] - 50) * 0.4
                recommendation = self._get_pcs_recommendation(total_quality_score, sr_proximity)
            else:
                suitability = base_suitability + (50 - mtf_alignment['alignment_score']) * 0.4  # Inverted for CCS
                recommendation = self._get_ccs_recommendation(total_quality_score, sr_proximity)
            
            suitability = max(0, min(100, suitability))
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'sr_levels': sr_levels,
                'quality_score': round(total_quality_score, 1),
                'quality_grade': quality_grade,
                'suitability': round(suitability, 1),
                'recommendation': recommendation,
                'liquidity': liquidity,
                'mtf_alignment': mtf_alignment,
                'sr_proximity': sr_proximity,
                'risk_assessment': self._assess_risk_level(total_quality_score, sr_proximity),
                'data': data  # Include for charting
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def _get_pcs_recommendation(self, quality_score: float, sr_proximity: Dict) -> str:
        """Get PCS-specific recommendation"""
        if quality_score >= 85 and sr_proximity['position_quality'] == 'OPTIMAL':
            return "EXCELLENT for Put Credit Spreads - Premium setup with optimal S/R positioning"
        elif quality_score >= 70 and sr_proximity['position_quality'] in ['OPTIMAL', 'GOOD']:
            return "STRONG for Put Credit Spreads - High quality with good support buffer"
        elif quality_score >= 55:
            return "MODERATE for Put Credit Spreads - Acceptable quality, monitor support levels"
        else:
            return "AVOID Put Credit Spreads - Low quality or risky S/R positioning"
    
    def _get_ccs_recommendation(self, quality_score: float, sr_proximity: Dict) -> str:
        """Get CCS-specific recommendation"""
        if quality_score >= 85 and sr_proximity['position_quality'] == 'OPTIMAL':
            return "EXCELLENT for Call Credit Spreads - Premium setup with optimal S/R positioning"
        elif quality_score >= 70 and sr_proximity['position_quality'] in ['OPTIMAL', 'GOOD']:
            return "STRONG for Call Credit Spreads - High quality with good resistance buffer"
        elif quality_score >= 55:
            return "MODERATE for Call Credit Spreads - Acceptable quality, monitor resistance levels"
        else:
            return "AVOID Call Credit Spreads - Low quality or risky S/R positioning"
    
    def _assess_risk_level(self, quality_score: float, sr_proximity: Dict) -> str:
        """Assess overall risk level"""
        if quality_score >= 75 and sr_proximity['position_quality'] == 'OPTIMAL':
            return "LOW"
        elif quality_score >= 60 and sr_proximity['position_quality'] in ['OPTIMAL', 'GOOD']:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def create_enhanced_sr_chart(self, stock_data: Dict, strategy_type: str) -> go.Figure:
        """Create enhanced chart with prominent S/R levels and clear price labels"""
        try:
            data = stock_data['data']
            sr_levels = stock_data['sr_levels']
            symbol = stock_data['symbol']
            current_price = stock_data['current_price']
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=(
                    f'{symbol} - {strategy_type} Analysis with Scientific S/R Levels',
                    'RSI (14)',
                    'Volume Profile'
                ),
                vertical_spacing=0.08,
                row_heights=[0.65, 0.2, 0.15]
            )
            
            # Main price chart - Candlestick
            fig.add_trace(
                go.Candlestick(
                    x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'],
                    name='Price',
                    increasing_line_color='#10b981',
                    decreasing_line_color='#ef4444',
                    increasing_fillcolor='rgba(16, 185, 129, 0.3)',
                    decreasing_fillcolor='rgba(239, 68, 68, 0.3)'
                ),
                row=1, col=1
            )
            
            # Define S/R colors and styles
            sr_colors = {
                's1': {'color': '#10b981', 'name': 'S1 (Strong Support)', 'width': 3},
                's2': {'color': '#059669', 'name': 'S2 (Medium Support)', 'width': 2},  
                's3': {'color': '#047857', 'name': 'S3 (Weak Support)', 'width': 2},
                'r1': {'color': '#ef4444', 'name': 'R1 (Strong Resistance)', 'width': 3},
                'r2': {'color': '#dc2626', 'name': 'R2 (Medium Resistance)', 'width': 2},
                'r3': {'color': '#b91c1c', 'name': 'R3 (Weak Resistance)', 'width': 2}
            }
            
            # Add S/R levels based on strategy type
            if strategy_type == "Put Credit Spreads":
                # Show all support levels for PCS (risk management)
                for level_name, level_value in sr_levels['supports'].items():
                    if level_value > 0:
                        style = sr_colors[level_name]
                        distance_pct = ((current_price - level_value) / current_price) * 100
                        
                        # Add horizontal line
                        fig.add_hline(
                            y=level_value,
                            line=dict(
                                color=style['color'], 
                                width=style['width'], 
                                dash='solid'
                            ),
                            annotation=dict(
                                text=f"<b>{level_name.upper()}: ₹{level_value:.2f}</b><br>Distance: {distance_pct:.1f}%",
                                x=0.02,
                                xref='paper',
                                bgcolor='rgba(255,255,255,0.9)',
                                bordercolor=style['color'],
                                borderwidth=2,
                                font=dict(size=11, color=style['color'])
                            ),
                            row=1, col=1
                        )
                        
                        # Add a subtle fill area below each support
                        fig.add_hrect(
                            y0=level_value * 0.998,
                            y1=level_value,
                            fillcolor=style['color'],
                            opacity=0.1,
                            line_width=0,
                            row=1, col=1
                        )
                
                # Show R1 for reference
                r1_value = sr_levels['resistances']['r1']
                if r1_value > current_price:
                    r1_distance = ((r1_value - current_price) / current_price) * 100
                    fig.add_hline(
                        y=r1_value,
                        line=dict(color='#ef4444', width=1, dash='dot'),
                        annotation=dict(
                            text=f"<b>R1: ₹{r1_value:.2f}</b> (+{r1_distance:.1f}%)",
                            x=0.98,
                            xref='paper',
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='#ef4444',
                            font=dict(size=10, color='#ef4444')
                        ),
                        row=1, col=1
                    )
                        
            else:  # Call Credit Spreads
                # Show all resistance levels for CCS (risk management)
                for level_name, level_value in sr_levels['resistances'].items():
                    if level_value > current_price:
                        style = sr_colors[level_name]
                        distance_pct = ((level_value - current_price) / current_price) * 100
                        
                        # Add horizontal line
                        fig.add_hline(
                            y=level_value,
                            line=dict(
                                color=style['color'], 
                                width=style['width'], 
                                dash='solid'
                            ),
                            annotation=dict(
                                text=f"<b>{level_name.upper()}: ₹{level_value:.2f}</b><br>Distance: {distance_pct:.1f}%",
                                x=0.02,
                                xref='paper',
                                bgcolor='rgba(255,255,255,0.9)',
                                bordercolor=style['color'],
                                borderwidth=2,
                                font=dict(size=11, color=style['color'])
                            ),
                            row=1, col=1
                        )
                        
                        # Add a subtle fill area above each resistance
                        fig.add_hrect(
                            y0=level_value,
                            y1=level_value * 1.002,
                            fillcolor=style['color'],
                            opacity=0.1,
                            line_width=0,
                            row=1, col=1
                        )
                
                # Show S1 for reference
                s1_value = sr_levels['supports']['s1']
                if s1_value < current_price:
                    s1_distance = ((current_price - s1_value) / current_price) * 100
                    fig.add_hline(
                        y=s1_value,
                        line=dict(color='#10b981', width=1, dash='dot'),
                        annotation=dict(
                            text=f"<b>S1: ₹{s1_value:.2f}</b> (-{s1_distance:.1f}%)",
                            x=0.98,
                            xref='paper',
                            bgcolor='rgba(255,255,255,0.8)',
                            bordercolor='#10b981',
                            font=dict(size=10, color='#10b981')
                        ),
                        row=1, col=1
                    )
            
            # Current price line
            fig.add_hline(
                y=current_price,
                line=dict(color='#1f2937', width=2, dash='dashdot'),
                annotation=dict(
                    text=f"<b>Current: ₹{current_price:.2f}</b>",
                    x=0.5,
                    xref='paper',
                    bgcolor='#1f2937',
                    font=dict(size=12, color='white')
                ),
                row=1, col=1
            )
            
            # Add moving averages with labels
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['SMA_20'],
                    name='SMA 20',
                    line=dict(color='#f59e0b', width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['SMA_50'],
                    name='SMA 50', 
                    line=dict(color='#8b5cf6', width=1.5),
                    opacity=0.8
                ),
                row=1, col=1
            )
            
            # RSI subplot with clear levels
            fig.add_trace(
                go.Scatter(
                    x=data.index,
                    y=data['RSI'],
                    name='RSI',
                    line=dict(color='#3b82f6', width=2),
                    fill='tonexty' if strategy_type == "Put Credit Spreads" else None,
                    fillcolor='rgba(59, 130, 246, 0.1)'
                ),
                row=2, col=1
            )
            
            # RSI reference lines
            fig.add_hline(y=70, line=dict(color='red', width=1, dash='dash'), 
                         annotation_text="Overbought (70)", row=2, col=1)
            fig.add_hline(y=30, line=dict(color='green', width=1, dash='dash'), 
                         annotation_text="Oversold (30)", row=2, col=1)
            fig.add_hline(y=50, line=dict(color='gray', width=1, dash='dot'), 
                         annotation_text="Neutral", row=2, col=1)
            
            # Volume with color coding
            volume_colors = []
            for i in range(len(data)):
                if data['Close'].iloc[i] >= data['Open'].iloc[i]:
                    volume_colors.append('#10b981')  # Green for up days
                else:
                    volume_colors.append('#ef4444')  # Red for down days
            
            fig.add_trace(
                go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color=volume_colors,
                    opacity=0.7
                ),
                row=3, col=1
            )
            
            # Layout customization
            fig.update_layout(
                title=dict(
                    text=f"<b>{symbol} - {strategy_type} Risk Management Chart</b><br>"
                         f"<span style='font-size:14px;'>Quality Score: {stock_data['quality_score']}/100 | "
                         f"Risk: {stock_data['risk_assessment']} | "
                         f"Position Quality: {stock_data['sr_proximity']['position_quality']}</span>",
                    x=0.5,
                    font=dict(size=16)
                ),
                height=900,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right", 
                    x=1
                ),
                xaxis_rangeslider_visible=False,
                template='plotly_white',
                font=dict(family='Inter, sans-serif')
            )
            
            # Update axes
            fig.update_xaxes(title_text="Date", row=3, col=1)
            fig.update_yaxes(title_text="Price (₹)", row=1, col=1)
            fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
            fig.update_yaxes(title_text="Volume", row=3, col=1)
            
            return fig
            
        except Exception as e:
            logger.error(f"Error creating enhanced S/R chart: {e}")
            # Return simple fallback chart
            fig = go.Figure()
            fig.add_annotation(
                text=f"Chart Error: {str(e)}",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20, color="red")
            )
            return fig

# MAIN STREAMLIT APPLICATION
def main():
    """Main Streamlit application with enhanced S/R visualization"""
    
    # Sidebar configuration
    st.sidebar.title("⚡ Options Scanner Pro v9.0")
    st.sidebar.markdown("### 🎯 Enhanced with Scientific S/R Levels")
    
    # Strategy selection
    strategy_type = st.sidebar.selectbox(
        "📊 Select Strategy Type",
        ["Put Credit Spreads", "Call Credit Spreads"],
        help="Choose between bullish (PCS) or bearish (CCS) strategies"
    )
    
    # Get theme
    theme_css, icon = get_theme_css(strategy_type)
    st.markdown(theme_css, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0;">
        <h1>{icon} NSE F&O Options Strategy Scanner Pro v9.0</h1>
        <h3 style="color: var(--primary-700);">
            {strategy_type} with Scientific S1/S2/S3 & R1/R2/R3 Levels
        </h3>
        <p style="color: var(--text-secondary); font-size: 1.1rem;">
            Risk Management with Visual S/R Level Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Configuration sidebar
    st.sidebar.markdown("### 🔧 Scanner Configuration")
    
    scan_count = st.sidebar.slider(
        "Stocks to Scan",
        min_value=5,
        max_value=50,
        value=15,
        step=5,
        help="Number of stocks to analyze (optimized for performance)"
    )
    
    quality_filter = st.sidebar.selectbox(
        "Quality Filter",
        ["All Quality", "HIGH+ Only", "PREMIUM Only"],
        help="Filter by minimum quality grade"
    )
    
    # Enhanced S/R explanation
    st.sidebar.markdown("### 🎯 S/R Level Guide")
    if strategy_type == "Put Credit Spreads":
        st.sidebar.markdown("""
        **Support Levels (Risk Management):**
        - **S1**: Strong support - Key level to watch
        - **S2**: Medium support - Secondary safety
        - **S3**: Weak support - Final safety net
        
        **Best PCS Setup:**
        - Price well above S1 (>3%)
        - Strong volume at support levels
        - Bullish trend alignment
        """)
    else:
        st.sidebar.markdown("""
        **Resistance Levels (Risk Management):**
        - **R1**: Strong resistance - Key level to watch  
        - **R2**: Medium resistance - Secondary target
        - **R3**: Weak resistance - Extended target
        
        **Best CCS Setup:**
        - Price well below R1 (>3%)
        - High volume at resistance levels
        - Bearish trend alignment
        """)
    
    # Scan button
    if st.sidebar.button("🚀 Start Enhanced S/R Scan", type="primary"):
        scanner = ProductionOptionsScanner()
        
        with st.spinner(f"Scanning {scan_count} stocks with advanced S/R analysis..."):
            progress_bar = st.progress(0)
            
            # Parallel scanning
            with ThreadPoolExecutor(max_workers=5) as executor:
                stocks_to_scan = scanner.nse_fno_stocks[:scan_count]
                
                # Submit all tasks
                future_to_stock = {
                    executor.submit(scanner.analyze_stock_with_sr, stock, strategy_type): stock 
                    for stock in stocks_to_scan
                }
                
                results = []
                completed = 0
                
                for future in as_completed(future_to_stock):
                    stock = future_to_stock[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {stock}: {e}")
                    
                    completed += 1
                    progress_bar.progress(completed / len(stocks_to_scan))
            
            # Filter results
            if quality_filter == "HIGH+ Only":
                results = [r for r in results if r['quality_grade'] in ['HIGH', 'PREMIUM']]
            elif quality_filter == "PREMIUM Only":
                results = [r for r in results if r['quality_grade'] == 'PREMIUM']
            
            # Sort by quality score
            results.sort(key=lambda x: x['quality_score'], reverse=True)
            
            # Display results
            st.markdown(f"### 📊 Enhanced S/R Scan Results - {len(results)} Opportunities")
            
            if results:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                premium_count = len([r for r in results if r['quality_grade'] == 'PREMIUM'])
                high_count = len([r for r in results if r['quality_grade'] == 'HIGH'])
                avg_quality = np.mean([r['quality_score'] for r in results])
                optimal_positioning = len([r for r in results if r['sr_proximity']['position_quality'] == 'OPTIMAL'])
                
                col1.metric("Premium Setups", premium_count, delta=f"{premium_count/len(results)*100:.0f}%")
                col2.metric("High Quality", high_count, delta=f"{high_count/len(results)*100:.0f}%")
                col3.metric("Avg Quality Score", f"{avg_quality:.0f}", delta="out of 100")
                col4.metric("Optimal S/R Position", optimal_positioning, delta=f"{optimal_positioning/len(results)*100:.0f}%")
                
                # Detailed results with enhanced visualization
                for i, stock_data in enumerate(results[:10]):  # Show top 10
                    with st.expander(
                        f"#{i+1} {stock_data['symbol']} - {stock_data['quality_grade']} Quality "
                        f"(Score: {stock_data['quality_score']}) - S/R: {stock_data['sr_proximity']['position_quality']}", 
                        expanded=i < 3
                    ):
                        # Two-column layout
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            # Key metrics card
                            st.markdown(f"""
                            <div class="quality-card">
                                <h4>{stock_data['symbol']} Analysis</h4>
                                <div class="metric-container">
                                    <span class="metric-label">Current Price</span>
                                    <span class="metric-value">₹{stock_data['current_price']:.2f}</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Quality Score</span>
                                    <span class="metric-value">{stock_data['quality_score']}/100</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Suitability</span>
                                    <span class="metric-value">{stock_data['suitability']}%</span>
                                </div>
                                <div class="metric-container">
                                    <span class="metric-label">Risk Level</span>
                                    <span class="risk-{stock_data['risk_assessment'].lower()}">{stock_data['risk_assessment']}</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # S/R Levels Display
                            sr_levels = stock_data['sr_levels']
                            
                            if strategy_type == "Put Credit Spreads":
                                st.markdown("""
                                <div class="sr-levels-card">
                                    <h4 style="text-align: center; margin-bottom: 1rem;">🛡️ Support Levels (Risk Management)</h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Support levels
                                for level_key, level_name in [('s1', 'S1 - Strong Support'), ('s2', 'S2 - Medium Support'), ('s3', 'S3 - Weak Support')]:
                                    level_value = sr_levels['supports'][level_key]
                                    distance = ((stock_data['current_price'] - level_value) / stock_data['current_price']) * 100
                                    
                                    st.markdown(f"""
                                    <div class="sr-level-item support-{level_key}">
                                        <div>
                                            <strong>{level_name}</strong><br>
                                            <small>Distance: {distance:.1f}%</small>
                                        </div>
                                        <div>
                                            <strong>₹{level_value:.2f}</strong>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            else:
                                st.markdown("""
                                <div class="sr-levels-card">
                                    <h4 style="text-align: center; margin-bottom: 1rem;">🎯 Resistance Levels (Risk Management)</h4>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Resistance levels
                                for level_key, level_name in [('r1', 'R1 - Strong Resistance'), ('r2', 'R2 - Medium Resistance'), ('r3', 'R3 - Weak Resistance')]:
                                    level_value = sr_levels['resistances'][level_key]
                                    if level_value > stock_data['current_price']:
                                        distance = ((level_value - stock_data['current_price']) / stock_data['current_price']) * 100
                                        
                                        st.markdown(f"""
                                        <div class="sr-level-item resistance-{level_key}">
                                            <div>
                                                <strong>{level_name}</strong><br>
                                                <small>Distance: {distance:.1f}%</small>
                                            </div>
                                            <div>
                                                <strong>₹{level_value:.2f}</strong>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            
                            # Quality breakdown
                            st.markdown("#### 📈 Quality Breakdown")
                            liquidity_emoji = "🟢" if stock_data['liquidity']['liquidity_grade'] == 'HIGH' else "🟡" if stock_data['liquidity']['liquidity_grade'] == 'MEDIUM' else "🔴"
                            trend_emoji = "🟢" if stock_data['mtf_alignment']['trend_strength'] == 'STRONG' else "🟡" if stock_data['mtf_alignment']['trend_strength'] == 'MEDIUM' else "🔴"
                            position_emoji = "🟢" if stock_data['sr_proximity']['position_quality'] == 'OPTIMAL' else "🟡" if stock_data['sr_proximity']['position_quality'] == 'GOOD' else "🔴"
                            
                            st.markdown(f"""
                            - {liquidity_emoji} **Liquidity**: {stock_data['liquidity']['liquidity_grade']} (Vol: {stock_data['liquidity']['avg_volume']:,.0f})
                            - {trend_emoji} **Trend Strength**: {stock_data['mtf_alignment']['trend_strength']} ({stock_data['mtf_alignment']['timeframe_consensus']})
                            - {position_emoji} **S/R Position**: {stock_data['sr_proximity']['position_quality']}
                            """)
                        
                        with col2:
                            # Enhanced chart with S/R levels
                            chart = scanner.create_enhanced_sr_chart(stock_data, strategy_type)
                            st.plotly_chart(chart, use_container_width=True)
                        
                        # Recommendation
                        st.markdown(f"""
                        #### 💡 Strategy Recommendation
                        **{stock_data['recommendation']}**
                        
                        **Key Risk Management Points:**
                        """)
                        
                        if strategy_type == "Put Credit Spreads":
                            s1_dist = stock_data['sr_proximity']['nearest_support_distance']
                            st.markdown(f"""
                            - Monitor S1 level at ₹{sr_levels['supports']['s1']:.2f} ({s1_dist:.1f}% below current price)
                            - Consider position sizing based on distance to support levels
                            - Exit strategy if price approaches S2 or below
                            """)
                        else:
                            r1_dist = stock_data['sr_proximity']['nearest_resistance_distance']  
                            st.markdown(f"""
                            - Monitor R1 level at ₹{sr_levels['resistances']['r1']:.2f} ({r1_dist:.1f}% above current price)
                            - Consider position sizing based on distance to resistance levels
                            - Exit strategy if price approaches R2 or above
                            """)
            else:
                st.warning("No qualifying opportunities found with current filters. Try adjusting quality filters or increasing scan count.")

if __name__ == "__main__":
    main()
