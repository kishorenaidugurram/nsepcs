#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Results Export
Runs the scanner with default filter criteria and sends results to Telegram
"""

import sys
import os
import json
import requests
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
except ImportError:
    print("Installing required packages...")
    os.system("pip install yfinance pandas numpy -q")
    import yfinance as yf
    import pandas as pd
    import numpy as np

warnings.filterwarnings('ignore')

# Telegram Configuration - Set via environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Default filter criteria (based on Streamlit app defaults)
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 75,
    'adx_min': 20,
    'ma_support': True,
    'ma_type': 'EMA',
    'ma_tolerance': 3,
    'min_volume_ratio': 1.2,
    'volume_breakout_ratio': 2.0,
    'lookback_days': 20,
    'pattern_strength_min': 65,
}

# NSE F&O Universe (219 stocks)
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
    'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS',
    'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS',
    'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS',
    'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS',
    'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'PPLPHARMA.NS',
    'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS',
    'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS',
    'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS',
    'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS',
    'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS',
    'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS',
    'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS',
    'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS',
    'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS', 'WIPRO.NS',
    'YESBANK.NS', 'ZYDUSLIFE.NS'
]

def calculate_rsi(prices, period=14):
    """Calculate RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data and calculate indicators"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate technical indicators using pandas/numpy
        data['RSI'] = calculate_rsi(data['Close'], period=14)
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['EMA_20'] = data['Close'].ewm(span=20, adjust=False).mean()

        return data
    except Exception as e:
        return None

def check_stock_filters(symbol, data, filters):
    """Check if stock meets filter criteria"""
    if data is None or len(data) < 21:
        return False, {}

    try:
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        sma_20 = data['SMA_20'].iloc[-1]
        ema_20 = data['EMA_20'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]

        # Check RSI
        if pd.isna(current_rsi) or not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
            return False, {}

        # Check MA Support
        if filters['ma_support']:
            ma_level = ema_20 if filters['ma_type'] == 'EMA' else sma_20
            if pd.isna(ma_level) or current_price < ma_level * (1 - filters['ma_tolerance']/100):
                return False, {}

        # Check Volume
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_20_volume if avg_20_volume > 0 else 0

        if volume_ratio < filters['min_volume_ratio']:
            return False, {}

        return True, {
            'symbol': symbol,
            'price': round(current_price, 2),
            'rsi': round(current_rsi, 1) if not pd.isna(current_rsi) else 0,
            'volume_ratio': round(volume_ratio, 2),
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')
        }
    except Exception as e:
        return False, {}

def scan_stocks(stocks_list, filters, max_workers=5):
    """Scan stocks in parallel"""
    qualifying_stocks = []
    completed = 0
    total = len(stocks_list)

    print(f"\n📊 Scanning {total} stocks...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_stock_data, symbol): symbol for symbol in stocks_list}

        for future in as_completed(futures):
            symbol = futures[future]
            completed += 1

            if completed % 20 == 0:
                print(f"  Progress: {completed}/{total}", file=sys.stderr)

            try:
                data = future.result()
                passed, result = check_stock_filters(symbol, data, filters)

                if passed:
                    qualifying_stocks.append(result)
                    print(f"  ✓ {symbol} qualified", file=sys.stderr)
            except:
                pass

    return qualifying_stocks

def send_to_telegram(qualifying_stocks):
    """Send results to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️  Telegram not configured - saving results locally", file=sys.stderr)
        return False

    try:
        message = "📊 **NSE F&O PCS Scanner Results**\n"
        message += f"⏰ {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"
        message += f"✅ Qualifying Stocks: {len(qualifying_stocks)}\n\n"

        if qualifying_stocks:
            message += "**Stocks Meeting Filter Criteria:**\n"
            for stock in qualifying_stocks[:15]:
                message += f"\n• {stock['symbol']}\n"
                message += f"  Price: ₹{stock['price']}\n"
                message += f"  RSI: {stock['rsi']}\n"
                message += f"  Vol Ratio: {stock['volume_ratio']}x"

            if len(qualifying_stocks) > 15:
                message += f"\n\n... and {len(qualifying_stocks) - 15} more"

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print(f"✅ Sent to Telegram", file=sys.stderr)
            return True
        else:
            print(f"❌ Telegram error: {response.text}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}", file=sys.stderr)
        return False

def main():
    """Main execution"""
    print("\n" + "="*60, file=sys.stderr)
    print("NSE F&O PCS Scanner", file=sys.stderr)
    print("="*60, file=sys.stderr)

    # Scan stocks
    qualifying_stocks = scan_stocks(COMPLETE_NSE_FO_UNIVERSE, DEFAULT_FILTERS, max_workers=10)

    print(f"\n📈 Results:", file=sys.stderr)
    print(f"   Total stocks scanned: {len(COMPLETE_NSE_FO_UNIVERSE)}", file=sys.stderr)
    print(f"   Qualifying stocks: {len(qualifying_stocks)}", file=sys.stderr)

    if qualifying_stocks:
        print(f"\n✅ Qualifying Stocks:", file=sys.stderr)
        for stock in qualifying_stocks:
            print(f"   • {stock['symbol']} @ ₹{stock['price']} (RSI: {stock['rsi']}, Vol: {stock['volume_ratio']}x)", file=sys.stderr)

    # Send to Telegram
    send_to_telegram(qualifying_stocks)

    # Output results as JSON
    print(json.dumps(qualifying_stocks, indent=2))

if __name__ == "__main__":
    main()
