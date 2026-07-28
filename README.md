# Wisalsaya Crypto Dashboard

Dashboard ส่วนตัวสำหรับฝึกอ่านตลาด Crypto แบบสั้น กระชับ และเน้นรักษาเงินต้น

## ฟังก์ชันในเวอร์ชันนี้

- ราคาตลาด BTC / ETH / BNB / DOGE
- Market Score 0–100
- Trend, RSI, Volume, Volatility และ Sentiment
- Support / Resistance Zone
- Fear & Greed Index
- Portfolio Snapshot
- Trading Lab ทุนตั้งต้น 1,000 บาท
- Journal และดาวน์โหลด CSV
- Responsive สำหรับ iPhone / iPad / Computer

## Deploy ผ่าน Streamlit Community Cloud

1. Upload ไฟล์ทั้งหมดในโฟลเดอร์นี้เข้า GitHub Repository
2. เปิด Streamlit Community Cloud
3. Sign in ด้วย GitHub
4. เลือก Create app
5. เลือก Repository ของคุณ
6. Main file path: `app.py`
7. กด Deploy

## โครงสร้างไฟล์

```text
wisalsaya-crypto-dashboard/
├── app.py
├── requirements.txt
├── README.md
└── .streamlit/
    └── config.toml
```

## หมายเหตุ

- ไม่ต้องใช้ Binance API Key
- ไม่ต้องใส่ Password, OTP หรือ API Secret
- Dashboard ดึงเฉพาะ Public Market Data
- Journal ใน Streamlit Session จะหายเมื่อ App Restart จึงควรกดดาวน์โหลด CSV เป็นระยะ
- ระบบนี้เป็นเครื่องมือเพื่อการเรียนรู้ ไม่ใช่คำแนะนำหรือคำสั่งซื้อขาย
