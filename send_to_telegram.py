#!/usr/bin/env python3
"""
Script to run NSE F&O PCS screening and send results to Telegram
"""

import sys
import os
import json
import time
from datetime import datetime
import requests
import pandas as pd
import yfinance as yf
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# NSE F&O stocks list
NSE_FO_STOCKS = [
    '360ONE.NS', 'ABB.NS', 'APLAPOLLO.NS', 'AUBANK.NS', 'ADANIENSOL.NS',
    'ADANIENT.NS', 'ADANIGREEN.NS', 'ADANIPORTS.NS', 'ABCAPITAL.NS', 'ALKEM.NS',
    'AMBER.NS', 'AMBUJACEM.NS', 'ANGELONE.NS', 'APOLLOHOSP.NS', 'ASHOKLEY.NS',
    'ASIANPAINT.NS', 'ASTRAL.NS', 'AUROPHARMA.NS', 'DMART.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BAJAJHLDNG.NS', 'BANDHANBNK.NS',
    'BANKBARODA.NS', 'BANKINDIA.NS', 'BHARATFORG.NS', 'BHEL.NS', 'BPCL.NS',
    'BHARTIARTL.NS', 'BIOCON.NS', 'BRITANNIA.NS', 'CANBK.NS', 'CHOLAFIN.NS',
    'CIPLA.NS', 'COALINDIA.NS', 'COFORGE.NS', 'COLPAL.NS', 'CAMS.NS',
    'CROMPTON.NS', 'CUMMINSIND.NS', 'DLF.NS', 'DABUR.NS', 'DIVISLAB.NS',
    'DRREDDY.NS', 'EICHERMOT.NS', 'EXIDEIND.NS', 'FORTIS.NS', 'GAIL.NS',
    'GMRAIRPORT.NS', 'GLENMARK.NS', 'GODREJCP.NS', 'GODREJPROP.NS', 'GRASIM.NS',
    'HCLTECH.NS', 'HDFCAMC.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS', 'HEROMOTOCO.NS',
    'HINDALCO.NS', 'HINDPETRO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ICICIGI.NS',
    'ICICIPRULI.NS', 'IDFCFIRSTB.NS', 'IIFL.NS', 'ITC.NS', 'INDIANB.NS',
    'IEX.NS', 'IOC.NS', 'IRCTC.NS', 'IRFC.NS', 'IREDA.NS', 'INDUSTOWER.NS',
    'INDUSINDBK.NS', 'NAUKRI.NS', 'INFY.NS', 'INOXWIND.NS', 'INDIGO.NS',
    'JINDALSTEL.NS', 'JSWENERGY.NS', 'JSWSTEEL.NS', 'JIOFIN.NS', 'JUBLFOOD.NS',
    'KEI.NS', 'KPITTECH.NS', 'KALYANKJIL.NS', 'KAYNES.NS', 'KFINTECH.NS',
    'KOTAKBANK.NS', 'LTIM.NS', 'LT.NS', 'LAURUSLABS.NS', 'LICI.NS',
    'LODHA.NS', 'LUPIN.NS', 'M&M.NS', 'MANAPPURAM.NS', 'MANKIND.NS',
    'MARICO.NS', 'MARUTI.NS', 'MFSL.NS', 'MPHASIS.NS', 'MUTHOOTFIN.NS',
    'NBCC.NS', 'NHPC.NS', 'NMDC.NS', 'NTPC.NS', 'NESTLEIND.NS',
    'OBEROIRLTY.NS', 'ONGC.NS', 'OIL.NS', 'PAYTM.NS', 'OFSS.NS',
    'POLICYBZR.NS', 'PIIND.NS', 'PAGEIND.NS', 'PATANJALI.NS', 'PERSISTENT.NS',
    'PETRONET.NS', 'PIDILITIND.NS', 'POLYCAB.NS', 'PFC.NS', 'POWERGRID.NS',
    'PNB.NS', 'RBLBANK.NS', 'RECLTD.NS', 'RVNL.NS', 'RELIANCE.NS',
    'SBICARD.NS', 'SBILIFE.NS', 'SHREECEM.NS', 'SRF.NS', 'SAMMAANCAP.NS',
    'MOTHERSON.NS', 'SHRIRAMFIN.NS', 'SIEMENS.NS', 'SOLARINDS.NS', 'SONACOMS.NS',
    'SBIN.NS', 'SAIL.NS', 'SUNPHARMA.NS', 'SUPREMEIND.NS', 'SUZLON.NS',
    'SWIGGY.NS', 'SYNGENE.NS', 'TATACONSUM.NS', 'TVSMOTOR.NS', 'TCS.NS',
    'TATAELXSI.NS', 'TATAPOWER.NS', 'TATASTEEL.NS', 'TATATECH.NS', 'TECHM.NS',
    'FEDERALBNK.NS', 'INDHOTEL.NS', 'TITAN.NS', 'TORNTPHARM.NS', 'TRENT.NS',
    'TIINDIA.NS', 'UPL.NS', 'ULTRACEMCO.NS', 'UNIONBANK.NS', 'UNITDSPR.NS',
    'VBL.NS', 'VEDL.NS', 'IDEA.NS', 'VOLTAS.NS', 'WIPRO.NS',
    'YESBANK.NS', 'ZYDUSLIFE.NS'
]


