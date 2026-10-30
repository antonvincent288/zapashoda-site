# -*- coding: utf-8 -*-
"""
Запас хода — генератор SEO-сайта v5 (Apple-дизайн).
Разделы: 137 моделей, 12 руководств, каталог новостей (RSS + своя страница у каждой),
VIN-справочник (хаб + бренды), карта зарядных станций (OSM/Overpass), llms.txt,
OG-карточки (PIL), поиск, sitemap, robots, 404.
Самодостаточен: данные моделей зашиты в DATA_B64. Запуск: python3 build.py [папка] (по умолчанию _site).
Домен: переменная окружения SITE_DOMAIN (по умолчанию https://zapashoda-ev.ru).
"""
import gzip, base64, json, os, re, sys, html, shutil
from datetime import date

DATA_B64 = (
 "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"
)

DATA = json.loads(gzip.decompress(base64.b64decode(DATA_B64.encode("ascii"))).decode("utf-8"))
PAINS = DATA["pains"]
MODELS = DATA["models"]

BRAND_PAINS = {
 'Zeekr': ['ZE-01','ZE-02','ZE-03','ZE-04','ZV-01'], 'Voyah': ['VO-01','VO-02','VO-03','VO-04','VO-05','VO-06','ZV-01'],
 'BYD': ['BYD-01','BYD-02','BYD-03','BYD-04','BAT-03'], 'Denza (BYD)': ['BYD-01','BYD-02','BAT-03'],
 'Li Auto': ['PHEV-02','PHEV-01','PHEV-03'], 'Avatr': ['AV-01','AV-02','BAT-01'], 'Hongqi': ['HO-01','HO-02','HO-03','BAT-01'],
 'Geely': ['GE-01','GE-02','BAT-01'], 'Deepal': ['DE-01','DE-02','PHEV-01','PHEV-03','BAT-01'],
 'MG': ['MG-01','MG-02','MG-03','BAT-01'], 'Kia': ['KR-01','KR-02'], 'Hyundai': ['KR-01','KR-02'], 'Genesis': ['KR-02'],
 'VW': ['EU-01','EU-02'], 'Skoda': ['EU-01','EU-02'], 'Audi': ['EU-01','EU-02'], 'Mercedes': ['EU-01','EU-02'], 'BMW': ['EU-02'],
 'Tesla': ['TS-01','TS-02','BAT-01'], 'Nissan': ['LEAF-01','LEAF-02','BAT-01','ST-05'],
 'Evolute': ['EVOL-01','EVOL-02','BAT-01'], 'Moskvich': ['EVOL-03','BAT-01'], 'AITO': ['AITO-01','BAT-01'],
 'Exeed': ['EX-01','BAT-01'], 'M-Hero': ['MHE-01','ST-05'], 'Mitsubishi': ['T1-02','BAT-01'],
 'Ora': ['BAT-01','BAT-03'], 'Xiaomi': ['BAT-01'], 'XPeng': ['BAT-01'], 'Leapmotor': ['BAT-01'], 'Changan': ['BAT-01'],
 'Lynk & Co': ['BAT-01'], 'JAC': ['BAT-01'], 'Neta': ['BAT-01'], 'Livan': ['BAT-01'], 'Skywell': ['BAT-01'],
 'SWM': ['BAT-01'], 'Kaiyi': ['BAT-01'], 'Wuling / Hongguang': ['BAT-01'], 'Dongfeng': ['BAT-01'], 'GAC': ['BAT-01'],
 'Seres': ['BAT-01'], 'IM Motors': ['BAT-01'], 'iCAR': ['BAT-01'], 'Luxeed (Chery/Huawei)': ['BAT-01'],
 'Stelato (BAIC/Huawei)': ['BAT-01'], 'Onvo (NIO)': ['BAT-01'], 'Lotus': ['BAT-01'], 'HiPhi': ['BAT-01'], 'Roewe': ['BAT-01'],
 'FAW': ['BAT-01']}
GROUP_EXTRA = {'GB/T': ['GB-01','GB-02','GB-03','GB-04','GB-05','GB-06','GB-07','GB-08'],
 'Type1/CCS1': ['T1-01','T1-02'], 'JP/CHAdeMO': ['T1-01','LEAF-01','LEAF-02']}
UNIVERSAL = ['UN-01','UN-02','UN-03','UN-04','UN-05','UN-06','ZM-01','ZM-02','ZM-03','ZM-04','ZM-05',
 'BAT-02','BAT-04','BAT-05','ST-01','ST-02','ST-03','ST-04','T1-03']
PHEV_UNIVERSAL = ['PHEV-01','PHEV-03']

def classify(m):
    ac = (m.get('ac') or ''); dc = (m.get('dc') or '')
    if 'GB/T' in ac or 'GB/T' in dc: return 'GB/T'
    if 'Type 1' in ac or 'CCS1' in dc or 'CCS1' in ac: return 'Type1/CCS1'
    if 'CHAdeMO' in dc or 'CHAdeMO' in ac: return 'JP/CHAdeMO'
    return 'EU'

def pains_for(m):
    grp = classify(m); ids = []
    ids += GROUP_EXTRA.get(grp, [])
    bp = BRAND_PAINS.get(m['brand'].strip())
    ids += bp if bp is not None else ['BAT-01']
    ids += UNIVERSAL
    if any(k in (m.get('type') or '') for k in ['EREV','PHEV','REX']): ids += PHEV_UNIVERSAL
    if 'Leaf' not in m['model']: ids = [i for i in ids if i not in ('LEAF-01','LEAF-02')]
    seen = set(); return [i for i in ids if not (i in seen or seen.add(i))]

_TR = str.maketrans({'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e','ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h','ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e','ю':'yu','я':'ya',' ':'-','/':'-','.':'-','(':'',')':'',',':'','+':'','–':'-','—':'-'})
def slug(s):
    return re.sub(r'-+','-', re.sub(r'[^a-z0-9\-]','', s.lower().translate(_TR))).strip('-')

# ================= КОНФИГ =================
SITE_DOMAIN = os.environ.get("SITE_DOMAIN", "https://zapashoda-ev.ru")
SITE_NAME = "Запас хода"
TG_CHANNEL = "https://t.me/zapashoda_ev"
TG_BOT_APP = "https://t.me/zapashoda_ev_bot/app"

