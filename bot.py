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

# 修正：補全所有官網請求時會帶上的參數
TARGET_SITES = [
    {
        "name": "AION2 官方公告", 
        "api_url": "https://tw.ncsoft.com/aion2/api/board/list?boardId=notice&page=1&pageSize=10&worldId=0",
        "web_url": "https://tw.ncsoft.com/aion2/board/notice/view?articleId="
    },
    {
        "name": "AION2 更新資訊", 
        "api_url": "https://tw.ncsoft.com/aion2/api/board/list?boardId=update&page=1&pageSize=10&worldId=0",
        "web_url": "https://tw.ncsoft.com/aion2/board/update/view?articleId="
    }
]

def get_latest_from_api(site):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tw.ncsoft.com/aion2/board/notice/list',
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        # 使用 Session 並模擬完整路徑
        session = requests.Session()
        res = session.get(site['api_url'], headers=headers, timeout=15)
        
        if res.status_code == 200:
            data = res.json()
            # 針對 NCSoft 回傳格式：資料通常在 result -> contents 或直接在 contents
            result_obj = data.get('result', {})
            articles = result_obj.get('contents', []) if isinstance(result_obj, dict) else data.get('contents', [])
            
            if articles:
                first = articles[0]
                article_id = str(first.get('articleId'))
                title = first.get('title')
                link = site['web_url'] + article_id
                return {"id": article_id, "title": title, "link": link}
            else:
                print(f"📭 {site['name']} API 回傳列表為空")
        else:
            print(f"⚠️ {site['name']} 狀態碼: {res.status_code}")
            print(f"DEBUG 詳細錯誤: {res.text[:300]}")
    except Exception as e:
        print(f"❌ 請求出錯: {e}")
    return None

def main():
    print("🚀 機器人啟動 (參數校正模式)...")
    
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("❌ 錯誤: 金鑰缺失")
        return

    history = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f:
                history = json.load(f)
        except: pass

    for site in TARGET_SITES:
        print(f"🔍 檢查: {site['name']}...")
        current = get_latest_from_api(site)
        
        if current:
            print(f"✅ 成功獲取: {current['title']}")
            if history.get(site['name']) != current['id']:
                print(f"🆕 偵測到更新，發送 LINE...")
                msg = f"🔔 {site['name']} 有新消息！\n\n【{current['title']}】\n\n傳送門：{current['link']}"
                
                try:
                    config = Configuration(access_token=LINE_ACCESS_TOKEN)
                    with ApiClient(config) as api_client:
                        api = MessagingApi(api_client)
                        api.push_message(PushMessageRequest(
                            to=USER_ID,
                            messages=[TextMessage(text=msg)]
                        ))
                    print("✨ LINE 推播完成")
                    history[site['name']] = current['id']
                except Exception as e:
                    print(f"❌ LINE 推播失敗: {e}")
            else:
                print("😴 無新內容。")

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)
    print("💾 任務結束。")

if __name__ == "__main__":
    main()
