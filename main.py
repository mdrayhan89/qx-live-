import time
import mysql.connector
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from quotexpy import Quotex

# --- সেটিংস ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"
ASSET = "EURUSD_otc"

def get_ssid():
    print("🚀 Logging in to Quotex to get new SSID...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        page = context.new_page()
        stealth_sync(page)
        
        page.goto("https://qxbroker.com/en/sign-in", wait_until="networkidle")
        page.fill('input[name="email"]', EMAIL)
        page.fill('input[name="password"]', PASSWORD)
        page.click('button[type="submit"]')
        
        # লগইন হওয়ার জন্য কিছুটা সময় দেওয়া
        time.sleep(10) 
        
        cookies = context.cookies()
        token = next((c['value'] for c in cookies if c['name'] == 'token'), None)
        browser.close()
        return token

def start_fetching():
    ssid = get_ssid()
    if not ssid:
        print("❌ SSID collection failed!")
        return

    client = Quotex(ssid=ssid)
    check, reason = client.connect()

    if check:
        print(f"✅ Connected to Quotex! Fetching {ASSET}...")
        client.start_candles_stream(ASSET, 60)
        
        # ডাটাবেস কানেকশন (আপনার Hosting DB Info দিন)
        db = mysql.connector.connect(
            host="your_host",
            user="your_user",
            password="your_password",
            database="your_db"
        )
        cursor = db.cursor()

        while True:
            try:
                candles = client.get_realtime_candles(ASSET)
                if candles:
                    latest = list(candles.values())[-1]
                    open_p, close_p = latest['open'], latest['close']
                    color = "green" if close_p > open_p else "red"
                    
                    sql = "REPLACE INTO candles (id, pair, open, high, low, close, color, candle_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                    val = (1, ASSET, open_p, latest['high'], latest['low'], close_p, color, time.strftime('%Y-%m-%d %H:%M:%S'))
                    
                    cursor.execute(sql, val)
                    db.commit()
                time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")
                break # কোনো এরর হলে লুপ ভেঙে আবার নতুন SSID নিবে
    else:
        print(f"Connection failed: {reason}")

if __name__ == "__main__":
    while True:
        start_fetching()
        time.sleep(10) # রিস্টার্ট হওয়ার আগে বিরতি