# ================= APPLE-ДИЗАЙН =================
CSS = r""":root{--bg:#f5f5f7;--card:#fff;--ink:#1d1d1f;--muted:#6e6e73;--line:rgba(0,0,0,.07);--lime:#0071e3;--lime-ink:#ffffff;--max:1040px}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:-apple-system,BlinkMacSystemFont,'SF Pro Text','Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.55;-webkit-font-smoothing:antialiased;font-size:16px}
a{color:inherit}
.wrap{max-width:var(--max);margin:0 auto;padding:0 22px}
main{max-width:var(--max);margin:0 auto;padding:6px 22px 20px}
header{position:sticky;top:0;z-index:50;background:rgba(245,245,247,.72);backdrop-filter:saturate(180%) blur(20px);-webkit-backdrop-filter:saturate(180%) blur(20px);border-bottom:1px solid var(--line)}
.hwrap{max-width:var(--max);margin:0 auto;padding:0 22px;height:52px;display:flex;align-items:center;gap:20px}
.brand{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:700;font-size:17px;color:var(--ink);letter-spacing:-.01em}
.brand svg{display:block;flex:none}
nav{margin-left:auto;display:flex;gap:2px;flex-wrap:wrap;justify-content:flex-end;min-width:0}
nav a{color:var(--ink);opacity:.72;text-decoration:none;font-size:13.5px;padding:7px 12px;border-radius:999px;transition:opacity .15s,background .15s}
nav a:hover{opacity:1;background:rgba(0,0,0,.06)}
nav a.on{opacity:1;background:rgba(0,0,0,.08);font-weight:600}
.crumbs{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:18px 0 0;font-size:13px;color:var(--muted)}
.crumbs a{color:var(--muted);text-decoration:none;opacity:.85}
.crumbs a:hover{opacity:1;color:var(--ink)}
.crumbs .crumb-sep{color:var(--muted);opacity:.5}
.crumbs .crumb-cur{color:var(--ink);font-weight:600}
a:focus-visible,button:focus-visible,.search:focus-visible{outline:2px solid var(--lime);outline-offset:2px;border-radius:10px}
h1{font-size:clamp(30px,5vw,44px);line-height:1.12;letter-spacing:-.03em;font-weight:700;margin:44px 0 14px}
.lede{font-size:clamp(17px,2.3vw,21px);color:var(--muted);line-height:1.45;max-width:760px}
h2{font-size:clamp(22px,3.4vw,30px);letter-spacing:-.018em;font-weight:700;margin:48px 0 14px;scroll-margin-top:70px}
h3{font-size:17.5px;font-weight:600;margin:20px 0 8px;letter-spacing:-.01em}
p{margin:10px 0;max-width:740px;line-height:1.75}
.note{color:var(--muted);font-size:14px;max-width:740px}
.card{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:22px 24px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.05)}
.card h3{margin-top:0}
.sol{background:rgba(0,113,227,.07);border-radius:14px;padding:14px 18px;margin-top:12px;font-size:15px}
.pain-id{display:inline-block;background:#f0f0f3;color:var(--muted);font-size:10.5px;font-weight:700;letter-spacing:.08em;padding:3px 10px;border-radius:999px;margin-bottom:10px}
.tag{border:1px solid var(--line);border-radius:999px;padding:5px 13px;font-size:12.5px;color:var(--muted);font-weight:500;background:#fff;display:inline-block;margin:0 6px 8px 0}
.tag.lime{background:var(--lime);color:var(--lime-ink);border-color:transparent;font-weight:600}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;padding:13px 26px;border-radius:999px;font-weight:600;font-size:15px;text-decoration:none;transition:opacity .2s;cursor:pointer;border:none}
.btn:hover{opacity:.88}
.btn.lime{background:var(--lime);color:var(--lime-ink);box-shadow:0 8px 24px rgba(0,113,227,.18)}
.btn.ghost{background:#e8e8ed;color:var(--ink)}
.btn.ghost:hover{background:#dfdfdF}
.cta{display:flex;gap:12px;flex-wrap:wrap;margin:36px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.mcard{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 22px;text-decoration:none;color:inherit;display:block;transition:transform .2s,box-shadow .2s;box-shadow:0 1px 2px rgba(0,0,0,.04),0 8px 24px rgba(0,0,0,.05)}
.mcard:hover{transform:translateY(-3px);box-shadow:0 12px 32px rgba(0,0,0,.1)}
.mcard b{font-size:15.5px;letter-spacing:-.01em;display:block}
.mcard span{display:block;font-size:13.5px;color:var(--muted);margin-top:6px}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:16px 0;border:1px solid var(--line);border-radius:14px;background:#fff}
.tw table{min-width:520px;border:none}
table{width:100%;border-collapse:collapse;font-size:14.5px;background:#fff}
td,th{padding:11px 14px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);font-weight:600;white-space:nowrap}
tr:last-child td{border-bottom:0}
.kicker{font-size:12px;font-weight:700;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}
.hero{padding:58px 0 4px;max-width:860px}
.hero h1{margin-top:0}
.hero .ctas{margin-top:26px}
.search{width:100%;max-width:560px;padding:14px 20px;border-radius:999px;border:1px solid var(--line);font-size:16px;background:#fff;margin:24px 0 8px;display:block}
.search:focus{outline:none;border-color:transparent;box-shadow:0 0 0 3px rgba(0,113,227,.25)}
.banner{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 16px;font-size:13.5px;color:var(--muted);margin:14px 0}
.faq{background:#fff;border:1px solid var(--line);border-radius:14px;padding:16px 20px;margin:10px 0}
.faq summary{cursor:pointer;font-weight:600}
.faq p{margin-top:10px;font-size:14.5px}
.newsdate{font-size:13px;color:var(--muted);font-weight:500}
.newscard{background:#fff;border:1px solid var(--line);border-radius:18px;overflow:hidden;text-decoration:none;color:inherit;display:block;transition:transform .15s,border-color .15s}
.newscard:hover{transform:translateY(-3px);border-color:#d0d0d6}
.newscard img{width:100%;display:block;aspect-ratio:1200/630;object-fit:cover;background:#111}
.newscard .inner{padding:18px 20px 20px}
.newscard b{font-size:16px;letter-spacing:-.01em;display:block;line-height:1.35}
.newscard span{display:block;font-size:13.5px;color:var(--muted);margin-top:8px}
.nmap{height:540px;border-radius:18px;overflow:hidden;border:1px solid var(--line);margin:16px 0;background:#e5e3df}
.leaflet-container{font:inherit;background:#e5e3df}
.src{font-size:12.5px;color:var(--muted);margin-top:10px}
.src a{color:var(--muted);text-decoration:underline;word-break:break-all}
.back{display:inline-block;margin:20px 0 0;color:var(--muted);text-decoration:none;font-size:14px;font-weight:500}
.back:hover{color:var(--ink)}
.cbtns{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 6px}
.cbtn{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;padding:9px 18px;font-size:14px;font-weight:500;cursor:pointer;transition:background .15s,transform .15s}
.cbtn:hover{background:#f0f0f3;transform:translateY(-1px)}
hr.sep{border:0;border-top:1px solid var(--line);margin:34px 0}
footer{border-top:1px solid var(--line);margin-top:72px;padding:36px 0 64px;color:var(--muted);font-size:13px}
footer .wrap{display:flex;flex-direction:column;gap:10px}
footer a{color:var(--muted)}
@media(max-width:720px){
.hwrap{gap:8px;padding:0 12px;height:48px}
.brand{font-size:15px;flex:0 0 auto}
.brand span{display:none}
nav{margin-left:0;flex:1 1 auto;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;-webkit-overflow-scrolling:touch;justify-content:flex-start}
nav::-webkit-scrollbar{display:none}
nav a{padding:8px 11px;font-size:12.5px;white-space:nowrap;flex:0 0 auto}
main{padding:4px 16px 16px}
h1{margin-top:28px}
.hero{padding:36px 0 4px}
.grid,.grid2{grid-template-columns:1fr}
.card{padding:18px}
.crumbs{font-size:12px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none}
.crumbs::-webkit-scrollbar{display:none}
.crumbs a{white-space:nowrap}}
main{padding:4px 16px 16px}
h1{margin-top:28px}
.hero{padding:36px 0 4px}
.grid,.grid2{grid-template-columns:1fr}
.card{padding:18px}
}"""

LOGO_SVG = '<svg width="26" height="26" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="16" fill="#1d1d1f"/><path d="M37 8 L16 38 h14 l-5 18 25-34 H34 l8-14 z" fill="#ffffff"/></svg>'

NAV = [("/index.html","Модели"),("/news/","Новости"),("/pains.html","Проблемы"),("/charging/","Карта ЗУ"),("/vin/","VIN"),("/about.html","О проекте")]

def header_html(active):
    links = "".join('<a href="'+u+'"'+(' class="on"' if u==active else '')+'>'+t+'</a>' for u,t in NAV)
    return '<header><div class="hwrap"><a class="brand" href="/index.html" title="Запас хода">'+LOGO_SVG+'<span>Запас хода</span></a><nav>'+links+'</nav></div></header>'

FOOTER = ('<footer><div class="wrap"><div>Запас хода — практика владения электромобилем в России: разъёмы, зима, зарядка, расходы. '
 '137 моделей, ввезённых в РФ в 2019–2026. Информация из открытых источников; решения носят рекомендательный характер. '
 'При поломке высоковольтной системы обращайтесь в специализированный сервис.</div>'
 '<div>Карта зарядных станций: данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL), запросы через Overpass API.</div>'
 '<div><a href="https://t.me/zapashoda_ev">Telegram-канал</a> · <a href="https://t.me/zapashoda_ev_bot/app">Мини-приложение</a> · <a href="/feed.xml">RSS</a> · <a href="/llms.txt">llms.txt</a></div></div></footer>')

SHARE_JS = '''<script>
function sharePg(){var t=document.title,u=location.href;
 if(navigator.share){navigator.share({title:t,url:u}).catch(function(){});}
 else if(navigator.clipboard){navigator.clipboard.writeText(t+' — '+u).then(function(){alert('Ссылка скопирована');});}
 else{prompt('Скопируйте ссылку:',u);}
}
document.addEventListener('click',function(e){var a=e.target.closest('a.btn.share');if(a){e.preventDefault();sharePg();}});
</script>'''

def write_page(path, title, desc, body, canonical_rel, og="/assets/og/default.png", crumbs=None):
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)
    crumbs_html = ''
    ld_crumbs = ''
    if crumbs:
        items = [("/", "Запас хода")] + list(crumbs)
        parts = []
        for idx2, (href, label) in enumerate(items):
            last = (idx2 == len(items) - 1)
            lab = html.escape(str(label))
            if last:
                parts.append('<span class="crumb-cur" aria-current="page">' + lab + '</span>')
            else:
                parts.append('<a href="' + href + '">' + lab + '</a>')
        crumbs_html = '<nav class="crumbs" aria-label="Хлебные крошки">' + ' <span class="crumb-sep">›</span> '.join(parts) + '</nav>'
        ld_list = []
        for idx2, (href, label) in enumerate(items):
            item = '{"@type":"ListItem","position":' + str(idx2 + 1) + ',"name":"' + html.escape(str(label)).replace('"','') + '"'
            if href:
                item += ',"item":"' + SITE_DOMAIN + href + '"'
            item += '}'
            ld_list.append(item)
        ld_crumbs = '<script type="application/ld+json">{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[' + ','.join(ld_list) + ']}</script>'
    doc = ('<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
     '<title>' + html.escape(title) + '</title>'
     '<meta name="description" content="' + html.escape(desc) + '">'
     '<link rel="icon" href="data:image/svg+xml,%3Csvg%20xmlns=%27http://www.w3.org/2000/svg%27%20viewBox=%270%200%2064%2064%27%3E%3Crect%20width=%2764%27%20height=%2764%27%20rx=%2714%27%20fill=%27%231d1d1f%27/%3E%3Cpath%20d=%27M37%208%20L16%2038%20h14%20l-5%2018%2025-34%20H34%20l8-14%20z%27%20fill=%27%23ffffff%27/%3E%3C/svg%3E">'
     '<meta property="og:type" content="article"><meta property="og:image" content="' + SITE_DOMAIN + og + '">'
     '<meta property="og:title" content="' + html.escape(title) + '"><meta property="og:description" content="' + html.escape(desc[:200]) + '">'
     '<meta property="og:url" content="' + SITE_DOMAIN + canonical_rel + '"><meta property="og:site_name" content="' + SITE_NAME + '">'
     '<link rel="canonical" href="' + SITE_DOMAIN + canonical_rel + '">'
     '<link rel="stylesheet" href="/style.css">'
     '<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"' + html.escape(title) + '","description":"' + html.escape(desc[:250]) + '","inLanguage":"ru"}</script>' + ld_crumbs +
     '</head><body>' + header_html(canonical_rel) + '<main>' + crumbs_html + body + '</main>' + FOOTER + SHARE_JS + '</body></html>')
    with open(path,'w',encoding='utf-8') as f: f.write(doc)

