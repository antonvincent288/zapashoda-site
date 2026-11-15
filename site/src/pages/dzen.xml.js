const articles = Object.values(import.meta.glob('../data/articles/**/*.json', { eager: true, import: 'default' }));
export async function GET(context) {
  const SITE = 'https://zapashoda-ev.ru';
  const items = articles
    .filter((a) => a && a.slug && a.title)
    .sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))
    .slice(0, 30);
  const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const items_xml = items.map((a) => {
    const link = a.url || (SITE + '/blog/' + a.slug);
    // полный текст: body_html + блоки FAQ, внутренние ссылки -> абсолютные
    let html = String(a.body_html || '');
    if (a.faq && a.faq.length) {
      html += '<h2>Частые вопросы</h2>' + a.faq.map((f) => '<h3>' + esc(f.q || '') + '</h3><p>' + esc(f.a || '') + '</p>').join('');
    }
    html = html.replace(/href="\//g, 'href="' + SITE + '/');
    const cover = a.og ? SITE + String(a.og) : '';
    return [
      '<item>',
      '<title>' + esc(a.title) + '</title>',
      '<link>' + esc(link) + '</link>',
      '<guid isPermaLink="true">' + esc(link) + '</guid>',
      '<pubDate>' + new Date((a.date || '2026-01-01') + 'T12:00:00Z').toUTCString() + '</pubDate>',
      '<description>' + esc(String(a.desc || '').slice(0, 900)) + '</description>',
      cover ? '<enclosure url="' + esc(cover) + '" type="image/png" length="60000"/>' : '',
      '<content:encoded><![CDATA[' + html.replace(/]]>/g, ']]&gt;') + ']]></content:encoded>',
      '</item>',
    ].filter(Boolean).join('');
  }).join('');
  const feed = '<?xml version="1.0" encoding="UTF-8"?>'
    + '<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom">'
    + '<channel>'
    + '<title>Запас хода</title>'
    + '<link>' + SITE + '</link>'
    + '<atom:link href="' + SITE + '/dzen.xml" rel="self" type="application/rss+xml"/>'
    + '<description>Практика зарядки EV в России: разъёмы, станции, адаптеры, разборы моделей</description>'
    + '<language>ru-RU</language>'
    + items_xml
    + '</channel></rss>';
  return new Response(feed, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } });
}
