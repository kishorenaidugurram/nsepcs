#!/usr/bin/env python3
"""
Telegram Stock Scanner - Automated NSE F&O Stock Analysis with Telegram Integration
Runs the PCS analysis and sends qualifying stocks to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional
import time
import requests

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scanner components from streamlit app
from streamlit_app import (
    ProfessionalPCSScanner,
    COMPLETE_NSE_FO_UNIVERSE
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/nsepcs_scanner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    """Configuration for scanner and Telegram"""

    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

    # Scanner filter settings
    MIN_PATTERN_STRENGTH = int(os.getenv('MIN_PATTERN_STRENGTH', '70'))
    MIN_VOLUME_RATIO = float(os.getenv('MIN_VOLUME_RATIO', '1.2'))
    MIN_ADX = float(os.getenv('MIN_ADX', '20'))
    MAX_STOCKS = int(os.getenv('MAX_STOCKS', '50'))

    # Technical filters
    RSI_MIN = int(os.getenv('RSI_MIN', '30'))
    RSI_MAX = int(os.getenv('RSI_MAX', '75'))

    # Minimum results threshold - only send if we found this many stocks
    MIN_RESULTS = int(os.getenv('MIN_RESULTS', '3'))


class TelegramNotifier:
    """Handle Telegram notifications"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram credentials not configured. Skipping notification.")
            return False

        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                },
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False

    def format_stock_result(self, result: Dict) -> str:
        """Format a single stock result for Telegram"""
        symbol = result['symbol'].replace('.NS', '').replace('^', '')
        price = result['current_price']
        volume_ratio = result['volume_ratio']
        rsi = result['rsi']
        adx = result['adx']

        # Get best pattern
        patterns = result.get('patterns', [])
        if patterns:
            best_pattern = max(patterns, key=lambda x: x['strength'])
            pattern_info = f"{best_pattern['type']} ({best_pattern['strength']:.0f}%)"
            confidence = best_pattern['confidence']
        else:
            pattern_info = "N/A"
            confidence = "N/A"

        # Format as HTML
        text = f"""
<b>{symbol}</b>
💰 Price: ₹{price:.2f}
📊 Volume: {volume_ratio:.1f}x
📈 RSI: {rsi:.1f}
⚡ ADX: {adx:.1f}
🎯 Pattern: {pattern_info}
🔒 Confidence: {confidence}
"""
        return text.strip()


class StockScanner:
    """Main scanner logic without Streamlit"""

    def __init__(self, config: Config):
        self.config = config
        self.scanner = ProfessionalPCSScanner()
        self.results = []

    def scan_stocks(self, stocks: List[str]) -> List[Dict]:
        """Scan a list of stocks and return results"""
        self.results = []

        logger.info(f"Starting scan of {len(stocks)} stocks")
        start_time = time.time()

        for i, symbol in enumerate(stocks):
            try:
                clean_symbol = symbol.replace('.NS', '').replace('^', '')

                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i + 1}/{len(stocks)} stocks analyzed")

                # Get stock data
                data = self.scanner.get_stock_data(symbol, period="3mo")
                if data is None or data.empty:
                    continue

                # Check volume
                volume_ok, volume_ratio, volume_details = self.scanner.check_volume_criteria(
                    data,
                    self.config.MIN_VOLUME_RATIO
                )
                if not volume_ok:
                    continue

                # Get technical indicators
                current_price = data['Close'].iloc[-1]
                current_rsi = data['RSI'].iloc[-1]
                current_adx = data['ADX'].iloc[-1]

                # Filter by ADX
                if current_adx < self.config.MIN_ADX:
                    continue

                # Filter by RSI range
                if not (self.config.RSI_MIN <= current_rsi <= self.config.RSI_MAX):
                    continue

                # Detect patterns
                filter_config = {
                    'min_volume_ratio': self.config.MIN_VOLUME_RATIO,
                    'rsi_min': self.config.RSI_MIN,
                    'rsi_max': self.config.RSI_MAX,
                    'adx_min': self.config.MIN_ADX,
                    'pattern_strength_min': self.config.MIN_PATTERN_STRENGTH,
                }

                patterns = self.scanner.detect_patterns(data, symbol, filter_config)
                if not patterns:
                    continue

                # Filter by pattern strength
                best_pattern = max(patterns, key=lambda x: x['strength'])
                if best_pattern['strength'] < self.config.MIN_PATTERN_STRENGTH:
                    continue

                # Create result
                stock_result = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'volume_ratio': volume_ratio,
                    'volume_details': volume_details,
                    'rsi': current_rsi,
                    'adx': current_adx,
                    'patterns': patterns,
                    'data': data,
                }

                self.results.append(stock_result)
                logger.debug(f"Added {clean_symbol} to results (strength: {best_pattern['strength']:.0f}%)")

            except Exception as e:
                logger.debug(f"Error analyzing {symbol}: {str(e)}")
                continue

        elapsed = time.time() - start_time
        logger.info(f"Scan complete. Found {len(self.results)} qualifying stocks in {elapsed:.1f}s")

        # Sort by pattern strength
        self.results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

        return self.results

    def get_summary(self) -> str:
        """Get a summary of the scan results"""
        if not self.results:
            return "No qualifying stocks found"

        total_patterns = sum(len(r['patterns']) for r in self.results)
        avg_strength = sum(
            max(p['strength'] for p in r['patterns'])
            for r in self.results
        ) / len(self.results)

        high_confidence = sum(
            1 for r in self.results
            for p in r['patterns']
            if p['confidence'] == 'HIGH'
        )

        summary = f"""
📊 <b>Stock Scanner Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</b>

🎯 Total Stocks: {len(self.results)}
🔥 Total Patterns: {total_patterns}
💪 Avg Strength: {avg_strength:.1f}%
🏆 High Confidence: {high_confidence}

Filters Applied:
• Min Pattern Strength: {self.config.MIN_PATTERN_STRENGTH}%
• Min Volume Ratio: {self.config.MIN_VOLUME_RATIO}x
• Min ADX: {self.config.MIN_ADX}
• RSI Range: {self.config.RSI_MIN}-{self.config.RSI_MAX}
"""
        return summary.strip()


