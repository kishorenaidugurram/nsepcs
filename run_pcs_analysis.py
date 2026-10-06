#!/usr/bin/env python3
"""
NSE F&O PCS Screener - Standalone Analysis Script
Runs PCS analysis and sends qualifying stocks to Telegram
"""

import os
import sys
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import pytz
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json

# Try to import telegram
try:
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: python-telegram-bot not installed. Install with: pip install python-telegram-bot")

warnings.filterwarnings('ignore')

# F&O Stocks list (from streamlit_app.py)
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

class PCSAnalyzer:
    def __init__(self, min_score=55, max_stocks=25):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.min_score = min_score
        self.max_stocks = max_stocks
        self.results = []

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def fetch_stock_data(self, symbol, period="3mo"):
        """Fetch stock data and calculate technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if len(data) < 20:
                return None

            # Calculate technical indicators manually
            data['RSI'] = self._calculate_rsi(data['Close'], 14)
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()
            data['EMA_20'] = data['Close'].ewm(span=20).mean()

            return data
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None

    def calculate_pcs_score(self, data, symbol):
        """Calculate PCS score based on technical analysis"""
        try:
            if data is None or len(data) < 20:
                return None

            current = data.iloc[-1]
            score = 0
            details = {}

            # 1. Bullish Momentum (30%)
            rsi = current['RSI']
            if 45 <= rsi <= 65:
                momentum_score = 30
            elif 40 <= rsi <= 70:
                momentum_score = 25
            elif 30 <= rsi <= 80:
                momentum_score = 20
            else:
                momentum_score = 10

            score += momentum_score
            details['momentum_score'] = momentum_score
            details['rsi'] = round(rsi, 2)

            # 2. Trend Strength (25%)
            close = current['Close']
            sma_20 = current['SMA_20']
            sma_50 = current['SMA_50']

            if close > sma_20 > sma_50:
                trend_score = 25
            elif close > sma_20:
                trend_score = 20
            elif close > sma_50:
                trend_score = 15
            else:
                trend_score = 5

            score += trend_score
            details['trend_score'] = trend_score

            # 3. Support Proximity (20%)
            distance_from_support = ((close - sma_20) / sma_20) * 100
            if distance_from_support >= 2:
                support_score = 20
            elif distance_from_support >= 0:
                support_score = 15
            elif distance_from_support >= -2:
                support_score = 10
            else:
                support_score = 5

            score += support_score
            details['support_score'] = support_score

            # 4. Volatility (15%)
            returns = data['Close'].pct_change()
            volatility = returns.std() * np.sqrt(252) * 100

            if 15 <= volatility <= 35:
                volatility_score = 15
            elif 10 <= volatility <= 45:
                volatility_score = 12
            elif 5 <= volatility <= 60:
                volatility_score = 8
            else:
                volatility_score = 4

            score += volatility_score
            details['volatility_score'] = volatility_score
            details['volatility'] = round(volatility, 2)

            # 5. Volume (10%)
            current_volume = current['Volume']
            avg_volume = data['Volume'].tail(20).mean()
            volume_ratio = current_volume / avg_volume

            if volume_ratio >= 1.2:
                volume_score = 10
            elif volume_ratio >= 1.0:
                volume_score = 7
            elif volume_ratio >= 0.8:
                volume_score = 4
            else:
                volume_score = 0

            score += volume_score
            details['volume_score'] = volume_score
            details['volume_ratio'] = round(volume_ratio, 2)

            # Determine confidence level
            if score >= 75:
                confidence = "HIGH"
                short_strike_otm = 5
                long_strike_otm = 10
            elif score >= 60:
                confidence = "MEDIUM"
                short_strike_otm = 8
                long_strike_otm = 13
            else:
                confidence = "LOW"
                short_strike_otm = 12
                long_strike_otm = 17

            return {
                'symbol': symbol,
                'score': round(score, 2),
                'confidence': confidence,
                'rsi': details['rsi'],
                'volatility': details['volatility'],
                'volume_ratio': details['volume_ratio'],
                'short_strike_otm': short_strike_otm,
                'long_strike_otm': long_strike_otm,
                'price': round(close, 2),
                'sma_20': round(sma_20, 2),
                'current_date': data.index[-1].strftime('%Y-%m-%d')
            }
        except Exception as e:
            print(f"Error calculating score for {symbol}: {str(e)}")
            return None

    def run_analysis(self):
        """Run PCS analysis on all stocks"""
        print(f"Starting PCS analysis for {len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")
        print(f"Filter: Minimum Score = {self.min_score}, Max Stocks = {self.max_stocks}")
        print("-" * 80)

        results = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self._analyze_single_stock, symbol): symbol
                for symbol in COMPLETE_NSE_FO_UNIVERSE
            }

            completed = 0
            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]
                try:
                    result = future.result()
                    if result and result['score'] >= self.min_score:
                        results.append(result)
                        print(f"✓ {symbol}: Score={result['score']} | {result['confidence']}")
                except Exception as e:
                    print(f"✗ {symbol}: Error - {str(e)}")

                if completed % 20 == 0:
                    print(f"  Progress: {completed}/{len(COMPLETE_NSE_FO_UNIVERSE)}")

        # Sort by score (descending) and limit to max_stocks
        results = sorted(results, key=lambda x: x['score'], reverse=True)[:self.max_stocks]

        print("-" * 80)
        print(f"\n✓ Analysis Complete!")
        print(f"Qualifying Stocks: {len(results)}")

        return results

    def _analyze_single_stock(self, symbol):
        """Analyze a single stock"""
        data = self.fetch_stock_data(symbol)
        return self.calculate_pcs_score(data, symbol)

    def format_results(self, results):
        """Format results as a dataframe"""
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame(results)
        df = df[['symbol', 'score', 'confidence', 'price', 'rsi', 'volatility', 'volume_ratio', 'sma_20']]
        df = df.sort_values('score', ascending=False)
        return df

    def send_to_telegram(self, results, bot_token=None, chat_id=None):
        """Send results to Telegram"""
        if not TELEGRAM_AVAILABLE:
            print("Telegram not available. Skipping telegram send.")
            return False

        # Get credentials from environment or parameters
        bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            print("Error: Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")
            print("Set them via environment variables or pass as arguments")
            return False

        try:
            bot = Bot(token=bot_token)

            # Prepare message
            message = self._format_telegram_message(results)

            # Send message
            bot.send_message(chat_id=chat_id, text=message, parse_mode='HTML')
            print(f"\n✓ Results sent to Telegram!")
            return True

        except Exception as e:
            print(f"\nError sending to Telegram: {str(e)}")
            return False

    def _format_telegram_message(self, results):
        """Format results for Telegram message"""
        if not results:
            return "❌ No stocks found matching the criteria."

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')

        message = f"""<b>🚀 NSE F&O PCS SCREENER RESULTS</b>
