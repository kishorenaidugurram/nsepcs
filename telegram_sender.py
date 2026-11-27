"""Telegram sender for NSE PCS Scanner results"""
import requests
import json
from datetime import datetime
from telegram_config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, is_configured

def send_telegram_message(message: str, parse_mode: str = "HTML") -> bool:
    """
    Send a message to Telegram

    Args:
        message: Message text to send
        parse_mode: 'HTML' or 'Markdown' for formatting

    Returns:
        True if successful, False otherwise
    """
    if not is_configured():
        print("⚠️  Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode
        }

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print(f"✅ Message sent to Telegram successfully")
            return True
        else:
            print(f"❌ Failed to send Telegram message: {response.status_code}")
            print(response.text)
            return False

    except Exception as e:
        print(f"❌ Error sending Telegram message: {str(e)}")
        return False

def format_stock_results(results: list, timestamp: str = None) -> str:
    """
    Format stock results for Telegram message

    Args:
        results: List of stock result dictionaries
        timestamp: Optional timestamp

    Returns:
        Formatted HTML message for Telegram
    """
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not results:
        return "❌ No stocks found matching the filter criteria"

    # Create header
    header = f"""
<b>🎯 NSE PCS Scanner Results</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
📅 <b>Timestamp:</b> {timestamp}
📊 <b>Stocks Found:</b> {len(results)}

<b>Top Qualifying Stocks:</b>
"""

    # Sort by strength
    sorted_results = sorted(results, key=lambda x: max(p['strength'] for p in x['patterns']), reverse=True)

    # Add top 20 stocks (Telegram has message length limits)
    stocks_list = ""
    for i, result in enumerate(sorted_results[:20], 1):
        symbol = result['symbol'].replace('.NS', '').replace('^', '')
        price = result['current_price']
        volume_ratio = result['volume_ratio']
        rsi = result['rsi']
        adx = result['adx']
        strength = max(p['strength'] for p in result['patterns'])
        confidence = 'HIGH' if strength >= 85 else 'MEDIUM' if strength >= 70 else 'LOW'

        # Determine emoji based on strength
        emoji = "🟢" if strength >= 85 else "🟡" if strength >= 70 else "🔴"

        stocks_list += f"""
{i}. {emoji} <b>{symbol}</b>
   💰 ₹{price:.2f} | 📊 Vol: {volume_ratio:.1f}x | RSI: {rsi:.0f} | ADX: {adx:.0f}
   💪 Strength: {strength:.0f}% | {confidence}
"""

    # Add footer
    footer = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Patterns Found: {sum(len(r['patterns']) for r in results)}
✨ High Confidence Stocks: {sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')}
📱 Sent from NSE PCS Scanner
"""

    if len(sorted_results) > 20:
        footer = f"""
... and {len(sorted_results) - 20} more stocks
━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Total Patterns Found: {sum(len(r['patterns']) for r in results)}
✨ High Confidence Stocks: {sum(1 for r in results for p in r['patterns'] if p['confidence'] == 'HIGH')}
📱 Sent from NSE PCS Scanner
"""

    return header + stocks_list + footer

def send_stock_results(results: list) -> bool:
    """
    Send formatted stock results to Telegram

    Args:
        results: List of stock result dictionaries

    Returns:
        True if successful, False otherwise
    """
    message = format_stock_results(results)
    return send_telegram_message(message)

def send_error_notification(error_message: str) -> bool:
    """
    Send error notification to Telegram

    Args:
        error_message: Error message to send

    Returns:
        True if successful, False otherwise
    """
    message = f"""
<b>❌ NSE PCS Scanner Error</b>
<b>━━━━━━━━━━━━━━━━━━━━━━━━━━━</b>
📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<code>{error_message}</code>
"""
    return send_telegram_message(message)
