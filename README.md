# 🤖 AI Stock Backtesting System

A comprehensive backtesting system that uses AI to suggest stocks and tests different trading strategies using real historical data.

## 📚 Documentation

We've created **two guides** to help you:

### 1. 📖 Complete Setup Guide (For First-Time Users)
**File**: `SETUP_GUIDE.md` (in artifacts folder)

This guide explains **everything** in simple language:
- What this system does
- How to install Python and packages
- How to get API keys (with screenshots)
- How to configure settings
- How to run backtests
- How to understand results
- Troubleshooting common problems

**Perfect for**: Beginners, first-time setup, detailed explanations

### 2. ⚡ Quick Start Cheat Sheet (For Quick Reference)
**File**: `QUICK_START.md` (in artifacts folder)

This is a **one-page reference** with:
- 3-minute setup steps
- Essential commands
- Settings comparison table
- Common errors and fixes
- Quick tips

**Perfect for**: Quick lookups, experienced users, reminders

## 🚀 Super Quick Start

```bash
# 1. Install packages
pip install -r requirements_real.txt

# 2. Add your API keys to config_real.py
# (Lines 9, 12, 17)

# 3. Test connection
python test_gemini.py

# 4. Run backtest
python run_real_backtest.py
```

## 📁 Project Structure

```
back testing/
├── config_real.py              # Main configuration file
├── run_real_backtest.py        # Single timeframe backtest
├── run_multi_timeframe.py      # Multi-timeframe backtest
├── test_gemini.py              # Test AI connection
├── requirements_real.txt       # Required packages
├── yahoo_data_fetcher.py       # Fetches stock data
├── finnhub_fetcher.py          # Fetches news data
├── mistral_ai_engine.py        # AI stock suggestions
├── gemini_ai_engine.py         # Backup AI engine
├── real_algorithm_engine.py    # Trading logic
├── stock_allocator.py          # Capital allocation
├── real_excel_reporter.py      # Excel report generator
└── results/                    # Output folder for Excel reports
```

## 🔑 Required API Keys

1. **Mistral AI**: https://console.mistral.ai/
2. **Gemini AI**: https://makersuite.google.com/app/apikey
3. **Finnhub**: https://finnhub.io/register

All are **FREE** with usage limits!

## 📊 What You Get

- ✅ Excel reports with all trades
- ✅ Performance metrics (win rate, P&L, etc.)
- ✅ Comparison of 5 AI strategies
- ✅ Daily breakdown of results
- ✅ Best/worst performing stocks

## ⚠️ Important Disclaimer

This is an **educational tool** for learning about algorithmic trading.

- Past performance does NOT guarantee future results
- Always test with paper money first
- Never invest more than you can afford to lose
- Consult a financial advisor before real trading

## 📞 Need Help?

1. **First-time setup?** → Read `SETUP_GUIDE.md` (in artifacts folder)
2. **Quick reference?** → Check `QUICK_START.md` (in artifacts folder)
3. **Having issues?** → See troubleshooting section in guides

## 📍 Documentation Location

The complete documentation files are located in:
```
C:\Users\advantix-user-002\.gemini\antigravity\brain\b86cace3-b0a2-437a-841c-a571794b903c\
├── SETUP_GUIDE.md      # Complete detailed guide
└── QUICK_START.md      # Quick reference cheat sheet
```

---

**Happy Backtesting! 🎉**

Remember: Learn first, trade later!
