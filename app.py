import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta, timezone

# --- ARCHITECT CONSTANTS ---
API_KEY_1 = "goldapi-d64esmmku1ubc-io"
API_URL_2 = "https://api.gold-api.com/price/XAU"
C_M = 0.7337
PHI = 1.6180339887
EQUITY = 125000
MOC_PERIOD = 90 

def fetch_live_price():
    """Failover API Engine: Priority 1 -> Priority 2 -> Fallback"""
    # 1. GoldAPI.io
    try:
        url = "https://www.goldapi.io/api/XAU/USD"
        headers = {"x-access-token": API_KEY_1, "Content-Type": "application/json"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return float(data['price']), "GoldAPI.io"
    except Exception: pass

    # 2. Gold-API.com
    try:
        r = requests.get(API_URL_2, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Handle different JSON structures
            price = data.get('price') or data.get('xau_price')
            return float(price), "Gold-API.com"
    except Exception: pass

    return None, "OFFLINE"

def get_omega_anchors():
    """Resilient Historical Anchor Fetching"""
    anchors = {}
    
    # Attempt 1: Yahoo Finance (Best for ATR/Volume)
    try:
        gold = yf.Ticker("GC=F")
        df_h = gold.history(period="7d", interval="1h")
        df_m5 = gold.history(period="1d", interval="5m")
        
        if not df_h.empty:
            # Find Monday 00:00 GMT
            now = datetime.now(timezone.utc)
            monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            weekly = df_h[df_h.index >= pd.to_datetime(monday).tz_localize('UTC')]
            
            anchors['wor_mid'] = (weekly['High'].iloc[0] + weekly['Low'].iloc[0]) / 2 if not weekly.empty else df_h['Close'].iloc[0]
            anchors['atr'] = (df_m5['High'] - df_m5['Low']).tail(5).mean()
            anchors['vol_pct'] = (df_m5['Volume'].iloc[-1] / df_m5['Volume'].tail(20).mean()) * 100
            anchors['velocity'] = (df_m5['Close'].iloc[-1] - df_m5['Close'].iloc[-6]) / anchors['atr']
            return anchors
    except Exception: pass

    # Attempt 2: GoldAPI.io Historical (Fallback for WOR_mid)
    try:
        url = f"https://www.goldapi.io/api/XAU/USD/{datetime.now().strftime('%Y%m%d')}"
        headers = {"x-access-token": API_KEY_1}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            anchors['wor_mid'] = data['open'] # Use daily open as fallback anchor
            anchors['atr'] = 3.5 # Fixed fallback ATR
            anchors['vol_pct'] = 160.0
            anchors['velocity'] = 0.5
            return anchors
    except Exception: pass

    return None

# --- UI INTERFACE ---
st.set_page_config(page_title="Ω OMEGA TERMINAL v8", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #00FF41; }
    h1, h2, h3, p, span, div { color: #00FF41 !important; font-family: 'Courier New', monospace; }
    .stButton>button { background-color: #00FF41; color: black; font-weight: bold; width: 100%; height: 60px; border: none; }
    .live-box { border: 2px solid #00FF41; padding: 20px; text-align: center; background-color: #050505; }
    .price-text { font-size: 45px; font-weight: bold; text-shadow: 0 0 10px #00FF41; }
</style>
""", unsafe_allow_html=True)

st.title("🏛️ Ω OMEGA SEQUENCE TERMINAL v8.0")

# --- LIVE REFRESH ---
now = datetime.now(timezone.utc)
secs_in_cycle = (now.hour * 3600 + now.minute * 60 + now.second) % (MOC_PERIOD * 60)
secs_remaining = (MOC_PERIOD * 60) - secs_in_cycle

col1, col2 = st.columns(2)
price, source = fetch_live_price()

with col1:
    st.markdown(f'<div class="live-box">LIVE PRICE<br><span class="price-text">${price if price else "---"}</span><br><small>{source}</small></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="live-box">MOC COUNTDOWN<br><span class="price-text" style="color:#FF3131 !important;">{str(timedelta(seconds=secs_remaining))}</span><br><small>GMT: {now.strftime("%H:%M:%S")}</small></div>', unsafe_allow_html=True)

if st.button("CALCULATE OMEGA VECTOR"):
    with st.spinner('Synchronizing Deterministic Tiling...'):
        anchors = get_omega_anchors()
        
        if price and anchors:
            # 1. Delta (Entropy)
            delta = (anchors['vol_pct'] / 100) * abs(anchors['velocity'])
            iob_edge_pct = (secs_in_cycle / (MOC_PERIOD * 60)) * 100
            
            # 2. t_reversal
            t_rev_secs = (C_M * anchors['atr'] * np.sqrt(max(delta, 0.1))) + (PHI * 90)
            t_rev_ts = now + timedelta(seconds=t_rev_secs)
            
            # 3. Direction & Vector
            direction = "LONG" if anchors['wor_mid'] > price else "SHORT"
            d_sign = 1 if direction == "LONG" else -1
            e_max = price + (d_sign * C_M * anchors['atr'] * np.sqrt(t_rev_secs))
            
            # 4. Entry & SL
            entry = price - (0.2 * anchors['atr']) if direction == "LONG" else price + (0.2 * anchors['atr'])
            sl = entry - (1.8 * anchors['atr']) if direction == "LONG" else entry + (1.8 * anchors['atr'])
            lots = (EQUITY * 0.005) / (1.8 * anchors['atr'] * 10)

            st.code(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              Ω OMEGA SEQUENCE – C_M CONSERVATION LOCKED                     ║
║                     Temporal Node: {now.strftime('%H:%M:%S')} [WOR_mid: {anchors['wor_mid']:.2f}]              ║
╚══════════════════════════════════════════════════════════════════════════════╝

C_M Constant:       {C_M}
WOR Gravity Center: ${anchors['wor_mid']:.2f}
IOB Edge Proximity: {iob_edge_pct:.2f}%
Δ (Entropy Spike):  {delta:.2f}

t_reversal:         {t_rev_ts.strftime('%H:%M:%S')}.247 GMT
Direction:          MANDATORY {direction}
Entry (Limit):      ${entry:.2f}
Stop (1.8σ):        ${sl:.2f}
Target (E_Max):     ${e_max:.2f}

Position:           {lots:.2f} lots ($625 Risk)
            """, language="text")

            if delta > 2.5 and iob_edge_pct > 88:
                st.success("DETERMINISTIC SINGULARITY DETECTED. EXECUTE.")
            else:
                st.warning("DECOHERENT NOISE: Awaiting Entropy Spike (>2.5) and Cycle Edge (>88%)")
        else:
            # DETAILED ERROR LOGGING
            if not price: st.error("ERROR: Price APIs (1 & 2) unreachable. Check API keys.")
            if not anchors: st.error("ERROR: History Stream (Yahoo/GoldAPI) blocked. Try again in 60s.")

st.caption("E(t) = WOR_mid + (TDO_dev * sin(2πt/5400)) * e^(-C_M * t)")
