from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

st.set_page_config(
    page_title="Wisalsaya Crypto Decision Lab 2.1",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

COINS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "LINK", "AVAX",
    "SUI", "TON", "NEAR", "APT", "ARB", "OP", "INJ", "DOT", "LTC", "BCH",
]
SYMBOLS = {coin: f"{coin}USDT" for coin in COINS}
DEFAULT_HOLDINGS = {"BNB": 0.42677969, "ETH": 0.03004642, "DOGE": 287.712}
TH_TZ = ZoneInfo("Asia/Bangkok")

st.markdown(
    """
<style>
:root{--bg:#06131f;--bg2:#0a2130;--card:#0e2737;--gold:#efca72;--green:#68d7b1;--red:#ff8fa3;--blue:#72b9ff;--text:#f7fafc;--muted:#a8bbc8}
.stApp{background:radial-gradient(circle at 85% 0%,rgba(21,91,94,.42),transparent 34%),linear-gradient(145deg,var(--bg),var(--bg2));color:var(--text)}
.block-container{max-width:1320px;padding-top:1.1rem;padding-bottom:3rem}
.hero-title{font-size:clamp(2rem,5vw,3.15rem);font-weight:850;letter-spacing:-.055em;line-height:1.05}
.hero-sub,.muted{color:var(--muted)}
.badge{display:inline-block;margin-top:.7rem;padding:.4rem .72rem;border-radius:999px;background:rgba(104,215,177,.1);border:1px solid rgba(239,202,114,.25);font-size:.75rem;font-weight:800}
.decision{background:linear-gradient(135deg,rgba(20,90,81,.97),rgba(10,43,59,.98));border:1px solid rgba(239,202,114,.55);border-radius:26px;padding:1.35rem;margin:.7rem 0 1rem;box-shadow:0 18px 46px rgba(0,0,0,.25)}
.score{font-size:2.7rem;font-weight:900;color:var(--gold);line-height:1}
.card{background:rgba(14,39,55,.93);border:1px solid rgba(239,202,114,.18);border-radius:22px;padding:1.05rem;margin-bottom:.8rem;box-shadow:0 10px 28px rgba(0,0,0,.16)}
.price{font-size:1.32rem;font-weight:850;color:var(--gold);margin:.35rem 0}
.positive{color:var(--green);font-weight:800}.negative{color:var(--red);font-weight:800}.neutral{color:var(--blue);font-weight:800}
.ready{color:var(--green);font-weight:850}.watch{color:var(--gold);font-weight:850}.wait{color:var(--muted);font-weight:850}.avoid{color:var(--red);font-weight:850}
div[data-testid="stMetric"]{background:rgba(14,39,55,.9);border:1px solid rgba(239,202,114,.18);border-radius:18px;padding:.85rem}
.stButton>button,.stDownloadButton>button{width:100%;min-height:44px;border-radius:14px;border:1px solid rgba(239,202,114,.5);background:#15474a;color:white;font-weight:800}
[data-testid="stDataFrame"]{border-radius:16px;overflow:hidden}
@media(max-width:720px){.block-container{padding-left:.75rem;padding-right:.75rem}.decision,.card{border-radius:18px}}
</style>
""",
    unsafe_allow_html=True,
)


def api_get(path: str, params: dict | None = None) -> dict | list:
    last_error: Exception | None = None
    for base in ["https://data-api.binance.vision", "https://api.binance.com"]:
        try:
            response = requests.get(f"{base}{path}", params=params, timeout=12)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise RuntimeError(f"ไม่สามารถดึงข้อมูลตลาดได้: {last_error}")


@st.cache_data(ttl=90)
def all_tickers() -> dict[str, dict[str, float]]:
    payload = api_get("/api/v3/ticker/24hr")
    wanted = set(SYMBOLS.values())
    result: dict[str, dict[str, float]] = {}
    for item in payload:
        symbol = item.get("symbol")
        if symbol in wanted:
            result[symbol] = {
                "price": float(item["lastPrice"]),
                "change": float(item["priceChangePercent"]),
                "high": float(item["highPrice"]),
                "low": float(item["lowPrice"]),
                "quote_volume": float(item.get("quoteVolume", 0)),
            }
    return result


