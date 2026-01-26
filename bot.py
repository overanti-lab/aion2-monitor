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
    # 這裡加入了更完整的模擬資訊，防止伺服器回傳 500
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tw.ncsoft.com/aion2/board/notice/list',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9',
        'X-Requested-With': 'XMLHttpRequest' # 告訴伺服器這是一個 API 請求
    }
    
    # 嘗試建立一個 session 來處理可能需要的 Cookie
    session = requests.Session()
    
    try:
        # 先訪問一次首頁取得基本 Cookie
        session.get("https://tw.ncsoft.com/aion2/board/notice/list", headers=headers, timeout=10)
        
        # 執行真正的 API 請求
        res = session.get(site['api_url'], headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            # 這裡要精確對應 NCSoft 的 JSON 結構
            # 通常資料會放在 data 或是 contents 欄位中
            articles = data.get('contents', [])
            if articles:
                first = articles[0]
                article_id = str(first.get('articleId'))
                title = first.get('title')
                link = site['web_url'] + article_id
                return {"id": article_id, "title": title, "link": link}
        else:
            print(f"⚠️ {site['name']} API 失敗，狀態碼: {res.status_code}")
            # 如果還是 500，印出回傳內容除錯
            if res.status_code == 500:
                print(f"DEBUG 回傳內容: {res.text[:200]}")
    except Exception as e:
        print(f"❌ 請求過程出錯: {e}")
    return None

def main():
    print("🚀 機器人啟動 (終極模擬模式)...")
    
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤: 找不到 LINE 金鑰，請檢查 GitHub Secrets 設定。")
        return

    history = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = {}

    for site in TARGET_SITES:
        print(f"🔍 檢查中: {site['name']}...")
        current = get_latest_from_api(site)
        
        if current:
            print(f"✅ 成功獲取: {current['title']}")
            if history.get(site['name']) != current['id']:
                print(f"🆕 偵測到新內容，準備發送 LINE...")
                msg = f"🔔 {site['name']} 有新消息！\n\n【{current['title']}】\n\n傳送門：{current['link']}"
                
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
                    print(f"❌ 推播失敗: {e}")
            else:
                print("😴 資料無變化。")
        else:
            print(f"📭 無法獲取有效資料。")

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 任務結束。")

if __name__ == "__main__":
    main()
