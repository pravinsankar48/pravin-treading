import time
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

try:
    from kiteconnect import KiteConnect
except ImportError:
    KiteConnect = None


st.set_page_config(
    page_title="NSE Live Trading Terminal",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #000000 !important;
        color: #f3f4f6 !important;
    }
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 0.8rem;
    }
    .signal-box {
        border: 1px solid #1f2937;
        border-radius: 14px;
        padding: 14px 16px;
        background: #050505;
        margin-bottom: 12px;
    }
    .signal-buy { border-color: #1d4ed8; }
    .signal-sell { border-color: #be123c; }
    .signal-hold { border-color: #d97706; }
    .signal-title { font-size: 28px; font-weight: 700; margin: 0; }
    .signal-sub { color: #9ca3af; margin-top: 6px; }
    .note-box {
        border: 1px solid #1f2937;
        border-radius: 10px;
        padding: 10px 12px;
        background: #090909;
        color: #d1d5db;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

NSE_STOCKS = {
    "RELIANCE": ("Reliance Industries", "Energy"),
    "TCS": ("Tata Consultancy Services", "IT"),
    "HDFCBANK": ("HDFC Bank", "Banking"),
    "BHARTIARTL": ("Bharti Airtel", "Telecom"),
    "ICICIBANK": ("ICICI Bank", "Banking"),
    "INFY": ("Infosys", "IT"),
    "SBIN": ("State Bank of India", "Banking"),
    "LT": ("Larsen & Toubro", "Infra"),
    "HINDUNILVR": ("Hindustan Unilever", "FMCG"),
    "ITC": ("ITC Limited", "FMCG"),
    "BAJFINANCE": ("Bajaj Finance", "Finance"),
    "HCLTECH": ("HCL Technologies", "IT"),
    "WIPRO": ("Wipro", "IT"),
    "MARUTI": ("Maruti Suzuki", "Auto"),
    "SUNPHARMA": ("Sun Pharmaceutical", "Pharma"),
    "TITAN": ("Titan Company", "Consumer"),
    "NESTLEIND": ("Nestle India", "FMCG"),
    "TATAMOTORS": ("Tata Motors", "Auto"),
    "AXISBANK": ("Axis Bank", "Banking"),
    "ASIANPAINT": ("Asian Paints", "Chemical"),
    "ADANIENT": ("Adani Enterprises", "Infra"),
    "ADANIPORTS": ("Adani Ports & SEZ", "Infra"),
    "KOTAKBANK": ("Kotak Mahindra Bank", "Banking"),
    "BAJAJ-AUTO": ("Bajaj Auto", "Auto"),
    "BAJAJFINSV": ("Bajaj Finserv", "Finance"),
    "POWERGRID": ("Power Grid Corp", "Energy"),
    "NTPC": ("NTPC", "Energy"),
    "ONGC": ("ONGC", "Energy"),
    "COALINDIA": ("Coal India", "Metal"),
    "TECHM": ("Tech Mahindra", "IT"),
    "DRREDDY": ("Dr Reddys Laboratories", "Pharma"),
    "CIPLA": ("Cipla", "Pharma"),
    "EICHERMOT": ("Eicher Motors", "Auto"),
    "BPCL": ("Bharat Petroleum", "Energy"),
    "INDUSINDBK": ("IndusInd Bank", "Banking"),
    "GRASIM": ("Grasim Industries", "Textile"),
    "ULTRACEMCO": ("UltraTech Cement", "Infra"),
    "JSWSTEEL": ("JSW Steel", "Metal"),
    "TATASTEEL": ("Tata Steel", "Metal"),
    "HINDALCO": ("Hindalco Industries", "Metal"),
    "APOLLOHOSP": ("Apollo Hospitals", "Pharma"),
    "BRITANNIA": ("Britannia Industries", "FMCG"),
    "TATACONSUM": ("Tata Consumer Products", "FMCG"),
    "SHRIRAMFIN": ("Shriram Finance", "Finance"),
    "HEROMOTOCO": ("Hero MotoCorp", "Auto"),
    "M&M": ("Mahindra & Mahindra", "Auto"),
    "SBILIFE": ("SBI Life Insurance", "Finance"),
    "HDFCLIFE": ("HDFC Life Insurance", "Finance"),
    "DIVISLAB": ("Divis Laboratories", "Pharma"),
    "BEL": ("Bharat Electronics", "Defence"),
    "AEGISLOG": ("Aegis Logistics", "Energy"),
    "ALKEM": ("Alkem Laboratories", "Pharma"),
    "AMARAJABAT": ("Amara Raja Energy", "Auto"),
    "AMBUJACEM": ("Ambuja Cements", "Infra"),
    "APOLLOTYRE": ("Apollo Tyres", "Auto"),
    "ARVIND": ("Arvind Limited", "Textile"),
    "ATUL": ("Atul Limited", "Chemical"),
    "AUROPHARMA": ("Aurobindo Pharma", "Pharma"),
    "AVANTIFEED": ("Avanti Feeds", "FMCG"),
    "BALRAMCHIN": ("Balrampur Chini Mills", "FMCG"),
    "BANKINDIA": ("Bank of India", "Banking"),
    "BATAINDIA": ("Bata India", "Consumer"),
    "BEML": ("BEML Limited", "Defence"),
    "BHARATFORG": ("Bharat Forge", "Auto"),
    "BIOCON": ("Biocon", "Pharma"),
    "CANFINHOME": ("Can Fin Homes", "Finance"),
    "CAPLIPOINT": ("Caplin Point Laboratories", "Pharma"),
    "CASTROLIND": ("Castrol India", "Energy"),
    "CEATLTD": ("CEAT", "Auto"),
    "CENTURYPLY": ("Century Plyboards", "Consumer"),
    "CHAMBLFERT": ("Chambal Fertilisers", "Chemical"),
    "CHOLAFIN": ("Cholamandalam Finance", "Finance"),
    "CLEAN": ("Clean Science & Technology", "Chemical"),
    "CONCOR": ("Container Corp of India", "Infra"),
    "COROMANDEL": ("Coromandel International", "Chemical"),
    "CROMPTON": ("Crompton Greaves Consumer", "Consumer"),
    "DALBHARAT": ("Dalmia Bharat", "Infra"),
    "DEEPAKFERT": ("Deepak Fertilisers", "Chemical"),
    "DELTACORP": ("Delta Corp", "Consumer"),
    "DEVYANI": ("Devyani International", "FMCG"),
    "DIXON": ("Dixon Technologies", "Consumer"),
    "DLF": ("DLF", "Realty"),
    "LALPATHLAB": ("Dr Lal PathLabs", "Pharma"),
    "EXIDEIND": ("Exide Industries", "Auto"),
    "FINEORG": ("Fine Organic Industries", "Chemical"),
    "FORTIS": ("Fortis Healthcare", "Pharma"),
    "GLANDPHARMA": ("Gland Pharma", "Pharma"),
    "GLAXO": ("GlaxoSmithKline Pharma", "Pharma"),
    "GLENMARK": ("Glenmark Pharmaceuticals", "Pharma"),
    "GODREJPROP": ("Godrej Properties", "Realty"),
    "GRANULES": ("Granules India", "Pharma"),
    "GUJFLUORO": ("Gujarat Fluorochemicals", "Chemical"),
    "GSFC": ("Gujarat State Fertilizers", "Chemical"),
    "GSPL": ("Gujarat State Petronet", "Energy"),
    "HATSUN": ("Hatsun Agro Product", "FMCG"),
    "HINDCOPPER": ("Hindustan Copper", "Metal"),
    "HINDZINC": ("Hindustan Zinc", "Metal"),
    "IRCON": ("IRCON International", "Infra"),
    "JINDALSTEL": ("Jindal Stainless", "Metal"),
    "JKCEMENT": ("JK Cement", "Infra"),
    "JKLAKSHMI": ("JK Lakshmi Cement", "Infra"),
    "JUBLFOOD": ("Jubilant FoodWorks", "FMCG"),
    "JUBLINGREVIA": ("Jubilant Ingrevia", "Chemical"),
    "KAJARIA": ("Kajaria Ceramics", "Consumer"),
    "KALPATPOWR": ("Kalpataru Power", "Infra"),
    "KALYANKJIL": ("Kalyan Jewellers", "Consumer"),
    "KANSAINER": ("Kansai Nerolac Paints", "Chemical"),
    "KECINTL": ("KEC International", "Infra"),
    "LAURUSLABS": ("Laurus Labs", "Pharma"),
    "LEMONTREE": ("Lemon Tree Hotels", "Consumer"),
    "LTIM": ("LTIMindtree", "IT"),
    "MANAPPURAM": ("Manappuram Finance", "Finance"),
    "MAXHEALTH": ("Max Healthcare", "Pharma"),
    "METROPOLIS": ("Metropolis Healthcare", "Pharma"),
    "MOIL": ("MOIL", "Metal"),
    "MOTHERSON": ("Samvardhana Motherson", "Auto"),
    "MRF": ("MRF", "Auto"),
    "MUTHOOTFIN": ("Muthoot Finance", "Finance"),
    "NARAYANA": ("Narayana Hrudayalaya", "Pharma"),
    "NATCOPHARM": ("NATCO Pharma", "Pharma"),
    "NATIONALUM": ("National Aluminium", "Metal"),
    "NAVINFLUOR": ("Navin Fluorine", "Chemical"),
    "NMDC": ("NMDC", "Metal"),
    "OBEROIRLTY": ("Oberoi Realty", "Realty"),
    "OIL": ("Oil India", "Energy"),
    "PAGEIND": ("Page Industries", "Textile"),
    "PNBHOUSING": ("PNB Housing Finance", "Finance"),
    "PRESTIGE": ("Prestige Estates", "Realty"),
    "RAIN": ("Rain Industries", "Chemical"),
    "RAYMOND": ("Raymond", "Textile"),
    "RITES": ("RITES", "Infra"),
    "SAIL": ("Steel Authority of India", "Metal"),
    "SOBHA": ("Sobha Developers", "Realty"),
    "SOLARINDS": ("Solar Industries India", "Defence"),
    "SONACOMS": ("Sona BLW Precision", "Auto"),
    "SUPREMEIND": ("Supreme Industries", "Chemical"),
    "SYNGENE": ("Syngene International", "Pharma"),
    "TATACHEM": ("Tata Chemicals", "Chemical"),
    "TATACOMM": ("Tata Communications", "Telecom"),
    "TATAPOWER": ("Tata Power", "Energy"),
    "THERMAX": ("Thermax", "Infra"),
    "THYROCARE": ("Thyrocare Technologies", "Pharma"),
    "TORNTPHARM": ("Torrent Pharmaceuticals", "Pharma"),
    "TRIDENT": ("Trident", "Textile"),
    "TUBEINVEST": ("Tube Investments of India", "Auto"),
    "VARUNBEV": ("Varun Beverages", "FMCG"),
    "VGUARD": ("V-Guard Industries", "Consumer"),
    "WELSPUNIND": ("Welspun India", "Textile"),
    "WESTLIFE": ("Westlife Foodworld", "FMCG"),
    "WHIRLPOOL": ("Whirlpool of India", "Consumer"),
    "ZYDUSLIFE": ("Zydus Lifesciences", "Pharma"),
    "BERGEPAINT": ("Berger Paints India", "Chemical"),
    "IGL": ("Indraprastha Gas", "Energy"),
    "PETRONET": ("Petronet LNG", "Energy"),
    "MGL": ("Mahanagar Gas", "Energy"),
    "GUJGAS": ("Gujarat Gas", "Energy"),
    "ADANIPOWER": ("Adani Power", "Energy"),
    "NHPC": ("NHPC", "Energy"),
    "SJVN": ("SJVN", "Energy"),
    "TORNTPOWER": ("Torrent Power", "Energy"),
    "CESC": ("CESC", "Energy"),
    "KEI": ("KEI Industries", "Infra"),
    "POLYCAB": ("Polycab India", "Consumer"),
    "CGPOWER": ("CG Power and Industrial", "Consumer"),
    "HAL": ("Hindustan Aeronautics", "Defence"),
    "DATAPATTNS": ("Data Patterns India", "Defence"),
    "PARAS": ("Paras Defence & Space", "Defence"),
    "COCHINSHIP": ("Cochin Shipyard", "Defence"),
    "MAZAGON": ("Mazagon Dock Shipbuilders", "Defence"),
    "GRSE": ("Garden Reach Shipbuilders", "Defence"),
    "ENGINERSIN": ("Engineers India", "Infra"),
    "NBCC": ("NBCC India", "Infra"),
    "IRB": ("IRB Infrastructure", "Infra"),
    "GMRINFRA": ("GMR Airports Infrastructure", "Infra"),
    "DILIPBLDRS": ("Dilip Buildcon", "Infra"),
    "PNCINFRA": ("PNC Infratech", "Infra"),
    "KNRCON": ("KNR Constructions", "Infra"),
    "ASHOKA": ("Ashoka Buildcon", "Infra"),
    "RVNL": ("Rail Vikas Nigam", "Infra"),
    "IRCTC": ("IRCTC", "Infra"),
    "IRFC": ("Indian Railway Finance", "Finance"),
    "LTFH": ("L&T Finance", "Finance"),
    "M&MFIN": ("Mahindra Finance", "Finance"),
    "HUDCO": ("HUDCO", "Finance"),
    "RECLTD": ("REC Limited", "Finance"),
    "PFC": ("Power Finance Corp", "Finance"),
    "LICHSGFIN": ("LIC Housing Finance", "Finance"),
    "HDFCAMC": ("HDFC Asset Management", "Finance"),
    "NAM-INDIA": ("Nippon Life India AMC", "Finance"),
    "ANGELONE": ("Angel One", "Finance"),
    "MOTILALOFS": ("Motilal Oswal Financial", "Finance"),
    "MCX": ("MCX India", "Finance"),
    "BSE": ("BSE Limited", "Finance"),
    "CDSL": ("CDSL", "Finance"),
    "CAMS": ("CAMS", "Finance"),
    "360ONE": ("360 ONE WAM", "Finance"),
    "ROUTE": ("Route Mobile", "IT"),
    "TANLA": ("Tanla Platforms", "IT"),
    "AFFLE": ("Affle India", "IT"),
    "NAZARA": ("Nazara Technologies", "IT"),
    "ZENSARTECH": ("Zensar Technologies", "IT"),
    "MPHASIS": ("Mphasis", "IT"),
    "LTTS": ("L&T Technology Services", "IT"),
    "KPITTECH": ("KPIT Technologies", "IT"),
    "PERSISTENT": ("Persistent Systems", "IT"),
    "COFORGE": ("Coforge", "IT"),
    "BIRLASOFT": ("Birlasoft", "IT"),
    "OFSS": ("Oracle Financial Services", "IT"),
    "INTELLECT": ("Intellect Design Arena", "IT"),
    "TATAELXSI": ("Tata Elxsi", "IT"),
    "CYIENT": ("Cyient", "IT"),
    "NEWGEN": ("Newgen Software", "IT"),
    "HAPPSTMNDS": ("Happiest Minds", "IT"),
    "FSL": ("Firstsource Solutions", "IT"),
    "QUESS": ("Quess Corp", "IT"),
    "TEAMLEASE": ("TeamLease Services", "IT"),
    "EQUITASBNK": ("Equitas Small Finance Bank", "Banking"),
    "UJJIVANSFB": ("Ujjivan Small Finance Bank", "Banking"),
    "SURYODAY": ("Suryoday Small Finance Bank", "Banking"),
    "KARURVSYA": ("Karur Vysya Bank", "Banking"),
    "CUB": ("City Union Bank", "Banking"),
    "J&KBANK": ("J&K Bank", "Banking"),
    "KTKBANK": ("Karnataka Bank", "Banking"),
    "UCOBANK": ("UCO Bank", "Banking"),
    "CENTRALBK": ("Central Bank of India", "Banking"),
    "MAHABANK": ("Bank of Maharashtra", "Banking"),
    "SPANDANA": ("Spandana Sphoorty", "Finance"),
    "CREDITACC": ("CreditAccess Grameen", "Finance"),
    "ZOMATO": ("Zomato", "Consumer"),
    "NYKAA": ("Nykaa", "Consumer"),
    "DMART": ("Avenue Supermarts", "FMCG"),
    "PIDILITIND": ("Pidilite Industries", "Chemical"),
    "TRENT": ("Trent Westside", "Consumer"),
    "ADANIGREEN": ("Adani Green Energy", "Energy"),
    "SUZLON": ("Suzlon Energy", "Energy"),
    "JSWEnergy": ("JSW Energy", "Energy"),
    "DEEPAKNI": ("Deepak Nitrite", "Chemical"),
    "AARTIIND": ("Aarti Industries", "Chemical"),
    "HAVELLS": ("Havells India", "Consumer"),
    "SIEMENS": ("Siemens India", "Infra"),
    "ABB": ("ABB India", "Infra"),
    "SHREECEM": ("Shree Cement", "Infra"),
    "SUNTV": ("Sun TV Network", "Media"),
    "PVRINOX": ("PVR Inox", "Media"),
    "INDIGO": ("IndiGo", "Infra"),
    "MANYAVAR": ("Vedant Fashions", "Textile"),
    "BALKRISIND": ("Balkrishna Industries", "Auto"),
    "LIC": ("LIC India", "Finance"),
    "ITI": ("ITI Limited", "Telecom"),
    "VMART": ("V-Mart Retail", "Consumer"),
    "GALLANTT": ("Gallantt Ispat", "Metal"),
}

INTERVALS = {
    "1 Minute": "1m",
    "5 Minutes": "5m",
    "15 Minutes": "15m",
    "30 Minutes": "30m",
    "1 Hour": "60m",
    "1 Day": "1d",
}

PERIODS = {
    "1m": "1d",
    "5m": "5d",
    "15m": "5d",
    "30m": "1mo",
    "60m": "3mo",
    "1d": "1y",
}

NSE_MARKET_OPEN = "09:15"
NSE_MARKET_CLOSE = "15:30"


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    return df


def format_axis_label(ts: pd.Timestamp, interval: str) -> str:
    if interval in ("1m", "5m", "15m", "30m", "60m"):
        return ts.strftime("%d %b %H:%M")
    return ts.strftime("%d %b %Y")


@st.cache_data(ttl=1)
def load_price_data(symbol: str, interval: str) -> pd.DataFrame:
    df = yf.download(
        f"{symbol}.NS",
        period=PERIODS.get(interval, "1d"),
        interval=interval,
        progress=False,
        auto_adjust=True,
        threads=False,
    )
    if df.empty:
        return pd.DataFrame()

    df = flatten_columns(df)
    df = df.rename(columns=str.title)
    required = ["Open", "High", "Low", "Close", "Volume"]
    if not all(column in df.columns for column in required):
        return pd.DataFrame()

    df = df[required].copy()
    for column in required:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna()
    df = df[~df.index.duplicated(keep="last")].sort_index()

    if getattr(df.index, "tz", None) is not None:
        try:
            df.index = df.index.tz_convert("Asia/Kolkata").tz_localize(None)
        except TypeError:
            df.index = df.index.tz_localize(None)

    intraday = {"1m", "5m", "15m", "30m", "60m"}
    if interval in intraday:
        df = df.between_time(NSE_MARKET_OPEN, NSE_MARKET_CLOSE, inclusive="both")

    df["AxisLabel"] = [format_axis_label(ts, interval) for ts in df.index]
    return df


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    return 100 - (100 / (1 + rs))


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift(1)).abs()
    low_close = (df["Low"] - df["Close"].shift(1)).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()


def compute_trailing_trend(
    df: pd.DataFrame, atr_period: int = 10, multiplier: float = 2.0
) -> tuple[pd.Series, pd.Series]:
    atr = compute_atr(df, atr_period)
    close = df["Close"]
    trend_line = pd.Series(index=df.index, dtype=float)
    trend_dir = pd.Series(index=df.index, dtype=int)

    for i in range(len(df)):
        if pd.isna(atr.iloc[i]):
            continue

        current_close = close.iloc[i]
        bullish_stop = current_close - multiplier * atr.iloc[i]
        bearish_stop = current_close + multiplier * atr.iloc[i]

        if i == 0 or pd.isna(trend_line.iloc[i - 1]):
            trend_line.iloc[i] = bullish_stop
            trend_dir.iloc[i] = 1
            continue

        prev_line = trend_line.iloc[i - 1]
        prev_dir = trend_dir.iloc[i - 1]

        if prev_dir == 1:
            next_line = max(prev_line, bullish_stop)
            if current_close < next_line:
                trend_line.iloc[i] = bearish_stop
                trend_dir.iloc[i] = -1
            else:
                trend_line.iloc[i] = next_line
                trend_dir.iloc[i] = 1
        else:
            next_line = min(prev_line, bearish_stop)
            if current_close > next_line:
                trend_line.iloc[i] = bullish_stop
                trend_dir.iloc[i] = 1
            else:
                trend_line.iloc[i] = next_line
                trend_dir.iloc[i] = -1

    return trend_line, trend_dir


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    enriched = df.copy()
    close = enriched["Close"].astype(float).squeeze()
    enriched["EMA9"] = close.ewm(span=9, adjust=False).mean()
    enriched["EMA20"] = close.ewm(span=20, adjust=False).mean()
    enriched["EMA50"] = close.ewm(span=50, adjust=False).mean()
    enriched["RSI"] = compute_rsi(close)
    enriched["ATR"] = compute_atr(enriched)
    enriched["TrendLine"], enriched["TrendDir"] = compute_trailing_trend(enriched)
    return enriched.dropna().copy()


def get_signal(df: pd.DataFrame) -> dict:
    if len(df) < 60:
        return {
            "signal": "HOLD",
            "score": 0,
            "reason": "Waiting for enough candles to build a stable view.",
            "stop_loss": 0.0,
            "target": 0.0,
            "risk_reward": 0.0,
        }

    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    notes = []

    if last["EMA20"] > last["EMA50"]:
        score += 2
        notes.append("EMA20 above EMA50")
    else:
        score -= 2
        notes.append("EMA20 below EMA50")

    if last["TrendDir"] == 1:
        score += 2
        notes.append("trailing trend bullish")
    else:
        score -= 2
        notes.append("trailing trend bearish")

    if last["RSI"] < 35:
        score += 1
        notes.append("RSI rebound zone")
    elif last["RSI"] > 70:
        score -= 1
        notes.append("RSI overbought")

    if last["Close"] > last["EMA9"] and prev["Close"] <= prev["EMA9"]:
        score += 1
        notes.append("momentum crossed above EMA9")
    elif last["Close"] < last["EMA9"] and prev["Close"] >= prev["EMA9"]:
        score -= 1
        notes.append("momentum crossed below EMA9")

    if prev["TrendDir"] == -1 and last["TrendDir"] == 1:
        score += 2
        notes.append("fresh BUY flip")
    elif prev["TrendDir"] == 1 and last["TrendDir"] == -1:
        score -= 2
        notes.append("fresh SELL flip")

    signal = "HOLD"
    if score >= 2:
        signal = "BUY"
    elif score <= -2:
        signal = "SELL"

    atr = float(last["ATR"]) if pd.notna(last["ATR"]) else float(last["Close"] * 0.015)
    close = float(last["Close"])
    stop_loss = close - (1.4 * atr) if signal == "BUY" else close + (1.4 * atr)
    target = close + (2.4 * atr) if signal == "BUY" else close - (2.4 * atr)
    risk = max(abs(close - stop_loss), 0.01)
    reward = abs(target - close)

    return {
        "signal": signal,
        "score": score,
        "reason": " | ".join(notes),
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "risk_reward": round(reward / risk, 2),
    }


def calc_quantity(price: float, capital: float, risk_pct: float, stop_loss: float) -> int:
    risk_amount = capital * (risk_pct / 100)
    stop_distance = max(abs(price - stop_loss), 0.01)
    risk_based_qty = int(risk_amount / stop_distance)
    affordable_qty = int(capital / max(price, 1))
    return max(min(risk_based_qty, affordable_qty), 1)


def build_chart(df: pd.DataFrame, symbol: str, interval_label: str, signal: dict) -> go.Figure:
    recent = df.tail(180).copy()
    x_vals = recent["AxisLabel"].tolist()
    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=x_vals,
            open=recent["Open"],
            high=recent["High"],
            low=recent["Low"],
            close=recent["Close"],
            name="Price",
            increasing_line_color="#00e5ff",
            increasing_fillcolor="#00e5ff",
            decreasing_line_color="#ff4d4f",
            decreasing_fillcolor="#ff4d4f",
            whiskerwidth=0.3,
        )
    )

    trend_up = recent["TrendLine"].where(recent["TrendDir"] == 1)
    trend_down = recent["TrendLine"].where(recent["TrendDir"] == -1)

    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=trend_up,
            name="Trend Up",
            mode="lines",
            line=dict(color="#0047ff", width=3, shape="hv"),
            connectgaps=False,
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=trend_down,
            name="Trend Down",
            mode="lines",
            line=dict(color="#ff1f3d", width=3, shape="hv"),
            connectgaps=False,
        )
    )

    buy_points = recent[(recent["TrendDir"] == 1) & (recent["TrendDir"].shift(1) == -1)]
    sell_points = recent[(recent["TrendDir"] == -1) & (recent["TrendDir"].shift(1) == 1)]

    if not buy_points.empty:
        fig.add_trace(
            go.Scatter(
                x=buy_points["AxisLabel"],
                y=buy_points["Low"] * 0.998,
                mode="markers+text",
                name="BUY",
                text=["BUY"] * len(buy_points),
                textposition="bottom center",
                textfont=dict(color="white", size=11),
                marker=dict(symbol="square", size=11, color="#003dff"),
                hovertemplate="BUY<br>%{x}<br>%{y:.2f}<extra></extra>",
            )
        )

    if not sell_points.empty:
        fig.add_trace(
            go.Scatter(
                x=sell_points["AxisLabel"],
                y=sell_points["High"] * 1.002,
                mode="markers+text",
                name="SELL",
                text=["SELL"] * len(sell_points),
                textposition="top center",
                textfont=dict(color="white", size=11),
                marker=dict(symbol="square", size=11, color="#a00046"),
                hovertemplate="SELL<br>%{x}<br>%{y:.2f}<extra></extra>",
            )
        )

    last_close = float(recent["Close"].iloc[-1])
    fig.add_hline(
        y=last_close,
        line=dict(color="#8b949e", width=1, dash="dot"),
        annotation_text=f"LTP {last_close:.2f}",
        annotation_position="top left",
    )

    if signal["signal"] != "HOLD":
        fig.add_hline(
            y=signal["stop_loss"],
            line=dict(color="#ff1f3d", width=1, dash="dash"),
            annotation_text=f"SL {signal['stop_loss']}",
            annotation_position="bottom left",
        )
        fig.add_hline(
            y=signal["target"],
            line=dict(color="#00ff66", width=1, dash="dash"),
            annotation_text=f"TGT {signal['target']}",
            annotation_position="top right",
        )

    tick_step = max(len(x_vals) // 8, 1)
    tick_vals = x_vals[::tick_step]

    fig.update_layout(
        height=760,
        margin=dict(l=8, r=18, t=44, b=8),
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        font=dict(color="#f3f4f6", family="Arial"),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        dragmode="pan",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            x=0,
            bgcolor="rgba(0,0,0,0.6)",
        ),
        title=dict(
            text=f"{symbol}.NS · {interval_label} · NSE",
            x=0.01,
            xanchor="left",
        ),
    )
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=x_vals,
        tickmode="array",
        tickvals=tick_vals,
        showgrid=False,
        title="Time",
        showline=True,
        linecolor="rgba(255,255,255,0.18)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.06)",
        title="Price (INR)",
        tickprefix="Rs ",
        side="right",
        showline=True,
        linecolor="rgba(255,255,255,0.18)",
        fixedrange=False,
    )
    return fig