@st.cache_data(ttl=180)
def klines(symbol: str, interval: str = "4h", limit: int = 220) -> pd.DataFrame:
    payload = api_get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": limit})
    df = pd.DataFrame(
        payload,
        columns=[
            "open_time", "open", "high", "low", "close", "volume", "close_time",
            "quote_volume", "trades", "taker_base", "taker_quote", "ignore",
        ],
    )
    for column in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    df["time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True).dt.tz_convert(TH_TZ)
    return df.dropna(subset=["close"]).reset_index(drop=True)


@st.cache_data(ttl=900)
def fear_greed() -> tuple[int, str]:
    try:
        response = requests.get("https://api.alternative.me/fng/", params={"limit": 1}, timeout=8)
        response.raise_for_status()
        item = response.json()["data"][0]
        return int(item["value"]), item["value_classification"]
    except Exception:  # noqa: BLE001
        return 50, "Neutral"


def calc_rsi(series: pd.Series, period: int = 14) -> float:
    delta = series.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gain / loss.replace(0, np.nan)
    value = 100 - (100 / (1 + rs))
    return float(value.iloc[-1]) if pd.notna(value.iloc[-1]) else 50.0


def normalize_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def analyze_coin(ticker_data: dict[str, float], df: pd.DataFrame, fng: int, btc_trend: str | None = None) -> dict:
    x = df.copy()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    x["return"] = x["close"].pct_change()

    close = float(x["close"].iloc[-1])
    ema20 = float(x["ema20"].iloc[-1])
    ema50 = float(x["ema50"].iloc[-1])
    rsi = calc_rsi(x["close"])
    volume_ratio = float(x["volume"].iloc[-1] / max(x["volume"].tail(20).mean(), 1e-12))
    volatility_pct = float(x["return"].tail(20).std() * np.sqrt(20) * 100)
    momentum_3 = float((close / x["close"].iloc[-4] - 1) * 100) if len(x) >= 4 else 0
    recent = x.tail(36)
    support = float(recent["low"].quantile(0.08))
    resistance = float(recent["high"].quantile(0.92))

    if close > ema20 > ema50:
        trend = "Uptrend"
        trend_score = 86
    elif close > ema20 and ema20 <= ema50:
        trend = "Sideway Up"
        trend_score = 70
    elif close < ema20 < ema50:
        trend = "Downtrend"
        trend_score = 28
    elif close < ema20 and ema20 >= ema50:
        trend = "Sideway Down"
        trend_score = 42
    else:
        trend = "Sideway"
        trend_score = 55

    if 52 <= rsi <= 66:
        momentum_score = 82
    elif 45 <= rsi < 52 or 66 < rsi <= 70:
        momentum_score = 68
    elif 35 <= rsi < 45:
        momentum_score = 50
    elif rsi > 75:
        momentum_score = 42
    else:
        momentum_score = 35
    momentum_score += max(-10, min(10, momentum_3 * 2))

    if volume_ratio >= 1.5:
        volume_score = 88
    elif volume_ratio >= 1.1:
        volume_score = 74
    elif volume_ratio >= 0.8:
        volume_score = 58
    else:
        volume_score = 40

    if 1.2 <= volatility_pct <= 6:
        volatility_score = 76
    elif volatility_pct < 1.2:
        volatility_score = 55
    elif volatility_pct <= 9:
        volatility_score = 60
    else:
        volatility_score = 38

    news_score = 65 if 35 <= fng <= 70 else 52 if 20 <= fng <= 80 else 40
    market_alignment = 65
    if btc_trend:
        if btc_trend in {"Uptrend", "Sideway Up"}:
            market_alignment = 78
        elif btc_trend in {"Downtrend", "Sideway Down"}:
            market_alignment = 35

    overall = (
        trend_score * 0.28
        + momentum_score * 0.22
        + volume_score * 0.18
        + volatility_score * 0.12
        + news_score * 0.08
        + market_alignment * 0.12
    )
    score = normalize_score(overall)

    if score >= 75 and trend in {"Uptrend", "Sideway Up"} and rsi <= 70:
        status = "READY"
    elif score >= 60 and trend not in {"Downtrend"}:
        status = "WATCH"
    elif score < 45 or trend == "Downtrend":
        status = "AVOID"
    else:
        status = "WAIT"

    up = normalize_score(18 + trend_score * 0.42 + momentum_score * 0.18 + market_alignment * 0.12)
    down = normalize_score(18 + (100 - trend_score) * 0.38 + (100 - momentum_score) * 0.16)
    sideway = max(10, 100 - up - down)
    total = up + down + sideway
    up, down, sideway = [round(v / total * 100) for v in (up, down, sideway)]
    sideway += 100 - up - down - sideway

    return {
        "score": score,
        "status": status,
        "trend": trend,
        "rsi": round(rsi, 1),
        "ema20": ema20,
        "ema50": ema50,
        "support": support,
        "resistance": resistance,
        "volume_ratio": round(volume_ratio, 2),
        "volatility_pct": round(volatility_pct, 2),
        "momentum_3": round(momentum_3, 2),
        "trend_score": normalize_score(trend_score),
        "momentum_score": normalize_score(momentum_score),
        "volume_score": normalize_score(volume_score),
        "volatility_score": normalize_score(volatility_score),
        "news_score": normalize_score(news_score),
        "up": up,
        "sideway": sideway,
        "down": down,
    }


def usd(value: float) -> str:
    if value >= 1000:
        return f"${value:,.0f}"
    if value >= 1:
        return f"${value:,.3f}"
    return f"${value:,.6f}"


def candle_chart(df: pd.DataFrame, name: str, support: float, resistance: float) -> go.Figure:
    x = df.tail(120).copy()
    x["ema20"] = x["close"].ewm(span=20, adjust=False).mean()
    x["ema50"] = x["close"].ewm(span=50, adjust=False).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=x["time"], open=x["open"], high=x["high"], low=x["low"], close=x["close"], name=name))
    fig.add_trace(go.Scatter(x=x["time"], y=x["ema20"], mode="lines", name="EMA 20"))
    fig.add_trace(go.Scatter(x=x["time"], y=x["ema50"], mode="lines", name="EMA 50"))
    fig.add_hline(y=support, line_dash="dot", annotation_text="Support")
    fig.add_hline(y=resistance, line_dash="dot", annotation_text="Resistance")
    fig.update_layout(
        height=500,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#dce7ee"),
        xaxis_rangeslider_visible=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(gridcolor="rgba(255,255,255,.06)"),
        legend=dict(orientation="h"),
    )
    return fig


