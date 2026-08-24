#!/usr/bin/env python3
"""
Standalone script to run NSE F&O stock analysis and extract qualifying stocks.
This extracts the core analysis logic from streamlit_app.py and runs it with predefined filters.
"""

import sys
import os
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

warnings.filterwarnings('ignore')

# Basic technical indicator functions
def calculate_rsi(prices, period=14):
    """Calculate RSI without ta library"""
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

    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX without ta library"""
    tr = np.maximum(high - low, np.maximum(abs(high - pd.Series(close).shift(1)), abs(low - pd.Series(close).shift(1))))
    atr = pd.Series(tr).rolling(period).mean()

    up = high - high.shift(1)
    down = low.shift(1) - low

    pos_dm = np.where(up > down, up, 0)
    neg_dm = np.where(down > up, down, 0)

    pos_di = 100 * pd.Series(pos_dm).rolling(period).mean() / atr
    neg_di = 100 * pd.Series(neg_dm).rolling(period).mean() / atr

    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = pd.Series(dx).rolling(period).mean()

    return adx.values

def calculate_sma(prices, period=20):
    """Calculate SMA"""
    return pd.Series(prices).rolling(period).mean().values

# Import scanner from streamlit app
sys.path.insert(0, '/home/user/nsepcs')

# Define F&O stocks list
COMPLETE_NSE_FO_UNIVERSE = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS', 'ADANIENT.NS',
    'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS', 'AMBER.NS', 'AMBUJACEM.NS',
    'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS', 'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS',
    'DMART.NS', 'AXISBANK.NS', 'BSE.NS', 'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS',
    'BAJAJHLDNG.NS', 'BANDHANBNK.NS', 'BANKBARODA.NS', 'BANKINDIA.NS', 'BDL.NS', 'BEL.NS',
    'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS', 'BHARTIARTL.NS', 'BIOCON.NS', 'BLUESTARCO.NS',
    'BOSCHLTD.NS', 'BRITANNIA.NS', 'CGPOWER.NS', 'CANBK.NS', 'CDSL.NS', 'CHOLAFIN.NS',
    'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS', 'CONCOR.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DALBHARAT.NS', 'DELHIVERY.NS',
    'DIVISLAB.NS', 'DIXON.NS', 'DRREDDY.NS', 'ETERNAL.NS', 'EICHERMOT.NS', 'EXIDEIND.NS',
    'NYKAA.NS', 'FORTIS.NS', 'GAIL.NS', 'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODREJCP.NS',
    'GODREJPROP.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HAVELLS.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'HAL.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS',
    'HINDZINC.NS', 'POWERINDIA.NS', 'HUDCO.NS', 'ICICIBANK.NS', 'ICICIGI.NS', 'ICICIPRULI.NS',
    'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS',
    'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS',
    'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS',
    'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS',
    'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS',
    'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS',
    'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS',
    'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
    'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS',
    'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS',
    'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS',
    'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS',
    'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS',
    'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS',
    'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS',
    'WAAREEENER.NS', 'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# Default filter criteria
DEFAULT_FILTERS = {
    'rsi_min': 30,
    'rsi_max': 70,
    'adx_min': 20,
    'pattern_strength_min': 70,
    'volume_breakout_ratio': 1.5,
    'lookback_days': 20,
    'ma_support': True,
    'ma_type': 'SMA',
    'ma_tolerance': 5,
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
}

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        if len(data) >= 20:
            return data
    except:
        pass
    return None

def get_stock_metrics(data):
    """Calculate technical indicators for a stock"""
    try:
        if len(data) < 20:
            return None

        data = data.copy()
        data['RSI'] = calculate_rsi(data['Close'].values, period=14)
        data['SMA_20'] = calculate_sma(data['Close'].values, period=20)
        data['ADX'] = calculate_adx(data['High'].values, data['Low'].values, data['Close'].values, period=14)
        data['Volume_Ratio'] = data['Volume'] / data['Volume'].tail(21).iloc[:-1].mean()

        return data
    except Exception as e:
        return None

def check_filter_criteria(data, filters):
    """Check if stock meets the filter criteria"""
    try:
        if data is None or len(data) < 2:
            return False

        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        current_volume_ratio = data['Volume_Ratio'].iloc[-1]

        # RSI check
        if not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
            return False

        # ADX check
        if current_adx < filters['adx_min']:
            return False

        # Volume check
        if current_volume_ratio < filters['volume_breakout_ratio']:
            return False

        # SMA support check
        if filters['ma_support']:
            sma_20 = data['SMA_20'].iloc[-1]
            current_price = data['Close'].iloc[-1]
            if current_price < sma_20 * (1 - filters['ma_tolerance']/100):
                return False

        return True
    except:
        return False

def analyze_stocks(stock_list, filters, max_workers=5):
    """Analyze a list of stocks and return those meeting criteria"""
    qualifying_stocks = []
    failed_stocks = []

    print(f"\n🔍 Analyzing {len(stock_list)} stocks with criteria:")
    print(f"   RSI Range: {filters['rsi_min']}-{filters['rsi_max']}")
    print(f"   ADX Minimum: {filters['adx_min']}")
    print(f"   Volume Ratio: {filters['volume_breakout_ratio']}x")
    print(f"   Pattern Strength: {filters['pattern_strength_min']}%\n")

    def analyze_single_stock(symbol):
        try:
            data = fetch_stock_data(symbol)
            if data is None:
                return None

            data = get_stock_metrics(data)
            if data is None:
                return None

            if check_filter_criteria(data, filters):
                current_data = data.iloc[-1]
                return {
                    'symbol': symbol.replace('.NS', ''),
                    'price': current_data['Close'],
                    'rsi': current_data['RSI'],
                    'adx': current_data['ADX'],
                    'volume_ratio': current_data['Volume_Ratio'],
                    'date': current_data.name.strftime('%Y-%m-%d')
                }
        except Exception as e:
            failed_stocks.append(symbol)

        return None

    # Run analysis in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(analyze_single_stock, symbol): symbol for symbol in stock_list}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            result = future.result()
            if result:
                qualifying_stocks.append(result)

            # Print progress
            if completed % 10 == 0:
                print(f"   Progress: {completed}/{len(stock_list)} stocks analyzed... Found {len(qualifying_stocks)} so far")

    return qualifying_stocks, failed_stocks

def format_results(qualifying_stocks):
    """Format results for display and export"""
    if not qualifying_stocks:
        return "No stocks meeting the filter criteria found."

    # Sort by RSI (closer to middle is better for PCS)
    qualifying_stocks_sorted = sorted(qualifying_stocks, key=lambda x: abs(x['rsi'] - 50))

    output = f"\n✅ STOCKS MEETING FILTER CRITERIA ({len(qualifying_stocks)} found)\n"
    output += f"{'='*70}\n"
    output += f"{'Symbol':<12} {'Price':<12} {'RSI':<8} {'ADX':<8} {'Volume':<12} {'Date':<12}\n"
    output += f"{'-'*70}\n"

    for stock in qualifying_stocks_sorted:
        output += f"{stock['symbol']:<12} ₹{stock['price']:<11.2f} {stock['rsi']:<7.1f} {stock['adx']:<7.1f} {stock['volume_ratio']:<11.1f}x {stock['date']:<12}\n"

    output += f"{'='*70}\n"
    return output, qualifying_stocks_sorted

def save_results(qualifying_stocks, filename="/tmp/stock_analysis_results.json"):
    """Save results to JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(qualifying_stocks, f, indent=2, default=str)
        return filename
    except Exception as e:
        print(f"Error saving results: {e}")
        return None

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    import urllib.request
    import urllib.parse

    bot_token = bot_token or os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("\n⚠️  Telegram not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables.")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = response.read().decode('utf-8')
            if 'ok' in result and 'true' in result:
                print("✅ Message sent to Telegram successfully!")
                return True
            else:
                print("⚠️  Telegram API error:", result[:100])
                return False
    except Exception as e:
        print(f"⚠️  Failed to send Telegram message: {e}")
        return False

