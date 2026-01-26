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

# AION2 修正後的 API 網址 (與官網同網域)
TARGET_SITES = [
    {
        "name": "AION2 官方公告", 
        "api_url": "https://tw.ncsoft.com/aion2/api/board/list?boardId=notice&page=1&pageSize=10",
        "web_url": "https://tw.ncsoft.com/aion2/board/notice/view?articleId="
    },
    {
        "name": "AION2 更新資訊", 
        "api_url": "https://tw.ncsoft.com/aion2/api/board/list?boardId=update&page=1&pageSize=10",
        "web_url": "https://tw.ncsoft.com/aion2/board/update/view?articleId="
    }
]

def get_latest_from_api(site):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tw.ncsoft.com/aion2/board/notice/list',
        'Accept': 'application/json, text/plain, */*'
    }
    try:
        res = requests.get(site['api_url'], headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # 根據 NCSoft JSON 結構提取資料
            articles = data.get('contents', [])
            if articles:
                first = articles[0]
                article_id = str(first.get('articleId'))
                title = first.get('title')
                link = site['web_url'] + article_id
                return {"id": article_id, "title": title, "link": link}
        else:
            print(f"⚠️ API 回傳異常狀態碼: {res.status_code}")
    except Exception as e:
        print(f"❌ API 請求出錯 ({site['name']}): {e}")
    return None

def main():
    print("🚀 機器人啟動 (修正版 API 模式)...")
    
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤: 找不到 LINE 金鑰，請確認 GitHub Secrets 設定。")
        return

    history = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                history = json.load(f)
            print(f"查閱舊紀錄: {history}")
        except:
            history = {}

    for site in TARGET_SITES:
        print(f"🔍 檢查中: {site['name']}...")
        current = get_latest_from_api(site)
        
        if current:
            print(f"✅ 成功獲取: {current['title']}")
            if history.get(site['name']) != current['id']:
                print(f"🆕 偵測到新文章，準備推送 LINE...")
                msg = f"🔔 {site['name']} 有新內容！\n\n【{current['title']}】\n\n連結：{current['link']}"
                
                try:
                    config = Configuration(access_token=LINE_ACCESS_TOKEN)
                    with ApiClient(config) as api_client:
                        api = MessagingApi(api_client)
                        api.push_message(PushMessageRequest(
                            to=USER_ID,
                            messages=[TextMessage(text=msg)]
                        ))
                    print("✨ LINE 推播成功！")
                    history[site['name']] = current['id']
                except Exception as e:
                    print(f"❌ LINE 推播失敗: {e}")
            else:
                print("😴 資料相同，無需更新。")
        else:
            print(f"📭 無法獲取 {site['name']} 的 API 資料。")

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 執行結束。")

if __name__ == "__main__":
    main()
