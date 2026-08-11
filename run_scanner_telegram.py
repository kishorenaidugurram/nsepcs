#!/usr/bin/env python3
"""
Standalone NSE F&O PCS Scanner - Telegram Bot Integration
Runs the screening logic and sends qualifying stocks to Telegram
"""

import os
import sys
import json
import time
from datetime import datetime
import pytz
import requests
import pandas as pd
import yfinance as yf
import numpy as np
import ta
from io import StringIO
import warnings

warnings.filterwarnings('ignore')

# Import the scanner class from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

class TelegramNotifier:
    """Send messages to Telegram"""
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message, parse_mode="HTML"):
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured. Message: {message[:100]}...")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Message sent to Telegram")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Telegram: {str(e)}")
            return False

    def send_file(self, file_content, filename, caption=""):
        """Send a file to Telegram"""
        if not self.bot_token or not self.chat_id:
            print(f"⚠️ Telegram not configured. File: {filename}")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"

            files = {
                'document': (filename, file_content, 'text/plain')
            }

            data = {
                'chat_id': self.chat_id,
                'caption': caption
            }

            response = requests.post(url, files=files, data=data, timeout=10)
            if response.status_code == 200:
                print(f"✅ File sent to Telegram: {filename}")
                return True
            else:
                print(f"❌ Telegram error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending file to Telegram: {str(e)}")
            return False

