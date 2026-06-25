#!/usr/bin/env python3
"""
Simplified NSE Stock Scanner - No external TA library dependency
Runs with built-in technical analysis calculations
"""

import os
import sys
import logging
from datetime import datetime
import pytz
import numpy as np
import pandas as pd
import yfinance as yf
import requests
from io import BytesIO

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# NSE F&O Universe
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
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
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


def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=period).mean().values


def calculate_ema(prices, period=20):
    """Calculate Exponential Moving Average"""
    return pd.Series(prices).ewm(span=period).mean().values


def calculate_macd(prices):
    """Calculate MACD indicator"""
    ema12 = pd.Series(prices).ewm(span=12).mean()
    ema26 = pd.Series(prices).ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    hist = macd - signal
    return macd.values, signal.values, hist.values


def get_stock_data(symbol, period="3mo"):
    """Fetch stock data and calculate indicators"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate indicators
        closes = data['Close'].values
        data['RSI'] = calculate_rsi(closes)
        data['SMA_20'] = calculate_sma(closes, 20)
        data['SMA_50'] = calculate_sma(closes, 50)
        data['EMA_20'] = calculate_ema(closes, 20)
        data['MACD'], data['MACD_signal'], data['MACD_hist'] = calculate_macd(closes)

        # Calculate ATR
        high = data['High'].values
        low = data['Low'].values
        tr = np.maximum(high - low, np.maximum(abs(high - closes), abs(low - closes)))
        data['ATR'] = pd.Series(tr).rolling(14).mean().values

        # Calculate ADX (simplified)
        data['ADX'] = calculate_rsi(high - low, 14)

        return data
    except Exception as e:
        logger.debug(f"Error fetching {symbol}: {str(e)[:50]}")
        return None


def detect_current_day_breakout(data, lookback_days=20):
    """Detect if current day is a breakout"""
    if len(data) < lookback_days + 2:
        return False, 0

    try:
        # Get current day
        current_day = data.iloc[-1]
        lookback_data = data.iloc[-(lookback_days + 1):-1]

        # Calculate resistance
        resistance = lookback_data['High'].max()
        support = lookback_data['Low'].min()
        consolidation = ((resistance - support) / support) * 100

        # Check breakout conditions
        breakout = current_day['Close'] > resistance * 1.005
        volume_ok = current_day['Volume'] > lookback_data['Volume'].mean() * 1.2
        tight_consolidation = consolidation < 15

        if breakout and volume_ok and tight_consolidation:
            strength = ((current_day['Close'] - resistance) / resistance) * 100 * 100
            strength = min(100, max(50, strength))
            return True, strength

        return False, 0
    except:
        return False, 0


def scan_stocks(stocks_to_scan, max_stocks=None):
    """Scan stocks for trading opportunities"""
    results = []

    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    logger.info(f"Scanning {len(stocks_to_scan)} stocks...")

    for i, symbol in enumerate(stocks_to_scan):
        if (i + 1) % 20 == 0:
            logger.info(f"Progress: {i + 1}/{len(stocks_to_scan)}")

        try:
            data = get_stock_data(symbol, "3mo")
            if data is None:
                continue

            # Check volume
            current_volume = data['Volume'].iloc[-1]
            avg_volume_20 = data['Volume'].tail(21).iloc[:-1].mean()
            volume_ratio = current_volume / avg_volume_20

            if volume_ratio < 1.2:
                continue

            # Check breakout
            is_breakout, strength = detect_current_day_breakout(data)
            if not is_breakout or strength < 65:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            if current_rsi > 75 or current_rsi < 30:
                continue

            if current_adx < 20:
                continue

            # Store result
            results.append({
                'symbol': symbol,
                'price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'strength': strength,
                'data': data
            })

        except Exception as e:
            logger.debug(f"Error processing {symbol}: {str(e)[:30]}")
            continue

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)
    logger.info(f"Found {len(results)} qualifying stocks")
    return results


def display_results(results, limit=20):
    """Display results in formatted table"""
    if not results:
        print("\n❌ No stocks found matching criteria.\n")
        return

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%d-%m-%Y %H:%M IST')

    print("\n" + "=" * 90)
    print(f"📊 NSE F&O STOCK SCANNER - CURRENT DAY BREAKOUTS")
    print(f"⏰ {timestamp}")
    print("=" * 90)
    print(f"\n✅ Found {len(results)} qualifying stocks\n")

    print(f"{'#':<3} {'Symbol':<8} {'Price':<10} {'Volume':<8} {'RSI':<6} {'ADX':<6} {'Strength':<10}")
    print("-" * 90)

    for idx, result in enumerate(results[:limit], 1):
        symbol = result['symbol'].replace('.NS', '')
        price = result['price']
        volume = result['volume_ratio']
        rsi = result['rsi']
        adx = result['adx']
        strength = result['strength']

        print(f"{idx:<3} {symbol:<8} ₹{price:<9.2f} {volume:<7.1f}x {rsi:<5.1f} {adx:<5.1f} {strength:<9.1f}%")

    print("-" * 90)
    print("\n⚠️  Disclaimer: For educational purpose only. Not investment advice.\n")


def export_to_csv(results, filename=None):
    """Export results to CSV"""
    if not results:
        return None

    if filename is None:
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        filename = f"scan_results_{timestamp}.csv"

    rows = []
    for r in results:
        rows.append({
            'Symbol': r['symbol'].replace('.NS', ''),
            'Price': f"{r['price']:.2f}",
            'Volume_Ratio': f"{r['volume_ratio']:.2f}",
            'RSI': f"{r['rsi']:.1f}",
            'ADX': f"{r['adx']:.1f}",
            'Strength': f"{r['strength']:.1f}"
        })

    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    logger.info(f"Saved to {filename}")
    return filename


def send_to_telegram(results, bot_token, chat_id):
    """Send results to Telegram"""
    if not results or not bot_token or not chat_id:
        return False

    message = "📊 *NSE Stock Scanner Results*\n\n"
    message += f"Found {len(results)} stocks:\n\n"

    for i, r in enumerate(results[:10], 1):
        symbol = r['symbol'].replace('.NS', '')
        message += f"{i}. {symbol}\n"
        message += f"   Price: ₹{r['price']:.2f}\n"
        message += f"   Volume: {r['volume_ratio']:.1f}x\n"
        message += f"   Strength: {r['strength']:.0f}%\n\n"

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {'chat_id': chat_id, 'text': message}
        requests.post(url, data=data, timeout=10)
        logger.info("Sent to Telegram")
        return True
    except Exception as e:
        logger.error(f"Telegram error: {e}")
        return False


def main():
    """Main entry point"""
    print("\n" + "=" * 90)
    print("🚀 NSE F&O STOCK SCANNER - SIMPLIFIED VERSION")
    print("=" * 90 + "\n")

    # Run scan
    results = scan_stocks(COMPLETE_NSE_FO_UNIVERSE)

    # Display
    display_results(results, limit=25)

    # Export
    if results:
        csv_file = export_to_csv(results)
        print(f"💾 Results saved to: {csv_file}\n")

        # Try Telegram if credentials available
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if bot_token and chat_id:
            if send_to_telegram(results, bot_token, chat_id):
                print("✅ Sent to Telegram\n")


if __name__ == "__main__":
    main()
