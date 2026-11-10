#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Публикатор: заливка файла в GitHub через Contents API с SHA-защитой.
Правило команды: единственный способ править прод-файлы. При расхождении SHA ветки
с ожидаемым (или при занятом имени) — отказ HEAD_MOVED, никаких затираний.

env: GITHUB_TOKEN (обязателен)
Использование:
  python3 gh_put_file.py --file local/path.astro \
      --repo antonvincent288/zapashoda-site --branch astrowind-migration \
      --path-in-repo site/src/pages/blog/x.astro --message "fix: ..."
  [--expect-sha <sha>]   — отказ, если текущий SHA пути в ветке не совпал (файл изменили за спиной)
  [--create-only]        — не перезаписывать существующий файл (для новых), иначе добавит « (1)»-путём нельзя: вернёт ошибку TAKEN
Выход: печатает {"ok":true,"commit":"<sha>"} или {"ok":false,"error":"HEAD_MOVED|TAKEN|HTTP <n>"}; exit 1 при ошибке.
"""
import argparse, base64, json, os, sys, urllib.request, urllib.parse

API = "https://api.github.com"

def api(url, token, data=None, method=None):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + token, "Content-Type": "application/json",
                                               "User-Agent": "zapashoda-agent/1.0"},
                                 data=data, method=method)
    try:
        r = urllib.request.urlopen(req, timeout=60)
        return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        try: return e.code, json.load(e)
        except Exception: return e.code, {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--branch", required=True)
    ap.add_argument("--path-in-repo", required=True)
    ap.add_argument("--message", required=True)
    ap.add_argument("--expect-sha", default=None)
    ap.add_argument("--create-only", action="store_true")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        print(json.dumps({"ok": False, "error": "NO_TOKEN (env GITHUB_TOKEN)"})); sys.exit(1)
    enc = urllib.parse.quote(args.path_in_repo, safe="")
    st, cur = api(f"{API}/repos/{args.repo}/contents/{enc}?ref={args.branch}", token)
    if args.create_only and st == 200:
        print(json.dumps({"ok": False, "error": "TAKEN", "sha": cur.get("sha", "")})); sys.exit(1)
    if args.expect_sha and st == 200 and cur.get("sha") != args.expect_sha:
        print(json.dumps({"ok": False, "error": "HEAD_MOVED", "remote_sha": cur.get("sha", ""), "expected": args.expect_sha})); sys.exit(1)
    body = {
        "message": args.message,
        "content": base64.b64encode(open(args.file, "rb").read()).decode(),
        "branch": args.branch,
    }
    if st == 200 and cur.get("sha"): body["sha"] = cur["sha"]
    elif st != 404:
        print(json.dumps({"ok": False, "error": f"HTTP {st}"})); sys.exit(1)
    st2, res = api(f"{API}/repos/{args.repo}/contents/{enc}", token, data=json.dumps(body).encode(), method="PUT")
    if st2 in (200, 201):
        print(json.dumps({"ok": True, "commit": res["commit"]["sha"][:9], "path": args.path_in_repo}))
        sys.exit(0)
    print(json.dumps({"ok": False, "error": f"HTTP {st2}", "resp": str(res.get("message", ""))[:200]}))
    sys.exit(1)

if __name__ == "__main__":
    main()
