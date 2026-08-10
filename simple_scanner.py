#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - No external TA library dependencies
Runs basic technical analysis and sends results to Telegram
"""

import sys
import os
import json
import requests
from datetime import datetime
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

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

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    deltas = np.diff(prices)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
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

def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data and calculate basic indicators"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")

        if len(data) < 20:
            return None

        # Calculate RSI
        data['RSI'] = calculate_rsi(data['Close'].values, period=14)

        # Calculate simple MAs
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()

        return data
    except:
        return None

def analyze_stock(symbol):
    """Analyze a stock for PCS opportunities"""
    clean_symbol = symbol.replace('.NS', '')

    try:
        data = fetch_stock_data(symbol)
        if data is None or len(data) < 20:
            return None

        # Get latest values
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        current_sma20 = data['SMA_20'].iloc[-1]
        current_sma50 = data['SMA_50'].iloc[-1]

        # Get current day data
        current_volume = data['Volume'].iloc[-1]
        avg_volume_20 = data['Volume'].tail(21).iloc[:-1].mean()
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 0

        # Calculate daily change
        daily_change = ((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100) if len(data) >= 2 else 0

        # Basic scoring
        score = 0
        signals = []

        # RSI analysis
        if 30 <= current_rsi <= 75:
            score += 20
            signals.append(f"Healthy RSI: {current_rsi:.1f}")
        elif current_rsi < 30:
            score += 15
            signals.append(f"Oversold RSI: {current_rsi:.1f}")

        # Moving average analysis
        if current_price > current_sma20 > current_sma50:
            score += 25
            signals.append("Above both MA20 and MA50")
        elif current_price > current_sma20:
            score += 15
            signals.append("Above MA20")
        elif current_price > current_sma50:
            score += 10
            signals.append("Above MA50")

        # Volume analysis
        if volume_ratio >= 1.5:
            score += 20
            signals.append(f"High volume: {volume_ratio:.1f}x")
        elif volume_ratio >= 1.0:
            score += 10
            signals.append(f"Normal volume: {volume_ratio:.1f}x")

        # Trend strength (uptrend check)
        if daily_change > 0:
            score += 10
            signals.append(f"Positive momentum: {daily_change:.2f}%")

        if score >= 40 and len(signals) >= 2:  # Minimum score threshold
            return {
                'symbol': clean_symbol,
                'price': float(current_price),
                'rsi': float(current_rsi),
                'sma20': float(current_sma20),
                'sma50': float(current_sma50),
                'volume_ratio': float(volume_ratio),
                'daily_change': float(daily_change),
                'score': int(score),
                'signals': signals,
                'signal_count': len(signals)
            }

        return None

    except Exception as e:
        return None

def send_to_telegram(message, bot_token=None, chat_id=None):
    """Send message to Telegram"""
    if not bot_token:
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not chat_id:
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("⚠️  Telegram credentials not found in environment variables")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print(f"✅ Telegram message sent successfully")
            return True
        else:
            print(f"❌ Telegram API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        return False

def format_results_for_telegram(results):
    """Format results for Telegram"""
    if not results:
        return "❌ <b>No qualifying stocks found</b>"

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    message = f"📊 <b>NSE F&O PCS Scanner Results</b>\n"
    message += f"⏰ {now}\n"
    message += f"✅ Found <b>{len(results)} stocks</b>\n"
    message += "━" * 45 + "\n\n"

    # Show top 15
    for i, stock in enumerate(results[:15], 1):
        signal_str = " | ".join(stock['signals'][:2])
        message += f"<b>{i}. {stock['symbol']}</b>\n"
        message += f"💰 ₹{stock['price']:.2f} ({stock['daily_change']:+.2f}%) | 📊 RSI:{stock['rsi']:.0f} | Score:{stock['score']}\n"
        message += f"📈 {signal_str}\n\n"

    if len(results) > 15:
        message += f"... and {len(results) - 15} more stocks\n\n"

    message += "━" * 45 + "\n"
    avg_score = sum(r['score'] for r in results) / len(results)
    message += f"📈 Average Score: {avg_score:.0f}\n"
    message += "🔔 Check the detailed web app for complete analysis"

    return message

def main():
    print("\n" + "=" * 70)
    print("NSE F&O PCS SCANNER - AUTOMATED ANALYSIS")
    print("=" * 70)

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:100]  # First 100 stocks

    print(f"\n🚀 Starting scan of {len(stocks_to_scan)} stocks...")
    print("-" * 70)

    results = []

    for i, symbol in enumerate(stocks_to_scan):
        clean_symbol = symbol.replace('.NS', '')
        pct = ((i + 1) / len(stocks_to_scan)) * 100
        print(f"[{pct:5.1f}%] 🔍 {clean_symbol:12s}", end='\r')

        result = analyze_stock(symbol)
        if result:
            results.append(result)

    print(" " * 70)  # Clear progress
    print("\n✅ Scan Complete!")
    print(f"📊 Found {len(results)} qualifying stocks\n")

    if results:
        # Sort and display top 10
        results.sort(key=lambda x: x['score'], reverse=True)

        print("🏆 Top 10 Stocks by Score:")
        print("-" * 70)
        for i, stock in enumerate(results[:10], 1):
            print(f"{i:2d}. {stock['symbol']:12s} | Score: {stock['score']:3d} | "
                  f"Price: ₹{stock['price']:8.2f} | RSI: {stock['rsi']:5.1f} | "
                  f"Volume: {stock['volume_ratio']:.1f}x")

        # Save results to files
        print("\n💾 Saving results...")

        # JSON
        json_file = f"/tmp/nsepcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w') as f:
            json.dump([{k: v for k, v in r.items() if k != 'signals'} for r in results], f, indent=2)
        print(f"   📄 {json_file}")

        # CSV
        csv_file = f"/tmp/nsepcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df = pd.DataFrame([
            {
                'Symbol': r['symbol'],
                'Price': f"₹{r['price']:.2f}",
                'RSI': f"{r['rsi']:.1f}",
                'Volume': f"{r['volume_ratio']:.1f}x",
                'Score': r['score'],
                'Change': f"{r['daily_change']:.2f}%"
            }
            for r in results
        ])
        df.to_csv(csv_file, index=False)
        print(f"   📋 {csv_file}")

        # Send to Telegram
        print("\n📤 Attempting to send to Telegram...")
        telegram_message = format_results_for_telegram(results)

        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        chat_id = os.environ.get('TELEGRAM_CHAT_ID')

        if bot_token and chat_id:
            sent = send_to_telegram(telegram_message, bot_token, chat_id)
            if sent:
                print("✅ Telegram notification sent successfully!")
        else:
            print("\n⚠️  Telegram credentials not set in environment")
            print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
            print("\n📌 Message that would be sent:")
            print(telegram_message)
    else:
        print("❌ No stocks found matching criteria")

if __name__ == "__main__":
    main()
