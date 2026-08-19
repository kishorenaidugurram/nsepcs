#!/usr/bin/env python3
"""
NSE F&O Stock Analyzer - Simplified Version
Runs basic stock analysis and sends results to Telegram
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import requests
from datetime import datetime, timedelta
import pytz

warnings.filterwarnings('ignore')

# ============ BASIC TECHNICAL INDICATORS ============
def calculate_rsi(prices, period=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def calculate_adx(high, low, close, period=14):
    """Calculate ADX (Average Directional Index) - simplified version"""
    plus_dm = high.diff()
    minus_dm = -low.diff()

    # Calculate directional movements
    plus_dm = plus_dm.where(plus_dm > 0, 0)
    minus_dm = minus_dm.where(minus_dm > 0, 0)

    # Calculate ATR
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()

    # Calculate directional indicators
    di_plus = 100 * (plus_dm.rolling(window=period).mean() / atr)
    di_minus = 100 * (minus_dm.rolling(window=period).mean() / atr)

    di_diff = abs(di_plus - di_minus)
    di_sum = di_plus + di_minus

    # Calculate ADX
    dx = 100 * (di_diff / di_sum)
    adx = dx.rolling(window=period).mean()

    return adx


# ============ TELEGRAM CONFIGURATION ============
def get_telegram_credentials():
    """Get Telegram bot token and chat ID from environment or config"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        print("WARNING: Telegram credentials not found in environment variables")
        print("  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram notifications")
        return None, None

    return token, chat_id


