import time
import os
import threading
from flask import Flask
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from quotexpy import Quotex
import mysql.connector

# --- Flask Server (Render-কে সজাগ রাখতে) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running!"

def run_web_server():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))

# --- আপনার আসল বটের কোড ---
EMAIL = "trrayhanislam786@gmail.com"
PASSWORD = "Mdrayhan@655"

def get_ssid():
    print("🚀 Getting SSID...")
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
        return token

def fetch_data():
    while True:
        ssid = get_ssid()
        if not ssid: continue
        
        client = Quotex(ssid=ssid)
        check, _ = client.connect()
        if check:
            client.start_candles_stream("EURUSD_otc", 60)
            while True:
                try:
                    # এখানে আপনার ডাটাবেস আপডেট লজিক থাকবে
                    print("Data Fetching...")
                    time.sleep(10)
                except: break

if __name__ == "__main__":
    # ওয়েব সার্ভার আলাদা থ্রেডে চালানো
    threading.Thread(target=run_web_server).start()
    # বট চালানো
    fetch_data()