def init_state() -> None:
    st.session_state.setdefault("paper_trades", [])
    st.session_state.setdefault("journal_v21", [])


def update_paper_trades(prices: dict[str, float]) -> None:
    for trade in st.session_state.paper_trades:
        if trade["status"] != "OPEN":
            continue
        current = prices.get(trade["coin"], trade["entry"])
        trade["current"] = current
        if current <= trade["stop"]:
            trade["status"] = "STOPPED"
            trade["exit"] = trade["stop"]
        elif current >= trade["target"]:
            trade["status"] = "TARGET"
            trade["exit"] = trade["target"]
        else:
            trade["exit"] = current
        trade["pnl"] = (trade["exit"] / trade["entry"] - 1) * trade["position_thb"]


def daily_realized_pnl(today: str) -> float:
    return float(
        sum(
            trade.get("pnl", 0.0)
            for trade in st.session_state.paper_trades
            if trade.get("date") == today and trade.get("status") in {"STOPPED", "TARGET", "CLOSED"}
        )
    )


init_state()
now = datetime.now(TH_TZ)
today = now.date().isoformat()

with st.sidebar:
    st.header("⚙️ Personal Settings")
    capital = st.number_input("ทุน Paper Trading (บาท)", min_value=100, value=1000, step=100)
    max_loss = st.number_input("ขาดทุนสูงสุดต่อวัน (บาท)", min_value=10, value=150, step=10)
    risk_per_trade = st.number_input("ความเสี่ยงต่อแผน (บาท)", min_value=10, max_value=int(max_loss), value=min(50, int(max_loss)), step=10)
    interval = st.selectbox("Timeframe สำหรับ Scanner", ["1h", "4h", "1d"], index=1)
    top_n = st.slider("จำนวนเหรียญเด่นบนหน้าแรก", 3, 10, 5)
    st.caption("ข้อมูลราคาใช้ Binance Public Market Data โดยไม่ใช้ API Key")

