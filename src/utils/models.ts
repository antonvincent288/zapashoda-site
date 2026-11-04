export type Model = {
  slug: string
  title: string
  desc: string
  og: string
  body_html: string
  headings: { id: string; text: string }[]
  brand: string
  type: string
  port: string
  name: string
  years: string
}
const mods = import.meta.glob('/src/data/models/*.json', { eager: true })
export const MODELS: Model[] = Object.values(mods).map((m) => (m.default ?? m) as Model)
  .sort((a, b) => a.brand.localeCompare(b.brand) || a.name.localeCompare(b.name))
