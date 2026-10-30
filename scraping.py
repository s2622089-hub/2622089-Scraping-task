
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
import time
import csv
from collections import deque

# 武蔵野大学のトップページ
START_URL = "https://www.musashino-u.ac.jp/"

# 同一ドメイン
DOMAIN = "www.musashino-u.ac.jp"

# URLとタイトルを保存する辞書
site_map = {}

# 巡回するURLを管理するキュー
queue = deque([START_URL])

# アクセス済みURL
visited = set()

# User-Agent
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; UniversitySiteMapBot/1.0)"
}

# CSVファイルを最初に開く
with open("sitemap.csv", "w", newline="", encoding="utf-8-sig") as f:

    writer = csv.writer(f)

    # ヘッダーを書き込む
    writer.writerow(["URL", "Title"])
    f.flush()

    try:
        while queue:

            url = queue.popleft()

            if url in visited:
                continue

            visited.add(url)

            try:
                # サーバーへの負荷を軽減
                time.sleep(1)

                response = requests.get(
                    url,
                    headers=headers,
                    timeout=15
                )

                response.raise_for_status()

                # HTML以外は対象外
                content_type = response.headers.get("Content-Type", "")

                if "text/html" not in content_type:
                    continue

                # 文字コードを自動判定
                response.encoding = response.apparent_encoding

                # HTMLを解析
                soup = BeautifulSoup(
                    response.text,
                    "html.parser"
                )

                # titleを取得
                title_tag = soup.find("title")

                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    title = ""

                # 辞書に格納
                site_map[url] = title

                # CSVにリアルタイム保存
                writer.writerow([url, title])

                # CSVへの書き込みを確定
                f.flush()

                # 進捗表示
                print(
                    f"取得済み: {len(site_map)}件 | "
                    f"URL: {url} | TITLE: {title}"
                )

                # ページ内のリンクを取得
                for link in soup.find_all("a", href=True):

                    next_url = urljoin(
                        response.url,
                        link["href"]
                    )

                    # フラグメントを除去
                    next_url, _ = urldefrag(next_url)

                    parsed_url = urlparse(next_url)

                    # 同一ドメインのみ対象
                    if (
                        parsed_url.scheme in ("http", "https")
                        and parsed_url.netloc == DOMAIN
                        and next_url not in visited
                        and next_url not in queue
                    ):
                        queue.append(next_url)

            except requests.exceptions.RequestException as e:
                print("アクセスエラー:", url, e)

    except KeyboardInterrupt:
        print("\nプログラムを中断しました。")

print("--------------------------------")
print("スクレイピング終了")
print("取得ページ数:", len(site_map))
print("sitemap.csvに保存しました")
