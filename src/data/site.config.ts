interface SiteConfig {
	site: string
	author: string
	title: string
	description: string
	lang: string
	ogLocale: string
	shareMessage: string
	paginationSize: number
}

export const siteConfig: SiteConfig = {
	site: 'https://zapashoda-ev.ru/',
	author: 'Запас хода',
	title: 'Запас хода — зарядка электромобилей в России',
	description: 'Практика владения электромобилем в России: разъёмы и адаптеры GB/T, Type 2, CCS2, реальные проблемы, карта зарядных станций и каталог с оплатой при получении.',
	lang: 'ru-RU',
	ogLocale: 'ru_RU',
	shareMessage: 'Поделиться статьёй',
	paginationSize: 12
}
