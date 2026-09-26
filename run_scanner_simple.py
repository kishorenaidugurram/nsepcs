#!/usr/bin/env python3
"""
Simplified standalone stock scanner that sends qualifying stocks to Telegram.
No dependency on the 'ta' library - uses numpy/pandas for technical indicators.
"""

import os
import sys
import json
from datetime import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import numpy as np
import yfinance as yf
import requests
import warnings

warnings.filterwarnings('ignore')

# Complete F&O Stock Universe
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
    'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS', 'IEX.NS', 'IOC.NS',
    'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS', 'INDUSINDBK.NS', 'NAUKRI.NS',
    'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS', 'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS',
    'JIOFIN.NS', 'JUBLFOOD.NS', 'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS',
    'KFINTECH.NS', 'KOTAKBANK.NS', 'LTF.NS', 'LICHSGFIN.NS', 'LTIM.NS', 'LT.NS',
    'LAURUSLABS.NS', 'LICI.NS', 'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS',
    'MANKIND.NS', 'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MAXHEALTH.NS', 'MAZDOCK.NS',
    'MPHASIS.NS', 'MCX.NS', 'MUTHOOTFIN.NS', 'NBCC.NS', 'NHPC.NS', 'NMDC.NS',
    'NTPC.NS', 'NATIONALUM.NS', 'NESTLEIND.NS', 'NUVAMA.NS', 'OBEROIRLTY.NS', 'ONGC.NS',
    'OIL.NS', 'PAYTM.NS', 'OFSS.NS', 'POLICYBZR.NS', 'PGEL.NS', 'PIIND.NS',
    'PNBHOUSING.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS', 'PETRONET.NS', 'PIDILITIND.NS',
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

def calculate_rsi(data, period=14):
    """Calculate RSI using numpy"""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(high, low, close, period=14):
    """Simplified ADX calculation"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    # Simplified DX calculation
    up_move = high.diff()
    down_move = -low.diff()

    pos_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    neg_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

    pos_di = 100 * (pos_dm.rolling(period).mean() / atr)
    neg_di = 100 * (neg_dm.rolling(period).mean() / atr)

    dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
    adx = dx.rolling(period).mean()

    return adx

def send_to_telegram(message, telegram_bot_token, telegram_chat_id):
    """Send message to Telegram chat"""
    if not telegram_bot_token or not telegram_chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"

        # Split message if too long
        max_length = 4000
        if len(message) > max_length:
            messages = [message[i:i+max_length] for i in range(0, len(message), max_length)]
        else:
            messages = [message]

        for msg in messages:
            payload = {
                'chat_id': telegram_chat_id,
                'text': msg,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                return False

        return True
    except Exception as e:
        print(f"Error sending to Telegram: {str(e)}")
        return False

def get_telegram_config():
    """Get Telegram bot token and chat ID"""
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    config_file = os.path.expanduser('~/.telegram_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                token = token or config.get('bot_token')
                chat_id = chat_id or config.get('chat_id')
        except:
            pass

    return token, chat_id

def scan_single_stock(symbol):
    """Scan a single stock for trading signals"""
    try:
        # Download data
        stock = yf.Ticker(symbol)
        data = stock.history(period="3mo", interval="1d")

        if data is None or len(data) < 30:
            return None

        # Calculate technical indicators
        data['RSI'] = calculate_rsi(data['Close'])
        data['SMA_20'] = data['Close'].rolling(20).mean()
        data['ADX'] = calculate_adx(data['High'], data['Low'], data['Close'])

        # Get current day metrics
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_adx = data['ADX'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]

        # Volume check
        avg_volume_20 = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_volume_20

        # Basic filters
        if current_rsi < 30 or current_rsi > 75:
            return None
        if current_adx < 20:
            return None
        if volume_ratio < 1.2:
            return None
        if current_price < data['SMA_20'].iloc[-1]:
            return None

        # Check for breakout (last 20 days high)
        resistance = data['High'].tail(20).max()
        if current_price < resistance * 1.005:
            return None

        # Calculate pattern strength
        strength = 50

        # RSI score
        if 40 <= current_rsi <= 70:
            strength += 15

        # ADX score
        if current_adx >= 25:
            strength += 15

        # Volume score
        if volume_ratio >= 2.0:
            strength += 15

        # Price action score
        daily_change = ((current_price - data['Close'].iloc[-2]) / data['Close'].iloc[-2]) * 100
        if daily_change >= 1.0:
            strength += 10

        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume_ratio': volume_ratio,
            'rsi': current_rsi,
            'adx': current_adx,
            'strength': min(strength, 100),
            'daily_change': daily_change,
        }

    except Exception as e:
        return None

def format_telegram_message(results, limit=30):
    """Format scan results for Telegram"""
    if not results:
        return "❌ No stocks found matching the filter criteria."

    results.sort(key=lambda x: x['strength'], reverse=True)
    results = results[:limit]

    message = "📊 <b>NSE STOCK SCAN RESULTS</b>\n"
    message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"
    message += f"<b>Total Stocks Found:</b> {len(results)}\n"
    message += f"<b>Filter Criteria:</b> Current Day Breakout + Volume Surge\n\n"

    for idx, result in enumerate(results, 1):
        symbol = result['symbol'].replace('.NS', '')
        strength = result['strength']

        if strength >= 85:
            emoji = "🔴"
        elif strength >= 70:
            emoji = "🟠"
        else:
            emoji = "🟡"

        message += f"{idx}. {emoji} <b>{symbol}</b>\n"
        message += f"   Price: ₹{result['current_price']:.2f}\n"
        message += f"   Strength: {strength:.0f}% | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}\n"
        message += f"   Volume: {result['volume_ratio']:.1f}x | Change: {result['daily_change']:.2f}%\n\n"

    message += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    message += "💡 <i>Note: Do your own research before trading.</i>"

    return message

def main():
    """Main function"""
    try:
        telegram_bot_token, telegram_chat_id = get_telegram_config()

        if not telegram_bot_token or not telegram_chat_id:
            print("⚠️ Telegram credentials not configured")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")

        print(f"\n🚀 Scanning {len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")
        print(f"📅 Scan time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

        results = []
        completed = 0

        # Parallel scanning
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(scan_single_stock, symbol): symbol for symbol in COMPLETE_NSE_FO_UNIVERSE}

            for future in as_completed(futures):
                completed += 1
                symbol = futures[future]

                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except:
                    pass

                if completed % 20 == 0:
                    print(f"✓ Processed {completed}/{len(COMPLETE_NSE_FO_UNIVERSE)} stocks...")

        print(f"\n✅ Scan complete! Found {len(results)} stocks matching criteria.\n")

        # Format message
        message = format_telegram_message(results)

        print("="*60)
        print("SCAN RESULTS:")
        print("="*60)
        print(message)
        print("="*60 + "\n")

        # Send to Telegram
        if telegram_bot_token and telegram_chat_id:
            print("📤 Sending to Telegram...")
            if send_to_telegram(message, telegram_bot_token, telegram_chat_id):
                print("✅ Successfully sent to Telegram!")
            else:
                print("❌ Failed to send to Telegram")

        return 0

    except KeyboardInterrupt:
        print("\n⛔ Scan interrupted")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
