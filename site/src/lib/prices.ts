import SKUS from '../data/sku.json';

const SKU_BY: Record<string, any> = {};
for (const it of ((SKUS as any).items || [])) SKU_BY[String(it.slug)] = it;

export const fmtRub = (n: number) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');

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
  [/(>\s*)\b690\s*\u20bd/g, 'smazka-silikonom-zima', '$1', ' ' + RUB],
  [/\b39\s?000\s*\u20bd/g, 'nastennaya-stanciya-gbt-7kw', '', ' ' + RUB],
  [/\b24\s?500\s*\u20bd/g, 'nastennaya-stanciya-type2-7kw', '', ' ' + RUB],
  [/\b7\s?000\s*\u20bd/g, 'adapter-type2-gbt-premium', '', ' ' + RUB],
  [/\b44\s?000\s*\u20bd/g, 'stanciya-2v1-type2-gbt', '', ' ' + RUB],
  [/\b16\s?000\s*\u20bd/g, 'portativnaya-zaryadka-gbt-7kw', '', ' ' + RUB],
];

export function priceFix(s: string): string {
  let out = String(s || '');
  for (const [re, slug, prefix, suffix] of RULES) {
    const it = SKU_BY[slug];
    if (!it || it.price == null) continue;
    out = out.replace(re, prefix + fmtRub(Number(it.price)) + suffix);
  }
  return out;
}
