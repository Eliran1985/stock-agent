import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from sectors import get_sp500

def get_all_tickers():
    """משתמש ב-S&P 500 כבסיס + סקטורים נוספים"""
    from sectors import SECTORS
    all_tickers = set()
    for tickers in SECTORS.values():
        all_tickers.update(tickers)
    return list(all_tickers)

def get_history(ticker, period="6mo"):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        market_cap = info.get("marketCap", 0)
        if market_cap < 1_000_000_000:
            return None, None
        hist = stock.history(period=period)
        if hist.empty or len(hist) < 60:
            return None, None
        hist.index = hist.index.tz_localize(None)
        return hist, info
    except Exception:
        return None, None

# ─────────────────────────────────────────
# סינון 1: שינוי כיוון מירידה לעלייה
# ─────────────────────────────────────────
def find_swing_points(hist):
    """מוצא שיאים ושפלים מקומיים"""
    highs = []
    lows = []
    closes = hist["Close"].values
    dates = hist.index

    for i in range(2, len(closes) - 2):
        if closes[i] > closes[i-1] and closes[i] > closes[i-2] and \
           closes[i] > closes[i+1] and closes[i] > closes[i+2]:
            highs.append((dates[i], closes[i]))
        if closes[i] < closes[i-1] and closes[i] < closes[i-2] and \
           closes[i] < closes[i+1] and closes[i] < closes[i+2]:
            lows.append((dates[i], closes[i]))

    return highs, lows

def check_trend_reversal(ticker):
    try:
        hist, info = get_history(ticker)
        if hist is None:
            return None

        three_months_ago = datetime.now() - timedelta(days=90)
        recent_cutoff = datetime.now() - timedelta(days=40)

        hist_old = hist[hist.index <= three_months_ago.strftime("%Y-%m-%d")]
        hist_recent = hist[hist.index >= recent_cutoff.strftime("%Y-%m-%d")]

        if len(hist_old) < 20 or len(hist_recent) < 10:
            return None

        # בדיקת ירידה בתקופה הישנה
        old_highs, old_lows = find_swing_points(hist_old)
        if len(old_highs) < 2 or len(old_lows) < 2:
            return None

        # שיאים ושפלים יורדים בתקופה הישנה
        old_highs_vals = [h[1] for h in old_highs[-3:]]
        old_lows_vals = [l[1] for l in old_lows[-3:]]
        downtrend = all(old_highs_vals[i] > old_highs_vals[i+1]
                       for i in range(len(old_highs_vals)-1))
        downtrend_lows = all(old_lows_vals[i] > old_lows_vals[i+1]
                            for i in range(len(old_lows_vals)-1))

        if not (downtrend and downtrend_lows):
            return None

        # בדיקת עלייה בתקופה האחרונה
        new_highs, new_lows = find_swing_points(hist_recent)
        if len(new_highs) < 2 or len(new_lows) < 2:
            return None

        new_highs_vals = [h[1] for h in new_highs[-3:]]
        new_lows_vals = [l[1] for l in new_lows[-3:]]
        uptrend = all(new_highs_vals[i] < new_highs_vals[i+1]
                     for i in range(len(new_highs_vals)-1))
        uptrend_lows = all(new_lows_vals[i] < new_lows_vals[i+1]
                          for i in range(len(new_lows_vals)-1))

        if not (uptrend and uptrend_lows):
            return None

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        avg_volume = int(hist["Volume"].mean())
        last_volume = int(hist.iloc[-1]["Volume"])
        volume_ratio = round((last_volume / avg_volume) * 100, 0)

        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "volume_ratio": volume_ratio,
            "market_cap_B": round(info.get("marketCap", 0) / 1e9, 2),
            "signal": "Trend Reversal"
        }
    except Exception:
        return None

