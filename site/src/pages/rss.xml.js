export async function GET() {
  const all = Object.values(import.meta.glob('../data/articles/blog/*.json', { eager: true, import: 'default' }));
  all.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));
  const SITE = 'https://zapashoda-ev.ru';
  const esc = (s) => String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const items = all.slice(0, 30).map((a) => '    <item><title>' + esc(a.title) + '</title><link>' + SITE + '/blog/' + a.slug + '/</link><guid isPermaLink="true">' + SITE + '/blog/' + a.slug + '/</guid><pubDate>' + new Date(String(a.date || '2026-01-01')).toUTCString() + '</pubDate><description>' + esc(a.desc) + '</description></item>').join(' ');
  const xml = '<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Запас хода — блог</title><link>' + SITE + '/blog/</link><description>Практика зарядки EV в России</description><language>ru</language>' + items + '</channel></rss>';
  return { body: xml, headers: { 'Content-Type': 'application/xml; charset=utf-8' } };
}
