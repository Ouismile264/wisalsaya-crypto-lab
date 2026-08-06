# Wisalsaya Crypto Decision Lab v3.1 — Persistence & Interactive Chart Fix

แอป Streamlit สำหรับเรียนรู้การวิเคราะห์ตลาดและ Paper Trading เท่านั้น แอปไม่เชื่อม API Key และไม่ส่งคำสั่งซื้อขายจริง

## สิ่งที่แก้ใน v3.1

### Chart Lab

- Candlestick แบบโต้ตอบ: ซูมด้วยล้อ/Trackpad, ลากเพื่อเลื่อน, Hover ดู OHLC และดับเบิลคลิกเพื่อรีเซ็ต
- เปิด Plotly toolbar, range slider, ดาวน์โหลดภาพ และเครื่องมือวาดเส้น
- เลือก Timeframe `15M / 1H / 4H / 1D`
- เลือกจำนวนแท่ง `100–1,000`
- เวลาแสดงเป็น `Asia/Bangkok`
- EMA20 และ EMA50 คำนวณจากแท่งชุดเดียวกับกราฟ
- ข้อมูล OHLC มาจาก Binance Spot pair เช่น `BTCUSDT` จึงควรเทียบกับ TradingView ที่ตั้ง Exchange = Binance, Pair = BTCUSDT และ Timeframe เดียวกัน

### Paper Trade / Paper Portfolio

- ใช้ SQLite ที่ `data/wisalsaya_lab.sqlite3` แทน Session State
- รายการไม่หายจากการ Refresh, ปิดแท็บ หรือ restart process ตามปกติ
- ติดตาม `OPEN`, `CLOSED_TARGET`, `CLOSED_STOP`, `CLOSED_MANUAL`
- แยก Unrealized PnL และ Realized PnL
- ปิดอัตโนมัติเมื่อแตะ Stop Loss/Take Profit เมื่อแอปอัปเดตราคา
- มีปุ่มปิดแผนเองและกำหนดราคาปิด
- Export/Import CSV และ migration จาก session รุ่นเดิม

### Journal

- Textarea พิมพ์ภาษาไทยได้และ Submit ภายใน form ถูกต้อง
- บันทึกถาวรลง SQLite
- เชื่อม Journal กับ Paper Trade ด้วย Trade ID
- ดึงผล Realized PnL จากรายการที่ปิดแล้ว
- Export/Import CSV

## อัปเดต GitHub

1. แตก ZIP รุ่นนี้
2. เข้า Repository เดิมใน GitHub
3. อัปโหลดทับไฟล์ต่อไปนี้:
   - `app.py`
   - `storage.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore`
4. กด **Commit changes**
5. รอ Streamlit redeploy แล้วเปิดแอปใหม่

ไฟล์ `storage.py` เป็นไฟล์ใหม่และจำเป็น หากไม่อัปโหลด แอปจะเปิดไม่ได้

## การสำรองข้อมูล

SQLite บน Streamlit Community Cloud ช่วยให้ข้อมูลอยู่ต่อเมื่อ Refresh, ปิดแท็บ หรือ process restart บน instance เดิม แต่พื้นที่เก็บไฟล์ของ Community Cloud **ไม่ใช่ฐานข้อมูลถาวรที่รับประกันข้าม redeploy/container replacement**

จึงควร:

1. ดาวน์โหลด Paper Trades CSV และ Journal CSV เป็นระยะ
2. ก่อนอัปเดตโค้ดทุกครั้ง ให้ Export CSV
3. หลัง deploy หากฐานข้อมูลว่าง ให้ Import CSV กลับเข้าแอป

ถ้าต้องการความถาวรระดับใช้งานระยะยาว ควรเปลี่ยน backend เป็น Supabase/Postgres ในรุ่นถัดไป

## วิธีใช้ Flow หลัก

1. ไปที่ **Trade Plan** และสร้าง Paper Trade โดยต้องเป็น `Stop Loss < Entry < Take Profit`
2. รายการจะอยู่ใน Paper Portfolio สถานะ `OPEN`
3. เมื่อเปิดหรือ Refresh แอป ระบบจะอัปเดตราคาปัจจุบันและ Unrealized PnL
4. เมื่อราคาแตะ Stop/Target ระบบจะปิดอัตโนมัติ หรือเลือก **ปิดแผนเอง** ได้
5. ไปหน้า **Journal** เลือก Paper Trade ที่ต้องการเชื่อม พิมพ์ Comment แล้วกดบันทึก
6. รายการที่ปิดแล้วจะแสดง Realized PnL; รายการ OPEN แสดง Unrealized PnL

## ทดสอบในเครื่อง

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## ข้อจำกัด

- การปิด Stop/Target เกิดเมื่อแอปทำงานและโหลดราคาล่าสุด ไม่ใช่ background worker ตลอด 24 ชั่วโมง
- ราคาอาจข้าม Stop/Target ระหว่างที่แอปหลับ รุ่นนี้บันทึก exit ตามระดับ Stop/Target เพื่อให้ Paper Test มีหลักเกณฑ์คงที่
- ผลลัพธ์เป็นการจำลอง ไม่รวม slippage และค่าธรรมเนียม เว้นแต่จะเพิ่มในกติกาภายหลัง