def src_html(p):
    links = [s for s in p['src'] if s.startswith('http')]
    if links:
        return 'Источники: ' + ' '.join('<a href="'+s+'">'+html.escape(re.sub(r"^https?://(www\\.)?","",s)[:70])+'</a>' for s in links)
    return 'Решение собрано по отзывам владельцев на профильных форумах и сервисах'

PAIN_ARTICLES = [
 ('ne-zaryazhaetsya','Не заряжается электромобиль: 10 причин и что делать','От кабеля и порта до OBC, заземления и прошивки станции. Пошаговая диагностика.',['UN-03','UN-04','BAT-04']),
 ('podogrev-batarei','Подогрев батареи электромобиля: зачем нужен и как включить','Как холодная батарея режет скорость зарядки и запас хода; предпрогрев от сети и в пути.',['UN-01','ZM-01']),
 ('zaryadka-ot-rozetki','Зарядка электромобиля от розетки 220В: время, проводка, безопасность','Сколько реально даёт розетка, какая проводка нужна, почему вышибает автоматы.',['GB-07','GB-08']),
 ('adapter-gbt','Адаптеры для китайских электромобилей: Type2→GB/T, CCS2→GB/T','Какие переходники нужны, как не купить несовместимый, что с батареей питания адаптера.',['GB-01','GB-02','GB-04','GB-05','GB-06']),
 ('zapas-hoda-zimoy','Запас хода электромобиля зимой: почему падает на 30–45% и как вернуть','Физика мороза, отопители, предпрогрев, шины и стиль вождения.',['ZM-01','ZM-02','BAT-03']),
 ('kabel-ne-otdaet','Кабель зарядки не отдаёт из порта: что делать','Почему замок не разблокирует коннектор и где аварийный тросик.',['UN-04']),
 ('12v-akb','12-вольтовый аккумулятор электромобиля: главная тайная боль','Почему садится, какие машины чаще страдают (BYD, Voyah, MG, Kia EV6, Hongqi) и что делать.',['BAT-04']),
 ('lyuchok','Лючок зарядки не открывается на морозе и тугой механизм','Аварийные тросики, прогрев, смазка механизма.',['UN-05','ZV-01']),
 ('udlinitel','Удлинитель и кабель для зарядки электромобиля','Сечение, автоматы, почему дешёвый удлинитель опасен.',['GB-08','UN-06']),
 ('type1-ccs1','Как заряжать электромобиль из США или Кореи в России','Type 1/CCS1: переходники, замена порта, радикальный кейс с перекодировкой.',['T1-01','T1-02','T1-03']),
 ('tesla','Tesla в России: зарядка, адаптеры, Supercharger','EU vs US версии, адаптеры, прогрев батареи на морозе.',['TS-01','TS-02']),
 ('chademo','CHAdeMO: Leaf и другие японские EV','Сети CHAdeMO, деградация от быстрых зарядок, мониторинг батареи.',['LEAF-01','LEAF-02','BAT-01']),
]

RELATED = {
  'ne-zaryazhaetsya': ['Zeekr','BYD','Geely','Voyah','Evolute','Changan'],
  'podogrev-batarei': ['Zeekr','Voyah','BYD','Li Auto','Ora'],
  'zaryadka-ot-rozetki': ['Li Auto','Geely','Changan','BYD','Deepal'],
  'adapter-gbt': ['Zeekr','Voyah','BYD','Avatr','Changan','Exeed','Geely'],
  'zapas-hoda-zimoy': ['BYD','Zeekr','Changan','Ora','MG'],
  'kabel-ne-otdaet': ['Zeekr','Voyah','BYD','MG'],
  '12v-akb': ['BYD','Voyah','MG','Kia','Hongqi'],
  'lyuchok': ['Voyah','Zeekr'],
  'udlinitel': ['Geely','Changan','Li Auto'],
  'type1-ccs1': ['Kia','Hyundai','Tesla','Mitsubishi','Ford'],
  'tesla': ['Tesla'],
  'chademo': ['Nissan'],
}

# ================= VIN-СПРАВОЧНИК =================
VIN_BRANDS = {
 'Zeekr': ('Китай','Группа Geely; заводы в Нинбо и Циндао. Код производителя начинается на L (Китай).'),
 'Li Auto': ('Китай','Заводы в Чанчжоу; код производителя начинается на L.'),
 'BYD': ('Китай','Заводы в Шэньчжэне, Сиане, Чанша и др.; код начинается на L.'),
 'Denza (BYD)': ('Китай','Совместное предприятие BYD и Mercedes-Benz; код начинается на L.'),
 'Voyah': ('Китай','Группа Dongfeng, завод в Ухане; код начинается на L.'),
 'Avatr': ('Китай','Changan + CATL + Huawei; код начинается на L.'),
 'Hongqi': ('Китай','FAW, заводы в Чанчуне; код начинается на L.'),
 'Geely': ('Китай','Заводы в Нинбо и др.; код начинается на L.'),
 'Deepal': ('Китай','Changan; код начинается на L.'),
 'Exeed': ('Китай','Chery; код начинается на L.'),
 'Changan': ('Китай','Заводы в Чунцине; код начинается на L.'),
 'AITO': ('Китай','Seres + Huawei; код начинается на L.'),
 'M-Hero': ('Китай','Dongfeng (Mengshi); код начинается на L.'),
 'Ora': ('Китай','Great Wall Motor; код начинается на L.'),
 'Xiaomi': ('Китай','Завод в Пекине; код начинается на L.'),
 'XPeng': ('Китай','Заводы в Чжаоцине и Ухане; код начинается на L.'),
 'Leapmotor': ('Китай','Код начинается на L.'),
 'Lynk & Co': ('Китай','Geely-Volvo; код начинается на L.'),
 'JAC': ('Китай','Код начинается на L.'),
 'Neta': ('Китай','Код начинается на L.'),
 'Livan': ('Китай','Geely-Renault JV; код начинается на L.'),
 'Skywell': ('Китай','Код начинается на L.'),
 'SWM': ('Китай','Код начинается на L.'),
 'Kaiyi': ('Китай','Код начинается на L.'),
 'Wuling / Hongguang': ('Китай','SAIC-GM-Wuling; код начинается на L.'),
 'Dongfeng': ('Китай','Код начинается на L.'),
 'GAC': ('Китай','Код начинается на L.'),
 'Seres': ('Китай','Код начинается на L.'),
 'IM Motors': ('Китай','SAIC; код начинается на L.'),
 'iCAR': ('Китай','Chery; код начинается на L.'),
 'Luxeed (Chery/Huawei)': ('Китай','Chery + Huawei; код начинается на L.'),
 'Stelato (BAIC/Huawei)': ('Китай','BAIC + Huawei; код начинается на L.'),
 'Onvo (NIO)': ('Китай','NIO; код начинается на L.'),
 'HiPhi': ('Китай','Код начинается на L.'),
 'Roewe': ('Китай','SAIC; код начинается на L.'),
 'FAW': ('Китай','Код начинается на L.'),
 'MG': ('Китай','Современные MG производит SAIC в Китае; исторические — Великобритания.'),
 'Tesla': ('США / Китай','Версии для Европы и РФ — с завода во Фремонте (США, VIN с 1 или 5) или из Шанхая (Китай, LRW). US-версии — порт NACS, EU/CN — CCS2/GB/T.'),
 'Nissan': ('Япония','Leaf собирается в Японии; часть машин для РФ — сборка в Санкт-Петербурге до 2022 года.'),
 'Mitsubishi': ('Япония','Код начинается на J (Япония).'),
 'Kia': ('Корея / Россия','Заводы Кореи (код K) и калининградский «Автотор» (X). Рынок поставки уточняйте по 11-й позиции VIN.'),
 'Hyundai': ('Корея / Россия','Заводы Кореи (код K), Таганрог и Екатеринбург (X).'),
 'Genesis': ('Корея','Завод в Ульсане; код K.'),
 'VW': ('Германия / Россия','Заводы в Вольфсбурге и др. (код W); для РФ — Калуга (X) до 2022 года.'),
 'Skoda': ('Чехия / Россия','Заводы в Млада-Болеславе (код T); для РФ — Калуга и Нижний Новгород (X) до 2022 года.'),
 'Audi': ('Германия','Заводы в Ингольштадте и Неккарзульме; код W.'),
 'Mercedes': ('Германия','Заводы в Зиндельфингене и др.; код W.'),
 'BMW': ('Германия','Заводы в Мюнхене и Лейпциге (код W); для РФ — «Автотор», Калининград (X).'),
 'Evolute': ('Россия','Собран в Липецке на заводе «Моторинвест»; код X.'),
 'Moskvich': ('Россия','Собран в Москве (бывший завод Renault); код X.'),
 'Lotus': ('Англия / Китай','Классика — Хетел (Англия, S); электрические Eletre/Emeya — Ухань (Китай, L).'),
}

VIN_YEAR = [('A',2010),('B',2011),('C',2012),('D',2013),('E',2014),('F',2015),('G',2016),('H',2017),
            ('J',2018),('K',2019),('L',2020),('M',2021),('N',2022),('P',2023),('R',2024),('S',2025),('T',2026)]