def fetch_stock_data(symbol, period="3mo"):
    """Fetch stock data from Yahoo Finance"""
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period=period, interval="1d")
        return data if len(data) >= 20 else None
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def calculate_rsi(prices, period=14):
    """Calculate RSI manually"""
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period + 1]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    rs = up / down if down != 0 else 0
    rsi = 100. - 100. / (1. + rs)

    return rsi


def calculate_pcs_score(data):
    """Calculate PCS score based on technical indicators"""
    if data is None or len(data) < 20:
        return 0

    try:
        prices = data['Close'].values
        volumes = data['Volume'].values

        current_close = prices[-1]
        current_volume = volumes[-1]

        # RSI calculation
        rsi = calculate_rsi(prices)

        if rsi is None:
            return 0

        # RSI score (30-80 is good, peak at 50-65)
        if 50 <= rsi <= 65:
            rsi_score = 30
        elif 40 <= rsi <= 70:
            rsi_score = 25
        elif 30 <= rsi <= 75:
            rsi_score = 20
        else:
            rsi_score = 0

        # Volume score
        avg_volume = volumes[-20:].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        volume_score = min(10, volume_ratio * 5)

        # Simple momentum score (comparing last 5 days)
        momentum = (prices[-1] - prices[-5]) / prices[-5] * 100
        if momentum > 2:
            trend_score = 25
        elif momentum > 0:
            trend_score = 15
        else:
            trend_score = 5

        # Support proximity score (SMA20)
        sma_20 = prices[-20:].mean()
        if current_close >= sma_20:
            support_score = 20
        else:
            support_score = 10

        # Total score (out of 100)
        total_score = rsi_score + volume_score + trend_score + support_score

        return min(100, total_score)

    except Exception as e:
        print(f"Error calculating score: {e}")
        return 0


def send_telegram_message(message):
    """Send message to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        print(f"   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        print(f"\n📝 Message that would be sent to Telegram:\n{message}\n")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return False


def send_large_telegram_message(title, data_list, max_chars=4000):
    """Send large message in chunks to Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        return False

    messages = []
    current_message = f"<b>{title}</b>\n\n"

    for item in data_list:
        item_text = f"• {item}\n"
        if len(current_message) + len(item_text) > max_chars:
            messages.append(current_message)
            current_message = item_text
        else:
            current_message += item_text

    if current_message:
        messages.append(current_message)

    # Send all messages
    success_count = 0
    for msg in messages:
        if send_telegram_message(msg):
            success_count += 1
        time.sleep(0.5)  # Rate limiting

    return success_count == len(messages)


