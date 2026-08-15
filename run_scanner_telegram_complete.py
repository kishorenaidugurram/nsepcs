#!/usr/bin/env python3
"""
Comprehensive NSE F&O PCS Scanner with Telegram Integration
Runs the stock scanner and sends qualifying stocks to Telegram

Setup Instructions:
1. Create a Telegram bot: Talk to @BotFather on Telegram and get your BOT_TOKEN
2. Get your Chat ID: Send /start to @userinfobot and note the ID
3. Set environment variables:
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
4. Run this script: python3 run_scanner_telegram_complete.py
"""

import sys
import os
import json
from datetime import datetime
import pytz
import logging
from typing import List, Dict, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import from main app
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE

# Telegram imports
try:
    import requests
except ImportError:
    logger.warning("requests library not available, installing...")
    os.system("pip install requests -q")
    import requests


class TelegramNotifier:
    """Send messages to Telegram Bot API"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        """Initialize Telegram notifier

        Args:
            bot_token: Telegram bot token (or set TELEGRAM_BOT_TOKEN env var)
            chat_id: Telegram chat ID (or set TELEGRAM_CHAT_ID env var)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        self.enabled = bool(self.bot_token and self.chat_id)

        if not self.enabled:
            logger.warning(
                "⚠️  Telegram not configured!\n"
                "   Set environment variables:\n"
                "   export TELEGRAM_BOT_TOKEN='your_token'\n"
                "   export TELEGRAM_CHAT_ID='your_chat_id'\n"
                "   Get token from @BotFather, chat ID from @userinfobot on Telegram"
            )
        else:
            logger.info(f"✅ Telegram initialized (Chat ID: {self.chat_id})")

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Send message to Telegram

        Args:
            message: Message text (supports HTML)
            parse_mode: Parse mode (HTML or Markdown)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning("Telegram not enabled")
            return False

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

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram")
                return True
            else:
                logger.error(f"❌ Failed to send: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Error sending message: {str(e)}")
            return False

    def send_stock_results(self, stocks: List[Dict], scan_config: Dict) -> bool:
        """Send stock screening results to Telegram

        Args:
            stocks: List of stock results
            scan_config: Scanner configuration used

        Returns:
            True if sent successfully
        """
        if not stocks:
            msg = "❌ <b>No Stocks Found</b>\nNo stocks met the filter criteria. Try adjusting parameters."
            self.send_message(msg)
            return False

        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M IST")

        # Build summary message
        message = f"""📊 <b>NSE F&O PCS Scanner Report</b>
⏰ {timestamp}

🎯 <b>Summary:</b>
📈 Stocks Found: <b>{len(stocks)}</b>
💪 Avg Strength: <b>{sum(max(p['strength'] for p in s['patterns']) for s in stocks) / len(stocks):.0f}%</b>

📋 <b>Scanner Settings:</b>
RSI: {scan_config['rsi_min']}-{scan_config['rsi_max']}
ADX Min: {scan_config['adx_min']}
Volume Ratio: {scan_config['min_volume_ratio']}x
Strength Threshold: {scan_config['pattern_strength_min']}%

🔝 <b>Top 10 Stocks:</b>
"""
        # Add top stocks
        top_stocks = sorted(
            stocks,
            key=lambda x: max(p['strength'] for p in x['patterns']),
            reverse=True
        )[:10]

        for i, stock in enumerate(top_stocks, 1):
            symbol = stock['symbol'].replace('.NS', '')
            price = stock['current_price']
            pattern = stock['patterns'][0] if stock['patterns'] else {}
            strength = pattern.get('strength', 0)
            confidence = pattern.get('confidence', 'N/A')
            pattern_type = pattern.get('type', 'N/A')

            emoji = "🟢" if confidence == 'HIGH' else "🟡" if confidence == 'MEDIUM' else "🔴"

            message += f"\n{i}. {emoji} <b>{symbol}</b>\n"
            message += f"   💰 ₹{price:.2f} | 💪 {strength:.0f}% | {confidence}\n"
            message += f"   📊 {pattern_type}\n"

        if len(stocks) > 10:
            message += f"\n... and <b>{len(stocks) - 10}</b> more stocks"

        message += """

📥 <b>Next Steps:</b>
1. Check full results in scan_results.json
2. Export to Excel for detailed analysis
3. Run Streamlit app for interactive charts
"""

        return self.send_message(message)

    def send_detailed_stock(self, stock: Dict) -> bool:
        """Send detailed stock analysis to Telegram

        Args:
            stock: Stock result dictionary

        Returns:
            True if sent successfully
        """
        symbol = stock['symbol'].replace('.NS', '')
        pattern = stock['patterns'][0] if stock['patterns'] else {}
        price = stock['current_price']
        rsi = stock['rsi']
        adx = stock['adx']
        volume_ratio = stock['volume_ratio']
        strength = pattern.get('strength', 0)
        confidence = pattern.get('confidence', 'N/A')
        pattern_type = pattern.get('type', 'N/A')
        success_rate = pattern.get('success_rate', 0)
        pcs_fit = pattern.get('pcs_suitability', 0)

        message = f"""📈 <b>{symbol} - Detailed Analysis</b>

💰 <b>Price Metrics:</b>
   Current Price: ₹<b>{price:.2f}</b>

📊 <b>Technical Indicators:</b>
   RSI: {rsi:.1f}
   ADX: {adx:.1f}
   Volume Ratio: {volume_ratio:.2f}x

🎯 <b>Pattern:</b>
   Type: <b>{pattern_type}</b>
   Strength: <b>{strength:.0f}%</b>
   Confidence: <b>{confidence}</b>
   Success Rate: {success_rate}%
   PCS Fit: {pcs_fit}%

💡 <b>Recommendation:</b>
   {'✅ STRONG BUY' if strength >= 85 else '⚠️  MODERATE' if strength >= 70 else '❌ WEAK'}
"""
        return self.send_message(message)


