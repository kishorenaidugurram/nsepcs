#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - Telegram Bot Integration
Runs the screening logic without ta dependency
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import pytz
import requests
import pandas as pd
import yfinance as yf
import numpy as np
import warnings

warnings.filterwarnings('ignore')

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

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

class TelegramNotifier:
    """Send messages to Telegram"""
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured.")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False

    def send_file(self, file_content, filename, caption=""):
        """Send a file to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured.")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

            files = {
                'document': (filename, file_content, 'text/plain')
            }

            data = {
                'chat_id': self.chat_id,
                'caption': caption
            }

            response = requests.post(url, files=files, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ File sent to Telegram: {filename}")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending file to Telegram: {str(e)}")
            return False

class SimpleRSI:
    """Calculate RSI without external dependencies"""
    @staticmethod
    def calculate(closes, period=14):
        """Calculate RSI"""
        if len(closes) < period + 1:
            return [np.nan] * len(closes)

        deltas = np.diff(closes)
        seed = deltas[:period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(closes)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(closes)):
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

class SimpleADX:
    """Calculate ADX without external dependencies"""
    @staticmethod
    def calculate(high, low, close, period=14):
        """Calculate ADX"""
        n = len(close)
        tr = np.zeros(n)
        dm_plus = np.zeros(n)
        dm_minus = np.zeros(n)

        for i in range(1, n):
            h_l = high[i] - low[i]
            h_c = abs(high[i] - close[i - 1])
            l_c = abs(low[i] - close[i - 1])
            tr[i] = max(h_l, h_c, l_c)

            up = high[i] - high[i - 1]
            down = low[i - 1] - low[i]

            if up > 0 and up > down:
                dm_plus[i] = up
            else:
                dm_plus[i] = 0

            if down > 0 and down > up:
                dm_minus[i] = down
            else:
                dm_minus[i] = 0

        atr = pd.Series(tr).rolling(period).mean()
        di_plus = 100 * pd.Series(dm_plus).rolling(period).mean() / atr
        di_minus = 100 * pd.Series(dm_minus).rolling(period).mean() / atr

        di_diff = abs(di_plus - di_minus)
        di_sum = di_plus + di_minus
        dx = 100 * di_diff / di_sum.replace(0, np.nan)
        adx = dx.rolling(period).mean()

        return adx.values

def get_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        if len(data) < 20:
            return None
        return data
    except:
        return None

def calculate_indicators(data):
    """Calculate technical indicators"""
    if data is None or len(data) < 20:
        return None

    close = data['Close'].values
    high = data['High'].values
    low = data['Low'].values

    # Calculate RSI
    rsi = SimpleRSI.calculate(close, period=14)

    # Calculate ADX
    adx = SimpleADX.calculate(high, low, close, period=14)

    # Calculate Simple Moving Averages
    sma_20 = pd.Series(close).rolling(20).mean().values
    sma_50 = pd.Series(close).rolling(50).mean().values

    # Calculate MACD
    ema_12 = pd.Series(close).ewm(span=12, adjust=False).mean().values
    ema_26 = pd.Series(close).ewm(span=26, adjust=False).mean().values
    macd = ema_12 - ema_26
    macd_signal = pd.Series(macd).ewm(span=9, adjust=False).mean().values

    data['RSI'] = rsi
    data['ADX'] = adx
    data['SMA_20'] = sma_20
    data['SMA_50'] = sma_50
    data['MACD'] = macd
    data['MACD_signal'] = macd_signal

    return data

def run_screening(max_stocks=50):
    """Run the PCS screening on NSE F&O stocks"""

    print(f"\n{'='*70}")
    print("🚀 NSE F&O PCS Scanner - Simplified Edition")
    print(f"{'='*70}\n")

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:max_stocks]

    # Default configuration
    rsi_min = 30
    rsi_max = 75
    adx_min = 20
    min_volume_ratio = 1.2
    volume_breakout_ratio = 2.0

    results = []
    total_stocks = len(stocks_to_scan)

    print(f"📊 Scanning {total_stocks} stocks...")
    print(f"⚙️ Filters: RSI {rsi_min}-{rsi_max}, ADX {adx_min}+, Volume {min_volume_ratio}x+")
    print()

    # Progress tracking
    for i, symbol in enumerate(stocks_to_scan, 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            # Get stock data
            data = get_stock_data(symbol, period="3mo")
            if data is None:
                print(f"[{i:3d}/{total_stocks}] ⏭️  {clean_symbol:15s} - No data")
                continue

            # Calculate indicators
            data = calculate_indicators(data)
            if data is None:
                print(f"[{i:3d}/{total_stocks}] ⏭️  {clean_symbol:15s} - Insufficient data")
                continue

            # Get latest values
            current_price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            adx = data['ADX'].iloc[-1]
            volume_ratio = data['Volume'].iloc[-1] / data['Volume'].tail(21).iloc[:-1].mean()

            # Check filters
            if np.isnan(rsi) or np.isnan(adx):
                print(f"[{i:3d}/{total_stocks}] ⏭️  {clean_symbol:15s} - NaN values")
                continue

            rsi_pass = rsi_min <= rsi <= rsi_max
            adx_pass = adx >= adx_min
            volume_pass = volume_ratio >= min_volume_ratio

            if rsi_pass and adx_pass and volume_pass:
                # Detect volume surge for breakout
                has_breakout = volume_ratio >= volume_breakout_ratio

                result = {
                    'symbol': clean_symbol,
                    'current_price': float(current_price),
                    'rsi': float(rsi),
                    'adx': float(adx),
                    'volume_ratio': float(volume_ratio),
                    'has_breakout': has_breakout,
                    'strength': min(100, int((volume_ratio / volume_breakout_ratio) * 50 + (min(100, adx) / 100) * 30 + ((rsi - rsi_min) / (rsi_max - rsi_min)) * 20))
                }

                results.append(result)

                breakout_emoji = "🔥" if has_breakout else "✅"
                print(f"[{i:3d}/{total_stocks}] {breakout_emoji} {clean_symbol:15s} - RSI: {rsi:5.1f} | ADX: {adx:5.1f} | Vol: {volume_ratio:4.1f}x | Score: {result['strength']}%")
            else:
                status = "❌"
                reasons = []
                if not rsi_pass:
                    reasons.append(f"RSI {rsi:.1f}")
                if not adx_pass:
                    reasons.append(f"ADX {adx:.1f}")
                if not volume_pass:
                    reasons.append(f"Vol {volume_ratio:.1f}x")
                print(f"[{i:3d}/{total_stocks}] {status} {clean_symbol:15s} - Failed: {', '.join(reasons)}")

        except Exception as e:
            print(f"[{i:3d}/{total_stocks}] ❌ {clean_symbol:15s} - Error: {str(e)[:40]}")
            continue

        # Rate limiting
        time.sleep(0.3)

    return results

def format_telegram_message(results):
    """Format results into a Telegram message"""
    if not results:
        return "❌ <b>No stocks found</b> meeting the filter criteria today."

    # Sort by strength
    results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""<b>📊 NSE F&O PCS Screener Results</b>
<code>Updated: {current_time}</code>

<b>✅ Stocks Found: {len(results_sorted)}</b>

"""

    for i, result in enumerate(results_sorted[:10], 1):  # Top 10
        symbol = result['symbol']
        strength = result['strength']
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        volume = result['volume_ratio']
        breakout = "🔥 BREAKOUT" if result['has_breakout'] else "✅ Qualified"

        message += f"""<b>{i}. {symbol}</b>
💰 ₹{price:.2f} | 💪 {strength}% | RSI {rsi:.0f} | ADX {adx:.0f} | Vol {volume:.1f}x
{breakout}

"""

    if len(results_sorted) > 10:
        message += f"\n<i>... and {len(results_sorted) - 10} more stocks</i>"

    message += f"""
<b>⚙️ Filter Criteria:</b>
• RSI: 30-75
• ADX: 20+
• Volume: 1.2x+
• Lookback: 20 days"""

    return message