VIN_STRUCT = '<h2>Как устроен VIN: 17 символов</h2><div class="tw"><table><tr><th>Позиции</th><th>Название</th><th>Что кодирует</th></tr>'
VIN_STRUCT += '<tr><td>1–3 (WMI)</td><td>Код завода-изготовителя</td><td>1-й символ — регион: <b>L</b> — Китай, <b>J</b> — Япония, <b>K</b> — Корея, <b>W</b> — Германия, <b>1/4/5</b> — США, <b>X</b> — Россия/СНГ, <b>S</b> — Великобритания, <b>T</b> — Чехия/Швейцария, <b>V</b> — Франция/Испания, <b>Z</b> — Италия, <b>Y</b> — Швеция/Финляндия.</td></tr>'
VIN_STRUCT += '<tr><td>4–9 (VDS)</td><td>Описание модели</td><td>Модель, двигатель, кузов. 9-я позиция — контрольная цифра (обязательна для машин американского рынка).</td></tr>'
VIN_STRUCT += '<tr><td>10</td><td>Модельный год</td><td>Код года — таблица ниже. Цикл повторяется каждые 30 лет.</td></tr>'
VIN_STRUCT += '<tr><td>11</td><td>Завод сборки</td><td>Буква/цифра конкретного завода.</td></tr>'
VIN_STRUCT += '<tr><td>12–17 (VIS)</td><td>Серийный номер</td><td>Порядковый номер машины.</td></tr></table></div>'
VIN_STRUCT += '<h2>Код модельного года (10-я позиция)</h2><div class="tw"><table><tr><th>Код</th><th>Год</th><th>Код</th><th>Год</th><th>Код</th><th>Год</th></tr>'
_vin_rows = ''
for _i in range(0, len(VIN_YEAR), 3):
    _trio = VIN_YEAR[_i:_i+3]
    _cells = ''.join('<td>'+c+'</td><td>'+str(y)+'</td>' for c,y in _trio)
    if len(_trio) < 3: _cells += '<td>—</td><td>—</td>'*(3-len(_trio))
    _vin_rows += '<tr>'+_cells+'</tr>'
VIN_STRUCT += _vin_rows + '</table></div>'
VIN_STRUCT += '<p class="note">Буквы I, O, Q, U, Z и цифра 0 в коде года не используются — чтобы не путать с 0, 1, 2 и V.</p>'
VIN_STRUCT += '<h2>Где искать VIN на электромобиле</h2><div class="card">'
VIN_STRUCT += '<p>У EV табличка с VIN обычно в тех же местах, что и у обычных машин:</p>'
VIN_STRUCT += '<p>• в нижнем углу <b>лобового стекла</b> со стороны водителя (виден снаружи);</p>'
VIN_STRUCT += '<p>• на <b>шильдике в проёме водительской двери</b> (B-стойка);</p>'
VIN_STRUCT += '<p>• в <b>документах</b>: ПТС, СТС, ЭПТС, договор купли-продажи, СБКТС.</p>'
VIN_STRUCT += '<p>У части китайских EV продублирован на наклейке в проёме лючка зарядки — удобно сверять при подключении адаптера.</p></div>'
VIN_STRUCT += '<h2>Проверка VIN перед покупкой (особенно параллельный импорт)</h2><div class="card">'
VIN_STRUCT += '<p><b>1. Сверьте VIN во всех местах.</b> VIN на кузове, на табличке и в документах должен совпадать посимвольно. Перебитый VIN — главная красная флаговая история.</p>'
VIN_STRUCT += '<p><b>2. Бесплатная проверка ГИБДД.</b> На сайте <a href="https://гибдд.рф/check/auto">гибдд.рф</a> по VIN бесплатно: история регистраций, ДТП, розыск, ограничения. Это первый шаг всегда.</p>'
VIN_STRUCT += '<p><b>3. ЭПТС и СБКТС.</b> У машин параллельного импорта (Zeekr, Li Auto, Avatr и др.) должен быть электронный ПТС и свидетельство о безопасности конструкции (СБКТС), оформленные на импортёра. Без СБКТС машину не поставят на учёт. Проверьте, что ЭПТС выпущен легально и на этот VIN.</p>'
VIN_STRUCT += '<p><b>4. Код года по 10-й позиции.</b> Сверьте с годом в ЭПТС: расхождение — повод задуматься о легальности ввоза или «омоложении» машины.</p>'
VIN_STRUCT += '<p><b>5. Расшифровка комплектации.</b> Точную расшифровку опций по VIN даёт дилер марки или официальный сервис по запросу — в интернет-справочниках встречаются ошибки.</p></div>'
VIN_STRUCT += '<p class="note">Справочник информационный: не юридическая консультация и не заменяет проверку по официальным базам.</p>'

def vin_brand_page(brand, outdir):
    country, note = VIN_BRANDS[brand]
    models_b = [m for m in MODELS if m['brand'].strip()==brand]
    top = sorted(models_b, key=lambda x: x['freq']!='Массовый')[:6]
    cards = ''.join('<a class="mcard" href="/models/'+slug(m['brand'])+'-'+slug(m['model'])+'.html"><b>'+html.escape(m['brand']+' '+m['model'])+'</b><span>'+html.escape(m['years']+' · '+m['type']+' · '+m['freq']+' ввоз')+'</span></a>' for m in top)
    parts = []
    parts.append('<a class="back" href="/vin/">← Все бренды VIN-справочника</a>')
    parts.append('<h1>VIN ' + html.escape(brand) + ': где табличка, код года и проверка истории</h1>')
    parts.append('<p class="lede">Код производителя, позиция модельного года и места расположения таблички у ' + html.escape(brand) + ', ввезённых в Россию.</p>')
    parts.append('<div class="card"><h3>Страна сборки и код завода</h3><p><span class="tag lime">' + html.escape(country) + '</span></p><p>' + html.escape(note) + '</p>')
    parts.append('<p class="note">Первый символ VIN соответствует региону производства: L — Китай, J — Япония, K — Корея, W — Германия, X — Россия/СНГ.</p></div>')
    parts.append(VIN_STRUCT)
    if cards:
        parts.append('<h2>Модели ' + html.escape(brand) + ' в нашей базе</h2><div class="grid2">' + cards + '</div>')
    parts.append('<h2>Что проверить по VIN ' + html.escape(brand) + ' перед покупкой</h2><div class="card">')
    parts.append('<p>Машины ' + html.escape(brand) + ' в РФ чаще всего ввезены по параллельному импорту или из Кореи — значит, ключевые проверки: совпадение VIN на кузове и в ЭПТС, наличие СБКТС, история ДТП по базе ГИБДД, код модельного года на 10-й позиции.</p>')
    parts.append('<p>Проверить историю бесплатно: <a href="https://гибдд.рф/check/auto">сервис ГИБДД по VIN</a>. Расшифровку комплектации — у дилера марки.</p></div>')
    parts.append('<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    sl = 'vin/'+slug(brand)+'.html'
    write_page(os.path.join(outdir, sl), 'VIN ' + brand + ': где табличка, код года, проверка истории — Запас хода',
        'Расшифровка VIN ' + brand + ' (' + country + '): код завода, модельный год на 10-й позиции, где находится табличка, бесплатная проверка ГИБДД и ЭПТС/СБКТС для параллельного импорта.',
        body, '/' + sl, og='/assets/og/vin-'+slug(brand)+'.png',
        crumbs=[('/vin/','VIN'),('',brand)])
    return sl

def model_page(m, outdir):
    grp = classify(m); ids = pains_for(m)
    pname = m['brand'] + ' ' + m['model']
    sl = 'models/' + slug(m['brand']) + '-' + slug(m['model']) + '.html'
    pain_html = ''.join(
        '<div class="card"><span class="pain-id">' + i + '</span><h3>' + html.escape(PAINS[i]["pain"]) + '</h3>'
        '<p class="note">Кому актуально: ' + html.escape(PAINS[i]["who"]) + '</p>'
        '<div class="sol"><b>Решение:</b> ' + html.escape(PAINS[i]["sol"]) + '</div>'
        '<p class="src">' + src_html(PAINS[i]) + '</p></div>' for i in ids)
    rows = ('<tr><td>AC (медленная)</td><td>' + html.escape(str(m.get("ac") or "—")) + '</td></tr>'
     '<tr><td>DC (быстрая)</td><td>' + html.escape(str(m.get("dc") or "—")) + '</td></tr>'
     '<tr><td>Бортовое зарядное (OBC)</td><td>' + html.escape(str(m.get("obc") or "—")) + '</td></tr>'
     '<tr><td>Мощность DC</td><td>' + html.escape(str(m.get("dcp") or "—")) + '</td></tr>'
     '<tr><td>Рынок вывоза</td><td>' + html.escape(str(m.get("market"))) + '</td></tr>')
    sol_block = html.escape(str(m['sol'])) if m.get('sol') else ''
    note = html.escape(str(m['note'])) if m.get('note') else ''
    srcrow = ('<p class="src">Источник спецификации: <a href="' + m["src"] + '">' + re.sub(r"^https?://(www\\.)?","",str(m["src"])) + '</a></p>') if m.get('src') and str(m['src']).startswith('http') else ''
    vin_link = ''
    if m['brand'].strip() in VIN_BRANDS:
        vin_link = ('<div class="card"><h3>VIN и история машины</h3><p>Владеете или выбираете с пробегом? Смотрите страницу '
          '<a href="/vin/'+slug(m['brand'])+'.html">VIN ' + html.escape(m['brand']) + '</a>: где табличка, код модельного года на 10-й позиции, '
          'бесплатная проверка ГИБДД и что проверить в ЭПТС/СБКТС у параллельного импорта.</p></div>')
    faq = ('<details class="faq"><summary>Каким разъёмом заряжается ' + html.escape(pname) + '?</summary>'
     '<p>AC: ' + html.escape(str(m.get("ac") or "—")) + '. DC: ' + html.escape(str(m.get("dc") or "—")) + '. Разъём зависит от рынка вывоза: ' + html.escape(str(m.get("market"))) + '.</p></details>'
     '<details class="faq"><summary>Можно ли зарядить ' + html.escape(pname) + ' от обычной розетки 220В?</summary>'
     '<p>Да, портативным зарядным устройством: обычная розетка даёт примерно 2,3–3,5 кВт. Паспортные «6–8 часов до 100%» относятся к станции 7 кВт — от розетки дольше. Нужны отдельная линия и автомат 32А.</p></details>'
     '<details class="faq"><summary>Какие типичные проблемы у ' + html.escape(pname) + '?</summary><p>Смотрите блок «Боли и решения» выше — собрано по отзывам владельцев и профильных сервисов, со ссылками на первоисточники.</p></details>')
    faq_ld = '<script type="application/ld+json">' + json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
          {"@type": "Question", "name": "Каким разъёмом заряжается " + pname + "?", "acceptedAnswer": {"@type": "Answer", "text": "AC: " + str(m.get('ac') or '—') + ". DC: " + str(m.get('dc') or '—') + ". Разъём зависит от рынка вывоза: " + str(m.get('market')) + "."}},
          {"@type": "Question", "name": "Можно ли зарядить " + pname + " от обычной розетки 220В?", "acceptedAnswer": {"@type": "Answer", "text": "Да, портативным зарядным устройством: розетка даёт 2,3–3,5 кВт. Нужны отдельная линия и автомат 32А; от розетки до 100% дольше, чем от станции 7 кВт."}},
          {"@type": "Question", "name": "Какие типичные проблемы у " + pname + "?", "acceptedAnswer": {"@type": "Answer", "text": "Смотрите раздел «Боли и решения»: типичные поломки и жизненные ситуации владельцев этой модели с решениями и ссылками на первоисточники."}}
        ]
    }, ensure_ascii=False) + '</script>'
    parts = []
    parts.append('<h1>' + html.escape(pname) + ': какой разъём зарядки, типичные проблемы и решения</h1>')
    parts.append('<p><span class="tag lime">' + m['years'] + '</span><span class="tag">' + m['type'] + '</span><span class="tag">' + grp + '</span><span class="tag">' + m['freq'] + ' ввоз</span></p>')
    parts.append('<p class="note">Важно: разъём зависит от рынка вывоза, а не от марки — проверяйте по фото лючка или VIN.</p>')
    parts.append('<h2>Разъёмы и мощность зарядки</h2><div class="tw"><table>' + rows + '</table></div>')
    parts.append(vin_link)
    if sol_block:
        parts.append('<div class="card"><h3>Что понадобится для зарядки</h3><p>' + sol_block + '</p></div>')
    if note:
        parts.append('<p class="note"><b>Примечание:</b> ' + note + '</p>')
    parts.append(srcrow)
    parts.append('<h2>Боли и решения для владельцев</h2>')
    parts.append(pain_html)
    parts.append(faq)
    parts.append(faq_ld)
    parts.append('<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    write_page(os.path.join(outdir, sl),
        pname + ' — какой разъём зарядки, типичные проблемы и решения | Запас хода',
        'Разъёмы AC/DC ' + pname + ' (' + m["years"] + '), зарядка от розетки и на станциях, реальные проблемы владельцев и проверенные решения. ' + grp + '-стандарт, ' + m["freq"] + ' ввоз в РФ.',
        body, '/' + sl, og='/assets/og/m-'+slug(m['brand'])+'-'+slug(m['model'])+'.png',
        crumbs=[('/index.html','Модели'),('',pname)])
    return sl