class StockScannerWithTelegram:
    """Main scanner class with Telegram integration"""

    def __init__(self):
        self.scanner = ProfessionalPCSScanner()
        self.notifier = TelegramNotifier()
        self.ist = pytz.timezone('Asia/Kolkata')

    def create_default_config(self) -> Dict:
        """Create optimized default configuration"""
        return {
            'rsi_min': 30,
            'rsi_max': 80,
            'adx_min': 15,
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
                'rectangle_top': False,
                'head_shoulders_bottom': True,
                'double_bottom': True,
                'three_rising_valleys': True,
                'rounding_bottom': True,
                'rounding_top_upside': False,
                'inverted_scallop': True
            },
            'pattern_priority': 'All Patterns (Comprehensive)',
            'analysis_mode': 'Daily + Weekly Combined (Recommended)',
            'enable_daily_analysis': True,
            'enable_weekly_validation': True
        }

    def scan_stocks(self, stocks_to_scan: List[str], config: Dict) -> List[Dict]:
        """Scan stocks for patterns

        Args:
            stocks_to_scan: List of stock symbols to scan
            config: Scanner configuration

        Returns:
            List of stock results
        """
        results = []
        logger.info(f"🔍 Starting scan of {len(stocks_to_scan)} stocks...")

        for i, symbol in enumerate(stocks_to_scan, 1):
            if i % 10 == 0:
                logger.info(f"⏳ Progress: {i}/{len(stocks_to_scan)}")

            try:
                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None:
                    continue

                # Check volume
                volume_ok, volume_ratio, _ = self.scanner.check_volume_criteria(
                    data, config['min_volume_ratio']
                )
                if not volume_ok:
                    continue

                # Detect patterns
                patterns = self.scanner.detect_patterns(data, symbol, config)
                if not patterns:
                    continue

                # Get metrics
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Create result
                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data
                }

                results.append(stock_result)
                logger.debug(f"✅ {symbol.replace('.NS', '')} - Pattern found")

            except Exception as e:
                logger.debug(f"⚠️  {symbol}: {str(e)[:50]}")
                continue

        logger.info(f"✅ Scan complete. Found {len(results)} stocks")
        return results

    def run(self, num_stocks: int = 50, send_telegram: bool = True):
        """Run the complete scanner workflow

        Args:
            num_stocks: Number of stocks to scan (default 50 for speed)
            send_telegram: Send results to Telegram (default True)
        """
        logger.info("=" * 70)
        logger.info("NSE F&O PCS SCANNER WITH TELEGRAM INTEGRATION")
        logger.info("=" * 70)

        # Configuration
        config = self.create_default_config()

        # Stocks to scan
        stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:num_stocks]

        # Scan
        results = self.scan_stocks(stocks_to_scan, config)

        if not results:
            logger.error("❌ No stocks found matching criteria")
            if send_telegram and self.notifier.enabled:
                self.notifier.send_message(
                    "❌ <b>Scan Complete</b>\n\n"
                    "No stocks found matching the filter criteria.\n\n"
                    "💡 Try adjusting parameters:\n"
                    "• Lower RSI threshold\n"
                    "• Reduce ADX minimum\n"
                    "• Increase volume ratio tolerance"
                )
            return

        # Sort by strength
        results.sort(
            key=lambda x: max(p['strength'] for p in x['patterns']),
            reverse=True
        )

        logger.info(f"📊 Found {len(results)} qualifying stocks!")

        # Send to Telegram
        if send_telegram:
            if self.notifier.enabled:
                self.notifier.send_stock_results(results, config)
                logger.info("📤 Results sent to Telegram")
            else:
                logger.warning("⚠️  Telegram not configured - skipping notification")

        # Save to JSON
        self._save_results(results, config)

        # Print summary
        self._print_summary(results[:10])

    def _save_results(self, results: List[Dict], config: Dict):
        """Save results to JSON file"""
        output_file = '/tmp/claude-0/-home-user-nsepcs/ca12a9e7-0f2a-59d1-a829-3fe74b60cf4c/scratchpad/scan_results.json'
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        results_data = []
        for result in results:
            pattern = result['patterns'][0] if result['patterns'] else {}
            results_data.append({
                'symbol': result['symbol'].replace('.NS', ''),
                'price': float(result['current_price']),
                'volume_ratio': float(result['volume_ratio']),
                'rsi': float(result['rsi']),
                'adx': float(result['adx']),
                'pattern_type': pattern.get('type', 'N/A'),
                'pattern_strength': float(pattern.get('strength', 0)),
                'confidence': pattern.get('confidence', 'N/A'),
                'success_rate': float(pattern.get('success_rate', 0)),
                'pcs_fit': float(pattern.get('pcs_suitability', 0))
            })

        with open(output_file, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)

        logger.info(f"💾 Results saved: {output_file}")

    def _print_summary(self, top_results: List[Dict]):
        """Print summary of top results"""
        logger.info("\n" + "=" * 70)
        logger.info("TOP RESULTS")
        logger.info("=" * 70)

        for i, stock in enumerate(top_results, 1):
            symbol = stock['symbol'].replace('.NS', '')
            price = stock['current_price']
            pattern = stock['patterns'][0] if stock['patterns'] else {}
            strength = pattern.get('strength', 0)
            confidence = pattern.get('confidence', 'N/A')
            pattern_type = pattern.get('type', 'N/A')

            logger.info(
                f"{i}. {symbol:15} | ₹{price:10.2f} | "
                f"Strength: {strength:5.0f}% | {confidence:8} | {pattern_type}"
            )

        logger.info("=" * 70)


def main():
    """Main entry point"""
    try:
        # Initialize and run scanner
        scanner = StockScannerWithTelegram()

        # Run with 50 stocks for demonstration
        # Increase for full scan: scanner.run(num_stocks=208)
        scanner.run(num_stocks=50, send_telegram=True)

        logger.info("\n✅ Scan completed successfully!")

    except KeyboardInterrupt:
        logger.info("\n⚠️  Scan interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
