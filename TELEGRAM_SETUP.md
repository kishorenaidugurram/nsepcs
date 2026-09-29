# Telegram Integration Setup

## Setup Instructions

To send stock scanning results to Telegram, follow these steps:

### 1. Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command: `/newbot`
3. Follow the prompts to:
   - Choose a name for your bot (e.g., "NSE Stock Scanner")
   - Choose a username (e.g., "nse_stock_scanner_bot")
4. BotFather will provide a **Bot Token** that looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### 2. Get Your Chat ID

1. Search for **@userinfobot** on Telegram
2. Send it any message
3. It will reply with your **User ID** (this is your Chat ID)

### 3. Set Environment Variables

Run these commands in your terminal:

```bash
export TELEGRAM_BOT_TOKEN='your_bot_token_here'
export TELEGRAM_CHAT_ID='your_chat_id_here'
```

For permanent setup (Linux/Mac), add to your `~/.bashrc` or `~/.zshrc`:

```bash
echo "export TELEGRAM_BOT_TOKEN='your_bot_token_here'" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID='your_chat_id_here'" >> ~/.bashrc
source ~/.bashrc
```

### 4. Verify Setup

```bash
python3 telegram_scanner.py --bot-token $TELEGRAM_BOT_TOKEN --chat-id $TELEGRAM_CHAT_ID --stocks 50
```

## Usage Examples

### Basic Scan (First 100 stocks)
```bash
python3 telegram_scanner.py
```

### Custom Parameters
```bash
# Scan first 50 stocks with minimum strength 70%
python3 telegram_scanner.py --stocks 50 --strength 70

# Export to Excel without Telegram
python3 telegram_scanner.py --stocks 100 --no-telegram
```

## Scheduled Execution

To run the scanner automatically, add to crontab:

```bash
# Run daily at 3:30 PM (market close)
30 15 * * 1-5 cd /home/user/nsepcs && python3 telegram_scanner.py

# Or with specific settings
30 15 * * 1-5 cd /home/user/nsepcs && python3 telegram_scanner.py --stocks 100 --strength 65
```

## Troubleshooting

### "Telegram credentials not provided"
- Verify that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set
- Check: `echo $TELEGRAM_BOT_TOKEN`
- Check: `echo $TELEGRAM_CHAT_ID`

### "Failed to send Telegram message"
- Verify bot token is correct
- Verify chat ID is correct
- Make sure the bot is not blocked
- Check internet connectivity

### No results found
- Try lower pattern strength: `--strength 60`
- Increase stocks to scan: `--stocks 150`
- Check if markets are closed

## Results

The scanner generates:
1. **Telegram Message** - Summary of stocks found
2. **Excel File** - Detailed analysis with all metrics
   - Symbol
   - Price
   - Technical indicators (RSI, ADX)
   - Volume ratio
   - Pattern strength
   - Detected patterns
   - Trading date

Results are saved as: `stock_scan_results_YYYYMMDD_HHMMSS.xlsx`