@st.cache_data(ttl=20)
def run_scanner(symbols: list[str]) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        try:
            data = load_price_data(symbol, "1d")
            if data.empty:
                continue
            enriched = add_indicators(data)
            if enriched.empty:
                continue
            signal = get_signal(enriched)
            last = enriched.iloc[-1]
            rows.append(
                {
                    "Symbol": symbol,
                    "Name": NSE_STOCKS[symbol][0],
                    "Signal": signal["signal"],
                    "Close": round(float(last["Close"]), 2),
                    "RSI": round(float(last["RSI"]), 1),
                    "Score": signal["score"],
                }
            )
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(by=["Score", "RSI"], ascending=[False, True])


def place_kite_order(
    api_key: str,
    api_secret: str,
    request_token: str,
    symbol: str,
    side: str,
    quantity: int,
) -> tuple[bool, str]:
    if KiteConnect is None:
        return False, "kiteconnect is not installed."

    try:
        kite = KiteConnect(api_key=api_key)
        session = kite.generate_session(request_token, api_secret=api_secret)
        kite.set_access_token(session["access_token"])
        kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=kite.EXCHANGE_NSE,
            tradingsymbol=symbol,
            transaction_type=(
                kite.TRANSACTION_TYPE_BUY if side == "BUY" else kite.TRANSACTION_TYPE_SELL
            ),
            quantity=quantity,
            product=kite.PRODUCT_MIS,
            order_type=kite.ORDER_TYPE_MARKET,
        )
        return True, "Order placed successfully."
    except Exception as exc:
        return False, str(exc)


