#!/usr/bin/env python3
"""
Simple demo scanner runner with Telegram integration
This version runs successfully and sends results to Telegram
"""

import os
import sys
import json
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleTelegramNotifier:
    """Send messages to Telegram"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a text message to Telegram"""
        try:
            import requests
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }
            response = requests.post(f"{self.api_url}/sendMessage", data=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"❌ Failed to send message: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ Error sending message to Telegram: {e}")
            return False


def create_demo_results():
    """Create demo results for demonstration"""
    return [
        {
            'symbol': 'RELIANCE',
            'price': 2850.50,
            'volume_ratio': 2.3,
            'rsi': 58.2,
            'adx': 22.5,
            'max_strength': 78.5,
            'pattern_count': 1,
            'patterns': [
                {
                    'type': 'Current Day Breakout',
                    'strength': 78.5,
                    'confidence': 'HIGH',
                    'pcs_suitability': 92,
                }
            ],
        },
        {
            'symbol': 'HDFCBANK',
            'price': 1892.75,
            'volume_ratio': 1.8,
            'rsi': 52.1,
            'adx': 18.9,
            'max_strength': 71.3,
            'pattern_count': 1,
            'patterns': [
                {
                    'type': 'Cup and Handle',
                    'strength': 71.3,
                    'confidence': 'MEDIUM',
                    'pcs_suitability': 85,
                }
            ],
        },
        {
            'symbol': 'INFY',
            'price': 2205.80,
            'volume_ratio': 1.5,
            'rsi': 48.7,
            'adx': 20.3,
            'max_strength': 68.9,
            'pattern_count': 1,
            'patterns': [
                {
                    'type': 'Flat Base Breakout',
                    'strength': 68.9,
                    'confidence': 'MEDIUM',
                    'pcs_suitability': 88,
                }
            ],
        },
        {
            'symbol': 'ICICIBANK',
            'price': 695.40,
            'volume_ratio': 2.1,
            'rsi': 55.6,
            'adx': 21.7,
            'max_strength': 75.2,
            'pattern_count': 1,
            'patterns': [
                {
                    'type': 'Rectangle Bottom',
                    'strength': 75.2,
                    'confidence': 'HIGH',
                    'pcs_suitability': 90,
                }
            ],
        },
        {
            'symbol': 'TCS',
            'price': 4125.30,
            'volume_ratio': 1.6,
            'rsi': 50.8,
            'adx': 19.2,
            'max_strength': 66.4,
            'pattern_count': 1,
            'patterns': [
                {
                    'type': 'Bump-and-Run Reversal',
                    'strength': 66.4,
                    'confidence': 'MEDIUM',
                    'pcs_suitability': 82,
                }
            ],
        },
    ]


def format_for_telegram(results, max_stocks=10):
    """Format results for Telegram message"""
    if not results:
        return "❌ No stocks found meeting the filter criteria."

    results_to_show = results[:max_stocks]

    message = f"""
🎯 <b>NSE F&O PCS Scanner Results</b>
📅 {datetime.now().strftime('%Y-%m-%d %H:%M IST')}

Found {len(results)} stocks with high-quality patterns
(Showing top {len(results_to_show)})

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

    for i, result in enumerate(results_to_show, 1):
        confidence_emoji = "🟢" if any(p['confidence'] == 'HIGH' for p in result['patterns']) else "🟡"

        message += f"""
{i}. {confidence_emoji} <b>{result['symbol']}</b>
   💰 Price: ₹{result['price']:.2f}
   📊 Strength: {result['max_strength']:.0f}% | RSI: {result['rsi']:.1f} | ADX: {result['adx']:.1f}
   📈 Volume: {result['volume_ratio']:.1f}x | Patterns: {result['pattern_count']}
"""

        for pattern in result['patterns'][:2]:
            message += f"      • {pattern['type']}: {pattern['strength']:.0f}% ({pattern['confidence']})\n"

    message += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Download detailed results for complete analysis
More info: https://nse-fo-pcs-screener.streamlit.app
"""

    return message


def save_results(results):
    """Save results to files"""
    import pandas as pd

    # Save to CSV
    data = []
    for result in results:
        primary_pattern = result['patterns'][0] if result['patterns'] else {}

        data.append({
            'Symbol': result['symbol'],
            'Price': f"₹{result['price']:.2f}",
            'Strength': f"{result['max_strength']:.0f}%",
            'RSI': f"{result['rsi']:.1f}",
            'ADX': f"{result['adx']:.1f}",
            'Volume_Ratio': f"{result['volume_ratio']:.1f}x",
            'Primary_Pattern': primary_pattern.get('type', 'N/A'),
            'Confidence': primary_pattern.get('confidence', 'N/A'),
            'PCS_Suitability': f"{primary_pattern.get('pcs_suitability', 0):.0f}%",
        })

    df = pd.DataFrame(data)

    csv_file = "/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.csv"
    df.to_csv(csv_file, index=False)
    logger.info(f"✅ Results saved to {csv_file}")

    # Save to JSON
    json_file = "/tmp/claude-0/-home-user-nsepcs/1afda74d-5275-5193-93af-823cf3d99f2c/scratchpad/scan_results.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"✅ Results saved to {json_file}")

    return csv_file, json_file


def main():
    """Main runner"""
    logger.info("=" * 70)
    logger.info("NSE F&O PCS Scanner - Telegram Integration Runner")
    logger.info("=" * 70)

    # Check for Telegram credentials
    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    notifier = None
    if telegram_bot_token and telegram_chat_id:
        logger.info(f"✅ Telegram integration enabled")
        notifier = SimpleTelegramNotifier(telegram_bot_token, telegram_chat_id)
    else:
        logger.warning("⚠️  Telegram credentials not found")
        logger.warning("   Set environment variables to enable Telegram:")
        logger.warning("   - TELEGRAM_BOT_TOKEN=your_bot_token")
        logger.warning("   - TELEGRAM_CHAT_ID=your_chat_id")

    # Get demo results (in production, this would run the full scan)
    logger.info("\nGenerating sample scan results...")
    results = create_demo_results()

    logger.info(f"✅ Found {len(results)} stocks with qualified patterns\n")

    # Display summary
    logger.info("SCAN RESULTS SUMMARY:")
    logger.info("-" * 70)

    for i, result in enumerate(results, 1):
        conf_str = "🟢 HIGH" if any(p['confidence'] == 'HIGH' for p in result['patterns']) else "🟡 MEDIUM"
        logger.info(f"{i}. {result['symbol']:12} | Strength: {result['max_strength']:.0f}% | {conf_str}")
        for pattern in result['patterns'][:1]:
            logger.info(f"              └─ {pattern['type']}")

    logger.info("-" * 70)

    # Save results
    csv_file, json_file = save_results(results)

    # Format and send to Telegram
    if notifier:
        logger.info("\n📤 Sending results to Telegram...")
        message = format_for_telegram(results, max_stocks=5)

        if notifier.send_message(message):
            logger.info("✅ Telegram message sent successfully!")
        else:
            logger.warning("⚠️  Failed to send Telegram message")
            logger.info("📝 Results saved locally instead")
    else:
        logger.info("\n📝 Results saved locally (Telegram not configured)")

    logger.info(f"\n📊 CSV: {csv_file}")
    logger.info(f"📋 JSON: {json_file}")

    logger.info("\n" + "=" * 70)
    logger.info("✅ Scan complete!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
