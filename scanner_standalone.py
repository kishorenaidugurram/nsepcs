#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner - No Streamlit or TA library required
Implements technical indicators using pandas/numpy directly
"""

import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import os
import warnings

warnings.filterwarnings('ignore')

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

class TechnicalIndicators:
    """Calculate technical indicators without TA library"""

    @staticmethod
    def rsi(prices, period=14):
        """Relative Strength Index"""
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = np.zeros_like(prices, dtype=float)
        rsi[:period] = 100. - 100. / (1. + rs)

        for i in range(period, len(prices)):
            delta = deltas[i-1]
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

    @staticmethod
    def sma(prices, period=20):
        """Simple Moving Average"""
        return pd.Series(prices).rolling(window=period).mean().values

    @staticmethod
    def ema(prices, period=20):
        """Exponential Moving Average"""
        return pd.Series(prices).ewm(span=period).mean().values

    @staticmethod
    def adx(high, low, close, period=14):
        """Average Directional Index"""
        plus_dm = np.zeros(len(high))
        minus_dm = np.zeros(len(high))

        for i in range(1, len(high)):
            up = high[i] - high[i-1]
            down = low[i-1] - low[i]

            if up > down and up > 0:
                plus_dm[i] = up
            if down > up and down > 0:
                minus_dm[i] = down

        tr = np.zeros(len(high))
        for i in range(1, len(high)):
            tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))

        atr = pd.Series(tr).rolling(window=period).mean().values
        plus_di = 100 * pd.Series(plus_dm).rolling(window=period).mean().values / (atr + 1e-10)
        minus_di = 100 * pd.Series(minus_dm).rolling(window=period).mean().values / (atr + 1e-10)

        di_diff = np.abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = 100 * di_diff / (di_sum + 1e-10)
        adx = pd.Series(dx).rolling(window=period).mean().values

        return adx

class SimpleScanner:
    """Simple stock scanner using technical indicators"""

    def __init__(self):
        self.cache = {}

    def get_stock_data(self, symbol, period="3mo"):
        """Fetch and calculate indicators for a stock"""
        try:
            data = yf.download(symbol, period=period, progress=False, threads=False)

            if data.empty or len(data) < 30:
                return None

            # Calculate indicators
            data['RSI'] = TechnicalIndicators.rsi(data['Close'].values, period=14)
            data['SMA_20'] = TechnicalIndicators.sma(data['Close'].values, period=20)
            data['EMA_20'] = TechnicalIndicators.ema(data['Close'].values, period=20)
            data['ADX'] = TechnicalIndicators.adx(
                data['High'].values,
                data['Low'].values,
                data['Close'].values,
                period=14
            )

            # Volume
            data['Volume_SMA'] = pd.Series(data['Volume']).rolling(window=20).mean().values

            return data

        except Exception as e:
            return None

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if current day volume is above average"""
        try:
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume_SMA'].iloc[-1]
            ratio = current_volume / avg_volume if avg_volume > 0 else 0
            return ratio >= min_ratio, ratio
        except:
            return False, 0

    def detect_breakout(self, data, lookback=20, volume_ratio=2.0):
        """Detect current day breakout"""
        try:
            close = data['Close'].values
            high = data['High'].values
            volume = data['Volume'].values

            if len(close) < lookback:
                return False

            # Last 20 days high
            recent_high = np.max(high[-lookback:-1])
            current_close = close[-1]
            current_volume = volume[-1]

            # Check volume
            avg_volume = np.mean(volume[-lookback:-1])
            vol_ratio = current_volume / avg_volume if avg_volume > 0 else 0

            # Breakout detected
            breakout = (current_close > recent_high * 1.002) and (vol_ratio >= volume_ratio * 0.8)

            return breakout

        except:
            return False

    def detect_patterns(self, data, symbol, config):
        """Detect simple chart patterns"""
        patterns = []

        try:
            close = data['Close'].values
            high = data['High'].values
            low = data['Low'].values
            rsi = data['RSI'].values
            adx = data['ADX'].values

            current_price = close[-1]
            current_rsi = rsi[-1]
            current_adx = adx[-1]

            # Basic filter checks
            if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
                return []

            if current_adx < config['adx_min']:
                return []

            # Check volume
            volume_ok, volume_ratio = self.check_volume_criteria(data, config['min_volume_ratio'])
            if not volume_ok:
                return []

            # Breakout pattern
            if config.get('pattern_filters', {}).get('current_day_breakout', True):
                if self.detect_breakout(data, config.get('lookback_days', 20), config.get('volume_breakout_ratio', 2.0)):
                    patterns.append({
                        'name': 'Breakout',
                        'strength': 75,
                        'type': 'current_day_breakout'
                    })

            # Double Bottom (simplified)
            if len(close) >= 30 and config.get('pattern_filters', {}).get('double_bottom', True):
                recent_low1 = np.min(low[-20:-10])
                recent_low2 = np.min(low[-10:])
                if abs(recent_low1 - recent_low2) / recent_low2 < 0.02:  # Within 2%
                    if current_price > (recent_low1 + recent_low2) / 2:
                        patterns.append({
                            'name': 'Double Bottom',
                            'strength': 70,
                            'type': 'double_bottom'
                        })

            # Cup and Handle (simplified)
            if len(close) >= 40 and config.get('pattern_filters', {}).get('cup_and_handle', True):
                cup_low = np.min(low[-30:-15])
                handle_high = np.max(high[-15:-5])
                current_level = close[-1]
                if cup_low < handle_high < current_level:
                    patterns.append({
                        'name': 'Cup & Handle',
                        'strength': 72,
                        'type': 'cup_and_handle'
                    })

        except Exception as e:
            pass

        # Filter by minimum strength
        return [p for p in patterns if p['strength'] >= config.get('pattern_strength_min', 65)]

