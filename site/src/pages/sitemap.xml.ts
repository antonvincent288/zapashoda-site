export const prerender = true;
import type { APIRoute } from 'astro';

const models = Object.values(import.meta.glob('../data/models/*.json', { eager: true, import: 'default' })) as any[];
const articles = Object.values(import.meta.glob('../data/articles/**/*.json', { eager: true, import: 'default' })) as any[];
const publicPages = import.meta.glob('../../public/**/*.html', { eager: false }) as Record<string, unknown>;

const SITE = 'https://zapashoda-ev.ru';
const LASTMOD = '2026-11-10';
type U = { loc: string; pri: string };
const urls: U[] = [{ loc: SITE + '/', pri: '1.0' }];
for (const p of ['models','blog','pain','safety','tools','b2b','about','services','catalog','shop/digital','charging','news','quiz','privacy','compare','partner','sovmestimost','razemy','calculators','tarify']) {
  urls.push({ loc: `${SITE}/${p}/`, pri: '0.7' });
}
for (const m of models) if (m && m.slug) urls.push({ loc: `${SITE}/models/${m.slug}/`, pri: '0.8' });
for (const r of ['type2','ccs2','gbt','chademo','type1','schuko']) urls.push({ loc: `${SITE}/razemy/${r}/`, pri: '0.7' });
for (const c2 of ['cost','time']) urls.push({ loc: `${SITE}/calculators/${c2}/`, pri: '0.7' });
for (const s2 of ['taksi','avtopark','azs','jk','salony','predlozh-mesto']) urls.push({ loc: `${SITE}/b2b/${s2}/`, pri: '0.6' });
for (const s5 of ['ustanovka-stancii','ustanovka-stancii-v-garazhe','uvelichenie-moshchnosti','stanciya-gbt','stanciya-type2','stanciya-2v1','tehobsluzhivanie','tehobsluzhivanie-stanciy','moschnost-stancii','oshibki-ustanovki']) urls.push({ loc: `${SITE}/services/${s5}.html`, pri: '0.6' });
const cmpPairs = (await import('../data/compare_pairs.json')).default as any;
for (const cp of (cmpPairs.pairs || [])) urls.push({ loc: `${SITE}/compare/${cp.slug}/`, pri: '0.6' });
for (const a of articles) if (a && a.slug && ['blog','pain','safety'].includes(String(a.section))) urls.push({ loc: `${SITE}/${a.section}/${a.slug}/`, pri: '0.7' });
const costPages = import.meta.glob('../pages/cost/*.astro') as Record<string, unknown>;
const costSlugs = Object.keys(costPages).map((p) => p.split('/').pop()!.replace('.astro', ''));
for (const c of costSlugs) urls.push(c === 'index' ? { loc: `${SITE}/cost/`, pri: '0.7' } : { loc: `${SITE}/cost/${c}/`, pri: '0.6' });
const brands = (await import('../data/legacy/brands.json')).default as any[];
urls.push({ loc: `${SITE}/brands/`, pri: '0.6' });
for (const b of brands) if (b.slug) urls.push({ loc: `${SITE}/brands/${b.slug}.html/`, pri: '0.5' });
const sku = (await import('../data/sku.json')).default as any;
for (const s3 of (sku.items || [])) if (s3.slug) urls.push({ loc: `${SITE}/catalog/${s3.slug}.html/`, pri: '0.7' });
const SKIP_PREFIXES = ['/decapcms', '/admin', '/app', '/assets'];
const known = new Set<string>(urls.map((x2) => x2.loc));
for (const f of Object.keys(publicPages)) {
  const u = f.replace('../../public', '');
  if (u === '/index.html') continue;
  const clean = u.endsWith('/index.html') ? u.replace(/index\.html$/, '') : u;
  if (SKIP_PREFIXES.some((p2) => clean === p2 || clean.startsWith(p2 + '/'))) continue;
  if (clean === '/rss.xml') continue;
  if (clean.endsWith('.html')) {
    const twin = clean.replace(/\.html$/, '/') + '';
    if (known.has(SITE + twin)) continue;
  }
  known.add(SITE + clean);
  urls.push({ loc: SITE + clean, pri: '0.5' });
}
const seen = new Set<string>();
const uniq = urls.filter((u) => (seen.has(u.loc) ? false : (seen.add(u.loc), true)));
const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  uniq.map((u) => `  <url><loc>${u.loc}</loc><changefreq>weekly</changefreq><priority>${u.pri}</priority><lastmod>${LASTMOD}</lastmod></url>`).join('\n') +
  `\n</urlset>\n`;
export const GET: APIRoute = () => new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