# ─────────────────────────────────────────
# סינון 2: פריצת קו התנגדות
# ─────────────────────────────────────────
def check_resistance_breakout(ticker):
    try:
        hist, info = get_history(ticker)
        if hist is None:
            return None

        three_days_ago = hist.index[-3] if len(hist) >= 3 else hist.index[0]
        three_months_ago = datetime.now() - timedelta(days=90)

        hist_resistance = hist[
            (hist.index >= three_months_ago.strftime("%Y-%m-%d")) &
            (hist.index < three_days_ago)
        ]
        hist_breakout = hist[hist.index >= three_days_ago]

        if hist_resistance.empty or hist_breakout.empty:
            return None

        # מציאת קו התנגדות עם לפחות 3 נגיעות מפוזרות
        resistance = None
        best_touches = 0
        highs = hist_resistance["High"].values
        dates = hist_resistance.index

        for price in highs:
            touch_dates = [dates[j] for j, h in enumerate(highs)
                          if abs(h - price) / price <= 0.02]
            if len(touch_dates) < 3:
                continue
            touch_dates_sorted = sorted(touch_dates)
            valid = [touch_dates_sorted[0]]
            for d in touch_dates_sorted[1:]:
                if (d - valid[-1]).days >= 10:
                    valid.append(d)
            if len(valid) >= 3 and len(valid) > best_touches:
                best_touches = len(valid)
                resistance = price

        if resistance is None:
            return None

        avg_volume = hist_resistance["Volume"].mean()
        breakout_candles = hist_breakout[hist_breakout["Close"] > resistance * 1.02]
        if breakout_candles.empty:
            return None

        breakout_date = breakout_candles.index[0]
        breakout_volume = hist_breakout.loc[breakout_date, "Volume"]
        volume_ratio = round((breakout_volume / avg_volume) * 100, 0)

        if volume_ratio < 130:
            return None

        current_price = info.get("currentPrice") or info.get("regularMarketPrice")

        return {
            "ticker": ticker,
            "price": round(current_price, 2),
            "resistance": round(resistance, 2),
            "breakout_date": breakout_date.strftime("%d/%m/%Y"),
            "volume_ratio": volume_ratio,
            "market_cap_B": round(info.get("marketCap", 0) / 1e9, 2),
            "signal": "Resistance Breakout"
        }
    except Exception:
        return None

# ─────────────────────────────────────────
# סינון 3: Cup and Handle
# ─────────────────────────────────────────
def check_cup_and_handle(ticker):
    try:
        hist, info = get_history(ticker, period="6mo")
        if hist is None or len(hist) < 60:
            return None

        closes = hist["Close"].values
        n = len(closes)

        # Cup: ירידה של לפחות 15% ואז התאוששות חזרה לרמה המקורית
        cup_start = closes[:n//2]
        cup_bottom_idx = np.argmin(cup_start)
        cup_bottom = cup_start[cup_bottom_idx]
        cup_left = cup_start[0]
        cup_right = closes[n//2]

        # בדיקת עומק הכוס — בין 15% ל-50%
        depth = (cup_left - cup_bottom) / cup_left
        if not (0.15 <= depth <= 0.50):
            return None

        # בדיקת התאוששות — הצד הימני חייב להיות תוך 5% מהצד השמאלי
        recovery = abs(cup_right - cup_left) / cup_left
        if recovery > 0.05:
            return None

        # Handle: ירידה קטנה של 5-15% אחרי הכוס
        handle = closes[n//2:]
        handle_high = handle[0]
        handle_low = np.min(handle[:len(handle)//2])
        handle_depth = (handle_high - handle_low) / handle_high
        if not (0.05 <= handle_depth <= 0.15):
            return None

        # פריצה: המחיר הנוכחי גבוה מהצד השמאלי של הכוס
        current_price = closes[-1]
        if current_price <= cup_left * 1.01:
            return None

        # נפח גבוה בפריצה
        avg_volume = hist["Volume"].mean()
        last_volume = hist["Volume"].iloc[-1]
        volume_ratio = round((last_volume / avg_volume) * 100, 0)
        if volume_ratio < 130:
            return None

        current_price_info = info.get("currentPrice") or info.get("regularMarketPrice")

        return {
            "ticker": ticker,
            "price": round(current_price_info, 2),
            "cup_depth_pct": round(depth * 100, 1),
            "volume_ratio": volume_ratio,
            "market_cap_B": round(info.get("marketCap", 0) / 1e9, 2),
            "signal": "Cup & Handle"
        }
    except Exception:
        return None

# ─────────────────────────────────────────
# הרצת כל הסינונים
# ─────────────────────────────────────────
def scan_signals():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    print(f"\nSignal scan started: {now.strftime('%H:%M:%S')}")

    tickers = get_all_tickers()
    print(f"Scanning {len(tickers)} stocks for signals...")

    reversals, breakouts, cups = [], [], []

    for i, ticker in enumerate(tickers):
        if i % 50 == 0:
            print(f"Progress: {i}/{len(tickers)}")

        r = check_trend_reversal(ticker)
        if r:
            reversals.append(r)

        b = check_resistance_breakout(ticker)
        if b:
            breakouts.append(b)

        c = check_cup_and_handle(ticker)
        if c:
            cups.append(c)

    # מיון לפי volume ולקיחת top 5
    def top5(lst):
        lst.sort(key=lambda x: x["volume_ratio"], reverse=True)
        return lst[:5]

    return {
        "reversals": top5(reversals),
        "breakouts": top5(breakouts),
        "cups": top5(cups),
    }, now

if __name__ == "__main__":
    results, ts = scan_signals()
    for signal_type, stocks in results.items():
        print(f"\n=== {signal_type.upper()} ===")
        for s in stocks:
            print(s)