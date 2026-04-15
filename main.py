import os
import time
import threading
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from quotexpy import Quotex

# --- সেটিংস ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"
current_data = {} # এখানে লাইভ ডেটা সেভ থাকবে

app = Flask(__name__)

# ১. সরাসরি URL এ ডেটা দেখার জন্য API রুট
@app.route('/')
def get_live_data():
    pair = request.args.get('pair', 'EURUSD_otc')
    data = current_data.get(pair, None)
    
    response = {
        "Owner_Developer": "DARK-X-RAYHAN",
        "Telegram": "@mdrayhan85",
        "Channel": "https://t.me/mdrayhan85",
        "success": True if data else False,
        "count": 1 if data else 0,
        "data": [data] if data else []
    }
    return jsonify(response)

# ২. অটো SSID এবং ডেটা ফেচার লজিক
def fetch_quotex_data():
    global current_data
    while True:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context()
                page = context.new_page()
                stealth_sync(page)
                page.goto("https://qxbroker.com/en/sign-in")
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                time.sleep(15) # লগইন হওয়ার জন্য সময়
                
                cookies = context.cookies()
                ssid = next((c['value'] for c in cookies if c['name'] == 'token'), None)
                browser.close()

                if ssid:
                    client = Quotex(ssid=ssid)
                    check, _ = client.connect()
                    if check:
                        # আপনি যে যে পেয়ারের ডেটা চান এখানে লিস্ট করতে পারেন
                        pairs = ["EURUSD_otc", "USDBDT_otc", "USDINR_otc"]
                        for p_name in pairs:
                            client.start_candles_stream(p_name, 60)
                        
                        while True:
                            for p_name in pairs:
                                candles = client.get_realtime_candles(p_name)
                                if candles:
                                    latest = list(candles.values())[-1]
                                    open_p, close_p = latest['open'], latest['close']
                                    color = "green" if close_p > open_p else "red"
                                    if open_p == close_p: color = "doji"
                                    
                                    current_data[p_name] = {
                                        "id": "1",
                                        "pair": p_name,
                                        "timeframe": "M1",
                                        "candle_time": time.strftime('%Y-%m-%d %H:%M:00'),
                                        "open": str(open_p),
                                        "high": str(latest['high']),
                                        "low": str(latest['low']),
                                        "close": str(close_p),
                                        "volume": "48",
                                        "color": color,
                                        "created_at": time.strftime('%Y-%m-%d %H:%M:%S')
                                    }
                            time.sleep(1) # ১ সেকেন্ড পর পর ডেটা আপডেট হবে
        except Exception as e:
            print(f"Error: {e}. Restarting...")
            time.sleep(5)

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ডেটা সংগ্রহের কাজ চলবে
    threading.Thread(target=fetch_quotex_data, daemon=True).start()
    # মেইন পোর্টে ওয়েব সার্ভার চলবে
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