fng_value, fng_label = fear_greed()
try:
    ticker_map = all_tickers()
    missing = [symbol for symbol in SYMBOLS.values() if symbol not in ticker_map]
    if missing:
        st.warning(f"ไม่พบข้อมูลบางเหรียญ: {', '.join(missing)}")

    btc_df = klines(SYMBOLS["BTC"], interval)
    btc_base = analyze_coin(ticker_map[SYMBOLS["BTC"]], btc_df, fng_value)
    market: dict[str, dict] = {
        "BTC": {**ticker_map[SYMBOLS["BTC"]], "df": btc_df, "a": btc_base}
    }
    progress = st.progress(0, text="กำลังวิเคราะห์ตลาด 20 เหรียญ...")
    for index, coin in enumerate(COINS[1:], start=1):
        symbol = SYMBOLS[coin]
        if symbol not in ticker_map:
            continue
        df = klines(symbol, interval)
        analysis = analyze_coin(ticker_map[symbol], df, fng_value, btc_base["trend"])
        market[coin] = {**ticker_map[symbol], "df": df, "a": analysis}
        progress.progress(index / (len(COINS) - 1), text=f"กำลังวิเคราะห์ {coin}...")
    progress.empty()
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

prices = {coin: data["price"] for coin, data in market.items()}
update_paper_trades(prices)
realized_today = daily_realized_pnl(today)
remaining_risk = max(0.0, max_loss + min(realized_today, 0.0))

scanner_rows = []
for coin, data in market.items():
    a = data["a"]
    scanner_rows.append(
        {
            "Coin": coin,
            "Price": data["price"],
            "24h %": data["change"],
            "Score": a["score"],
            "Status": a["status"],
            "Trend": a["trend"],
            "RSI": a["rsi"],
            "Volume x": a["volume_ratio"],
            "Volatility %": a["volatility_pct"],
            "Up %": a["up"],
            "Sideway %": a["sideway"],
            "Down %": a["down"],
        }
    )
scanner_df = pd.DataFrame(scanner_rows).sort_values(["Score", "Volume x"], ascending=[False, False]).reset_index(drop=True)
market_score = int(round(scanner_df.loc[scanner_df["Coin"].isin(["BTC", "ETH", "BNB"]), "Score"].mean()))

if realized_today <= -max_loss:
    label, main, note = "🛑 STOP FOR TODAY", "แตะขีดจำกัดขาดทุนจำลองแล้ว", "หยุดสร้างแผนใหม่และทบทวน Journal"
elif market_score >= 75 and btc_base["trend"] in {"Uptrend", "Sideway Up"}:
    label, main, note = "🟢 OPPORTUNITY", "มีโอกาสเกิดจังหวะมากกว่าปกติ", "เลือกเฉพาะเหรียญที่ READY และรอสัญญาณยืนยัน"
