import { ARTICLES } from '../utils/articles'
import { MODELS } from '../utils/models'
import extra from '../data/extra_pages.json'
import { siteConfig } from '@/site-config'

export const GET = async () => {
  const urls: { loc: string; priority: string }[] = []
  urls.push({ loc: '/', priority: '1.0' })
  urls.push({ loc: '/models/', priority: '0.9' })
  urls.push({ loc: '/blog/', priority: '0.8' })
  urls.push({ loc: '/pain/', priority: '0.8' })
  urls.push({ loc: '/safety/', priority: '0.7' })
  for (const m of MODELS) urls.push({ loc: `/models/${m.slug}/`, priority: '0.8' })
  for (const a of ARTICLES) urls.push({ loc: `/${a.section}/${a.slug}/`, priority: a.section === 'blog' ? '0.7' : '0.6' })
  for (const e of extra as string[]) urls.push({ loc: e, priority: '0.5' })
  const base = siteConfig.site.replace(/\/$/, '')
  const xml = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls
    .map((u) => `<url><loc>${base}${u.loc}</loc><priority>${u.priority}</priority></url>`)
    .join('\n')}\n</urlset>`
  return new Response(xml, { headers: { 'Content-Type': 'application/xml; charset=utf-8' } })
}
