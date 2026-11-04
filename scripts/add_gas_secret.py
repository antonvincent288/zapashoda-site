#!/usr/bin/env python3
"""Однокомандная установка секрета GAS_CLASP_TOKEN в репозиторий.

ВАЖНО: токен передаётся в переменных окружения, НЕ в коде и НЕ в чате.
Запуск у себя (терминал владельца):

  pip install pynacl requests
  export GH_TOKEN="ghp_..."            # PAT с правами repo/admin
  export GAS_CLASP_TOKEN="ваш clasp токен"
  python scripts/add_gas_secret.py

Скрипт сам возьмёт публичный ключ репозитория, зашифрует токен
(libsodium sealed box, как требует GitHub) и запишет секрет.
"""
import os, sys, base64, json
import urllib.request
try:
    from nacl import encoding, public as nacl_public
except ImportError:
    print("pip install pynacl"); sys.exit(1)

REPO = os.environ.get("GITHUB_REPOSITORY", "antonvincent288/zapashoda-site")
SECRET_NAME = "GAS_CLASP_TOKEN"

def api(path, method="GET", data=None, token=None):
    req = urllib.request.Request("https://api.github.com/%s" % path,
                                 data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": "token " + token,
                                          "Accept": "application/vnd.github+json",
                                          "User-Agent": "zapashoda-secret-helper"},
                                 method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read())
        except Exception: return e.code, {}

def main():
    token = os.environ.get("GH_TOKEN", "")
    secret = os.environ.get("GAS_CLASP_TOKEN", "")
    if not token:
        print("нет GH_TOKEN в окружении"); sys.exit(1)
    if not secret:
        print("нет GAS_CLASP_TOKEN в окружении"); sys.exit(1)
    st, key = api("repos/%s/actions/secrets/public-key" % REPO, token=token)
    if st != 200:
        print("не удалось получить публичный ключ (проверь права PAT: repo, admin или 'Secrets write'):", st); sys.exit(1)
    pk = nacl_public.PublicKey(key["key"].encode("utf-8"), encoding.Base64Encoder())
    sealed = nacl_public.SealedBox(pk).encrypt(secret.encode("utf-8"))
    enc = base64.b64encode(sealed).decode("utf-8")
    st, resp = api("repos/%s/actions/secrets/%s" % (REPO, SECRET_NAME), "PUT",
                   {"encrypted_value": enc, "key_id": key["key_id"]}, token=token)
    if st in (201, 204):
        print("OK: секрет %s записан в %s" % (SECRET_NAME, REPO))
    else:
        print("ошибка", st, resp); sys.exit(1)
    # контроль: секрет числится
    st, lst = api("repos/%s/actions/secrets" % REPO, token=token)
    names = [s["name"] for s in lst.get("secrets", [])]
    print("секреты в репо:", names)
    if SECRET_NAME in names:
        print("ПОДТВЕРЖДЕНО: gas_watch теперь увидит токен при следующем запуске turbo")

if __name__ == "__main__":
    main()
