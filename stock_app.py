# 🚀 PLUG & PLAY AUTO TRADING WEB APP (FINAL)

# ===== INSTALL FIRST =====
# pip install streamlit yfinance kiteconnect pandas

import streamlit as st
import pandas as pd
import yfinance as yf
from kiteconnect import KiteConnect
from datetime import datetime

st.set_page_config(page_title="Auto Trading App", layout="wide")

st.title("🤖 Auto Trading Web App (Plug & Play)")

# ===== SIDEBAR =====
st.sidebar.header("🔐 Zerodha Login")
api_key = st.sidebar.text_input("API KEY")
api_secret = st.sidebar.text_input("API SECRET")
request_token = st.sidebar.text_input("Request Token")

st.sidebar.header("⚙️ Settings")
stock = st.sidebar.text_input("Stock", "RELIANCE.NS")
capital = st.sidebar.number_input("Capital", value=10000)
risk_pct = st.sidebar.slider("Risk %", 1, 5, 2)

# ===== CONNECT =====
kite = None
if api_key and api_secret and request_token:
    try:
        kite = KiteConnect(api_key=api_key)
        data = kite.generate_session(request_token, api_secret=api_secret)
        kite.set_access_token(data["access_token"])
        st.sidebar.success("✅ Connected")
    except Exception as e:
        st.sidebar.error(f"❌ Connection Failed: {e}")

# ===== DATA =====
@st.cache_data(ttl=60)
def load(symbol):
    df = yf.download(symbol, period="5d", interval="15m")
    if df.empty:
        st.warning("No data fetched. Check your stock symbol.")
    return df

df = load(stock)

# ===== INDICATORS =====
def indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100/(1+rs))

    return df

# ===== STRATEGY =====
def get_signal(df):
    # Drop rows with NaN in indicators
    df = df.dropna(subset=['EMA20','EMA50','RSI'])
    if df.empty:
        return "HOLD"
    
    row = df.iloc[-1]
    if row['EMA20'] > row['EMA50'] and row['RSI'] < 60:
        return "BUY"
    elif row['EMA20'] < row['EMA50'] and row['RSI'] > 40:
        return "SELL"
    return "HOLD"

# ===== RISK =====
def qty_calc(price):
    risk_amt = capital * (risk_pct/100)
    sl_dist = price * 0.02
    qty = int(risk_amt / sl_dist)
    return max(qty,1)

# ===== PnL =====
def pnl(entry, exit, qty, typ):
    return (exit-entry)*qty if typ=="BUY" else (entry-exit)*qty

# ===== SESSION =====
if "trades" not in st.session_state:
    st.session_state.trades = []

# ===== MAIN =====
if not df.empty:
    df = indicators(df)

    # Check if enough data for EMA50
    if df['EMA50'].isna().all():
        st.warning("Not enough data to calculate EMA50 and RSI. Waiting for more candles...")
    else:
        price = df['Close'].iloc[-1]
        signal = get_signal(df)
        qty = qty_calc(price)

        sl = price * 0.98
        tgt = price * 1.03

        col1,col2,col3 = st.columns(3)
        col1.metric("Price", f"₹{price:.2f}")
        col2.metric("Signal", signal)
        col3.metric("Qty", qty)

        st.write(f"SL: ₹{sl:.2f} | Target: ₹{tgt:.2f}")

        # ===== AUTO TRADE =====
        if st.button("🚀 Execute Trade") and signal != "HOLD":
            if kite:
                try:
                    kite.place_order(
                        variety=kite.VARIETY_BO,
                        exchange=kite.EXCHANGE_NSE,
                        tradingsymbol=stock.replace(".NS",""),
                        transaction_type=kite.TRANSACTION_TYPE_BUY if signal=="BUY" else kite.TRANSACTION_TYPE_SELL,
                        quantity=qty,
                        product=kite.PRODUCT_MIS,
                        order_type=kite.ORDER_TYPE_MARKET,
                        squareoff=abs(tgt-price),
                        stoploss=abs(price-sl)
                    )
                except Exception as e:
                    st.error(f"Trade failed: {e}")

            st.session_state.trades.append({
                "time": datetime.now(),
                "stock": stock,
                "type": signal,
                "entry": price,
                "qty": qty,
                "sl": sl,
                "target": tgt,
                "status": "OPEN"
            })

            st.success("Trade Executed")

        # ===== AUTO EXIT =====
        for t in st.session_state.trades:
            if t['status'] == "OPEN":
                if t['type']=="BUY" and (price<=t['sl'] or price>=t['target']):
                    t['exit']=price
                    t['status']="CLOSED"
                    t['pnl']=pnl(t['entry'],price,t['qty'],t['type'])

                elif t['type']=="SELL" and (price>=t['sl'] or price<=t['target']):
                    t['exit']=price
                    t['status']="CLOSED"
                    t['pnl']=pnl(t['entry'],price,t['qty'],t['type'])

        # ===== DASHBOARD =====
        st.subheader("📊 Trades")
        df_trades = pd.DataFrame(st.session_state.trades)
        st.dataframe(df_trades)

        total = sum(t.get("pnl",0) for t in st.session_state.trades if t.get("status")=="CLOSED")
        st.subheader("💰 Total PnL")
        st.metric("PnL", f"₹{total:.2f}")

st.markdown("---")
st.markdown("⚠️ Plug & Play App. Test with small capital first.")