def run_screening(min_score=55, max_stocks=None, verbose=True):
    """Run the PCS screening on all NSE F&O stocks"""
    results = []
    stocks_to_analyze = NSE_FO_STOCKS if max_stocks is None else NSE_FO_STOCKS[:max_stocks]

    print(f"🔍 Starting analysis of {len(stocks_to_analyze)} stocks...")
    print(f"📊 Minimum score threshold: {min_score}")

    if verbose:
        start_time = time.time()

    # Parallel processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_stock_data, symbol): symbol
            for symbol in stocks_to_analyze
        }

        completed = 0
        for future in as_completed(futures):
            completed += 1
            symbol = futures[future]

            try:
                data = future.result()
                score = calculate_pcs_score(data)

                if score >= min_score:
                    current_price = data['Close'].iloc[-1] if data is not None else 0
                    results.append({
                        'symbol': symbol.replace('.NS', ''),
                        'score': score,
                        'price': current_price
                    })

                if verbose and completed % 10 == 0:
                    print(f"  Progress: {completed}/{len(stocks_to_analyze)}")

            except Exception as e:
                print(f"  Error processing {symbol}: {e}")

    # Sort by score
    results.sort(key=lambda x: x['score'], reverse=True)

    if verbose:
        elapsed = time.time() - start_time
        print(f"\n✅ Analysis complete in {elapsed:.1f} seconds")
        print(f"📈 Found {len(results)} stocks meeting criteria\n")

    return results


def format_results(results):
    """Format results for display"""
    if not results:
        return "No stocks meeting the filter criteria found."

    lines = []
    lines.append(f"<b>📊 NSE F&O PCS Screener Results</b>")
    lines.append(f"<b>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</b>")
    lines.append("")
    lines.append(f"<b>Found {len(results)} qualifying stocks:</b>")
    lines.append("")

    for i, stock in enumerate(results, 1):
        score_emoji = "🟢" if stock['score'] >= 75 else "🟡" if stock['score'] >= 60 else "🔴"
        lines.append(
            f"{i}. {score_emoji} <b>{stock['symbol']}</b> | Score: {stock['score']:.0f}/100 | Price: ₹{stock['price']:.2f}"
        )

    lines.append("")
    lines.append("<i>Green (🟢): High Confidence (75+)</i>")
    lines.append("<i>Yellow (🟡): Medium Confidence (60-74)</i>")
    lines.append("<i>Red (🔴): Low Confidence (<60)</i>")

    return lines


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("🚀 NSE F&O PCS Screener - Telegram Integration")
    print("="*60 + "\n")

    # Configuration
    min_score = 55
    max_stocks = 50  # Limit to first 50 stocks for speed

    print(f"⚙️  Configuration:")
    print(f"   Minimum Score: {min_score}")
    print(f"   Max Stocks to Analyze: {max_stocks}")
    print(f"   Bot Token: {'✅ Set' if TELEGRAM_BOT_TOKEN else '❌ Not Set'}")
    print(f"   Chat ID: {'✅ Set' if TELEGRAM_CHAT_ID else '❌ Not Set'}")
    print()

    # Run screening
    results = run_screening(min_score=min_score, max_stocks=max_stocks, verbose=True)

    # Format results
    formatted = format_results(results)

    # Display results
    print("\n📋 Results:")
    print("\n".join(formatted))

    # Send to Telegram
    print("\n📤 Sending to Telegram...")
    if send_large_telegram_message("📊 NSE F&O PCS Screener Results", formatted):
        print("✅ Message sent successfully!")
    else:
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            print("❌ Failed to send message")
        # Message was already shown in send_telegram_message if credentials missing

    print("\n" + "="*60)
    print(f"📊 Analysis Summary:")
    print(f"   Total Stocks Screened: {max_stocks}")
    print(f"   Qualifying Stocks: {len(results)}")
    print(f"   Success Rate: {len(results)/max_stocks*100:.1f}%")
    print("="*60 + "\n")

    return results


if __name__ == "__main__":
    results = main()
