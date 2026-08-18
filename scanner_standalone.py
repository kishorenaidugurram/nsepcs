#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - No Streamlit dependency
Sends results to Telegram
"""

import sys
import os
import json
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd
import yfinance as yf
import requests

# Stock Universe
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS',
    'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS',
    'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS',
    'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS',
    'BEL.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    gains = deltas.copy()
    losses = deltas.copy()

    gains[gains < 0] = 0
    losses[losses > 0] = 0
    losses = -losses

    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])

    if avg_loss == 0:
        return 100 if avg_gain > 0 else 0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    if len(high) < period + 1:
        return None

    tr1 = high - low
    tr2 = np.abs(high - np.concatenate(([close[0]], close[:-1])))
    tr3 = np.abs(low - np.concatenate(([close[0]], close[:-1])))

    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    atr = np.mean(tr[-period:])

    return min(100, atr / close[-1] * 100 * 14)

def detect_volume_breakout(data, min_volume_ratio=1.2):
    """Detect if current day has volume breakout"""
    if len(data) < 20:
        return False, 1.0

    current_volume = data['Volume'].iloc[-1]
    avg_volume_20 = data['Volume'].iloc[-21:-1].mean()

    volume_ratio = current_volume / avg_volume_20
    return volume_ratio >= min_volume_ratio, volume_ratio

def detect_price_breakout(data, lookback_days=20, min_breakout_pct=1.0):
    """Detect if price broke out above resistance"""
    if len(data) < lookback_days + 1:
        return False, 0

    lookback_data = data.iloc[-(lookback_days + 1):-1]
    current_data = data.iloc[-1]

    resistance = lookback_data['High'].max()
    support = lookback_data['Low'].min()

    current_close = current_data['Close']
    current_high = current_data['High']

    # Check if price broke resistance
    breakout_pct = ((current_close - resistance) / resistance) * 100

    if breakout_pct >= min_breakout_pct and current_high > resistance:
        return True, breakout_pct

    return False, breakout_pct

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        return data
    except Exception as e:
        print(f"   ⚠️  Error fetching {symbol}: {str(e)[:30]}")
        return None

def scan_stock(symbol, filters):
    """Scan a single stock for trading setups"""
    try:
        # Fetch data
        data = fetch_stock_data(symbol, period="3mo")
        if data is None:
            return None

        if len(data) < 20:
            return None

        # Calculate indicators
        close_prices = data['Close'].values
        high_prices = data['High'].values
        low_prices = data['Low'].values

        rsi = calculate_rsi(close_prices)
        adx = calculate_adx(high_prices, low_prices, close_prices)

        if rsi is None or adx is None:
            return None

        # Check RSI filter
        if not (filters['rsi_min'] <= rsi <= filters['rsi_max']):
            return None

        # Check ADX filter
        if adx < filters['adx_min']:
            return None

        # Check volume breakout
        volume_ok, volume_ratio = detect_volume_breakout(data, filters['min_volume_ratio'])
        if not volume_ok:
            return None

        # Check price breakout
        breakout_detected, breakout_pct = detect_price_breakout(data, filters['lookback_days'])
        if not breakout_detected:
            return None

        # Get current price
        current_price = data['Close'].iloc[-1]

        return {
            'symbol': symbol,
            'clean_symbol': symbol.replace('.NS', ''),
            'current_price': current_price,
            'rsi': rsi,
            'adx': adx,
            'volume_ratio': volume_ratio,
            'breakout_pct': breakout_pct,
            'strength': min(100, (breakout_pct * 2) + (rsi / 100 * 30) + (adx / 50 * 30))
        }

    except Exception as e:
        return None

def send_to_telegram(message, results=None):
    """Send results to Telegram"""
    try:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        full_message = message
        if results and len(results) > 0:
            full_message += f"\n\n📊 Stocks Found: {len(results)}\n\n"
            for i, result in enumerate(results[:15], 1):
                symbol = result['clean_symbol']
                price = result['current_price']
                strength = result['strength']
                breakout = result['breakout_pct']
                full_message += f"{i}. {symbol} - ₹{price:.2f} | Strength: {strength:.0f}% | Breakout: {breakout:.2f}%\n"

            if len(results) > 15:
                full_message += f"\n... and {len(results) - 15} more stocks"

        payload = {
            'chat_id': chat_id,
            'text': full_message,
            'parse_mode': 'HTML'
        }

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        print(f"⚠️  Telegram error: {str(e)[:50]}")
        return False

def run_scanner():
    """Main scanner execution"""

    # Filter configuration
    filters = {
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'min_volume_ratio': 1.2,
        'lookback_days': 20,
    }

    ist = pytz.timezone('Asia/Kolkata')
    print("="*70)
    print(f"🚀 NSE F&O PCS Scanner - Standalone Version")
    print(f"⏰ {datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} F&O stocks")
    print(f"⚙️  RSI: {filters['rsi_min']}-{filters['rsi_max']} | ADX > {filters['adx_min']} | Vol Ratio > {filters['min_volume_ratio']}x")
    print("="*70)

    results = []
    failed = 0
    skipped = 0

    for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE, 1):
        clean = symbol.replace('.NS', '')
        print(f"[{i:3d}/{len(COMPLETE_NSE_FO_UNIVERSE)}] {clean:12s} ", end='', flush=True)

        try:
            result = scan_stock(symbol, filters)
            if result:
                results.append(result)
                print(f"✅ Strength: {result['strength']:5.1f}% | Price: ₹{result['current_price']:8.2f}")
            else:
                print("⊘")
                skipped += 1
        except Exception as e:
            print(f"❌ {str(e)[:20]}")
            failed += 1

    print("\n" + "="*70)
    print(f"📊 RESULTS SUMMARY")
    print(f"✅ Matching stocks: {len(results)}")
    print(f"⊘ Filtered out: {skipped}")
    print(f"❌ Errors: {failed}")
    print("="*70)

    if results:
        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)

        print("\n📈 TOP 10 RESULTS:")
        print("-" * 70)
        print(f"{'#':3} {'Symbol':12} {'Price':>10} {'RSI':>7} {'ADX':>7} {'Vol':>8} {'Strength':>10}")
        print("-" * 70)

        for i, result in enumerate(results[:10], 1):
            print(f"{i:3d} {result['clean_symbol']:12} ₹{result['current_price']:8.2f}  "
                  f"{result['rsi']:6.1f}  {result['adx']:6.1f}  "
                  f"{result['volume_ratio']:7.2f}x  {result['strength']:9.1f}%")

        if len(results) > 10:
            print(f"\n... and {len(results) - 10} more stocks meeting criteria")

        # Save results
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            json_file = f"/tmp/scanner_{ts}.json"

            with open(json_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now(ist).isoformat(),
                    'total': len(results),
                    'stocks': [
                        {
                            'symbol': r['clean_symbol'],
                            'price': float(r['current_price']),
                            'rsi': float(r['rsi']),
                            'adx': float(r['adx']),
                            'volume': float(r['volume_ratio']),
                            'strength': float(r['strength'])
                        }
                        for r in results
                    ]
                }, f, indent=2)

            print(f"\n💾 Results saved: {json_file}")
        except Exception as e:
            print(f"⚠️  Save error: {e}")

        # Send to Telegram
        msg = f"📊 <b>NSE F&O PCS Scanner</b>\n⏰ {datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')}\n🎯 Found: {len(results)} stocks"
        if send_to_telegram(msg, results):
            print("✅ Results sent to Telegram")
        else:
            print("⚠️  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
    else:
        msg = "❌ No stocks found matching filter criteria"
        send_to_telegram(msg, None)
        print("\n" + msg)

    print("="*70)
    return len(results)

if __name__ == "__main__":
    try:
        count = run_scanner()
        sys.exit(0 if count > 0 else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