def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("NSE F&O Stock Scanner - Telegram Edition")
    logger.info("="*60)

    # Validate configuration
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.warning("⚠️  Telegram credentials not configured!")
        logger.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables")
        logger.info("Continuing with local analysis only (no Telegram notifications)")
        telegram_enabled = False
    else:
        telegram_enabled = True
        logger.info("✅ Telegram notifications enabled")

    # Initialize components
    scanner = StockScanner(Config)

    if telegram_enabled:
        notifier = TelegramNotifier(Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID)

    # Prepare stocks to scan
    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:Config.MAX_STOCKS]
    logger.info(f"Scanning {len(stocks_to_scan)} stocks from NSE F&O universe")

    # Run scan
    results = scanner.scan_stocks(stocks_to_scan)

    # Check if we have minimum results
    if len(results) < Config.MIN_RESULTS:
        logger.warning(f"Only {len(results)} stocks found, below minimum threshold of {Config.MIN_RESULTS}")
        logger.info("No notifications sent")
        return

    # Send summary to Telegram
    if telegram_enabled:
        logger.info("Sending results to Telegram...")

        # Send summary
        summary = scanner.get_summary()
        notifier.send_message(summary)

        # Send top stocks (limit to 10 to avoid message limits)
        top_results = results[:10]

        for i, result in enumerate(top_results, 1):
            try:
                message = f"<b>#{i} - {result['symbol'].replace('.NS', '')}</b>\n"
                message += notifier.format_stock_result(result)

                notifier.send_message(message)
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"Error sending stock result: {str(e)}")

        logger.info("✅ Results sent to Telegram successfully!")
    else:
        logger.info("Local results (no Telegram):")
        print(scanner.get_summary())
        print("\nTop 5 Stocks:")
        for i, result in enumerate(results[:5], 1):
            print(notifier.format_stock_result(result))

    # Save results to file
    results_file = f"/tmp/nsepcs_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        # Convert results to JSON-serializable format
        results_data = []
        for r in results:
            results_data.append({
                'symbol': r['symbol'],
                'price': float(r['current_price']),
                'volume_ratio': float(r['volume_ratio']),
                'rsi': float(r['rsi']),
                'adx': float(r['adx']),
                'patterns': [
                    {
                        'type': p['type'],
                        'strength': float(p['strength']),
                        'confidence': p['confidence'],
                    }
                    for p in r['patterns']
                ]
            })

        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Results saved to {results_file}")
    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")

    logger.info("="*60)
    logger.info("Scan complete!")
    logger.info("="*60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
