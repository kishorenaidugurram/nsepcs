#!/usr/bin/env python3
"""
Standalone PCS Scanner - Runs the NSE F&O PCS scanner programmatically
and sends results to Telegram (if configured) or saves to file.
"""

import sys
import os
import json
import pandas as pd
from datetime import datetime
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

warnings.filterwarnings('ignore')

# Import the scanner class from the main app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_API_URL = "https://api.telegram.org/bot"

def send_telegram_message(message: str, bot_token: str = None, chat_id: str = None):
    """Send message to Telegram"""
    token = bot_token or TELEGRAM_BOT_TOKEN
    chat = chat_id or TELEGRAM_CHAT_ID

    if not token or not chat:
        print("❌ Telegram credentials not configured. Skipping Telegram send.")
        return False

    try:
        url = f"{TELEGRAM_API_URL}{token}/sendMessage"
        payload = {
            "chat_id": chat,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ Message sent to Telegram")
            return True
        else:
            print(f"❌ Telegram error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def format_stock_results_for_telegram(results: list) -> str:
    """Format stock results for Telegram message"""
    if not results:
        return "No stocks meeting criteria found."

    # Telegram message length limit is 4096, so we need to be concise
    message = f"<b>🎯 PCS Scanner Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}</b>\n\n"

    # Group by confidence level
    high_conf = [r for r in results if r.get('confidence') == 'HIGH']
    med_conf = [r for r in results if r.get('confidence') == 'MEDIUM']
    low_conf = [r for r in results if r.get('confidence') == 'LOW']

    def add_stocks(stocks, title, emoji):
        if stocks:
            message_part = f"\n<b>{emoji} {title} Confidence ({len(stocks)})</b>\n"
            for stock in stocks[:5]:  # Limit to 5 per group due to message size
                score = stock.get('pcs_score', 'N/A')
                symbol = stock.get('symbol', 'N/A')
                price = stock.get('current_price', 'N/A')
                message_part += f"  • {symbol}: {score}% | ₹{price}\n"
            if len(stocks) > 5:
                message_part += f"  ... and {len(stocks) - 5} more\n"
            return message_part
        return ""

    message += add_stocks(high_conf, "HIGH", "🟢")
    message += add_stocks(med_conf, "MEDIUM", "🟡")
    message += add_stocks(low_conf, "LOW", "🔴")

    message += f"\n<b>Total:</b> {len(results)} stocks\n"
    message += f"<i>Run at {datetime.now().strftime('%H:%M UTC')}</i>"

    return message

def get_default_filters() -> dict:
    """Return default filter configuration for automated runs"""
    return {
        'min_score': 60,  # Minimum PCS score
        'max_stocks': 30,  # Analyze up to 30 stocks
        'liquidity_tier': 1,  # All liquidity tiers
        'rsi_min': 30,
        'rsi_max': 80,
        'adx_min': 20,
        'ma_support': True,
        'ma_type': 'SMA',
        'ma_tolerance': 5,
        'pattern_strength_min': 0.6,
        'lookback_days': 20,
        'volume_breakout_ratio': 1.5,
        'show_charts': False,
        'show_enhancement': True,
        'enable_daily_analysis': True,
        'enable_weekly_validation': True,
        'analysis_mode': 'Daily + Weekly Combined (Recommended)',
        'pattern_priority': 'All Patterns (Comprehensive)',
        'pattern_filters': {
            'current_day_breakout': True,
            'cup_and_handle': True,
            'double_bottom': True,
            'rectangle_bottom': True,
            'head_shoulders_bottom': True,
            'bump_and_run_reversal_bottom': True,
            'flat_base_breakout': True,
        }
    }

def run_scanner_batch(max_stocks: int = 30, min_score: int = 60):
    """Run scanner on a batch of stocks"""
    print(f"🚀 Starting PCS Scanner")
    print(f"   Max Stocks: {max_stocks}")
    print(f"   Min Score: {min_score}")
    print()

    scanner = ProfessionalPCSScanner()
    filters = get_default_filters()
    filters['min_score'] = min_score

    # Get list of stocks to analyze
    nse_stocks = scanner.nse_stocks[:max_stocks]

    results = []
    analyzed = 0

    print(f"📊 Analyzing {len(nse_stocks)} stocks...")

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}

        for stock in nse_stocks:
            future = executor.submit(scanner.detect_patterns,
                                   stock['data'],
                                   stock['symbol'],
                                   filters)
            futures[future] = stock

        for i, future in enumerate(as_completed(futures), 1):
            stock = futures[future]
            try:
                patterns = future.result(timeout=30)
                if patterns:
                    result = {
                        'symbol': stock['symbol'],
                        'name': stock['name'],
                        'current_price': stock.get('current_price', 0),
                        'pcs_score': int(patterns[0].get('strength', 0) * 100) if patterns else 0,
                        'pattern': patterns[0].get('pattern') if patterns else 'N/A',
                        'confidence': patterns[0].get('confidence') if patterns else 'LOW',
                    }
                    if result['pcs_score'] >= min_score:
                        results.append(result)
                        print(f"  ✓ {stock['symbol']:12} | {result['pcs_score']:3}% | {result['confidence']}")
                analyzed += 1
                if i % 10 == 0:
                    print(f"    Analyzed {i}/{len(nse_stocks)}...")
            except Exception as e:
                print(f"  ✗ {stock['symbol']:12} | Error: {str(e)[:30]}")
                analyzed += 1

    print(f"\n✅ Analysis complete: {len(results)} qualifying stocks from {analyzed} analyzed")
    return results

def save_results_to_file(results: list, filename: str = None):
    """Save results to CSV file"""
    if not filename:
        filename = f"/tmp/pcs_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    if results:
        df = pd.DataFrame(results)
        df = df.sort_values('pcs_score', ascending=False)
        df.to_csv(filename, index=False)
        print(f"💾 Results saved to: {filename}")
        return filename
    return None

def main():
    """Main entry point"""
    print("=" * 60)
    print("NSE F&O PCS SCANNER - AUTOMATED RUN")
    print("=" * 60)
    print()

    try:
        # Run scanner
        results = run_scanner_batch(max_stocks=30, min_score=60)

        if results:
            print(f"\n📈 Found {len(results)} qualifying stocks")

            # Format for Telegram
            telegram_message = format_stock_results_for_telegram(results)

            # Try to send to Telegram
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                print("\n📱 Sending to Telegram...")
                send_telegram_message(telegram_message)
            else:
                print("\n⚠️  Telegram not configured. Results:")
                print(telegram_message)

            # Save results to file
            csv_file = save_results_to_file(results)

            print(f"\n✅ Scan completed successfully!")
            return csv_file
        else:
            print("\n⚠️  No stocks meeting filter criteria")
            if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
                send_telegram_message("⚠️ No stocks met the PCS filter criteria in today's scan.")
            return None

    except Exception as e:
        error_msg = f"❌ Scanner error: {str(e)}"
        print(error_msg)
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            send_telegram_message(f"<b>❌ PCS Scanner Error</b>\n{error_msg}")
        raise

if __name__ == "__main__":
    main()