def run_screening(max_stocks=50):
    """Run the PCS screening on NSE F&O stocks"""

    print(f"\n{'='*60}")
    print("🚀 NSE F&O PCS Scanner - Telegram Edition")
    print(f"{'='*60}\n")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Default configuration (based on Streamlit defaults)
    config = {
        'stocks_to_scan': COMPLETE_NSE_FO_UNIVERSE[:max_stocks],
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
            'rectangle_top': True,
            'head_shoulders_bottom': True,
            'double_bottom': True,
            'three_rising_valleys': True,
            'rounding_bottom': True,
            'rounding_top_upside': True,
            'inverted_scallop': True,
        },
        'pattern_priority': 'All Patterns (Comprehensive)',
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'show_news': True,
    }

    results = []
    total_stocks = len(config['stocks_to_scan'])

    print(f"📊 Scanning {total_stocks} stocks...")
    print(f"⚙️ Filters: RSI {config['rsi_min']}-{config['rsi_max']}, ADX {config['adx_min']}+, Volume {config['min_volume_ratio']}x+")
    print(f"💪 Pattern Strength Min: {config['pattern_strength_min']}%\n")

    # Progress tracking
    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        try:
            clean_symbol = symbol.replace('.NS', '').replace('^', '')

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                print(f"[{i:3d}/{total_stocks}] ⏭️  {clean_symbol:15s} - Insufficient data")
                continue

            # Extract metrics
            current_price = data['Close'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            adx = data['ADX'].iloc[-1]
            macd = data['MACD'].iloc[-1]
            macd_signal = data['MACD_signal'].iloc[-1]
            volume_ratio = data['Volume'].iloc[-1] / data['Volume'].tail(21).iloc[:-1].mean()

            # Check basic filters
            rsi_pass = config['rsi_min'] <= rsi <= config['rsi_max']
            adx_pass = adx >= config['adx_min']
            volume_pass = volume_ratio >= config['min_volume_ratio']

            if not (rsi_pass and adx_pass and volume_pass):
                print(f"[{i:3d}/{total_stocks}] ❌ {clean_symbol:15s} - Filters failed (RSI:{rsi:.1f}, ADX:{adx:.1f}, Vol:{volume_ratio:.1f}x)")
                continue

            # Detect patterns
            patterns = []

            # Current day breakout detection
            if config['pattern_filters']['current_day_breakout']:
                breakout_detected, strength, details = scanner.detect_current_day_breakout(
                    data,
                    lookback_days=config['lookback_days'],
                    min_volume_ratio=config['volume_breakout_ratio']
                )
                if breakout_detected and strength >= config['pattern_strength_min']:
                    patterns.append({
                        'type': 'Current Day Breakout',
                        'strength': strength,
                        'confidence': 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'
                    })

            # Get weekly validation if enabled
            weekly_validation = {}
            if config['enable_weekly_validation']:
                weekly_data = scanner.get_weekly_stock_data(symbol, period="6mo")
                if weekly_data is not None:
                    weekly_validation = scanner.validate_weekly_strength(data, weekly_data, 'Current Day Breakout')

            if patterns:
                max_strength = max(p['strength'] for p in patterns)
                overall_confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

                # Get news if enabled
                news_data = {}
                if config['show_news']:
                    try:
                        news_data = scanner.get_fundamental_news(symbol, clean_symbol)
                    except:
                        news_data = {'news_count': 0}

                result = {
                    'symbol': clean_symbol,
                    'current_price': current_price,
                    'rsi': rsi,
                    'adx': adx,
                    'volume_ratio': volume_ratio,
                    'macd': macd,
                    'macd_signal': macd_signal,
                    'patterns': patterns,
                    'max_strength': max_strength,
                    'confidence': overall_confidence,
                    'weekly_validation': weekly_validation,
                    'news_count': news_data.get('news_count', 0)
                }

                results.append(result)

                has_weekly = "✅" if weekly_validation.get('weekly_validation') else "⚠️"
                has_news = "📰" if news_data.get('news_count', 0) > 0 else ""

                print(f"[{i:3d}/{total_stocks}] ✅ {clean_symbol:15s} - Strength: {max_strength:3.0f}% | "
                      f"RSI: {rsi:5.1f} | ADX: {adx:5.1f} | Vol: {volume_ratio:4.1f}x | {has_weekly} {has_news}")
            else:
                print(f"[{i:3d}/{total_stocks}] ⏭️  {clean_symbol:15s} - No patterns found")

        except Exception as e:
            print(f"[{i:3d}/{total_stocks}] ❌ {clean_symbol:15s} - Error: {str(e)[:30]}")
            continue

        # Rate limiting
        time.sleep(0.5)

    return results

def format_telegram_message(results):
    """Format results into a Telegram message"""
    if not results:
        return "❌ No stocks found meeting the filter criteria today."

    # Sort by strength
    results_sorted = sorted(results, key=lambda x: x['max_strength'], reverse=True)

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""
📊 <b>NSE F&O PCS Screener Results</b>
🕐 {current_time}

🎯 <b>Stocks Found: {len(results_sorted)}</b>

"""

    for i, result in enumerate(results_sorted[:10], 1):  # Top 10
        symbol = result['symbol']
        strength = result['max_strength']
        confidence = result['confidence']
        price = result['current_price']
        rsi = result['rsi']
        adx = result['adx']
        volume = result['volume_ratio']

        confidence_emoji = "🟢" if confidence == 'HIGH' else "🟡" if confidence == 'MEDIUM' else "🔴"

        message += f"""{i}. {confidence_emoji} <b>{symbol}</b>
   💰 ₹{price:.2f} | 💪 {strength:.0f}% | RSI {rsi:.1f} | ADX {adx:.1f} | Vol {volume:.1f}x
   {result['patterns'][0]['type']}

"""

    if len(results_sorted) > 10:
        message += f"\n📈 ... and {len(results_sorted) - 10} more stocks\n"

    message += "\n✅ <b>Filter Criteria:</b>"
    message += "\n• RSI: 30-75"
    message += "\n• ADX: 20+"
    message += "\n• Volume: 1.2x+"
    message += "\n• Pattern Strength: 65%+"

    return message

def format_csv_export(results):
    """Export results to CSV format"""
    if not results:
        return ""

    results_sorted = sorted(results, key=lambda x: x['max_strength'], reverse=True)

    csv_data = "Symbol,Price,RSI,ADX,Volume_Ratio,Pattern_Strength,Confidence,Pattern_Type\n"

    for result in results_sorted:
        pattern_type = result['patterns'][0]['type'] if result['patterns'] else 'N/A'
        csv_data += f"{result['symbol']},{result['current_price']:.2f},{result['rsi']:.1f},{result['adx']:.1f},"
        csv_data += f"{result['volume_ratio']:.2f},{result['max_strength']:.0f},{result['confidence']},{pattern_type}\n"

    return csv_data

def main():
    """Main execution"""

    # Get config from environment or use defaults
    max_stocks = int(os.getenv('SCAN_MAX_STOCKS', '50'))

    # Validate Telegram config
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ WARNING: Telegram credentials not found!")
        print("Set environment variables:")
        print("  export TELEGRAM_BOT_TOKEN=your_bot_token")
        print("  export TELEGRAM_CHAT_ID=your_chat_id")
        print("\nContinuing without Telegram notifications...")

    try:
        # Run screening
        results = run_screening(max_stocks=max_stocks)

        print(f"\n{'='*60}")
        print(f"📊 Screening Complete!")
        print(f"✅ Found {len(results)} qualifying stocks")
        print(f"{'='*60}\n")

        if results:
            # Display results
            results_sorted = sorted(results, key=lambda x: x['max_strength'], reverse=True)
            print("\n🏆 Top Results:")
            print("-" * 80)
            for i, result in enumerate(results_sorted[:10], 1):
                print(f"{i}. {result['symbol']:12} | Strength: {result['max_strength']:3.0f}% | "
                      f"RSI: {result['rsi']:5.1f} | ADX: {result['adx']:5.1f} | Vol: {result['volume_ratio']:4.1f}x")
            print("-" * 80)

            # Send to Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                print("\n📤 Sending results to Telegram...")
                notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)

                # Send summary message
                message = format_telegram_message(results)
                notifier.send_message(message)

                # Send CSV export
                csv_data = format_csv_export(results)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"nse_pcs_scan_{timestamp}.csv"
                notifier.send_file(csv_data.encode(), filename, "📊 Complete Stock List")

                print("✅ Results sent to Telegram!")
            else:
                print("\n⚠️ Telegram not configured - results not sent")
                print("\nTo set up Telegram notifications:")
                print("1. Create a Telegram bot via @BotFather")
                print("2. Get your chat ID")
                print("3. Set environment variables:")
                print("   export TELEGRAM_BOT_TOKEN=your_token")
                print("   export TELEGRAM_CHAT_ID=your_chat_id")
        else:
            print("\n⚠️ No qualifying stocks found today.")
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
                notifier.send_message("❌ No stocks found meeting the filter criteria today.")

    except KeyboardInterrupt:
        print("\n\n⚠️ Scanning interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
            notifier.send_message(f"❌ Scanner error: {str(e)[:100]}")
        sys.exit(1)

if __name__ == "__main__":
    main()
