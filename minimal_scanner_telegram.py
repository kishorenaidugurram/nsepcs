#!/usr/bin/env python3
"""
Minimal standalone NSE PCS scanner with Telegram integration
No external dependencies beyond basic packages
"""

import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# NSE F&O Universe
COMPLETE_NSE_FO_UNIVERSE = [
    'NIFTY.NS', 'BANKNIFTY.NS', 'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS',
    'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS',
    'KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS',
    'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS',
    'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS',
    'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS'
]


def calculate_rsi(data, period=14):
    """Calculate RSI (Relative Strength Index)"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    ema_fast = data.ewm(span=fast).mean()
    ema_slow = data.ewm(span=slow).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=std_dev).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band


def fetch_stock_data(symbol, period='3mo'):
    """Fetch stock data from yfinance"""
    try:
        data = yf.download(symbol, period=period, progress=False)
        if data is None or len(data) < 2:
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data['Close'])

        macd_line, signal_line, histogram = calculate_macd(data['Close'])
        data['MACD'] = macd_line
        data['MACD_Signal'] = signal_line
        data['MACD_Histogram'] = histogram

        upper_band, middle_band, lower_band = calculate_bollinger_bands(data['Close'])
        data['BB_Upper'] = upper_band
        data['BB_Middle'] = middle_band
        data['BB_Lower'] = lower_band
        data['BB_Width'] = (upper_band - lower_band) / middle_band

        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['Volume_MA'] = data['Volume'].rolling(window=20).mean()

        # Simple ADX calculation
        data['ADX'] = 25  # Placeholder

        return data

    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None


def detect_patterns(data, symbol):
    """Detect simple technical patterns"""
    patterns = []

    if data is None or len(data) < 5:
        return patterns

    try:
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        avg_volume = data['Volume_MA'].iloc[-1]

        # Get recent candles
        close = data['Close']
        high = data['High']
        low = data['Low']

        # Pattern 1: RSI Oversold Bounce (RSI < 40)
        if 25 < current_rsi < 40:
            if close.iloc[-1] > close.iloc[-2]:  # Bullish candle
                if current_volume > avg_volume * 1.2:  # Volume confirmation
                    patterns.append({
                        'type': 'RSI Oversold Bounce',
                        'strength': 0.65,
                        'confidence': 'MEDIUM'
                    })

        # Pattern 2: Recent Breakout (Volume spike + Price up)
        if current_volume > avg_volume * 2.5:
            recent_high = high.iloc[-5:].max()
            if current_price >= recent_high * 0.98:
                if close.iloc[-1] > close.iloc[-2]:
                    patterns.append({
                        'type': 'Volume Breakout',
                        'strength': 0.72,
                        'confidence': 'HIGH'
                    })

        # Pattern 3: Bollinger Band touches
        bb_lower = data['BB_Lower'].iloc[-1]
        bb_upper = data['BB_Upper'].iloc[-1]
        bb_middle = data['BB_Middle'].iloc[-1]

        if current_price <= bb_lower * 1.02 and close.iloc[-1] > close.iloc[-2]:
            patterns.append({
                'type': 'Bollinger Band Lower Touch',
                'strength': 0.68,
                'confidence': 'MEDIUM'
            })

        # Pattern 4: MACD Bullish Crossover
        macd_hist = data['MACD_Histogram']
        if len(macd_hist) > 2:
            if macd_hist.iloc[-1] > 0 and macd_hist.iloc[-2] <= 0:
                patterns.append({
                    'type': 'MACD Bullish Crossover',
                    'strength': 0.70,
                    'confidence': 'MEDIUM'
                })

        # Pattern 5: Volume above average
        if current_volume > avg_volume * 1.5 and close.iloc[-1] > close.iloc[-2]:
            patterns.append({
                'type': 'Above-Average Volume on Up Move',
                'strength': 0.60,
                'confidence': 'LOW'
            })

    except Exception as e:
        print(f"Error detecting patterns for {symbol}: {e}")

    return patterns


def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram not configured - message not sent")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            },
            timeout=10
        )

        if response.status_code == 200:
            print("✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


def run_scanner():
    """Run the stock scanner"""
    print("\n" + "="*70)
    print("NSE F&O TECHNICAL SCANNER - Telegram Edition")
    print("="*70)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} stocks for technical patterns\n")

    results = []

    for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE, 1):
        clean_symbol = symbol.replace('.NS', '')
        print(f"[{i:2d}/{len(COMPLETE_NSE_FO_UNIVERSE)}] Analyzing {clean_symbol:12s} ... ", end="", flush=True)

        try:
            # Fetch data
            data = fetch_stock_data(symbol, period='3mo')

            if data is None:
                print("❌ No data")
                continue

            # Detect patterns
            patterns = detect_patterns(data, symbol)

            if not patterns:
                print("❌ No patterns")
                continue

            # Get current metrics
            current_price = float(data['Close'].iloc[-1])
            current_rsi = float(data['RSI'].iloc[-1])
            current_volume = float(data['Volume'].iloc[-1])
            avg_volume = float(data['Volume_MA'].iloc[-1])
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0

            # Store result
            stock_result = {
                'symbol': clean_symbol,
                'price': current_price,
                'rsi': current_rsi,
                'volume_ratio': volume_ratio,
                'patterns': patterns,
                'num_patterns': len(patterns),
                'avg_strength': np.mean([p['strength'] for p in patterns])
            }

            results.append(stock_result)
            print(f"✅ {len(patterns)} pattern(s) detected")

        except Exception as e:
            print(f"❌ Error: {str(e)[:40]}")
            continue

    print("\n" + "="*70)
    print(f"✅ Scan Complete! Found {len(results)} stocks with patterns")
    print("="*70 + "\n")

    return results


def format_telegram_report(results):
    """Format results for Telegram"""
    if not results:
        return "❌ <b>No stocks found with technical patterns today</b>"

    # Sort by average pattern strength
    results.sort(key=lambda x: x['avg_strength'], reverse=True)

    message = f"<b>📊 NSE Technical Scanner Report</b>\n"
    message += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n"
    message += f"<b>✅ Found {len(results)} Stocks with Technical Patterns</b>\n"
    message += "━" * 50 + "\n\n"

    # Show top 15 stocks
    for i, stock in enumerate(results[:15], 1):
        message += f"<b>{i}. {stock['symbol']}</b>\n"
        message += f"💰 Price: ₹{stock['price']:.2f}\n"
        message += f"📈 RSI: {stock['rsi']:.1f} | Vol Ratio: {stock['volume_ratio']:.2f}x\n"
        message += f"🎯 Patterns ({stock['num_patterns']}): "

        pattern_names = [p['type'] for p in stock['patterns'][:2]]
        message += ", ".join(pattern_names)
        if stock['num_patterns'] > 2:
            message += f" (+{stock['num_patterns']-2} more)"

        message += "\n"
        message += "─" * 50 + "\n"

    if len(results) > 15:
        message += f"\n<i>... and {len(results) - 15} more stocks</i>\n"

    message += f"\n<b>Total Patterns Found:</b> {sum(s['num_patterns'] for s in results)}\n"
    message += f"<b>Average RSI:</b> {np.mean([s['rsi'] for s in results]):.1f}\n"

    return message


def save_to_csv(results):
    """Save results to CSV"""
    if not results:
        return None

    data = []
    for stock in results:
        for pattern in stock['patterns']:
            data.append({
                'Symbol': stock['symbol'],
                'Price': f"₹{stock['price']:.2f}",
                'RSI': f"{stock['rsi']:.1f}",
                'Volume_Ratio': f"{stock['volume_ratio']:.2f}x",
                'Pattern': pattern['type'],
                'Strength': f"{pattern['strength']:.2f}",
                'Confidence': pattern['confidence'],
                'Scan_Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })

    df = pd.DataFrame(data)
    filename = f"/tmp/nse_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ Results saved to: {filename}")

    return filename


def main():
    """Main execution"""

    # Check Telegram config
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  WARNING: Telegram not configured!")
        print("Set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN=<your_bot_token>")
        print("  export TELEGRAM_CHAT_ID=<your_chat_id>")
        print()

    # Run scanner
    results = run_scanner()

    if not results:
        print("❌ No results to report")
        msg = "❌ NSE Scanner ran but found no stocks with significant patterns"
        send_telegram_message(msg)
        return

    # Format and send report
    telegram_report = format_telegram_report(results)
    print("\n" + "="*70)
    print("📱 TELEGRAM REPORT:")
    print("="*70)
    print(telegram_report)
    print("="*70 + "\n")

    # Send to Telegram
    send_telegram_message(telegram_report)

    # Save to CSV
    csv_file = save_to_csv(results)

    print("\n✅ Scanner execution complete!")


if __name__ == "__main__":
    main()