<i>{current_time} IST</i>

<b>Stocks Meeting Criteria: {len(results)}</b>

"""
        for idx, result in enumerate(results[:15], 1):  # Top 15 only for telegram
            message += f"""<b>{idx}. {result['symbol']}</b>
   Score: {result['score']} ({result['confidence']})
   Price: ₹{result['price']} | RSI: {result['rsi']} | Vol: {result['volatility']}%

"""

        message += f"""
<b>Details:</b>
• Min Score Filter: {self.min_score}
• Total Qualifying: {len(results)}
• Time Generated: {current_time}

<i>Always verify and do your own analysis before trading.</i>"""

        return message

    def save_results(self, results, filename=None):
        """Save results to file"""
        if not filename:
            ist = pytz.timezone('Asia/Kolkata')
            date_str = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
            filename = f'pcs_results_{date_str}.csv'

        df = self.format_results(results)
        df.to_csv(filename, index=False)
        print(f"✓ Results saved to {filename}")
        return filename


def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description='NSE F&O PCS Screener')
    parser.add_argument('--min-score', type=float, default=55, help='Minimum PCS score (default: 55)')
    parser.add_argument('--max-stocks', type=int, default=25, help='Maximum stocks to analyze (default: 25)')
    parser.add_argument('--telegram-token', help='Telegram bot token')
    parser.add_argument('--telegram-chat-id', help='Telegram chat ID')
    parser.add_argument('--no-telegram', action='store_true', help='Skip Telegram send')
    parser.add_argument('--save-csv', action='store_true', help='Save results to CSV')

    args = parser.parse_args()

    # Run analysis
    analyzer = PCSAnalyzer(min_score=args.min_score, max_stocks=args.max_stocks)
    results = analyzer.run_analysis()

    # Display results
    if results:
        print("\nTop Results:")
        df = analyzer.format_results(results)
        print(df.to_string(index=False))
    else:
        print("No stocks found matching the criteria.")

    # Send to Telegram if enabled
    if not args.no_telegram and TELEGRAM_AVAILABLE:
        analyzer.send_to_telegram(results, args.telegram_token, args.telegram_chat_id)

    # Save CSV if requested
    if args.save_csv:
        analyzer.save_results(results)


if __name__ == "__main__":
    main()
