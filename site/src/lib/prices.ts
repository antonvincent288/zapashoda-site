import SKUS from '../data/sku.json';

const SKU_BY: Record<string, any> = {};
for (const it of ((SKUS as any).items || [])) SKU_BY[String(it.slug)] = it;

export const fmtRub = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

// ФЛАГ ЦЕН (директива владельца 11.11.2026): одна константа управляет ценами на ВСЁМ сайте.
//   PRICES_ON = false — цены каталога выключены: вместо цены показывается «скоро»,
//                       литеральные цены в контенте гасятся priceFix'ом (включая бандлы и «выгоду»),
//                       РРЦ-блок B2B скрыт, суммы в корзине и lead-модалке не показываются
//                       (цена уходит только дилеру в заявку).
//   PRICES_ON = true  — цены снова видны везде автоматически, без правок страниц.
export const PRICES_ON = false;
export const SOON = 'скоро';

export function priceOut(price: number | null | undefined): string {
  return PRICES_ON && price != null ? fmtRub(Number(price)) + ' ₽' : SOON;
}

// Директива владельца (09.11.2026): цены нигде не вшиваются жёстко.
// В контенте (JSON body_html, статьи) могут остаться старые литералы —
// при рендере они заменяются на актуальные цены каталога (sku.json).
// Менять цены нужно только в каталоге: здесь они подхватятся автоматически.
const RUB = '\u20bd';
const RULES: Array<[RegExp, string, string, string]> = [
  [/\u043e\u0442\s*4\s?500\s*\u20bd/g, 'adapter-type2-gbt-base', 'от ', ' ' + RUB],
  [/\u043e\u0442\s*9\s?500\s*\u20bd/g, 'portativnaya-zaryadka-gbt-3-5kw', 'от ', ' ' + RUB],
  [/\u043e\u0442\s*7\s?500\s*\u20bd/g, 'portativnaya-zaryadka-type2-3-5kw', 'от ', ' ' + RUB],
  [/\b95\s?000\s*\u20bd/g, 'adapter-ccs2-gbt-dc', '', ' ' + RUB],
  [/\b13\s?500\s*\u20bd/g, 'kabel-type2-type2-5m-22kw', '', ' ' + RUB],
  [/\b9\s?900\s*\u20bd/g, 'udlinitel-type2-type2-5m', '', ' ' + RUB],
  [/(?:&gt;|>)\s*690\s*\u20bd/g, 'smazka-silikonom-zima', '', ' ' + RUB],
  [/\b39\s?000\s*\u20bd/g, 'nastennaya-stanciya-gbt-7kw', '', ' ' + RUB],
  [/\b24\s?500\s*\u20bd/g, 'nastennaya-stanciya-type2-7kw', '', ' ' + RUB],
  [/\b7\s?000\s*\u20bd/g, 'adapter-type2-gbt-premium', '', ' ' + RUB],
  [/\b44\s?000\s*\u20bd/g, 'stanciya-2v1-type2-gbt', '', ' ' + RUB],
  [/\b16\s?000\s*\u20bd/g, 'portativnaya-zaryadka-gbt-7kw', '', ' ' + RUB],
  [/\b6\s?500\s*\u20bd/g, 'adapter-gbt-type2-reverse', '', ' ' + RUB],
  [/\b8\s?500\s*\u20bd/g, 'adapter-type1-type2', '', ' ' + RUB],
  [/\b13\s?000\s*\u20bd/g, 'kabel-type2-gbt-5m-22kw', '', ' ' + RUB],
  [/\b34\s?500\s*\u20bd/g, 'nastennaya-stanciya-type2-22kw', '', ' ' + RUB],
  [/\b15\s?500\s*\u20bd/g, 'kabel-type2-type2-7m-32a', '', ' ' + RUB],
];
const LIT_EXTRA: RegExp[] = [
  /\b20\s?190\s*\u20bd/g,
  /\b22\s?190\s*\u20bd/g,
  /\b26\s?190\s*\u20bd/g,
  /\b28\s?190\s*\u20bd/g,
  /\b34\s?590\s*\u20bd/g,
  /\b36\s?590\s*\u20bd/g,
];

export function priceFix(s: string): string {
  let out = String(s || '');
  if (!PRICES_ON) {
    for (const [re] of RULES) out = out.replace(re, SOON);
    for (const re of LIT_EXTRA) out = out.replace(re, SOON);
    // «Выгода N ₽» при выключенных ценах не имеет смысла — убираем целиком
    out = out.replace(/[Вв]ыгода\s+\d{1,3}(?:\s?\d{3})+\s*\u20bd/g, '');
    // любая литеральная цена с тысячной группой (4 500 ₽, 19 900 ₽, 20 190 ₽…) — 1–3 цифры + группы;
    // товарные тарифы (15–22 ₽/кВт·ч, 3,5 ₽) не матчатся, у них нет тысячной группы
    out = out.replace(/\b\d{1,3}(?:\s?\d{3})+\s*\u20bd/g, SOON);
    return out;
  }
  for (const [re, slug, prefix, suffix] of RULES) {
    const it = SKU_BY[slug];
    if (!it || it.price == null) continue;
    out = out.replace(re, prefix + fmtRub(Number(it.price)) + suffix);
  }
  return out;
}