elif market_score >= 60:
    label, main, note = "🟡 WATCH", "ตลาดเริ่มน่าสนใจแต่ยังไม่ชัด", "ยังไม่ไล่ราคา ให้ดู Trend และ Volume ไปทางเดียวกัน"
else:
    label, main, note = "⚪ WAIT", "วันนี้เหมาะกับการรอ", "รักษาเงินต้นและฝึกอ่านรูปแบบตลาด"

st.markdown(
    f"""
<div class="hero-title">Wisalsaya Crypto Decision Lab</div>
<div class="hero-sub">Version 2.1 • Automated Practice Edition • {now:%d/%m/%Y %H:%M} น.</div>
<div class="badge">20-COIN SCANNER • PAPER TRADING • BEGINNER MODE</div>
<div class="decision">
<div class="score">{market_score}/100</div>
<h3>{label}</h3>
<div>{main}</div>
<div class="muted">{note}</div>
</div>
""",
    unsafe_allow_html=True,
)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("ทุนทดลอง", f"{capital:,.0f} บาท")
m2.metric("ขาดทุนสูงสุด/วัน", f"{max_loss:,.0f} บาท")
m3.metric("ผลปิดวันนี้", f"{realized_today:+,.2f} บาท")
m4.metric("Risk คงเหลือ", f"{remaining_risk:,.0f} บาท")
m5.metric("Fear & Greed", f"{fng_value}/100", fng_label)

st.subheader(f"🏆 Top {top_n} Opportunities")
top_df = scanner_df.head(top_n)
columns = st.columns(top_n)
for column, (_, row) in zip(columns, top_df.iterrows()):
    css = row["Status"].lower()
    sign = "+" if row["24h %"] >= 0 else ""
    with column:
        st.markdown(
            f"""
<div class="card">
<h3>{row['Coin']}</h3>
<div class="score" style="font-size:2rem">{int(row['Score'])}</div>
<div class="{css}">{row['Status']}</div>
<div class="muted">{row['Trend']}<br>RSI {row['RSI']:.1f}<br>Volume {row['Volume x']:.2f}x<br>{sign}{row['24h %']:.2f}% / 24 ชม.</div>
</div>
""",
            unsafe_allow_html=True,
        )

st.subheader("🔎 20-Coin Scanner")
f1, f2, f3 = st.columns(3)
with f1:
    min_score = st.slider("คะแนนขั้นต่ำ", 0, 100, 55)
with f2:
    status_filter = st.multiselect("สถานะ", ["READY", "WATCH", "WAIT", "AVOID"], default=["READY", "WATCH", "WAIT"])
with f3:
    trend_filter = st.multiselect("Trend", ["Uptrend", "Sideway Up", "Sideway", "Sideway Down", "Downtrend"], default=[])
filtered = scanner_df[(scanner_df["Score"] >= min_score) & (scanner_df["Status"].isin(status_filter))]
if trend_filter:
    filtered = filtered[filtered["Trend"].isin(trend_filter)]
st.dataframe(
    filtered.style.format(
        {
            "Price": "{:,.6f}", "24h %": "{:+.2f}", "RSI": "{:.1f}", "Volume x": "{:.2f}",
            "Volatility %": "{:.2f}", "Up %": "{:.0f}", "Sideway %": "{:.0f}", "Down %": "{:.0f}",
        }
    ).background_gradient(subset=["Score"], cmap="YlGn"),
    hide_index=True,
    use_container_width=True,
    height=560,
)

st.subheader("📈 Chart Lab")
left, right = st.columns([1.9, 1])
with left:
    default_coin = str(top_df.iloc[0]["Coin"])
    asset = st.selectbox("เลือกเหรียญ", list(scanner_df["Coin"]), index=list(scanner_df["Coin"]).index(default_coin))
    selected = market[asset]
    a = selected["a"]
    st.plotly_chart(candle_chart(selected["df"], asset, a["support"], a["resistance"]), use_container_width=True, config={"displayModeBar": False})
