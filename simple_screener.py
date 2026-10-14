#!/usr/bin/env python3
"""
Simple NSE F&O Stock Screener with Telegram Integration
Screens stocks for bullish patterns and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime, timedelta
import pytz
import requests

def calculate_rsi(data, period=14):
    """Calculate RSI indicator"""
    if len(data) < period:
        return None

    closes = data['Close'].values
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]

    seed = deltas[:period]
    up = sum([x for x in seed if x > 0]) / period
    down = -sum([x for x in seed if x < 0]) / period

    rs = up / down if down != 0 else 0
    rsi = 100 - (100 / (1 + rs))

    for i in range(period, len(deltas)):
        delta = deltas[i]
        if delta > 0:
            up_val = delta
            down_val = 0
        else:
            up_val = 0
            down_val = -delta

        up = (up * (period - 1) + up_val) / period
        down = (down * (period - 1) + down_val) / period

        rs = up / down if down != 0 else 0
        rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_sma(data, period=20):
    """Calculate Simple Moving Average"""
    if len(data) < period:
        return None
    return data['Close'].tail(period).mean()


def calculate_volume_change(data, period=5):
    """Calculate volume change ratio"""
    if len(data) < period:
        return 1.0

    avg_vol = data['Volume'].tail(period).mean()
    current_vol = data['Volume'].iloc[-1]

    return current_vol / avg_vol if avg_vol > 0 else 1.0


def is_above_support(data, support_lookback=20):
    """Check if price is above support level (SMA 20)"""
    if len(data) < support_lookback:
        return True

    sma_20 = calculate_sma(data, support_lookback)
    current_price = data['Close'].iloc[-1]

    if sma_20 is None:
        return True

    # Price should be above SMA 20 with small tolerance
    return current_price >= sma_20 * 0.97  # 3% tolerance


def detect_breakout(data, lookback_days=20):
    """Detect if price has broken out above recent resistance"""
    if len(data) < lookback_days:
        return False, 0

    recent_data = data.tail(lookback_days)
    high_price = recent_data['High'].iloc[-1]
    previous_high = recent_data['High'].iloc[:-1].max()

    if previous_high == 0:
        return False, 0

    breakout_strength = ((high_price - previous_high) / previous_high) * 100

    # Breakout occurs if current high is above previous high
    return high_price > previous_high, breakout_strength


def detect_bullish_pattern(data, symbol):
    """Detect simple bullish patterns"""
    patterns = []

    try:
        # Pattern 1: Price above SMA with high volume
        if len(data) >= 20:
            sma_20 = calculate_sma(data, 20)
            current_price = data['Close'].iloc[-1]
            rsi = calculate_rsi(data, 14)
            vol_ratio = calculate_volume_change(data, 5)

            if sma_20 and current_price > sma_20 and rsi and 40 <= rsi <= 75 and vol_ratio > 1.0:
                patterns.append({
                    'name': 'Bullish Trend',
                    'strength': min(85, 50 + (vol_ratio - 1) * 20),
                    'description': f'Price above SMA20, RSI={rsi:.0f}, Volume={vol_ratio:.1f}x'
                })

        # Pattern 2: Recent breakout
        breakout, strength = detect_breakout(data, 20)
        if breakout and strength > 0.5:
            patterns.append({
                'name': 'Breakout Signal',
                'strength': min(90, 60 + strength),
                'description': f'Price breakout ({strength:.2f}%)'
            })

        # Pattern 3: Volume confirmation
        if len(data) >= 5:
            vol_ratio = calculate_volume_change(data, 5)
            if vol_ratio > 1.5:
                patterns.append({
                    'name': 'Volume Surge',
                    'strength': min(80, 50 + (vol_ratio - 1) * 15),
                    'description': f'Above-average volume ({vol_ratio:.1f}x)'
                })

    except Exception as e:
        pass

    return patterns


def screen_stocks():
    """Screen stocks and return results"""

    print("=" * 70)
    print("NSE F&O PCS SCREENER - TELEGRAM AUTOMATION")
    print("=" * 70)

    # Get Telegram credentials
    telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if telegram_token and telegram_chat_id:
        print(f"\n✓ Telegram configured for chat: {telegram_chat_id}")
        send_telegram = True
    else:
        print("\n⚠️  Telegram credentials not found in environment variables")
        print("   Set: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        send_telegram = False

    # Import yfinance
    try:
        import yfinance as yf
        import pandas as pd
    except ImportError:
        print("Error: yfinance not installed")
        return False

    # Stock universe - top 30 liquid F&O stocks
    stocks = [
        'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
        'SBIN.NS', 'MARUTI.NS', 'WIPRO.NS', 'BAJFINANCE.NS', 'KOTAKBANK.NS',
        'AXISBANK.NS', 'ASIANPAINT.NS', 'SUNPHARMA.NS', 'HCLTECH.NS', 'TATAMOTORS.NS',
        'ADANIPORTS.NS', 'LTIM.NS', 'BHARTIARTL.NS', 'TITAN.NS', 'BAJAJFINSV.NS',
        'TECHM.NS', 'ONGC.NS', 'POWERGRID.NS', 'NTPC.NS', 'COALINDIA.NS',
        'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS', 'INDUSINDBK.NS', 'SHRIRAMFIN.NS'
    ]

    print(f"\n📊 Screening {len(stocks)} stocks...")

    results = []
    ist = pytz.timezone('Asia/Kolkata')

    for symbol in stocks:
        try:
            # Get 3 months of data
            stock = yf.Ticker(symbol)
            data = stock.history(period='3mo')

            if data.empty or len(data) < 20:
                continue

            # Get current price
            current_price = data['Close'].iloc[-1]

            # Detect patterns
            patterns = detect_bullish_pattern(data, symbol)

            if not patterns:
                continue

            # Calculate metrics
            rsi = calculate_rsi(data, 14)
            vol_ratio = calculate_volume_change(data, 5)
            max_strength = max([p['strength'] for p in patterns])

            # Determine confidence
            confidence = 'HIGH' if max_strength >= 80 else 'MEDIUM' if max_strength >= 65 else 'LOW'

            result = {
                'symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': rsi if rsi else 0,
                'volume_ratio': vol_ratio,
                'patterns': patterns,
                'max_strength': max_strength,
                'confidence': confidence
            }

            results.append(result)
            print(f"  ✓ {result['symbol']} ({confidence} - {max_strength:.0f}%)")

        except Exception as e:
            continue

    # Format results
    if not results:
        message = "❌ No stocks found matching filter criteria"
    else:
        # Sort by strength
        results.sort(key=lambda x: x['max_strength'], reverse=True)

        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

        message = f"""🎯 NSE F&O PCS SCREENER
