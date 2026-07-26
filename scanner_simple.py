#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Simplified Standalone Mode
Focuses on high-probability setups without complex dependencies
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
import pytz

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install yfinance pandas numpy requests")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# NSE F&O Universe - 219 stocks
NSE_FO_STOCKS = [
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

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_telegram_message(text):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except:
        return False


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    gains = deltas.copy()
    gains[gains < 0] = 0
    losses = -deltas.copy()
    losses[losses < 0] = 0

    if len(gains) < period:
        return None

    avg_gain = gains[-period:].mean()
    avg_loss = losses[-period:].mean()

    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def analyze_stock(symbol):
    """Analyze a single stock for PCS opportunities"""
    try:
        # Fetch stock data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="3mo", interval="1d")

        if hist.empty or len(hist) < 20:
            return None

        # Get current day data
        current = hist.iloc[-1]
        current_price = current['Close']
        current_volume = current['Volume']

        # Calculate technical indicators
        closes = hist['Close'].values
        rsi = calculate_rsi(closes)

        if rsi is None:
            return None

        # Volume analysis
        avg_volume = hist['Volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0

        # Moving averages
        sma_20 = hist['Close'].tail(20).mean()
        sma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else None

        # Price position
        above_sma20 = current_price > sma_20
        above_sma50 = current_price > sma_50 if sma_50 else False

        # Recent trend (last 5 days)
        recent_closes = closes[-5:]
        uptrend = recent_closes[-1] > recent_closes[0]

        # High confidence if:
        # 1. RSI between 30-70 (not overbought/oversold)
        # 2. Volume above 1.0x average
        # 3. Price above both key MAs
        # 4. Recent uptrend

        confidence_score = 0

        # RSI check
        if 30 <= rsi <= 70:
            confidence_score += 30
        elif 25 <= rsi <= 75:
            confidence_score += 15

        # Volume check
        if volume_ratio >= 1.5:
            confidence_score += 25
        elif volume_ratio >= 1.0:
            confidence_score += 15

        # MA support
        if above_sma20:
            confidence_score += 15
        if above_sma50:
            confidence_score += 15

        # Trend
        if uptrend:
            confidence_score += 15

        # Only return if score >= 50 (moderate confidence)
        if confidence_score >= 50:
            return {
                'symbol': symbol,
                'price': current_price,
                'rsi': rsi,
                'volume_ratio': volume_ratio,
                'above_sma20': above_sma20,
                'above_sma50': above_sma50,
                'uptrend': uptrend,
                'confidence': confidence_score,
                'sma_20': sma_20,
                'volume': current_volume
            }

        return None

    except Exception as e:
        logger.debug(f"Error analyzing {symbol}: {str(e)}")
        return None


def run_scan():
    """Run the PCS scanner"""
    logger.info("=" * 60)
    logger.info("NSE F&O PCS Scanner - Simplified Mode")
    logger.info(f"Scanning {len(NSE_FO_STOCKS)} stocks")
    logger.info("=" * 60)

    results = []

    for i, symbol in enumerate(NSE_FO_STOCKS):
        if (i + 1) % 50 == 0:
            logger.info(f"Progress: {i+1}/{len(NSE_FO_STOCKS)} scanned, {len(results)} qualifying")

        analysis = analyze_stock(symbol)
        if analysis:
            results.append(analysis)

    # Sort by confidence
    results.sort(key=lambda x: x['confidence'], reverse=True)

    logger.info("=" * 60)
    logger.info(f"SCAN COMPLETE: Found {len(results)} qualifying stocks")
    logger.info("=" * 60)

    return results


def format_results(results):
    """Format results for display and Telegram"""
    if not results:
        return "❌ No qualifying stocks found"

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    # Create main message
    message = f"<b>📊 NSE F&O PCS Scan Results</b>\n"
    message += f"<b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}\n"
    message += f"<b>Found:</b> {len(results)} stocks\n"
    message += "─" * 50 + "\n\n"

    # Top 15 stocks
    for i, stock in enumerate(results[:15], 1):
        symbol = stock['symbol'].replace('.NS', '')
        conf = stock['confidence']
        message += f"<b>{i}. {symbol}</b> ({conf}%)\n"
        message += f"   Price: ₹{stock['price']:.2f}\n"
        message += f"   RSI: {stock['rsi']:.1f} | Vol: {stock['volume_ratio']:.1f}x\n"

    if len(results) > 15:
        message += f"\n<b>... and {len(results) - 15} more stocks</b>\n"

    return message


def main():
    """Main execution"""
    try:
        # Run scan
        results = run_scan()

        # Format results
        formatted = format_results(results)

        # Print to console
        print("\n" + formatted + "\n")

        # Send to Telegram if configured
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            logger.info("Sending results to Telegram...")
            if send_telegram_message(formatted):
                logger.info("✅ Results sent to Telegram")

                # Send stock list
                symbols = [r['symbol'].replace('.NS', '') for r in results[:20]]
                stock_list = "📋 Top Stocks:\n\n" + " | ".join(symbols)
                send_telegram_message(stock_list)
            else:
                logger.warning("⚠️ Failed to send to Telegram")
        else:
            logger.info("⚠️ Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")

        return 0

    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
