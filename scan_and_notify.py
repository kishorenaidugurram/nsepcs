#!/usr/bin/env python3
"""
NSE F&O PCS Screening & Telegram Notification Script
Runs automated stock screening and sends results to Telegram
"""

import os
import sys
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import yfinance as yf
import talib as ta  # Using TA-Lib instead of ta package
import pytz
from typing import List, Dict, Optional
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Telegram Configuration (set via environment variables)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Stock Universe - NSE F&O Stocks
COMPLETE_NSE_FO_UNIVERSE = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
    'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS',
    'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS',
    'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS', 'EICHERMOT.NS', 'HEROMOTOCO.NS',
    'BAJAJ-AUTO.NS', 'M&M.NS', 'TATACONSUM.NS', 'MRF.NS', 'PAGEIND.NS'
]

# Default Filter Criteria
DEFAULT_MIN_SCORE = 55  # Minimum pattern strength score
DEFAULT_MIN_RSI = 30    # Minimum RSI
DEFAULT_MAX_RSI = 75    # Maximum RSI
DEFAULT_MIN_ADX = 20    # Minimum ADX

IST = pytz.timezone('Asia/Kolkata')

# ============================================================================
# DATA FETCHING
# ============================================================================

def fetch_stock_data(symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False, interval='1d')
        if data is None or len(data) < 20:
            return None

        # Calculate technical indicators using TA-Lib
        data['RSI'] = ta.RSI(data['Close'], timeperiod=14)
        data['SMA_20'] = ta.SMA(data['Close'], timeperiod=20)
        data['SMA_50'] = ta.SMA(data['Close'], timeperiod=50)
        data['EMA_20'] = ta.EMA(data['Close'], timeperiod=20)

        bb_upper, bb_middle, bb_lower = ta.BBANDS(data['Close'], timeperiod=20, nbdevup=2, nbdevdn=2)
        data['BB_upper'] = bb_upper
        data['BB_lower'] = bb_lower
        data['BB_middle'] = bb_middle

        data['MACD'], data['MACD_signal'], data['MACD_hist'] = ta.MACD(data['Close'], fastperiod=12, slowperiod=26, signalperiod=9)
        data['ADX'] = ta.ADX(data['High'], data['Low'], data['Close'], timeperiod=14)
        data['ATR'] = ta.ATR(data['High'], data['Low'], data['Close'], timeperiod=14)

        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# ============================================================================
# ANALYSIS ENGINE
# ============================================================================

def calculate_pattern_score(data: pd.DataFrame, symbol: str, min_rsi: float = DEFAULT_MIN_RSI,
                          max_rsi: float = DEFAULT_MAX_RSI, min_adx: float = DEFAULT_MIN_ADX) -> Dict:
    """
    Calculate pattern strength score for a stock
    Returns a dict with score (0-100) and trading signals
    """
    if data is None or len(data) < 20:
        return {'score': 0, 'signals': [], 'error': 'Insufficient data'}

    try:
        current = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else current

        score = 0
        signals = []

        # RSI Analysis (30% weight)
        rsi = current['RSI']
        if min_rsi <= rsi <= max_rsi:
            rsi_score = 30
            signals.append(f"RSI optimal: {rsi:.1f}")
        elif rsi < min_rsi:
            rsi_score = 10
            signals.append(f"RSI oversold: {rsi:.1f} (potential bounce)")
        else:
            rsi_score = 5
            signals.append(f"RSI overbought: {rsi:.1f}")

        score += rsi_score

        # ADX Trend Strength (25% weight)
        adx = current['ADX']
        if adx >= min_adx:
            adx_score = 25
            signals.append(f"Strong trend: ADX {adx:.1f}")
        else:
            adx_score = 10
            signals.append(f"Weak trend: ADX {adx:.1f}")

        score += adx_score

        # Moving Average Support (20% weight)
        price = current['Close']
        sma20 = current['SMA_20']
        sma50 = current['SMA_50']

        if price > sma20 > sma50:
            ma_score = 20
            signals.append("Perfect MA alignment (bullish)")
        elif price > sma20:
            ma_score = 15
            signals.append("Price above SMA20")
        else:
            ma_score = 5
            signals.append("Price below SMA20")

        score += ma_score

        # Volume Analysis (15% weight)
        if len(data) >= 5:
            recent_volume = data['Volume'].iloc[-5:].mean()
            current_volume = current['Volume']
            vol_ratio = current_volume / recent_volume if recent_volume > 0 else 0

            if vol_ratio > 1.2:
                vol_score = 15
                signals.append(f"High volume: {vol_ratio:.2f}x average")
            elif vol_ratio > 1.0:
                vol_score = 10
                signals.append(f"Above average volume: {vol_ratio:.2f}x")
            else:
                vol_score = 5
                signals.append(f"Below average volume: {vol_ratio:.2f}x")

            score += vol_score

        # MACD Momentum (10% weight)
        macd = current['MACD']
        macd_signal = current['MACD_signal']

        if macd > macd_signal:
            macd_score = 10
            signals.append("MACD bullish (positive histogram)")
        else:
            macd_score = 0
            signals.append("MACD bearish")

        score += macd_score

        return {
            'score': min(100, max(0, score)),
            'signals': signals,
            'rsi': rsi,
            'adx': adx,
            'price': price,
            'sma20': sma20,
            'sma50': sma50
        }

    except Exception as e:
        return {'score': 0, 'signals': [], 'error': str(e)}