# ================= НОВОСТИ =================
def load_news(data_dir):
    ndir = os.path.join(data_dir, 'news')
    items = []
    if os.path.isdir(ndir):
        for fn in sorted(os.listdir(ndir)):
            if fn.endswith('.json'):
                try:
                    with open(os.path.join(ndir, fn), encoding='utf-8') as f:
                        it = json.load(f)
                    it['_file'] = fn
                    items.append(it)
                except Exception as e:
                    print('WARN news file:', fn, e)
    items.sort(key=lambda x: x.get('date',''), reverse=True)
    return items

def load_news_map(data_dir):
    p = os.path.join(data_dir, 'news_map.json')
    if os.path.exists(p):
        try:
            with open(p, encoding='utf-8') as f: return json.load(f)
        except Exception: pass
    return {}

def news_slug_page(it):
    return '/news/' + it['date'] + '-' + it['slug'] + '.html'

def month_ru(mn):
    return ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'][mn-1]

def fmt_date(d):
    try:
        y,m,dd = d.split('-'); return dd + ' ' + month_ru(int(m)) + ' ' + y
    except Exception: return d

def news_page(it, outdir, news_map):
    sl_file = it['date'] + '-' + it['slug'] + '.html'
    discuss = TG_CHANNEL
    mid = news_map.get(it['slug'])
    if mid: discuss = TG_CHANNEL + '/' + str(mid)
    parts = []
    parts.append('<a class="back" href="/news/">← Все новости</a>')
    parts.append('<h1>' + html.escape(it['title']) + '</h1>')
    parts.append('<p class="newsdate">' + fmt_date(it['date']) + ' · Запас хода</p>')
    parts.append(it['body'])
    rel_models = it.get('related') or []
    if rel_models:
        parts.append('<h2>Связанные страницы справочника</h2><p class="note">' + ', '.join(rel_models) + '</p>')
    parts.append('<hr class="sep">')
    parts.append('<div class="cta"><a class="btn lime" href="' + discuss + '">Обсудить в Telegram</a>'
     '<a class="btn ghost" href="' + TG_BOT_APP + '">Каталог аксессуаров</a>'
     '<a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>')
    body = ''.join(parts)
    write_page(os.path.join(outdir,'news',sl_file), it['title'] + ' | Запас хода',
        it.get('teaser') or it['title'], body, news_slug_page(it),
        og='/assets/og/n-'+it['date']+'-'+it['slug']+'.png',
        crumbs=[('/news/','Новости'),('',it['title'])])

def news_index(items, outdir):
    cards = ''
    for it in items:
        cards += ('<a class="newscard" href="' + news_slug_page(it) + '">'
          '<img src="/assets/og/n-' + it['date'] + '-' + it['slug'] + '.png" alt="" loading="lazy">'
          '<div class="inner"><span class="newsdate">' + fmt_date(it['date']) + '</span>'
          '<b>' + html.escape(it['title']) + '</b><span>' + html.escape(it.get('teaser') or '') + '</span></div></a>')
    body = ('<div class="hero"><div class="kicker">Лента</div><h1>Новости и разборы</h1>'
     '<p class="lede">Практика владения EV в России: цифры, зима, зарядка, новые модели. Коротко и по делу.</p>'
     '<input class="search" id="q" placeholder="Поиск по новостям: зима, адаптер, батарея…"></div>'
     '<div class="grid" id="nlist">' + cards + '</div>'
     '<script>document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase();'
     'document.querySelectorAll("#nlist .newscard").forEach(function(c){var t=(c.textContent||"").toLowerCase();'
     'c.style.display=t.indexOf(q)>=0?"":"none"});});</script>')
    write_page(os.path.join(outdir,'news','index.html'), 'Новости об электромобилях в России | Запас хода',
        'Лента: цифры, зима, зарядка, новые модели EV в России. Каждая новость — отдельная страница с разбором.', body, '/news/')

def news_feed(items, outdir):
    ch = ''
    for it in items:
        ch += ('<item><title>' + html.escape(it['title']) + '</title>'
         '<link>' + SITE_DOMAIN + news_slug_page(it) + '</link>'
         '<guid>' + SITE_DOMAIN + news_slug_page(it) + '</guid>'
         '<pubDate>' + it['date'] + 'T09:00:00+03:00</pubDate>'
         '<description>' + html.escape(it.get('teaser') or '') + '</description></item>')
    xml = ('<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel>'
     '<title>' + SITE_NAME + ' — новости EV в России</title><link>' + SITE_DOMAIN + '/news/</link>'
     '<description>Практика владения электромобилем в России: цифры, зима, зарядка, аксессуары</description><language>ru</language>' + ch + '</channel></rss>')
    with open(os.path.join(outdir,'feed.xml'),'w',encoding='utf-8') as f: f.write(xml)

# ================= КАРТА ЗАРЯДНЫХ СТАНЦИЙ =================
CITIES = [
 ('Москва','55.62,37.28,56.05,38.05'),('Санкт-Петербург','59.75,30.05,60.12,30.62'),
 ('Нижний Новгород','56.18,43.74,56.40,44.10'),('Екатеринбург','56.72,60.48,56.94,60.75'),
 ('Новосибирск','54.94,82.80,55.10,83.10'),('Казань','55.70,49.05,55.90,49.28'),
 ('Краснодар','44.95,38.88,45.10,39.08'),('Ростов-на-Дону','47.16,39.60,47.32,39.82'),
 ('Сочи','43.50,39.60,43.68,39.85'),('Владивосток','43.05,131.80,43.24,132.05'),
 ('Симферополь','44.88,34.05,45.00,34.20'),('Минск','53.82,27.44,53.98,27.66'),
 ('Алматы','43.17,76.80,43.32,76.99')]

