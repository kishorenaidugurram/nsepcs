#!/usr/bin/env python3
"""
Simple NSE F&O PCS Scanner without ta library dependency.
Sends qualifying stocks to Telegram.
"""

import os
import sys
import logging
import asyncio
from datetime import datetime
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

import yfinance as yf
import pandas as pd
import numpy as np

# Try to import telegram
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Telegram not available - run: pip3 install python-telegram-bot --break-system-packages")

# Stock universe
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period+1]
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


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return pd.Series(prices).rolling(window=period).mean().values


def scan_stock(symbol):
    """Scan a single stock"""
    try:
        # Fetch data
        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo")

        if len(data) < 30:
            return None

        closes = data['Close'].values
        volumes = data['Volume'].values

        # Calculate indicators
        rsi = calculate_rsi(closes)[-1]
        sma20 = calculate_sma(closes, 20)[-1]
        sma50 = calculate_sma(closes, 50)[-1]

        current_price = closes[-1]
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])

        # Check criteria
        price_above_sma = current_price > sma20 > sma50
        rsi_good = 30 <= rsi <= 70
        volume_good = current_volume > avg_volume

        if not (price_above_sma and rsi_good and volume_good):
            return None

        # Calculate score
        score = 0
        if current_price > sma50:
            score += 20
        if rsi > 40 and rsi < 65:
            score += 25
        if current_volume > avg_volume * 1.5:
            score += 25
        if current_price > sma20:
            score += 15
        if current_volume > avg_volume * 2.0:
            score += 15

        if score < 60:
            return None

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'sma20': sma20,
            'sma50': sma50,
            'volume_ratio': current_volume / avg_volume,
            'score': score
        }

    except Exception as e:
        logger.debug(f"Error scanning {symbol}: {e}")
        return None


class TelegramNotifier:
    """Send notifications to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.bot = Bot(token=bot_token) if TELEGRAM_AVAILABLE else None

    async def send_message(self, message):
        """Send message to Telegram"""
        if not self.bot:
            logger.warning("Telegram bot not available")
            return False

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info("✅ Message sent to Telegram")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send Telegram message: {e}")
            return False

    async def send_results(self, stocks, scan_date):
        """Send results to Telegram"""
        if not stocks:
            msg = "❌ No qualifying stocks found in today's scan."
        else:
            msg = f"""
📊 <b>NSE F&O PCS Scan Results</b>
📅 {scan_date}
🎯 Total Qualified: {len(stocks)}

<b>Stocks Meeting Filter Criteria:</b>
"""
            for i, stock in enumerate(stocks[:20], 1):
                symbol = stock['symbol'].replace('.NS', '')
                msg += f"\n{i:2d}. <b>{symbol}</b> | ₹{stock['price']:.2f} | RSI: {stock['rsi']:>5.1f} | Vol: {stock['volume_ratio']:.1f}x | Score: {stock['score']:.0f}"

        await self.send_message(msg)


async def main():
    """Main execution"""

    logger.info("=" * 70)
    logger.info("NSE F&O PCS SCANNER - AUTOMATED TELEGRAM NOTIFIER")
    logger.info("=" * 70)

    scan_date = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M:%S IST')
    logger.info(f"Scan started at: {scan_date}")

    # Scan stocks
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_stock, sym): sym for sym in COMPLETE_NSE_FO_UNIVERSE}
        completed = 0

        for future in as_completed(futures):
            completed += 1
            if completed % 20 == 0:
                logger.info(f"Progress: {completed}/{len(COMPLETE_NSE_FO_UNIVERSE)}")

            result = future.result()
            if result:
                results.append(result)

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    logger.info(f"\n✅ Scan Complete! Found {len(results)} qualifying stocks\n")

    if results:
        print("\n" + "=" * 90)
        print("QUALIFYING STOCKS - MEETING FILTER CRITERIA")
        print("=" * 90)
        print(f"{'#':<3} {'Symbol':<12} {'Price':<10} {'RSI':<6} {'Vol Ratio':<10} {'Score':<7}")
        print("-" * 90)
        for i, stock in enumerate(results[:20], 1):
            symbol = stock['symbol'].replace('.NS', '')
            print(f"{i:<3} {symbol:<12} ₹{stock['price']:>8.2f} {stock['rsi']:>5.1f}  {stock['volume_ratio']:>8.2f}x  {stock['score']:>6.0f}")
        print("=" * 90 + "\n")

    # Send to Telegram
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if bot_token and chat_id and TELEGRAM_AVAILABLE:
        logger.info("📱 Sending results to Telegram...")
        notifier = TelegramNotifier(bot_token, chat_id)
        await notifier.send_results(results, scan_date)
    else:
        if not bot_token or not chat_id:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
            logger.info("   Set them to enable Telegram notifications:")
            logger.info("   export TELEGRAM_BOT_TOKEN='your_token'")
            logger.info("   export TELEGRAM_CHAT_ID='your_chat_id'")
        else:
            logger.warning("⚠️ Telegram library not available")

    # Save to CSV
    if results:
        df = pd.DataFrame(results)
        csv_file = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_file, index=False)
        logger.info(f"💾 Results saved to {csv_file}")

    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