# ============================================================================
# SCREENING ENGINE
# ============================================================================

def screen_stocks(stock_list: List[str], min_score: float = DEFAULT_MIN_SCORE,
                 max_stocks: Optional[int] = None) -> List[Dict]:
    """Screen multiple stocks and return sorted results"""
    results = []
    total = min(max_stocks, len(stock_list)) if max_stocks else len(stock_list)

    print(f"🔍 Screening {total} stocks for high-probability PCS setups...")

    for idx, symbol in enumerate(stock_list[:total]):
        print(f"  [{idx+1}/{total}] Analyzing {symbol}...", end='\r')

        data = fetch_stock_data(symbol)
        if data is None:
            continue

        analysis = calculate_pattern_score(data)
        score = analysis.get('score', 0)

        if score >= min_score:
            results.append({
                'symbol': symbol,
                'score': score,
                'rsi': analysis.get('rsi'),
                'adx': analysis.get('adx'),
                'price': analysis.get('price'),
                'sma20': analysis.get('sma20'),
                'sma50': analysis.get('sma50'),
                'signals': analysis.get('signals', [])
            })

    print(f"\n✅ Screening complete. Found {len(results)} high-probability setups.\n")

    # Sort by score (highest first)
    return sorted(results, key=lambda x: x['score'], reverse=True)

# ============================================================================
# TELEGRAM NOTIFICATION
# ============================================================================

def send_telegram_message(message: str) -> bool:
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable notifications.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

def format_results_for_telegram(results: List[Dict]) -> str:
    """Format screening results for Telegram"""
    if not results:
        return "❌ No high-probability PCS setups found in today's screening."

    timestamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")

    message = f"""
<b>📊 NSE F&O PCS SCREENING RESULTS</b>
<i>{timestamp}</i>

<b>🎯 High-Probability Setups Found: {len(results)}</b>

"""

    for idx, stock in enumerate(results[:10], 1):  # Top 10 only for Telegram
        message += f"""<b>{idx}. {stock['symbol']}</b>
Score: {stock['score']:.1f}/100 | RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}
Price: ₹{stock['price']:.2f} | SMA20: ₹{stock['sma20']:.2f}
Signals: {', '.join(stock['signals'][:2])}

"""

    if len(results) > 10:
        message += f"\n📈 <b>... and {len(results) - 10} more setups</b>"

    message += f"""
<b>Setup Recommendations:</b>
• HIGH Confidence (Score 75+): Use conservative strike selection
• MEDIUM Confidence (60-74): Moderate strikes with balanced risk
• LOW Confidence (<60): Aggressive strikes, higher risk

<i>⚠️ Disclaimer: This is not financial advice. Paper trade first.</i>
"""

    return message

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "="*60)
    print("NSE F&O PCS SCREENING & TELEGRAM NOTIFICATION")
    print("="*60 + "\n")

    # Run screening
    results = screen_stocks(COMPLETE_NSE_FO_UNIVERSE, min_score=DEFAULT_MIN_SCORE)

    # Display results locally
    print("\n📊 TOP RESULTS:")
    print("-" * 60)

    if results:
        for idx, stock in enumerate(results[:10], 1):
            print(f"{idx}. {stock['symbol']:12} Score: {stock['score']:6.1f}/100 RSI: {stock['rsi']:5.1f} ADX: {stock['adx']:5.1f}")
    else:
        print("No high-probability setups found.")

    # Save results to CSV
    if results:
        df = pd.DataFrame(results)
        csv_path = f"/tmp/nse_pcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        print(f"\n💾 Results saved to: {csv_path}")

    # Send Telegram notification
    print("\n📱 Sending Telegram notification...")
    message = format_results_for_telegram(results)

    if send_telegram_message(message):
        print("✅ Message sent successfully to Telegram!")
    else:
        print(message)  # Print to console as fallback

    print("\n" + "="*60)
    print(f"Scan completed: {len(results)} high-probability setups found")
    print("="*60 + "\n")

    return len(results)

if __name__ == "__main__":
    main()