def map_page(outdir):
    city_btns = ''.join('<button class="cbtn" data-bbox="' + bb + '">' + c + '</button>' for c,bb in CITIES)
    body = ('<div class="hero"><div class="kicker">Карта</div><h1>Зарядные станции рядом</h1>'
     '<p class="lede">Живая карта зарядной инфраструктуры по данным OpenStreetMap. Выберите город — покажем станции, операторов и разъёмы.</p></div>'
     '<div class="cbtns">' + city_btns + '</div>'
     '<div id="map" class="nmap"></div>'
     '<p class="note" id="mstat">Загрузка данных…</p>'
     '<h2>Как пользоваться картой</h2>'
     '<div class="card"><p>Данные — открытая база OpenStreetMap: зарядки размечают сами пользователи, покрытие в мегаполисах хорошее, в малых городах — частичное. '
     'Станция кликабельна: покажет оператора и типы разъёмов, если они указаны в данных.</p>'
     '<p class="note">Не видите станцию, которая есть в реальности? Её можно добавить в OSM за пару минут — база открытая.</p></div>'
     '<p class="note">Данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL). Запросы через Overpass API.</p>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/pains.html">Проблемы и решения</a></div>'
     '<link rel="stylesheet" href="/assets/leaflet/leaflet.css">'
     '<script src="/assets/leaflet/leaflet.js"></script>'
     '<script>'
     'var map=L.map("map").setView([55.75,37.6],10);'
     'L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);'
     'var markers=[];'
     'function clearM(){markers.forEach(function(m){map.removeLayer(m)});markers=[];}var OV_HOSTS=["https://maps.mail.ru/osm/tools/overpass/api/interpreter","https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"];function fetchOverpass(q){var chain=Promise.reject();OV_HOSTS.forEach(function(h){chain=chain.catch(function(){return fetch(h,{method:"POST",body:"data="+encodeURIComponent(q)}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json()});});});return chain;}'
     'function loadBbox(bbox){var p=bbox.split(",");clearM();document.getElementById("mstat").textContent="Загрузка…";'
     'map.fitBounds([[p[0],p[1]],[p[2],p[3]]]);'
     'var q="[out:json][timeout:25];node[amenity=charging_station]("+bbox+");out tags center 400;";'
     'fetchOverpass(q)'
     '.then(function(r){return r.json()})'
     '.then(function(d){var els=d.elements||[];els.forEach(function(e){var la=e.lat,lo=e.lon;if(!la&&e.center){la=e.center.lat;lo=e.center.lon}if(la==null)return;'
     'var t=e.tags||{};var nm=t.operator||t.name||"Зарядная станция";var sk=[];for(var k in t){if(k.indexOf("socket:")===0&&t[k]!=="no")sk.push(k.replace("socket:",""))}'
     'var txt="<b>"+nm+"</b>"+(sk.length?"<br>Разъёмы: "+sk.join(", "):"");'
     'var m=L.marker([la,lo]).addTo(map).bindPopup(txt);markers.push(m);});'
     'document.getElementById("mstat").textContent=els.length?("Найдено станций: "+els.length):("В этой области OpenStreetMap пока нет размеченных зарядок — добавьте их, это открытая база");})'
     '.catch(function(){document.getElementById("mstat").textContent="Не удалось загрузить станции — попробуйте ещё раз через минуту";});}'
     'document.querySelectorAll(".cbtn").forEach(function(b){b.addEventListener("click",function(){loadBbox(b.dataset.bbox)})});'
     'loadBbox("' + CITIES[0][1] + '");'
     '</script>')
    write_page(os.path.join(outdir,'charging','index.html'), 'Карта зарядных станций для электромобилей | Запас хода',
        'Живая карта зарядных станций по данным OpenStreetMap: Москва, Санкт-Петербург, Екатеринбург, Казань и другие города. Операторы и разъёмы.',
        body, '/charging/', crumbs=[('', 'Карта ЗУ')])

def map_page(outdir):
    city_btns = ''.join('<button class="cbtn" data-bbox="' + bb + '">' + c + '</button>' for c,bb in CITIES)
    body = ('<div class="hero"><div class="kicker">Карта</div><h1>Зарядные станции рядом</h1>'
     '<p class="lede">Живая карта зарядной инфраструктуры по данным OpenStreetMap. Выберите город — покажем станции, операторов и разъёмы.</p></div>'
     '<div class="cbtns">' + city_btns + '</div>'
     '<div id="map" class="nmap"></div>'
     '<p class="note" id="mstat">Загрузка данных…</p>'
     '<h2>Как пользоваться картой</h2>'
     '<div class="card"><p>Данные — открытая база OpenStreetMap: зарядки размечают сами пользователи, покрытие в мегаполисах хорошее, в малых городах — частичное. '
     'Станция кликабельна: покажет оператора и типы разъёмов, если они указаны в данных.</p>'
     '<p class="note">Не видите станцию, которая есть в реальности? Её можно добавить в OSM за пару минут — база открытая.</p></div>'
     '<p class="note">Данные © участники <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (ODbL). Запросы через Overpass API.</p>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/pains.html">Проблемы и решения</a></div>'
     '<link rel="stylesheet" href="/assets/leaflet/leaflet.css">'
     '<script src="/assets/leaflet/leaflet.js"></script>'
     '<script>'
     'var map=L.map("map").setView([55.75,37.6],10);'
     'L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"© OpenStreetMap"}).addTo(map);'
     'var markers=[];'
     'function clearM(){markers.forEach(function(m){map.removeLayer(m)});markers=[];}var OV_HOSTS=["https://maps.mail.ru/osm/tools/overpass/api/interpreter","https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"];function fetchOverpass(q){var chain=Promise.reject();OV_HOSTS.forEach(function(h){chain=chain.catch(function(){return fetch(h,{method:"POST",body:"data="+encodeURIComponent(q)}).then(function(r){if(!r.ok)throw new Error("http "+r.status);return r.json()});});});return chain;}'
     'function loadBbox(bbox){var p=bbox.split(",");clearM();document.getElementById("mstat").textContent="Загрузка…";'
     'map.fitBounds([[p[0],p[1]],[p[2],p[3]]]);'
     'var q="[out:json][timeout:25];node[amenity=charging_station]("+bbox+");out tags center 400;";'
     'fetchOverpass(q)'
     '.then(function(r){return r.json()})'
     '.then(function(d){var els=d.elements||[];els.forEach(function(e){var la=e.lat,lo=e.lon;if(!la&&e.center){la=e.center.lat;lo=e.center.lon}if(la==null)return;'
     'var t=e.tags||{};var nm=t.operator||t.name||"Зарядная станция";var sk=[];for(var k in t){if(k.indexOf("socket:")===0&&t[k]!=="no")sk.push(k.replace("socket:",""))}'
     'var txt="<b>"+nm+"</b>"+(sk.length?"<br>Разъёмы: "+sk.join(", "):"");'
     'var m=L.marker([la,lo]).addTo(map).bindPopup(txt);markers.push(m);});'
     'document.getElementById("mstat").textContent=els.length?("Найдено станций: "+els.length):("В этой области OpenStreetMap пока нет размеченных зарядок — добавьте их, это открытая база");})'
     '.catch(function(){document.getElementById("mstat").textContent="Не удалось загрузить станции — попробуйте ещё раз через минуту";});}'
     'document.querySelectorAll(".cbtn").forEach(function(b){b.addEventListener("click",function(){loadBbox(b.dataset.bbox)})});'
     'loadBbox("' + CITIES[0][1] + '");'
     '</script>')
    write_page(os.path.join(outdir,'charging','index.html'), 'Карта зарядных станций для электромобилей | Запас хода',
        'Живая карта зарядных станций по данным OpenStreetMap: Москва, Санкт-Петербург, Екатеринбург, Казань и другие города. Операторы и разъёмы.',
        body, '/charging/', crumbs=[('', 'Карта ЗУ')])

# ================= ПОИСК =================
def search_page(outdir, index_items):
    js = json.dumps(index_items, ensure_ascii=False)
    body = ('<div class="hero"><div class="kicker">Поиск</div><h1>Поиск по справочнику</h1>'
     '<p class="lede">Модели, проблемы, новости и VIN — всё в одном поиске.</p></div>'
     '<input class="search" id="q" placeholder="Например: Zeekr, адаптер, зимой, VIN…">'
     '<div id="res"></div>'
     '<script>var IDX=' + js + ';'
     'document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase().trim();var out="";'
     'if(q){var hits=IDX.filter(function(x){return (x.t+" "+x.d).toLowerCase().indexOf(q)>=0}).slice(0,40);'
     'out=hits.map(function(x){return "<a class=mcard href="+x.u+"><b>"+x.t+"</b><span>"+x.d+"</span></a>"}).join("");'
     'if(!hits.length)out="<p class=note>Ничего не нашлось. Попробуйте другое слово.</p>";}'
     'document.getElementById("res").innerHTML=out;});</script>')
    write_page(os.path.join(outdir,'search.html'), 'Поиск | Запас хода',
        'Поиск по 137 моделям, руководствам, новостям и VIN-справочнику.', body, '/search.html')

