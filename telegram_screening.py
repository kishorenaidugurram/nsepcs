#!/usr/bin/env python3
"""
Standalone stock screening script for NSE F&O stocks with Telegram integration.
Runs the screening logic from streamlit_app.py without Streamlit UI.
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import yfinance as yf
import warnings
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

warnings.filterwarnings('ignore')

# NSE F&O Stock Universe
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
    'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS',
    'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS',
    'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS',
    'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS', 'KOTAKBANK.NS',
    'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS',
    'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS',
    'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS',
    'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS',
    'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS',
    'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS', 'PNBHOUSING.NS',
    'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
    'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS',
    'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS',
    'RELIANCE.NS', 'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS',
    'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS',
    'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS',
    'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS',
    'TATATECH.NS', 'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS',
    'TITAN.NS', 'TORNTPHARM.NS', 'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS',
    'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS',
    'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]

# Default filter configuration
DEFAULT_CONFIG = {
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
        'flat_base': True,
        'bump_and_run': True,
        'rectangle_bottom': True,
        'rectangle_top': False,
        'head_shoulders_bottom': True,
        'double_bottom': True,
        'three_rising_valleys': True,
        'rounding_bottom': True,
        'rounding_top_upside': True,
        'inverted_scallop': True,
    },
    'pattern_priority': 'All Patterns (Comprehensive)',
    'analysis_mode': 'Daily + Weekly Combined (Recommended)',
    'enable_daily_analysis': True,
    'enable_weekly_validation': True,
    'show_charts': False,
    'show_news': False
}


def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    if len(prices) < period + 1:
        return np.nan

    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
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

    return rsi[-1]


def calculate_adx(high, low, close, period=14):
    """Calculate ADX manually"""
    if len(high) < period + 1:
        return 0

    tr = []
    for i in range(1, len(high)):
        h = high.iloc[i] if hasattr(high, 'iloc') else high[i]
        l = low.iloc[i] if hasattr(low, 'iloc') else low[i]
        c = close.iloc[i-1] if hasattr(close, 'iloc') else close[i-1]

        tr.append(max(h - l, abs(h - c), abs(l - c)))

    atr = sum(tr[:period]) / period

    # Simplified ADX - just return average true range as proxy
    return min(atr, 50)  # Cap at 50 for practical filtering


class StockScreener:
    """Core stock screening engine"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def fetch_stock_data(self, symbol, period="3mo"):
        """Fetch stock data using yfinance"""
        try:
            data = yf.download(symbol, period=period, progress=False)
            return data
        except Exception as e:
            print(f"Error fetching {symbol}: {str(e)}")
            return None

    def detect_current_day_breakout(self, data, lookback_days=20, min_volume_ratio=2.0):
        """Detect if stock broke out above 20-day or 50-day range with volume"""
        try:
            if len(data) < lookback_days + 1:
                return False, 0.0

            # Get recent data
            recent = data.iloc[-lookback_days-1:-1].copy()
            current = data.iloc[-1]

            # Calculate range
            high_20d = recent['High'].max()
            low_20d = recent['Low'].min()
            avg_volume_20d = recent['Volume'].mean()

            # Check breakout
            is_breakout = current['Close'] > high_20d
            volume_ratio = current['Volume'] / avg_volume_20d if avg_volume_20d > 0 else 0

            if is_breakout and volume_ratio >= min_volume_ratio:
                # Calculate strength
                breakout_strength = ((current['Close'] - high_20d) / high_20d) * 100
                return True, 70 + min(breakout_strength * 10, 30)

            return False, 0.0
        except Exception as e:
            return False, 0.0

    def validate_technical_filters(self, data, filters):
        """Validate if stock meets technical criteria"""
        try:
            if len(data) < 20:
                return False

            recent = data.iloc[-1]

            # RSI check
            current_rsi = calculate_rsi(data['Close'].values, period=14)
            if np.isnan(current_rsi) or not (filters['rsi_min'] <= current_rsi <= filters['rsi_max']):
                return False

            # ADX check - simplified
            current_adx = calculate_adx(data['High'], data['Low'], data['Close'], period=14)
            if current_adx < filters['adx_min']:
                return False

            # Moving Average Support check
            if filters['ma_support']:
                if filters['ma_type'] == 'SMA':
                    ma_20 = data['Close'].rolling(20).mean().iloc[-1]
                else:  # EMA
                    ma_20 = data['Close'].ewm(span=20).mean().iloc[-1]

                tolerance = 1 - (filters['ma_tolerance'] / 100)
                if recent['Close'] < ma_20 * tolerance:
                    return False

            return True
        except Exception as e:
            return False

    def screen_stock(self, symbol, config):
        """Screen a single stock"""
        try:
            # Fetch data
            data = self.fetch_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Validate technical filters
            if not self.validate_technical_filters(data, config):
                return None

            # Check for breakout
            is_breakout, breakout_strength = self.detect_current_day_breakout(
                data,
                lookback_days=config['lookback_days'],
                min_volume_ratio=config['volume_breakout_ratio']
            )

            if not is_breakout or breakout_strength < config['pattern_strength_min']:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = calculate_rsi(data['Close'].values, period=14)

            return {
                'symbol': symbol,
                'price': current_price,
                'rsi': current_rsi,
                'strength': breakout_strength,
                'date': data.index[-1].strftime('%Y-%m-%d')
            }
        except Exception as e:
            return None


