import rss from '@astrojs/rss'
import { ARTICLES } from '../../utils/articles'
import { siteConfig } from '@/site-config'

export const GET = async () =>
  rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: siteConfig.site,
    items: ARTICLES.slice(0, 50).map((a) => ({
      title: a.title,
      description: a.desc,
      pubDate: a.date ? new Date(a.date) : new Date(),
      link: `/${a.section}/${a.slug}/`
    }))
  })