# ================= LLMS.TXT =================
def llms_files(outdir, news):
    canon = [
      ('Каталог моделей', '/index.html', '137 моделей EV в РФ: разъёмы, мощности, боли, решения'),
      ('Руководства по проблемам', '/pains.html', '12 практических руководств с решениями'),
      ('Новости', '/news/', 'Лента: цифры, зима, зарядка, новые модели'),
      ('Карта зарядных станций', '/charging/', 'Зарядные станции по данным OpenStreetMap'),
      ('VIN-справочник', '/vin/', 'Структура VIN, коды года, проверка истории для EV в РФ'),
      ('О проекте', '/about.html', 'Методика и источники справочника'),
    ]
    txt = '# ' + SITE_NAME + '\n\n> Практика владения электромобилем в России: разъёмы зарядки (GB/T, Type 2/CCS2, Type 1/CCS1, CHAdeMO), зимняя эксплуатация, реальные расходы, VIN-проверка параллельного импорта. База: 137 моделей 2019–2026, ввезённых в РФ. Мини-приложение с каталогом аксессуаров: https://t.me/zapashoda_ev_bot/app\n\n'
    txt += '## Разделы\n\n'
    for t,u,d in canon: txt += '- [' + t + '](' + SITE_DOMAIN + u + '): ' + d + '\n'
    txt += '\n## Популярные модели\n\n'
    pop = ['Zeekr 001','Zeekr 007','Zeekr 7X','Li Auto L6','Voyah Free','Avatr 11','Xiaomi SU7','BYD Song Plus EV','BYD Yuan Plus','Geely EX5','Geely Galaxy E5','Deepal S07','Evolute i-Jet','Moskvich 3e','Tesla Model 3','VW ID.3','BMW i4','Nissan Leaf']
    seen = set()
    for pn in pop:
        hit = [m for m in MODELS if pn.lower() in (m['brand']+' '+m['model']).lower()]
        if hit and hit[0]['model'] not in seen:
            m = hit[0]; seen.add(m['model'])
            txt += '- [' + m['brand'] + ' ' + m['model'] + '](' + SITE_DOMAIN + '/models/' + slug(m['brand']) + '-' + slug(m['model']) + '.html): разъёмы ' + str(m.get('ac') or '?') + ' / ' + str(m.get('dc') or '?') + '\n'
    txt += '\n## Руководства по проблемам\n\n'
    for sl,t,d,_ in PAIN_ARTICLES: txt += '- [' + t + '](' + SITE_DOMAIN + '/pain/' + sl + '.html): ' + d + '\n'
    if news:
        txt += '\n## Свежие новости\n\n'
        for it in news[:20]: txt += '- [' + it['title'] + '](' + SITE_DOMAIN + news_slug_page(it) + '): ' + (it.get('teaser') or '') + '\n'
    with open(os.path.join(outdir,'llms.txt'),'w',encoding='utf-8') as f: f.write(txt)

    full = txt + '\n\n# ПОЛНЫЙ ТЕКСТ РУКОВОДСТВ\n\n'
    for sl,t,d,pids in PAIN_ARTICLES:
        full += '## ' + t + '\n\n' + d + '\n\n'
        for i in pids:
            p = PAINS[i]
            full += '### ' + p['pain'] + ' [' + i + ']\nКому: ' + p['who'] + '\nРешение: ' + p['sol'] + '\n' + src_html(p).replace('<a href="','( ').replace('</a>',' )').replace('Источники: ','Источники: ') + '\n\n'
    full += '# МОДЕЛИ: РАЗЪЁМЫ\n\n'
    for m in MODELS:
        full += '## ' + m['brand'] + ' ' + m['model'] + ' (' + m['years'] + ', ' + m['type'] + ', ' + m['market'] + ')\n'
        full += 'AC: ' + str(m.get('ac') or '—') + ' | DC: ' + str(m.get('dc') or '—') + ' | OBC: ' + str(m.get('obc') or '—') + ' | DC-мощность: ' + str(m.get('dcp') or '—') + '\n'
        if m.get('sol'): full += 'Для зарядки: ' + str(m['sol']) + '\n'
        full += '\n'
    if news:
        full += '# НОВОСТИ\n\n'
        for it in news:
            full += '## ' + it['title'] + ' (' + it['date'] + ')\n' + (it.get('teaser') or '') + '\n\n' + it['body'].replace('</p><p>','\n\n').replace('<p>','').replace('</p>','') + '\n\n'
    with open(os.path.join(outdir,'llms-full.txt'),'w',encoding='utf-8') as f: f.write(full)

# ================= OG-КАРТОЧКИ (PIL) =================
def og_gen(outdir, jobs):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print('PIL недоступен — OG-карточки пропущены'); return
    here = os.path.dirname(os.path.abspath(__file__))
    fb = os.path.join(here, 'assets', 'fonts', 'DejaVuSans-Bold.ttf')
    if not os.path.exists(fb):
        fb = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    if not os.path.exists(fb):
        print('Шрифт не найден — OG пропущены'); return
    f_big = ImageFont.truetype(fb, 62); f_small = ImageFont.truetype(fb, 30); f_url = ImageFont.truetype(fb, 26)
    ogdir = os.path.join(outdir, 'assets', 'og')
    os.makedirs(ogdir, exist_ok=True)
    LIME = (245, 245, 247); DARK = (29, 29, 31); MUT = (142, 142, 147); DEC = (214, 214, 222)
    for rel, title in jobs:
        img = Image.new('RGB', (1200, 630), LIME)
        dr = ImageDraw.Draw(img)
        dr.polygon([(1060, 60), (940, 230), (1020, 230), (970, 400), (1120, 190), (1030, 190), (1090, 60)], fill=DEC)
        words = title.split()
        lines = []; cur = ''
        for w in words:
            t = (cur + ' ' + w).strip()
            if dr.textlength(t, font=f_big) > 1020 and cur:
                lines.append(cur); cur = w
            else:
                cur = t
        if cur: lines.append(cur)
        lines = lines[:4]
        y = 250
        for ln in lines:
            dr.text((60, y), ln, font=f_big, fill=DARK); y += 74
        dr.text((60, 520), 'ЗАПАС ХОДА · ПРАКТИКА EV В РОССИИ', font=f_small, fill=DARK)
        dr.text((60, 566), SITE_DOMAIN.replace('https://','').replace('http://',''), font=f_url, fill=MUT)
        p = os.path.join(outdir, rel.lstrip('/'))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        img.save(p, 'PNG', optimize=True)
    print('OG-карточек:', len(jobs))

# ================= ГЛАВНАЯ, ПРОЧИЕ, SITEMAP =================
def home_page(outdir):
    art_cards = ''.join('<a class="mcard" href="/pain/'+sl+'.html"><b>'+html.escape(title)+'</b><span>'+html.escape(desc)+'</span></a>' for sl,title,desc,pids in PAIN_ARTICLES)
    pop_names = ['Zeekr 001','Zeekr 007','Zeekr 7X','Li Auto L6','Voyah Free','Avatr 11','Xiaomi SU7','Changan Qiyuan A05','BYD Song Plus EV','BYD Yuan Plus','Geely EX5','Geely Galaxy E5','Deepal S07','Evolute i-Jet','Moskvich 3e','Tesla Model 3','VW ID.3','BMW i4','Nissan Leaf']
    pop_cards = ''
    for pn in pop_names:
        hit = [m for m in MODELS if pn.lower() in (m['brand']+' '+m['model']).lower()]
        if hit:
            m = hit[0]
            pop_cards += '<a class="mcard" href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html"><b>'+html.escape(m["brand"]+" "+m["model"])+'</b><span>'+m["years"]+' · '+m["type"]+' · '+m["freq"]+' ввоз</span></a>'
    model_cards = ''.join('<a class="mcard" href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html"><b>'+html.escape(m["brand"]+" "+m["model"])+'</b><span>'+m["years"]+' · '+m["type"]+' · '+m["freq"]+' ввоз</span></a>' for m in sorted(MODELS, key=lambda x:(x['freq']!='Массовый', x['brand'], x['model'])))
    body = ('<div class="hero"><div class="kicker">Справочник</div>'
     '<h1>Как зарядить и чем лечить ваш электромобиль</h1>'
     '<p class="lede">Разъёмы, реальные проблемы и проверенные решения для 137 моделей, ввезённых в Россию в 2019–2026: GB/T, Type 2/CCS2, Type 1/CCS1, CHAdeMO.</p>'
     '<div class="ctas"><a class="btn lime" href="' + TG_BOT_APP + '">Открыть каталог аксессуаров</a><a class="btn ghost" href="/news/">Читать новости</a></div></div>'
     '<input class="search" id="q" placeholder="Начните вводить марку или модель: Zeekr, BYD, Leaf…">'
     '<h2>Частые проблемы — быстрые ответы</h2><div class="grid">' + art_cards + '</div>'
     '<h2>Популярные модели</h2><p class="note">Разъёмы, мощность и решения по самым массовым машинам в РФ.</p><div class="grid">' + pop_cards + '</div>'
     '<h2 id="models-list">Все модели</h2><div class="grid">' + model_cards + '</div>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Каталог в мини-приложении</a><a class="btn ghost" href="' + TG_CHANNEL + '">Канал «Запас хода»</a><a class="btn ghost" href="/charging/">Карта зарядных станций</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>'
     '<script>document.getElementById("q").addEventListener("input",function(){var q=this.value.toLowerCase();'
     'document.querySelectorAll(".grid .mcard").forEach(function(c){c.style.display=c.textContent.toLowerCase().indexOf(q)>=0?"":"none"});});</script>')
    write_page(os.path.join(outdir,'index.html'), 'Запас хода — разъёмы зарядки, боли и решения для 137 моделей EV в России',
        'Справочник: какой разъём зарядки у Zeekr, BYD, Voyah, Li Auto, Leaf и 130+ других моделей, типичные проблемы владельцев и решения, карта ЗУ и VIN-проверка.',
        body, '/')

def pains_index(outdir):
    arts = ''.join('<a class="mcard" href="/pain/'+sl+'.html"><b>'+title+'</b><span>'+desc+'</span></a>' for sl,title,desc,pids in PAIN_ARTICLES)
    write_page(os.path.join(outdir,'pains.html'), 'Проблемы и решения электромобилей | Запас хода',
        'Не заряжается, подогрев батареи, зарядка от розетки, адаптеры GB/T и CCS2, кабель не отдаёт, 12В АКБ, CHAdeMO — решения с источниками.',
        '<h1>Типичные проблемы электромобилей и их решения</h1><p class="lede">Руководства по самым частым болям владельцев — со ссылками на первоисточники.</p><div class="grid">'+arts+'</div>', '/pains.html')