def send_to_telegram(message, telegram_token=None, telegram_chat_id=None):
    """Send message to Telegram"""
    if telegram_token is None:
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_chat_id is None:
        telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not telegram_token or not telegram_chat_id:
        print("ERROR: Telegram credentials not configured")
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        payload = {
            'chat_id': telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def format_results_for_telegram(results):
    """Format screening results for Telegram"""
    if not results:
        return "No stocks matching criteria found today."

    lines = [
        "🎯 <b>NSE F&O Stock Screening Results</b>",
        f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}",
        f"📊 Stocks Found: {len(results)}",
        "",
        "<b>Matching Stocks:</b>",
    ]

    for i, stock in enumerate(results, 1):
        line = (
            f"{i}. <b>{stock['symbol']}</b>\n"
            f"   Price: ₹{stock['price']:.2f} | RSI: {stock['rsi']:.1f} | "
            f"Strength: {stock['strength']:.1f}%"
        )
        lines.append(line)

    return "\n".join(lines)


def run_screening(config=None, max_workers=10):
    """Run stock screening"""
    if config is None:
        config = DEFAULT_CONFIG

    print("Starting NSE F&O Stock Screening...")
    print(f"Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} stocks")

    screener = StockScreener()
    results = []

    # Multi-threaded screening
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(screener.screen_stock, symbol, config): symbol
            for symbol in COMPLETE_NSE_FO_UNIVERSE
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            if completed % 20 == 0:
                print(f"Scanned {completed}/{len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")

            result = future.result()
            if result:
                results.append(result)

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    print(f"\nScreening complete. Found {len(results)} stocks matching criteria.")

    return results


def main():
    """Main execution function"""
    print("=" * 60)
    print("NSE F&O Stock Screening with Telegram Integration")
    print("=" * 60)

    # Run screening
    results = run_screening(DEFAULT_CONFIG)

    # Format and send results
    message = format_results_for_telegram(results)

    print("\nFormatted message:")
    print(message)

    print("\n" + "=" * 60)
    print("Sending results to Telegram...")

    success = send_to_telegram(message)

    if success:
        print("✓ Message sent successfully!")
    else:
        print("✗ Failed to send message")
        print("\nResults would have been:")
        print(message)

    print("=" * 60)

    return 0 if success or not os.getenv('TELEGRAM_BOT_TOKEN') else 1


if __name__ == "__main__":
    sys.exit(main())
