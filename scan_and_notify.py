#!/usr/bin/env python3
"""
Simplified Stock Scanner - Runs PCS screening and sends results to Telegram
No dependency on 'ta' library - uses pandas/numpy for indicators
"""

import sys
import os
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
from typing import Dict, List, Tuple, Optional

warnings.filterwarnings('ignore')

# F&O Universe
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
    'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS', 'PPLPHARMA.NS',
    'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS', 'PRESTIGE.NS', 'PNB.NS',
    'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS', 'SBILIFE.NS',
    'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS',
    'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS',
    'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS',
    'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TECHM.NS',
    'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS',
    'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS',
    'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS',
    'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]


class SimpleStockScanner:
    """Simplified stock scanner using basic indicators"""

    @staticmethod
    def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_sma(data: pd.Series, window: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        return data.rolling(window=window).mean()

    @staticmethod
    def check_volume_criteria(data: pd.DataFrame, min_ratio: float = 1.2) -> Tuple[bool, float]:
        """Check if current day volume meets criteria"""
        if len(data) < 20:
            return False, 0

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

        ratio = current_volume / avg_20_volume
        return ratio >= min_ratio, ratio

    @staticmethod
    def detect_bullish_pattern(data: pd.DataFrame) -> Tuple[bool, float]:
        """Detect basic bullish patterns"""
        if len(data) < 30:
            return False, 0

        close = data['Close']
        high = data['High']
        low = data['Low']
        volume = data['Volume']

        # Calculate indicators
        rsi = SimpleStockScanner.calculate_rsi(close)
        sma_20 = SimpleStockScanner.calculate_sma(close, 20)
        sma_50 = SimpleStockScanner.calculate_sma(close, 50)

        # Get current values
        current_close = close.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_volume = volume.iloc[-1]
        avg_volume = volume.tail(20).mean()

        strength = 0

        # Basic bullish conditions
        if current_close > sma_20.iloc[-1]:
            strength += 20

        if sma_20.iloc[-1] > sma_50.iloc[-1]:
            strength += 20

        if 40 <= current_rsi <= 70:
            strength += 20

        if current_volume > avg_volume * 1.5:
            strength += 20

        # Uptrend check - higher highs, higher lows
        if len(data) >= 5:
            if high.iloc[-1] > high.iloc[-2] and low.iloc[-1] > low.iloc[-2]:
                strength += 20

        return strength >= 60, strength

    @staticmethod
    def get_stock_data(symbol: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """Fetch stock data"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            return data if len(data) >= 20 else None
        except:
            return None


class TelegramNotifier:
    """Send notifications to Telegram"""

    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, message: str) -> bool:
        """Send a message to Telegram"""
        if not self.is_configured():
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram: {e}")
            return False

    def send_results(self, results: List[Dict], scan_time: str) -> bool:
        """Format and send results to Telegram"""
        if not results:
            message = f"<b>🚫 NSE F&O Scan - No Results</b>\n📅 {scan_time}"
            self.send_message(message)
            return True

        # Sort by strength
        results.sort(key=lambda x: x['strength'], reverse=True)

        # Header
        header = f"""<b>📊 NSE F&O Scanner Results</b>
📅 {scan_time}
🎯 Found: <b>{len(results)} stocks</b>

<b>🏆 Top Opportunities:</b>"""

        # Add top 10 stocks
        stocks_text = ""
        for idx, result in enumerate(results[:10], 1):
            symbol = result['symbol'].replace('.NS', '')
            stocks_text += f"\n{idx}. <b>{symbol}</b> ({result['strength']:.0f}% | Vol: {result['volume_ratio']:.1f}x)"

        footer = ""
        if len(results) > 10:
            footer = f"\n\n... + {len(results) - 10} more stocks"

        message = header + stocks_text + footer

        # Send main message
        sent = self.send_message(message)

        # Send detailed list as follow-up
        if len(results) > 10 and sent:
            detail_msg = "<b>📋 Full List:</b>\n\n"
            for idx, result in enumerate(results, 1):
                symbol = result['symbol'].replace('.NS', '')
                detail_msg += f"{idx}. {symbol} - {result['strength']:.0f}%\n"
            self.send_message(detail_msg)

        return True


def main():
    """Main execution"""

    print(f"""
{'='*60}
🤖 NSE F&O Stock Scanner - Automated Routine
{'='*60}
📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")

    # Configuration
    min_volume_ratio = float(os.getenv('SCAN_MIN_VOLUME', 1.2))
    max_stocks = int(os.getenv('SCAN_MAX_STOCKS', 50))

    # Initialize notifier
    notifier = TelegramNotifier()

    if notifier.is_configured():
        print("✅ Telegram configured")
    else:
        print("⚠️  Telegram NOT configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")

    # Scan stocks
    print(f"\n🔍 Scanning {len(COMPLETE_NSE_FO_UNIVERSE[:max_stocks])} stocks...")

    results = []
    scanner = SimpleStockScanner()

    for i, symbol in enumerate(COMPLETE_NSE_FO_UNIVERSE[:max_stocks], 1):
        clean_symbol = symbol.replace('.NS', '')
        print(f"[{i:3d}/{max_stocks}] {clean_symbol:12}", end='\r')

        try:
            # Get data
            data = scanner.get_stock_data(symbol)
            if data is None:
                continue

            # Check volume
            volume_ok, volume_ratio = scanner.check_volume_criteria(data, min_volume_ratio)
            if not volume_ok:
                continue

            # Check pattern
            pattern_ok, strength = scanner.detect_bullish_pattern(data)
            if not pattern_ok:
                continue

            # Get price
            current_price = data['Close'].iloc[-1]

            results.append({
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'strength': strength
            })

        except Exception as e:
            continue

    print(f"\n✅ Scan complete! Found {len(results)} stocks\n")

    # Send to Telegram
    scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if notifier.is_configured():
        print("📤 Sending to Telegram...")
        notifier.send_results(results, scan_time)
        print("✅ Sent!")

    # Display results
    if results:
        print("\n🏆 Top 5 Stocks:\n")
        for idx, r in enumerate(sorted(results, key=lambda x: x['strength'], reverse=True)[:5], 1):
            print(f"{idx}. {r['symbol'].replace('.NS', '')} - {r['strength']:.0f}% strength")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
