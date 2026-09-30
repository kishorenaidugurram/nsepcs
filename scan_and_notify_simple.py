#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Simplified version with Telegram notification
Runs the stock scanner without external technical analysis libraries
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Try to import technical analysis library
try:
    import ta
    HAS_TA = True
except ImportError:
    HAS_TA = False
    logger.warning("ta library not available, using simplified indicators")

# Try to import yfinance
try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False
    logger.error("yfinance required but not installed")
    sys.exit(1)

# F&O Universe
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

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


# ============= SIMPLIFIED TECHNICAL INDICATORS =============
def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - 100.0 / (1.0 + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else 0
        rsi[i] = 100.0 - 100.0 / (1.0 + rs)

    return rsi


def calculate_adx(high, low, close, period=14):
    """Calculate ADX indicator (simplified)"""
    plus_dm = np.zeros(len(high))
    minus_dm = np.zeros(len(high))

    for i in range(1, len(high)):
        up_move = high[i] - high[i-1]
        down_move = low[i-1] - low[i]

        if up_move > down_move and up_move > 0:
            plus_dm[i] = up_move
        else:
            plus_dm[i] = 0

        if down_move > up_move and down_move > 0:
            minus_dm[i] = down_move
        else:
            minus_dm[i] = 0

    tr = np.zeros(len(high))
    for i in range(1, len(high)):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))

    atr = np.convolve(tr, np.ones(period)/period, mode='valid')
    atr = np.concatenate([np.full(period-1, np.nan), atr])

    plus_di = 100 * np.convolve(plus_dm, np.ones(period)/period, mode='valid')
    plus_di = np.concatenate([np.full(period-1, np.nan), plus_di]) / atr

    minus_di = 100 * np.convolve(minus_dm, np.ones(period)/period, mode='valid')
    minus_di = np.concatenate([np.full(period-1, np.nan), minus_di]) / atr

    di_diff = np.abs(plus_di - minus_di)
    di_sum = plus_di + minus_di
    di_sum[di_sum == 0] = 1
    dx = 100 * di_diff / di_sum

    adx = np.convolve(dx[~np.isnan(dx)], np.ones(period)/period, mode='valid')
    adx_full = np.full(len(high), np.nan)
    adx_full[period*2:period*2+len(adx)] = adx

    # Fill forward
    for i in range(len(adx_full)):
        if not np.isnan(adx_full[i]):
            last_val = adx_full[i]
        elif i > 0:
            adx_full[i] = last_val

    return np.nan_to_num(adx_full, nan=20.0)  # Default to 20 if NaN


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    return np.convolve(prices, np.ones(period)/period, mode='valid')


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from yfinance"""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Add technical indicators
        close = data['Close'].values
        high = data['High'].values
        low = data['Low'].values

        if HAS_TA:
            try:
                data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
                data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
                data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
            except:
                # Fallback to simplified
                data['RSI'] = calculate_rsi(close)
                sma = calculate_sma(close, 20)
                data['SMA_20'] = np.concatenate([np.full(len(close)-len(sma), np.nan), sma])
                data['ADX'] = calculate_adx(high, low, close)
        else:
            # Use simplified indicators
            data['RSI'] = calculate_rsi(close)
            sma = calculate_sma(close, 20)
            data['SMA_20'] = np.concatenate([np.full(len(close)-len(sma), np.nan), sma])
            data['ADX'] = calculate_adx(high, low, close)

        return data
    except Exception as e:
        logger.debug(f"Error fetching {symbol}: {str(e)}")
        return None


def send_telegram_message(message, parse_mode="HTML"):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }
        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            logger.info("Telegram notification sent")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Telegram error: {str(e)}")
        return False


def analyze_stock(symbol):
    """Analyze a single stock"""
    try:
        data = fetch_stock_data(symbol, period="3mo")
        if data is None or len(data) < 20:
            return None

        # Get current values
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1] if not np.isnan(data['RSI'].iloc[-1]) else 50
        current_adx = data['ADX'].iloc[-1] if not np.isnan(data['ADX'].iloc[-1]) else 20
        current_volume = data['Volume'].iloc[-1]

        # Check volume ratio
        avg_volume = data['Volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume

        # Filter criteria
        rsi_ok = 30 <= current_rsi <= 75
        adx_ok = current_adx > 20
        volume_ok = volume_ratio > 1.2

        if not (rsi_ok and adx_ok and volume_ok):
            return None

        # Check for breakout
        resistance = data['High'].tail(20).max()
        support = data['Low'].tail(20).min()
        breakout_detected = current_price > resistance * 1.005

        if not breakout_detected:
            return None

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': current_rsi,
            'adx': current_adx,
            'volume_ratio': volume_ratio,
            'resistance': resistance,
            'support': support,
            'breakout_pct': ((current_price - resistance) / resistance) * 100 if resistance > 0 else 0
        }

    except Exception as e:
        logger.debug(f"Error analyzing {symbol}: {str(e)}")
        return None


def format_results(results, max_items=15):
    """Format results for Telegram"""
    if not results:
        return "❌ <b>No stocks found matching criteria</b>"

    # Sort by volume ratio (highest first)
    sorted_results = sorted(results, key=lambda x: x['volume_ratio'], reverse=True)[:max_items]

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = (
        f"✅ <b>NSE F&O Scan Results</b>\n"
        f"📅 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for idx, result in enumerate(sorted_results, 1):
        symbol = result['symbol'].replace('.NS', '')
        message += (
            f"<b>{idx}. {symbol}</b>\n"
            f"   💰 ₹{result['price']:.2f}\n"
            f"   📈 RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
            f"   📊 Vol: {result['volume_ratio']:.1f}x | Breakout: {result['breakout_pct']:+.1f}%\n\n"
        )

    if len(results) > max_items:
        message += f"... and {len(results) - max_items} more\n\n"

    message += (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Filters: RSI(30-75), ADX>20, Vol>1.2x\n"
        f"Found: {len(results)} stocks"
    )

    return message


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Starting")
    logger.info("=" * 60)

    ist = pytz.timezone('Asia/Kolkata')
    start_time = datetime.now(ist)

    # Send start notification
    send_telegram_message(
        f"🚀 <b>Scan Started</b>\n"
        f"⏰ {start_time.strftime('%H:%M IST')}\n"
        f"📊 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} stocks"
    )

    results = []

    # Scan stocks with threading
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analyze_stock, sym): sym for sym in COMPLETE_NSE_FO_UNIVERSE}

        for idx, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            if idx % 20 == 0:
                logger.info(f"Processed {idx}/{len(COMPLETE_NSE_FO_UNIVERSE)}")

            try:
                result = future.result()
                if result:
                    results.append(result)
                    logger.info(f"✓ {symbol.replace('.NS', '')}")
            except Exception as e:
                logger.debug(f"Error processing {symbol}: {str(e)}")

    logger.info(f"Scan complete. Found {len(results)} stocks")

    # Format and send results
    message = format_results(results, max_items=15)
    send_telegram_message(message)

    # Print summary
    print("\n" + "=" * 60)
    print("SCAN RESULTS")
    print("=" * 60)
    print(f"Found {len(results)} stocks meeting criteria\n")

    for idx, result in enumerate(sorted(results, key=lambda x: x['volume_ratio'], reverse=True)[:10], 1):
        symbol = result['symbol'].replace('.NS', '')
        print(f"{idx:2d}. {symbol:12s} | ₹{result['price']:8.2f} | RSI:{result['rsi']:5.1f} | Vol:{result['volume_ratio']:4.1f}x")

    if len(results) > 10:
        print(f"\n... and {len(results) - 10} more stocks")

    print("=" * 60)


if __name__ == "__main__":
    main()
