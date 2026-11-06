const articles = Object.values(import.meta.glob('../data/articles/**/*.json', { eager: true, import: 'default' }));
export async function GET(context) {
  const SITE = 'https://zapashoda-ev.ru';
  const items = articles
    .filter((a) => a && a.slug && a.title)
    .sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))
    .slice(0, 60);
  const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const xml = items.map((a) => {
    const link = a.url || (SITE + '/blog/' + a.slug);
    const p = String(a.desc || '');
    return [
      '<item>',
      '<title>' + esc(a.title) + '</title>',
      '<link>' + esc(link) + '</link>',
      '<guid isPermaLink="true">' + esc(link) + '</guid>',
      '<description>' + esc(p.slice(0, 500)) + '</description>',
      a.date ? '<pubDate>' + new Date(a.date + 'T12:00:00Z').toUTCString() + '</pubDate>' : '',
      '</item>',
    ].filter(Boolean).join('');
  }).join('');
  const feed = '<?xml version="1.0" encoding="UTF-8"?>'
    + '<rss version="2.0"><channel>'
    + '<title>Запас хода — практика зарядки EV в России</title>'
    + '<link>' + SITE + '</link>'
    + '<description>Подбор зарядки и адаптеров для электромобилей, карта станций, разборы проблем</description>'
    + '<language>ru-RU</language>'
    + xml
    + '</channel></rss>';
  return new Response(feed, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