📅 {current_time}

📊 STOCKS FOUND: {len(results)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        for i, r in enumerate(results[:10], 1):  # Top 10
            emoji = '🟢' if r['confidence'] == 'HIGH' else '🟡' if r['confidence'] == 'MEDIUM' else '🔴'

            message += f"""{i}. {r['symbol']} {emoji}
   Price: ₹{r['price']:.2f}
   RSI: {r['rsi']:.0f} | Vol: {r['volume_ratio']:.1f}x
   Strength: {r['max_strength']:.0f}%

"""

        if len(results) > 10:
            message += f"\n... and {len(results) - 10} more stocks\n"

        message += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  Disclaimer: For educational purposes only.
    Not financial advice. Always use proper risk management.
"""

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(message)

    # Save to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"/home/user/nsepcs/screening_results_{timestamp}.txt"

    try:
        with open(output_file, 'w') as f:
            f.write(message)
        print(f"\n✓ Results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving file: {e}")

    # Send to Telegram
    if send_telegram:
        try:
            print("\n📤 Sending to Telegram...")
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

            # Chunk message if too long
            max_length = 4096
            if len(message) > max_length:
                # Send in chunks
                for i in range(0, len(message), max_length):
                    chunk = message[i:i+max_length]
                    requests.post(url, json={
                        'chat_id': telegram_chat_id,
                        'text': chunk,
                        'parse_mode': 'HTML'
                    }, timeout=10)
            else:
                response = requests.post(url, json={
                    'chat_id': telegram_chat_id,
                    'text': message,
                    'parse_mode': 'HTML'
                }, timeout=10)

                if response.status_code == 200:
                    print("✓ Message sent to Telegram!")
                else:
                    print(f"❌ Telegram error: {response.text}")
        except Exception as e:
            print(f"❌ Error sending to Telegram: {e}")

    return True


if __name__ == "__main__":
    try:
        success = screen_stocks()
        if success:
            print("\n✅ Screening completed!")
            sys.exit(0)
        else:
            print("\n❌ Screening failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⛔ Screening cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
