#!/usr/bin/env python3
"""
NSE F&O PCS Scanner with Telegram Notification
Analyzes NSE F&O stocks and sends results to Telegram

Setup Instructions:
===================
1. Set environment variables:
   export TELEGRAM_BOT_TOKEN='your_bot_token_here'
   export TELEGRAM_CHAT_ID='your_chat_id_here'

2. Run the scanner:
   python3 run_scanner_and_notify.py

For scheduled execution with cron:
   TELEGRAM_BOT_TOKEN='token' TELEGRAM_CHAT_ID='chat_id' python3 /path/to/run_scanner_and_notify.py

"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta
import pytz
import yfinance as yf
import pandas as pd
import numpy as np
import warnings
from finta import TA
warnings.filterwarnings('ignore')

# NSE F&O stocks list
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

class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.enabled = bool(self.bot_token and self.chat_id)

    def send(self, message, parse_mode='HTML'):
        """Send message to Telegram"""
        if not self.enabled:
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️  Error sending Telegram message: {e}")
            return False

    def notify_status(self, message):
        """Send status notification"""
        if self.enabled:
            return self.send(message)
        else:
            print(f"📢 {message}")
            return True


class NSEPCSScanner:
    """Lightweight NSE F&O PCS Scanner"""

    def __init__(self):
        self.results = []
        self.failed_stocks = []

    def fetch_stock_data(self, symbol, period="3mo"):
        """Fetch stock data from Yahoo Finance"""
        try:
            if not symbol.endswith('.NS'):
                symbol = f"{symbol}.NS"

            data = yf.download(symbol, period=period, progress=False, timeout=10)

            if data is None or data.empty:
                return None

            return data
        except Exception as e:
            return None

    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        if data is None or data.empty or len(data) < 20:
            return None

        try:
            df = data.copy()
            df.columns = [col.lower() for col in df.columns]

            if 'open' not in df.columns:
                df['open'] = df['close']

            indicators = {}

            # RSI
            try:
                rsi_val = TA.RSI(df, period=14)
                indicators['rsi'] = float(rsi_val.iloc[-1]) if isinstance(rsi_val, pd.Series) else float(rsi_val)
            except:
                indicators['rsi'] = None

            # ADX
            try:
                adx_val = TA.ADX(df, period=14)
                indicators['adx'] = float(adx_val.iloc[-1]) if isinstance(adx_val, pd.Series) else float(adx_val)
            except:
                indicators['adx'] = None

            # SMA 20
            try:
                sma_val = TA.SMA(df, period=20)
                indicators['sma_20'] = float(sma_val.iloc[-1]) if isinstance(sma_val, pd.Series) else float(sma_val)
            except:
                indicators['sma_20'] = None

            # EMA 20
            try:
                ema_val = TA.EMA(df, period=20)
                indicators['ema_20'] = float(ema_val.iloc[-1]) if isinstance(ema_val, pd.Series) else float(ema_val)
            except:
                indicators['ema_20'] = None

            # MACD
            try:
                macd_val = TA.MACD(df)
                indicators['macd'] = float(macd_val.iloc[-1, 0]) if isinstance(macd_val, pd.DataFrame) else float(macd_val)
            except:
                indicators['macd'] = None

            # Bollinger Bands
            try:
                bb_val = TA.BBANDS(df, period=20)
                if isinstance(bb_val, pd.DataFrame) and not bb_val.empty:
                    indicators['bb_upper'] = float(bb_val.iloc[-1, 0])
                    indicators['bb_lower'] = float(bb_val.iloc[-1, 1])
                else:
                    indicators['bb_upper'] = None
                    indicators['bb_lower'] = None
            except:
                indicators['bb_upper'] = None
                indicators['bb_lower'] = None

            # Volume SMA
            try:
                vol_sma = TA.SMA(df[['volume']], period=20)
                indicators['vol_sma'] = float(vol_sma.iloc[-1]) if isinstance(vol_sma, pd.Series) else float(vol_sma)
            except:
                indicators['vol_sma'] = None

            # Current price and volume
            indicators['price'] = float(df['close'].iloc[-1])
            indicators['volume'] = float(df['volume'].iloc[-1])

            return indicators
        except Exception as e:
            return None

    def calculate_pcs_score(self, data, indicators, config):
        """Calculate PCS score"""
        if indicators is None:
            return 0

        score = 0
        weights = {
            'bullish_momentum': 0.30,
            'trend_strength': 0.25,
            'support_proximity': 0.20,
            'volatility': 0.15,
            'volume': 0.10
        }

        # Bullish Momentum (RSI) - 30%
        rsi = indicators.get('rsi')
        if rsi:
            if 45 <= rsi <= 65:
                momentum_score = 90
            elif 30 <= rsi < 45 or 65 < rsi <= 75:
                momentum_score = 70
            else:
                momentum_score = 30
            score += momentum_score * weights['bullish_momentum']

        # Trend Strength (ADX) - 25%
        adx = indicators.get('adx')
        if adx and adx >= config.get('adx_min', 20):
            trend_score = min(90, 50 + (adx - config.get('adx_min', 20)) * 2)
            score += trend_score * weights['trend_strength']
        else:
            score += 40 * weights['trend_strength']

        # Support Proximity - 20%
        if config.get('ma_support', True):
            price = indicators.get('price')
            sma_20 = indicators.get('sma_20')
            if price and sma_20:
                distance_pct = ((price - sma_20) / sma_20) * 100
                if 0 <= distance_pct <= config.get('ma_tolerance', 3):
                    support_score = 85
                elif -3 <= distance_pct < 0 or distance_pct > 3:
                    support_score = 65
                else:
                    support_score = 40
                score += support_score * weights['support_proximity']

        # Volatility - 15%
        score += 70 * weights['volatility']

        # Volume - 10%
        volume = indicators.get('volume')
        vol_sma = indicators.get('vol_sma')
        if volume and vol_sma and volume >= vol_sma * config.get('min_volume_ratio', 1.2):
            volume_score = 85
            score += volume_score * weights['volume']
        else:
            score += 50 * weights['volume']

        return min(100, max(0, score))

    def scan(self, stocks=None, pattern_strength_min=65):
        """Run the scanner"""
        if stocks is None:
            stocks = COMPLETE_NSE_FO_UNIVERSE

        config = {
            'rsi_min': 30,
            'rsi_max': 75,
            'adx_min': 20,
            'ma_support': True,
            'ma_tolerance': 3,
            'min_volume_ratio': 1.2,
            'pattern_strength_min': pattern_strength_min,
        }

        print(f"Starting PCS scanner on {len(stocks)} stocks...")

        self.results = []
        self.failed_stocks = []

        for i, symbol in enumerate(stocks, 1):
            try:
                symbol_clean = symbol.replace('.NS', '')
                print(f"[{i:3d}/{len(stocks)}] Analyzing {symbol_clean:12s}...", end='\r')

                data = self.fetch_stock_data(symbol)
                if data is None or data.empty:
                    self.failed_stocks.append((symbol_clean, "No data"))
                    continue

                indicators = self.calculate_indicators(data)
                if indicators is None:
                    self.failed_stocks.append((symbol_clean, "Indicator error"))
                    continue

                pcs_score = self.calculate_pcs_score(data, indicators, config)

                if pcs_score >= pattern_strength_min:
                    result = {
                        'symbol': symbol,
                        'symbol_clean': symbol_clean,
                        'pcs_score': pcs_score,
                        'price': indicators.get('price'),
                        'rsi': indicators.get('rsi'),
                        'adx': indicators.get('adx'),
                    }
                    self.results.append(result)
                    print(f"✓ {symbol_clean:12s}: {pcs_score:5.0f}     ")

            except Exception as e:
                self.failed_stocks.append((symbol, str(e)[:30]))
                continue

        print(f"\n✅ Scan complete. Found {len(self.results)} qualifying stocks.")
        return self.results

    def format_message(self):
        """Format results for Telegram"""
        if not self.results:
            return "❌ No stocks meeting the filter criteria found."

        ist = pytz.timezone('Asia/Kolkata')
        current_time = datetime.now(ist)

        sorted_results = sorted(self.results, key=lambda x: x.get('pcs_score', 0), reverse=True)

        message = f"""
