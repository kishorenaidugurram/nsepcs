#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Integration
Screens stocks based on technical criteria and sends results to Telegram
"""

import os
import sys
import json
import time
from datetime import datetime
import pytz
import requests
import yfinance as yf
import pandas as pd
import numpy as np
import ta
import warnings
warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# NSE F&O Stock Universe
COMPLETE_NSE_FO_UNIVERSE = [
    # Updated 208 F&O Individual stocks
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
    'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS', 'IRCTC.NS',
    'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS',
    'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS',
    'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS',
    'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS',
    'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS',
    'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MPHASIS.NS',
    'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS',
    'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS',
    'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS',
    'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
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

class TelegramScanner:
    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def send_telegram_message(self, message):
        """Send message to Telegram"""
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            print("⚠️ Telegram credentials not set. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
            return False

        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"✅ Telegram message sent successfully")
                return True
            else:
                print(f"❌ Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Telegram error: {str(e)}")
            return False

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data with technical indicators"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")

            if len(data) < 20:
                return None

            # Calculate indicators
            data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
            data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
            data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
            data['EMA_20'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
            data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
            data['MACD'] = ta.trend.MACD(data['Close']).macd()
            data['MACD_signal'] = ta.trend.MACD(data['Close']).macd_signal()
            data['Stoch_K'] = ta.momentum.StochasticOscillator(data['High'], data['Low'], data['Close']).stoch()

            return data
        except Exception as e:
            return None

    def check_volume_criteria(self, data, min_ratio=1.5):
        """Check volume criteria"""
        if len(data) < 21:
            return False, 0

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_20_volume

        return volume_ratio >= min_ratio, volume_ratio

    def scan_stock(self, symbol, filters):
        """Scan a single stock against criteria"""
        try:
            data = self.get_stock_data(symbol)
            if data is None:
                return None

            current_close = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_macd = data['MACD'].iloc[-1]
            current_macd_signal = data['MACD_signal'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]

            # Apply filters
            rsi_check = filters['rsi_min'] <= current_rsi <= filters['rsi_max']
            adx_check = current_adx >= filters['adx_min']
            price_above_sma = current_close > sma_20
            sma_alignment = sma_20 > sma_50
            macd_check = current_macd > current_macd_signal

            volume_check, volume_ratio = self.check_volume_criteria(data, filters['volume_ratio'])

            # Calculate score
            score = 0
            signals = []

            if rsi_check:
                score += 20
                signals.append(f"RSI: {current_rsi:.1f}")

            if adx_check:
                score += 20
                signals.append(f"ADX: {current_adx:.1f}")

            if price_above_sma:
                score += 15
                signals.append("Price > SMA20")

            if sma_alignment:
                score += 15
                signals.append("SMA20 > SMA50")

            if macd_check:
                score += 15
                signals.append("MACD Bullish")

            if volume_check:
                score += 15
                signals.append(f"Volume: {volume_ratio:.2f}x")

            if score >= filters['min_score']:
                return {
                    'symbol': symbol,
                    'price': current_close,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'score': score,
                    'signals': signals,
                    'volume_ratio': volume_ratio,
                    'date': datetime.now(self.ist).strftime('%Y-%m-%d')
                }

            return None

        except Exception as e:
            return None

    def run_scan(self, filters):
        """Run scan on all stocks"""
        qualified_stocks = []
        failed_stocks = []

        print(f"\n📊 Starting NSE F&O Scanner with {len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")
        print(f"📋 Filters: RSI({filters['rsi_min']}-{filters['rsi_max']}), ADX(≥{filters['adx_min']}), "
              f"Volume(≥{filters['volume_ratio']}x), Min Score(≥{filters['min_score']})")

        for idx, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE, 1):
            if idx % 50 == 0:
                print(f"   Scanned {idx}/{len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")

            result = self.scan_stock(symbol, filters)
            if result:
                qualified_stocks.append(result)

            # Rate limiting
            time.sleep(0.1)

        print(f"\n✅ Scan completed!")
        return qualified_stocks

    def format_telegram_message(self, stocks):
        """Format stocks for Telegram message"""
        if not stocks:
            return "<b>📊 NSE F&O Scanner Report</b>\n\n❌ No stocks met the criteria today."

        # Sort by score
        stocks.sort(key=lambda x: x['score'], reverse=True)

        message = f"""<b>📊 NSE F&O Scanner Report</b>
<i>Generated: {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M:%S')} IST</i>

<b>Found {len(stocks)} qualifying stocks:</b>

"""

        for i, stock in enumerate(stocks[:10], 1):  # Top 10
            message += f"""<b>{i}. {stock['symbol'].replace('.NS', '')}</b>
   Price: ₹{stock['price']:.2f}
   Score: {stock['score']}/100
   RSI: {stock['rsi']:.1f} | ADX: {stock['adx']:.1f}
   Volume: {stock['volume_ratio']:.2f}x
   Signals: {', '.join(stock['signals'][:3])}

"""

        if len(stocks) > 10:
            message += f"\n... and {len(stocks) - 10} more stocks\n"

        message += f"\n<i>All {len(stocks)} stocks exported to Excel</i>"

        return message

    def save_to_csv(self, stocks):
        """Save results to CSV"""
        if not stocks:
            return None

        df = pd.DataFrame(stocks)
        df = df.sort_values('score', ascending=False)

        filename = f"scanner_results_{datetime.now(self.ist).strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ Results saved to: {filename}")

        return filename

def main():
    """Main execution"""
    # Default filters
    filters = {
        'rsi_min': 30,
        'rsi_max': 70,
        'adx_min': 20,
        'volume_ratio': 1.5,
        'min_score': 60
    }

    scanner = TelegramScanner()

    # Run scan
    qualified_stocks = scanner.run_scan(filters)

    # Save results
    scanner.save_to_csv(qualified_stocks)

    # Send to Telegram
    message = scanner.format_telegram_message(qualified_stocks)
    scanner.send_telegram_message(message)

    # Print summary
    print(f"\n{'='*60}")
    print(f"📈 SUMMARY")
    print(f"{'='*60}")
    print(f"Total stocks qualified: {len(qualified_stocks)}")
    if qualified_stocks:
        print(f"\nTop 5 stocks by score:")
        for stock in sorted(qualified_stocks, key=lambda x: x['score'], reverse=True)[:5]:
            print(f"  • {stock['symbol']}: Score {stock['score']} - RSI {stock['rsi']:.1f}, ADX {stock['adx']:.1f}")

if __name__ == "__main__":
    main()
