#!/usr/bin/env python3
"""
NSE PCS Scanner - Telegram Integration
Runs the stock scanner and sends results to Telegram
"""

import yfinance as yf
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import pytz
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings
import sys
import time
import json
from typing import List, Dict

warnings.filterwarnings('ignore')

# Import the scanner class from streamlit_app
import sys
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

class TelegramScanner:
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram scanner with bot credentials"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        self.scanner = ProfessionalPCSScanner()
        self.ist = pytz.timezone('Asia/Kolkata')

    def send_telegram_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to Telegram"""
        try:
            url = f"{self.telegram_api}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Failed to send Telegram message: {e}")
            return False

    def run_scan(self,
                 stocks: List[str] = None,
                 rsi_min: int = 30,
                 rsi_max: int = 75,
                 adx_min: int = 20,
                 min_volume_ratio: float = 1.2,
                 pattern_strength_min: int = 65,
                 max_stocks: int = None) -> List[Dict]:
        """Run scanner on stocks"""

        if stocks is None:
            stocks = COMPLETE_NSE_FO_UNIVERSE

        if max_stocks:
            stocks = stocks[:max_stocks]

        results = []
        total = len(stocks)

        print(f"🚀 Starting scan on {total} stocks...")
        self.send_telegram_message(f"🚀 <b>NSE PCS Scanner Started</b>\n⏱️ Scanning {total} stocks...\n⏰ Time: {datetime.now(self.ist).strftime('%H:%M IST')}")

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}

            for i, symbol in enumerate(stocks):
                future = executor.submit(
                    self._scan_stock,
                    symbol, rsi_min, rsi_max, adx_min, min_volume_ratio, pattern_strength_min
                )
                futures[future] = (symbol, i + 1, total)

            for future in as_completed(futures):
                symbol, current, total = futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        print(f"✅ [{current}/{total}] {symbol.replace('.NS', '')} - Found pattern")
                    else:
                        print(f"⏭️  [{current}/{total}] {symbol.replace('.NS', '')}")
                except Exception as e:
                    print(f"❌ [{current}/{total}] {symbol.replace('.NS', '')} - Error: {e}")

        return results

    def _scan_stock(self, symbol: str, rsi_min: int, rsi_max: int, adx_min: int,
                    min_volume_ratio: float, pattern_strength_min: int) -> Dict:
        """Scan individual stock"""
        try:
            # Get stock data
            data = self.scanner.get_stock_data(symbol, period="3mo")
            if data is None or len(data) < 20:
                return None

            # Check volume
            volume_ok, volume_ratio, _ = self.scanner.check_volume_criteria(data, min_volume_ratio)
            if not volume_ok:
                return None

            # Create filter config
            config = {
                'rsi_min': rsi_min,
                'rsi_max': rsi_max,
                'adx_min': adx_min,
                'pattern_strength_min': pattern_strength_min,
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
                'min_volume_ratio': min_volume_ratio,
            }

            # Detect patterns
            patterns = self.scanner.detect_patterns(data, symbol, config)
            if not patterns:
                return None

            # Filter by strength
            patterns = [p for p in patterns if p['strength'] >= pattern_strength_min]
            if not patterns:
                return None

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            return {
                'symbol': symbol,
                'current_price': current_price,
                'volume_ratio': volume_ratio,
                'rsi': current_rsi,
                'adx': current_adx,
                'patterns': patterns,
                'data': data
            }

        except Exception as e:
            return None

    def format_results_for_telegram(self, results: List[Dict]) -> str:
        """Format scan results for Telegram"""
        if not results:
            return "❌ <b>No stocks found meeting the criteria</b>"

        # Sort by pattern strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        message = f"✅ <b>Scan Complete: {len(results)} Stocks Found</b>\n"
        message += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n\n"

        # Summary
        total_patterns = sum(len(r['patterns']) for r in results)
        avg_strength = np.mean([p['strength'] for r in results for p in r['patterns']])

        message += f"📊 <b>Summary</b>\n"
        message += f"• Stocks: {len(results)}\n"
        message += f"• Total Patterns: {total_patterns}\n"
        message += f"• Avg Strength: {avg_strength:.1f}%\n\n"

        # Top 20 stocks
        message += "<b>Top Stocks:</b>\n"
        message += "<code>"

        for i, result in enumerate(results[:20], 1):
            symbol_clean = result['symbol'].replace('.NS', '').replace('^', '')
            max_strength = max(p['strength'] for p in result['patterns'])
            best_pattern = max(result['patterns'], key=lambda x: x['strength'])

            message += f"{i:2d}. {symbol_clean:8s} | "
            message += f"₹{result['current_price']:8.2f} | "
            message += f"Vol:{result['volume_ratio']:5.1f}x | "
            message += f"RSI:{result['rsi']:5.1f} | "
            message += f"Str:{max_strength:3.0f}%\n"

        message += "</code>\n"

        if len(results) > 20:
            message += f"\n... and {len(results) - 20} more stocks\n"

        # Export details
        message += f"\n💾 <b>Full List:</b>\n"
        stocks_list = " | ".join([r['symbol'].replace('.NS', '') for r in results])
        message += f"<code>{stocks_list}</code>"

        return message

    def send_detailed_results(self, results: List[Dict], batch_size: int = 10):
        """Send detailed results in batches"""
        if not results:
            self.send_telegram_message("❌ No stocks found meeting the criteria")
            return

        # Sort by strength
        results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        # Send summary first
        summary_msg = self.format_results_for_telegram(results)
        self.send_telegram_message(summary_msg)

        time.sleep(1)

        # Send detailed info for top stocks
        for i, result in enumerate(results[:batch_size], 1):
            symbol_clean = result['symbol'].replace('.NS', '').replace('^', '')

            detail_msg = f"<b>#{i}. {symbol_clean}</b>\n"
            detail_msg += f"💰 Price: ₹{result['current_price']:.2f}\n"
            detail_msg += f"📊 Volume: {result['volume_ratio']:.2f}x\n"
            detail_msg += f"📈 RSI: {result['rsi']:.1f}\n"
            detail_msg += f"⚡ ADX: {result['adx']:.1f}\n\n"

            detail_msg += "<b>Patterns:</b>\n"
            for pattern in sorted(result['patterns'], key=lambda x: x['strength'], reverse=True)[:3]:
                detail_msg += f"• {pattern['type']}: {pattern['strength']:.0f}% ({pattern['confidence']})\n"

            self.send_telegram_message(detail_msg)
            time.sleep(0.5)

    def run_and_report(self, max_stocks: int = None):
        """Run scan and send results to Telegram"""
        try:
            # Run scan with default settings
            results = self.run_scan(
                stocks=COMPLETE_NSE_FO_UNIVERSE,
                rsi_min=30,
                rsi_max=75,
                adx_min=20,
                min_volume_ratio=1.2,
                pattern_strength_min=65,
                max_stocks=max_stocks
            )

            print(f"\n✅ Scan completed! Found {len(results)} stocks")

            # Send results to Telegram
            self.send_detailed_results(results, batch_size=10)

            print("✅ Results sent to Telegram!")
            return results

        except Exception as e:
            error_msg = f"❌ Scanner error: {str(e)}"
            print(error_msg)
            self.send_telegram_message(error_msg)
            return []


def main():
    # Check for credentials
    if len(sys.argv) < 2:
        print("❌ Usage: python telegram_scanner.py <BOT_TOKEN> <CHAT_ID> [MAX_STOCKS]")
        print("\nExample: python telegram_scanner.py 123456:ABC-DEF 987654321 None")
        print("\nTo get bot token and chat ID:")
        print("1. Create bot: https://t.me/BotFather")
        print("2. Get chat ID: Send a message to @userinfobot")
        sys.exit(1)

    bot_token = sys.argv[1]
    chat_id = sys.argv[2]
    max_stocks = int(sys.argv[3]) if len(sys.argv) > 3 else None

    if max_stocks is None or max_stocks == "None":
        max_stocks = None

    print(f"""
    ╔════════════════════════════════════════╗
    ║   NSE PCS Scanner - Telegram Edition   ║
    ║                                        ║
    ║   📊 Analyzing NSE F&O Stocks         ║
    ║   🚀 Sending results to Telegram      ║
    ╚════════════════════════════════════════╝
    """)

    # Run scanner
    telegram_scanner = TelegramScanner(bot_token, chat_id)
    results = telegram_scanner.run_and_report(max_stocks=max_stocks)

    # Save results to CSV for reference
    if results:
        df = pd.DataFrame([{
            'Symbol': r['symbol'].replace('.NS', ''),
            'Price': r['current_price'],
            'Volume': r['volume_ratio'],
            'RSI': r['rsi'],
            'ADX': r['adx'],
            'Top_Pattern': max(r['patterns'], key=lambda x: x['strength'])['type'],
            'Pattern_Strength': max(r['patterns'], key=lambda x: x['strength'])['strength']
        } for r in results])

        csv_path = f"/tmp/scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ Results saved to: {csv_path}")


if __name__ == "__main__":
    main()
