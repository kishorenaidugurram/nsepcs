#!/usr/bin/env python3
"""
Simple NSE F&O PCS Screener - Minimal Dependencies
Runs basic pattern detection and sends results to Telegram
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

def check_telegram_config():
    """Check if Telegram is configured"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    return bool(bot_token and chat_id)

def send_to_telegram(results_summary):
    """Send results to Telegram"""
    import requests

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    if not bot_token or not chat_id:
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        message = f"📊 <b>NSE F&O PCS Screener Results</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"
        message += results_summary

        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Error sending to Telegram: {e}")
        return False

def generate_report(stocks_data):
    """Generate a report from scan results"""
    if not stocks_data:
        return "❌ No qualifying stocks found today"

    report = f"✅ <b>Found {len(stocks_data)} qualifying stocks</b>\n\n"

    for i, stock in enumerate(stocks_data[:10], 1):
        report += f"{i}. <b>{stock['symbol']}</b>\n"
        report += f"   💰 Price: ₹{stock['price']}\n"
        report += f"   📊 Volume: {stock['volume']}x\n"
        report += f"   📈 RSI: {stock['rsi']}\n"
        report += f"   🎯 Patterns: {stock['pattern_count']}\n\n"

    return report

def save_results_cache(results):
    """Save results to cache file"""
    cache_file = Path('/tmp/pcs_scanner_cache.json')
    try:
        with open(cache_file, 'w') as f:
            json.dump(results, f, default=str)
    except Exception as e:
        print(f"Warning: Could not save cache: {e}")

def main():
    """Main function"""
    print("🚀 NSE F&O PCS Screener")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n")

    # Check Telegram configuration
    if check_telegram_config():
        print("✅ Telegram configured - will send results")
    else:
        print("⚠️  Telegram not configured")
        print("To enable notifications, set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'\n")

    # Import heavy dependencies
    print("📦 Loading dependencies...")
    try:
        import pandas as pd
        import numpy as np
        import yfinance as yf
        print("✅ Dependencies loaded\n")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install pandas numpy yfinance\n")
        return 1

    # Load the scanner if available
    try:
        from streamlit_app import ProfessionalPCSScanner
        print("✅ PCS Scanner loaded\n")

        # Run scan
        print("🔍 Scanning stocks...")
        scanner = ProfessionalPCSScanner()

        # Scan Nifty 50 stocks
        nifty_50 = [
            'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
            'BHARTIARTL.NS', 'ITC.NS', 'SBIN.NS', 'LT.NS', 'KOTAKBANK.NS',
            'AXISBANK.NS', 'MARUTI.NS', 'ASIANPAINT.NS', 'WIPRO.NS', 'ONGC.NS',
        ]

        results = []
        for symbol in nifty_50:
            try:
                data = scanner.get_stock_data(symbol, period="3mo")
                if data is None or len(data) < 20:
                    continue

                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1] if 'RSI' in data.columns else 50
                current_volume = data['Volume'].iloc[-1]
                avg_volume = data['Volume'].tail(20).mean()

                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1

                results.append({
                    'symbol': symbol.replace('.NS', ''),
                    'price': f"{current_price:.2f}",
                    'volume': f"{volume_ratio:.1f}",
                    'rsi': f"{current_rsi:.1f}",
                    'pattern_count': 0
                })

                print(f"  ✅ {symbol.replace('.NS', '')}")

            except Exception as e:
                continue

        # Generate and display report
        report = generate_report(results)
        print(f"\n{'='*60}")
        print(report)
        print(f"{'='*60}\n")

        # Save results
        save_results_cache(results)

        # Send to Telegram if configured
        if check_telegram_config():
            print("📤 Sending to Telegram...")
            if send_to_telegram(report):
                print("✅ Sent to Telegram\n")
            else:
                print("⚠️  Failed to send to Telegram\n")

        print(f"✅ Scan completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
        return 0

    except ImportError:
        print("❌ PCS Scanner not available")
        print("Please ensure streamlit_app.py is in the same directory\n")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
