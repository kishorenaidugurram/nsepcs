#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner - Independent of Streamlit
Runs pattern detection and sends results to Telegram
"""

import os
import sys
import json
from datetime import datetime
import traceback

# Core imports
import pandas as pd
import numpy as np
import yfinance as yf
import ta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Telegram
try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    TelegramError = Exception
    Bot = None


# NSE F&O Universe
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
    'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS',
    'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS',
    'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS', 'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS',
    'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS',
    'PIIND.NS', 'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS',
    'PIDILITIND.NS', 'PPLPHARMA.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS', 'PREMIERENE.NS',
    'PRESTIGE.NS', 'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS', 'SBICARD.NS',
    'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS', 'MOTHERSON.NS', 'SHRIRAMFIN.NS',
    'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS', 'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS',
    'SUPREMEIND.NS', 'SUZLON.NS', 'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS',
    'TCS.NS', 'TATAELXSI.NS', 'TMPV.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS',
    'TECHM.NS', 'FEDERALBNK.NS', 'INDHOTEL.NS', 'PHOENIXLTD.NS', 'TITAN.NS', 'TORNTPHARM.NS',
    'TORNTPOWER.NS', 'TRENT.NS', 'TIINDIA.NS', 'UNOMINDA.NS', 'UPL.NS', 'ULTRACEMCO.NS',
    'UNIONBANK.NS', 'UNITDSPR.NS', 'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WAAREEENER.NS',
    'WIPRO.NS', 'YESBANK.NS', 'ZYDUSLIFE.NS'
]


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate technical indicators
        data['RSI'] = ta.momentum.RSIIndicator(data['Close']).rsi()
        data['SMA_20'] = ta.trend.SMAIndicator(data['Close'], window=20).sma_indicator()
        data['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
        data['ADX'] = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close']).adx()
        data['MACD'] = ta.trend.MACD(data['Close']).macd()
        data['Volume_Ratio'] = data['Volume'] / data['Volume'].rolling(20).mean()

        return data
    except Exception as e:
        return None


def check_volume_criteria(data, min_ratio=1.0):
    """Check if volume meets criteria"""
    if len(data) < 21:
        return False, 0

    current_volume = data['Volume'].iloc[-1]
    avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

    volume_ratio = current_volume / avg_20_volume
    return volume_ratio >= min_ratio, volume_ratio


def detect_breakout_pattern(data, lookback_days=20):
    """Detect if stock is in breakout pattern"""
    if len(data) < lookback_days + 2:
        return False, 0

    current_day = data.iloc[-1]
    lookback_data = data.iloc[-(lookback_days + 1):-1]

    resistance = lookback_data['High'].max()
    support = lookback_data['Low'].min()

    current_close = current_day['Close']
    current_high = current_day['High']
    current_volume = current_day['Volume']

    # Breakout conditions
    price_breakout = current_close > resistance * 1.005
    volume_breakout = current_volume > lookback_data['Volume'].mean() * 1.5

    consolidation_range = ((resistance - support) / support) * 100
    tight_consolidation = consolidation_range < 15

    if not (price_breakout and volume_breakout and tight_consolidation):
        return False, 0

    # Calculate strength
    strength = 0

    breakout_pct = ((current_close - resistance) / resistance) * 100
    if breakout_pct >= 2:
        strength += 35
    elif breakout_pct >= 1:
        strength += 20
    else:
        strength += 10

    volume_ratio = current_volume / lookback_data['Volume'].mean()
    if volume_ratio >= 2:
        strength += 30
    elif volume_ratio >= 1.5:
        strength += 15

    if consolidation_range <= 10:
        strength += 25
    else:
        strength += 15

    return True, strength


def detect_cup_handle(data):
    """Detect Cup and Handle pattern"""
    if len(data) < 50:
        return False, 0

    recent = data.iloc[-50:]

    # Cup: Find valley
    valley_idx = recent['Low'].idxmin()
    valley_val = recent['Low'].min()
    valley_pos = recent.index.get_loc(valley_idx)

    # Check if we're near the handle
    current_low = recent['Low'].iloc[-10:].min()
    current_price = recent['Close'].iloc[-1]

    # Cup and Handle criteria
    if valley_pos < 10 or valley_pos > 40:
        return False, 0

    cup_depth = ((recent['High'].max() - valley_val) / valley_val) * 100
    if cup_depth < 5 or cup_depth > 25:
        return False, 0

    # Handle should be shallow
    handle_depth = ((current_low - valley_val) / valley_val) * 100
    if handle_depth > 5:
        return False, 0

    # Breakout from handle
    if current_price > recent['High'].iloc[-30:-10].max():
        strength = 60 + (cup_depth / 30 * 20) + (20 - handle_depth) / 20 * 10
        return True, min(strength, 95)

    return False, 0


def scan_stock(symbol):
    """Scan a single stock"""
    try:
        data = fetch_stock_data(symbol)
        if data is None:
            return None

        # Check volume
        vol_ok, vol_ratio = check_volume_criteria(data, min_ratio=1.0)
        if not vol_ok:
            return None

        # Get indicators
        current_price = data['Close'].iloc[-1]
        rsi = data['RSI'].iloc[-1]
        adx = data['ADX'].iloc[-1]

        # Filter by RSI and ADX
        if not (30 <= rsi <= 85) or adx < 15:
            return None

        patterns = []

        # Check breakout
        breakout, strength = detect_breakout_pattern(data)
        if breakout and strength >= 70:
            patterns.append({
                'type': 'Current Day Breakout',
                'strength': strength,
                'confidence': 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
            })

        # Check cup and handle
        cup_detected, cup_strength = detect_cup_handle(data)
        if cup_detected and cup_strength >= 70:
            patterns.append({
                'type': 'Cup and Handle',
                'strength': cup_strength,
                'confidence': 'HIGH' if cup_strength >= 85 else 'MEDIUM'
            })

        if not patterns:
            return None

        return {
            'symbol': symbol,
            'price': current_price,
            'rsi': rsi,
            'adx': adx,
            'volume_ratio': vol_ratio,
            'patterns': patterns,
            'max_strength': max([p['strength'] for p in patterns])
        }

    except Exception as e:
        return None


class TelegramSender:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.bot = None

        if self.bot_token and self.chat_id:
            try:
                self.bot = Bot(token=self.bot_token)
            except:
                pass

    def send(self, message):
        """Send message to Telegram"""
        if not self.bot:
            print(f"\n📨 Message (no Telegram configured):\n{message}")
            return False

        try:
            self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='HTML')
            return True
        except Exception as e:
            print(f"❌ Telegram error: {e}")
            return False


def main():
    print("=" * 60)
    print("🚀 NSE F&O Stock Scanner - Standalone Edition")
    print("=" * 60)

    # Initialize Telegram
    telegram = TelegramSender()

    if telegram.bot:
        print("✅ Telegram configured and connected")
        telegram.send(f"<b>🚀 Scan Started</b>\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
    else:
        print("⚠️  Telegram not configured (set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)")
        print("   Results will be printed to console only")

    # Scan stocks
    print(f"\n🔍 Scanning {len(COMPLETE_NSE_FO_UNIVERSE[:100])} stocks...")

    results = []
    scanned = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(scan_stock, symbol): symbol for symbol in COMPLETE_NSE_FO_UNIVERSE[:100]}

        for future in as_completed(futures):
            scanned += 1
            result = future.result()

            if result:
                results.append(result)

            if scanned % 10 == 0:
                print(f"  Progress: {scanned}/100 ({len(results)} patterns found)")

    # Sort results
    results.sort(key=lambda x: x['max_strength'], reverse=True)

    # Prepare message
    message = f"<b>📊 Scan Results - {len(results)} Stocks Found</b>\n"
    message += f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>\n\n"

    if results:
        for idx, r in enumerate(results[:20], 1):
            symbol = r['symbol'].replace('.NS', '')
            message += f"<b>{idx}. {symbol}</b> | ₹{r['price']:.2f} | Strength: {r['max_strength']:.0f}%\n"
            message += f"   RSI: {r['rsi']:.1f} | ADX: {r['adx']:.1f} | Vol: {r['volume_ratio']:.2f}x\n"
            message += f"   Patterns: {', '.join([p['type'] for p in r['patterns']])}\n\n"
    else:
        message += "❌ No stocks meeting criteria found"

    # Send results
    print(f"\n✅ Scan Complete! Found {len(results)} stocks")
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60)

    # Send to Telegram
    if telegram.bot:
        # Send in chunks (Telegram has 4096 char limit)
        chunk_size = 3500
        for i in range(0, len(message), chunk_size):
            telegram.send(message[i:i+chunk_size])

        summary = f"\n✅ <b>Scan Complete</b>\nTotal: {len(results)} stocks\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
        telegram.send(summary)

    # Save to file
    output_file = f'/tmp/scan_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
