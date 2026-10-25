#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Standalone Scheduled Task
Runs PCS analysis and sends results to Telegram
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Try to import yfinance
try:
    import yfinance as yf
except ImportError:
    print("Error: yfinance not installed. Install with: pip install yfinance")
    sys.exit(1)

# Telegram configuration from environment
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# NSE F&O Stocks - Top Liquid Stocks
HIGH_LIQUIDITY_STOCKS = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS',
    'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS',
    'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS',
]

def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️  Error sending Telegram message: {e}")
        return False

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        data = yf.download(symbol, period=period, progress=False, threads=False)
        if data.empty or len(data) < 20:
            return None
        return data
    except Exception:
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi[-1]

def calculate_macd(prices):
    """Calculate MACD"""
    if len(prices) < 26:
        return None, None, None

    ema12 = pd.Series(prices).ewm(span=12).mean()
    ema26 = pd.Series(prices).ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()

    return macd.iloc[-1], signal.iloc[-1], macd.iloc[-1] - signal.iloc[-1]

def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    if len(close) < period:
        return None

    # Calculate TR
    tr1 = high - low
    tr2 = np.abs(high - close.shift())
    tr3 = np.abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    # Plus and Minus DM
    up = high.diff()
    down = -low.diff()

    pos_dm = up.copy()
    pos_dm[pos_dm < 0] = 0
    pos_dm[down > up] = 0

    neg_dm = down.copy()
    neg_dm[neg_dm < 0] = 0
    neg_dm[up > down] = 0

    di_plus = 100 * pos_dm.rolling(period).mean() / atr
    di_minus = 100 * neg_dm.rolling(period).mean() / atr

    di_diff = (di_plus - di_minus).abs()
    di_sum = di_plus + di_minus

    adx = 100 * di_diff.rolling(period).mean() / di_sum
    return adx.iloc[-1]

def calculate_pcs_score(data, symbol):
    """
    Calculate Put Credit Spread (PCS) Score
    Based on bullish momentum, trend strength, and support proximity
    """
    try:
        if len(data) < 30:
            return None

        close = data['Close'].values
        high = data['High'].values
        low = data['Low'].values
        volume = data['Volume'].values

        score = 0

        # 1. RSI Component (30%)
        current_rsi = calculate_rsi(close)
        if current_rsi is None:
            return None

        if 45 <= current_rsi <= 65:
            rsi_score = 30
        elif 40 <= current_rsi < 45 or 65 < current_rsi <= 70:
            rsi_score = 20
        elif 35 <= current_rsi < 40 or 70 < current_rsi <= 75:
            rsi_score = 10
        else:
            rsi_score = 0
        score += rsi_score

        # 2. MACD Component (25%)
        macd, signal, macd_diff = calculate_macd(close)
        if macd is None:
            return None

        if macd > signal and macd_diff > 0:
            macd_score = 25
        elif macd > signal or macd_diff > 0:
            macd_score = 15
        else:
            macd_score = 0
        score += macd_score

        # 3. Support Proximity (20%)
        current_price = close[-1]
        sma20 = pd.Series(close).rolling(20).mean().iloc[-1]

        if sma20 is not None and not np.isnan(sma20):
            distance_from_support = abs(current_price - sma20) / sma20

            if distance_from_support < 0.02:  # Within 2% of support
                support_score = 20
            elif distance_from_support < 0.05:  # Within 5%
                support_score = 15
            elif distance_from_support < 0.08:  # Within 8%
                support_score = 10
            else:
                support_score = 5
        else:
            support_score = 5
        score += support_score

        # 4. Volume Component (10%)
        vol_sma = pd.Series(volume).rolling(20).mean().iloc[-1]
        if vol_sma > 0:
            volume_ratio = volume[-1] / vol_sma
            if volume_ratio > 1.5:
                volume_score = 10
            elif volume_ratio > 1.2:
                volume_score = 7
            elif volume_ratio > 1.0:
                volume_score = 5
            else:
                volume_score = 0
        else:
            volume_score = 0
        score += volume_score

        # 5. ADX Component (15%)
        adx = calculate_adx(
            pd.Series(high),
            pd.Series(low),
            pd.Series(close)
        )

        if adx is not None and not np.isnan(adx):
            if adx > 25:
                adx_score = 15
            elif adx > 20:
                adx_score = 10
            elif adx > 15:
                adx_score = 5
            else:
                adx_score = 0
        else:
            adx_score = 0
        score += adx_score

        return min(max(score, 0), 100)

    except Exception as e:
        return None

