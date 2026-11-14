#!/usr/bin/env python3
"""
Simple NSE Stock Scanner - Send qualifying stocks to Telegram
Designed for scheduled execution without complex dependencies
"""

import os
import sys
import json
from datetime import datetime
import pytz
import logging
import requests
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import numpy as np
except ImportError:
    logger.error("pandas/numpy not found. Installing...")
    os.system("python3 -m pip install pandas numpy -q")
    import pandas as pd
    import numpy as np

try:
    from telegram import Bot
except ImportError:
    logger.warning("telegram not found. Installing...")
    os.system("python3 -m pip install python-telegram-bot -q")
    from telegram import Bot

# F&O stocks list
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

class SimpleStockScanner:
    """Simple stock scanner without complex indicators"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if self.telegram_token and self.telegram_chat_id:
            self.bot = Bot(token=self.telegram_token)
            logger.info(f"✓ Telegram configured for chat {self.telegram_chat_id}")
        else:
            self.bot = None
            logger.warning("⚠ Telegram credentials missing. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")

    def get_stock_data(self, symbol):
        """Fetch stock data from Yahoo Finance"""
        try:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules=price,summaryDetail"
            headers = {'User-Agent': 'Mozilla/5.0'}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None

            data = response.json()
            price_data = data.get('quoteSummary', {}).get('result', [{}])[0].get('price', {})

            if not price_data:
                return None

            return {
                'symbol': symbol,
                'current_price': price_data.get('regularMarketPrice', {}).get('raw'),
                'prev_close': price_data.get('regularMarketPreviousClose', {}).get('raw'),
                'day_high': price_data.get('regularMarketDayHigh', {}).get('raw'),
                'day_low': price_data.get('regularMarketDayLow', {}).get('raw'),
                'volume': price_data.get('regularMarketVolume', {}).get('raw'),
                'market_cap': price_data.get('marketCap', {}).get('raw'),
            }
        except Exception as e:
            logger.debug(f"Error fetching {symbol}: {e}")
            return None

    def analyze_stock(self, data):
        """Simple analysis of stock data"""
        if not data or not data.get('current_price'):
            return None

        try:
            current = data['current_price']
            prev_close = data['prev_close']
            day_high = data['day_high']
            day_low = data['day_low']

            if not all([current, prev_close, day_high, day_low]):
                return None

            # Calculate metrics
            change_pct = ((current - prev_close) / prev_close) * 100
            intraday_range = ((day_high - day_low) / day_low) * 100
            close_position = ((current - day_low) / (day_high - day_low)) * 100

            # Simple scoring: stocks near day highs with positive change
            score = 0
            score += 30 if close_position > 75 else (20 if close_position > 60 else 10)
            score += 25 if change_pct > 1.5 else (15 if change_pct > 0.5 else 0)
            score += 20 if intraday_range > 3 else (10 if intraday_range > 1.5 else 0)
            score += 15 if data.get('volume', 0) > 0 else 0
            score += 10  # Base confidence

            return {
                'symbol': data['symbol'].replace('.NS', ''),
                'current_price': round(current, 2),
                'change_pct': round(change_pct, 2),
                'day_high': round(day_high, 2),
                'day_low': round(day_low, 2),
                'close_position': round(close_position, 1),
                'intraday_range': round(intraday_range, 2),
                'score': min(100, int(score))
            }
        except Exception as e:
            logger.debug(f"Error analyzing stock: {e}")
            return None

    def scan(self, stocks=None, min_score=60):
        """Scan stocks and return qualifying ones"""
        if stocks is None:
            stocks = COMPLETE_NSE_FO_UNIVERSE

        logger.info(f"Starting scan of {len(stocks)} stocks with min_score={min_score}")

        results = []
        for idx, symbol in enumerate(stocks, 1):
            try:
                clean_symbol = symbol.replace('.NS', '')

                if idx % 10 == 0:
                    logger.info(f"Progress: {idx}/{len(stocks)}")

                # Fetch data
                data = self.get_stock_data(symbol)
                if not data:
                    continue

                # Analyze
                analysis = self.analyze_stock(data)
                if not analysis:
                    continue

                # Filter by score
                if analysis['score'] >= min_score:
                    results.append(analysis)
                    logger.info(f"✓ {clean_symbol}: Score {analysis['score']}, "
                               f"Change {analysis['change_pct']:+.2f}%, "
                               f"Close {analysis['close_position']:.1f}%")

            except Exception as e:
                logger.debug(f"Error with {symbol}: {e}")
                continue

        logger.info(f"Scan complete: Found {len(results)} qualifying stocks")
        return results

    def send_to_telegram(self, results, limit=20):
        """Send results to Telegram"""
        if not self.bot or not results:
            if not self.bot:
                logger.info("Telegram not configured")
            return False

        try:
            # Sort by score
            sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)[:limit]

            timestamp = datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')

            message = f"*NSE PCS Scanner Results* - {timestamp}\n"
            message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += f"📊 Found {len(sorted_results)} qualifying stocks\n\n"

            for idx, stock in enumerate(sorted_results, 1):
                emoji = "🟢" if stock['score'] >= 80 else "🟡" if stock['score'] >= 70 else "🔴"
                message += f"{idx}. *{stock['symbol']}* {emoji}\n"
                message += f"   Price: ₹{stock['current_price']}\n"
                message += f"   Change: {stock['change_pct']:+.2f}%\n"
                message += f"   Score: {stock['score']}/100\n"
                message += f"   High/Low: ₹{stock['day_high']}/₹{stock['day_low']}\n\n"

            message += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            message += "⚠️ _Educational purposes only. Not financial advice._\n"

            logger.info(f"Sending {len(sorted_results)} stocks to Telegram...")
            self.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='Markdown'
            )

            logger.info("✅ Message sent to Telegram")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def save_results_to_file(self, results):
        """Save results to file"""
        if not results:
            return None

        try:
            timestamp = datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')
            filename = f"/tmp/pcs_scan_{timestamp}.txt"

            with open(filename, 'w') as f:
                f.write(f"NSE PCS Scanner Results - {datetime.now(self.ist)}\n")
                f.write("=" * 80 + "\n\n")

                sorted_results = sorted(results, key=lambda x: x['score'], reverse=True)

                for stock in sorted_results:
                    f.write(f"{stock['symbol']:<10} | Score: {stock['score']:<3} | "
                           f"Price: ₹{stock['current_price']:<8} | "
                           f"Change: {stock['change_pct']:>+7.2f}%\n")

                f.write("\n" + "=" * 80 + "\n")
                f.write(f"Total qualifying stocks: {len(results)}\n")

            logger.info(f"Results saved to {filename}")
            return filename

        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            return None


def main():
    logger.info("=" * 80)
    logger.info("NSE Stock Scanner - Scheduled Execution")
    logger.info("=" * 80)

    try:
        scanner = SimpleStockScanner()

        # Run scan
        results = scanner.scan(min_score=60)

        if results:
            logger.info(f"\n✅ Found {len(results)} qualifying stocks")

            # Save results
            scanner.save_results_to_file(results)

            # Send to Telegram
            scanner.send_to_telegram(results)

            # Print top 10
            logger.info("\n" + "=" * 80)
            logger.info("TOP QUALIFYING STOCKS:")
            logger.info("=" * 80)

            top_stocks = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
            for idx, stock in enumerate(top_stocks, 1):
                logger.info(f"{idx}. {stock['symbol']:<10} - Score: {stock['score']:<3} | "
                           f"₹{stock['current_price']:<8} | {stock['change_pct']:>+7.2f}%")
        else:
            logger.warning("⚠ No qualifying stocks found")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("Scan completed")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
