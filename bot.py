import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage, BroadcastRequest
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
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 加入這行偽裝，減少被阻擋機率
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        # 增加等待時間到 12 秒，應對官網卡頓
        time.sleep(12) 
        
        # 嘗試滾動一下網頁，有時能觸發動態內容載入
        driver.execute_script("window.scrollTo(0,500);")
        time.sleep(2)
        
        elements = driver.find_elements(By.CSS_SELECTOR, 'a[href*="articleId"]')
        if elements:
            # 取得第一個有效的公告 (排除掉一些置頂但不是最新的標籤)
            for el in elements:
                title = el.text.strip()
                link = el.get_attribute('href')
                if title and 'articleId=' in link:
                    article_id = link.split('articleId=')[-1]
                    return {"id": article_id, "title": title, "link": link}
    except Exception as e:
        print(f"❌ Selenium 抓取異常: {e}")
    finally:
        driver.quit()
    return None

def main():
    print("🚀 啟動 Selenium 真人模擬模式...")
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤：找不到 LINE 金鑰或 ID")
        return

    history = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}

    for site in TARGET_SITES:
        print(f"🔍 模擬開啟瀏覽器檢查: {site['name']}...")
        current = get_latest_with_selenium(site['url'])
        
        if current and current.get('title'):
            print(f"✅ 看到最新公告: {current['title']}")
            
            # --- 此處縮排已修正 ---
            if history.get(site['name']) != current['id']:
                print(f"🆕 發現新公告！準備進行廣播...")
                msg = f"🔔 {site['name']} 更新！\n\n【{current['title']}】\n\n連結：{current['link']}"
                
                try:
                    config = Configuration(access_token=LINE_ACCESS_TOKEN)
                    with ApiClient(config) as api_client:
                        api = MessagingApi(api_client)
                        
                        # 使用 broadcast 發送給所有好友
                        api.broadcast(BroadcastRequest(
                            messages=[TextMessage(text=msg)]
                        ))
                    print("✨ 全員廣播完成！")
                    # 成功發送後才更新紀錄
                    history[site['name']] = current['id']
                except Exception as e:
                    print(f"❌ 廣播失敗: {e}")
            else:
                print("😴 沒有新內容。")
        else:
            print(f"📭 在 {site['name']} 找不到公告資料。")

    # 存檔
    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 任務結束。")

if __name__ == "__main__":
    main()
