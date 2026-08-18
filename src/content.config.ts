import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const mediaObject = z
  .object({
    url: z.string().optional(),
    filename: z.string().optional(),
    alt: z.string().nullable().optional(),
    sizes: z.record(z.string(), z.any()).optional(),
  })
  .passthrough();

const mediaField = z.union([z.string(), mediaObject, z.number(), z.null()]).optional();

const blog = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    excerpt: z.string().optional(),
    date: z.coerce.date().optional(),
    image: mediaField,
    featuredImage: mediaField,
    imageAlt: z.string().optional(),
    featuredImageAlt: z.string().optional(),
    slug: z.string(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
