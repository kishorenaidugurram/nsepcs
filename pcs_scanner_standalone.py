#!/usr/bin/env python3
"""
Standalone PCS Scanner - Simplified Version
Runs NSE F&O PCS analysis without external TA library dependencies
Sends results to Telegram
"""

import os
import json
import asyncio
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

# Import Telegram bot
from telegram import Bot
from telegram.error import TelegramError

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# F&O Universe
NIFTY_50 = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
    'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TECHM.NS', 'ULTRACEMCO.NS',
    'SUNPHARMA.NS', 'TITAN.NS', 'COALINDIA.NS', 'BAJFINANCE.NS', 'HCLTECH.NS',
    'JSWSTEEL.NS', 'INDUSINDBK.NS', 'BRITANNIA.NS', 'CIPLA.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HEROMOTOCO.NS', 'HINDALCO.NS', 'TATASTEEL.NS',
    'BPCL.NS', 'M&M.NS', 'BAJAJ-AUTO.NS', 'SHRIRAMFIN.NS', 'ADANIPORTS.NS',
    'APOLLOHOSP.NS', 'BAJAJFINSV.NS', 'DIVISLAB.NS', 'NESTLEIND.NS', 'TRENT.NS',
    'HDFCLIFE.NS', 'SBILIFE.NS', 'LTIM.NS', 'ADANIENT.NS', 'HINDUNILVR.NS'
]