📊 <b>NSE F&O PCS Scanner Results</b>
🕐 <b>Time:</b> {current_time.strftime('%Y-%m-%d %H:%M IST')}
✨ <b>Stocks Found:</b> {len(sorted_results)}
⚠️  <b>Failed:</b> {len(self.failed_stocks)}

"""

        for i, result in enumerate(sorted_results[:20], 1):
            symbol = result['symbol_clean']
            score = result.get('pcs_score', 0)
            price = result.get('price', 0)
            rsi = result.get('rsi')

            rsi_str = f"{rsi:.0f}" if rsi else "N/A"
            message += f"{i:2d}. <b>{symbol:12s}</b> | PCS: {score:5.0f} | RSI: {rsi_str:>3s} | ₹{price:.2f}\n"

        if len(sorted_results) > 20:
            message += f"\n... and {len(sorted_results) - 20} more stocks\n"

        message += """
<b>Settings:</b> RSI 30-75 | ADX 20+ | Volume 1.2x | MA Support 3%

"""
        return message


def main():
    """Main execution"""
    print(__doc__)

    # Initialize notifier
    notifier = TelegramNotifier()

    if not notifier.enabled:
        print("\n⚠️  WARNING: Telegram credentials not configured!")
        print("Set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN='your_token'")
        print("  export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\nRunning in display-only mode...\n")

    try:
        # Run scanner
        scanner = NSEPCSScanner()
        scanner.scan()

        # Format message
        message = scanner.format_message()

        # Send or display results
        if notifier.enabled:
            print("📤 Sending results to Telegram...")
            if notifier.send(message):
                print("✅ Message sent successfully!")
                return 0
            else:
                print("❌ Failed to send message")
                return 1
        else:
            print("📋 SCANNER RESULTS:")
            print("="*60)
            print(message)
            print("="*60)
            return 0

    except KeyboardInterrupt:
        print("\n⚠️  Scanner interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
