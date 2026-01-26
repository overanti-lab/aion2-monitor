import requests
from bs4 import BeautifulSoup
import json
import os
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, PushMessageRequest, TextMessage
)

# 從 GitHub Secrets 讀取金鑰
LINE_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
USER_ID = os.getenv('LINE_USER_ID')
DB_FILE = 'last_ids.json'

TARGET_SITES = [
    {"name": "AION2 官方公告", "url": "https://tw.ncsoft.com/aion2/board/notice/list"},
    {"name": "AION2 更新資訊", "url": "https://tw.ncsoft.com/aion2/board/update/list"}
]
BASE_URL = "https://tw.ncsoft.com"

def get_latest_article(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        first_post = soup.select_one('a[href*="articleId"]')
        if first_post:
            title = first_post.get_text(strip=True)
            link = BASE_URL + first_post['href']
            article_id = link.split('articleId=')[-1]
            return {"id": article_id, "title": title, "link": link}
    except Exception as e:
        print(f"抓取失敗: {e}")
    return None

def push_to_line(msg):
    configuration = Configuration(access_token=LINE_ACCESS_TOKEN)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(PushMessageRequest(
            to=USER_ID,
            messages=[TextMessage(text=msg)]
        ))

def main():
    if not LINE_ACCESS_TOKEN or not USER_ID:
        print("錯誤: 找不到 LINE 金鑰設定")
        return

    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            history = json.load(f)
    else:
        history = {}

    for site in TARGET_SITES:
        current = get_latest_article(site['url'])
        if not current: continue
        
        if history.get(site['name']) != current['id']:
            msg = f"🔔 {site['name']} 有新內容！\n\n【{current['title']}】\n\n連結：{current['link']}"
            push_to_line(msg)
            history[site['name']] = current['id']

    with open(DB_FILE, 'w') as f:
        json.dump(history, f)

if __name__ == "__main__":
    main()