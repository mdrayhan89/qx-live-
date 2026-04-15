import os
import time
import threading
from flask import Flask, jsonify, request
from playwright.sync_api import sync_playwright
import playwright_stealth

# --- Quotex Library Import Fix ---
# কিছু ভার্সনে সরাসরি Quotex পাওয়া যায় না, তাই এই লজিকটি রাখা হয়েছে
try:
    from quotexpy import Quotex
except ImportError:
    try:
        from quotexpy.main import Quotex
    except:
        import quotexpy
        if hasattr(quotexpy, 'Quotex'):
            Quotex = quotexpy.Quotex
        else:
            # যদি কোড ফেইল হয় তবে এটি ব্যাকআপ হিসেবে কাজ করবে
            Quotex = None

app = Flask(__name__)

# --- সেটিংস ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"
client = None  

# --- অটো লগইন এবং কানেকশন হ্যান্ডলার ---
def connect_quotex():
    global client
    while True:
        try:
            print("🚀 Attempting to Login and Connect to Quotex...")
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                # রিয়েল ব্রাউজার এনভায়রনমেন্ট তৈরি করা
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                # ফিক্সড স্টিলথ মোড (বট ডিটেকশন এড়াতে)
                playwright_stealth.stealth_sync(page)
                
                # লগইন পেজে যাওয়া
                page.goto("https://qxbroker.com/en/sign-in", wait_until="networkidle", timeout=60000)
                page.fill('input[name="email"]', EMAIL)
                page.fill('input[name="password"]', PASSWORD)
                page.click('button[type="submit"]')
                
                # লগইন প্রসেস হওয়ার জন্য সময় দেওয়া
                time.sleep(15) 
                
                # কুকিজ থেকে টোকেন সংগ্রহ
                cookies = context.cookies()
                token = next((c['value'] for c in cookies if c['name'] == 'token'), None)
                browser.close()

                if token and Quotex:
                    client = Quotex(ssid=token)
                    check, _ = client.connect()
                    if check:
                        print("✅ Quotex Connected Successfully!")
                        # কানেকশন ধরে রাখার জন্য লুপ
                        while client.check_connect():
                            time.sleep(10)
                else:
                    print("❌ Login Failed or Token not found. Retrying in 30s...")
                    time.sleep(30)
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            time.sleep(10)

# --- API এর মেইন রুট ---
@app.route('/')
def get_candles_api():
    global client
    # URL থেকে প্যারামিটার নেওয়া
    pair = request.args.get('pair', 'EURUSD_otc')
    try:
        count = int(request.args.get('count', 1))
    except:
        count = 1
    
    # ৩০০০ ক্যান্ডেলের বেশি এলাউ করা হবে না সার্ভারের নিরাপত্তার জন্য
    if count > 3000: count = 3000 

    if client and client.check_connect():
        try:
            # হিস্টোরিক্যাল ক্যান্ডেল ডেটা সংগ্রহ (Timeframe 60 = 1m)
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
                    "Channel": "https://t.me/mdrayhan85",
                    "success": True,
                    "count": len(formatted_candles),
                    "data": formatted_candles
                })
            else:
                return jsonify({"success": False, "message": "No data received from Quotex."})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    
    return jsonify({
        "success": False, 
        "message": "Quotex not connected yet. Please wait 15-30 seconds after deploy."
    })

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে কোটাক্স কানেকশন চালানো যাতে ওয়েব রিকোয়েস্ট ব্লক না হয়
    threading.Thread(target=connect_quotex, daemon=True).start()
    
    # Render এর পোর্টে ওয়েব সার্ভার রান করা
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
