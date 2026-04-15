import os
import time
import threading
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from quotexpy import Quotex

app = Flask(__name__)

# --- Settings ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"
client = None  # Global client variable

# --- Quotex Connection Handler ---
def connect_quotex():
    global client
    while True:
        try:
            print("🚀 Attempting to get new SSID and Connect...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                stealth_sync(page)
                page.goto("https://qxbroker.com/en/sign-in")
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                time.sleep(15) 
                
                cookies = context.cookies()
                token = next((c['value'] for c in cookies if c['name'] == 'token'), None)
                browser.close()

                if token:
                    client = Quotex(ssid=token)
                    check, _ = client.connect()
                    if check:
                        print("✅ Quotex Connected Successfully!")
                        # কানেকশন ধরে রাখার জন্য একটি লুপ (Heartbeat)
                        while client.check_connect():
                            time.sleep(10)
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            time.sleep(10)

# --- API Route ---
@app.route('/')
def get_candles_api():
    global client
    pair = request.args.get('pair', 'EURUSD_otc')
    # ইউজার কতগুলো ক্যান্ডেল চায় (ডিফল্ট ১০, ম্যাক্স ৩০০০)
    try:
        count = int(request.args.get('count', 10))
    except:
        count = 10
    
    if count > 3000: count = 3000 # লিমিট সেট করে দেওয়া হলো

    if client and client.check_connect():
        # Quotex থেকে হিস্ট্রি ডেটা ফেচ করা
        # ৬৬০ মানে ১ মিনিটের ক্যান্ডেল (Timeframe)
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
    
    return jsonify({
        "success": False,
        "message": "Quotex not connected or invalid request."
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে কানেকশন হ্যান্ডলার চালানো
    threading.Thread(target=connect_quotex, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
