# NSE F&O PCS Scanner - Telegram Output Examples

## 📱 Sample Telegram Messages

### Message 1: Scan Header
```
📊 NSE F&O PCS Scan Results
2026-09-12 14:30 IST

✅ Stocks Found: 12
RSI Range: 30-75
ADX Min: 20
Pattern Strength Min: 65
────────────────────────────
```

### Message 2: Stock Results (Batch 1)
```
1. RELIANCE
   ₹2,850.25 | RSI: 45.2 | ADX: 28.5

2. TCS
   ₹3,420.10 | RSI: 52.8 | ADX: 35.2

3. INFY
   ₹2,145.50 | RSI: 48.3 | ADX: 30.1

4. HDFCBANK
   ₹1,920.75 | RSI: 51.5 | ADX: 32.7

5. ICICIBANK
   ₹1,185.30 | RSI: 46.9 | ADX: 26.4

6. SBIN
   ₹645.20 | RSI: 49.2 | ADX: 28.2

7. KOTAKBANK
   ₹3,545.80 | RSI: 50.1 | ADX: 31.6

8. AXISBANK
   ₹1,015.45 | RSI: 47.3 | ADX: 25.8

9. MARUTI
   ₹8,320.50 | RSI: 44.7 | ADX: 29.3

10. ASIANPAINT
    ₹3,125.90 | RSI: 53.2 | ADX: 34.1
```

### Message 3: Stock Results (Batch 2)
```
11. SUNPHARMA
    ₹845.30 | RSI: 48.5 | ADX: 27.9

12. TATAMOTORS
    ₹520.15 | RSI: 46.2 | ADX: 24.5
```

### Message 4: Scan Footer
```
────────────────────────────
✅ Scan completed at 14:35 IST
Total matches: 12
```

---

## 🎯 Understanding the Output

### Stock Information Format
```
N. SYMBOL
   ₹PRICE | RSI: VALUE | ADX: VALUE
```

**What each metric means:**

| Metric | Range | Interpretation |
|--------|-------|-----------------|
| **RSI** | 0-100 | Momentum indicator |
| | 0-30 | Oversold (potential bounce) |
| | 30-70 | Neutral zone |
| | 70-100 | Overbought (potential reversal) |
| **ADX** | 0-25 | Weak trend |
| | 25-50 | Moderate to strong trend |
| | 50+ | Very strong trend |

### Filter Criteria Shown
```
RSI Range: 30-75          ← Stocks between RSI 30-75
ADX Min: 20               ← Trend strength must be at least 20
Pattern Strength Min: 65  ← Technical patterns scoring 65+
```

---

## 📊 How to Use These Results

### 1. **For Put Credit Spreads (PCS)**
If RSI is around 50:
- Consider SHORT PUT spreads (more neutral)
- Strike selection: 5-8% OTM from current price

If RSI is 45-50:
- High probability trade
- Consider 5% OTM short strike, 10% OTM long strike

### 2. **For Entry Timing**
- High ADX (30+) = Strong trend, good entry
- Low ADX (<25) = Weak trend, skip
- RSI near support = Better entry point

### 3. **Risk Management**
- Max loss per trade = 2% of account
- Stop loss = 3% below entry
- Target profit = 20% of spread width

### 4. **Portfolio Management**
- Never hold more than 5 simultaneous spreads
- Max portfolio exposure = 20%
- Diversify across sectors

---

## 🔄 Typical Scan Sequence

```
Morning (After market open):
📊 NSE F&O PCS Scan Results
9:45 IST
Stocks Found: 8 ← Good entry opportunities forming

Afternoon (Market momentum):
📊 NSE F&O PCS Scan Results
1:30 IST
Stocks Found: 15 ← Peak opportunity window

Late afternoon (Consolidation):
📊 NSE F&O PCS Scan Results
3:00 IST
Stocks Found: 5 ← Filter out noise, only best setups
```

---

## 💡 Daily Routine Using Scanner

### 6:30 AM - Pre-market Analysis
- Set Telegram alerts ON
- Review previous day's trades
- Prepare filter settings

### 9:15 AM - Market Open
- First scan runs
- Review high-probability setups
- Note 2-3 candidates for entry

### 10:30 AM - Secondary Scan
- Check if patterns confirmed
- Enter first trades

### 1:30 PM - Peak Activity
- Scan for additional opportunities
- Manage existing positions
- Take profits on 50% targets

### 3:15 PM - Market Close
- Final scan
- Review day's trades
- Plan next day strategy

---

## 📈 Example Trade Flow

**Telegram Alert Received:**
```
1. RELIANCE
   ₹2,850.25 | RSI: 45.2 | ADX: 28.5
```

**Action Plan:**
1. Check current price (verify it matches alert)
2. Look at 15-min chart for entry pullback
3. Calculate strike prices:
   - Current: ₹2,850
   - 5% OTM: ₹2,707 (short put)
   - 10% OTM: ₹2,565 (long put)
4. Check option liquidity
5. Execute spread order
6. Set stop loss at ₹2,960 (3% above entry)

---

## ✅ Confirmation Checklist

Before acting on alerts:
- [ ] Is the stock liquid (high option volumes)?
- [ ] Does RSI value make sense for your strategy?
- [ ] Is ADX strong enough (20+)?
- [ ] Are option bid-ask spreads reasonable?
- [ ] Do you have capital available?
- [ ] Is your risk properly sized?

---

## 🚨 When to Skip a Stock

Even if scanner flags a stock, SKIP if:
- Option spreads are too wide
- Stock is announcing results within 2 weeks
- Recent major news/earnings
- Low trading volume
- ADX too low (<15)
- RSI in extreme zone (0-20 or 80-100)

---

## 📚 Further Learning

Recommended reading before implementing:
1. **Options Trading Basics** - Understand put spreads
2. **Technical Analysis** - RSI and ADX interpretation
3. **Risk Management** - Position sizing rules
4. **Paper Trading** - Practice before live

---

## 🎯 Sample Portfolio Using Alerts

**Account Size**: ₹5,00,000

**Position Sizing (2% rule)**:
- Max per trade: ₹10,000
- Typical spread width: ₹500-800
- 10-12 simultaneous spreads active

**Example Portfolio From One Day's Alerts**:
```
1. RELIANCE PCS - ₹10,000 risk
2. TCS PCS - ₹10,000 risk
3. INFY PCS - ₹10,000 risk
4. HDFC BANK PCS - ₹10,000 risk
5. MARUTI PCS - ₹9,000 risk
6. SUNPHARMA PCS - ₹8,000 risk

Total Capital at Risk: ₹57,000 (11.4% of account)
Expected Profit (if all 50% wins): ₹15,000 - ₹20,000
```

---

**Last Updated**: 2026-09-12
**Ready to Trade**: Yes, after Telegram setup
