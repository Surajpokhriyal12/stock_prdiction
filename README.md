# StockSense — Stock Prediction Website

A stock trend analysis & prediction web app built with **FastAPI** (Python backend) and a modern HTML/JS frontend.

## Features
- 📈 Interactive price history chart with moving averages (MA7, MA20, MA50)
- 🔮 14-day price prediction using linear trend analysis
- 📊 RSI (Relative Strength Index) chart
- 🟢 Bullish / Bearish / Neutral signal badge
- 📦 Key stats: P/E ratio, Market Cap, 52-week high/low
- ⚡ Fast — powered by Yahoo Finance via `yfinance`

## Project Structure
```
stock_app/
├── main.py            # FastAPI backend
├── requirements.txt   # Python dependencies
├── static/
│   └── index.html     # Frontend (HTML + Chart.js)
└── README.md
```

## Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Open in browser
```
http://localhost:8000
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves the frontend
| `GET /api/stock/{ticker}?period=6mo` | Returns stock data + predictions |

### Period options: `3mo`, `6mo`, `1y`, `2y`

### Example API call:
```
GET /api/stock/AAPL?period=6mo
```

## Prediction Method

The app uses **simple linear regression** on historical closing prices to extrapolate future prices 14 days ahead.

Trend signals are based on:
- **Moving Average crossover** (MA7 vs MA20)
- **Linear slope direction** (upward or downward)
- **RSI** displayed for overbought/oversold context

> ⚠️ This tool is for educational purposes only. Not financial advice.
# stock_prdiction
this is a web app which help us to read and predict the price of any stock.
