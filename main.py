import requests
from bs4 import BeautifulSoup
import json, os, time

# === LINE Bot 設定 ===
LINE_CHANNEL_ACCESS_TOKEN = "osuxiHDjx/wQBptWVIaudoFZQbPUWp9d9RButRBkcr59B21LkIaGStxp+2KuB0eXuCAdHHhQNyICkXSjntITiWyEDLQY+yB5fmWK/sTHrPg8NfOOV+gq30qkq+teRsAQZTlcECzceGGjiMhSPF4cOAdB04t89/1O/w1cDnyilFU="
LINE_USER_ID = "U7c2f2f29de1bbe0d55b0bf800c741c77"

def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{
            "type": "text",
            "text": text
        }]
    }
    r = requests.post(url, headers=headers, json=data)
    print("LINE 傳送結果:", r.status_code, r.text)


# === AION2 公告爬蟲 ===
def fetch_latest_notice():
    url = "https://tw.ncsoft.com/aion2/board/notice/list"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    # 抓取公告列表
    notices = soup.select("ul.board_list li")

    results = []
    for n in notices:
        link_tag = n.select_one("a")
        if not link_tag:
            continue
        title = link_tag.text.strip()
        link = "https://tw.ncsoft.com" + link_tag["href"]
        results.append((title, link))
    return results


# === 檢查是否有新公告 ===
def check_for_new_notices(current):
    filename = "latest.json"

    if not os.path.exists(filename):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)
        return []

    with open(filename, "r", encoding="utf-8") as f:
        previous = json.load(f)

    prev_titles = {n[0] for n in previous}
    new_items = [n for n in current if n[0] not in prev_titles]

    if new_items:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(current, f, ensure_ascii=False, indent=2)

    return new_items


# === 主程式 ===
def main():
    current_notices = fetch_latest_notice()
    new_notices = check_for_new_notices(current_notices)

    if new_notices:
        for title, link in new_notices:
            msg = f"📢【AION2 新公告】\n{title}\n{link}"
            send_line_message(msg)
            print("已發送通知:", title)
    else:
        print("目前沒有新公告。")

if __name__ == "__main__":
    while True:
        main()
        time.sleep(600)  # 每10分鐘檢查一次

# === 啟動 Flask ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ AION2 monitor 正在運行中！"

if __name__ == "__main__":
    threading.Thread(target=background_job, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
