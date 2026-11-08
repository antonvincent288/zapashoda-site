export const prerender = true;
import type { APIRoute } from 'astro';

const models = Object.values(import.meta.glob('../data/models/*.json', { eager: true, import: 'default' })) as any[];
const articles = Object.values(import.meta.glob('../data/articles/**/*.json', { eager: true, import: 'default' })) as any[];
const publicPages = import.meta.glob('../../public/**/*.html', { eager: false }) as Record<string, unknown>;

const SITE = 'https://zapashoda-ev.ru';
type U = { loc: string; pri: string };
const urls: U[] = [{ loc: SITE + '/', pri: '1.0' }];
for (const p of ['models','blog','pain','safety','tools','b2b','about','services','catalog','shop/digital','charging','news','quiz','razemy']) {
  urls.push({ loc: `${SITE}/${p}/`, pri: '0.7' });
}
urls.push({ loc: SITE + '/rss.xml', pri: '0.3' });
for (const m of models) if (m && m.slug) urls.push({ loc: `${SITE}/models/${m.slug}/`, pri: '0.8' });
for (const r of ['type2','ccs2','gbt','chademo','type1','schuko']) urls.push({ loc: `${SITE}/razemy/${r}/`, pri: '0.7' });
for (const r of ['type2','ccs2','gbt','chademo','type1','schuko']) urls.push({ loc: `${SITE}/razemy/${r}/`, pri: '0.7' });
for (const a of articles) if (a && a.slug && a.section) urls.push({ loc: `${SITE}/${a.section}/${a.slug}/`, pri: '0.7' });
for (const f of Object.keys(publicPages)) {
  const u = f.replace('../../public', '');
  if (u === '/index.html') continue;
  const clean = u.endsWith('/index.html') ? u.replace(/index\.html$/, '') : u;
  urls.push({ loc: SITE + clean, pri: '0.5' });
}
const seen = new Set<string>();
const uniq = urls.filter((u) => (seen.has(u.loc) ? false : (seen.add(u.loc), true)));
const body = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  uniq.map((u) => `  <url><loc>${u.loc}</loc><changefreq>weekly</changefreq><priority>${u.pri}</priority></url>`).join('\n') +
  `\n</urlset>\n`;
export const GET: APIRoute = () => new Response(body, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