def pain_article_page(sl, title, desc, pids, outdir):
    rel_html = ', '.join('<a href="/models/'+slug(m["brand"])+'-'+slug(m["model"])+'.html">'+html.escape(m["brand"]+" "+m["model"])+'</a>' for m in rel_models(RELATED.get(sl,[])))
    blocks = ''.join('<div class="card"><span class="pain-id">'+i+'</span><h3>'+html.escape(PAINS[i]["pain"])+'</h3><div class="sol"><b>Решение:</b> '+html.escape(PAINS[i]["sol"])+'</div><p class="src">'+src_html(PAINS[i])+'</p></div>' for i in pids)
    body = '<h1>'+title+'</h1><p class="lede">'+desc+'</p>'+blocks+'<h2>Связанные модели</h2><p class="note">Разъёмы и боли конкретных моделей: '+rel_html+'. Полный каталог — <a href="/index.html">по ссылке</a>.</p><div class="cta"><a class="btn lime" href="'+TG_BOT_APP+'">Подобрать комплект</a><a class="btn ghost" href="'+TG_CHANNEL+'">Канал «Запас хода»</a><a class="btn ghost share" href="#" onclick="sharePg();return false;">Поделиться</a></div>'
    write_page(os.path.join(outdir,'pain', sl+'.html'), title+' | Запас хода', 'Практическое руководство: '+desc, body, '/pain/'+sl+'.html', crumbs=[('/pains.html','Проблемы'),('',title)])

def rel_models(rel_brands):
    out = []
    for b in rel_brands:
        ms = [m for m in MODELS if m['brand'].strip()==b and m['freq']=='Массовый'] or [m for m in MODELS if m['brand'].strip()==b]
        for m in ms[:1]: out.append(m)
    return out[:4]

def about_page(outdir, news):
    n = len(news)
    write_page(os.path.join(outdir,'about.html'), 'О проекте «Запас хода»', 'Как устроен справочник владения электромобилем: источники, методика, кто делает.',
        '<h1>О проекте</h1><p class="lede">«Запас хода» — независимый справочник по практике владения электромобилем в России.</p>'
        '<p>База: 137 моделей с типами подключения, реальные боли владельцев с форумов (Drive2, chinamobil, клубы брендов) и профильных сервисов. Каждое решение снабжено ссылкой на первоисточник. Карта зарядных станций — данные OpenStreetMap (ODbL).</p>'
        '<p>Также у нас: Telegram-канал <a href="'+TG_CHANNEL+'">@zapashoda_ev</a> и мини-приложение с каталогом аксессуаров (<a href="'+TG_BOT_APP+'">открыть</a>). Новостей в ленте на момент сборки: '+str(n)+'.</p>'
        '<p class="note">Проект ведёт поставщик зарядных комплектов для китайских и европейских EV: подбор, доставка по РФ, консультация.</p>', '/about.html')

def vin_hub(outdir):
    pop_first = ['Zeekr','Li Auto','BYD','Voyah','Avatr','Tesla','VW','BMW','Kia','Hyundai','Nissan','Xiaomi','Geely','Hongqi','Evolute','Moskvich','Audi','Mercedes','Skoda','MG']
    brands = sorted(VIN_BRANDS, key=lambda b: pop_first.index(b) if b in pop_first else 999)
    cards = ''.join('<a class="mcard" href="/vin/'+slug(b)+'.html"><b>VIN '+html.escape(b)+'</b><span>'+html.escape(VIN_BRANDS[b][0])+' · код года, табличка, проверка</span></a>' for b in brands)
    body = ('<div class="hero"><div class="kicker">VIN-справочник</div><h1>VIN электромобиля: расшифровка и проверка</h1>'
     '<p class="lede">17 символов, которые говорят о машине всё: код завода, модельный год, серийник. Для владельцев EV в России — с акцентом на параллельный импорт.</p></div>'
     + VIN_STRUCT +
     '<h2>VIN по брендам</h2><div class="grid2">' + cards + '</div>'
     '<div class="cta"><a class="btn lime" href="' + TG_BOT_APP + '">Подобрать комплект зарядки</a><a class="btn ghost" href="/news/">Новости</a></div>')
    write_page(os.path.join(outdir,'vin','index.html'), 'VIN-справочник электромобилей: расшифровка, код года, проверка | Запас хода',
        'Как расшифровать VIN электромобиля: структура, коды модельного года, где находится табличка, бесплатная проверка ГИБДД и ЭПТС/СБКТС для параллельного импорта.',
        body, '/vin/')

def misc_pages(outdir):
    with open(os.path.join(outdir,'robots.txt'),'w',encoding='utf-8') as f:
        f.write('User-agent: *\nAllow: /\nSitemap: '+SITE_DOMAIN+'/sitemap.xml\n')
    with open(os.path.join(outdir,'.nojekyll'),'w') as f: f.write('')
    body = '<h1>Страница не найдена</h1><p class="lede">Такой страницы нет — возможно, ссылка устарела.</p><div class="cta"><a class="btn lime" href="/index.html">На главную</a><a class="btn ghost" href="/news/">Новости</a></div>'
    write_page(os.path.join(outdir,'404.html'), '404 — страница не найдена | Запас хода', 'Страница не найдена.', body, '/404.html')

def build_sitemap(slugs_model, news, vin_slugs):
    urls = [SITE_DOMAIN+'/', SITE_DOMAIN+'/pains.html', SITE_DOMAIN+'/about.html', SITE_DOMAIN+'/news/',
            SITE_DOMAIN+'/charging/', SITE_DOMAIN+'/vin/', SITE_DOMAIN+'/search.html']
    urls += [SITE_DOMAIN+'/'+s.replace('.html','') for s in slugs_model]
    urls += [SITE_DOMAIN+'/pain/'+s+'.html' for s,_,_,_ in PAIN_ARTICLES]
    urls += [SITE_DOMAIN+news_slug_page(it) for it in news]
    urls += [SITE_DOMAIN+'/'+s.replace('.html','') for s in vin_slugs]
    return '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join('<url><loc>'+u+'</loc></url>' for u in urls) + '</urlset>'

def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else '_site'
    repo_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(repo_root, 'data')
    os.makedirs(outdir, exist_ok=True)
    os.makedirs(os.path.join(outdir,'assets'), exist_ok=True)
    LOGO = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1d1d1f"/><path d="M37 8 L16 38 h14 l-5 18 25-34 H34 l8-14 z" fill="#ffffff"/></svg>'
    with open(os.path.join(outdir,'assets','logo.svg'),'w',encoding='utf-8') as f: f.write(LOGO)
    with open(os.path.join(outdir,'style.css'),'w',encoding='utf-8') as f: f.write(CSS)
    # leaflet
    lf = os.path.join(repo_root,'static','leaflet')
    if os.path.isdir(lf):
        dst = os.path.join(outdir,'assets','leaflet')
        if os.path.isdir(dst): shutil.rmtree(dst)
        shutil.copytree(lf, dst)
    news = load_news(data_dir)
    news_map = load_news_map(data_dir)
    print('Новостей в базе:', len(news))
    home_page(outdir)
    pains_index(outdir)
    slugs = [model_page(m, outdir) for m in MODELS]
    for sl,title,desc,pids in PAIN_ARTICLES:
        pain_article_page(sl,title,desc,pids,outdir)
    for it in news:
        news_page(it, outdir, news_map)
    news_index(news, outdir)
    news_feed(news, outdir)
    vin_slugs = []
    for brand in sorted(VIN_BRANDS):
        if brand in [m['brand'].strip() for m in MODELS] or True:
            vin_slugs.append(vin_brand_page(brand, outdir))
    vin_hub(outdir)
    map_page(outdir)
    idx = []
    for m in MODELS:
        idx.append({'t': m['brand']+' '+m['model'], 'd': 'Разъёмы: '+str(m.get('ac') or '—')+' / '+str(m.get('dc') or '—')+' · '+m['type']+' · '+m['market'], 'u': '/models/'+slug(m['brand'])+'-'+slug(m['model'])+'.html'})
    for sl,title,desc,_ in PAIN_ARTICLES:
        idx.append({'t': title, 'd': desc, 'u': '/pain/'+sl+'.html'})
    for it in news:
        idx.append({'t': it['title'], 'd': it.get('teaser') or '', 'u': news_slug_page(it)})
    for brand in VIN_BRANDS:
        idx.append({'t': 'VIN '+brand, 'd': 'Расшифровка VIN, код года, проверка истории ('+VIN_BRANDS[brand][0]+')', 'u': '/vin/'+slug(brand)+'.html'})
    for t,u,d in [('/', 'Запас хода', 'Справочник по зарядке EV в России'), ('/charging/','Карта зарядных станций','ЗУ по данным OSM'), ('/pains.html','Проблемы и решения','12 руководств')]:
        idx.append({'t': t, 'd': d, 'u': u})
    search_page(outdir, idx)
    llms_files(outdir, news)
    about_page(outdir, news)
    misc_pages(outdir)
    # OG-карточки: новости + бренды VIN + дефолт
    jobs = [('/assets/og/default.png', 'Запас хода — практика владения электромобилем в России')]
    for it in news:
        jobs.append(('/assets/og/n-'+it['date']+'-'+it['slug']+'.png', it['title']))
    for brand in VIN_BRANDS:
        jobs.append(('/assets/og/vin-'+slug(brand)+'.png', 'VIN '+brand+': расшифровка и проверка истории'))
    for sl,title,_,_ in PAIN_ARTICLES:
        jobs.append(('/assets/og/p-'+sl+'.png', title))
    og_gen(outdir, jobs)
    # OG для моделей (137) — упрощённые (заголовок покороче)
    for m in MODELS:
        jobs.append(('/assets/og/m-'+slug(m['brand'])+'-'+slug(m['model'])+'.png', m['brand']+' '+m['model']+' — разъёмы зарядки'))
    og_gen(outdir, jobs)
    with open(os.path.join(outdir,'sitemap.xml'),'w',encoding='utf-8') as f: f.write(build_sitemap(slugs, news, vin_slugs))
    total = sum(len(fs) for _,_,fs in os.walk(outdir))
    print('Готово: моделей', len(slugs), '| новостей', len(news), '| VIN-страниц', len(vin_slugs), '| файлов в _site:', total)

if __name__ == '__main__':
    main()
