from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Wisalsaya Crypto Decision Lab v3",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BANGKOK = ZoneInfo("Asia/Bangkok")
APP_DIR = Path(__file__).resolve().parent

COINS = {
    "BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "SOL": "SOLUSDT",
    "XRP": "XRPUSDT", "ADA": "ADAUSDT", "DOGE": "DOGEUSDT", "TRX": "TRXUSDT",
    "LINK": "LINKUSDT", "AVAX": "AVAXUSDT", "SUI": "SUIUSDT", "TON": "TONUSDT",
    "NEAR": "NEARUSDT", "APT": "APTUSDT", "ARB": "ARBUSDT", "OP": "OPUSDT",
    "INJ": "INJUSDT", "DOT": "DOTUSDT", "LTC": "LTCUSDT", "BCH": "BCHUSDT",
}

COIN_ICONS = {
    "BTC": "₿", "ETH": "Ξ", "BNB": "◆", "SOL": "S", "XRP": "X",
    "ADA": "A", "DOGE": "Ð", "TRX": "T", "LINK": "⬡", "AVAX": "A",
    "SUI": "S", "TON": "T", "NEAR": "N", "APT": "A", "ARB": "A",
    "OP": "O", "INJ": "I", "DOT": "●", "LTC": "Ł", "BCH": "₿",
}

# ---------- Theme ----------
st.markdown("""
<style>
:root{
 --bg:#06111b;--bg2:#0a1d2b;--panel:#0d2534;--panel2:#102b3b;--line:rgba(232,194,104,.22);
 --gold:#e8c268;--green:#56d6a5;--red:#ff788e;--blue:#6fc9ff;--text:#f4f7fb;--muted:#9eb2bf;
}
.stApp{background:radial-gradient(circle at 86% 2%,rgba(26,117,106,.28),transparent 31%),linear-gradient(145deg,var(--bg),var(--bg2));color:var(--text)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#07141f,#0a202d);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
.block-container{max-width:1450px;padding-top:1.1rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.02em}
.brand{font-size:1.55rem;font-weight:900;color:var(--gold);line-height:1.05}.brand-sub{color:var(--muted);font-size:.78rem;letter-spacing:.08em}
.page-title{font-size:clamp(1.7rem,3vw,2.65rem);font-weight:900;color:var(--gold);margin-bottom:.1rem}
.page-sub{color:var(--muted);margin-bottom:.8rem}
.pill{display:inline-block;padding:.32rem .68rem;border-radius:999px;border:1px solid var(--line);background:rgba(86,214,165,.09);font-size:.73rem;font-weight:800}
.hero{background:linear-gradient(125deg,rgba(20,80,73,.96),rgba(9,35,52,.98));border:1px solid rgba(232,194,104,.55);border-radius:26px;padding:1.35rem 1.45rem;box-shadow:0 18px 48px rgba(0,0,0,.23);margin:.55rem 0 1rem}
.hero-grid{display:grid;grid-template-columns:210px 1fr;gap:1.2rem;align-items:center}.hero-score{font-size:3.1rem;font-weight:950;color:var(--gold);line-height:1}.hero-label{font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.12em}.hero-status{display:inline-block;margin-top:.55rem;padding:.38rem .72rem;border-radius:999px;background:rgba(86,214,165,.16);border:1px solid rgba(86,214,165,.45);font-weight:900;color:var(--green)}
.hero-head{font-size:1.35rem;font-weight:900}.hero-note{color:var(--muted);margin-top:.4rem}
.ui-card{background:linear-gradient(180deg,rgba(16,43,59,.97),rgba(11,31,45,.97));border:1px solid var(--line);border-radius:20px;padding:1rem;box-shadow:0 10px 28px rgba(0,0,0,.15);height:100%}
.metric-label{color:var(--muted);font-size:.78rem}.metric-value{font-size:1.35rem;font-weight:900;color:var(--gold);margin-top:.22rem}.metric-note{font-size:.75rem;color:var(--muted);margin-top:.22rem}
.coin-card{background:linear-gradient(180deg,rgba(17,45,61,.98),rgba(10,31,44,.98));border:1px solid var(--line);border-radius:18px;padding:.9rem;height:100%}.coin-head{display:flex;justify-content:space-between;align-items:center}.coin-icon{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:rgba(232,194,104,.12);border:1px solid rgba(232,194,104,.35);font-weight:900;color:var(--gold)}.coin-score{font-size:1.45rem;font-weight:950;color:var(--gold)}.coin-name{font-weight:900}.coin-meta{color:var(--muted);font-size:.79rem;line-height:1.55;margin-top:.55rem}.status{display:inline-block;margin-top:.6rem;padding:.3rem .62rem;border-radius:999px;font-size:.7rem;font-weight:900}.ready{background:rgba(86,214,165,.15);color:var(--green);border:1px solid rgba(86,214,165,.4)}.watch{background:rgba(111,201,255,.13);color:var(--blue);border:1px solid rgba(111,201,255,.35)}.wait{background:rgba(232,194,104,.12);color:var(--gold);border:1px solid rgba(232,194,104,.35)}.avoid{background:rgba(255,120,142,.12);color:var(--red);border:1px solid rgba(255,120,142,.35)}
.level{display:flex;justify-content:space-between;padding:.62rem .72rem;border-bottom:1px solid rgba(255,255,255,.06)}.level:last-child{border-bottom:none}.level b{color:var(--gold)}
.news-item{padding:.7rem 0;border-bottom:1px solid rgba(255,255,255,.06)}.news-item:last-child{border-bottom:none}.news-title{font-weight:800;font-size:.9rem}.news-meta{color:var(--muted);font-size:.73rem;margin-top:.22rem}
.coach{background:linear-gradient(135deg,rgba(232,194,104,.13),rgba(86,214,165,.08));border:1px solid rgba(232,194,104,.32);border-radius:20px;padding:1rem}
.section-title{font-size:1.18rem;font-weight:900;color:var(--text);margin:.9rem 0 .55rem}.section-kicker{color:var(--gold);font-size:.78rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase}
div[data-testid="stMetric"]{background:rgba(16,43,59,.92);border:1px solid var(--line);border-radius:17px;padding:.75rem}
.stButton>button,.stDownloadButton>button{width:100%;border-radius:13px;border:1px solid rgba(232,194,104,.45);background:#15484b;color:white;font-weight:850;min-height:42px}.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--gold);color:white}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:14px;overflow:hidden}
hr{border-color:rgba(255,255,255,.07)}
@media(max-width:800px){.hero-grid{grid-template-columns:1fr}.hero-score{font-size:2.55rem}.block-container{padding-left:.7rem;padding-right:.7rem}.ui-card,.coin-card{border-radius:16px}}
</style>
""", unsafe_allow_html=True)

