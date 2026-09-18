#!/usr/bin/env python3
"""
Standalone PCS Stock Scanner - Automated Batch Run
Analyzes NSE F&O stocks for PCS opportunities and sends results to Telegram
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import yfinance as yf
import ta
from datetime import datetime, timedelta
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import pytz

warnings.filterwarnings('ignore')

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# NSE F&O Universe (top 60 liquid stocks)
TOP_NSE_FO_STOCKS = [
    'NIFTY', 'BANKNIFTY',  # Indices
    'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
    'KOTAKBANK', 'AXISBANK', 'SUNPHARMA', 'ASIANPAINT', 'MARUTI', 'WIPRO',
    'HCLTECH', 'TATAMOTORS', 'BAJAJFINSV', 'BAJFINANCE', 'INDUSINDBK',
    'TITAN', 'NESTLEIND', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA',
    'JSWSTEEL', 'TATASTEEL', 'HINDALCO', 'ULTRACEMCO', 'TECHM',
    'BIOCON', 'CIPLA', 'LUPIN', 'BHARTIARTL', 'BHARATFORG', 'BLUESTARCO',
    'BOSCHLTD', 'BRITANNIA', 'CANBK', 'COLPAL', 'CONCOR', 'DMART',
    'DABUR', 'EICHERMOT', 'FEDERALBNK', 'GAIL', 'GRASIM', 'HEXAWARE',
    'HEROMOTOCO', 'HDFC', 'ICICI', 'IDFCFIRSTB', 'MOTHERSON', 'MRF',
    'PAGEIND', 'PEL', 'SBICARD', 'SBILIFE', 'SIEMENS', 'TATACONSUM'
]

def fetch_stock_data(symbol, days=90):
    """Fetch stock data from Yahoo Finance"""
    try:
        ticker = f"{symbol}.NS" if not symbol.endswith('.NS') else symbol
        data = yf.download(ticker, period=f"{days}d", progress=False, threads=False)

        if data is None or len(data) < 20:
            return None

        # Calculate indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
        data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
        data['MACD'] = ta.trend.MACD(data['Close']).macd()
        data['MACD_signal'] = ta.trend.MACD(data['Close']).macd_signal()
        data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
        data['BB_lower'] = ta.volatility.BollingerBands(data['Close']).bollinger_lband()
        data['Volume_MA'] = data['Volume'].rolling(20).mean()

        return data
    except Exception as e:
        return None

def calculate_pcs_score(data):
    """Calculate PCS compatibility score (0-100)"""
    if data is None or len(data) < 20:
        return 0

    try:
        latest = data.iloc[-1]

        scores = []

        # 1. RSI Score (30% weight) - Ideal range 40-70
        rsi = latest['RSI']
        if pd.notna(rsi):
            if 40 <= rsi <= 70:
                rsi_score = 100
            elif 30 <= rsi <= 80:
                rsi_score = 80
            else:
                rsi_score = max(0, 100 - abs(rsi - 50) * 2)
            scores.append(rsi_score * 0.30)

        # 2. Trend Score (25% weight) - ADX > 20 + MACD positive
        adx = latest['ADX']
        macd = latest['MACD']
        macd_signal = latest['MACD_signal']

        trend_score = 0
        if pd.notna(adx) and adx > 20:
            trend_score += 50
        if pd.notna(macd) and pd.notna(macd_signal) and macd > macd_signal:
            trend_score += 50
        scores.append(trend_score * 0.25)

        # 3. Support Proximity (20% weight)
        price = latest['Close']
        sma20 = latest['SMA_20']
        bb_lower = latest['BB_lower']

        support_score = 0
        if pd.notna(sma20) and price > sma20 * 0.98:  # Within 2% of SMA
            support_score += 60
        if pd.notna(bb_lower) and price > bb_lower * 0.99:  # Within 1% of BB lower
            support_score += 40
        scores.append(support_score * 0.20)

        # 4. Volume Confirmation (15% weight)
        volume = latest['Volume']
        volume_ma = latest['Volume_MA']

        volume_score = 0
        if pd.notna(volume) and pd.notna(volume_ma) and volume > volume_ma:
            volume_pct = min(100, (volume / volume_ma) * 50)
            volume_score = volume_pct
        scores.append(volume_score * 0.15)

        # 5. Volatility Score (10% weight) - Optimal 15-35% IV
        returns = data['Close'].pct_change().dropna()
        if len(returns) > 0:
            volatility = returns.std() * np.sqrt(252) * 100  # Annualized
            if 15 <= volatility <= 35:
                vol_score = 100
            elif 10 <= volatility <= 50:
                vol_score = 80
            else:
                vol_score = max(0, 100 - abs(volatility - 25) * 2)
            scores.append(vol_score * 0.10)

        total_score = sum(scores)
        return min(100, max(0, total_score))

    except Exception as e:
        return 0

def send_to_telegram(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def main():
    print("=" * 70)
    print("🚀 NSE F&O PCS SCANNER - AUTOMATED BATCH RUN")
    print("=" * 70)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"📊 Analyzing {len(TOP_NSE_FO_STOCKS)} top liquid stocks")
    print()

    results = []

    def analyze_stock(symbol):
        """Analyze a single stock"""
        try:
            # Fetch data
            data = fetch_stock_data(symbol, days=90)
            if data is None:
                return None

            # Calculate score
            score = calculate_pcs_score(data)
            if score < 50:  # Skip low scores
                return None

            latest = data.iloc[-1]
            price = latest['Close']
            rsi = latest['RSI']
            adx = latest['ADX']

            return {
                'symbol': symbol,
                'price': round(price, 2),
                'score': round(score, 1),
                'rsi': round(rsi, 1),
                'adx': round(adx, 1),
                'confidence': 'HIGH' if score >= 75 else 'MEDIUM' if score >= 60 else 'LOW'
            }
        except Exception as e:
            return None

    # Parallel processing
    print("📈 Analyzing stocks (this may take 2-3 minutes)...")
    print()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analyze_stock, symbol): symbol for symbol in TOP_NSE_FO_STOCKS}

        completed = 0
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                result = future.result(timeout=30)
                if result:
                    results.append(result)
                    emoji = "🟢" if result['confidence'] == 'HIGH' else "🟡" if result['confidence'] == 'MEDIUM' else "🔴"
                    print(f"{emoji} {result['symbol']:12} | Score: {result['score']:5.1f}% | RSI: {result['rsi']:5.1f} | ADX: {result['adx']:5.1f}")
                completed += 1
                if completed % 10 == 0:
                    print(f"   ... Progress: {completed}/{len(TOP_NSE_FO_STOCKS)}")
            except Exception as e:
                completed += 1

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    print()
    print("=" * 70)
    print(f"✅ SCAN COMPLETE - Found {len(results)} qualifying stocks")
    print("=" * 70)
    print()

    if results:
        # Save to CSV
        df = pd.DataFrame(results)
        csv_file = f"/tmp/pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        print(f"💾 Results saved: {csv_file}")
        print()

        # Print results
        print("📊 TOP RESULTS BY PCS SCORE:")
        print()
        for i, r in enumerate(results[:15], 1):
            print(f"{i:2d}. {r['symbol']:12} │ {r['score']:6.1f}% │ RSI:{r['rsi']:5.1f} │ ADX:{r['adx']:5.1f} │ {r['confidence']}")

        if len(results) > 15:
            print(f"... and {len(results) - 15} more stocks")

        print()

        # Prepare Telegram message
        high_conf = [r for r in results if r['confidence'] == 'HIGH']
        med_conf = [r for r in results if r['confidence'] == 'MEDIUM']

        tg_message = f"<b>🎯 NSE F&O PCS SCAN RESULTS</b>\n"
        tg_message += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M IST')}</i>\n\n"

        if high_conf:
            tg_message += f"<b>🟢 HIGH Confidence ({len(high_conf)}):</b>\n"
            for r in high_conf[:5]:
                tg_message += f"  • {r['symbol']}: {r['score']:.1f}%\n"
            if len(high_conf) > 5:
                tg_message += f"  ... +{len(high_conf)-5} more\n"
            tg_message += "\n"

        if med_conf:
            tg_message += f"<b>🟡 MEDIUM Confidence ({len(med_conf)}):</b>\n"
            for r in med_conf[:5]:
                tg_message += f"  • {r['symbol']}: {r['score']:.1f}%\n"
            if len(med_conf) > 5:
                tg_message += f"  ... +{len(med_conf)-5} more\n"

        tg_message += f"\n<b>Total:</b> {len(results)} stocks\n"
        tg_message += f"<code>CSV: pcs_scan.csv</code>"

        # Send to Telegram
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            print("📱 Sending to Telegram...")
            if send_to_telegram(tg_message):
                print("✅ Message sent successfully!")
            else:
                print("❌ Failed to send Telegram message")
        else:
            print("⚠️  Telegram not configured")
            print("\nTo enable Telegram, set:")
            print("  export TELEGRAM_BOT_TOKEN=your_token")
            print("  export TELEGRAM_CHAT_ID=your_chat_id")

        print()
        print(f"🎉 Scan completed successfully!")
        return csv_file
    else:
        msg = "⚠️ No stocks met the PCS criteria in today's scan."
        print(msg)
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            send_to_telegram(msg)
        return None

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            send_to_telegram(f"❌ Scanner error: {str(e)[:200]}")
        sys.exit(1)
