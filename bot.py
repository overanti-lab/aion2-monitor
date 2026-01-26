import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
)

# 設定
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
DB_FILE = 'last_ids.json'

TARGET_SITES = [
    {"name": "AION2 官方公告", "url": "https://tw.ncsoft.com/aion2/board/notice/list"},
    {"name": "AION2 更新資訊", "url": "https://tw.ncsoft.com/aion2/board/update/list"}
]

def get_latest_with_selenium(url):
    chrome_options = Options()
    chrome_options.add_argument('--headless') # 不顯示視窗
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        time.sleep(7) # 強制等待網頁載入內容
        
        # 尋找頁面中第一個 articleId 的連結
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="articleId"]')
        if elements:
            first = elements[0]
            title = first.text.strip()
            link = first.get_attribute('href')
            article_id = link.split('articleId=')[-1]
            return {"id": article_id, "title": title, "link": link}
    except Exception as e:
        print(f"❌ Selenium 抓取異常: {e}")
    finally:
        driver.quit()
    return None

def main():
    print("🚀 啟動 Selenium 真人模擬模式...")
    if not LINE_ACCESS_TOKEN or not USER_ID: return

    history = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: history = json.load(f)

    for site in TARGET_SITES:
        print(f"🔍 模擬開啟瀏覽器檢查: {site['name']}...")
        current = get_latest_with_selenium(site['url'])
        
        if current and current['title']:
            print(f"✅ 看到最新公告: {current['title']}")
            if history.get(site['name']) != current['id']:
                print(f"🆕 發現新公告！")
                msg = f"🔔 {site['name']} 更新！\n\n【{current['title']}】\n\n連結：{current['link']}"
                
                # 發送 LINE
                config = Configuration(access_token=LINE_ACCESS_TOKEN)
                with ApiClient(config) as api_client:
                    MessagingApi(api_client).push_message(PushMessageRequest(
                        to=USER_ID, messages=[TextMessage(text=msg)]
                    ))
                history[site['name']] = current['id']
            else:
                print("😴 沒有新內容。")
        else:
            print("📭 瀏覽器內找不到公告，請檢查 CSS 選擇器。")

    with open(DB_FILE, 'w') as f: json.dump(history, f)

if __name__ == "__main__":
    main()