class SimpleIndicators:
    """Calculate technical indicators without external TA library"""

    @staticmethod
    def rsi(data, period=14):
        """Calculate RSI indicator"""
        close = data['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def sma(data, period=20):
        """Calculate Simple Moving Average"""
        return data['Close'].rolling(window=period).mean()

    @staticmethod
    def ema(data, period=20):
        """Calculate Exponential Moving Average"""
        return data['Close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def macd(data, fast=12, slow=26, signal=9):
        """Calculate MACD"""
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(data, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        sma = data['Close'].rolling(window=period).mean()
        std = data['Close'].rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, lower, sma

    @staticmethod
    def adx(data, period=14):
        """Simplified ADX calculation"""
        high = data['High']
        low = data['Low']
        close = data['Close']

        # Calculate TR
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        # Simple trend strength (not true ADX but good approximation)
        trend_strength = ((high - low) / close) * 100
        adx = trend_strength.rolling(window=period).mean()

        return adx

class PCSScanner:
    """Simplified PCS Scanner"""

    def __init__(self):
        self.indicators = SimpleIndicators()

    def fetch_stock_data(self, symbol, period="3mo"):
        """Fetch stock data from yfinance"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period)
            return data if len(data) >= 20 else None
        except:
            return None

    def calculate_indicators(self, data):
        """Calculate all technical indicators"""
        data['RSI'] = self.indicators.rsi(data)
        data['SMA_20'] = self.indicators.sma(data, 20)
        data['SMA_50'] = self.indicators.sma(data, 50)
        data['EMA_20'] = self.indicators.ema(data, 20)

        macd_line, signal, histogram = self.indicators.macd(data)
        data['MACD'] = macd_line
        data['MACD_signal'] = signal
        data['MACD_hist'] = histogram

        upper, lower, middle = self.indicators.bollinger_bands(data)
        data['BB_upper'] = upper
        data['BB_lower'] = lower
        data['BB_middle'] = middle

        data['ADX'] = self.indicators.adx(data)

        return data

    def detect_patterns(self, data, symbol):
        """Detect chart patterns and calculate strength score"""

        if len(data) < 20:
            return None

        try:
            # Get latest data
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]
            current_macd = data['MACD'].iloc[-1]
            current_macd_signal = data['MACD_signal'].iloc[-1]
            sma_20 = data['SMA_20'].iloc[-1]
            sma_50 = data['SMA_50'].iloc[-1]

            # Check if we have valid indicators
            if pd.isna([current_rsi, current_adx, current_macd]).any():
                return None

            patterns = []

            # Pattern 1: Breakout
            lookback_data = data.iloc[-21:-1]
            if len(lookback_data) >= 20:
                resistance = lookback_data['High'].max()
                support = lookback_data['Low'].min()

                # Check for breakout
                if current_price > resistance * 1.005:  # 0.5% above resistance
                    strength = self._calculate_breakout_strength(
                        data, current_price, resistance, support
                    )
                    if strength >= 50:
                        patterns.append({
                            'type': 'Breakout',
                            'strength': strength,
                            'details': f'Price: ₹{current_price:.2f}, Resistance: ₹{resistance:.2f}'
                        })

            # Pattern 2: Support + Bullish Indicators
            if (current_price > sma_20 and
                current_rsi > 45 and current_rsi < 70 and
                current_adx > 15):
                strength = self._calculate_support_strength(
                    current_price, sma_20, current_rsi, current_adx
                )
                if strength >= 50:
                    patterns.append({
                        'type': 'Support & Bullish',
                        'strength': strength,
                        'details': f'RSI: {current_rsi:.1f}, ADX: {current_adx:.1f}'
                    })

            # Pattern 3: MACD Bullish Crossover
            if current_macd > current_macd_signal and current_macd > 0:
                strength = 60
                if current_adx > 25:
                    strength += 10
                if current_rsi > 50:
                    strength += 5

                patterns.append({
                    'type': 'MACD Bullish',
                    'strength': min(strength, 100),
                    'details': f'MACD positive trend'
                })

            # Pattern 4: Price near support with high volume expectation
            if current_price > sma_50 and current_price < sma_20 * 1.05:
                strength = self._calculate_bounce_strength(
                    current_price, sma_20, sma_50, current_rsi
                )
                if strength >= 50:
                    patterns.append({
                        'type': 'Bounce Setup',
                        'strength': strength,
                        'details': f'Near SMA20 support'
                    })

            return patterns if patterns else None

        except Exception as e:
            print(f"   Error analyzing {symbol}: {str(e)}")
            return None

    def _calculate_breakout_strength(self, data, price, resistance, support):
        """Calculate breakout pattern strength"""
        strength = 50

        # Distance from resistance
        breakout_pct = ((price - resistance) / resistance) * 100
        if breakout_pct >= 1:
            strength += 20
        elif breakout_pct >= 0.5:
            strength += 10

        # Consolidation range quality
        consolidation = ((resistance - support) / support) * 100
        if consolidation < 15:
            strength += 15
        elif consolidation < 20:
            strength += 10

        # Volume confirmation (if available)
        try:
            recent_volume = data['Volume'].iloc[-5:].mean()
            older_volume = data['Volume'].iloc[-20:-5].mean()
            if recent_volume > older_volume * 1.2:
                strength += 10
        except:
            pass

        return min(strength, 100)

    def _calculate_support_strength(self, price, sma_20, rsi, adx):
        """Calculate support and bullish indicators strength"""
        strength = 50

        # Support proximity
        if price > sma_20 * 0.99:  # Very close to SMA
            strength += 15
        elif price > sma_20 * 0.98:
            strength += 10

        # RSI quality
        if rsi > 50 and rsi < 65:
            strength += 15
        elif rsi > 45 and rsi < 70:
            strength += 10

        # ADX strength
        if adx > 25:
            strength += 10
        elif adx > 15:
            strength += 5

        return min(strength, 100)

    def _calculate_bounce_strength(self, price, sma_20, sma_50, rsi):
        """Calculate bounce setup strength"""
        strength = 50

        # Distance from support
        distance_from_sma50 = ((price - sma_50) / sma_50) * 100
        if distance_from_sma50 > 3 and distance_from_sma50 < 8:
            strength += 15
        elif distance_from_sma50 > 2:
            strength += 10

        # RSI oversold bounce
        if rsi < 50 and rsi > 35:
            strength += 15
        elif rsi < 60:
            strength += 10

        return min(strength, 100)

def run_scan(stocks=None, max_stocks=50):
    """Run PCS scan on stocks"""

    if stocks is None:
        stocks = NIFTY_50

    stocks = stocks[:max_stocks]
    scanner = PCSScanner()
    results = []

    print(f"\n{'='*60}")
    print(f"📊 PCS Scanner - Scanning {len(stocks)} Stocks")
    print(f"{'='*60}\n")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(analyze_stock, scanner, symbol): symbol for symbol in stocks}

        completed = 0
        for future in as_completed(futures):
            completed += 1
            symbol = futures[future]
            try:
                result = future.result()
                if result:
                    results.append(result)
                    status = "✅" if result['patterns'] else "⏭️ "
                    print(f"{status} {result['symbol']}: {result.get('patterns', 'No patterns')}")
            except Exception as e:
                print(f"❌ {symbol}: Error")

            if completed % 10 == 0:
                print(f"   [{completed}/{len(stocks)}] Progress...")

    # Sort by strength
    results.sort(key=lambda x: x['best_strength'], reverse=True)

    print(f"\n{'='*60}")
    print(f"✅ Scan Complete: {len(results)} stocks with patterns")
    print(f"{'='*60}\n")

    return results

def analyze_stock(scanner, symbol):
    """Analyze single stock"""
    try:
        data = scanner.fetch_stock_data(symbol, "3mo")
        if data is None:
            return None

        data = scanner.calculate_indicators(data)
        patterns = scanner.detect_patterns(data, symbol)

        if not patterns:
            return None

        # Get best pattern
        best = max(patterns, key=lambda x: x['strength'])

        return {
            'symbol': symbol,
            'patterns': best['type'],
            'best_strength': best['strength'],
            'current_price': float(data['Close'].iloc[-1]),
            'current_rsi': float(data['RSI'].iloc[-1]),
            'current_adx': float(data['ADX'].iloc[-1]),
            'pattern_details': best['details']
        }
    except:
        return None

async def send_to_telegram(results):
    """Send results to Telegram"""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram credentials not configured.")
        print("   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        save_results(results)
        return

    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

        if not results:
            msg = f"🔍 PCS Scan - {timestamp}\n\n❌ No patterns detected"
        else:
            msg = f"✅ PCS Scan Results - {timestamp}\n\n"
            msg += f"📊 Found {len(results)} stocks:\n\n"

            for i, stock in enumerate(results[:10], 1):
                msg += f"{i}. {stock['symbol']}\n"
                msg += f"   {stock['patterns']} (Strength: {stock['best_strength']:.0f}/100)\n"
                msg += f"   Price: ₹{stock['current_price']:.2f} | RSI: {stock['current_rsi']:.1f}\n\n"

            if len(results) > 10:
                msg += f"... +{len(results)-10} more"

        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg)
        print("✅ Results sent to Telegram!")

    except TelegramError as e:
        print(f"❌ Telegram Error: {e}")
        save_results(results)
    except Exception as e:
        print(f"❌ Error: {e}")
        save_results(results)

def save_results(results):
    """Save results to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scan_results_{timestamp}.json"

    data = {
        'timestamp': datetime.now().isoformat(),
        'total_stocks': len(results),
        'stocks': [
            {
                'symbol': s['symbol'],
                'pattern': s['patterns'],
                'strength': s['best_strength'],
                'price': s['current_price']
            }
            for s in results
        ]
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"📁 Results saved: {filename}")

async def main():
    """Main execution"""
    print("\n🎯 NSE F&O PCS Scanner - Automated Mode\n")

    # Run scan
    results = run_scan(stocks=NIFTY_50[:50], max_stocks=50)

    if results:
        print(f"🏆 Top Results:")
        for i, s in enumerate(results[:5], 1):
            print(f"   {i}. {s['symbol']} - {s['patterns']} ({s['best_strength']:.0f}/100)")

    # Send to Telegram
    print(f"\n📤 Sending results...")
    await send_to_telegram(results)

    print(f"\n✅ Done!\n")

if __name__ == '__main__':
    asyncio.run(main())
