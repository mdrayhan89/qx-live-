import os
import time
import threading
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import playwright_stealth
from quotexpy import Quotex

app = Flask(__name__)

# --- Settings ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"
client = None  

# --- Quotex Connection Handler ---
def connect_quotex():
    global client
    while True:
        try:
            print("🚀 Attempting to Login and Connect to Quotex...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # ফিক্সড স্টিলথ মোড
                playwright_stealth.stealth_sync(page)
                
                page.goto("https://qxbroker.com/en/sign-in", wait_until="networkidle")
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                
                # লগইন হওয়ার জন্য ১৫ সেকেন্ড অপেক্ষা
                time.sleep(15) 
                
                cookies = context.cookies()
                token = next((c['value'] for c in cookies if c['name'] == 'token'), None)
                browser.close()

                if token:
                    client = Quotex(ssid=token)
                    check, _ = client.connect()
                    if check:
                        print("✅ Quotex Connected Successfully!")
                        while client.check_connect():
                            time.sleep(10)
                else:
                    print("❌ Token not found. Retrying in 30s...")
                    time.sleep(30)
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            time.sleep(10)

# --- API Route ---
@app.route('/')
def get_candles_api():
    global client
    pair = request.args.get('pair', 'EURUSD_otc')
    
    # ইউজার কতগুলো ক্যান্ডেল চায় (Default 1, Max 3000)
    try:
        count = int(request.args.get('count', 1))
    except:
        count = 1
    
    if count > 3000: count = 3000 

    if client and client.check_connect():
        try:
            # ক্যান্ডেল হিস্ট্রি ফেচ করা (60 মানে 1 মিনিট টাইমফ্রেম)
            candles = client.get_candles(pair, 60, count, time.time())
            
            formatted_candles = []
            if candles:
                for c in candles:
                    open_p, close_p = c['open'], c['close']
                    color = "green" if close_p > open_p else "red"
                    if open_p == close_p: color = "doji"
                    
                    formatted_candles.append({
                        "id": str(len(formatted_candles) + 1),
                        "pair": pair,
                        "timeframe": "M1",
                        "candle_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['at'])),
                        "open": str(open_p),
                        "high": str(c['high']),
                        "low": str(c['low']),
                        "close": str(close_p),
                        "volume": "48",
                        "color": color,
                        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
                    })

                return jsonify({
                    "Owner_Developer": "DARK-X-RAYHAN",
                    "Telegram": "@mdrayhan85",
                    "success": True,
                    "count": len(formatted_candles),
                    "data": formatted_candles
                })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    return jsonify({
        "success": False,
        "message": "Quotex not connected. Please wait a moment and refresh."
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে কোটাক্স কানেকশন চালানো
    threading.Thread(target=connect_quotex, daemon=True).start()
    
    # পোর্ট সেটআপ (Render এর জন্য)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
