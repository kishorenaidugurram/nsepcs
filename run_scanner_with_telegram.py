#!/usr/bin/env python3
"""
Telegram Stock Scanner - Run this on your local machine
Scans NSE F&O stocks and sends results to Telegram

Setup:
1. Create a Telegram bot: Message @BotFather on Telegram, type /newbot
2. Get your chat ID: Message @userinfobot
3. Set environment variables:
   export TELEGRAM_BOT_TOKEN='your_bot_token'
   export TELEGRAM_CHAT_ID='your_chat_id'
4. Install requirements:
   pip install -r requirements.txt
5. Run this script:
   python3 run_scanner_with_telegram.py
"""

import os
import sys
import pandas as pd
from datetime import datetime
import requests

from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE


def send_telegram_message(bot_token, chat_id, message, parse_mode='HTML'):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")
        return False


def send_telegram_document(bot_token, chat_id, file_path, caption=""):
    """Send file to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': chat_id, 'caption': caption}
            response = requests.post(url, files=files, data=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error sending Telegram document: {e}")
        return False


def run_scanner(stocks_to_scan=None, max_stocks=None):
    """Run the stock scanner and collect results"""
    scanner = ProfessionalPCSScanner()

    if stocks_to_scan is None:
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE

    if max_stocks:
        stocks_to_scan = stocks_to_scan[:max_stocks]

    # Configuration
    config = {
        'stocks_to_scan': stocks_to_scan,
        'min_volume_ratio': 1.0,
        'show_news': False,
        'enhancements': {}
    }

    results = []
    errors = []

    print(f"\n{'='*60}")
    print(f"Starting scan of {len(config['stocks_to_scan'])} stocks...")
    print(f"{'='*60}\n")

    for i, symbol in enumerate(config['stocks_to_scan'], 1):
        clean_symbol = symbol.replace('.NS', '').replace('^', '')
        progress = f"[{i}/{len(config['stocks_to_scan'])}]"

        try:
            print(f"{progress} Scanning {clean_symbol}...", end=" ")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                print("❌ No data")
                errors.append((clean_symbol, "No data available"))
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(
                data, config['min_volume_ratio']
            )
            if not volume_ok:
                print("⊘ Low volume")
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, config)
            if not patterns:
                print("⊘ No patterns")
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result entry
            stock_result = {
                'symbol': symbol,
                'clean_symbol': clean_symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
            }

            results.append(stock_result)
            best_pattern = max(patterns, key=lambda p: p['strength'])
            print(f"✓ {len(patterns)} patterns | Best: {best_pattern['type'][:20]} ({best_pattern['strength']:.0f}%)")

        except Exception as e:
            error_msg = str(e)[:50]
            print(f"❌ Error: {error_msg}")
            errors.append((clean_symbol, error_msg))
            continue

    return results, errors


def format_results_for_telegram(results):
    """Format scan results for Telegram message"""
    if not results:
        return "❌ No stocks matched the filter criteria today."

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    message = "<b>📈 NSE F&O Stock Scanner Results</b>\n"
    message += f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</i>\n"
    message += f"<b>Total Stocks Scanned: {len(results)}</b>\n"
    message += "━" * 50 + "\n\n"

    for idx, result in enumerate(results[:15], 1):  # Limit to 15 for message size
        symbol = result['clean_symbol']
        price = result['current_price']
        patterns = result['patterns']
        best_pattern = max(patterns, key=lambda p: p['strength'])

        confidence_emoji = "🟢" if best_pattern['confidence'] == 'HIGH' else "🟡" if best_pattern['confidence'] == 'MEDIUM' else "🔴"

        message += f"<b>{idx}. {symbol}</b> {confidence_emoji}\n"
        message += f"   Price: <b>₹{price:.2f}</b>\n"
        message += f"   Pattern: {best_pattern['type']}\n"
        message += f"   Strength: {best_pattern['strength']:.0f}% | Success: {best_pattern['success_rate']}%\n"
        message += f"   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f} | Vol: {result['volume_ratio']:.1f}x\n"
        message += "\n"

    if len(results) > 15:
        message += f"<i>... and {len(results) - 15} more stocks</i>\n"

    return message


def main():
    print("\n" + "="*60)
    print("NSE F&O Stock Scanner with Telegram Integration")
    print("="*60)

    # Get Telegram credentials from environment
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    send_to_telegram = False
    if bot_token and chat_id:
        send_to_telegram = True
        print(f"\n✓ Telegram configured")
        print(f"  Bot Token: {bot_token[:20]}...")
        print(f"  Chat ID: {chat_id}")
    else:
        print("\n⚠️  Telegram credentials not found!")
        print("   To enable Telegram, set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_bot_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        print("\n   Continuing scan without Telegram...")

    # Ask user how many stocks to scan
    print("\nChoose scan scope:")
    print("  1. Quick scan (20 stocks)")
    print("  2. Standard scan (50 stocks)")
    print("  3. Full scan (all stocks)")
    print("  4. Custom number")

    choice = input("\nEnter your choice (1-4): ").strip()

    max_stocks = None
    if choice == '1':
        max_stocks = 20
    elif choice == '2':
        max_stocks = 50
    elif choice == '3':
        max_stocks = None
    elif choice == '4':
        try:
            max_stocks = int(input("Enter number of stocks to scan: "))
        except ValueError:
            max_stocks = 20
    else:
        max_stocks = 20

    # Run scanner
    results, errors = run_scanner(max_stocks=max_stocks)

    # Display summary
    print(f"\n{'='*60}")
    print(f"Scan Complete!")
    print(f"{'='*60}")
    print(f"✓ Stocks found: {len(results)}")
    if errors:
        print(f"✗ Errors: {len(errors)}")

    if not results:
        print("\n❌ No stocks matched the filter criteria.")
        if send_to_telegram:
            send_telegram_message(
                bot_token, chat_id,
                "<b>📈 Stock Scanner Result</b>\n\n"
                "❌ No stocks matched the filter criteria today."
            )
        return

    # Sort and display top results
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    print(f"\n{'Top 10 Stocks by Strength:':^60}")
    print("─" * 60)
    for i, result in enumerate(results[:10], 1):
        symbol = result['clean_symbol']
        price = result['current_price']
        best = max(result['patterns'], key=lambda p: p['strength'])
        print(f"{i:2}. {symbol:12} | ₹{price:8.2f} | {best['type'][:25]:25} | {best['strength']:6.0f}%")

    # Save to CSV
    csv_path = f"scanner_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:
        summary_data = []
        for result in results:
            best = max(result['patterns'], key=lambda p: p['strength'])
            summary_data.append({
                'Symbol': result['clean_symbol'],
                'Price': result['current_price'],
                'Pattern': best['type'],
                'Strength': best['strength'],
                'Confidence': best['confidence'],
                'RSI': result['rsi'],
                'ADX': result['adx'],
                'Volume': result['volume_ratio']
            })

        df = pd.DataFrame(summary_data)
        df.to_csv(csv_path, index=False)
        print(f"\n✓ Results saved to: {csv_path}")
    except Exception as e:
        print(f"\n✗ Error saving CSV: {e}")

    # Send to Telegram if configured
    if send_to_telegram:
        print(f"\n📤 Sending results to Telegram...")
        message = format_results_for_telegram(results)

        if send_telegram_message(bot_token, chat_id, message):
            print("✓ Message sent successfully!")

            # Also send CSV file if it exists
            if os.path.exists(csv_path):
                if send_telegram_document(bot_token, chat_id, csv_path,
                                        f"📊 Scanner Results - {len(results)} stocks"):
                    print("✓ CSV file sent successfully!")
        else:
            print("✗ Failed to send message to Telegram")
            print("   Check your bot token and chat ID")

    print("\n" + "="*60)
    print("Scanner completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
