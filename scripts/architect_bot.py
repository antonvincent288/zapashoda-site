#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Архитектор-бот zapashoda (Pollinations GPT-OSS 20B).
Раз в 6 часов (GitHub Actions) читает мост Алисы и roadmap, кладёт совет/ответ
в bridge/architect_to_alisa.json. Пишет ТОЛЬКО bridge/ — деплой не триггерит.
Секретов не читает и не пишет. Правила: без выдуманных фактов и цен."""
import json, os, sys, time, re, base64, urllib.request, urllib.error

REPO = os.environ.get("GITHUB_REPOSITORY") or "antonvincent288/zapashoda-site"
TOKEN = os.environ.get("GITHUB_TOKEN") or ""
POLLINATIONS_MODEL = "openai-fast"  # GPT-OSS 20B Reasoning (OVH)
FALLBACK_MODEL = "openai"
BR = "bridge"
def req(url, method="GET", data=None, headers=None, timeout=90):
    h = {"User-Agent": "architect-bot/1.0", "Accept": "application/vnd.github+json"}
    h.update(headers or {})
    if TOKEN: h["Authorization"] = "token " + TOKEN
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        resp = urllib.request.urlopen(r, timeout=timeout); raw = resp.read()
        try: return resp.status, json.loads(raw)
        except Exception: return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, raw
def blob_sha(content):
    st, b = req("https://api.github.com/repos/%s/git/blobs" % REPO, "POST",
        {"content": base64.b64encode(content.encode("utf-8")).decode(), "encoding": "base64"})
    assert st == 201, (st, b)
    return b["sha"]
def get_file(path):
    st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
    if st != 200: return None
    head = ref["object"]["sha"]
    st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
    if st != 200: return None
    st, t = req("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, c["tree"]["sha"]), "GET")
    if st != 200: return None
    it = next((x for x in t["tree"] if x["path"] == path), None)
    if not it: return None
    st, bl = req("https://api.github.com/repos/%s/git/blobs/%s" % (REPO, it["sha"]))
    if st != 200: return None
    return base64.b64decode(bl["content"]).decode("utf-8")
def push_files(files, message):
    for attempt in range(3):
        st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
        head = ref["object"]["sha"]
        st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
        items = [{"path": p, "mode": "100644", "type": "blob", "sha": blob_sha(cnt)} for p, cnt in files.items()]
        st, tree = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST",
            {"base_tree": c["tree"]["sha"], "tree": items})
        assert st == 201, (st, tree)
        st, newc = req("https://api.github.com/repos/%s/git/commits" % REPO, "POST",
            {"message": message, "tree": tree["sha"], "parents": [head]})
        assert st == 201, (st, newc)
        st, _ = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO, "PATCH",
            {"sha": newc["sha"], "force": False})
        if st == 200: return newc["sha"]
        time.sleep(8)
    raise RuntimeError("не удалось запушить (гонка)")
def pollinations(prompt, system):
    body = {"model": POLLINATIONS_MODEL,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.4, "max_tokens": 1100, "private": True}
    for attempt in range(4):
        st, d = req("https://text.pollinations.ai/openai", "POST", body, headers={"Content-Type": "application/json"})
        if st == 429:
            time.sleep(50); continue
        if st == 200 and isinstance(d, dict) and d.get("choices"):
            return d["choices"][0]["message"]["content"]
        if st == 200:
            body["model"] = FALLBACK_MODEL
        time.sleep(10)
    raise RuntimeError("Pollinations недоступен")
def parse_json(text):
    text = re.sub(r"```(?:json)?", "", str(text)).strip()
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try: return json.loads(m.group(0))
        except Exception: pass
    return None
SYSTEM = """Ты — архитектор проекта zapashoda-ev.ru (зарядные аксессуары для электромобилей; НЕ огнетушители).
Твоя работа: советы, планирование и ревью по задачам, которые ставит Алиса (AI-ассистент владельца)
и по состоянию репо. ТЫ НЕ ПИШЕШЬ КОД и не меняешь сайт — только анализируешь и даёшь план.
Жёсткие правила:
1. Ни одного выдуманного факта. Если данных нет — прямо пиши «нужно уточнить у владельца».
2. Цены и коммерческие условия НЕ придумывать. Где нужна цена — писать [ЦЕНА: согласовать с владельцем].
3. Секреты (токены, ключи) не упоминать и не запрашивать.
4. Отвечай СТРОГО одним JSON-объектом без markdown-обёрток:
{"topic": "короткая тема", "body": "полный текст совета/ответа", "priority": "normal", "expect": "answer"}
5. Пиши по-русски, по делу, без воды, до ~1200 знаков."""
def main():
    roadmap = get_file(BR + "/roadmap.md") or "roadmap отсутствует"
    ai = get_file("AI_BRIDGE.json")
    a2z_raw = get_file(BR + "/architect_to_alisa.json") or '{"protocol":"zapashoda-bridge-v1","messages":[]}'
    z2a_raw = get_file(BR + "/alisa_to_architect.json") or '{"protocol":"zapashoda-bridge-v1","messages":[]}'
    state_raw = get_file(BR + "/architect_state.json") or "{}"
    a2z = json.loads(a2z_raw); z2a = json.loads(z2a_raw)
    try: state = json.loads(state_raw)
    except Exception: state = {}
    alisa_msgs = [m for m in z2a.get("messages", []) if m.get("from") == "alisa"]
    my_msgs = a2z.get("messages", [])
    def z_num(mid):
        m = re.match(r"Z-(\d+)", str(mid or ""))
        return int(m.group(1)) if m else -1
    last_z = state.get("last_alisa_id", "")
    pending = [m for m in alisa_msgs if z_num(m.get("id")) > z_num(last_z)]
    ctx_pending = "\n\n".join("id=%s | topic=%s\n%s" % (m.get("id"), m.get("topic"), (m.get("body") or "")[:1500]) for m in pending[-4:])
    ctx_mine = "\n\n".join("id=%s (ответ на %s): %s" % (m.get("id"), m.get("answer_to"), (m.get("body") or "")[:400]) for m in my_msgs[-3:])
    nums = [int(m.group(1)) for m in (re.match(r"A-(\d+)", x.get("id", "")) for x in my_msgs) if m]
    next_num = max(nums + [0]) + 1
    if pending:
        task = "ответь на последнее сообщение Алисы (иди по его смыслу; связывание произойдёт по порядку очереди)"
    else:
        task = "новых сообщений Алисы нет — дай один полезный статус-совет по текущему этапу проекта; без выдуманного прогресса"
    prompt = "Состояние проекта (roadmap):\n%s\n\nСтатус сборки (AI_BRIDGE.json):\n%s\n\nНедавние ответы архитектора:\n%s\n\nНовые сообщения Алисы (%d):\n%s\n\nЗадача: %s\nВерни СТРОГО JSON в формате из системной инструкции." % (
        roadmap[:6000], (ai or "{}")[:1200], ctx_mine, len(pending), ctx_pending or "(нет)", task)
    content = pollinations(prompt, SYSTEM)
    parsed = parse_json(content) or {"topic": "Совет архитектора", "body": str(content)[:1500], "priority": "normal", "expect": "answer"}
    import datetime
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec="seconds")
    msg = {"id": "A-%04d" % next_num, "ts": ts, "from": "architect",
           "topic": str(parsed.get("topic", "Без темы"))[:120],
           "body": str(parsed.get("body", content))[:4000],
           "priority": parsed.get("priority") if parsed.get("priority") in ("normal", "high") else "normal",
           "expect": "answer", "answer_to": (pending[-1]["id"] if pending else None)}
    a2z.setdefault("messages", []).append(msg)
    state["last_alisa_id"] = (pending[-1]["id"] if pending else last_z) or ""
    sha = push_files({BR + "/architect_to_alisa.json": json.dumps(a2z, ensure_ascii=False, indent=2),
                      BR + "/architect_state.json": json.dumps(state, ensure_ascii=False, indent=2)},
                     "architect-bot: %s" % msg["id"])
    print("pushed", sha[:12], "|", msg["id"], "|", msg["topic"])
if __name__ == "__main__":
    main()
