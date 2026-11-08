export const prerender = true;
import type { APIRoute } from 'astro';

const models = Object.values(import.meta.glob('../data/models/*.json', { eager: true, import: 'default' })) as any[];
const articles = Object.values(import.meta.glob('../data/articles/**/*.json', { eager: true, import: 'default' })) as any[];
const sku = (await import('../data/sku.json')).default as any;
const razemy = (await import('../data/razemy_conf.json')).default as any;
const b2b = (await import('../data/b2b_segments.json')).default as any;

let blogFaq = 0;
for (const a of articles) if (a && a.slug && a.section === 'blog') { blogFaq += (a.faq && a.faq.length ? 1 : 0); }

const body = JSON.stringify({
  last_build_stamp: new Date().toISOString(),
  site: 'zapashoda-ev.ru',
  active_features: ['matrix', 'calculators_v3', 'shop', 'b2b_segments', 'razemy', 'stations_map', 'quiz', 'digital_guide_shop', 'blog_faqpage', 'station_status_button'],
  payments: 'tinkoff_test (DEMO-key)',
  open_bugs: [
    'b2b_pdf: static/b2b/paket-dileram.pdf описывает старую партнёрскую модель с лидами — нужна переверстка под модель опт + Mini App (мост Z-0042, ждёт вердикта владельца)',
    'tinkoff: терминал на DEMO-ключе — для боевых платежей заменить на production-ключ (владелец)',
    'shorts: автопилот не публикует — ждёт решения владельца'
  ],
  contacts: { telegram: 'https://t.me/zapashoda_ev', bot: 'https://t.me/zapashoda_ev_bot' },
  catalog: { models: models.length, sku_items: (sku.items || []).length, razemy_pages: 1 + (razemy.items ? razemy.items.length : 0), b2b_segments: (b2b.length || 0) + 1, stations_map: 2073, blog_faqpage: blogFaq, blog_total: articles.filter((a) => a && a.slug && a.section === 'blog').length },
  llm_hint: 'Запас хода — магазин аксессуаров для зарядки EV в РФ: адаптеры, кабели, зарядные станции, матрица совместимости, справочник разъёмов, карта ЭЗС. РРЦ и подбор по модели — в каталоге.',
}, null, 1);
export const GET: APIRoute = () => new Response(body, { headers: { 'Content-Type': 'application/json; charset=utf-8' } });
