#!/usr/bin/env python3
"""
Simplified NSE F&O PCS Analysis - No dependencies on 'ta' package
"""
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import requests
import os
import pytz

# Configuration
DEFAULT_MIN_PCS_SCORE = 60
DEFAULT_MAX_STOCKS = 40
STOCKS_BY_TIER = {
    1: ['RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS', 'SBIN.NS', 'LT.NS', 'ITC.NS'],
    2: ['KOTAKBANK.NS', 'AXISBANK.NS', 'HCLTECH.NS', 'WIPRO.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'BHARTIARTL.NS', 'SUNPHARMA.NS'],
    3: ['BAJFINANCE.NS', 'BAJAJFINSV.NS', 'INDUSINDBK.NS', 'TECHM.NS', 'TITAN.NS', 'NESTLEIND.NS', 'ULTRACEMCO.NS', 'POWERGRID.NS', 'NTPC.NS', 'ONGC.NS', 'COALINDIA.NS', 'JSWSTEEL.NS', 'TATASTEEL.NS', 'HINDALCO.NS']
}

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    try:
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs)

        rsis = [rsi]
        for i in range(period, len(deltas)):
            if deltas[i] >= 0:
                up = (up * (period - 1) + deltas[i]) / period
                down = (down * (period - 1)) / period
            else:
                up = (up * (period - 1)) / period
                down = (down * (period - 1) - deltas[i]) / period
            rs = up / down if down != 0 else 0
            rsi = 100.0 - 100.0 / (1.0 + rs)
            rsis.append(rsi)

        return rsis[-1] if rsis else 50
    except:
        return 50

def calculate_sma(prices, period=20):
    """Calculate Simple Moving Average"""
    try:
        return np.mean(prices[-period:]) if len(prices) >= period else prices[-1]
    except:
        return prices[-1]

def calculate_ema(prices, period=20):
    """Calculate Exponential Moving Average"""
    try:
        if len(prices) < period:
            return prices[-1]
        k = 2 / (period + 1)
        ema = prices[0]
        for i in range(1, len(prices)):
            ema = prices[i] * k + ema * (1 - k)
        return ema
    except:
        return prices[-1]

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """Calculate MACD"""
    try:
        ema_fast = calculate_ema(prices, fast)
        ema_slow = calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        return macd, 0  # Return simplified MACD
    except:
        return 0, 0

def calculate_volatility(returns, period=252):
    """Calculate annualized volatility"""
    try:
        return np.std(returns) * np.sqrt(period) * 100
    except:
        return 20

def get_stock_data(symbol, period="3mo"):
    """Fetch stock data using yfinance"""
    try:
        print(f"  📥 Fetching data for {symbol}...", end='')
        data = yf.download(symbol, period=period, progress=False)
        if data is None or len(data) < 20:
            print(" ❌")
            return None
        print(" ✓")
        return data
    except Exception as e:
        print(f" ❌ ({str(e)[:30]})")
        return None

def analyze_stock(symbol, data):
    """Analyze single stock for PCS score"""
    try:
        if data is None or len(data) < 20:
            return None

        # Current data
        current_price = data['Close'].iloc[-1]
        current_volume = data['Volume'].iloc[-1]
        prices = data['Close'].values

        # Calculate indicators
        rsi = calculate_rsi(prices)
        sma_20 = calculate_sma(prices, 20)
        sma_50 = calculate_sma(prices, 50)
        ema_20 = calculate_ema(prices, 20)
        macd_value, macd_signal = calculate_macd(prices)

        # Volume analysis
        avg_volume_20 = data['Volume'].tail(20).mean()
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1

        # Returns for volatility
        returns = data['Close'].pct_change().dropna().values
        volatility = calculate_volatility(returns) if len(returns) > 0 else 20

        # ============ PCS SCORE CALCULATION ============
        pcs_score = 0
        signals = []

        # 1. MOMENTUM (30%)
        if rsi < 30:
            momentum_score = 30
            signals.append(f"Oversold (RSI {rsi:.1f})")
        elif 30 <= rsi <= 70:
            momentum_score = 20 + (abs(50 - rsi) / 20) * 10
            signals.append(f"Neutral momentum (RSI {rsi:.1f})")
        else:
            momentum_score = 10
            signals.append(f"Overbought (RSI {rsi:.1f})")

        pcs_score += momentum_score * 0.30

        # 2. TREND STRENGTH (25%)
        if current_price > ema_20 > sma_50:
            trend_score = 25
            signals.append("Strong uptrend")
        elif current_price > ema_20:
            trend_score = 20
            signals.append("Bullish trend")
        elif current_price > sma_50:
            trend_score = 15
            signals.append("Above long-term MA")
        else:
            trend_score = 5
            signals.append("Downtrend")

        pcs_score += trend_score * 0.25

        # 3. SUPPORT PROXIMITY (20%)
        distance_from_sma20 = ((current_price - sma_20) / sma_20) * 100
        if abs(distance_from_sma20) <= 5:
            support_score = 20
            signals.append(f"Near SMA20 ({distance_from_sma20:.1f}%)")
        elif abs(distance_from_sma20) <= 10:
            support_score = 15
            signals.append(f"Close to SMA20 ({distance_from_sma20:.1f}%)")
        else:
            support_score = 8
            signals.append(f"Away from SMA20 ({distance_from_sma20:.1f}%)")

        pcs_score += support_score * 0.20

        # 4. VOLUME ANALYSIS (10%)
        if volume_ratio >= 1.5:
            volume_score = 10
            signals.append(f"High volume ({volume_ratio:.1f}x)")
        elif volume_ratio >= 1.0:
            volume_score = 7
            signals.append(f"Avg volume ({volume_ratio:.1f}x)")
        else:
            volume_score = 3
            signals.append(f"Low volume ({volume_ratio:.1f}x)")

        pcs_score += volume_score * 0.10

        # 5. VOLATILITY ASSESSMENT (15%)
        if 15 <= volatility <= 35:
            volatility_score = 15
            signals.append(f"Optimal volatility ({volatility:.1f}%)")
        elif 10 <= volatility < 50:
            volatility_score = 12
            signals.append(f"Good volatility ({volatility:.1f}%)")
        else:
            volatility_score = 8
            signals.append(f"Sub-optimal vol ({volatility:.1f}%)")

        pcs_score += volatility_score * 0.15

        return {
            'symbol': symbol,
            'pcs_score': pcs_score,
            'current_price': current_price,
            'rsi': rsi,
            'sma20': sma_20,
            'volume_ratio': volume_ratio,
            'volatility': volatility,
            'signals': signals,
            'confidence': 'HIGH' if pcs_score >= 75 else 'MEDIUM' if pcs_score >= 60 else 'LOW'
        }

    except Exception as e:
        print(f"    Error analyzing {symbol}: {str(e)}")
        return None

