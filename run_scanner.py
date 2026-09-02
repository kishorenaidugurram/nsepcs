#!/usr/bin/env python3
"""
Standalone NSE F&O Stock Scanner - Runs independently and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime
import pytz
import requests
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the scanner from streamlit app
sys.path.insert(0, '/home/user/nsepcs')
from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE


class TelegramNotifier:
    """Handle sending messages to Telegram"""

    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, message):
        """Send a message to Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"❌ Failed to send Telegram message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending Telegram message: {str(e)}")
            return False

    def send_document(self, file_path, caption="Stock Scan Results"):
        """Send a file to Telegram"""
        try:
            url = f"{self.base_url}/sendDocument"

            with open(file_path, 'rb') as f:
                files = {'document': f}
                payload = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'Markdown'
                }
                response = requests.post(url, files=files, data=payload, timeout=30)

            if response.status_code == 200:
                logger.info("✅ File sent to Telegram successfully")
                return True
            else:
                logger.error(f"❌ Failed to send file to Telegram: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending file to Telegram: {str(e)}")
            return False


def load_config():
    """Load configuration from file or environment"""
    config_file = '/home/user/nsepcs/scanner_config.json'

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Replace environment variables
        bot_token = os.environ.get('TELEGRAM_BOT_TOKEN', config['telegram']['bot_token'])
        chat_id = os.environ.get('TELEGRAM_CHAT_ID', config['telegram']['chat_id'])

        if bot_token == '${TELEGRAM_BOT_TOKEN}' or not bot_token:
            logger.error("❌ TELEGRAM_BOT_TOKEN not configured")
            return None

        if chat_id == '${TELEGRAM_CHAT_ID}' or not chat_id:
            logger.error("❌ TELEGRAM_CHAT_ID not configured")
            return None

        config['telegram']['bot_token'] = bot_token
        config['telegram']['chat_id'] = chat_id

        logger.info("✅ Configuration loaded successfully")
        return config

    except Exception as e:
        logger.error(f"❌ Error loading configuration: {str(e)}")
        return None


def run_stock_scan(config, scanner):
    """Run the stock scanning analysis"""
    logger.info("🚀 Starting stock scan...")

    stocks_to_scan = COMPLETE_NSE_FO_UNIVERSE[:config['scanner']['max_stocks']]
    results = []

    filters = {
        'stocks_to_scan': stocks_to_scan,
        'rsi_min': config['scanner']['rsi_min'],
        'rsi_max': config['scanner']['rsi_max'],
        'adx_min': config['scanner']['adx_min'],
        'pattern_strength_min': config['scanner']['pattern_strength_min'],
        'min_volume_ratio': config['scanner']['volume_ratio'],
        'volume_breakout_ratio': config['scanner']['volume_breakout_ratio'],
        'lookback_days': config['scanner']['lookback_days'],
        'ma_support': config['scanner']['ma_support'],
        'ma_type': config['scanner']['ma_type'],
        'ma_tolerance': config['scanner']['ma_tolerance'],
        'pattern_filters': config['scanner']['pattern_filters'],
        'pattern_priority': 'All Patterns (Comprehensive)',
        'analysis_mode': config['scanner']['analysis_mode'],
        'enable_daily_analysis': config['scanner']['enable_daily_analysis'],
        'enable_weekly_validation': config['scanner']['enable_weekly_validation'],
    }

    # Scan stocks
    for i, symbol in enumerate(stocks_to_scan):
        try:
            clean_symbol = symbol.replace('.NS', '')
            logger.info(f"📊 Analyzing {clean_symbol} ({i+1}/{len(stocks_to_scan)})")

            # Get stock data
            data = scanner.get_stock_data(symbol, period="3mo")
            if data is None:
                continue

            # Check volume criteria
            volume_ok, volume_ratio, volume_details = scanner.check_volume_criteria(data, filters['min_volume_ratio'])
            if not volume_ok:
                continue

            # Detect patterns
            patterns = scanner.detect_patterns(data, symbol, filters)
            if not patterns:
                continue

            # Get current metrics
            current_price = data['Close'].iloc[-1]
            current_rsi = data['RSI'].iloc[-1]
            current_adx = data['ADX'].iloc[-1]

            # Create result
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
            logger.info(f"✅ Found {len(patterns)} pattern(s) in {clean_symbol}")

        except Exception as e:
            logger.warning(f"⚠️  Error analyzing {symbol}: {str(e)}")
            continue

    logger.info(f"✅ Scan complete! Found {len(results)} stocks with patterns")
    return results


