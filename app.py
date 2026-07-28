from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
import io

import numpy as np
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Wisalsaya Crypto Dashboard",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------------------
# Personal configuration
# ----------------------------
CAPITAL_THB = 1_000
MAX_DAILY_LOSS_THB = 150
DAILY_GOAL_MIN_THB = 20
DAILY_GOAL_MAX_THB = 50

DEFAULT_HOLDINGS = {
    "BNB": 0.42677969,
    "ETH": 0.03004642,
    "DOGE": 287.712,
}

SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "DOGE": "DOGEUSDT",
}

# ----------------------------
# Style
# ----------------------------
st.markdown(
    """
    <style>
    :root {
        --navy-1: #07131f;
        --navy-2: #0b2030;
        --card: rgba(16, 40, 55, 0.90);
        --gold: #e8c875;
        --emerald: #65d6b0;
        --muted: #a9bac7;
        --white: #f7f9fb;
        --danger: #ff9ca9;
    }

    .stApp {
        background:
          radial-gradient(circle at 85% 0%, rgba(26,75,86,.55), transparent 30%),
          linear-gradient(145deg, var(--navy-1), var(--navy-2));
        color: var(--white);
    }

    .block-container {
        max-width: 1120px;
        padding-top: 1.25rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 { color: var(--white); }

    .hero-title {
        font-size: clamp(1.75rem, 5vw, 2.8rem);
        font-weight: 800;
        letter-spacing: -0.045em;
        margin-bottom: .15rem;
    }

    .hero-subtitle {
        color: var(--muted);
        font-size: .92rem;
        margin-bottom: 1rem;
    }

    .decision {
        background:
          linear-gradient(135deg, rgba(23,87,78,.98), rgba(10,43,59,.97));
        border: 1px solid rgba(232,200,117,.55);
        border-radius: 25px;
        padding: 1.3rem;
        box-shadow: 0 18px 45px rgba(0,0,0,.25);
        margin-bottom: .9rem;
    }

    .card {
        background: var(--card);
        border: 1px solid rgba(232,200,117,.18);
        border-radius: 21px;
        padding: 1.05rem;
        box-shadow: 0 10px 30px rgba(0,0,0,.18);
        margin-bottom: .75rem;
    }

    .eyebrow {
        color: var(--muted);
        font-size: .74rem;
        font-weight: 700;
        letter-spacing: .10em;
        text-transform: uppercase;
    }

    .score {
        color: var(--gold);
        font-size: 2.25rem;
        font-weight: 850;
        line-height: 1.1;
        margin-top: .25rem;
    }

    .decision-title {
        color: var(--white);
        font-size: 1.08rem;
        font-weight: 750;
        margin-top: .45rem;
    }

    .muted {
        color: var(--muted);
        font-size: .84rem;
        line-height: 1.55;
    }

    .coin {
        font-size: 1.22rem;
        font-weight: 800;
    }

    .price {
        color: var(--gold);
        font-size: 1.28rem;
        font-weight: 800;
        margin-top: .3rem;
    }

    .positive { color: var(--emerald); font-weight: 750; }
    .negative { color: var(--danger); font-weight: 750; }
    .neutral { color: var(--gold); font-weight: 750; }

    div[data-testid="stMetric"] {
        background: rgba(16,40,55,.88);
        border: 1px solid rgba(232,200,117,.16);
        border-radius: 18px;
        padding: .9rem;
    }

    div[data-testid="stMetricLabel"] { color: var(--muted); }
    div[data-testid="stMetricValue"] { color: var(--white); }

    .stButton > button, .stDownloadButton > button {
        width: 100%;
        border-radius: 14px;
        min-height: 44px;
        font-weight: 750;
        border: 1px solid rgba(232,200,117,.50);
        background: #17464a;
        color: white;
    }

    .stButton > button:hover, .stDownloadButton > button:hover {
        border-color: var(--gold);
        color: var(--gold);
    }

    @media (max-width: 640px) {
        .block-container { padding-left: .75rem; padding-right: .75rem; }
        .decision, .card { border-radius: 18px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------
# Data
# ----------------------------
@st.cache_data(ttl=60)
def fetch_ticker(symbol: str) -> dict:
    endpoints = [
        "https://data-api.binance.vision",
        "https://api.binance.com",
    ]
    last_error = None

    for base in endpoints:
        try:
            response = requests.get(
                f"{base}/api/v3/ticker/24hr",
                params={"symbol": symbol},
                timeout=8,
            )
            response.raise_for_status()
            payload = response.json()
            return {
                "price": float(payload["lastPrice"]),
                "change_24h": float(payload["priceChangePercent"]),
                "high_24h": float(payload["highPrice"]),
                "low_24h": float(payload["lowPrice"]),
                "quote_volume": float(payload["quoteVolume"]),
                "source": base,
            }
        except (requests.RequestException, KeyError, ValueError) as exc:
            last_error = exc

    raise RuntimeError(f"Market data unavailable: {last_error}")


@st.cache_data(ttl=60)
def fetch_klines(symbol: str, interval: str = "15m", limit: int = 200) -> pd.DataFrame:
    endpoints = [
        "https://data-api.binance.vision",
        "https://api.binance.com",
    ]
    last_error = None

    for base in endpoints:
        try:
            response = requests.get(
                f"{base}/api/v3/klines",
                params={"symbol": symbol, "interval": interval, "limit": limit},
                timeout=8,
            )
            response.raise_for_status()
            rows = response.json()

            frame = pd.DataFrame(
                rows,
                columns=[
                    "open_time", "open", "high", "low", "close", "volume",
                    "close_time", "quote_volume", "trades", "taker_base",
                    "taker_quote", "ignore",
                ],
            )
            for col in ["open", "high", "low", "close", "volume"]:
                frame[col] = pd.to_numeric(frame[col], errors="coerce")

            frame["time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
            return frame.dropna(subset=["close"])
        except (requests.RequestException, ValueError) as exc:
            last_error = exc

    raise RuntimeError(f"Kline data unavailable: {last_error}")


@st.cache_data(ttl=900)
def fetch_fear_greed() -> dict:
    try:
        response = requests.get(
            "https://api.alternative.me/fng/",
            params={"limit": 1, "format": "json"},
            timeout=8,
        )
        response.raise_for_status()
        item = response.json()["data"][0]
        return {
            "value": int(item["value"]),
            "label": str(item["value_classification"]),
        }
    except Exception:
        return {"value": 50, "label": "Neutral (fallback)"}


def rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    value = 100 - (100 / (1 + rs))
    return float(value.iloc[-1]) if pd.notna(value.iloc[-1]) else 50.0


def analyse(ticker: dict, frame: pd.DataFrame, sentiment: dict) -> dict:
    df = frame.copy()
    df["ema20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema50"] = df["close"].ewm(span=50, adjust=False).mean()

    close = float(df["close"].iloc[-1])
    ema20 = float(df["ema20"].iloc[-1])
    ema50 = float(df["ema50"].iloc[-1])
    rsi_value = rsi(df["close"])

    recent = df.tail(24)
    support = float(recent["low"].min())
    resistance = float(recent["high"].max())

    average_volume = float(df["volume"].tail(20).mean())
    volume_ratio = float(df["volume"].iloc[-1] / average_volume) if average_volume else 1.0
    range_pct = float((recent["high"].max() - recent["low"].min()) / close * 100)

    trend_score = 8
    trend_score += 8 if close > ema20 else 0
    trend_score += 8 if ema20 > ema50 else 0
    trend_score += 6 if ticker["change_24h"] > 0 else 0
    trend_score = min(trend_score, 30)

    if 52 <= rsi_value <= 68:
        momentum_score = 22
    elif 45 <= rsi_value < 52 or 68 < rsi_value <= 75:
        momentum_score = 16
    elif 35 <= rsi_value < 45:
        momentum_score = 10
    else:
        momentum_score = 6

    if volume_ratio >= 1.50:
        volume_score = 20
    elif volume_ratio >= 1.10:
        volume_score = 15
    elif volume_ratio >= 0.75:
        volume_score = 10
    else:
        volume_score = 6

    if 1.0 <= range_pct <= 4.5:
        volatility_score = 13
    elif range_pct < 1.0:
        volatility_score = 7
    else:
        volatility_score = 8

    fear_value = sentiment["value"]
    if 35 <= fear_value <= 70:
        sentiment_score = 8
    elif 20 <= fear_value < 35 or 70 < fear_value <= 80:
        sentiment_score = 6
    else:
        sentiment_score = 4

    total = int(round(
        trend_score + momentum_score + volume_score +
        volatility_score + sentiment_score
    ))

    if close > ema20 > ema50:
        trend = "Sideway Up"
        probs = (58, 24, 18)
    elif close < ema20 < ema50:
        trend = "Sideway Down"
        probs = (18, 25, 57)
    else:
        trend = "Sideway"
        probs = (35, 35, 30)

    return {
        "score": min(total, 100),
        "trend": trend,
        "rsi": round(rsi_value, 1),
        "support": support,
        "resistance": resistance,
        "up": probs[0],
        "sideway": probs[1],
        "down": probs[2],
        "trend_score": trend_score,
        "momentum_score": momentum_score,
        "volume_score": volume_score,
        "volatility_score": volatility_score,
        "sentiment_score": sentiment_score,
    }


def decision(score: int) -> tuple[str, str]:
    if score >= 80:
        return (
            "🟢 มีโอกาสเกิดจังหวะมากกว่าปกติ",
            "เฝ้ารอการยืนยันเหนือโซนสำคัญ ไม่ไล่ราคา",
        )
    if score >= 65:
        return (
            "🟡 เฝ้าระวัง",
            "ตลาดมีแรงบางส่วน แต่ยังไม่ชัดพอให้รีบตัดสินใจ",
        )
    return (
        "⚪ วันนี้เหมาะกับการรอ",
        "เป้าหมายหลักคือรักษาเงินต้นและฝึกอ่านรูปแบบตลาด",
    )


def usd(value: float) -> str:
    return f"${value:,.2f}" if value >= 1 else f"${value:,.5f}"


# ----------------------------
# Header
# ----------------------------
now = datetime.now(ZoneInfo("Asia/Bangkok"))
st.markdown('<div class="hero-title">Wisalsaya Crypto Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="hero-subtitle">Morning Brief • {now:%d/%m/%Y %H:%M} น. • สำหรับผู้เริ่มต้น</div>',
    unsafe_allow_html=True,
)

sentiment = fetch_fear_greed()
results = {}

try:
    for name in ["BTC", "ETH", "BNB", "DOGE"]:
        ticker = fetch_ticker(SYMBOLS[name])
        frame = fetch_klines(SYMBOLS[name])
        results[name] = {**ticker, **analyse(ticker, frame, sentiment), "frame": frame}
except RuntimeError as exc:
    st.error("ไม่สามารถดึงข้อมูลตลาดได้ในขณะนี้ กรุณากด Refresh อีกครั้ง")
    st.caption(str(exc))
    st.stop()

core_scores = [results[name]["score"] for name in ["BTC", "ETH", "BNB"]]
market_score = int(round(sum(core_scores) / len(core_scores)))
decision_title, decision_detail = decision(market_score)

st.markdown(
    f"""
    <div class="decision">
      <div class="eyebrow">Today's Decision</div>
      <div class="score">{market_score}/100</div>
      <div class="decision-title">{decision_title}</div>
      <div class="muted">{decision_detail}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2, m3, m4 = st.columns(4)
m1.metric("ทุนทดลอง", f"{CAPITAL_THB:,.0f} บาท")
m2.metric("เป้าหมายฝึก", f"{DAILY_GOAL_MIN_THB}–{DAILY_GOAL_MAX_THB} บาท")
m3.metric("ขาดทุนสูงสุด", f"{MAX_DAILY_LOSS_THB} บาท")
m4.metric("Fear & Greed", f'{sentiment["value"]}/100', sentiment["label"])

# ----------------------------
# Market radar
# ----------------------------
st.subheader("Market Radar")
cols = st.columns(3)

for col, name in zip(cols, ["BTC", "ETH", "BNB"]):
    item = results[name]
    css = "positive" if item["change_24h"] >= 0 else "negative"
    sign = "+" if item["change_24h"] >= 0 else ""
    with col:
        st.markdown(
            f"""
            <div class="card">
              <div class="coin">{name}</div>
              <div class="price">{usd(item["price"])}</div>
              <div class="{css}">{sign}{item["change_24h"]:.2f}% / 24 ชม.</div>
              <hr style="border-color:rgba(255,255,255,.08)">
              <div class="muted">
                Trend: <b>{item["trend"]}</b><br>
                Score: <b>{item["score"]}/100</b><br>
                RSI: <b>{item["rsi"]}</b>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------------------
# Detail
# ----------------------------
selected_name = st.selectbox("ดูรายละเอียด", ["BTC", "ETH", "BNB"])
selected = results[selected_name]

left, right = st.columns([1.2, 1])

with left:
    st.markdown("### ความน่าจะเป็นเชิงจำลอง")
    prob_df = pd.DataFrame(
        {
            "ทิศทาง": ["ขาขึ้น", "Sideway", "ขาลง"],
            "ความน่าจะเป็น (%)": [
                selected["up"],
                selected["sideway"],
                selected["down"],
            ],
        }
    )
    st.bar_chart(prob_df, x="ทิศทาง", y="ความน่าจะเป็น (%)")

with right:
    st.markdown("### โซนเฝ้าระวัง")
    st.markdown(
        f"""
        <div class="card">
          <div class="eyebrow">Resistance Zone</div>
          <div class="price">{usd(selected["resistance"])}</div>
          <div class="muted">
            หากราคายืนเหนือโซนนี้พร้อม Volume เพิ่ม
            ความน่าจะเป็นขาขึ้นจะเพิ่มขึ้น
          </div>
        </div>
        <div class="card">
          <div class="eyebrow">Support Zone</div>
          <div class="price">{usd(selected["support"])}</div>
          <div class="muted">
            หากราคาหลุดโซนนี้ จุดดังกล่าวคือจุดเฝ้าระวังแรงขาย
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with st.expander("ดูรายละเอียดคะแนน"):
    score_table = pd.DataFrame(
        {
            "องค์ประกอบ": ["Trend", "Momentum", "Volume", "Volatility", "Sentiment"],
            "คะแนน": [
                selected["trend_score"],
                selected["momentum_score"],
                selected["volume_score"],
                selected["volatility_score"],
                selected["sentiment_score"],
            ],
            "คะแนนเต็ม": [30, 25, 20, 15, 10],
        }
    )
    st.dataframe(score_table, hide_index=True, use_container_width=True)

# ----------------------------
# Portfolio snapshot
# ----------------------------
st.subheader("Portfolio Snapshot")
thb_per_usdt = st.number_input(
    "อัตราแลกเปลี่ยนโดยประมาณ (บาทต่อ USDT)",
    min_value=25.0,
    max_value=50.0,
    value=36.0,
    step=0.1,
    help="แก้ไขให้ตรงกับอัตราที่เห็นในแอป Binance TH",
)

holdings = {}
portfolio_rows = []
total_thb = 0.0

for name, default_qty in DEFAULT_HOLDINGS.items():
    qty = st.number_input(
        f"จำนวน {name}",
        min_value=0.0,
        value=float(default_qty),
        format="%.8f",
        key=f"qty_{name}",
    )
    holdings[name] = qty
    value_thb = qty * results[name]["price"] * thb_per_usdt
    total_thb += value_thb
    portfolio_rows.append({"สินทรัพย์": name, "จำนวน": qty, "มูลค่าโดยประมาณ (บาท)": value_thb})

portfolio_df = pd.DataFrame(portfolio_rows)
st.dataframe(
    portfolio_df.style.format({"จำนวน": "{:,.8f}", "มูลค่าโดยประมาณ (บาท)": "{:,.2f}"}),
    hide_index=True,
    use_container_width=True,
)
st.metric("มูลค่าพอร์ตโดยประมาณ", f"{total_thb:,.2f} บาท")

st.info(
    "Trading Lab แนะนำให้แยกจาก BNB และ ETH ระยะยาว "
    "โดยใช้เงินก้อนทดลอง 1,000 บาทและไม่เติมเงินเพื่อไล่ตามผลขาดทุน"
)

# ----------------------------
# Journal
# ----------------------------
st.subheader("Trading Lab Journal")

if "journal" not in st.session_state:
    st.session_state.journal = []

with st.form("journal_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    journal_date = c1.date_input("วันที่", value=now.date())
    coin = c2.selectbox("สินทรัพย์", ["ยังไม่ได้จำลอง", "BTC", "ETH", "BNB"])

    result_thb = st.number_input(
        "ผลลัพธ์วันนี้ (บาท)",
        min_value=-float(MAX_DAILY_LOSS_THB),
        max_value=1_000.0,
        value=0.0,
        step=1.0,
    )
    emotion = st.select_slider(
        "อารมณ์ก่อนตัดสินใจ",
        ["กังวล", "ลังเล", "ปกติ", "มั่นใจ", "มั่นใจมาก"],
        value="ปกติ",
    )
    lesson = st.text_area(
        "บทเรียนสั้น ๆ",
        placeholder="ตัวอย่าง: รอสัญญาณยืนยันได้ดี หรือเข้าเร็วเกินไป",
    )
    submitted = st.form_submit_button("บันทึก Journal")

if submitted:
    st.session_state.journal.append(
        {
            "วันที่": str(journal_date),
            "สินทรัพย์": coin,
            "ผลลัพธ์ (บาท)": result_thb,
            "อารมณ์": emotion,
            "บทเรียน": lesson,
        }
    )
    if result_thb <= -MAX_DAILY_LOSS_THB:
        st.warning("แตะขีดจำกัดขาดทุนรายวันแล้ว ให้หยุดการจำลองสำหรับวันนี้")
    else:
        st.success("บันทึก Journal แล้ว")

if st.session_state.journal:
    journal_df = pd.DataFrame(st.session_state.journal)
    st.dataframe(journal_df, hide_index=True, use_container_width=True)

    csv_bytes = journal_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "ดาวน์โหลด Journal เป็น CSV",
        data=csv_bytes,
        file_name=f"crypto_journal_{now:%Y%m%d}.csv",
        mime="text/csv",
    )

st.caption(
    "Dashboard นี้ใช้เพื่อฝึกอ่านข้อมูลทางเทคนิค ความน่าจะเป็น "
    "และการควบคุมความเสี่ยงเท่านั้น ไม่เชื่อมบัญชี Binance "
    "และไม่มีคำสั่งซื้อขายอัตโนมัติ"
)
