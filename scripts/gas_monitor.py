#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GAS-монитор: ежедневный cron дергает endpoint bonus_selftest на GAS (v12)
и пишет вердикт в мост. GAS не вставлен → напоминает владельцу."""
import json, os, sys, urllib.request, urllib.error, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guide_writer import get_file, push_files, BR, REPO, req
def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec="seconds")
def main():
    cfg = json.loads(get_file("data/site_config.json") or "{}")
    gas = str((cfg.get("shop") or {}).get("gas_pay_url") or cfg.get("gas_pay_url") or "")
    if not gas:
        body = "GAS-монитор: gas_pay_url не найден в site_config — напоминание владельцу о вставке GAS v11+v12."
        status = "not-configured"
    else:
        try:
            body_req = json.dumps({"t": "bonus_selftest"}).encode()
            r = urllib.request.Request(gas, data=body_req, headers={"Content-Type": "text/plain;charset=utf-8"})
            resp = json.loads(urllib.request.urlopen(r, timeout=25).read().decode("utf-8", errors="replace"))
            if resp.get("ok") and resp.get("version") == "v12":
                status = "live"
                body = ("GAS v12 ЖИВОЙ: продукты %d, все по 990 ₽: %s; бонус %d ₽; строк в «Бонусах»: %d. "
                        "Владелец: можно проводить первую боевую транзакцию." % (
                            resp.get("products"), "ДА" if resp.get("all990") else "НЕТ(!)",
                            resp.get("bonusRub"), resp.get("bonusRows")))
            elif resp.get("ok"):
                status = "v11-only"
                body = "GAS отвечает, но это v11 (нет selftest-эндпоинта) — вставить дельту v12 (reports/gas_v12_shop_products_audit.js)."
            else:
                status = "no-endpoint"
                body = "GAS отвечает без selftest — v11 вставлена, v12 нет. Вставить дельту v12."
        except Exception as e:
            status = "down"
            body = "GAS-монитор: endpoint недоступен (%s). Напоминание владельцу: вставить GAS v11 + дельту v12." % type(e).__name__
    st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
    head = ref["object"]["sha"]
    st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
    a2z = json.loads(get_file(BR + "/architect_to_alisa.json") or '{"messages":[]}')
    a2z.setdefault("messages", []).append({"id": "M-%s" % now()[11:13] + now()[14:16], "ts": now(),
        "from": "gas-monitor", "topic": "GAS статус (%s)" % status, "body": body[:1500],
        "priority": "normal", "expect": "none", "answer_to": None})
    def blobf(cnt):
        st, b = req("https://api.github.com/repos/%s/git/blobs" % REPO, "POST", {"content": __import__("base64").b64encode(cnt.encode("utf-8")).decode(), "encoding": "base64"})
        assert st == 201; return b["sha"]
    items = [{"path": BR + "/architect_to_alisa.json", "mode": "100644", "type": "blob", "sha": blobf(json.dumps(a2z, ensure_ascii=False, indent=2))}]
    st, tr = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST", {"base_tree": c["tree"]["sha"], "tree": items})
    st, nc = req("https://api.github.com/repos/%s/git/commits" % REPO, "POST", {"message": "gas-monitor: " + status, "tree": tr["sha"], "parents": [head]})
    st, _ = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO, "PATCH", {"sha": nc["sha"], "force": False})
    print(status, "|", body[:160])
if __name__ == "__main__":
    main()
