#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Арт-Директор (Visual QA Validator) zapashoda — по регламенту владельца 03.11 (вечный).
Жёстко блокирует гайд-продукты, нарушающие визуальную упаковку:
① заглушки/пустые списки >3 пунктов ② антракит/светлые разделители — проверяются на этапе
сборки PDF (VISUAL_SPEC ниже — контракт для компилятора) ③ боли/лайфхаки не в gbox
④ вода вместо хардкора. Заблокированное возвращается на перегенерацию."""
import json, os, re, sys, base64, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from guide_writer import get_file, push_files, qa_check_chapter, BR, REPO, req
VISUAL_SPEC = {
    "palette": {"anthracite": "#1d1d1f", "light": "#f5f5f7", "gold": "#D4AF37", "marine": "#003a40", "acid": "#c8ea95", "green": "#0aad0a"},
    "rules": [
        "PDF-компилятор обязан чередовать фоны разделов: антрацит → светлый → антрацит…",
        "Каждая боль/лайфхак — закруглённый бокс (радиус 12+) с акцентом #D4AF37 (линия/номер/иконка)",
        "Заглушки любого вида запрещены навсегда: [ЦЕНА…], TODO, пустые списки",
        "Каждая глава: ≥1 бокс, ≥8 маркеров хардкора (цифры/шаги/сроки/кВт/км/минуты), ≤3 оборотов воды",
    ],
}
def now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3))).isoformat(timespec="seconds")
def next_v_id(a2z):
    import re as _re
    nums = [int(m.group(1)) for m in (_re.match(r"V-(\d+)", x.get("id", "")) for x in a2z.get("messages", [])) if m]
    return max(nums + [0]) + 1
def main():
    base = BR + "/drafts/guides"
    st, ref = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO)
    if st != 200: return
    head = ref["object"]["sha"]
    st, c = req("https://api.github.com/repos/%s/git/commits/%s" % (REPO, head))
    st, t = req("https://api.github.com/repos/%s/git/trees/%s?recursive=1" % (REPO, c["tree"]["sha"]), "GET")
    paths = [it["path"] for it in t["tree"]]
    approved = [p for p in paths if p.startswith(base + "/approved/") and p.endswith(".json")]
    if not approved:
        print("approved пуст — проверять нечего"); return
    notes, files, deletes = [], {}, []
    for ap in approved:
        slug = ap.split("/")[-1][:-5]
        d = json.loads(get_file(ap))
        fails = []
        for i, ch in enumerate(d.get("chapters", [])):
            errs = qa_check_chapter(ch)
            if errs: fails.append("гл.%d: %s" % (i + 1, "; ".join(errs)))
        placeholders = sum(1 for ch in d.get("chapters", []) if re.search(r"\[ЦЕНА", ch))
        if placeholders: fails.append("заглушек в гайде: %d" % placeholders)
        if fails:
            # блок: возвращаем на перегенерацию
            draft_path = base + "/" + slug + ".json"
            draft = get_file(draft_path)
            if draft:
                dj = json.loads(draft)
                dj["qa_failed"] = fails[:6]
                files[draft_path] = json.dumps(dj, ensure_ascii=False, indent=1)
            deletes.append(ap)
            notes.append("БЛОК: %s → перегенерация. %s" % (slug, " | ".join(fails)[:400]))
        else:
            notes.append("OK: %s — упаковка соответствует регламенту" % slug)
    if notes:
        a2z = json.loads(get_file(BR + "/architect_to_alisa.json") or '{"messages":[]}')
        a2z.setdefault("messages", []).append({"id": "V-%04d" % next_v_id(a2z), "ts": now(), "from": "art-qa",
            "topic": "Арт-Директор: визуальный аудит гайдов", "body": "\n".join(notes)[:2800],
            "priority": "high" if any("БЛОК" in n for n in notes) else "normal",
            "expect": "review", "answer_to": None})
        files[BR + "/architect_to_alisa.json"] = json.dumps(a2z, ensure_ascii=False, indent=2)
    if deletes:
        items = [{"path": p, "mode": "100644", "type": "blob", "sha": None} for p in deletes]
    else:
        items = []
    st, tree = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST", {"base_tree": c["tree"]["sha"], "tree": items + [{"path": p, "mode": "100644", "type": "blob", "sha": None} for p in []]})
    # blobs
    def _blob(cnt):
        st, b = req("https://api.github.com/repos/%s/git/blobs" % REPO, "POST", {"content": base64.b64encode(cnt.encode("utf-8")).decode(), "encoding": "base64"})
        assert st == 201, (st, b); return b["sha"]
    items += [{"path": p, "mode": "100644", "type": "blob", "sha": _blob(cnt)} for p, cnt in files.items()]
    st, tree = req("https://api.github.com/repos/%s/git/trees" % REPO, "POST", {"base_tree": c["tree"]["sha"], "tree": items})
    assert st == 201, (st, tree)
    msg = "art-qa: " + ("блок %d гайдов → перегенерация" % len(deletes) if deletes else "визуальный аудит пройден")
    st, newc = req("https://api.github.com/repos/%s/git/commits" % REPO, "POST", {"message": msg, "tree": tree["sha"], "parents": [head]})
    assert st == 201, (st, newc)
    st, _ = req("https://api.github.com/repos/%s/git/refs/heads/main" % REPO, "PATCH", {"sha": newc["sha"], "force": False})
    if st != 200: raise RuntimeError("гонка пуша art-qa")
    print(msg, "|", "; ".join(notes)[:300])
if __name__ == "__main__":
    main()