def format_results_for_telegram(results):
    """Format scan results as Telegram message"""

    if not results:
        return "🔍 No stocks found matching the filter criteria."

    # Sort by pattern strength
    results.sort(key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Create header
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M IST')

    message = f"""
🎯 **NSE F&O Stock Scanner Results**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date/Time: {current_time}
📊 Stocks Found: {len(results)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    # Add stock details
    for idx, result in enumerate(results[:20], 1):  # Limit to top 20
        max_strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

        patterns_list = ', '.join([p['type'][:20] for p in result['patterns'][:2]])

        message += f"""`{idx}. {result['clean_symbol']}`
   Price: ₹{result['current_price']:.2f} | Vol: {result['volume_ratio']:.1f}x
   RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}
   Confidence: {confidence} ({max_strength:.0f}%)
   Patterns: {patterns_list}

"""

    # Add footer
    message += """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ *Disclaimer:* This analysis is for educational purposes only.
Always consult with a financial advisor before trading.
📈 For detailed analysis, visit the live app.
"""

    return message


def create_excel_export(results):
    """Create Excel file with results"""
    try:
        data = []
        for result in results:
            max_strength = max(p['strength'] for p in result['patterns'])
            confidence = 'HIGH' if max_strength >= 85 else 'MEDIUM' if max_strength >= 70 else 'LOW'

            data.append({
                'Symbol': result['clean_symbol'],
                'Price': result['current_price'],
                'Volume Ratio': result['volume_ratio'],
                'RSI': result['rsi'],
                'ADX': result['adx'],
                'Confidence': confidence,
                'Strength %': max_strength,
                'Pattern Count': len(result['patterns']),
                'Patterns': ', '.join([p['type'] for p in result['patterns']])
            })

        df = pd.DataFrame(data)

        # Create Excel file
        ist = pytz.timezone('Asia/Kolkata')
        timestamp = datetime.now(ist).strftime('%Y%m%d_%H%M%S')
        file_path = f'/tmp/nse_scanner_results_{timestamp}.xlsx'

        df.to_excel(file_path, index=False, sheet_name='Stock Scan Results')
        logger.info(f"✅ Excel file created: {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"❌ Error creating Excel file: {str(e)}")
        return None


def main():
    logger.info("=" * 60)
    logger.info("🚀 NSE F&O Stock Scanner - Telegram Edition")
    logger.info("=" * 60)

    # Load configuration
    config = load_config()
    if not config:
        logger.error("❌ Failed to load configuration. Exiting.")
        return False

    # Initialize Telegram notifier
    telegram = TelegramNotifier(
        config['telegram']['bot_token'],
        config['telegram']['chat_id']
    )

    # Send start notification
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S IST')
    telegram.send_message(f"🚀 Starting NSE F&O scanner at {current_time}...")

    # Initialize scanner
    scanner = ProfessionalPCSScanner()

    # Run scan
    try:
        results = run_stock_scan(config, scanner)
    except Exception as e:
        logger.error(f"❌ Error during scan: {str(e)}")
        telegram.send_message(f"❌ Scanner error: {str(e)}")
        return False

    if not results:
        logger.warning("⚠️ No stocks found matching criteria")
        telegram.send_message("⚠️ No stocks found matching the filter criteria.")
        return True

    # Format and send main results message
    telegram_message = format_results_for_telegram(results)
    telegram.send_message(telegram_message)

    # Create and send Excel export
    excel_file = create_excel_export(results)
    if excel_file:
        telegram.send_document(
            excel_file,
            f"📊 Stock Scan Results - {len(results)} stocks found"
        )

    # Send completion message
    telegram.send_message(f"""
✅ *Scan Complete!*

📊 Summary:
• Stocks Analyzed: {config['scanner']['max_stocks']}
• Stocks With Patterns: {len(results)}
• Filters Used:
  - RSI: {config['scanner']['rsi_min']}-{config['scanner']['rsi_max']}
  - ADX Min: {config['scanner']['adx_min']}
  - Pattern Strength: {config['scanner']['pattern_strength_min']}%

🔗 View detailed charts: https://nse-fo-pcs-screener.streamlit.app

""")

    logger.info("✅ All done! Results sent to Telegram.")
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
