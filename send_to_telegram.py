#!/usr/bin/env python3
"""
NSE PCS Scanner - Simple Telegram Reporter
Extracts and sends scan results to Telegram
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import pytz
import sys
import os

class SimpleTelegramReporter:
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram reporter"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api = f"https://api.telegram.org/bot{bot_token}"
        self.ist = pytz.timezone('Asia/Kolkata')

    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
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

    def send_scan_results(self, csv_path: str = None, stocks_list: list = None):
        """Send scan results to Telegram"""

        # If CSV path provided, read it
        if csv_path and os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)

                header = f"✅ <b>NSE PCS Scan Results</b>\n"
                header += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n"
                header += f"📊 Found {len(df)} stocks meeting criteria\n\n"

                # Send summary
                self.send_message(header)

                # Send top stocks
                if len(df) > 0:
                    top_msg = "<b>Top Stocks:</b>\n<code>"
                    for i, (_, row) in enumerate(df.head(20).iterrows(), 1):
                        top_msg += f"{i:2d}. {row.get('Symbol', 'N/A'):8s} | "
                        top_msg += f"₹{float(row.get('Price', 0)):8.2f} | "
                        top_msg += f"Str:{float(row.get('Pattern_Strength', 0)):3.0f}%\n"
                    top_msg += "</code>"

                    if len(df) > 20:
                        top_msg += f"\n... and {len(df) - 20} more stocks"

                    self.send_message(top_msg)

                    # Send full stock list
                    stock_list = " | ".join(df['Symbol'].astype(str).tolist())
                    list_msg = f"<b>All Stocks:</b>\n<code>{stock_list}</code>"
                    self.send_message(list_msg)

            except Exception as e:
                self.send_message(f"❌ Error reading results: {str(e)}")

        elif stocks_list:
            # Send provided stocks list
            msg = f"✅ <b>NSE PCS Scan Results</b>\n"
            msg += f"⏰ {datetime.now(self.ist).strftime('%Y-%m-%d %H:%M IST')}\n"
            msg += f"📊 Found {len(stocks_list)} stocks\n\n"
            msg += "<b>Symbols:</b>\n"
            msg += "<code>" + " | ".join(stocks_list[:50]) + "</code>"

            if len(stocks_list) > 50:
                msg += f"\n... and {len(stocks_list) - 50} more"

            self.send_message(msg)
        else:
            self.send_message("❌ No results to send")


def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python send_to_telegram.py <BOT_TOKEN> <CHAT_ID> [CSV_FILE]")
        print("\nExample: python send_to_telegram.py 123456:ABC-DEF 987654321 /path/to/results.csv")
        sys.exit(1)

    bot_token = sys.argv[1]
    chat_id = sys.argv[2]
    csv_file = sys.argv[3] if len(sys.argv) > 3 else None

    reporter = SimpleTelegramReporter(bot_token, chat_id)

    print("📤 Sending scan results to Telegram...")

    if csv_file:
        reporter.send_scan_results(csv_path=csv_file)
        print(f"✅ Results from {csv_file} sent to Telegram")
    else:
        print("❌ Please provide a CSV file with scan results")
        print("   Usage: python send_to_telegram.py <TOKEN> <CHAT_ID> <CSV_FILE>")

if __name__ == "__main__":
    main()
