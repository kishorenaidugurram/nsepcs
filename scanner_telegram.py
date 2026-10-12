#!/usr/bin/env python3
"""
Final NSE PCS Scanner - Telegram notification script
Installs dependencies and runs analysis
"""

import subprocess
import sys
import os

# Install essential dependencies
print("Installing dependencies...")
essential_packages = [
    'yfinance>=0.2.18',
    'pandas>=2.0.0',
    'numpy>=1.24.0',
    'plotly>=5.17.0',
    'pytz>=2023.3',
    'beautifulsoup4>=4.12.0',
    'openpyxl>=3.1.0',
    'scikit-learn>=1.3.0',
    'scipy>=1.11.0',
    'requests>=2.28.0'
]

for package in essential_packages:
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', package],
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

print("✓ Dependencies installed")

# Now run the actual analysis
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import requests

# NSE F&O stocks - main liquid ones
NSE_FO_STOCKS = [
    'NIFTY.NS', 'BANKNIFTY.NS',
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'SBIN.NS', 'LT.NS', 'ITC.NS', 'KOTAKBANK.NS', 'AXISBANK.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS',
    'SUNPHARMA.NS', 'TATAMOTORS.NS', 'ADANIENT.NS', 'BAJFINANCE.NS',
    'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS',
    'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS',
    'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period if period > 0 else 0
    down = -seed[seed < 0].sum() / period if period > 0 else 0

    if up == 0 and down == 0:
        return 50

    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs) if down != 0 else 50

    return rsi

def analyze_stock(symbol):
    """Analyze a stock using yfinance"""
    try:
        import yfinance as yf

        stock = yf.Ticker(symbol)
        hist = stock.history(period="3mo")

        if len(hist) < 20:
            return None

        # Current values
        current_price = hist['Close'].iloc[-1]
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].iloc[-20:].mean()

        # Check volume
        if avg_volume == 0:
            return None

        volume_ratio = current_volume / avg_volume
        if volume_ratio < 1.2:
            return None

        # Calculate RSI
        rsi = calculate_rsi(hist['Close'].values, period=14)
        if rsi is None or not (30 <= rsi <= 75):
            return None

        # Support/Resistance
        high_20 = hist['High'].iloc[-20:].max()
        low_20 = hist['Low'].iloc[-20:].min()

        if (high_20 - low_20) == 0:
            return None

        proximity = (current_price - low_20) / (high_20 - low_20)

        # Strong bullish signal if close to support and good RSI
        if proximity < 0.4:  # In lower 40% of 20-day range
            strength = 60 + (1 - proximity) * 30
            return {
                'symbol': symbol.replace('.NS', ''),
                'price': round(current_price, 2),
                'rsi': round(rsi, 1),
                'volume_ratio': round(volume_ratio, 2),
                'proximity_score': round(proximity, 2),
                'support': round(low_20, 2),
                'resistance': round(high_20, 2),
                'pattern': 'Bullish Support Zone',
                'strength': round(strength, 0)
            }

        return None

    except Exception as e:
        return None

print(f"\n{'='*60}")
print("NSE PCS Scanner - Automated Analysis")
print(f"{'='*60}\n")
print(f"Analyzing {len(NSE_FO_STOCKS)} stocks...\n")

results = []
for i, symbol in enumerate(NSE_FO_STOCKS, 1):
    clean_symbol = symbol.replace('.NS', '')
    print(f"[{i}/{len(NSE_FO_STOCKS)}] {clean_symbol:<15}", end='\r')

    result = analyze_stock(symbol)
    if result:
        results.append(result)

print(" " * 60, end='\r')

# Format for Telegram
if results:
    results.sort(key=lambda x: x['strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""🚀 NSE PCS Scanner Results
{timestamp}

📊 Found {len(results)} stocks with bullish patterns

"""

    for i, stock in enumerate(results[:12], 1):
        message += f"""{i}. {stock['symbol']}
   Price: ₹{stock['price']} | RSI: {stock['rsi']}
   Pattern: {stock['pattern']} ({int(stock['strength'])}/100)
   Support: ₹{stock['support']} | Resistance: ₹{stock['resistance']}

"""

    message += "\n💡 For detailed PCS strike selection analysis\n"

    print(message)
    print("=" * 60)

    # Save to CSV
    csv_file = "/tmp/claude-0/-home-user-nsepcs/4d86c3dd-ae17-50f8-bd07-38b1052ae491/scratchpad/pcs_results.csv"
    df = pd.DataFrame(results)
    df = df[['symbol', 'price', 'rsi', 'volume_ratio', 'strength', 'pattern']]
    df.to_csv(csv_file, index=False)
    print(f"\n✓ Results saved to: {csv_file}")

    # Try to send to Telegram
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    print("\nTelegram Status:")
    if token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}

            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                print("✓ Message sent to Telegram successfully")
            else:
                print(f"✗ Failed to send (HTTP {response.status_code})")
        except Exception as e:
            print(f"✗ Connection error: {str(e)[:50]}")
    else:
        print("⚠ Telegram not configured")
        print("  Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable notifications")

else:
    print("\n⚠ No stocks found meeting the filter criteria")
    print("  - Check market conditions")
    print("  - Verify data source availability")
