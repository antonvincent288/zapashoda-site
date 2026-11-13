// (13.11) Перелинковка «модели ↔ каталог ↔ статьи» — серверные блоки.
//  1) buyKitHtml: «Базовый комплект зарядки для [Модель]» на страницах моделей
//     (+ через ModelBuyBlock в конце статей/compare/partner/sovmestimost).
//  2) insetHtml/injectIntoArticle: нативные врезки «Инженерное решение» в статьях
//     (трасса/дом/зима — подбор по слагу, без слов «акция/скидка»).
//  3) Калькулятор стоимости — статический CTA на карточку станции (cost/index.astro).
import { priceOut } from './prices';
import SKU from '../data/sku.json';

const SKU_BY: Record<string, any> = {};
for (const it of ((SKU as any).items || [])) SKU_BY[String(it.slug)] = it;

function esc(s: string): string {
  return String(s || '').replace(/[&<>"]/g, (c: string) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string));
}
function cardUrl(skuSlug: string, modelSlug: string): string {
  return '/catalog/' + skuSlug + '.html' + (modelSlug ? ('?model=' + encodeURIComponent(modelSlug)) : '');
}
function normPort(port: any, name?: string, slug?: string): string {
  const nm = String(name || ''), sl = String(slug || '');
  if (/tesla/i.test(nm) && /-us\b/.test(sl)) return 'nacs';
  const s = String(port || '').toLowerCase();
  if (s.includes('nacs')) return 'nacs';
  if (s.includes('gb/t')) return 'gbt';
  if (s.includes('chademo')) return 'chademo';
  if (s.includes('type1') || s.includes('ccs1')) return 'type1';
  return 'type2';
}
const PORT_LABEL: Record<string, string> = {
  gbt: 'GB/T (Zeekr, Li Auto, Voyah, BYD)',
  type2: 'Type 2 / CCS2 (Evolute, VW, Tesla EU)',
  nacs: 'Tesla NACS (США)',
  type1: 'Type 1 (J1772)',
  chademo: 'CHAdeMO',
};
function kitFor(port: string): string[] {
  if (port === 'gbt') return ['adapter-ccs2-gbt-dc', 'kabel-type2-gbt-7m-22kw', 'smazka-silikonom-zima'];
  if (port === 'nacs') return ['adapter-nacs-ccs2-type2'];
  if (port === 'type1') return ['adapter-type1-type2', 'portativnaya-zaryadka-type2-3-5kw', 'smazka-silikonom-zima'];
  if (port === 'chademo') return [];
  return ['kabel-type2-type2-5m-22kw', 'portativnaya-zaryadka-type2-7kw', 'smazka-silikonom-zima'];
}
export function buyKitHtml(model: any): string {
  const name = String((model && (model.name || model.title)) || '').trim();
  const mslug = String((model && model.slug) || '');
  const port = normPort(model && model.port, name, mslug);
  const head = name ? ('Базовый комплект зарядки для ' + esc(name)) : 'Самое ходовое из каталога';
  const sub = name ? ('подобрано по разъёму: ' + esc(PORT_LABEL[port] || '') + ' · оплата у дилера при получении') : 'по портам GB/T и Type 2 · оплата у дилера при получении';
  const slugs = kitFor(port);
  if (!slugs.length) {
    return '<section class="kitblock" style="margin-top:22px;padding:20px 22px;background:var(--card);border:1px solid var(--line);border-radius:18px"><h2 style="margin:0 0 8px;font-size:20px">' + head + '</h2><p style="margin:0;font-size:14.5px;color:var(--txt-muted)">Разъём CHAdeMO: станции редки, готового комплекта нет — подберём по VIN в Telegram @zapashoda_ev_bot.</p></section>';
  }
  const cards = slugs.map((s) => {
    const it = SKU_BY[s] || {};
    return '<a class="kit-card" href="' + cardUrl(s, mslug) + '" style="display:flex;flex-direction:column;gap:8px;padding:16px;border:1px solid var(--line);border-radius:14px;background:var(--bg);text-decoration:none;color:var(--txt)">' +
      '<span style="font-size:14.5px;font-weight:600;line-height:1.35">' + esc(String(it.title || s)) + '</span>' +
      '<span style="font-size:16px;font-weight:800;color:var(--gold)">' + esc(priceOut(it.price)) + '</span>' +
      '<span style="font-size:12.5px;color:var(--txt-muted)">Цена фиксируется при бронировании</span></a>';
  }).join('');
  const note = port === 'nacs'
    ? '<div class="kit-note" style="margin-top:12px;font-size:13.5px;color:var(--txt-muted)">Для US-Tesla остальной набор подбирается по VIN — напишите в Telegram @zapashoda_ev_bot.</div>'
    : '';
  return '<section class="kitblock" style="margin-top:22px;padding:20px 22px;background:var(--card);border:1px solid var(--line);border-radius:18px">' +
    '<h2 style="margin:0 0 6px;font-size:20px">' + head + '</h2>' +
    '<div style="font-size:13px;color:var(--txt-muted);margin-bottom:14px">' + sub + '</div>' +
    '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px">' + cards + '</div>' + note + '</section>';
}
export type InsetVariant = 'trassa' | 'home' | 'winter';
const RULES: Array<[InsetVariant, RegExp]> = [
  ['winter', /(zim|moroz|holod)/i],
  ['trassa', /(m-?11|m-?12|trass|bystro|dc-zaryad|handshake|otdaet-menshe|karta-zaryadnyh|150-kvt|60-80)/i],
  ['home', /(domash|chastnom-dome|rozetka|tarif|parkov|parking|kvartir|ustanovk|dlya-doma|nastennaya|-kvt|schetchik|avtomat)/i],
];
export function variantForSlug(slug: string): InsetVariant | null {
  const s = String(slug || '').toLowerCase();
  for (const [v, re] of RULES) if (re.test(s)) return v;
  return null;
}
const INSETS: Record<InsetVariant, { title: string; text: string; links: Array<Array<string>> }> = {
  trassa: {
    title: 'Быстрая зарядка китайского EV на трассе',
    text: 'Машины с портом GB/T (Zeekr, Li Auto, Voyah, BYD) подключаются к основной сети быстрых станций CCS2 через переходник. Важно, чтобы у адаптера был термодатчик: без него порт греется на высоких токах. Проверенный адаптер держит заявленный ток до 300 А и отключается при перегреве.',
    links: [['/catalog/adapter-ccs2-gbt-dc.html', 'Адаптер CCS2 → GB/T DC, 250–300 А'], ['/catalog/kabel-type2-gbt-10m-32a.html', 'Кабель Type 2–GB/T, 10 м, 32 А']],
  },
  home: {
    title: 'Домашняя зарядка без перегрузки проводки',
    text: 'Настенная станция с динамической балансировкой (DLB) сама снижает ток, когда дома пиковое потребление: не выбивает пробки и не греет проводку. Монтаж под ключ: инженер партнёра привозит станцию, ставит, подключает УЗО и проверяет на вашем авто. Смета фиксируется до начала работ — сюрпризов не бывает.',
    links: [['/catalog/stanciya-2v1-type2-gbt.html', 'Настенная станция 2-в-1 GB/T + Type 2, 22 кВт'], ['/blog/ustanovka-zaryadnoy-stancii-elektromobilya/', 'Как проходит установка: разбор']],
  },
  winter: {
    title: 'Зимняя зарядка без примерзания',
    text: 'Заглушка порта и дверцы лючка примерзают уже при −15…−20 °C — силиконовая смазка решает это заранее, до морозов. Оплётка кабеля из TPU остаётся гибкой до −40 °C: обычный PVC-кабель с маркетплейса на морозе дубеет за одну ночь.',
    links: [['/catalog/smazka-silikonom-zima.html', 'Смазка силиконовая (зимний kit)'], ['/catalog/kabel-type2-gbt-10m-32a.html', 'Кабель Type 2–GB/T, 10 м, морозостойкий']],
  },
};
export function insetHtml(v: InsetVariant): string {
  const d = INSETS[v];
  const links = d.links.map((l) =>
    '<a href="' + l[0] + '" style="display:inline-block;padding:9px 14px;border:1px solid rgba(77,155,245,.45);border-radius:10px;color:#7FB8FF;text-decoration:none;font-size:13.5px;font-weight:600">' + esc(l[1]) + '</a>').join(' ');
  return '<aside class="ins-inset" data-inset="' + v + '" style="margin:22px 0;padding:18px 20px;background:#14181F;border:1px solid var(--line);border-left:3px solid #4d9bf5;border-radius:14px">' +
    '<div style="font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#7FB8FF;margin-bottom:6px">Инженерное решение</div>' +
    '<div style="font-size:15.5px;font-weight:700;color:var(--txt);line-height:1.4;margin-bottom:6px">' + esc(d.title) + '</div>' +
    '<p style="margin:0 0 12px;font-size:14px;color:var(--txt-muted);line-height:1.55">' + esc(d.text) + '</p>' +
    '<div style="display:flex;gap:10px;flex-wrap:wrap">' + links + '</div></aside>';
}
export function injectIntoArticle(body: string, slug: string): string {
  const v = variantForSlug(slug);
  if (!v) return body;
  const h = String(body || '');
  if (h.includes('ins-inset')) return h;
  const ins = insetHtml(v);
  const ends: number[] = [];
  const re = /<\/h2>/g; let mm: RegExpExecArray | null;
  while ((mm = re.exec(h))) ends.push(mm.index + mm[0].length);
  let at = -1;
  if (ends.length >= 2) {
    const pEnd = h.indexOf('</p>', ends[1]);
    at = (pEnd >= 0 && pEnd - ends[1] < 1200) ? pEnd + 4 : ends[1];
  } else if (ends.length === 1) {
    at = ends[0];
  } else {
    let n = 0; const rp = /<\/p>/g;
    while ((mm = rp.exec(h))) { n++; if (n === 2) { at = rp.lastIndex; break; } }
  }
  return at > 0 ? (h.slice(0, at) + ins + h.slice(at)) : h;
}
