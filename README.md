# Wisalsaya Crypto Decision Lab v2.1

## ฟังก์ชันหลัก
- วิเคราะห์ตลาดอัตโนมัติ 20 เหรียญ
- Binance Public Market Data โดยไม่ใช้ API Key
- คะแนน 0–100 แยก Trend, Momentum, Volume, Volatility และ News Impact proxy
- สถานะ READY / WATCH / WAIT / AVOID
- Top Opportunities อัตโนมัติ
- Chart Lab พร้อม EMA20, EMA50, Support และ Resistance
- Probability Simulation: Up / Sideway / Down
- Paper Trading Lab พร้อมติดตาม Stop Loss และ Target เมื่อแอปรีเฟรช
- คำนวณกำไร/ขาดทุนจำลองและ Daily Risk Limit
- STOP FOR TODAY เมื่อขาดทุนถึงขีดจำกัด
- Trading Journal และดาวน์โหลด CSV
- Beginner Coach ภาษาไทย

## วิธีอัปเดตบน GitHub
1. แตกไฟล์ ZIP
2. อัปโหลด `app.py`, `requirements.txt`, `README.md` ทับไฟล์เดิม
3. กด Commit changes
4. Streamlit Community Cloud จะ Deploy ใหม่อัตโนมัติ

## หมายเหตุสำคัญ
- Paper Trade และ Journal เก็บใน Streamlit Session จึงอาจหายเมื่อแอป restart
- ควรดาวน์โหลด CSV เก็บไว้ทุกวัน
- Version ถัดไปสามารถเพิ่มฐานข้อมูลถาวร เช่น Supabase หรือ Google Sheets
- ไม่มีการเชื่อม Binance API Key, Password, OTP หรือ API Secret
- ไม่มีคำสั่งซื้อขายอัตโนมัติ