def format_telegram_message(qualifying_stocks):
    """Format results for Telegram (HTML format)"""
    if not qualifying_stocks:
        return "<b>⚠️ No stocks meeting the filter criteria</b>"

    message = "<b>✅ NSE F&O STOCKS - FILTER RESULTS</b>\n"
    message += f"<b>Found:</b> {len(qualifying_stocks)} stocks\n"
    message += f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    message += "<b>Criteria:</b> RSI(30-70) | ADX(20+) | Vol(1.5x+) | SMA Support\n\n"

    message += "<code>"
    message += f"{'Symbol':<12} {'Price':<12} {'RSI':<7} {'ADX':<7} {'Vol':<6}\n"
    message += "-" * 50 + "\n"

    for stock in qualifying_stocks[:10]:  # Limit to top 10 for Telegram
        message += f"{stock['symbol']:<12} ₹{stock['price']:<11.0f} {stock['rsi']:<6.1f} {stock['adx']:<6.1f} {stock['volume_ratio']:<5.1f}x\n"

    message += "</code>"

    if len(qualifying_stocks) > 10:
        message += f"\n<i>... and {len(qualifying_stocks) - 10} more stocks</i>"

    return message

def main():
    print("\n" + "="*70)
    print("NSE F&O STOCK ANALYSIS - AUTOMATED RUN")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Analyzing {len(COMPLETE_NSE_FO_UNIVERSE)} F&O stocks...")

    # Run analysis
    qualifying_stocks, failed_stocks = analyze_stocks(
        COMPLETE_NSE_FO_UNIVERSE,
        DEFAULT_FILTERS,
        max_workers=8
    )

    # Format and display results
    output, sorted_stocks = format_results(qualifying_stocks)
    print(output)

    if failed_stocks:
        print(f"\n⚠️  Failed to analyze: {len(failed_stocks)} stocks")
        print(f"   (Network issues or insufficient data)")

    # Save results
    result_file = save_results(sorted_stocks)
    if result_file:
        print(f"\n💾 Results saved to: {result_file}")

    # Send to Telegram if configured
    telegram_message = format_telegram_message(sorted_stocks)
    send_to_telegram(telegram_message)

    # Return results for further processing
    return sorted_stocks, output

if __name__ == "__main__":
    qualifying_stocks, output = main()

    print("\n" + "="*70)
    print(f"Analysis complete at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70 + "\n")
