import yfinance as yf
import pandas as pd
from datetime import datetime
from scanner import scan_stocks, WATCHLIST, get_stock_data
import json

def generate_dashboard():
    results = scan_stocks()
    
    # נתונים לכל המניות ברשימה לצורך הצגה
    all_data = []
    for ticker in WATCHLIST:
        data = get_stock_data(ticker)
        if data:
            all_data.append(data)

    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    matches_html = ""
    if results:
        for r in results:
            matches_html += f"""
            <div class="stock-card match">
                <h2>{r['ticker']}</h2>
                <p>Pre-market change: <strong>+{r['pre_market_change']}%</strong></p>
                <p>Volume ratio: <strong>{r['volume_ratio']}%</strong></p>
                <p>Market cap: <strong>${r['market_cap_B']}B</strong></p>
                <p>Price: <strong>${r['current_price']}</strong></p>
                <p>MA150: <strong>${r['ma150']}</strong></p>
            </div>"""
    else:
        matches_html = "<p class='no-match'>No stocks match the criteria right now.</p>"

    html = f"""<!DOCTYPE html>
<html dir="ltr">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="300">
    <title>Stock Scanner</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: #0d1117; color: #e6edf3; padding: 20px; }}
        h1 {{ color: #58a6ff; }}
        .timestamp {{ color: #8b949e; margin-bottom: 20px; }}
        .stock-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px;
                      padding: 15px; margin: 10px; display: inline-block; min-width: 200px; }}
        .match {{ border-color: #3fb950; }}
        .match h2 {{ color: #3fb950; }}
        .no-match {{ color: #8b949e; font-size: 18px; }}
        strong {{ color: #58a6ff; }}
    </style>
</head>
<body>
    <h1>Stock Pre-Market Scanner</h1>
    <p class="timestamp">Last scan: {now}</p>
    <h2>Matching Stocks</h2>
    {matches_html}
</body>
</html>"""

    with open("dashboard.html", "w") as f:
        f.write(html)
    print(f"Dashboard updated: {now}")

if __name__ == "__main__":
    generate_dashboard()
    import webbrowser, os
    webbrowser.open("file://" + os.path.abspath("dashboard.html"))