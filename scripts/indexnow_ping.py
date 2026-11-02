#!/usr/bin/env python3
# IndexNow: уведомить поисковики (Яндекс, Bing) об обновлённых URL.
# Работает после деплоя: берёт sitemap.xml с прода и отправляет URL батчем.
import urllib.request, json, sys

KEY = "a1c7f3d9e2b5604f8d2a71c9be43f560"
HOST = "zapashoda-ev.ru"

def main():
    sm = urllib.request.urlopen(f"https://{HOST}/sitemap.xml", timeout=60).read().decode("utf-8", "ignore")
    urls = [u.replace("</loc>", "").split("https://")[-1] for u in sm.split("<loc>")]
    urls = ["https://" + u for u in urls if u and HOST in u]
    urls = list(dict.fromkeys(urls))
    if not urls:
        print("sitemap пуст"); return
    payload = json.dumps({"host": HOST, "key": KEY,
        "keyLocation": f"https://{HOST}/{KEY}.txt", "urlList": urls}).encode("utf-8")
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "zapashoda-indexnow"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        print("IndexNow:", resp.status, "| url в очереди:", len(urls))
    except Exception as e:
        print("IndexNow error:", e)

if __name__ == "__main__":
    main()
