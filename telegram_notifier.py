#!/usr/bin/env python3
"""
Telegram Notifier for NSE F&O PCS Screener
Sends stock screening results to Telegram
"""

import os
import requests
from datetime import datetime
from typing import List, Dict

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        """Initialize Telegram notifier with bot token and chat ID"""
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables must be set or passed as arguments"
            )

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured Telegram chat"""
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_stocks_summary(self, results: List[Dict]) -> bool:
        """Send a summary of screened stocks to Telegram"""
        if not results:
            message = "📊 <b>NSE F&O PCS Screener</b>\n\n❌ No stocks found matching the criteria today."
            return self.send_message(message)

        # Sort by pattern strength
        sorted_results = sorted(
            results,
            key=lambda x: max(p.get('strength', 0) for p in x.get('patterns', [])),
            reverse=True
        )

        # Build message
        message = f"📊 <b>NSE F&O PCS Screener Results</b>\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}\n\n"
        message += f"✅ <b>Found {len(sorted_results)} qualifying stocks</b>\n\n"

        # Add top 10 stocks
        for idx, result in enumerate(sorted_results[:10], 1):
            symbol = result.get('symbol', 'UNKNOWN').replace('.NS', '')
            price = result.get('current_price', 0)
            volume_ratio = result.get('volume_ratio', 0)
            rsi = result.get('rsi', 0)
            patterns = result.get('patterns', [])

            if patterns:
                best_pattern = max(patterns, key=lambda p: p.get('strength', 0))
                strength = best_pattern.get('strength', 0)
                confidence = best_pattern.get('confidence', 'UNKNOWN')
                pattern_type = best_pattern.get('type', 'Unknown')

                emoji = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"

                message += f"{idx}. <b>{symbol}</b> {emoji}\n"
                message += f"   💰 ₹{price:.2f} | 📊 {volume_ratio:.1f}x | RSI: {rsi:.1f}\n"
                message += f"   🎯 {pattern_type}\n"
                message += f"   💪 Strength: {strength:.0f}% | {confidence}\n\n"

        # Summary stats
        total_patterns = sum(len(r.get('patterns', [])) for r in sorted_results)
        avg_strength = sum(
            max(p.get('strength', 0) for p in r.get('patterns', []))
            for r in sorted_results
        ) / len(sorted_results) if sorted_results else 0
        high_conf = sum(
            1 for r in sorted_results
            for p in r.get('patterns', [])
            if p.get('confidence') == 'HIGH'
        )

        message += f"\n<b>📈 Summary Statistics:</b>\n"
        message += f"• Total Patterns: {total_patterns}\n"
        message += f"• Avg Strength: {avg_strength:.1f}%\n"
        message += f"• High Confidence: {high_conf}\n"

        return self.send_message(message)

    def send_detailed_stock_report(self, symbol: str, result: Dict) -> bool:
        """Send a detailed report for a specific stock"""
        symbol = result.get('symbol', symbol).replace('.NS', '')
        price = result.get('current_price', 0)
        volume_ratio = result.get('volume_ratio', 0)
        rsi = result.get('rsi', 0)
        adx = result.get('adx', 0)
        patterns = result.get('patterns', [])

        message = f"📊 <b>Detailed Report: {symbol}</b>\n\n"
        message += f"💰 <b>Price:</b> ₹{price:.2f}\n"
        message += f"📊 <b>Volume:</b> {volume_ratio:.1f}x (above avg)\n"
        message += f"📈 <b>RSI:</b> {rsi:.1f}\n"
        message += f"⚡ <b>ADX:</b> {adx:.1f}\n\n"

        if patterns:
            message += f"<b>🎯 Detected Patterns ({len(patterns)}):</b>\n\n"
            for pattern in patterns:
                pattern_type = pattern.get('type', 'Unknown')
                strength = pattern.get('strength', 0)
                confidence = pattern.get('confidence', 'UNKNOWN')
                success_rate = pattern.get('success_rate', 0)

                emoji = "🟢" if confidence == "HIGH" else "🟡" if confidence == "MEDIUM" else "🔴"
                message += f"{emoji} <b>{pattern_type}</b>\n"
                message += f"   Strength: {strength:.0f}% | Confidence: {confidence}\n"
                message += f"   Success Rate: {success_rate}%\n"

        return self.send_message(message)


if __name__ == "__main__":
    # Test notifier
    import sys

    # Check if credentials are configured
    if not os.getenv('TELEGRAM_BOT_TOKEN') or not os.getenv('TELEGRAM_CHAT_ID'):
        print("⚠️  Telegram credentials not configured!")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to enable Telegram notifications.")
        sys.exit(1)

    try:
        notifier = TelegramNotifier()
        test_message = "✅ Telegram notifier is configured and working!"
        if notifier.send_message(test_message):
            print("✅ Test message sent successfully")
        else:
            print("❌ Failed to send test message")
    except Exception as e:
        print(f"❌ Error: {e}")
