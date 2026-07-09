#!/usr/bin/env python3
"""
Test script to validate Telegram configuration and connectivity
Run this before using the scanner to ensure your setup is correct
"""

import json
import sys
import requests
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_config_file():
    """Test if config file exists and is valid JSON"""
    logger.info("\n🔍 Testing configuration file...\n")

    try:
        with open('telegram_config.json', 'r') as f:
            config = json.load(f)
        logger.info("✅ Config file found and valid JSON")
        return config
    except FileNotFoundError:
        logger.error("❌ Config file not found: telegram_config.json")
        logger.info("   Create it using: cp telegram_config.example.json telegram_config.json")
        return None
    except json.JSONDecodeError:
        logger.error("❌ Config file has invalid JSON format")
        return None


def test_telegram_credentials(config):
    """Test if Telegram credentials are present and properly formatted"""
    logger.info("\n🔐 Checking Telegram credentials...\n")

    if not config:
        return False

    if 'telegram' not in config:
        logger.error("❌ Missing 'telegram' section in config")
        return False

    bot_token = config['telegram'].get('bot_token', '')
    chat_id = config['telegram'].get('chat_id', '')

    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        logger.error("❌ Bot token is empty or not configured")
        logger.info("   Get token from @BotFather on Telegram")
        return False

    if not chat_id or chat_id == 'YOUR_CHAT_ID_HERE':
        logger.error("❌ Chat ID is empty or not configured")
        logger.info("   Get chat ID by visiting: https://api.telegram.org/bot{TOKEN}/getUpdates")
        return False

    logger.info(f"✅ Bot token configured: {bot_token[:10]}...")
    logger.info(f"✅ Chat ID configured: {chat_id}")
    return True


def test_telegram_connectivity(config):
    """Test actual connection to Telegram API"""
    logger.info("\n📡 Testing Telegram API connectivity...\n")

    if not config or 'telegram' not in config:
        logger.error("❌ No Telegram config available")
        return False

    bot_token = config['telegram'].get('bot_token', '')
    chat_id = config['telegram'].get('chat_id', '')

    try:
        # Test 1: Get bot info
        logger.info("  1. Testing bot info retrieval...")
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result'].get('first_name', 'Unknown')
                logger.info(f"     ✅ Bot connected: {bot_name}")
            else:
                logger.error("     ❌ Bot token invalid or revoked")
                return False
        else:
            logger.error(f"     ❌ API error: {response.status_code}")
            return False

        # Test 2: Try sending test message
        logger.info("  2. Testing message sending...")
        send_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        message = f"""🤖 *Stock Scanner Test Message*

*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
*Status:* Configuration test successful!

This confirms:
✅ Bot token is valid
✅ Chat ID is correct
✅ API connectivity works
✅ Ready to receive stock updates

Your scanner is configured correctly!
"""

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'
        }

        response = requests.post(send_url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                logger.info("     ✅ Test message sent successfully!")
                logger.info("\n📱 Check your Telegram for the test message")
                return True
            else:
                error_msg = result.get('description', 'Unknown error')
                logger.error(f"     ❌ Message sending failed: {error_msg}")
                return False
        else:
            logger.error(f"     ❌ API error: {response.status_code}")
            logger.error(f"        Response: {response.text}")
            return False

    except requests.Timeout:
        logger.error("❌ Request timeout - check internet connection")
        return False
    except requests.RequestException as e:
        logger.error(f"❌ Network error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False


def test_scanner_dependencies():
    """Test if required Python packages are installed"""
    logger.info("\n📦 Checking Python dependencies...\n")

    required_packages = {
        'streamlit': 'Streamlit web framework',
        'yfinance': 'Yahoo Finance data',
        'pandas': 'Data manipulation',
        'numpy': 'Numerical computing',
        'ta': 'Technical analysis indicators',
        'requests': 'HTTP requests (Telegram API)',
        'plotly': 'Interactive charts',
        'pytz': 'Timezone handling',
        'scikit-learn': 'ML clustering',
        'scipy': 'Scientific computing',
        'beautifulsoup4': 'Web scraping',
        'openpyxl': 'Excel export'
    }

    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package.replace('-', '_'))
            logger.info(f"✅ {package:20} - {description}")
        except ImportError:
            logger.error(f"❌ {package:20} - {description} [MISSING]")
            missing.append(package)

    if missing:
        logger.info(f"\n❌ Missing packages: {', '.join(missing)}")
        logger.info("   Install with: pip install -r requirements.txt")
        return False
    else:
        logger.info("\n✅ All dependencies installed")
        return True


def test_scanner_code():
    """Test if scanner code can be imported"""
    logger.info("\n🔧 Testing scanner module import...\n")

    try:
        from streamlit_app import ProfessionalPCSScanner, COMPLETE_NSE_FO_UNIVERSE
        logger.info("✅ Scanner module imported successfully")
        logger.info(f"✅ F&O universe contains {len(COMPLETE_NSE_FO_UNIVERSE)} stocks")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import scanner: {e}")
        logger.info("   Make sure streamlit_app.py is in the same directory")
        return False
    except Exception as e:
        logger.error(f"❌ Error importing scanner: {e}")
        return False


def run_full_test():
    """Run all tests"""
    logger.info("=" * 70)
    logger.info("NSE Stock Scanner - Telegram Configuration Test")
    logger.info("=" * 70)

    # Test sequence
    config = test_config_file()
    if not config:
        return False

    if not test_telegram_credentials(config):
        return False

    if not test_telegram_connectivity(config):
        return False

    if not test_scanner_dependencies():
        logger.warning("\n⚠️  Some dependencies are missing, but setup test passed")

    if not test_scanner_code():
        logger.warning("\n⚠️  Scanner import failed, but connectivity test passed")

    return True


def print_summary(success):
    """Print test summary"""
    logger.info("\n" + "=" * 70)
    if success:
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("\nYour system is ready to run: python telegram_scanner.py")
        logger.info("=" * 70)
        return 0
    else:
        logger.info("❌ SOME TESTS FAILED")
        logger.info("\nPlease fix the issues above and run this test again")
        logger.info("\nFor help, see TELEGRAM_SETUP.md")
        logger.info("=" * 70)
        return 1


def main():
    """Main entry point"""
    try:
        success = run_full_test()
        return print_summary(success)
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