def send_to_telegram(message, token, chat_id, parse_mode='HTML'):
    """Send message to Telegram"""
    if not token or not chat_id:
        print("Telegram not configured, skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # Break message into chunks if too long (Telegram limit is 4096 chars)
    max_length = 4096
    if len(message) > max_length:
        messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
    else:
        messages = [message]

    for msg in messages:
        try:
            payload = {
                'chat_id': chat_id,
                'text': msg,
                'parse_mode': parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"Telegram send failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"Error sending to Telegram: {e}")
            return False

    return True


# ============ STOCK ANALYSIS ============
def get_stock_data(symbol, period="3mo"):
    """Get stock data and calculate basic indicators"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['SMA_20'] = calculate_sma(data['Close'], 20)
        data['SMA_50'] = calculate_sma(data['Close'], 50)
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def detect_current_day_breakout(data, lookback_days=20):
    """Detect if current day is a breakout above resistance"""
    if len(data) < lookback_days + 2:
        return False, 0

    current_day = data.iloc[-1]
    lookback_data = data.iloc[-(lookback_days + 1):-1]

    resistance_level = lookback_data['High'].max()
    support_level = lookback_data['Low'].min()

    current_close = current_day['Close']
    current_high = current_day['High']
    current_volume = current_day['Volume']

    # Breakout conditions
    price_breakout = current_close > resistance_level * 1.005
    high_breakout = current_high > resistance_level * 1.01

    # Volume confirmation
    avg_volume = lookback_data['Volume'].mean()
    volume_breakout = current_volume > (avg_volume * 2.0)

    # Consolidation quality
    consolidation_range = ((resistance_level - support_level) / support_level) * 100
    tight_consolidation = consolidation_range < 15

    # Current day confirmed
    current_day_confirmed = price_breakout and volume_breakout and tight_consolidation

    if not current_day_confirmed:
        return False, 0

    # Calculate strength
    strength = 0

    breakout_percentage = ((current_close - resistance_level) / resistance_level) * 100
    if breakout_percentage >= 3:
        strength += 35
    elif breakout_percentage >= 2:
        strength += 25
    elif breakout_percentage >= 1:
        strength += 20
    elif breakout_percentage >= 0.5:
        strength += 15

    volume_ratio = current_volume / avg_volume
    if volume_ratio >= 4:
        strength += 30
    elif volume_ratio >= 3:
        strength += 25
    elif volume_ratio >= 2:
        strength += 20

    if consolidation_range <= 8:
        strength += 25
    elif consolidation_range <= 12:
        strength += 20
    elif consolidation_range <= 15:
        strength += 15

    return True, strength


def analyze_stock(symbol, stock_list_name=""):
    """Analyze a single stock and return results"""
    try:
        print(f"  Analyzing {symbol.replace('.NS', ''):<12}", end='\r')

        # Get data
        data = get_stock_data(symbol, period="3mo")
        if data is None:
            return None

        # Get current metrics
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        current_high = data['High'].iloc[-1]
        current_low = data['Low'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]

        # Check volume (at least 1.5x average)
        avg_volume = data['Volume'].tail(20).mean()
        if current_volume < avg_volume * 1.5:
            return None

        # Check basic filters
        if current_rsi < 20 or current_rsi > 90:  # Extreme RSI
            return None
        if current_adx < 15:  # Weak trend
            return None

        # Detect breakout
        breakout_detected, breakout_strength = detect_current_day_breakout(data, lookback_days=20)

        # Check support/resistance
        resistance_20d = data['High'].tail(20).max()
        support_20d = data['Low'].tail(20).min()

        # Proximity to resistance
        distance_to_resistance = ((resistance_20d - current_price) / resistance_20d) * 100
        is_near_resistance = distance_to_resistance < 5  # Within 5% of resistance

        # Basic momentum score
        sma_20 = data['SMA_20'].iloc[-1]
        sma_50 = data['SMA_50'].iloc[-1]

        # Check if price is above key moving averages
        bullish_trend = current_price > sma_20 > sma_50

        # Calculate overall strength
        strength = 0

        if breakout_detected:
            strength += breakout_strength
        else:
            # Score based on position relative to MAs and support/resistance
            if bullish_trend:
                strength += 40
            elif current_price > sma_20:
                strength += 30
            elif current_price > sma_50:
                strength += 20

        # RSI bonus
        if 40 <= current_rsi <= 70:
            strength += 15
        elif 30 <= current_rsi < 40:
            strength += 10

        # ADX bonus
        if current_adx >= 25:
            strength += 15
        elif current_adx >= 20:
            strength += 10

        # Volume bonus
        volume_ratio = current_volume / avg_volume
        if volume_ratio >= 3:
            strength += 15
        elif volume_ratio >= 2:
            strength += 10

        # Distance from support bonus
        distance_from_support = ((current_price - support_20d) / support_20d) * 100
        if distance_from_support >= 20:
            strength += 10
        elif distance_from_support >= 10:
            strength += 5

        if strength < 50:  # Minimum threshold
            return None

        return {
            'symbol': symbol,
            'clean_symbol': symbol.replace('.NS', '').replace('^', ''),
            'price': current_price,
            'strength': strength,
            'rsi': current_rsi,
            'adx': current_adx,
            'volume_ratio': volume_ratio,
            'breakout': breakout_detected,
            'bullish_trend': bullish_trend,
            'near_resistance': is_near_resistance
        }

    except Exception as e:
        return None


def analyze_stocks(stock_symbols):
    """Analyze multiple stocks"""
    results = []

    print(f"Analyzing {len(stock_symbols)} stocks...")
    for i, symbol in enumerate(stock_symbols):
        result = analyze_stock(symbol)
        if result:
            results.append(result)

    print(f"\n✓ Found {len(results)} stocks meeting criteria")
    return results


def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks found meeting the criteria today."

    # Sort by breakout first, then by strength
    results.sort(key=lambda x: (not x['breakout'], -x['strength']))

    breakout_stocks = [r for r in results if r['breakout']]
    other_stocks = [r for r in results if not r['breakout']]

    timestamp = datetime.now(pytz.timezone('Asia/Kolkata')).strftime("%Y-%m-%d %H:%M IST")

    message = f"""
<b>🎯 NSE Stock Screener Results</b>
<i>{timestamp}</i>

<b>📊 Summary:</b>
• Total qualified: {len(results)}
• Current Day Breakouts: {len(breakout_stocks)}
• Other Setups: {len(other_stocks)}

"""

    # Current day breakouts
    if breakout_stocks:
        message += "<b>🔥 CURRENT DAY BREAKOUTS (Highest Priority):</b>\n"
        for i, stock in enumerate(breakout_stocks[:15], 1):
            message += f"{i}. <b>{stock['clean_symbol']}</b> ₹{stock['price']:.2f} | 💪 {stock['strength']:.0f}% | RSI: {stock['rsi']:.0f} | Vol: {stock['volume_ratio']:.1f}x\n"
        message += "\n"

    # Other stocks
    if other_stocks:
        message += "<b>📈 OTHER QUALIFIED STOCKS:</b>\n"
        for i, stock in enumerate(other_stocks[:15], 1):
            trend = "📈" if stock['bullish_trend'] else "➡️"
            message += f"{i}. <b>{stock['clean_symbol']}</b> ₹{stock['price']:.2f} | 💪 {stock['strength']:.0f}% | RSI: {stock['rsi']:.0f} | Vol: {stock['volume_ratio']:.1f}x {trend}\n"

    # Export list
    message += "\n<b>📋 Quick Stock List:</b>\n<code>"
    all_symbols = [r['clean_symbol'] for r in results[:25]]
    message += ", ".join(all_symbols)
    message += "</code>"

    message += "\n\n<i>Scan completed successfully ✓</i>"

    return message


def main():
    """Main function"""
    print("=" * 70)
    print("NSE STOCK SCREENER - Analysis & Telegram Notification")
    print("=" * 70)

    # Get Telegram credentials
    telegram_token, telegram_chat_id = get_telegram_credentials()

    # Define stocks to analyze - Focus on most liquid NSE F&O stocks
    stocks_to_analyze = [
        # Nifty 50 large caps
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
        'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
        'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
        # Bank Nifty
        'IDFCFIRSTB.NS', 'AUBANK.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'CANBK.NS',
        'FEDERALBNK.NS', 'PNB.NS',
        # Other liquid stocks
        'ADANIENT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
        'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS'
    ]

    print(f"\n📈 Starting analysis of {len(stocks_to_analyze)} stocks...\n")

    # Analyze stocks
    results = analyze_stocks(stocks_to_analyze)

    # Format message
    message = format_telegram_message(results)

    print("\n" + "=" * 70)
    print("MESSAGE:")
    print("=" * 70)
    # Show message without HTML tags in console
    preview = message.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '').replace('<code>', '').replace('</code>', '')
    print(preview)
    print("=" * 70)

    # Send to Telegram
    if telegram_token and telegram_chat_id:
        print("\n📤 Sending to Telegram...")
        if send_to_telegram(message, telegram_token, telegram_chat_id, parse_mode='HTML'):
            print("✅ Message sent successfully!")
        else:
            print("❌ Failed to send message")
    else:
        print("\n⚠️ Telegram not configured")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

    # Save results
    if results:
        df = pd.DataFrame(results)
        csv_file = f"/tmp/nse_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"\n💾 Results saved: {csv_file}")

    print("\n✓ Complete!")


if __name__ == "__main__":
    main()