with right:
    st.markdown(
        f"""
<div class="card"><b>Opportunity Score</b><div class="price">{a['score']}/100 • {a['status']}</div><div class="muted">Trend {a['trend']} • RSI {a['rsi']} • Volume {a['volume_ratio']}x</div></div>
<div class="card"><b>Resistance</b><div class="price">{usd(a['resistance'])}</div><div class="muted">เฝ้าดูการยืนเหนือโซนพร้อม Volume</div></div>
<div class="card"><b>Support</b><div class="price">{usd(a['support'])}</div><div class="muted">หลุดโซนนี้ให้ระวังแรงขาย</div></div>
<div class="card"><b>Probability</b><div class="muted">Up {a['up']}% • Sideway {a['sideway']}% • Down {a['down']}%</div></div>
""",
        unsafe_allow_html=True,
    )
    breakdown = pd.DataFrame(
        {
            "Indicator": ["Trend", "Momentum", "Volume", "Volatility", "News Impact"],
            "Score": [a["trend_score"], a["momentum_score"], a["volume_score"], a["volatility_score"], a["news_score"]],
        }
    )
    st.bar_chart(breakdown.set_index("Indicator"), horizontal=True)

st.subheader("🧪 Paper Trading Lab")
if realized_today <= -max_loss:
    st.error("STOP FOR TODAY — ระบบปิดการสร้างแผนใหม่ เพราะผลขาดทุนจำลองแตะขีดจำกัดแล้ว")
else:
    with st.form("paper_trade_form"):
        p1, p2, p3, p4 = st.columns(4)
        trade_coin = p1.selectbox("เหรียญ", list(scanner_df["Coin"]), index=list(scanner_df["Coin"]).index(asset))
        entry = p2.number_input("Entry จำลอง", min_value=0.00000001, value=float(prices[trade_coin]), format="%.8f")
        stop_default = float(entry * 0.98)
        target_default = float(entry * 1.04)
        stop = p3.number_input("Stop Loss", min_value=0.00000001, value=stop_default, format="%.8f")
        target = p4.number_input("Target", min_value=0.00000001, value=target_default, format="%.8f")
        q1, q2, q3 = st.columns(3)
        risk_budget = q1.number_input("งบเสี่ยง (บาท)", min_value=10, max_value=int(max(10, remaining_risk)), value=min(int(risk_per_trade), int(max(10, remaining_risk))), step=10)
        thesis = q2.text_input("เหตุผลสั้น ๆ", value=f"Score {market[trade_coin]['a']['score']} • {market[trade_coin]['a']['trend']}")
        confirm = q3.checkbox("ฉันวาง Stop และ Target ก่อนสร้างแผน")
        create_trade = st.form_submit_button("สร้าง Paper Trade")
    if create_trade:
        if not confirm:
            st.warning("กรุณายืนยันว่ากำหนด Stop และ Target แล้ว")
        elif stop >= entry:
            st.warning("สำหรับแผน Long จำลอง Stop ต้องต่ำกว่า Entry")
        elif target <= entry:
            st.warning("Target ต้องสูงกว่า Entry")
        else:
            risk_pct = (entry - stop) / entry
            position_thb = min(float(capital), float(risk_budget) / risk_pct)
            st.session_state.paper_trades.append(
                {
                    "id": len(st.session_state.paper_trades) + 1,
                    "date": today,
                    "created": now.strftime("%H:%M"),
                    "coin": trade_coin,
                    "entry": entry,
                    "stop": stop,
                    "target": target,
                    "position_thb": position_thb,
                    "risk_budget": float(risk_budget),
                    "status": "OPEN",
                    "current": prices[trade_coin],
                    "exit": prices[trade_coin],
                    "pnl": 0.0,
                    "thesis": thesis,
                }
            )
            st.success("สร้าง Paper Trade เรียบร้อย ระบบจะติดตาม Stop/Target เมื่อแอปรีเฟรช")
            st.rerun()