def format_csv_export(results):
    """Export results to CSV format"""
    if not results:
        return ""

    results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)

    csv_data = "Symbol,Price,RSI,ADX,Volume_Ratio,Strength_Score,Has_Breakout\n"

    for result in results_sorted:
        csv_data += f"{result['symbol']},{result['current_price']:.2f},{result['rsi']:.1f},{result['adx']:.1f},"
        csv_data += f"{result['volume_ratio']:.2f},{result['strength']},{'Yes' if result['has_breakout'] else 'No'}\n"

    return csv_data

def main():
    """Main execution"""

    # Get config from environment or use defaults
    max_stocks = int(os.getenv('SCAN_MAX_STOCKS', '50'))

    # Validate Telegram config
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ WARNING: Telegram credentials not configured!")
        print("\nTo set up Telegram notifications:")
        print("1. Create a bot via @BotFather on Telegram")
        print("2. Get your Chat ID")
        print("3. Set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN=your_bot_token")
        print("   export TELEGRAM_CHAT_ID=your_chat_id")
        print("\nContinuing without Telegram...\n")

    try:
        # Run screening
        results = run_screening(max_stocks=max_stocks)

        print(f"\n{'='*70}")
        print(f"✅ Screening Complete! Found {len(results)} qualifying stocks")
        print(f"{'='*70}\n")

        if results:
            # Display top results
            results_sorted = sorted(results, key=lambda x: x['strength'], reverse=True)
            print("🏆 Top Results:")
            print("-" * 80)
            for i, result in enumerate(results_sorted[:10], 1):
                breakout = "🔥" if result['has_breakout'] else "✅"
                print(f"{i}. {result['symbol']:12} | Score: {result['strength']:3}% | "
                      f"RSI: {result['rsi']:5.1f} | ADX: {result['adx']:5.1f} | "
                      f"Vol: {result['volume_ratio']:4.1f}x | {breakout}")
            print("-" * 80)

            # Send to Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                print("\n📤 Sending to Telegram...")
                notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

                # Send summary
                message = format_telegram_message(results)
                notifier.send_message(message)

                # Send CSV
                csv_data = format_csv_export(results)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"nse_pcs_scan_{timestamp}.csv"
                notifier.send_file(csv_data.encode(), filename, "📊 Complete Results")

                print("\n✅ Results sent to Telegram!")
            else:
                print("\n💾 Results not sent to Telegram (not configured)")
        else:
            print("⚠️ No qualifying stocks found today.")
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                msg = "❌ <b>No stocks found</b> meeting filter criteria today."
                notifier.send_message(msg)

    except KeyboardInterrupt:
        print("\n⚠️ Scanning interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                notifier.send_message(f"❌ Scanner error: {str(e)[:100]}")
            except:
                pass
        sys.exit(1)

if __name__ == "__main__":
    main()