def scan_stock(symbol, min_score=60):
    """Scan a single stock for PCS opportunities"""
    try:
        # Fetch data
        data = fetch_stock_data(symbol, period="3mo")
        if data is None:
            return None

        # Calculate PCS score
        pcs_score = calculate_pcs_score(data, symbol)
        if pcs_score is None or pcs_score < min_score:
            return None

        # Get current price
        current_price = data['Close'].iloc[-1]

        # Calculate RSI
        rsi = calculate_rsi(data['Close'].values)

        return {
            'Symbol': symbol,
            'Price': float(current_price),
            'Score': float(pcs_score),
            'RSI': float(rsi) if rsi else None
        }

    except Exception:
        return None

def format_telegram_message(results_df):
    """Format results for Telegram"""
    if results_df.empty:
        return "🔍 <b>NSE PCS Scan Complete</b>\n\n❌ No stocks meeting filter criteria found today."

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%H:%M IST')

    message = f"🔍 <b>NSE PCS Scan Results</b>\n"
    message += f"<i>Updated: {current_time}</i>\n\n"

    # Top results
    top_results = results_df.head(10)

    for idx, row in top_results.iterrows():
        symbol = row['Symbol'].replace('.NS', '')
        score = row['Score']
        price = row['Price']

        # Score emoji
        if score >= 75:
            emoji = "🟢"
        elif score >= 60:
            emoji = "🟡"
        else:
            emoji = "🔴"

        message += f"{emoji} <b>{symbol}</b> • {score:.0f}\n"
        message += f"   Price: ₹{price:.2f}\n"

    message += f"\n📊 Total: {len(results_df)} stocks matched\n"
    message += "📈 <i>Trade Smart. Trade Safe.</i>"

    return message

def run_pcs_scan(stocks=None, min_score=60, max_workers=3):
    """Run the PCS screening"""
    if stocks is None:
        stocks = HIGH_LIQUIDITY_STOCKS

    ist = pytz.timezone('Asia/Kolkata')
    print("\n" + "=" * 70)
    print("🚀 NSE F&O PCS Screener - Scheduled Scan")
    print("=" * 70)

    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    print(f"\n⏰ Started at: {current_time}")
    print(f"📊 Scanning {len(stocks)} stocks with min score: {min_score}\n")

    results = []
    completed = 0

    # Use ThreadPoolExecutor for concurrent scanning
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(scan_stock, symbol, min_score): symbol
            for symbol in stocks
        }

        for future in as_completed(futures):
            symbol = futures[future]
            completed += 1
            clean_symbol = symbol.replace('.NS', '')

            try:
                result = future.result()
                if result:
                    results.append(result)
                    print(f"[{completed:2d}/{len(stocks)}] {clean_symbol:12s} ✅ Score: {result['Score']:6.1f}")
                else:
                    print(f"[{completed:2d}/{len(stocks)}] {clean_symbol:12s} ⏭️  No match")
            except Exception as e:
                print(f"[{completed:2d}/{len(stocks)}] {clean_symbol:12s} ❌ Error")

    # Create results dataframe
    if results:
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('Score', ascending=False)

        print(f"\n{'='*70}")
        print(f"✅ Scan Complete! Found {len(results_df)} stocks")
        print(f"{'='*70}\n")

        print(results_df.to_string(index=False))

        # Save results
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        csv_file = f"/tmp/nse_pcs_results_{timestamp}.csv"
        results_df.to_csv(csv_file, index=False)
        print(f"\n💾 Results saved to: {csv_file}")

        # Send Telegram message
        print("\n📱 Sending results to Telegram...")
        message = format_telegram_message(results_df)
        send_telegram_message(message)

        return results_df
    else:
        print(f"\n{'='*70}")
        print("❌ No stocks found meeting the filter criteria")
        print(f"{'='*70}\n")

        # Send notification to Telegram
        message = format_telegram_message(pd.DataFrame())
        send_telegram_message(message)

        return pd.DataFrame()

if __name__ == "__main__":
    try:
        # Run scan with default settings
        results = run_pcs_scan(
            stocks=HIGH_LIQUIDITY_STOCKS,
            min_score=60
        )
        print("\n✅ Task completed successfully!")
    except KeyboardInterrupt:
        print("\n⚠️  Task interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Task failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
