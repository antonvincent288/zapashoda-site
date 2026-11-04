import { defineCollection, z } from 'astro:content'
import { CATEGORIES } from '@/data/categories'

const blog = defineCollection({
	schema: ({ image }) =>
		z.object({
			title: z.string().max(200),
			description: z.string(),
			pubDate: z
				.string()
				.or(z.date())
				.transform((val) => new Date(val)),
			heroImage: image().optional(),
			category: z.string(),
			tags: z.array(z.string()).default([]),
			draft: z.boolean().default(false)
		})
})

export const collections = { blog }