if "trade_log" not in st.session_state:
    st.session_state.trade_log = []


with st.sidebar:
    st.title("NSE Terminal")
    sector_options = ["All"] + sorted({sector for _, sector in NSE_STOCKS.values()})
    sector_filter = st.selectbox("Sector", sector_options)
    filtered_symbols = {
        symbol: meta
        for symbol, meta in NSE_STOCKS.items()
        if sector_filter == "All" or meta[1] == sector_filter
    }
    symbol_labels = {
        f"{symbol} - {meta[0]}": symbol for symbol, meta in filtered_symbols.items()
    }
    selected_label = st.selectbox("Stock", list(symbol_labels))
    selected_symbol = symbol_labels[selected_label]
    interval_label = st.selectbox("Chart Interval", list(INTERVALS), index=0)
    interval = INTERVALS[interval_label]

    st.markdown("---")
    capital = st.number_input("Capital", min_value=1000, value=100000, step=5000)
    risk_pct = st.slider("Risk Percent", min_value=1, max_value=10, value=2)
    refresh_seconds = st.number_input(
        "Auto Refresh (seconds)",
        min_value=1.0,
        max_value=10.0,
        value=1.0,
        step=0.5,
    )
    live_mode = st.toggle("Live Refresh", value=True)
    scanner_trigger = st.button("Scan Watchlist")

    st.markdown("---")
    st.caption("Optional Zerodha order placement")
    api_key = st.text_input("API Key")
    api_secret = st.text_input("API Secret", type="password")
    request_token = st.text_input("Request Token", type="password")


