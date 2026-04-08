import pandas as pd
import requests

def get_sp500():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/main/data/constituents.csv"
    df = pd.read_csv(url)
    return df["Symbol"].str.replace(".", "-").tolist()

def get_nasdaq100():
    # רשימת נאסדק 100
    return [
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA",
        "AVGO", "COST", "NFLX", "AMD", "PEP", "ADBE", "CSCO", "INTC",
        "INTU", "CMCSA", "TXN", "AMGN", "QCOM", "HON", "AMAT", "BKNG",
        "ISRG", "VRTX", "REGN", "MU", "PANW", "ADP", "GILD", "ADI",
        "LRCX", "MELI", "SBUX", "MDLZ", "SNPS", "CDNS", "KLAC", "ASML",
        "ABNB", "CRWD", "FTNT", "MRVL", "KDP", "ORLY", "CTAS", "MNST",
        "MAR", "PCAR", "PYPL", "WDAY", "DXCM", "CHTR", "FAST", "ODFL",
        "ROST", "IDXX", "BIIB", "VRSK", "DLTR", "EXC", "XEL", "GEHC",
        "ON", "TTWO", "ZS", "TEAM", "DDOG", "SGEN", "WBD", "ILMN",
        "GFS", "LCID", "RIVN", "ENPH", "ALGN", "FANG", "CEG", "CPRT",
        "PAYX", "MCHP", "AEP", "LULU", "NXPI", "SIRI", "ANSS", "MRNA",
        "OKTA", "EBAY", "ZM", "MTCH", "DOCU", "SPLK", "COUP", "PLTR",
        "RGEN", "HOOD", "COIN"
    ]

def get_space():
    return [
        "SPCE", "RKLB", "ASTS", "PL", "BKSY", "KTOS", "AJRD",
        "BA", "LMT", "NOC", "RTX", "GD", "MAXR", "SITS",
        "ASTR", "MNTS", "VORB", "RDW", "NARO"
    ]

def get_defense():
    return [
        "LMT", "RTX", "NOC", "GD", "BA", "HII", "TDG", "KTOS",
        "CACI", "SAIC", "LDOS", "BAH", "DRS", "AXON", "AVAV",
        "HEI", "TXT", "L3H", "FLIR", "MOOG"
    ]

def get_energy():
    return [
        "XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO",
        "PXD", "OXY", "DVN", "HAL", "BKR", "FANG", "HES",
        "MRO", "APA", "CTRA", "EQT", "AR", "RRC", "CNX",
        "WMB", "KMI", "OKE", "ET", "EPD", "MPLX"
    ]

def get_health():
    return [
        "JNJ", "UNH", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT",
        "DHR", "BMY", "AMGN", "GILD", "ISRG", "MDT", "CVS",
        "CI", "HUM", "CNC", "MOH", "WCG", "VRTX", "REGN",
        "BIIB", "MRNA", "BNTX", "NVAX", "SGEN", "ALNY", "BMRN"
    ]

def get_materials():
    return [
        "LIN", "APD", "ECL", "SHW", "PPG", "NEM", "FCX", "NUE",
        "STLD", "RS", "VMC", "MLM", "CF", "MOS", "ALB",
        "DD", "DOW", "LYB", "EMN", "FMC", "IFF", "CE",
        "ATI", "ARNC", "CMC", "WRK", "PKG", "IP"
    ]

def get_banks():
    return [
        "JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "PNC",
        "TFC", "COF", "AXP", "BK", "STT", "SCHW", "FITB",
        "KEY", "HBAN", "RF", "CFG", "MTB", "ZION", "CMA",
        "ALLY", "SYF", "DFS", "COF", "NYCB", "WAL"
    ]

SECTORS = {
    "Space": get_space(),
    "Energy": get_energy(),
    "Health": get_health(),
    "Materials": get_materials(),
    "Banks": get_banks(),
    "Defense": get_defense(),
    "S&P 500": get_sp500(),
    "Nasdaq 100": get_nasdaq100(),
}