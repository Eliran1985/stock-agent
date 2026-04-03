import yfinance as yf
import pandas as pd
from datetime import datetime

WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AMD",
    "NFLX", "CRM", "SHOP", "COIN", "PLTR", "ROKU", "SNAP",
    "UBER", "LYFT", "ABNB", "DASH", "RBLX", "U", "PATH", "AI"
]

def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 150:
            return None
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        pre_market_price = info.get("preMarketPrice")
        avg_volume = info.get("averageVolume")
        current_volume = info.get("preMarketVolume") or info.get("regularMarketVolume")
        market_cap = info.get("marketCap", 0)
        ma150 = hist["Close"].tail(150).mean()
        if not all([current_price, pre_market_price, avg_volume, current_volume]):
            return None
        pre_market_change = ((pre_market_price - current_price) / current_price) * 100
        volume_ratio = (current_volume / avg_volume) * 100
        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "pre_market_price": round(pre_market_price, 2),
            "pre_market_change": round(pre_market_change, 2),
            "volume_ratio": round(volume_ratio, 0),
            "market_cap_B": round(market_cap / 1e9, 2),
            "ma150": round(ma150, 2),
            "above_ma150": current_price > ma150
        }
    except Exception:
        return None

def scan_stocks():
    print(f"\nScanning started: {datetime.now().strftime('%H:%M:%S')}")
    results = []
    for ticker in WATCHLIST:
        data = get_stock_data(ticker)
        if data is None:
            continue
        if (data["pre_market_change"] > -50 and
            data["volume_ratio"] > 0 and
            data["market_cap_B"] >= 0.1):
            results.append(data)
            print(f"FOUND: {ticker}")
    return results

if __name__ == "__main__":
    results = scan_stocks()
    if results:
        df = pd.DataFrame(results)
        print("\nResults:")
        print(df.to_string(index=False))
    else:
        print("\nNo stocks match the criteria right now.")
