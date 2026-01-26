import requests
from bs4 import BeautifulSoup
import json
import os
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
)

LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
DB_FILE = 'last_ids.json'

TARGET_SITES = [
    {"name": "AION2 官方公告", "url": "https://tw.ncsoft.com/aion2/board/notice/list"},
    {"name": "AION2 更新資訊", "url": "https://tw.ncsoft.com/aion2/board/update/list"}
]
BASE_URL = "https://tw.ncsoft.com"

def get_latest_article(url):
    # 根據 AION2 官網結構，API 通常隱藏在特定的路徑下
    # 我們將網址轉換為 API 請求網址 (這部分是根據 NCSoft 慣用規則推測)
    is_notice = "notice" in url
    api_url = "https://tw.ncsoft.com/aion2/api/board/list"
    
    params = {
        "boardId": "notice" if is_notice else "update",
        "page": 1,
        "pageSize": 10
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': url
    }

    try:
        # 直接請求 JSON 資料
        res = requests.get(api_url, params=params, headers=headers, timeout=15)
        
        # 如果 API 存在且回傳成功
        if res.status_code == 200:
            data = res.json()
            # 取得列表中的第一筆
            articles = data.get('contents', [])
            if articles:
                first = articles[0]
                title = first.get('title')
                article_id = str(first.get('articleId'))
                # 組合出前端看得到的網址
                board_type = "notice" if is_notice else "update"
                link = f"https://tw.ncsoft.com/aion2/board/{board_type}/view?articleId={article_id}"
                
                return {"id": article_id, "title": title, "link": link}
        
        # 如果 API 方式失敗，嘗試備案：直接分析 HTML (針對伺服器渲染的情況)
        print(f"DEBUG: API 抓取未果，試圖解析 HTML...")
        soup = BeautifulSoup(res.text, 'html.parser')
        # ... (保留原本的 soup 解析邏輯作為備案)
        
    except Exception as e:
        print(f"❌ 抓取異常: {e}")
    return None

def main():
    print("🚀 機器人開始執行...")
    
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤: 找不到 LINE 金鑰設定，請檢查 GitHub Secrets。")
        return

    # 讀取舊紀錄
    history = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            history = json.load(f)
        print(f"查閱舊紀錄: {history}")

    for site in TARGET_SITES:
        print(f"🔍 正在檢查: {site['name']}...")
        current = get_latest_article(site['url'])
        
        if current:
            print(f"✅ 成功抓取！最新標題: {current['title']} (ID: {current['id']})")
            
            # 判斷是否更新
            if history.get(site['name']) != current['id']:
                print(f"🆕 偵測到新內容，發送推播中...")
                msg = f"🔔 {site['name']} 有新內容！\n\n【{current['title']}】\n\n連結：{current['link']}"
                
                try:
                    configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
                    with ApiClient(configuration) as api_client:
                        line_bot_api = MessagingApi(api_client)
                        line_bot_api.push_message(PushMessageRequest(
                            to=USER_ID,
                            messages=[TextMessage(text=msg)]
                        ))
                    print("✨ LINE 推播成功！")
                except Exception as e:
                    print(f"❌ LINE 推播失敗: {e}")
                
                history[site['name']] = current['id']
            else:
                print("😴 資料與上次相同，跳過。")
        else:
            print(f"📭 {site['name']} 無法取得有效資料。")

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 紀錄更新完畢，執行結束。")

if __name__ == "__main__":
    main()
