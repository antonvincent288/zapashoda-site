export type Article = {
  slug: string
  title: string
  desc: string
  category: string
  read_min: number
  date: string
  og: string
  body_html: string
  extra_html: string
  headings: { id: string; text: string }[]
}

const mods = import.meta.glob('/src/data/articles/**/*.json', { eager: true })

export const ARTICLES: Article[] = Object.values(mods).map((m) => m.default as Article)

export function bySection(section: string): Article[] {
  return ARTICLES.filter((a) => a.section === section).sort((a, b) => (a.date < b.date ? 1 : -1))
}

export function getArticle(section: string, slug: string): Article | undefined {
  return ARTICLES.find((a) => a.section === section && a.slug === slug)
}