def send_to_telegram(message: str) -> bool:
    """Send message to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def format_results(results, count=20):
    """Format results for Telegram"""
    if not results:
        return "No stocks met the filter criteria today."

    sorted_results = sorted(results, key=lambda x: x.get('strength', 0), reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    timestamp = datetime.now(ist).strftime('%d-%b-%Y %H:%M IST')

    msg = f"<b>NSE F&O Scan Results</b>\n"
    msg += f"<i>{timestamp}</i>\n"
    msg += f"📊 Stocks Found: <b>{len(sorted_results)}</b>\n"
    msg += "─" * 40 + "\n\n"

    for idx, r in enumerate(sorted_results[:count], 1):
        symbol = r['symbol'].replace('.NS', '')
        price = r.get('price', 'N/A')
        patterns = r.get('pattern_names', ['N/A'])
        msg += f"{idx}. <b>{symbol}</b> @ ₹{price:.2f}\n"
        msg += f"   📈 {', '.join(patterns[:2])}\n"

    if len(sorted_results) > count:
        msg += f"\n... and {len(sorted_results) - count} more"

    msg += f"\n\n⚠️  <i>For info only. Not financial advice.</i>"

    return msg

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("NSE F&O STOCK SCANNER - TELEGRAM MODE")
    print("="*60 + "\n")

    # Configuration
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE,
        'rsi_min': 30,
        'rsi_max': 75,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'EMA',
        'ma_tolerance': 3,
        'min_volume_ratio': 1.2,
        'volume_breakout_ratio': 2.0,
        'lookback_days': 20,
        'pattern_strength_min': 65,
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'flat_base': False,
            'double_bottom': True,
            'bump_and_run': False,
            'rectangle_bottom': False,
            'rectangle_top': False,
            'head_shoulders_bottom': False,
            'three_rising_valleys': False,
            'rounding_bottom': False,
            'rounding_top_upside': False,
            'inverted_scallop': False,
        },
    }

    scanner = SimpleScanner()
    results = []

    print(f"📊 Scanning {len(config['stocks_to_scan'])} stocks...")
    print("─" * 60)

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            if i % 25 == 0:
                pct = 100 * i // len(config['stocks_to_scan'])
                print(f"⏳ Progress: {i}/{len(config['stocks_to_scan'])} ({pct}%)")

            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or data.empty:
                continue

            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                continue

            current_price = data['Close'].iloc[-1]
            avg_strength = np.mean([p['strength'] for p in patterns])

            results.append({
                'symbol': symbol,
                'price': current_price,
                'patterns': patterns,
                'pattern_names': [p['name'] for p in patterns],
                'strength': avg_strength,
            })

            print(f"✓ {symbol.replace('.NS', '')}: {len(patterns)} pattern(s)")

        except Exception as e:
            pass

    print("\n" + "─" * 60)
    print(f"✅ Scan complete: {len(results)} stocks found")

    # Format and display message
    message = format_results(results, count=20)
    print("\n📱 Message to send:\n")
    print(message)
    print("\n" + "="*60)

    # Send to Telegram
    send_to_telegram(message)

    # Save results
    with open('/tmp/scan_results.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat(),
            'total_stocks': len(results),
            'stocks': [
                {
                    'symbol': r['symbol'].replace('.NS', ''),
                    'price': float(r['price']),
                    'patterns': r['pattern_names'],
                    'strength': float(r['strength']),
                }
                for r in sorted(results, key=lambda x: x['strength'], reverse=True)[:50]
            ]
        }, f, indent=2)

    print(f"\n💾 Results saved to: /tmp/scan_results.json")
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