def run_analysis(min_pcs_score=DEFAULT_MIN_PCS_SCORE, max_stocks=DEFAULT_MAX_STOCKS):
    """Run PCS analysis on all stocks"""
    print(f"\n🚀 NSE F&O PCS Analysis")
    print(f"{'='*60}")
    print(f"Min Score: {min_pcs_score} | Max Stocks: {max_stocks}")
    print(f"{'='*60}\n")

    # Get stocks to analyze
    stocks = []
    for tier in [1, 2, 3]:
        stocks.extend(STOCKS_BY_TIER[tier])
    stocks = stocks[:max_stocks]

    results = []
    total = len(stocks)

    for idx, symbol in enumerate(stocks, 1):
        print(f"[{idx:2d}/{total}] {symbol:20s}", end=' ')
        try:
            data = get_stock_data(symbol)
            if data is not None:
                analysis = analyze_stock(symbol, data)
                if analysis and analysis['pcs_score'] >= min_pcs_score:
                    results.append(analysis)
                    print(f"✅ Score: {analysis['pcs_score']:6.1f}")
                elif analysis:
                    print(f"⚠️  Score: {analysis['pcs_score']:6.1f} (Below threshold)")
                else:
                    print("❌ Analysis failed")
            else:
                print("❌ No data")
        except Exception as e:
            print(f"❌ Error: {str(e)[:40]}")

    results.sort(key=lambda x: x['pcs_score'], reverse=True)
    return results

def format_telegram_message(results):
    """Format results for Telegram"""
    if not results:
        return "📉 No stocks meeting the filter criteria found."

    message = "📊 *NSE F&O PCS Scanner Results*\n"
    message += f"_{datetime.now().strftime('%Y-%m-%d %H:%M IST')}_\n\n"
    message += f"✅ Found *{len(results)}* stocks (Score ≥ {DEFAULT_MIN_PCS_SCORE})\n"
    message += "─" * 50 + "\n\n"

    for idx, stock in enumerate(results[:15], 1):
        confidence_emoji = "🟢" if stock['confidence'] == 'HIGH' else "🟡" if stock['confidence'] == 'MEDIUM' else "🔴"
        symbol_clean = stock['symbol'].replace('.NS', '')
        message += f"{idx}. *{symbol_clean}* {confidence_emoji}\n"
        message += f"   Score: *{stock['pcs_score']:.1f}* | Price: ₹{stock['current_price']:.2f}\n"
        message += f"   RSI: {stock['rsi']:.1f} | Vol: {stock['volume_ratio']:.1f}x\n"
        if stock['signals']:
            message += f"   📌 {stock['signals'][0]}\n"
        message += "\n"

    if len(results) > 15:
        message += f"...and {len(results) - 15} more stocks"

    return message

def send_to_telegram(message):
    """Send message to Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        print("\n⚠️  Telegram credentials not configured")
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ Sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {str(e)}")
        return False

def save_to_csv(results):
    """Save results to CSV"""
    if not results:
        return

    filename = '/tmp/claude-0/-home-user-nsepcs/fdb7acda-1d8c-5ba5-ac99-c24f3388dbba/scratchpad/pcs_results.csv'
    df = pd.DataFrame([{
        'Symbol': r['symbol'].replace('.NS', ''),
        'PCS Score': f"{r['pcs_score']:.1f}",
        'Price (₹)': f"{r['current_price']:.2f}",
        'RSI': f"{r['rsi']:.1f}",
        'Volume Ratio': f"{r['volume_ratio']:.1f}x",
        'Volatility': f"{r['volatility']:.1f}%",
        'Confidence': r['confidence'],
        'Key Signal': r['signals'][0] if r['signals'] else 'N/A'
    } for r in results])

    df.to_csv(filename, index=False)
    print(f"\n✅ Results saved: {filename}")
    return df

if __name__ == "__main__":
    try:
        results = run_analysis(
            min_pcs_score=DEFAULT_MIN_PCS_SCORE,
            max_stocks=DEFAULT_MAX_STOCKS
        )

        if results:
            print(f"\n{'='*60}")
            print(f"✅ ANALYSIS COMPLETE - {len(results)} Stocks Found")
            print(f"{'='*60}")

            # Format message
            message = format_telegram_message(results)

            # Try Telegram
            send_to_telegram(message)

            # Save CSV
            df = save_to_csv(results)
            if df is not None:
                print("\n" + "="*60)
                print(df.to_string(index=False))
                print("="*60)
        else:
            print(f"\n⚠️  No stocks found above score threshold of {DEFAULT_MIN_PCS_SCORE}")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
