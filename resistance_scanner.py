import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

def get_sp500_tickers():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
    df = pd.read_csv(url)
    return df["Symbol"].str.replace(".", "-").tolist()

def find_resistance_level(highs, tolerance=0.02, min_touches=4):
    """
    מוצא קו התנגדות — רמת מחיר שנגעו בה לפחות 4 פעמים
    עם פיזור של לפחות 2 שבועות בין הנגיעות
    """
    highs_array = highs.values
    dates = highs.index

    best_resistance = None
    best_touches = 0

    for i, price in enumerate(highs_array):
        touch_dates = []
        for j, h in enumerate(highs_array):
            if abs(h - price) / price <= tolerance:
                touch_dates.append(dates[j])

        if len(touch_dates) < min_touches:
            continue

        # וידוא שהנגיעות מפוזרות לפחות 2 שבועות אחת מהשניה
        touch_dates_sorted = sorted(touch_dates)
        valid_touches = [touch_dates_sorted[0]]
        for d in touch_dates_sorted[1:]:
            if (d - valid_touches[-1]).days >= 14:
                valid_touches.append(d)

        if len(valid_touches) >= min_touches:
            if len(valid_touches) > best_touches:
                best_touches = len(valid_touches)
                best_resistance = price

    return best_resistance

def check_resistance_breakout(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        market_cap = info.get("marketCap", 0)
        if market_cap < 1_000_000_000:
            return None

        hist = stock.history(period="6mo")
        if hist.empty or len(hist) < 60:
            return None

        hist.index = hist.index.tz_localize(None)

        # תקופת ההתנגדות — עד 3 ימי מסחר אחרונים
        three_days_ago = hist.index[-3] if len(hist) >= 3 else hist.index[0]
        three_months_ago = datetime.now() - timedelta(days=90)

        hist_resistance = hist[
            (hist.index >= three_months_ago.strftime("%Y-%m-%d")) &
            (hist.index < three_days_ago)
        ]
        hist_breakout = hist[hist.index >= three_days_ago]

        if hist_resistance.empty or hist_breakout.empty:
            return None

        # מציאת קו התנגדות עם לפחות 4 נגיעות מפוזרות
        resistance = find_resistance_level(hist_resistance["High"])
        if resistance is None:
            return None

        # בדיקת פריצה — סגירה של לפחות 3% מעל ההתנגדות
        avg_volume = hist_resistance["Volume"].mean()
        breakout_candles = hist_breakout[
            hist_breakout["Close"] > resistance * 1.03
        ]

        if breakout_candles.empty:
            return None

        # בדיקת נפח ביום הפריצה — לפחות 150% מהממוצע
        breakout_date = breakout_candles.index[0]
        breakout_volume = hist_breakout.loc[breakout_date, "Volume"]
        volume_ratio = (breakout_volume / avg_volume) * 100

        if volume_ratio < 150:
            return None

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        return {
            "ticker": ticker,
            "current_price": round(current_price, 2),
            "resistance": round(resistance, 2),
            "breakout_pct": round(((current_price - resistance) / resistance) * 100, 1),
            "breakout_date": breakout_date.strftime("%d/%m/%Y"),
            "volume_ratio": round(volume_ratio, 0),
            "market_cap_B": round(market_cap / 1e9, 2),
        }

    except Exception:
        return None

def scan_resistance_breakouts():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    print(f"\nResistance scan started: {now.strftime('%H:%M:%S')}")

    tickers = get_sp500_tickers()
    print(f"Scanning {len(tickers)} S&P 500 stocks...")

    results = []
    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(tickers)}")
        data = check_resistance_breakout(ticker)
        if data:
            results.append(data)
            print(f"BREAKOUT FOUND: {ticker}")

    # מיון לפי נפח ולקיחת 5 הראשונים
    results.sort(key=lambda x: x["volume_ratio"], reverse=True)
    return results[:5]

if __name__ == "__main__":
    results = scan_resistance_breakouts()
    if results:
        df = pd.DataFrame(results)
        print("\nTop 5 Resistance Breakouts by Volume:")
        print(df.to_string(index=False))
    else:
        print("\nNo resistance breakouts found.")