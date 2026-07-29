#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Non-Streamlit Version
Runs the scanner and sends results to Telegram
"""

import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import requests

warnings.filterwarnings('ignore')

# Configuration
MIN_PCS_SCORE = 55
LIQUIDITY_TIER = 1
MAX_STOCKS = 50  # Limit to 50 for faster scanning
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

# Complete NSE F&O Universe from streamlit_app.py
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS',
    'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS',
    'BLUESTARCO.NS', 'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS',
    'CDSL.NS', 'CHOLAFIN.NS', 'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS',
    'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS', 'CROMPTON.NS', 'CUMMINSIND.NS',
    'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS', 'DIVISLAB.NS',
    'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS',
    'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS',
    'HDFCBANK.NS', 'HDFCLIFE.NS', 'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS',
    'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'HINDZINC.NS', 'POWERINDIA.NS',
    'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS', 'IDFCFIRSTB.NS',
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS',
    'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS',
    'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS',
    'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS',
    'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS',
    'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS',
]

def calculate_rsi(closes, period=14):
    """Calculate RSI manually"""
    deltas = np.diff(closes)
    gains = deltas.copy()
    losses = deltas.copy()
    gains[gains < 0] = 0
    losses[losses > 0] = 0

    gains = pd.Series(gains)
    losses = pd.Series(losses)

    avg_gain = gains.rolling(window=period).mean()
    avg_loss = losses.rolling(window=period).mean().abs()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def calculate_macd(closes, fast=12, slow=26, signal=9):
    """Calculate MACD manually"""
    ema_fast = pd.Series(closes).ewm(span=fast).mean()
    ema_slow = pd.Series(closes).ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    macd_hist = macd - macd_signal
    return macd.iloc[-1], macd_signal.iloc[-1], macd_hist.iloc[-1]

def calculate_moving_averages(closes):
    """Calculate SMA"""
    sma_20 = pd.Series(closes).rolling(window=20).mean().iloc[-1]
    sma_50 = pd.Series(closes).rolling(window=50).mean().iloc[-1]
    return sma_20, sma_50

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        if len(data) < 50:
            return None
        return data
    except Exception:
        return None

def calculate_pcs_score(data, symbol):
    """Calculate PCS score based on technical indicators"""
    try:
        if data is None or len(data) < 50:
            return None

        closes = data['Close'].values
        highs = data['High'].values
        lows = data['Low'].values
        volumes = data['Volume'].values

        # Get current values
        current_price = closes[-1]

        # RSI
        rsi = calculate_rsi(closes, period=14)

        # MACD
        macd, macd_signal, macd_hist = calculate_macd(closes)

        # SMA
        sma_20, sma_50 = calculate_moving_averages(closes)

        # Support level (SMA_20)
        support_level = sma_20
        distance_from_support = ((current_price - support_level) / support_level) * 100 if support_level > 0 else 0

        # Calculate volatility
        returns = pd.Series(closes).pct_change().dropna()
        recent_returns = returns.tail(20).std() * np.sqrt(252) * 100

        # Check volume
        recent_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1

        # Score components (0-100)
        # 1. Bullish Momentum (30%) - RSI 45-65 is sweet spot
        if pd.notna(rsi):
            if 45 <= rsi <= 65:
                momentum_score = 100
            elif rsi < 45:
                momentum_score = (rsi / 45) * 100
            else:
                momentum_score = ((100 - rsi) / 35) * 100
            momentum_score = max(0, min(100, momentum_score))
        else:
            momentum_score = 50

        # 2. Trend Strength (25%) - MACD histogram
        if pd.notna(macd_hist):
            if macd_hist > 0:
                trend_score = min(100, abs(macd_hist) * 200 + 50)
            else:
                trend_score = max(0, 50 - abs(macd_hist) * 200)
        else:
            trend_score = 50

        # 3. Support Proximity (20%) - Closer to support is better
        if distance_from_support >= 0 and distance_from_support <= 5:
            support_score = 100
        elif distance_from_support < 0:
            support_score = 50
        else:
            support_score = max(0, 100 - (distance_from_support - 5) * 5)

        # 4. Volatility (15%) - Optimal is 15-35%
        if 15 <= recent_returns <= 35:
            volatility_score = 100
        elif recent_returns < 15:
            volatility_score = (recent_returns / 15) * 100
        else:
            volatility_score = max(0, 100 - ((recent_returns - 35) / 30) * 100)
        volatility_score = max(0, min(100, volatility_score))

        # 5. Volume Confirmation (10%)
        volume_score = min(100, volume_ratio * 100)

        # Composite Score
        pcs_score = (
            momentum_score * 0.30 +
            trend_score * 0.25 +
            support_score * 0.20 +
            volatility_score * 0.15 +
            volume_score * 0.10
        )

        return max(0, min(100, pcs_score)), rsi, current_price

    except Exception as e:
        return None, None, None

def run_scanner(stocks_list, min_score=55, max_stocks=None):
    """Run the scanner on a list of stocks"""
    results = []

    if max_stocks:
        stocks_list = stocks_list[:max_stocks]

    print(f"\n🔍 Scanning {len(stocks_list)} stocks for PCS opportunities...")
    print("=" * 60)

    for i, symbol in enumerate(stocks_list):
        print(f"[{i+1}/{len(stocks_list)}] {symbol}...", end=" ", flush=True)

        try:
            # Fetch data
            data = fetch_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                continue

            # Calculate PCS score
            pcs_score, rsi, current_price = calculate_pcs_score(data, symbol)
            if pcs_score is None:
                print("❌ Score calculation failed")
                continue

            # Filter by minimum score
            if pcs_score < min_score:
                print(f"❌ Score: {pcs_score:.1f} < {min_score}")
                continue

            # Passed filter
            # Determine confidence level
            if pcs_score >= 75:
                confidence = "HIGH"
            elif pcs_score >= 60:
                confidence = "MEDIUM"
            else:
                confidence = "LOW"

            result = {
                'symbol': symbol.replace('.NS', ''),
                'pcs_score': pcs_score,
                'confidence': confidence,
                'current_price': current_price,
                'rsi': rsi,
            }

            results.append(result)
            print(f"✅ Score: {pcs_score:.1f} ({confidence})")

        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            continue

    # Sort by score
    results.sort(key=lambda x: x['pcs_score'], reverse=True)

    return results

def format_results(results):
    """Format results for display and Telegram"""
    if not results:
        return "❌ No stocks met the filter criteria."

    output = f"\n📊 NSE F&O PCS SCANNER RESULTS\n"
    output += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"Filter: Min PCS Score >= {MIN_PCS_SCORE}\n"
    output += f"Stocks Found: {len(results)}\n"
    output += "=" * 70 + "\n\n"

    # Group by confidence
    high = [r for r in results if r['confidence'] == 'HIGH']
    medium = [r for r in results if r['confidence'] == 'MEDIUM']
    low = [r for r in results if r['confidence'] == 'LOW']

    if high:
        output += "🟢 HIGH CONFIDENCE (Score >= 75):\n"
        output += "-" * 70 + "\n"
        for r in high:
            output += f"{r['symbol']:12} | Score: {r['pcs_score']:5.1f} | "
            output += f"Price: ₹{r['current_price']:.2f} | RSI: {r['rsi']:.1f}\n"
        output += "\n"

    if medium:
        output += "🟡 MEDIUM CONFIDENCE (Score 60-74):\n"
        output += "-" * 70 + "\n"
        for r in medium:
            output += f"{r['symbol']:12} | Score: {r['pcs_score']:5.1f} | "
            output += f"Price: ₹{r['current_price']:.2f} | RSI: {r['rsi']:.1f}\n"
        output += "\n"

    if low:
        output += "🔴 LOW CONFIDENCE (Score < 60):\n"
        output += "-" * 70 + "\n"
        for r in low:
            output += f"{r['symbol']:12} | Score: {r['pcs_score']:5.1f} | "
            output += f"Price: ₹{r['current_price']:.2f} | RSI: {r['rsi']:.1f}\n"
        output += "\n"

    return output

def send_to_telegram(message):
    """Send message to Telegram if credentials are available"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  Telegram credentials not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

        # Split message if too long (Telegram limit is 4096 chars)
        max_length = 4096
        if len(message) > max_length:
            messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        else:
            messages = [message]

        for msg in messages:
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': msg,
                'parse_mode': 'HTML'
            }

            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                print(f"❌ Telegram error: {response.status_code} - {response.text}")
                return False

        print("✅ Results sent to Telegram successfully!")
        return True

    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("NSE F&O PCS SCANNER - Telegram Edition")
    print("=" * 70)
    print(f"Config: Min Score={MIN_PCS_SCORE}, Max Stocks={MAX_STOCKS}")
    print(f"Telegram: {'Configured' if TELEGRAM_BOT_TOKEN else 'Not configured'}")

    # Run scanner
    results = run_scanner(COMPLETE_NSE_FO_UNIVERSE, MIN_PCS_SCORE, MAX_STOCKS)

    # Format results
    formatted_output = format_results(results)
    print(formatted_output)

    # Save to file
    output_file = f"/tmp/pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w') as f:
        f.write(formatted_output)
    print(f"\n📁 Results saved to: {output_file}")

    # Send to Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        send_to_telegram(formatted_output)
    else:
        print("\n⚠️  Telegram not configured. Results saved locally only.")

    print("\n" + "=" * 70)
    print(f"Scan completed. Found {len(results)} qualifying stocks.")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    main()
