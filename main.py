from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Stock Prediction API")

# Serve static files
'''app.mount("/static", StaticFiles(directory="static"), name="static")'''


@app.get("/")
async def root():
    BASE_DIR = Path(__file__).resolve().parent
    index_path = BASE_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="index.html not found")
    return FileResponse(str(index_path))


@app.get("/api/stock/{ticker}")
async def get_stock_data(ticker: str, period: str = "6mo"):
    """Fetch historical stock data and generate trend prediction."""
    try:
        stock = yf.Ticker(ticker.upper())
        hist = stock.history(period=period)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'")

        info = stock.info

        # Prepare historical data
        dates = hist.index.strftime("%Y-%m-%d").tolist()
        closes = hist["Close"].round(2).tolist()
        volumes = hist["Volume"].tolist()

        # Helper to convert NaN/numpy types to JSON-safe Python types
        def _sanitize_list(lst):
            out = []
            for v in lst:
                try:
                    if pd.isna(v):
                        out.append(None)
                    else:
                        # convert numpy types to native python
                        if isinstance(v, (np.floating, np.integer)):
                            out.append(v.item())
                        else:
                            out.append(v)
                except Exception:
                    out.append(None)
            return out

        # --- Trend Analysis ---
        closes_arr = np.array(closes)

        # Moving averages
        ma7 = pd.Series(closes_arr).rolling(7).mean().round(2).tolist()
        ma20 = pd.Series(closes_arr).rolling(20).mean().round(2).tolist()
        ma50 = pd.Series(closes_arr).rolling(50).mean().round(2).tolist()

        # RSI (14-period)
        delta = pd.Series(closes_arr).diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).round(2).tolist()

        # Linear regression trend for prediction (next 14 days)
        x = np.arange(len(closes_arr))
        coeffs = np.polyfit(x, closes_arr, 1)
        slope = coeffs[0]

        # Predict next 14 days
        pred_days = 14
        future_dates = [(datetime.now() + timedelta(days=i + 1)).strftime("%Y-%m-%d")
                for i in range(pred_days)]
        future_prices = [round(float(closes_arr[-1] + slope * (i + 1)), 2)
                 for i in range(pred_days)]

        # Sanitize numeric lists for JSON serialization
        closes = _sanitize_list(closes)
        volumes = _sanitize_list(volumes)
        ma7 = _sanitize_list(ma7)
        ma20 = _sanitize_list(ma20)
        ma50 = _sanitize_list(ma50)
        rsi = _sanitize_list(rsi)
        future_prices = _sanitize_list(future_prices)

        # Trend signal
        # pick last non-null values
        last_ma7 = next((v for v in reversed(ma7) if v is not None), None)
        last_ma20 = next((v for v in reversed(ma20) if v is not None), None)
        last_rsi = next((v for v in reversed(rsi) if v is not None), None)
        if last_ma7 is None:
            last_ma7 = closes[-1]
        if last_ma20 is None:
            last_ma20 = closes[-1]
        if last_rsi is None:
            last_rsi = 50

        if slope > 0 and last_ma7 > last_ma20:
            signal = "BULLISH"
            signal_color = "#00d48a"
        elif slope < 0 and last_ma7 < last_ma20:
            signal = "BEARISH"
            signal_color = "#ff4d6d"
        else:
            signal = "NEUTRAL"
            signal_color = "#f4a535"

        # Price change — use last two valid close values
        valid_closes = [c for c in closes if c is not None]
        if len(valid_closes) < 2:
            raise HTTPException(status_code=500, detail="Not enough valid close data for price change")
        price_change = round(valid_closes[-1] - valid_closes[-2], 2)
        price_change_pct = round((price_change / valid_closes[-2]) * 100, 2)

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName", ticker.upper()),
            "current_price": round(closes_arr[-1], 2),
            "price_change": price_change,
            "price_change_pct": price_change_pct,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "signal": signal,
            "signal_color": signal_color,
            "slope": round(slope, 4),
            "rsi": round(last_rsi, 1),
            "historical": {
                "dates": dates,
                "closes": closes,
                "volumes": volumes,
                "ma7": ma7,
                "ma20": ma20,
                "ma50": ma50,
                "rsi": rsi,
            },
            "prediction": {
                "dates": future_dates,
                "prices": future_prices,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
