#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Scanner - Runs analysis and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import asyncio
from telegram import Bot
import traceback
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
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

    return rsi

def calculate_adx(high, low, close, period=14):
    """Calculate ADX indicator"""
    tr1 = high - low
    tr2 = np.abs(high - np.roll(close, 1))
    tr3 = np.abs(low - np.roll(close, 1))
    tr = np.maximum(tr1, np.maximum(tr2, tr3))

    plus_dm = np.zeros_like(high)
    minus_dm = np.zeros_like(low)

    for i in range(1, len(high)):
        up = high[i] - high[i-1]
        down = low[i-1] - low[i]

        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down

    tr_sum = tr.rolling(window=period).sum()
    plus_dm_sum = plus_dm.rolling(window=period).sum()
    minus_dm_sum = minus_dm.rolling(window=period).sum()

    plus_di = 100 * plus_dm_sum / tr_sum
    minus_di = 100 * minus_dm_sum / tr_sum

    di_diff = np.abs(plus_di - minus_di)
    di_sum = plus_di + minus_di

    dx = 100 * di_diff / di_sum
    adx = dx.rolling(window=period).mean()

    return adx

class SimpleStockAnalyzer:
    """Simplified stock analyzer without ta library"""

    @staticmethod
    def get_stock_data(symbol, period="3mo"):
        """Fetch stock data from Yahoo Finance"""
        try:
            ticker = symbol.replace('.NS', '')
            data = yf.download(f"{ticker}.NS", period=period, progress=False, threads=False)

            if data is None or len(data) == 0:
                return None

            # Calculate indicators
            data['RSI'] = calculate_rsi(data['Close'].values)
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['EMA_20'] = data['Close'].ewm(span=20).mean()
            data['ADX'] = calculate_adx(
                data['High'].values,
                data['Low'].values,
                data['Close'].rolling(window=14).mean().values
            )

            return data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return None

    @staticmethod
    def analyze_stock(symbol):
        """Analyze a single stock"""
        data = SimpleStockAnalyzer.get_stock_data(symbol)

        if data is None or len(data) < 20:
            return None

        try:
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].tail(20).mean()

            # Basic filter criteria
            rsi_min, rsi_max = 30, 75
            adx_min = 20

            filters_passed = (
                rsi_min <= current_rsi <= rsi_max and
                current_adx >= adx_min and
                current_volume > avg_volume * 1.2
            )

            if not filters_passed:
                return None

            # Calculate strength score (0-100)
            rsi_score = 100 * (current_rsi - rsi_min) / (rsi_max - rsi_min)
            adx_score = min(100, (current_adx - adx_min) / (50 - adx_min) * 100) if current_adx > adx_min else 0
            volume_score = min(100, (current_volume / avg_volume) * 50) if avg_volume > 0 else 0

            strength = (rsi_score * 0.4 + adx_score * 0.4 + volume_score * 0.2)

            return {
                'symbol': symbol,
                'clean_symbol': symbol.replace('.NS', ''),
                'price': current_price,
                'rsi': current_rsi,
                'adx': current_adx,
                'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1.0,
                'strength': max(0, min(100, strength)),
                'data': data
            }
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None

def get_nse_stocks():
    """Get list of NSE F&O stocks to scan"""
    # Top NSE F&O stocks
    stocks = [
        'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK', 'SBIN', 'LT', 'ITC',
        'KOTAKBANK', 'AXISBANK', 'HCLTECH', 'WIPRO', 'MARUTI', 'ASIANPAINT', 'BHARTIARTL', 'SUNPHARMA',
        'TATAMOTORS', 'ADANIENT', 'BAJFINANCE', 'BAJAJFINSV', 'INDUSINDBK', 'TECHM', 'TITAN', 'NESTLEIND',
        'ULTRACEMCO', 'POWERGRID', 'NTPC', 'ONGC', 'COALINDIA', 'JSWSTEEL', 'TATASTEEL', 'HINDALCO',
        'BPCL', 'DRREDDY', 'BRITANNIA', 'CIPLA', 'DIVISLAB', 'HEROMOTOCORP', 'TATACONSUM', 'MARICO',
        'APOLLOHOSP', 'HDFC', 'HDFLFC', 'ICICIPRULI', 'SBICARD', 'SBILIFE', 'ICICISECURITIES', 'UNIONBANK'
    ]
    return [f"{s}.NS" for s in stocks]

