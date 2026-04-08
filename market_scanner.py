import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz
from sectors import SECTORS

def get_market_data(tickers, min_market_cap=1_000_000_000):
    """מושך נתוני מסחר עבור רשימת מניות"""
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="5d")

            if hist.empty:
                continue

            market_cap = info.get("marketCap", 0)
            if market_cap < min_market_cap:
                continue

            # נתוני יום המסחר האחרון
            last = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) >= 2 else None

            current_price = round(last["Close"], 2)
            volume = int(last["Volume"])
            avg_volume = int(hist["Volume"].mean())

            change_pct = 0
            if prev is not None and prev["Close"] > 0:
                change_pct = round(((last["Close"] - prev["Close"]) / prev["Close"]) * 100, 2)

            results.append({
                "ticker": ticker,
                "price": current_price,
                "change_pct": change_pct,
                "volume": volume,
                "avg_volume": avg_volume,
                "volume_ratio": round((volume / avg_volume) * 100, 0) if avg_volume > 0 else 0,
                "market_cap_B": round(market_cap / 1e9, 2),
            })
        except Exception:
            continue

    return pd.DataFrame(results)

def get_sector_tables(sector_name, tickers):
    """מחזיר 3 טבלאות לסקטור: Volume, Gainers, Losers"""
    print(f"  Scanning {sector_name} ({len(tickers)} stocks)...")
    df = get_market_data(tickers)

    if df.empty:
        return None, None, None

    top_volume = df.nlargest(10, "volume")[
        ["ticker", "price", "change_pct", "volume", "volume_ratio", "market_cap_B"]
    ].reset_index(drop=True)

    top_gainers = df.nlargest(10, "change_pct")[
        ["ticker", "price", "change_pct", "volume", "volume_ratio", "market_cap_B"]
    ].reset_index(drop=True)

    top_losers = df.nsmallest(10, "change_pct")[
        ["ticker", "price", "change_pct", "volume", "volume_ratio", "market_cap_B"]
    ].reset_index(drop=True)

    return top_volume, top_gainers, top_losers

def scan_all_sectors():
    """סורק את כל הסקטורים"""
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    print(f"\nMarket scan started: {now.strftime('%d/%m/%Y %H:%M:%S')} (Israel Time)")

    sector_results = {}
    for sector_name, tickers in SECTORS.items():
        volume, gainers, losers = get_sector_tables(sector_name, tickers)
        if volume is not None:
            sector_results[sector_name] = {
                "volume": volume,
                "gainers": gainers,
                "losers": losers,
            }

    return sector_results, now

if __name__ == "__main__":
    results, timestamp = scan_all_sectors()
    for sector, tables in results.items():
        print(f"\n=== {sector} ===")
        print("Top Volume:")
        print(tables["volume"].to_string(index=False))