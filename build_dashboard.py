import yfinance as yf
import pandas as pd
import numpy as np
import json
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
from market_scanner import scan_all_sectors
from signal_scanner import scan_signals

def make_chart(ticker, signal_type, signal_data):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="6mo")
        hist.index = hist.index.tz_localize(None)
        if hist.empty:
            return "null"

        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=[str(d) for d in hist.index],
            open=hist["Open"].tolist(),
            high=hist["High"].tolist(),
            low=hist["Low"].tolist(),
            close=hist["Close"].tolist(),
            name=ticker,
            increasing_line_color="#26a69a",
            decreasing_line_color="#ef5350"
        ))

        colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(hist["Close"], hist["Open"])]
        fig.add_trace(go.Bar(
            x=[str(d) for d in hist.index],
            y=hist["Volume"].tolist(),
            name="Volume",
            marker_color=colors,
            opacity=0.25,
            yaxis="y2"
        ))

        shapes = []
        annotations = []

        if signal_type == "breakouts" and "resistance" in signal_data:
            resistance = float(signal_data["resistance"])
            shapes.append(dict(
                type="line", xref="paper", yref="y",
                x0=0, x1=1, y0=resistance, y1=resistance,
                line=dict(color="#FFD700", width=2, dash="dash")
            ))
            annotations.append(dict(
                xref="paper", yref="y",
                x=0.02, y=resistance,
                text=f"Resistance: ${resistance}",
                showarrow=False,
                font=dict(color="#FFD700", size=11),
                bgcolor="#0d1117",
                bordercolor="#FFD700"
            ))
            try:
                bd = datetime.strptime(signal_data["breakout_date"], "%d/%m/%Y")
                bd_str = bd.strftime("%Y-%m-%d")
                annotations.append(dict(
                    x=bd_str, y=resistance * 1.015,
                    text="▲ BREAKOUT",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="#00FF7F",
                    font=dict(color="#00FF7F", size=12, family="Arial Black"),
                    bgcolor="#0d1117",
                    bordercolor="#00FF7F",
                    arrowsize=1.5
                ))
            except Exception:
                pass

        elif signal_type == "cups":
            n = len(hist)
            mid = n // 2
            bottom_idx = hist["Close"][:mid].idxmin()
            annotations += [
                dict(x=str(hist.index[0]), y=float(hist["Close"].iloc[0]),
                     text="Cup Left", showarrow=False,
                     font=dict(color="#FFD700", size=10), bgcolor="#0d1117"),
                dict(x=str(bottom_idx), y=float(hist["Close"][bottom_idx]),
                     text="Bottom", showarrow=True, arrowcolor="#FFD700",
                     font=dict(color="#FFD700", size=10), bgcolor="#0d1117"),
                dict(x=str(hist.index[mid]), y=float(hist["Close"].iloc[mid]),
                     text="Handle", showarrow=False,
                     font=dict(color="#FF9800", size=10), bgcolor="#0d1117"),
            ]

        elif signal_type == "reversals":
            mid = len(hist) // 2
            shapes.append(dict(
                type="line", xref="x", yref="paper",
                x0=str(hist.index[mid]), x1=str(hist.index[mid]),
                y0=0, y1=1,
                line=dict(color="#FF9800", width=2, dash="dot")
            ))
            annotations.append(dict(
                x=str(hist.index[mid]), y=1,
                xref="x", yref="paper",
                text="Trend Change",
                showarrow=False,
                font=dict(color="#FF9800", size=11),
                bgcolor="#0d1117",
                bordercolor="#FF9800"
            ))

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            xaxis_rangeslider_visible=False,
            height=420,
            margin=dict(l=10, r=10, t=20, b=10),
            showlegend=False,
            shapes=shapes,
            annotations=annotations,
            yaxis=dict(side="right", gridcolor="#1e2a3a"),
            yaxis2=dict(overlaying="y", side="left", showgrid=False,
                        showticklabels=False,
                        range=[0, hist["Volume"].max() * 5]),
            xaxis=dict(gridcolor="#1e2a3a", type="category",
                       nticks=8, tickangle=-30),
            font=dict(color="#e6edf3", family="Segoe UI")
        )

        return json.dumps(json.loads(fig.to_json()))
    except Exception as e:
        print(f"Chart error for {ticker}: {e}")
        return "null"

