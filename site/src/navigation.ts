import { getPermalink, getBlogPermalink, getAsset } from './utils/permalinks';

export const headerData = {
  links: [
    {
      text: 'Homes',
      links: [
        {
          text: 'SaaS',
          href: getPermalink('/homes/saas'),
        },
        {
          text: 'Startup',
          href: getPermalink('/homes/startup'),
        },
        {
          text: 'Mobile App',
          href: getPermalink('/homes/mobile-app'),
        },
        {
          text: 'Personal',
          href: getPermalink('/homes/personal'),
        },
      ],
    },
    {
      text: 'Pages',
      links: [
        {
          text: 'Features (Anchor Link)',
          href: getPermalink('/#features'),
        },
        {
          text: 'Services',
          href: getPermalink('/services'),
        },
        {
          text: 'Pricing',
          href: getPermalink('/pricing'),
        },
        {
          text: 'About us',
          href: getPermalink('/about'),
        },
        {
          text: 'Contact',
          href: getPermalink('/contact'),
        },
        {
          text: 'Terms',
          href: getPermalink('/terms'),
        },
        {
          text: 'Privacy policy',
          href: getPermalink('/privacy'),
        },
      ],
    },
    {
      text: 'Landing',
      links: [
        {
          text: 'Lead Generation',
          href: getPermalink('/landing/lead-generation'),
        },
        {
          text: 'Long-form Sales',
          href: getPermalink('/landing/sales'),
        },
        {
          text: 'Click-Through',
          href: getPermalink('/landing/click-through'),
        },
        {
          text: 'Product Details (or Services)',
          href: getPermalink('/landing/product'),
        },
        {
          text: 'Coming Soon or Pre-Launch',
          href: getPermalink('/landing/pre-launch'),
        },
        {
          text: 'Subscription',
          href: getPermalink('/landing/subscription'),
        },
      ],
    },
    {
      text: 'Blog',
      links: [
        {
          text: 'Blog List',
          href: getBlogPermalink(),
        },
        {
          text: 'Article',
          href: getPermalink('get-started-website-with-astro-tailwind-css', 'post'),
        },
        {
          text: 'Article (with MDX)',
          href: getPermalink('markdown-elements-demo-post', 'post'),
        },
        {
          text: 'Category Page',
          href: getPermalink('tutorials', 'category'),
        },
        {
          text: 'Tag Page',
          href: getPermalink('astro', 'tag'),
        },
      ],
    },
  ],
  actions: [{ text: 'Download', href: 'https://github.com/arthelokyo/astrowind', target: '_blank' }],
};

export const footerData = {
  links: [
    {
      title: 'Модели',
      links: [
        { text: 'Каталог моделей', href: getPermalink('/models/') },
        { text: 'Zeekr 001', href: getPermalink('/models/zeekr-001-001-fr/') },
        { text: 'Разъёмы GB/T', href: getPermalink('/razemy/') },
        { text: 'Каталог товаров', href: getPermalink('/catalog/') },
      ],
    },
    {
      title: 'База знаний',
      links: [
        { text: 'Блог', href: getBlogPermalink() },
        { text: 'Проблемы', href: getPermalink('/pain/') },
        { text: 'VIN-справочник', href: getPermalink('/vin/') },
        { text: 'Гайды', href: getPermalink('/shop/digital/') },
      ],
    },
    {
      title: 'Инструменты',
      links: [
        { text: 'Калькуляторы', href: getPermalink('/calculator/') },
        { text: 'Всё о твоей машине', href: getPermalink('/quiz/') },
        { text: 'Поиск', href: getPermalink('/search/') },
        { text: 'Зарядные станции', href: getPermalink('/charging/') },
      ],
    },
    {
      title: 'Связь',
      links: [
        { text: 'Telegram-канал', href: 'https://t.me/zapashoda_ev', target: '_blank' },
        { text: 'Написать нам', href: 'mailto:f-epshtein@yandex.ru' },
        { text: 'Мини-приложение', href: 'https://t.me/zapashoda_ev_bot/app', target: '_blank' },
        { text: 'Партнёрам', href: getPermalink('/partners/') },
      ],
    },
  ],
  secondaryLinks: [
    { text: 'Политика конфиденциальности', href: getPermalink('/privacy') },
    { text: 'О проекте', href: getPermalink('/about') },
  ],
  socialLinks: [
    { ariaLabel: 'Telegram', icon: 'tabler:brand-telegram', href: 'https://t.me/zapashoda_ev' },
    { ariaLabel: 'Дзен', icon: 'tabler:brand-dzen', href: 'https://dzen.ru/zapashoda' },
  ],
  footNote: `© 2026 Запас хода — практика зарядки EV в России`,
};