if st.session_state.paper_trades:
    trade_df = pd.DataFrame(st.session_state.paper_trades)
    display_cols = ["id", "date", "created", "coin", "status", "entry", "current", "stop", "target", "position_thb", "risk_budget", "pnl", "thesis"]
    st.dataframe(
        trade_df[display_cols].style.format(
            {"entry": "{:,.8f}", "current": "{:,.8f}", "stop": "{:,.8f}", "target": "{:,.8f}", "position_thb": "{:,.2f}", "risk_budget": "{:,.2f}", "pnl": "{:+,.2f}"}
        ),
        hide_index=True,
        use_container_width=True,
    )
    st.download_button(
        "ดาวน์โหลด Paper Trades เป็น CSV",
        trade_df.to_csv(index=False).encode("utf-8-sig"),
        f"wisalsaya_paper_trades_{now:%Y%m%d}.csv",
        "text/csv",
    )
else:
    st.info("ยังไม่มี Paper Trade — วันที่เลือก WAIT ก็ถือเป็นการฝึกที่ถูกต้อง")

st.subheader("📝 Trading Journal")
with st.form("journal_form", clear_on_submit=True):
    j1, j2, j3 = st.columns(3)
    journal_coin = j1.selectbox("สินทรัพย์", ["ไม่มีแผน"] + COINS)
    decision = j2.selectbox("Decision", ["WAIT", "WATCH", "READY", "STOP FOR TODAY"])
    emotion = j3.select_slider("อารมณ์", ["กังวล", "ลังเล", "ปกติ", "มั่นใจ", "มั่นใจมาก"], value="ปกติ")
    lesson = st.text_area("บทเรียนวันนี้")
    save_journal = st.form_submit_button("บันทึก Journal")
if save_journal:
    st.session_state.journal_v21.append(
        {
            "วันที่": today,
            "เวลา": now.strftime("%H:%M"),
            "Market Score": market_score,
            "BTC Trend": btc_base["trend"],
            "BTC RSI": btc_base["rsi"],
            "เหรียญ": journal_coin,
            "Decision": decision,
            "อารมณ์": emotion,
            "บทเรียน": lesson,
        }
    )
    st.success("บันทึก Journal แล้ว")
if st.session_state.journal_v21:
    journal_df = pd.DataFrame(st.session_state.journal_v21)
    st.dataframe(journal_df, hide_index=True, use_container_width=True)
    st.download_button(
        "ดาวน์โหลด Journal เป็น CSV",
        journal_df.to_csv(index=False).encode("utf-8-sig"),
        f"wisalsaya_journal_{now:%Y%m%d}.csv",
        "text/csv",
    )

st.subheader("📚 Beginner Coach")
coach_lines = [
    f"Market Score วันนี้ {market_score}/100 — {label.replace('🟢 ', '').replace('🟡 ', '').replace('⚪ ', '').replace('🛑 ', '')}",
    f"BTC Trend = {btc_base['trend']} และ RSI = {btc_base['rsi']}",
    f"เหรียญคะแนนสูงสุดคือ {top_df.iloc[0]['Coin']} ({int(top_df.iloc[0]['Score'])}/100) แต่ต้องดู Trigger และ Volume ก่อนเสมอ",
    "RSI สูงไม่ได้แปลว่าต้องเข้า และการเลือก WAIT ถือเป็นการตัดสินใจที่ถูกต้องได้",
]
st.markdown("\n".join(f"- {line}" for line in coach_lines))

st.caption(
    "Version 2.1 • ระบบวิเคราะห์เชิงสถิติและ Paper Trading เพื่อการฝึกเท่านั้น • ไม่มีการเชื่อม API Key และไม่มีคำสั่งซื้อขายอัตโนมัติ • ข้อมูลใน session อาจหายเมื่อแอป restart กรุณาดาวน์โหลด CSV เก็บไว้"
)
