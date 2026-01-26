import requests
import json
import os
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
)

# 金鑰與設定
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
DB_FILE = 'last_ids.json'

# AION2 真正的 API 進入點
TARGET_SITES = [
    {
        "name": "AION2 官方公告", 
        "api_url": "https://aion2-api.plaync.com.tw/board/v1.0/articles?boardId=notice&page=1&pageSize=10",
        "web_url": "https://tw.ncsoft.com/aion2/board/notice/view?articleId="
    },
    {
        "name": "AION2 更新資訊", 
        "api_url": "https://aion2-api.plaync.com.tw/board/v1.0/articles?boardId=update&page=1&pageSize=10",
        "web_url": "https://tw.ncsoft.com/aion2/board/update/view?articleId="
    }
]

def get_latest_from_api(site):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Origin': 'https://tw.ncsoft.com',
        'Referer': 'https://tw.ncsoft.com/'
    }
    try:
        res = requests.get(site['api_url'], headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # 取得文章列表中的第一筆
            articles = data.get('contents', [])
            if articles:
                first = articles[0]
                article_id = str(first.get('articleId'))
                title = first.get('title')
                link = site['web_url'] + article_id
                return {"id": article_id, "title": title, "link": link}
    except Exception as e:
        print(f"❌ API 請求異常 ({site['name']}): {e}")
    return None

def main():
    print("🚀 機器人啟動 (API 模式)...")
    
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤: 找不到 LINE 金鑰。")
        return

    history = {}
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            history = json.load(f)

    for site in TARGET_SITES:
        print(f"🔍 檢查中: {site['name']}...")
        current = get_latest_from_api(site)
        
        if current:
            print(f"✅ 抓取成功: {current['title']}")
            if history.get(site['name']) != current['id']:
                print(f"🆕 偵測到更新！發送 LINE...")
                msg = f"🔔 {site['name']} 有新消息！\n\n【{current['title']}】\n\n連結：{current['link']}"
                
                try:
                    config = Configuration(access_token=LINE_ACCESS_TOKEN)
                    with ApiClient(config) as api_client:
                        api = MessagingApi(api_client)
                        api.push_message(PushMessageRequest(
                            to=USER_ID,
                            messages=[TextMessage(text=msg)]
                        ))
                    print("✨ LINE 推播完成")
                except Exception as e:
                    print(f"❌ 推播失敗: {e}")
                
                history[site['name']] = current['id']
            else:
                print("😴 資料無變化。")
        else:
            print(f"📭 無法從 API 取得資料。")

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 任務結束。")

if __name__ == "__main__":
    main()
