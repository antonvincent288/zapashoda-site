import json, time, urllib.request
UA = {"User-Agent": "zapashoda-ev geo-audit/1.0 (api@zapashoda-ev.ru)"}
def rev(lat, lon):
    u = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=jsonv2&zoom=18&accept-language=ru"
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
        return json.loads(r.read().decode())
def norm(s):
    return (s or "").lower().replace("ё", "е")
stations = json.load(open("site/public/charging/stations.json"))["stations"]
bad, checked, errors = [], 0, 0
for s in stations:
    try:
        j = rev(s["lat"], s["lon"])
        a = j.get("address", {})
        road = a.get("road") or ""
        house = a.get("house_number") or ""
        city = a.get("city") or a.get("town") or a.get("village") or a.get("state") or ""
        geo = " ".join(p for p in [city, road, house] if p)
        db = norm(s.get("a") or "")
        verdict = "ok"
        if house and norm(house) in db:
            verdict = "ok"
        elif road and (norm(road).replace(" улица", "").replace(" ул.", "") in db):
            verdict = "warn"
        else:
            verdict = "bad"
        if verdict != "ok":
            bad.append({"n": s.get("n", ""), "a": s.get("a", ""), "lat": s["lat"], "lon": s["lon"], "geo": geo, "verdict": verdict})
    except Exception:
        errors += 1
    time.sleep(1.05)
    checked += 1
out = {"updated": time.strftime("%Y-%m-%dT%H:%M:%S"), "checked": checked, "errors": errors, "warn_bad_count": len(bad), "items": bad[:800]}
json.dump(out, open("site/public/charging/geo_audit.json", "w"), ensure_ascii=False, indent=1)
print("audit done: checked", checked, "bad/warn", len(bad), "errors", errors)
