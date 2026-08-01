#!/usr/bin/env python3
"""
NSE F&O PCS Scanner - Telegram Notification Integration
Scans NSE stocks for patterns matching criteria and sends results to Telegram
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import pytz
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Complete NSE F&O universe
COMPLETE_NSE_FO_UNIVERSE = [
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

class SimplePCSScanner:
    """Simplified PCS scanner without TA dependency"""

    def __init__(self):
        self.ist = pytz.timezone('Asia/Kolkata')

    def get_stock_data(self, symbol, period="3mo"):
        """Get stock data from Yahoo Finance"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period=period, interval="1d")
            if len(data) < 20:
                return None

            # Add basic technical indicators
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['SMA_20'] = data['Close'].rolling(window=20).mean()
            data['SMA_50'] = data['Close'].rolling(window=50).mean()

            return data
        except:
            return None

    def _calculate_rsi(self, prices, period=14):
        """Simple RSI calculation"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def check_volume_criteria(self, data, min_ratio=1.0):
        """Check if current day volume is above average"""
        if len(data) < 21:
            return False, 0, {}

        current_volume = data['Volume'].iloc[-1]
        avg_20_volume = data['Volume'].tail(21).iloc[:-1].mean()

        volume_ratio = current_volume / avg_20_volume

        return volume_ratio >= min_ratio, volume_ratio, {
            'current': current_volume,
            'avg_20': avg_20_volume,
            'ratio': volume_ratio
        }

    def detect_simple_patterns(self, data, config):
        """Detect simple bullish patterns"""
        if len(data) < 20:
            return []

        patterns = []
        close = data['Close']
        high = data['High']
        low = data['Low']
        rsi = data['RSI']
        sma_20 = data['SMA_20']

        # Current price analysis
        current_price = close.iloc[-1]
        current_rsi = rsi.iloc[-1]
        current_high = high.iloc[-1]
        current_low = low.iloc[-1]

        # Basic momentum pattern: Price above SMA20, RSI not overbought
        if current_price > sma_20.iloc[-1] and current_rsi < 70:
            # Check for volume confirmation
            current_vol = data['Volume'].iloc[-1]
            avg_vol = data['Volume'].tail(20).mean()

            if current_vol > avg_vol:
                patterns.append({
                    'type': 'Bullish Momentum',
                    'strength': min(100, 60 + (current_rsi - 40) if current_rsi > 40 else 40),
                    'confidence': 'HIGH' if current_rsi > 50 else 'MEDIUM',
                    'success_rate': 65
                })

        # Range breakout pattern: Today's high above 20-day high
        range_high = high.tail(20).max()
        if current_high > range_high * 1.01:  # 1% above recent high
            patterns.append({
                'type': 'Range Breakout',
                'strength': min(100, 75 + (current_rsi - 50) if current_rsi > 50 else 60),
                'confidence': 'HIGH' if current_rsi > 45 else 'MEDIUM',
                'success_rate': 70
            })

        # Oversold bounce: RSI in oversold, price above support
        if current_rsi < 40 and current_price > low.tail(20).min():
            patterns.append({
                'type': 'Oversold Bounce Setup',
                'strength': min(100, 50 + (40 - current_rsi)),
                'confidence': 'MEDIUM',
                'success_rate': 60
            })

        return patterns


class TelegramSender:
    """Handle Telegram notifications"""

    def __init__(self, bot_token=None, chat_id=None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')

        if not self.bot_token or not self.chat_id:
            raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables are required")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(self, message, parse_mode='HTML'):
        """Send a message to Telegram"""
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_stocks_results(self, results, total_scanned=0):
        """Send scan results to Telegram"""
        if not results:
            message = f"🔍 <b>NSE PCS Scanner</b>\nNo stocks found meeting the filter criteria.\nTotal scanned: {total_scanned}"
            self.send_message(message)
            return

        # Create summary message
        message_parts = []
        message_parts.append(f"🎉 <b>NSE PCS Scanner Results</b>")
        message_parts.append(f"<i>Total Stocks Found: {len(results)}</i>")
        message_parts.append("")

        # Sort by pattern strength
        results_sorted = sorted(results, key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        # Add top results (limit to 10 to avoid message size issues)
        for i, result in enumerate(results_sorted[:10], 1):
            symbol = result['symbol'].replace('.NS', '').replace('^', '')
            price = result['current_price']
            max_strength = max(p['strength'] for p in result['patterns'])
            rsi = result['rsi']
            patterns = ', '.join([p['type'] for p in result['patterns'][:2]])  # First 2 patterns

            confidence = '🟢 HIGH' if max_strength >= 85 else '🟡 MEDIUM' if max_strength >= 70 else '🔴 LOW'

            message_parts.append(
                f"<b>{i}. {symbol}</b> - {confidence}\n"
                f"   Price: ₹{price:.2f} | RSI: {rsi:.1f} | Strength: {max_strength:.0f}%\n"
                f"   Patterns: {patterns}"
            )

        message_parts.append("")
        message_parts.append(f"<i>Generated: {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M IST')}</i>")

        # Send in chunks if message is too long
        full_message = "\n".join(message_parts)

        # Telegram has a 4096 character limit
        if len(full_message) <= 4096:
            self.send_message(full_message)
        else:
            # Send summary first
            summary = f"🎉 <b>NSE PCS Scanner Results</b>\n<i>Found {len(results)} stocks</i>"
            self.send_message(summary)

            # Send in chunks
            chunk_size = 40
            for chunk_num, i in enumerate(range(0, len(results_sorted), chunk_size)):
                chunk = results_sorted[i:i+chunk_size]
                chunk_message = f"<b>Stocks {i+1}-{min(i+chunk_size, len(results_sorted))}</b>\n\n"

                for result in chunk:
                    symbol = result['symbol'].replace('.NS', '').replace('^', '')
                    max_strength = max(p['strength'] for p in result['patterns'])
                    rsi = result['rsi']
                    confidence = '🟢 HIGH' if max_strength >= 85 else '🟡 MEDIUM' if max_strength >= 70 else '🔴 LOW'
                    chunk_message += f"<b>{symbol}</b> {confidence} | {max_strength:.0f}% | RSI:{rsi:.1f}\n"

                self.send_message(chunk_message)

def run_scanner(
    stocks_to_scan=None,
    pattern_strength_min=50,
    rsi_min=30,
    rsi_max=80,
    min_volume_ratio=0.8,
    max_workers=5
):
    """
    Run the PCS scanner on specified stocks

    Args:
        stocks_to_scan: List of stock symbols to scan
        pattern_strength_min: Minimum pattern strength (0-100)
        rsi_min: Minimum RSI value
        rsi_max: Maximum RSI value
        min_volume_ratio: Minimum volume ratio
        max_workers: Number of parallel workers

    Returns:
        List of stocks meeting criteria
    """

    if stocks_to_scan is None:
        # Use top F&O stocks if none specified
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:30]

    scanner = SimplePCSScanner()

    # Configuration dictionary
    config = {
        'rsi_min': rsi_min,
        'rsi_max': rsi_max,
        'pattern_strength_min': pattern_strength_min,
        'min_volume_ratio': min_volume_ratio
    }

    results = []
    total_scanned = 0

    print(f"Starting scan of {len(stocks_to_scan)} stocks...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        for symbol in stocks_to_scan:
            future = executor.submit(_scan_single_stock, scanner, symbol, config)
            futures[future] = symbol

        for i, future in enumerate(as_completed(futures), 1):
            symbol = futures[future]
            total_scanned += 1

            try:
                result = future.result(timeout=30)
                if result:
                    results.append(result)
                    print(f"✓ {symbol} - Found patterns")
                else:
                    print(f"✗ {symbol} - No patterns")
            except Exception as e:
                print(f"✗ {symbol} - Error: {str(e)[:50]}")

            # Progress indicator
            if total_scanned % 5 == 0:
                print(f"Progress: {total_scanned}/{len(stocks_to_scan)}")

    print(f"\nScan complete. Found {len(results)} stocks with patterns.")
    return results, total_scanned

def _scan_single_stock(scanner, symbol, config):
    """Scan a single stock for patterns"""
    try:
        # Get stock data
        data = scanner.get_stock_data(symbol, period="3mo")
        if data is None or len(data) < 20:
            return None

        # Check volume
        volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
            data,
            config['min_volume_ratio']
        )
        if not volume_ok:
            return None

        # Detect patterns
        patterns = scanner.detect_simple_patterns(data, config)
        if not patterns:
            return None

        # Filter by pattern strength
        patterns = [p for p in patterns if p['strength'] >= config['pattern_strength_min']]
        if not patterns:
            return None

        # Get current metrics
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]

        # Filter by RSI range
        if not (config['rsi_min'] <= current_rsi <= config['rsi_max']):
            return None

        return {
            'symbol': symbol,
            'current_price': current_price,
            'volume_ratio': volume_ratio,
            'rsi': current_rsi,
            'patterns': patterns
        }

    except Exception as e:
        return None

def main():
    """Main entry point"""

    # Check for Telegram credentials
    if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('TELEGRAM_CHAT_ID'):
        print("Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables not set")
        print("Set them using: export TELEGRAM_BOT_TOKEN='your_token'")
        print("              : export TELEGRAM_CHAT_ID='your_chat_id'")
        sys.exit(1)

    try:
        # Initialize Telegram sender
        telegram = TelegramSender()

        # Send starting message
        telegram.send_message("🔍 <b>NSE PCS Scanner</b> - Starting scan...")

        # Run scanner with optimized settings for hourly scanning
        results, total_scanned = run_scanner(
            stocks_to_scan=COMPLETE_NSE_FO_UNIVERSE[:30],  # Scan top 30 F&O stocks
            pattern_strength_min=50,  # Moderate quality patterns
            rsi_min=25,
            rsi_max=85,
            min_volume_ratio=0.8,
            max_workers=5
        )

        # Send results to Telegram
        telegram.send_stocks_results(results, total_scanned)

        print(f"Successfully sent {len(results)} results to Telegram")

    except Exception as e:
        print(f"Error: {e}")
        try:
            telegram = TelegramSender()
            telegram.send_message(f"❌ <b>NSE PCS Scanner Error</b>\n{str(e)}")
        except:
            pass
        sys.exit(1)

if __name__ == "__main__":
    main()