def run_analysis():
    """Run the stock analysis"""
    print("=" * 80)
    print("NSE F&O PCS SCREENER - SIMPLIFIED ANALYSIS")
    print("=" * 80)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    print(f"\n📅 Analysis Date: {current_time.strftime('%Y-%m-%d %H:%M IST')}\n")

    stocks = get_nse_stocks()
    print(f"🎯 Scanning {len(stocks)} stocks...\n")

    analyzer = SimpleStockAnalyzer()
    results = []

    for i, symbol in enumerate(stocks):
        clean_name = symbol.replace('.NS', '')
        progress = ((i + 1) / len(stocks)) * 100
        print(f"[{progress:3.0f}%] Analyzing {clean_name:15s}", end='\r')

        analysis = analyzer.analyze_stock(symbol)
        if analysis:
            results.append(analysis)

    print(f"\n✅ Analysis complete!\n")

    # Sort by strength
    results.sort(key=lambda x: x['strength'], reverse=True)

    return results

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "❌ No stocks meeting the filter criteria found today."

    # Group by strength
    high = [r for r in results if r['strength'] >= 70]
    medium = [r for r in results if 50 <= r['strength'] < 70]
    low = [r for r in results if r['strength'] < 50]

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    message = f"🎯 <b>NSE F&O PCS Screener Results</b>\n"
    message += f"📅 {current_time.strftime('%Y-%m-%d %H:%M IST')}\n\n"

    if high:
        message += f"🟢 <b>HIGH STRENGTH ({len(high)})</b>\n"
        for r in high[:10]:
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['price']:.2f} | Strength: {r['strength']:.0f}%\n"
        if len(high) > 10:
            message += f"  ... and {len(high)-10} more\n"
        message += "\n"

    if medium:
        message += f"🟡 <b>MEDIUM STRENGTH ({len(medium)})</b>\n"
        for r in medium[:10]:
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['price']:.2f} | Strength: {r['strength']:.0f}%\n"
        if len(medium) > 10:
            message += f"  ... and {len(medium)-10} more\n"
        message += "\n"

    if low:
        message += f"🔴 <b>LOW STRENGTH ({len(low)})</b>\n"
        for r in low[:5]:
            message += f"  • <b>{r['clean_symbol']}</b> - ₹{r['price']:.2f} | Strength: {r['strength']:.0f}%\n"
        if len(low) > 5:
            message += f"  ... and {len(low)-5} more\n"
        message += "\n"

    message += f"📊 Total Stocks Found: {len(results)}"

    return message

async def send_to_telegram(message, telegram_token, telegram_chat_id):
    """Send message to Telegram"""
    try:
        bot = Bot(token=telegram_token)
        await bot.send_message(
            chat_id=telegram_chat_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")
        return False

def main():
    """Main execution"""
    results = run_analysis()

    # Print summary
    print(f"📊 RESULTS SUMMARY")
    print(f"=" * 80)
    print(f"Total stocks found: {len(results)}\n")

    if results:
        high = sum(1 for r in results if r['strength'] >= 70)
        medium = sum(1 for r in results if 50 <= r['strength'] < 70)
        low = sum(1 for r in results if r['strength'] < 50)

        print(f"🟢 High Strength (70-100%): {high}")
        print(f"🟡 Medium Strength (50-70%): {medium}")
        print(f"🔴 Low Strength (<50%): {low}\n")

        print("📈 TOP 15 STOCKS BY STRENGTH:")
        for i, r in enumerate(results[:15], 1):
            print(f"  {i:2d}. {r['clean_symbol']:12s} - ₹{r['price']:8.2f} - Strength: {r['strength']:5.1f}% - RSI: {r['rsi']:5.1f} - ADX: {r['adx']:5.1f}")

    print(f"\n" + "=" * 80)

    # Save results to JSON
    results_json = []
    for r in results:
        results_json.append({
            'symbol': r['clean_symbol'],
            'price': r['price'],
            'rsi': r['rsi'],
            'adx': r['adx'],
            'volume_ratio': r['volume_ratio'],
            'strength': r['strength'],
            'timestamp': datetime.now(pytz.timezone('Asia/Kolkata')).isoformat()
        })

    output_file = '/home/user/nsepcs/scan_results.json'
    with open(output_file, 'w') as f:
        json.dump(results_json, f, indent=2)
    print(f"\n💾 Results saved to: {output_file}")

    # Save CSV report
    if results:
        df = pd.DataFrame([
            {
                'Symbol': r['clean_symbol'],
                'Price': f"₹{r['price']:.2f}",
                'RSI': f"{r['rsi']:.1f}",
                'ADX': f"{r['adx']:.1f}",
                'Volume Ratio': f"{r['volume_ratio']:.2f}x",
                'Strength': f"{r['strength']:.1f}%"
            }
            for r in results
        ])
        csv_file = '/home/user/nsepcs/scan_results.csv'
        df.to_csv(csv_file, index=False)
        print(f"💾 CSV report saved to: {csv_file}")

    # Format and prepare Telegram message
    message = format_telegram_message(results)

    # Try to send to Telegram
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if telegram_token and telegram_chat_id:
        print(f"\n📤 Sending results to Telegram...")
        success = asyncio.run(send_to_telegram(message, telegram_token, telegram_chat_id))
        if success:
            print("✅ Message sent to Telegram!")
    else:
        print(f"\n⚠️  Telegram credentials not found in environment variables.")
        print(f"   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable Telegram sending.")
        print(f"\n📱 Message to send to Telegram:")
        print(message)

    return results

if __name__ == "__main__":
    try:
        results = main()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
