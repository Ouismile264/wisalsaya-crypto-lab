from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Wisalsaya Crypto Dashboard v2",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "BNB": "BNBUSDT", "DOGE": "DOGEUSDT"}
DEFAULT_HOLDINGS = {"BNB": 0.42677969, "ETH": 0.03004642, "DOGE": 287.712}

st.markdown("""
<style>
:root{--bg:#06131f;--bg2:#0a2130;--card:#0e2737;--gold:#efca72;--green:#68d7b1;--red:#ff8fa3;--text:#f7fafc;--muted:#a8bbc8}
.stApp{background:radial-gradient(circle at 85% 0%,rgba(21,91,94,.42),transparent 34%),linear-gradient(145deg,var(--bg),var(--bg2));color:var(--text)}
.block-container{max-width:1220px;padding-top:1.2rem;padding-bottom:3rem}
.hero-title{font-size:clamp(2rem,5vw,3.1rem);font-weight:850;letter-spacing:-.055em;line-height:1.05}
.hero-sub,.muted{color:var(--muted)}
.badge{display:inline-block;margin-top:.7rem;padding:.4rem .72rem;border-radius:999px;background:rgba(104,215,177,.1);border:1px solid rgba(239,202,114,.25);font-size:.75rem;font-weight:800}
.decision{background:linear-gradient(135deg,rgba(20,90,81,.97),rgba(10,43,59,.98));border:1px solid rgba(239,202,114,.55);border-radius:26px;padding:1.35rem;margin:.7rem 0 1rem;box-shadow:0 18px 46px rgba(0,0,0,.25)}
.score{font-size:2.7rem;font-weight:900;color:var(--gold);line-height:1}
.card{background:rgba(14,39,55,.93);border:1px solid rgba(239,202,114,.18);border-radius:22px;padding:1.05rem;margin-bottom:.8rem;box-shadow:0 10px 28px rgba(0,0,0,.16)}
.price{font-size:1.32rem;font-weight:850;color:var(--gold);margin:.35rem 0}
.positive{color:var(--green);font-weight:800}.negative{color:var(--red);font-weight:800}
div[data-testid="stMetric"]{background:rgba(14,39,55,.9);border:1px solid rgba(239,202,114,.18);border-radius:18px;padding:.85rem}
.stButton>button,.stDownloadButton>button{width:100%;min-height:44px;border-radius:14px;border:1px solid rgba(239,202,114,.5);background:#15474a;color:white;font-weight:800}
@media(max-width:720px){.block-container{padding-left:.75rem;padding-right:.75rem}.decision,.card{border-radius:18px}}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)
def ticker(symbol):
    for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
        try:
            r = requests.get(f"{base}/api/v3/ticker/24hr", params={"symbol": symbol}, timeout=8)
            r.raise_for_status()
            p = r.json()
            return {
                "price": float(p["lastPrice"]),
                "change": float(p["priceChangePercent"]),
                "high": float(p["highPrice"]),
                "low": float(p["lowPrice"]),
            }
        except Exception:
            pass
    raise RuntimeError("ไม่สามารถดึงราคาตลาดได้")


@st.cache_data(ttl=60)
def klines(symbol, interval="15m", limit=240):
    for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
        try:
            r = requests.get(
                f"{base}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                timeout=8,
            )
            r.raise_for_status()
            df = pd.DataFrame(r.json(), columns=[
                "open_time","open","high","low","close","volume",
                "close_time","quote_volume","trades","taker_base","taker_quote","ignore"
            ])
            for c in ["open","high","low","close","volume"]:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
            return df.dropna(subset=["close"])
        except Exception:
            pass
    raise RuntimeError("ไม่สามารถดึงกราฟตลาดได้")


@st.cache_data(ttl=900)
def fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/", params={"limit": 1}, timeout=8)
        r.raise_for_status()
        x = r.json()["data"][0]
        return int(x["value"]), x["value_classification"]
    except Exception:
        return 50, "Neutral"


def rsi(series, period=14):
    d = series.diff()
    gain = d.clip(lower=0).ewm(alpha=1/period, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/period, adjust=False).mean()
    value = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    return float(value.iloc[-1]) if pd.notna(value.iloc[-1]) else 50.0


def analyze(t, df, fng):
    x = df.copy()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    close, e20, e50 = float(x["close"].iloc[-1]), float(x["ema20"].iloc[-1]), float(x["ema50"].iloc[-1])
    rv = rsi(x["close"])
    recent = x.tail(32)
    vr = float(x["volume"].iloc[-1] / x["volume"].tail(20).mean())
    score = 8 + (8 if close > e20 else 0) + (8 if e20 > e50 else 0) + (6 if t["change"] > 0 else 0)
    score += 22 if 52 <= rv <= 68 else 16 if 45 <= rv <= 75 else 10 if 35 <= rv < 45 else 6
    score += 20 if vr >= 1.5 else 15 if vr >= 1.1 else 10 if vr >= .75 else 6
    score += 13 if 1 <= ((recent["high"].max()-recent["low"].min())/close*100) <= 4.5 else 8
    score += 8 if 35 <= fng <= 70 else 6 if 20 <= fng <= 80 else 4

    if close > e20 > e50:
        trend, probs = "Sideway Up", (58, 24, 18)
    elif close < e20 < e50:
        trend, probs = "Sideway Down", (18, 25, 57)
    else:
        trend, probs = "Sideway", (35, 35, 30)

    return {
        "score": min(int(round(score)), 100),
        "trend": trend,
        "rsi": round(rv, 1),
        "ema20": e20,
        "ema50": e50,
        "support": float(recent["low"].min()),
        "resistance": float(recent["high"].max()),
        "volume_ratio": round(vr, 2),
        "up": probs[0], "sideway": probs[1], "down": probs[2],
    }


def usd(v):
    return f"${v:,.2f}" if v >= 1 else f"${v:,.5f}"


def candle_chart(df, name):
    x = df.tail(120).copy()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=x["time"], open=x["open"], high=x["high"], low=x["low"], close=x["close"], name=name))
    fig.add_trace(go.Scatter(x=x["time"], y=x["ema20"], mode="lines", name="EMA 20"))
    fig.add_trace(go.Scatter(x=x["time"], y=x["ema50"], mode="lines", name="EMA 50"))
    fig.update_layout(
        height=470, margin=dict(l=10,r=10,t=20,b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce7ee"), xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="rgba(255,255,255,.06)")
    )
    return fig


def pie_chart(df):
    fig = go.Figure(data=[go.Pie(labels=df["Asset"], values=df["Value THB"], hole=.62, textinfo="label+percent")])
    fig.update_layout(height=360, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#dce7ee"), showlegend=False)
    return fig


with st.sidebar:
    st.header("⚙️ Personal Settings")
    capital = st.number_input("ทุน Trading Lab (บาท)", min_value=100, value=1000, step=100)
    max_loss = st.number_input("ขาดทุนสูงสุดต่อวัน (บาท)", min_value=10, value=150, step=10)
    goal_min = st.number_input("เป้าหมายขั้นต่ำ (บาท)", min_value=0, value=20, step=10)
    goal_max = st.number_input("เป้าหมายสูงสุด (บาท)", min_value=0, value=50, step=10)


fng_value, fng_label = fear_greed()
market = {}
try:
    for name, symbol in SYMBOLS.items():
        t = ticker(symbol)
        df = klines(symbol)
        market[name] = {**t, "df": df, "a": analyze(t, df, fng_value)}
except RuntimeError as e:
    st.error(str(e))
    st.stop()

now = datetime.now(ZoneInfo("Asia/Bangkok"))
st.markdown(f"""
<div class="hero-title">Wisalsaya Crypto Dashboard</div>
<div class="hero-sub">Version 2.0 • Morning Brief • {now:%d/%m/%Y %H:%M} น.</div>
<div class="badge">LIVE MARKET DATA • BEGINNER MODE</div>
""", unsafe_allow_html=True)

score = int(round(np.mean([market[x]["a"]["score"] for x in ["BTC","ETH","BNB"]])))
if score >= 80:
    label, main, note = "🟢 Opportunity Watch", "มีแรงสนับสนุนมากกว่าปกติ", "รอสัญญาณยืนยันและไม่ไล่ราคา"
elif score >= 65:
    label, main, note = "🟡 Watch Closely", "ตลาดเริ่มมีแรงแต่ยังไม่ชัด", "รอให้ราคาและ Volume ไปทิศทางเดียวกัน"
else:
    label, main, note = "⚪ Capital Protection", "วันนี้เหมาะกับการรอ", "รักษาเงินต้นและฝึกอ่านรูปแบบตลาด"

st.markdown(f"""
<div class="decision">
<div class="score">{score}/100</div>
<h3>{label}</h3>
<div>{main}</div>
<div class="muted">{note}</div>
</div>
""", unsafe_allow_html=True)

m1,m2,m3,m4 = st.columns(4)
m1.metric("ทุนทดลอง", f"{capital:,.0f} บาท")
m2.metric("เป้าหมายฝึก", f"{goal_min:,.0f}–{goal_max:,.0f} บาท")
m3.metric("ขาดทุนสูงสุด", f"{max_loss:,.0f} บาท")
m4.metric("Fear & Greed", f"{fng_value}/100", fng_label)

st.subheader("Market Radar")
cols = st.columns(3)
for col, name in zip(cols, ["BTC","ETH","BNB"]):
    x, a = market[name], market[name]["a"]
    cls, sign = ("positive","+") if x["change"] >= 0 else ("negative","")
    with col:
        st.markdown(f"""
        <div class="card">
        <h3>{name}</h3>
        <div class="price">{usd(x["price"])}</div>
        <div class="{cls}">{sign}{x["change"]:.2f}% / 24 ชม.</div><hr>
        <div class="muted">Trend: <b>{a["trend"]}</b><br>Score: <b>{a["score"]}/100</b><br>RSI: <b>{a["rsi"]}</b><br>Volume: <b>{a["volume_ratio"]}x</b></div>
        </div>
        """, unsafe_allow_html=True)

st.subheader("Chart Lab")
left,right = st.columns([1.8,1])
with left:
    asset = st.selectbox("เลือกสินทรัพย์", ["BTC","ETH","BNB"])
    st.plotly_chart(candle_chart(market[asset]["df"], asset), use_container_width=True, config={"displayModeBar":False})
with right:
    a = market[asset]["a"]
    st.markdown(f"""
    <div class="card"><b>Resistance</b><div class="price">{usd(a["resistance"])}</div><div class="muted">เฝ้าดูการยืนเหนือโซนพร้อม Volume</div></div>
    <div class="card"><b>Support</b><div class="price">{usd(a["support"])}</div><div class="muted">หลุดโซนนี้ให้ระวังแรงขาย</div></div>
    <div class="card"><b>Probability</b><div class="muted">Up {a["up"]}% • Sideway {a["sideway"]}% • Down {a["down"]}%</div></div>
    """, unsafe_allow_html=True)

st.subheader("Risk Calculator")
r1,r2,r3 = st.columns(3)
entry = r1.number_input("ราคาเข้าโดยประมาณ", min_value=.00001, value=float(market["BTC"]["price"]), format="%.5f")
stop = r2.number_input("จุดหยุดขาดทุน", min_value=.00001, value=float(market["BTC"]["price"]*.985), format="%.5f")
risk_budget = r3.number_input("งบเสี่ยงต่อรายการ (บาท)", min_value=1.0, max_value=float(max_loss), value=float(min(50,max_loss)), step=5.0)
risk_pct = abs(entry-stop)/entry*100
position = risk_budget/(risk_pct/100) if risk_pct else 0
c1,c2,c3 = st.columns(3)
c1.metric("ระยะ Stop Loss", f"{risk_pct:.2f}%")
c2.metric("ขนาดสถานะสูงสุด", f"{position:,.2f} บาท")
c3.metric("เทียบทุน", f"{position/capital*100:.1f}%")
if position > capital:
    st.warning("ขนาดสถานะจากสูตรสูงกว่าทุน Trading Lab ให้จำกัดไม่เกินทุนที่มีจริง")

st.subheader("Portfolio Snapshot")
rate = st.number_input("อัตราแลกเปลี่ยนโดยประมาณ (บาทต่อ USDT)", min_value=25.0, max_value=50.0, value=36.0, step=.1)
rows = []
for name, qty0 in DEFAULT_HOLDINGS.items():
    qty = st.number_input(f"จำนวน {name}", min_value=0.0, value=float(qty0), format="%.8f", key=f"qty_{name}")
    rows.append({"Asset":name,"Quantity":qty,"Price USDT":market[name]["price"],"Value THB":qty*market[name]["price"]*rate})
pdf = pd.DataFrame(rows)
p1,p2 = st.columns([1,1.15])
with p1:
    st.plotly_chart(pie_chart(pdf), use_container_width=True, config={"displayModeBar":False})
with p2:
    st.metric("มูลค่าพอร์ตโดยประมาณ", f"{pdf['Value THB'].sum():,.2f} บาท")
    st.dataframe(pdf.style.format({"Quantity":"{:,.8f}","Price USDT":"{:,.5f}","Value THB":"{:,.2f}"}), hide_index=True, use_container_width=True)

st.subheader("Morning Checklist")
q1,q2 = st.columns(2)
with q1:
    st.checkbox("ดู Market Score ก่อนดูราคา")
    st.checkbox("ดู BTC ก่อน ETH และ BNB")
    st.checkbox("กำหนด Stop Loss ก่อนจำลองรายการ")
with q2:
    st.checkbox("ไม่ไล่ราคา")
    st.checkbox("หยุดเมื่อแตะขาดทุนสูงสุด")
    st.checkbox("บันทึกบทเรียนหลังจบวัน")

st.subheader("Trading Journal")
if "journal_v2" not in st.session_state:
    st.session_state.journal_v2 = []
with st.form("journal_form", clear_on_submit=True):
    j1,j2 = st.columns(2)
    d = j1.date_input("วันที่", value=now.date())
    coin = j2.selectbox("สินทรัพย์", ["ยังไม่ได้จำลอง","BTC","ETH","BNB"])
    action = st.selectbox("การตัดสินใจ", ["รอ","เฝ้าดู","จำลองเข้า","หยุดตามแผน","ผิดแผน"])
    result = st.number_input("ผลลัพธ์วันนี้ (บาท)", min_value=-float(max_loss), max_value=1000.0, value=0.0, step=1.0)
    emotion = st.select_slider("อารมณ์", ["กังวล","ลังเล","ปกติ","มั่นใจ","มั่นใจมาก"], value="ปกติ")
    lesson = st.text_area("บทเรียนสั้น ๆ")
    submit = st.form_submit_button("บันทึก Journal")
if submit:
    st.session_state.journal_v2.append({"วันที่":str(d),"สินทรัพย์":coin,"การตัดสินใจ":action,"ผลลัพธ์ (บาท)":result,"อารมณ์":emotion,"บทเรียน":lesson})
    st.success("บันทึก Journal เรียบร้อยแล้ว")
if st.session_state.journal_v2:
    jdf = pd.DataFrame(st.session_state.journal_v2)
    st.dataframe(jdf, hide_index=True, use_container_width=True)
    st.download_button("ดาวน์โหลด Journal เป็น CSV", jdf.to_csv(index=False).encode("utf-8-sig"), f"wisalsaya_journal_{now:%Y%m%d}.csv", "text/csv")

st.caption("Version 2.0 • เพื่อฝึกอ่านตลาดและควบคุมความเสี่ยง ไม่มีการเชื่อม API Key และไม่มีคำสั่งซื้อขายอัตโนมัติ")