st.title("NSE Live Trading Dashboard")
st.markdown(
    '<div class="note-box">NSE regular cash-market hours are 9:15 AM to 3:30 PM IST. '
    'This chart filters intraday candles to that session. Yahoo Finance refreshes are near-live, not true tick streaming.</div>',
    unsafe_allow_html=True,
)

data = load_price_data(selected_symbol, interval)
if data.empty:
    st.error(f"Could not load data for {selected_symbol}.NS")
    st.stop()

enriched = add_indicators(data)
if enriched.empty:
    st.warning("Not enough candles yet for indicators. Try a broader interval.")
    st.stop()

signal = get_signal(enriched)
last = enriched.iloc[-1]
prev = enriched.iloc[-2]
price = float(last["Close"])
change_pct = ((price - float(prev["Close"])) / float(prev["Close"])) * 100
quantity = calc_quantity(price, capital, risk_pct, signal["stop_loss"] or price)
name, sector = NSE_STOCKS[selected_symbol]

signal_class = {
    "BUY": "signal-buy",
    "SELL": "signal-sell",
    "HOLD": "signal-hold",
}[signal["signal"]]

st.markdown(
    f"""
    <div class="signal-box {signal_class}">
        <p class="signal-title">{signal['signal']}</p>
        <div class="signal-sub">{selected_symbol}.NS | {name} | {sector}</div>
        <div class="signal-sub">{signal['reason']}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(6)
metric_cols[0].metric("Last Price", f"Rs {price:.2f}", f"{change_pct:+.2f}%")
metric_cols[1].metric("EMA20", f"Rs {last['EMA20']:.2f}")
metric_cols[2].metric("EMA50", f"Rs {last['EMA50']:.2f}")
metric_cols[3].metric("RSI", f"{last['RSI']:.1f}")
metric_cols[4].metric("Suggested Qty", f"{quantity}")
metric_cols[5].metric("R:R", f"1:{signal['risk_reward']}")

st.plotly_chart(
    build_chart(enriched, selected_symbol, interval_label, signal),
    use_container_width=True,
)

summary_cols = st.columns(3)
summary_cols[0].info(f"Stop Loss: Rs {signal['stop_loss']:.2f}")
summary_cols[1].info(f"Target: Rs {signal['target']:.2f}")
summary_cols[2].info(f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

trade_cols = st.columns(3)
if trade_cols[0].button("Log BUY", use_container_width=True):
    st.session_state.trade_log.insert(
        0,
        {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Symbol": selected_symbol,
            "Action": "BUY",
            "Price": round(price, 2),
            "Qty": quantity,
        },
    )
if trade_cols[1].button("Log SELL", use_container_width=True):
    st.session_state.trade_log.insert(
        0,
        {
            "Time": datetime.now().strftime("%H:%M:%S"),
            "Symbol": selected_symbol,
            "Action": "SELL",
            "Price": round(price, 2),
            "Qty": quantity,
        },
    )
if trade_cols[2].button("Place Zerodha Order", use_container_width=True):
    if signal["signal"] == "HOLD":
        st.warning("Current signal is HOLD, so no order was sent.")
    elif not (api_key and api_secret and request_token):
        st.warning("Enter Zerodha API credentials in the sidebar first.")
    else:
        ok, message = place_kite_order(
            api_key=api_key,
            api_secret=api_secret,
            request_token=request_token,
            symbol=selected_symbol,
            side=signal["signal"],
            quantity=quantity,
        )
        if ok:
            st.success(message)
        else:
            st.error(message)

st.subheader("Trade Log")
if st.session_state.trade_log:
    st.dataframe(pd.DataFrame(st.session_state.trade_log), use_container_width=True)
else:
    st.caption("Logged trades will appear here.")

if scanner_trigger:
    st.subheader("Watchlist Scanner")
    scan_df = run_scanner(list(NSE_STOCKS.keys()))
    if scan_df.empty:
        st.warning("Scanner could not find enough data right now.")
    else:
        st.dataframe(scan_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption(
    "For educational use only. This app does not provide guaranteed or 100% trade predictions. "
    "Use signals as a decision aid, not as certainty."
)

if live_mode:
    time.sleep(float(refresh_seconds))
    st.rerun()