# ---------- Data ----------
@st.cache_data(ttl=60, show_spinner=False)
def ticker(symbol: str) -> dict:
    errors = []
    for base in ("https://data-api.binance.vision", "https://api.binance.com"):
        try:
            r = requests.get(f"{base}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=8)
            r.raise_for_status()
            p = r.json()
            return {
                "price": float(p["lastPrice"]), "change": float(p["priceChangePercent"]),
                "high": float(p["highPrice"]), "low": float(p["lowPrice"]),
                "quote_volume": float(p["quoteVolume"]),
            }
        except Exception as exc:
            errors.append(str(exc))
    raise RuntimeError("ไม่สามารถดึงราคาตลาดได้")

@st.cache_data(ttl=90, show_spinner=False)
def klines(symbol: str, interval: str = "4h", limit: int = 240) -> pd.DataFrame:
    for base in ("https://data-api.binance.vision", "https://api.binance.com"):
        try:
            r = requests.get(f"{base}/api/v3/klines", params={"symbol": symbol, "interval": interval, "limit": limit}, timeout=10)
            r.raise_for_status()
            df = pd.DataFrame(r.json(), columns=[
                "open_time","open","high","low","close","volume","close_time","quote_volume",
                "trades","taker_base","taker_quote","ignore"
            ])
            for col in ("open","high","low","close","volume","quote_volume"):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(BANGKOK)
            return df.dropna(subset=["close"])
        except Exception:
            continue
    raise RuntimeError("ไม่สามารถดึงข้อมูลกราฟได้")

@st.cache_data(ttl=900, show_spinner=False)
def fear_greed() -> tuple[int, str]:
    try:
        r = requests.get("https://api.alternative.me/fng/", params={"limit": 1}, timeout=8)
        r.raise_for_status(); x = r.json()["data"][0]
        return int(x["value"]), x["value_classification"]
    except Exception:
        return 50, "Neutral"

@st.cache_data(ttl=900, show_spinner=False)
def crypto_news() -> list[dict]:
    feeds = [
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Cointelegraph", "https://cointelegraph.com/rss"),
    ]
    items: list[dict] = []
    for source, url in feeds:
        try:
            r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for node in root.findall(".//item")[:5]:
                title = (node.findtext("title") or "").strip()
                link = (node.findtext("link") or "").strip()
                pub = (node.findtext("pubDate") or "").strip()
                if title:
                    items.append({"title": title, "link": link, "source": source, "published": pub})
        except Exception:
            continue
    return items[:6]

def rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff(); gain = delta.clip(lower=0); loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean().replace(0, np.nan)
    value = 100 - (100 / (1 + avg_gain / avg_loss))
    return float(value.iloc[-1]) if pd.notna(value.iloc[-1]) else 50.0

def normalize(value: float, low: float, high: float) -> float:
    if high <= low: return 50.0
    return float(np.clip((value-low)/(high-low)*100, 0, 100))

def analyze(t: dict, df: pd.DataFrame, fng: int, btc_trend: str | None = None) -> dict:
    x = df.copy()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    x["ret"] = x["close"].pct_change()
    close = float(x["close"].iloc[-1]); e20 = float(x["ema20"].iloc[-1]); e50 = float(x["ema50"].iloc[-1])
    rv = rsi(x["close"]); vr = float(x["volume"].iloc[-1] / max(x["volume"].tail(20).mean(), 1e-12))
    vol = float(x["ret"].tail(20).std() * math.sqrt(20) * 100)
    recent = x.tail(36)
    mom = float((close / float(x["close"].iloc[-7]) - 1) * 100) if len(x) >= 7 else 0

    if close > e20 > e50:
        trend = "Uptrend" if (close/e20-1) > .012 else "Sideway Up"
        trend_score = 82 if trend == "Uptrend" else 72
    elif close < e20 < e50:
        trend = "Downtrend" if (e20/close-1) > .012 else "Sideway Down"
        trend_score = 22 if trend == "Downtrend" else 34
    else:
        trend = "Sideway"
        trend_score = 52

    momentum_score = 85 if 55 <= rv <= 68 and mom > 0 else 70 if 50 <= rv < 70 else 55 if 42 <= rv < 75 else 35
    volume_score = 90 if vr >= 1.6 else 76 if vr >= 1.2 else 60 if vr >= .85 else 42
    volatility_score = 72 if 1.2 <= vol <= 5.5 else 55 if .7 <= vol <= 8 else 35
    news_score = 65 if 35 <= fng <= 70 else 52 if 20 <= fng <= 80 else 38
    market_align = 70 if btc_trend in (None, "Uptrend", "Sideway Up") else 52 if btc_trend == "Sideway" else 35

    weights = {"trend":.28,"momentum":.22,"volume":.18,"volatility":.12,"news":.10,"market":.10}
    score = round(trend_score*weights["trend"] + momentum_score*weights["momentum"] + volume_score*weights["volume"] + volatility_score*weights["volatility"] + news_score*weights["news"] + market_align*weights["market"])

    if trend in ("Uptrend","Sideway Up"):
        up, side, down = (56,29,15) if rv < 70 else (47,32,21)
    elif trend in ("Downtrend","Sideway Down"):
        up, side, down = (18,27,55)
    else:
        up, side, down = (35,43,22) if rv >= 50 else (27,44,29)

    support = float(recent["low"].quantile(.10)); resistance = float(recent["high"].quantile(.90))
    trigger = resistance * 1.002
    stop = max(support, close * .975)
    target1 = trigger + (trigger-stop)*1.5
    target2 = trigger + (trigger-stop)*2.2

    if score >= 78 and trend in ("Uptrend","Sideway Up") and rv < 70:
        status = "READY"
    elif score >= 63:
        status = "WATCH"
    elif score >= 48:
        status = "WAIT"
    else:
        status = "AVOID"

    return {
        "score": int(np.clip(score,0,100)), "trend": trend, "rsi": round(rv,1),
        "volume_ratio": round(vr,2), "volatility": round(vol,2), "momentum": round(mom,2),
        "support": support, "resistance": resistance, "trigger": trigger, "stop": stop,
        "target1": target1, "target2": target2, "up":up,"sideway":side,"down":down,
        "status":status, "trend_score":trend_score, "momentum_score":momentum_score,
        "volume_score":volume_score, "volatility_score":volatility_score,"news_score":news_score,
        "ema20":e20,"ema50":e50,
    }

def money(v: float) -> str:
    if v >= 1000: return f"${v:,.2f}"
    if v >= 1: return f"${v:,.3f}"
    return f"${v:,.6f}"

def status_class(status: str) -> str:
    return status.lower()

def decision_from_score(score: int, btc_trend: str, btc_rsi: float) -> tuple[str,str,str]:
    if score >= 75 and btc_trend in ("Uptrend","Sideway Up") and btc_rsi < 70:
        return "OPPORTUNITY", "มีโอกาสเกิดจังหวะมากกว่าปกติ", "ยังต้องรอ Trigger และ Volume ยืนยันก่อน"
    if score >= 60:
        return "WATCH", "ตลาดเริ่มน่าสนใจ แต่ยังไม่ชัดเจน", "โฟกัสการเฝ้าดู ไม่ไล่ราคา"
    return "WAIT", "วันนี้เหมาะกับการรอ", "รักษาเงินต้นและฝึกอ่านตลาด"

def load_market(interval: str) -> dict:
    fng, _ = fear_greed()
    out = {}
    btc_t = ticker(COINS["BTC"]); btc_df = klines(COINS["BTC"], interval)
    btc_a = analyze(btc_t, btc_df, fng, None)
    out["BTC"] = {**btc_t,"df":btc_df,"a":btc_a}
    for name, symbol in COINS.items():
        if name == "BTC": continue
        t = ticker(symbol); df = klines(symbol, interval)
        out[name] = {**t,"df":df,"a":analyze(t,df,fng,btc_a["trend"])}
    return out

def candle_chart(df: pd.DataFrame, symbol: str, a: dict) -> go.Figure:
    x = df.tail(120).copy(); x["ema20"] = x["close"].ewm(span=20,adjust=False).mean(); x["ema50"] = x["close"].ewm(span=50,adjust=False).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=x["time"],open=x["open"],high=x["high"],low=x["low"],close=x["close"],name=symbol,increasing_line_color="#56d6a5",decreasing_line_color="#ff788e"))
    fig.add_trace(go.Scatter(x=x["time"],y=x["ema20"],name="EMA20",line=dict(width=1.6)))
    fig.add_trace(go.Scatter(x=x["time"],y=x["ema50"],name="EMA50",line=dict(width=1.6,dash="dot")))
    for y,label,color in [(a["support"],"Support","#56d6a5"),(a["resistance"],"Resistance","#ff788e"),(a["trigger"],"Trigger","#6fc9ff")]:
        fig.add_hline(y=y,line_dash="dash",line_color=color,annotation_text=label,annotation_position="top left")
    fig.update_layout(height=520,margin=dict(l=8,r=8,t=22,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#dce7ee"),xaxis_rangeslider_visible=False,xaxis=dict(showgrid=False),yaxis=dict(gridcolor="rgba(255,255,255,.06)"),legend=dict(orientation="h",y=1.02,x=0))
    return fig

def probability_chart(a: dict) -> go.Figure:
    fig = go.Figure(go.Bar(x=["ขาขึ้น","Sideway","ขาลง"],y=[a["up"],a["sideway"],a["down"]],text=[f"{a['up']}%",f"{a['sideway']}%",f"{a['down']}%"],textposition="auto"))
    fig.update_layout(height=260,margin=dict(l=8,r=8,t=10,b=8),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font=dict(color="#dce7ee"),yaxis=dict(range=[0,100],gridcolor="rgba(255,255,255,.06)"),showlegend=False)
    return fig

# ---------- State ----------
if "paper_trades" not in st.session_state: st.session_state.paper_trades = []
if "journal" not in st.session_state: st.session_state.journal = []
if "watchlist" not in st.session_state: st.session_state.watchlist = ["BTC","ETH","BNB"]

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="brand">✦ WISALSAYA</div><div class="brand-sub">CRYPTO DECISION LAB</div>', unsafe_allow_html=True)
    st.markdown("---")
    page = st.radio("เมนู", ["Dashboard","Coin Scanner","Chart Lab","Trade Plan","Journal","Learning"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**⚙️ Personal Settings**")
    capital = st.number_input("ทุนทดลอง (บาท)", min_value=100, value=1000, step=100)
    max_daily_loss = st.number_input("ขาดทุนสูงสุดต่อวัน", min_value=10, value=150, step=10)
    per_trade_risk = st.number_input("ความเสี่ยงต่อแผน", min_value=10, max_value=int(max_daily_loss), value=min(50,int(max_daily_loss)), step=10)
    interval_label = st.selectbox("Timeframe หลัก", ["1H","4H","1D"], index=1)
    interval = {"1H":"1h","4H":"4h","1D":"1d"}[interval_label]
    st.caption("Paper Trading only • ไม่มีการส่งคำสั่งซื้อขาย")

# ---------- Load ----------
now = datetime.now(BANGKOK)
with st.spinner("กำลังอัปเดตตลาด 20 เหรียญ..."):
    try:
        market = load_market(interval)
    except Exception as exc:
        st.error(f"ดึงข้อมูลตลาดไม่สำเร็จ: {exc}")
        st.stop()

fng_value, fng_label = fear_greed()
ranked = sorted(market.items(), key=lambda item: item[1]["a"]["score"], reverse=True)
core_score = round(np.mean([market[x]["a"]["score"] for x in ("BTC","ETH","BNB")]))
decision, decision_head, decision_note = decision_from_score(core_score, market["BTC"]["a"]["trend"], market["BTC"]["a"]["rsi"])

# update paper trades using latest price
for trade in st.session_state.paper_trades:
    if trade["status"] != "OPEN": continue
    p = market.get(trade["coin"],{}).get("price")
    if p is None: continue
    trade["current"] = p
    if p <= trade["stop"]:
        trade["status"] = "STOP"; trade["exit"] = trade["stop"]
    elif p >= trade["target"]:
        trade["status"] = "TARGET"; trade["exit"] = trade["target"]
    exit_price = trade.get("exit", p)
    trade["pnl"] = (exit_price-trade["entry"])/trade["entry"]*trade["position"]

closed_pnl = sum(t.get("pnl",0) for t in st.session_state.paper_trades if t["status"] != "OPEN")
open_pnl = sum(t.get("pnl",0) for t in st.session_state.paper_trades if t["status"] == "OPEN")
today_loss = abs(sum(min(0,t.get("pnl",0)) for t in st.session_state.paper_trades if t["created"] == now.strftime("%Y-%m-%d") and t["status"] != "OPEN"))
risk_remaining = max(0, max_daily_loss - today_loss)

# ---------- Components ----------
def page_header(title: str, subtitle: str):
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">{subtitle} • อัปเดต {now:%d/%m/%Y %H:%M} น.</div>', unsafe_allow_html=True)

def decision_box():
    btc = market["BTC"]["a"]
    st.markdown(f"""
    <div class="hero"><div class="hero-grid">
      <div><div class="hero-label">Decision Box</div><div class="hero-score">{core_score}/100</div><div class="hero-status">{decision}</div></div>
      <div><div class="hero-head">{decision_head}</div><div class="hero-note">{decision_note}</div><div class="hero-note">BTC Trend: <b>{btc['trend']}</b> • RSI {btc['rsi']} • Fear & Greed {fng_value}</div></div>
    </div></div>
    """, unsafe_allow_html=True)

def metric_card(label: str, value: str, note: str = ""):
    st.markdown(f'<div class="ui-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)

def coin_card(name: str, payload: dict):
    a = payload["a"]
    st.markdown(f"""
    <div class="coin-card"><div class="coin-head"><div class="coin-icon">{COIN_ICONS[name]}</div><div class="coin-score">{a['score']}</div></div>
    <div class="coin-name">{name}/USDT</div><div class="coin-meta">Trend: <b>{a['trend']}</b><br>RSI {a['rsi']} • Volume {a['volume_ratio']}x<br>24h {payload['change']:+.2f}%</div>
    <span class="status {status_class(a['status'])}">{a['status']}</span></div>
    """, unsafe_allow_html=True)

# ---------- Pages ----------
if page == "Dashboard":
    page_header("Wisalsaya Crypto Decision Assistant", "Morning Brief • Beginner Mode")
    st.markdown('<span class="pill">LIVE MARKET DATA</span>', unsafe_allow_html=True)
    decision_box()
    c1,c2,c3,c4 = st.columns(4)
    with c1: metric_card("พอร์ตทดลอง", f"{capital + closed_pnl + open_pnl:,.2f} บาท", f"P/L {closed_pnl+open_pnl:+.2f} บาท")
    with c2: metric_card("ความเสี่ยงคงเหลือวันนี้", f"{risk_remaining:,.0f} บาท", f"Limit {max_daily_loss:,.0f} บาท")
    with c3: metric_card("Fear & Greed", f"{fng_value}/100", fng_label)
    with c4: metric_card("Market Status", decision, "ประเมินจาก BTC/ETH/BNB")

    st.markdown('<div class="section-title">Coin Scanner — Top 5 วันนี้</div>', unsafe_allow_html=True)
    cols = st.columns(5)
    for col,(name,payload) in zip(cols, ranked[:5]):
        with col: coin_card(name,payload)

    left,right = st.columns([1.45,1])
    with left:
        st.markdown('<div class="section-title">Chart Lab — Top Coin</div>', unsafe_allow_html=True)
        top_name, top_payload = ranked[0]
        st.plotly_chart(candle_chart(top_payload["df"], top_name, top_payload["a"]), use_container_width=True, config={"displayModeBar":False})
    with right:
        st.markdown('<div class="section-title">News Impact</div>', unsafe_allow_html=True)
        news = crypto_news()
        if news:
            html = '<div class="ui-card">' + ''.join([f'<div class="news-item"><div class="news-title">{n["title"]}</div><div class="news-meta">{n["source"]} • ข่าวล่าสุดสำหรับประเมินผลกระทบ</div></div>' for n in news[:3]]) + '</div>'
            st.markdown(html, unsafe_allow_html=True)
        else:
            st.info("ยังไม่สามารถโหลดข่าว RSS ได้ในขณะนี้")
        st.markdown('<div class="section-title">Beginner Coach</div>', unsafe_allow_html=True)
        coach = ["ดู BTC ก่อนเสมอ", "ถ้า Trend ยัง Sideway ให้รอ Trigger", "RSI สูงไม่ได้แปลว่าต้องเข้า"]
        st.markdown('<div class="coach"><b>วันนี้ควรทำอะไร</b><br><br>• ' + '<br>• '.join(coach) + '<br><br><span style="color:#9eb2bf">ทำตามแผนก่อนดูผลลัพธ์</span></div>', unsafe_allow_html=True)

elif page == "Coin Scanner":
    page_header("Coin Scanner", "วิเคราะห์และจัดอันดับ 20 เหรียญ")
    f1,f2,f3 = st.columns(3)
    min_score = f1.slider("คะแนนขั้นต่ำ", 0, 100, 50)
    status_filter = f2.multiselect("สถานะ", ["READY","WATCH","WAIT","AVOID"], default=["READY","WATCH","WAIT"])
    trend_filter = f3.multiselect("Trend", ["Uptrend","Sideway Up","Sideway","Sideway Down","Downtrend"], default=[])
    filtered = [(n,p) for n,p in ranked if p["a"]["score"] >= min_score and p["a"]["status"] in status_filter and (not trend_filter or p["a"]["trend"] in trend_filter)]
    for start in range(0,len(filtered),4):
        cols = st.columns(4)
        for col,(name,payload) in zip(cols,filtered[start:start+4]):
            with col:
                coin_card(name,payload)
                if st.button(f"เปิด {name} ใน Chart Lab", key=f"chart_{name}"):
                    st.session_state["selected_coin"] = name
                    st.info(f"เลือก {name} แล้ว กรุณาเปิดเมนู Chart Lab")
    table = pd.DataFrame([{
        "Coin":n,"Score":p["a"]["score"],"Status":p["a"]["status"],"Trend":p["a"]["trend"],"RSI":p["a"]["rsi"],"Volume x":p["a"]["volume_ratio"],"24h %":p["change"]
    } for n,p in filtered])
    if not table.empty:
        st.dataframe(table, hide_index=True, use_container_width=True)

elif page == "Chart Lab":
    page_header("Chart Lab", "อ่านกราฟและแผนแบบมีเงื่อนไข")
    default_coin = st.session_state.get("selected_coin","ETH")
    coin = st.selectbox("เลือกเหรียญ", list(COINS.keys()), index=list(COINS.keys()).index(default_coin))
    p = market[coin]; a = p["a"]
    top1,top2,top3,top4 = st.columns(4)
    with top1: metric_card("Opportunity Score", f"{a['score']}/100", a["status"])
    with top2: metric_card("Trend", a["trend"], f"EMA20 {money(a['ema20'])}")
    with top3: metric_card("RSI", str(a["rsi"]), "แรงซื้อ/แรงขาย")
    with top4: metric_card("Volume", f"{a['volume_ratio']}x", f"Volatility {a['volatility']}%")
    left,right = st.columns([1.7,1])
    with left:
        st.plotly_chart(candle_chart(p["df"],coin,a),use_container_width=True,config={"displayModeBar":False})
    with right:
        st.markdown(f"""
        <div class="ui-card">
        <div class="level"><span>แนวรับ</span><b>{money(a['support'])}</b></div>
        <div class="level"><span>แนวต้าน</span><b>{money(a['resistance'])}</b></div>
        <div class="level"><span>Trigger</span><b>{money(a['trigger'])}</b></div>
        <div class="level"><span>Stop Loss</span><b>{money(a['stop'])}</b></div>
        <div class="level"><span>Target 1</span><b>{money(a['target1'])}</b></div>
        <div class="level"><span>Target 2</span><b>{money(a['target2'])}</b></div>
        </div>
        """, unsafe_allow_html=True)
        st.plotly_chart(probability_chart(a),use_container_width=True,config={"displayModeBar":False})
    st.markdown('<div class="coach"><b>AI Explanation</b><br><br>' + ("เงื่อนไขเริ่มน่าสนใจ แต่ยังต้องยืนยันด้วยราคาและ Volume" if a["status"] in ("READY","WATCH") else "สัญญาณยังไม่ชัด ให้ใช้เพื่อเรียนรู้มากกว่าวางแผนเข้า") + '</div>', unsafe_allow_html=True)

elif page == "Trade Plan":
    page_header("Trade Plan & Paper Portfolio", "ทดลองโดยไม่ใช้เงินจริง")
    decision_box()
    if risk_remaining <= 0:
        st.error("STOP FOR TODAY — ถึงขีดจำกัดความเสี่ยงรายวันแล้ว")
    coin = st.selectbox("เหรียญสำหรับแผนจำลอง", list(COINS.keys()))
    a = market[coin]["a"]
    c1,c2,c3 = st.columns(3)
    entry = c1.number_input("Entry จำลอง", value=float(a["trigger"]), format="%.8f")
    stop = c2.number_input("Stop Loss", value=float(a["stop"]), format="%.8f")
    target = c3.number_input("Take Profit", value=float(a["target1"]), format="%.8f")
    risk = st.slider("ความเสี่ยงจำลองต่อแผน (บาท)",10,int(max(10,min(max_daily_loss,risk_remaining))),int(min(per_trade_risk,max(10,risk_remaining))),step=10)
    stop_pct = abs(entry-stop)/entry if entry else 0
    position = min(float(capital), risk/stop_pct if stop_pct else 0)
    m1,m2,m3 = st.columns(3)
    m1.metric("ระยะ Stop",f"{stop_pct*100:.2f}%")
    m2.metric("ขนาดสถานะ",f"{position:,.2f} บาท")
    rr = (target-entry)/(entry-stop) if entry>stop else 0
    m3.metric("Risk/Reward",f"1:{rr:.2f}")
    reason = st.text_area("เหตุผลของแผน", value=f"Score {a['score']} • Trend {a['trend']} • RSI {a['rsi']} • รอ Trigger")
    if st.button("สร้าง Paper Trade", disabled=(risk_remaining<=0 or entry<=stop or target<=entry)):
        st.session_state.paper_trades.append({"created":now.strftime("%Y-%m-%d"),"coin":coin,"entry":entry,"stop":stop,"target":target,"risk":risk,"position":position,"status":"OPEN","current":market[coin]["price"],"pnl":0.0,"reason":reason})
        st.success("สร้าง Paper Trade แล้ว ระบบจะติดตามเมื่อรีเฟรชแอป")
    st.markdown('<div class="section-title">Paper Portfolio</div>',unsafe_allow_html=True)
    if st.session_state.paper_trades:
        tdf = pd.DataFrame(st.session_state.paper_trades)
        st.dataframe(tdf[["created","coin","entry","stop","target","status","current","pnl","reason"]],hide_index=True,use_container_width=True)
        st.download_button("ดาวน์โหลด Paper Trades CSV",tdf.to_csv(index=False).encode("utf-8-sig"),f"paper_trades_{now:%Y%m%d}.csv","text/csv")
    else:
        st.info("ยังไม่มี Paper Trade")

elif page == "Journal":
    page_header("Trading Journal", "บันทึกการตัดสินใจและบทเรียน")
    with st.form("journal_form",clear_on_submit=True):
        c1,c2 = st.columns(2)
        date = c1.date_input("วันที่",value=now.date())
        coin = c2.selectbox("เหรียญ",["ยังไม่ได้เลือก"]+list(COINS.keys()))
        decision_j = st.selectbox("Decision",["WAIT","WATCH","READY","PAPER TRADE","STOP FOR TODAY"])
        result = st.number_input("ผลลัพธ์จำลอง (บาท)",value=0.0,step=1.0)
        emotion = st.select_slider("อารมณ์",["กังวล","ลังเล","ปกติ","มั่นใจ","มั่นใจมาก"],value="ปกติ")
        lesson = st.text_area("บทเรียน")
        submitted = st.form_submit_button("บันทึก Journal")
    if submitted:
        st.session_state.journal.append({"วันที่":str(date),"เหรียญ":coin,"Decision":decision_j,"ผลลัพธ์":result,"อารมณ์":emotion,"บทเรียน":lesson})
        st.success("บันทึกเรียบร้อย")
    if st.session_state.journal:
        jdf = pd.DataFrame(st.session_state.journal)
        st.dataframe(jdf,hide_index=True,use_container_width=True)
        st.download_button("ดาวน์โหลด Journal CSV",jdf.to_csv(index=False).encode("utf-8-sig"),f"journal_{now:%Y%m%d}.csv","text/csv")
    else:
        st.info("ยังไม่มีบันทึก")

else:
    page_header("Learning Path", "เรียนทีละขั้น ไม่เร่งใช้เงินจริง")
    weeks = [
        ("Week 1","อ่าน Market Score, Trend, RSI และ Decision","75%"),
        ("Week 2","EMA20/EMA50, Volume, Support และ Resistance","0%"),
        ("Week 3","Trigger, Stop Loss, Target และ Risk/Reward","0%"),
        ("Week 4","Paper Trading, Journal และทบทวนความผิดพลาด","0%"),
    ]
    for w,title,progress in weeks:
        st.markdown(f'<div class="ui-card"><div class="section-kicker">{w}</div><div class="section-title">{title}</div><div class="metric-note">ความคืบหน้า {progress}</div></div><br>',unsafe_allow_html=True)
    st.markdown('<div class="coach"><b>กฎสำคัญ</b><br><br>• ไม่จำเป็นต้องเทรดทุกวัน<br>• ไม่มี Stop Loss = ไม่มีแผน<br>• เป้าหมายแรกคือวินัย ไม่ใช่กำไรสูงสุด<br>• ผลลัพธ์ Paper Trading ต้องทดสอบอย่างน้อย 30–50 แผน</div>',unsafe_allow_html=True)

st.caption("Wisalsaya Crypto Decision Lab v3.0 Full Premium Edition • วิเคราะห์เพื่อการศึกษาและ Paper Trading เท่านั้น • ไม่มีคำสั่งซื้อขายอัตโนมัติ")
