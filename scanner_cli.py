#!/usr/bin/env python3
"""
Lightweight NSE F&O PCS Scanner CLI
Runs without Streamlit dependencies
"""

import os
import json
from datetime import datetime
import pytz
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
import requests

warnings.filterwarnings('ignore')

# NSE F&O Stock Universe - 219 stocks
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
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS',
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS',
    'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS',
    'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS',
    'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS',
    'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS',
    'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS',
    'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS',
    'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS',
    'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS',
    'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
    'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS',
    'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS',
    'RELIANCE.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS',
    'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS',
    'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS',
    'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS',
    'TATATECH.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS',
    'TITAN.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS',
    'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS',
    'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        if len(data) < 20:
            return None

        # Calculate basic technical indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()

        return data
    except:
        return None

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def check_volume_spike(data, min_ratio=1.2):
    """Check if today's volume is significantly higher than average"""
    if len(data) < 21:
        return False, 0

    current_volume = data['Volume'].iloc[-1]
    avg_20_volume = data['Volume'].iloc[:-1].tail(20).mean()

    volume_ratio = current_volume / avg_20_volume
    return volume_ratio >= min_ratio, volume_ratio

def detect_technical_patterns(data, symbol):
    """Detect simple technical patterns"""
    if len(data) < 20:
        return []

    patterns = []

    # Get latest values
    current_close = data['Close'].iloc[-1]
    current_high = data['High'].iloc[-1]
    current_rsi = data['RSI'].iloc[-1]
    current_sma20 = data['SMA_20'].iloc[-1]
    current_sma50 = data['SMA_50'].iloc[-1]

    lookback_data = data.iloc[:-1].tail(20)
    resistance = lookback_data['High'].max()
    support = lookback_data['Low'].min()

    # Pattern 1: Breakout
    if current_close > resistance * 1.005 and current_rsi < 75:
        strength = min(100, 60 + (current_rsi - 30) * 0.5)
        patterns.append({
            'type': 'Breakout',
            'strength': strength,
            'confidence': 'HIGH' if strength >= 75 else 'MEDIUM',
            'details': f'Above 20-day high ({resistance:.2f})'
        })

    # Pattern 2: Moving Average Crossover
    if current_sma20 and current_sma50:
        if current_sma20 > current_sma50 and current_close > current_sma20:
            strength = 70
            patterns.append({
                'type': 'MA Bullish',
                'strength': strength,
                'confidence': 'MEDIUM',
                'details': 'Close above both SMA20 and SMA50'
            })

    # Pattern 3: Support Test
    if support < current_close < support * 1.03 and current_rsi > 30:
        strength = 65
        patterns.append({
            'type': 'Support Test',
            'strength': strength,
            'confidence': 'MEDIUM',
            'details': f'Near support level ({support:.2f})'
        })

    return patterns

def run_scan():
    """Run the stock scanner"""
    print("\n" + "="*60)
    print("🎯 NSE F&O PCS Scanner - CLI Edition")
    print("="*60)

    ist = pytz.timezone('Asia/Kolkata')
    scan_time = datetime.now(ist)
    print(f"📊 Scan Time: {scan_time.strftime('%Y-%m-%d %H:%M:%S IST')}\n")

    results = []
    total_stocks = len(COMPLETE_NSE_FO_UNIVERSE)

    print(f"📈 Scanning {total_stocks} stocks...\n")

    for idx, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE):
        if (idx + 1) % 20 == 0:
            print(f"  Progress: {idx + 1}/{total_stocks} stocks processed")

        try:
            # Fetch data
            data = fetch_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio = check_volume_spike(data, min_ratio=1.2)
            if not volume_ok:
                continue

            # Detect patterns
            patterns = detect_technical_patterns(data, symbol)
            if not patterns:
                continue

            # Get latest metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]

            # Add to results
            clean_symbol = symbol.replace('.NS', '')
            results.append({
                'symbol': clean_symbol,
                'price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'patterns': patterns
            })

        except Exception as e:
            continue

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    print(f"\n{'='*60}")
    print(f"✅ Scan Complete! Found {len(results)} stocks")
    print(f"{'='*60}\n")

    return results

def send_to_telegram(stocks, token, chat_id):
    """Send results to Telegram"""
    if not token or not chat_id:
        print("⚠️  Telegram token or chat_id not provided")
        return False

    try:
        # Prepare message
        message = "🎯 *NSE F&O PCS Scanner Results*\n"
        message += f"⏰ {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M IST')}\n\n"

        if not stocks:
            message += "❌ No stocks found matching criteria today."
        else:
            message += f"✅ Found *{len(stocks)} stocks* with technical patterns!\n\n"

            # Add stocks with their patterns
            for idx, stock in enumerate(stocks[:15], 1):
                patterns_str = ", ".join([p['type'] for p in stock['patterns']])
                max_strength = max(p['strength'] for p in stock['patterns'])

                message += f"{idx}. *{stock['symbol']}*\n"
                message += f"   Price: ₹{stock['price']:.2f}\n"
                message += f"   Patterns: {patterns_str}\n"
                message += f"   Strength: {max_strength:.0f}%\n\n"

            if len(stocks) > 15:
                message += f"... and *{len(stocks) - 15} more stocks*"

        # Send to Telegram
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Results sent to Telegram!")
            return True
        else:
            print(f"❌ Failed to send to Telegram (Status: {response.status_code})")
            return False

    except Exception as e:
        print(f"❌ Error sending to Telegram: {str(e)}")
        return False

def save_results(stocks):
    """Save results to JSON file"""
    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')

    output_dir = '/tmp/claude-0/-home-user-nsepcs/ad59d2ce-88fa-57a6-ab8b-7cbaf51b3e1b/scratchpad'
    os.makedirs(output_dir, exist_ok=True)

    output_file = f"{output_dir}/scan_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(stocks, f, indent=2)

    print(f"💾 Results saved to: {output_file}\n")

    # Also print summary
    print("📊 SUMMARY:")
    print(f"   Total Stocks: {len(stocks)}")
    if stocks:
        avg_strength = np.mean([max(p['strength'] for p in s['patterns']) for s in stocks])
        print(f"   Avg Strength: {avg_strength:.1f}%")
        print(f"\n🏆 TOP STOCKS:")
        for stock in stocks[:5]:
            patterns = ", ".join([p['type'] for p in stock['patterns']])
            print(f"   • {stock['symbol']}: {patterns}")

    return output_file

def main():
    import sys

    # Get Telegram credentials from environment
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

    # Allow override via command line args
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv[1:]):
            if arg == '--token' and i + 2 < len(sys.argv):
                telegram_token = sys.argv[i + 2]
            elif arg == '--chat' and i + 2 < len(sys.argv):
                telegram_chat_id = sys.argv[i + 2]

    try:
        # Run the scan
        stocks = run_scan()

        # Save results
        save_results(stocks)

        # Send to Telegram if credentials available
        if telegram_token and telegram_chat_id:
            send_to_telegram(stocks, telegram_token, telegram_chat_id)
        else:
            print("ℹ️  To send results to Telegram, set:")
            print("   export TELEGRAM_BOT_TOKEN='your_token'")
            print("   export TELEGRAM_CHAT_ID='your_chat_id'")

        return 0

    except KeyboardInterrupt:
        print("\n⚠️  Scan interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    exit(main())