def df_to_html(df, table_id):
    if df is None or df.empty:
        return "<p class='no-data'>No data available</p>"
    rows = ""
    for _, row in df.iterrows():
        change = row.get("change_pct", 0)
        change_class = "positive" if change > 0 else "negative" if change < 0 else ""
        change_str = f"+{change}%" if change > 0 else f"{change}%"
        vol_str = f"{int(row['volume']):,}" if "volume" in row else "—"
        vol_ratio = f"{int(row['volume_ratio'])}%" if "volume_ratio" in row else "—"
        rows += f"""<tr>
            <td class="ticker-cell">{row['ticker']}</td>
            <td>${row['price']}</td>
            <td class="{change_class}">{change_str}</td>
            <td>{vol_str}</td>
            <td>{vol_ratio}</td>
            <td>${row['market_cap_B']}B</td>
        </tr>"""
    return f"""<table class="data-table" id="{table_id}">
        <thead><tr>
            <th>Ticker</th><th>Price</th><th>Change</th>
            <th>Volume</th><th>Vol%</th><th>Mkt Cap</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>"""

def signal_card(stock, signal_type, chart_json):
    chart_id = f"chart_{stock['ticker']}_{signal_type}"
    extra = ""
    if signal_type == "breakouts":
        extra = f"""
        <span class='tag res-tag'>R: ${stock.get('resistance','—')}</span>
        <span class='tag date-tag'>📅 {stock.get('breakout_date','—')}</span>"""
    elif signal_type == "cups":
        extra = f"<span class='tag'>Depth: {stock.get('cup_depth_pct','—')}%</span>"

    return f"""<div class="signal-card">
        <div class="signal-header">
            <span class="signal-ticker">{stock['ticker']}</span>
            <span class="signal-price">${stock['price']}</span>
            <span class="tag vol-tag">Vol: {int(stock['volume_ratio'])}%</span>
            <span class="tag cap-tag">${stock['market_cap_B']}B</span>
            {extra}
            <button class="chart-btn" onclick="toggleChart('{chart_id}')">
                📈 Chart
            </button>
        </div>
        <div class="chart-container" id="{chart_id}" style="display:none;">
            <div id="{chart_id}_plot" style="width:100%;height:420px;"></div>
        </div>
        <script>
            window.__charts = window.__charts || {{}};
            window.__charts['{chart_id}'] = {chart_json};
        </script>
    </div>"""

def build_sectors_html(sector_results):
    html = ""
    icons = {"Space":"🚀","Energy":"⚡","Health":"🏥","Materials":"⚗️",
             "Banks":"🏦","Defense":"🛡️","S&P 500":"📊","Nasdaq 100":"💻"}
    for sector, tables in sector_results.items():
        sid = sector.replace(" ","_").replace("&","and").replace("/","_")
        icon = icons.get(sector, "📁")
        html += f"""<div class="sector-block">
            <div class="sector-header" onclick="toggleSector('{sid}')">
                <div class="sector-title">
                    <span class="sector-icon">{icon}</span>
                    <h2>{sector}</h2>
                </div>
                <span class="toggle-icon" id="icon_{sid}">▼</span>
            </div>
            <div class="sector-content" id="sector_{sid}">
                <div class="tables-grid">
                    <div class="table-block">
                        <h3 class="table-title volume-title">🔥 Top Volume</h3>
                        {df_to_html(tables['volume'], f'vol_{sid}')}
                    </div>
                    <div class="table-block">
                        <h3 class="table-title gainers-title">📈 Top Gainers</h3>
                        {df_to_html(tables['gainers'], f'gain_{sid}')}
                    </div>
                    <div class="table-block">
                        <h3 class="table-title losers-title">📉 Top Losers</h3>
                        {df_to_html(tables['losers'], f'loss_{sid}')}
                    </div>
                </div>
            </div>
        </div>"""
    return html

def build_signals_html(signal_results):
    config = {
        "reversals": ("🔄", "Trend Reversals", "Downtrend flipping to uptrend"),
        "breakouts": ("🚀", "Resistance Breakouts", "Price broke key resistance with high volume"),
        "cups": ("☕", "Cup & Handle", "Classic bullish continuation pattern"),
    }
    html = ""
    for signal_type, (icon, title, desc) in config.items():
        stocks = signal_results.get(signal_type, [])
        cards = ""
        for stock in stocks:
            chart_json = make_chart(stock["ticker"], signal_type, stock)
            cards += signal_card(stock, signal_type, chart_json)
        if not cards:
            cards = "<p class='no-data'>No signals found</p>"
        html += f"""<div class="signal-section">
            <div class="signal-section-header">
                <div class="signal-title-row">
                    <span class="signal-icon">{icon}</span>
                    <div>
                        <h2>{title}</h2>
                        <p class="signal-desc">{desc}</p>
                    </div>
                </div>
            </div>
            {cards}
        </div>"""
    return html

CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body {
    font-family: 'Segoe UI', system-ui, sans-serif;
    background: #060b14;
    color: #e6edf3;
    min-height: 100vh;
}
.header {
    background: linear-gradient(135deg, #0d1117 0%, #0f1923 100%);
    border-bottom: 1px solid #1e2d3d;
    padding: 18px 40px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky; top: 0; z-index: 100;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
}
.logo { display:flex; align-items:center; gap:14px; }
.logo-icon {
    width:42px; height:42px;
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    border-radius:10px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.3rem;
}
.header-left h1 {
    font-size:1.6rem; font-weight:800;
    background: linear-gradient(90deg, #79c0ff, #58a6ff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.header-left p { color:#8b949e; font-size:0.8rem; margin-top:2px; }
.timestamp {
    background: #0d1117;
    border: 1px solid #1e2d3d;
    border-radius:8px; padding:8px 16px;
    font-size:0.82rem; color:#8b949e;
}
.timestamp span { color:#58a6ff; font-weight:600; }
.nav-tabs {
    display:flex; gap:4px;
    padding:12px 40px;
    background:#0a0e1a;
    border-bottom:1px solid #1e2d3d;
}
.nav-tab {
    padding:8px 22px; border-radius:6px;
    cursor:pointer; font-size:0.88rem; font-weight:600;
    border:1px solid transparent;
    transition:all 0.2s; color:#8b949e; background:transparent;
}
.nav-tab:hover { color:#e6edf3; background:#161b22; }
.nav-tab.active {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color:white; border-color:#388bfd;
    box-shadow: 0 0 12px rgba(31,111,235,0.4);
}
.main { padding:28px 40px; max-width:1700px; margin:0 auto; }
.tab-content { display:none; }
.tab-content.active { display:block; }
.sector-block {
    background:#0d1117;
    border:1px solid #1e2d3d;
    border-radius:14px;
    margin-bottom:14px;
    overflow:hidden;
    transition: box-shadow 0.2s;
}
.sector-block:hover { box-shadow: 0 0 0 1px #388bfd44; }
.sector-header {
    display:flex; justify-content:space-between; align-items:center;
    padding:15px 24px; cursor:pointer;
    background: linear-gradient(90deg, #0f1923, #0d1117);
    transition:background 0.2s;
}
.sector-header:hover { background: linear-gradient(90deg, #161b22, #0f1923); }
.sector-title { display:flex; align-items:center; gap:12px; }
.sector-icon { font-size:1.3rem; }
.sector-header h2 { font-size:1rem; color:#79c0ff; font-weight:700; }
.toggle-icon { color:#58a6ff; font-size:0.9rem; transition:transform 0.3s; }
.sector-content { padding:20px; background:#080c14; }
.tables-grid {
    display:grid; grid-template-columns:repeat(3,1fr); gap:16px;
}
.table-block {
    background:#0d1117;
    border:1px solid #1e2d3d;
    border-radius:10px; padding:16px;
}
.table-title {
    font-size:0.85rem; font-weight:700;
    margin-bottom:12px; padding-bottom:8px;
    border-bottom:1px solid #1e2d3d;
}
.volume-title { color:#f0883e; }
.gainers-title { color:#3fb950; }
.losers-title { color:#f85149; }
.data-table { width:100%; border-collapse:collapse; font-size:0.8rem; }
.data-table th {
    text-align:left; padding:5px 8px;
    color:#6e7681; font-weight:600;
    border-bottom:1px solid #1e2d3d;
    text-transform:uppercase; font-size:0.72rem; letter-spacing:0.5px;
}
.data-table td { padding:6px 8px; border-bottom:1px solid #0a0e1a; }
.data-table tr:last-child td { border-bottom:none; }
.data-table tr:hover { background:#111820; }
.ticker-cell { font-weight:800; color:#58a6ff; letter-spacing:0.5px; }
.positive { color:#3fb950; font-weight:700; }
.negative { color:#f85149; font-weight:700; }
.signal-section {
    background:#0d1117;
    border:1px solid #1e2d3d;
    border-radius:14px;
    margin-bottom:20px;
    overflow:hidden;
}
.signal-section-header {
    padding:18px 24px;
    background: linear-gradient(90deg, #0f1923, #0d1117);
    border-bottom:1px solid #1e2d3d;
}
.signal-title-row { display:flex; align-items:center; gap:14px; }
.signal-icon { font-size:1.8rem; }
.signal-section-header h2 { font-size:1.1rem; color:#e6edf3; font-weight:800; }
.signal-desc { color:#8b949e; font-size:0.82rem; margin-top:3px; }
.signal-card {
    border-bottom:1px solid #1e2d3d;
    padding:14px 24px;
    transition:background 0.2s;
}
.signal-card:last-child { border-bottom:none; }
.signal-card:hover { background:#0a0e1a; }
.signal-header {
    display:flex; align-items:center; gap:10px; flex-wrap:wrap;
}
.signal-ticker {
    font-size:1.1rem; font-weight:800;
    color:#58a6ff; min-width:65px;
    letter-spacing:0.5px;
}
.signal-price { font-size:1rem; color:#e6edf3; font-weight:700; }
.tag {
    background:#111820;
    border:1px solid #1e2d3d;
    border-radius:5px; padding:3px 9px;
    font-size:0.76rem; color:#8b949e;
}
.vol-tag { color:#f0883e; border-color:#f0883e33; background:#1a1208; }
.cap-tag { color:#79c0ff; border-color:#79c0ff33; background:#0a1120; }
.res-tag { color:#FFD700; border-color:#FFD70033; background:#1a1500; }
.date-tag { color:#a371f7; border-color:#a371f733; background:#110d1a; }
.chart-btn {
    margin-left:auto;
    background: linear-gradient(135deg, #1f6feb, #388bfd);
    color:white; border:none; border-radius:7px;
    padding:6px 16px; cursor:pointer;
    font-size:0.82rem; font-weight:600;
    transition:all 0.2s;
    box-shadow: 0 2px 8px rgba(31,111,235,0.3);
}
.chart-btn:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff);
    box-shadow: 0 4px 16px rgba(31,111,235,0.5);
    transform: translateY(-1px);
}
.chart-container {
    margin-top:14px;
    border-radius:10px; overflow:hidden;
    border:1px solid #1e2d3d;
    background:#0d1117;
}
.no-data { color:#8b949e; padding:20px; text-align:center; font-size:0.88rem; }
"""

JS = """
function switchTab(tab, el) {
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + tab).classList.add('active');
    el.classList.add('active');
}
function toggleSector(sid) {
    const el = document.getElementById('sector_' + sid);
    const icon = document.getElementById('icon_' + sid);
    const hidden = el.style.display === 'none';
    el.style.display = hidden ? 'block' : 'none';
    icon.style.transform = hidden ? 'rotate(0deg)' : 'rotate(-90deg)';
}
function toggleChart(chartId) {
    const container = document.getElementById(chartId);
    const plotDiv = document.getElementById(chartId + '_plot');
    const isHidden = container.style.display === 'none';
    container.style.display = isHidden ? 'block' : 'none';
    if (isHidden && plotDiv && !plotDiv.hasChildNodes()) {
        const data = window.__charts && window.__charts[chartId];
        if (data) {
            Plotly.newPlot(plotDiv, data.data, data.layout, {responsive: true, displayModeBar: false});
        }
    }
}
"""

def build_dashboard():
    israel_tz = pytz.timezone("Asia/Jerusalem")
    now = datetime.now(israel_tz)
    print(f"\nBuilding dashboard: {now.strftime('%d/%m/%Y %H:%M:%S')}")

    print("\n[1/2] Scanning sectors...")
    sector_results, _ = scan_all_sectors()

    print("\n[2/2] Scanning signals...")
    signal_results, _ = scan_signals()

    sectors_html = build_sectors_html(sector_results)
    signals_html = build_signals_html(signal_results)
    timestamp = now.strftime("%d/%m/%Y %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Intelligence Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>{CSS}</style>
</head>
<body>
<div class="header">
    <div class="logo">
        <div class="logo-icon">📊</div>
        <div class="header-left">
            <h1>Market Intelligence</h1>
            <p>US Market Scanner — Professional Analysis</p>
        </div>
    </div>
    <div class="timestamp">Last updated: <span>{timestamp} (Israel Time)</span></div>
</div>
<div class="nav-tabs">
    <button class="nav-tab active" onclick="switchTab('sectors', this)">📂 Sectors</button>
    <button class="nav-tab" onclick="switchTab('signals', this)">🎯 Signals</button>
</div>
<div class="main">
    <div class="tab-content active" id="tab-sectors">{sectors_html}</div>
    <div class="tab-content" id="tab-signals">{signals_html}</div>
</div>
<script>{JS}</script>
</body>
</html>"""

    with open("dashboard.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard saved! ({timestamp})")

if __name__ == "__main__":
    build_dashboard()
    import webbrowser, os
    webbrowser.open("file://" + os.path.abspath("dashboard.html"))