import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const mediaObject = z
  .object({
    url: z.string().optional(),
    src: z.string().optional(),
    filename: z.string().optional(),
    prefix: z.string().optional(),
    alt: z.string().nullable().optional(),
    sizes: z.record(z.string(), z.any()).optional(),
  })
  .passthrough();

const mediaField = z.preprocess((val) => {
  if (val == null || val === '') return undefined;
  if (typeof val === 'number') return undefined;
  if (typeof val === 'string') {
    const t = val.trim();
    if (!t || /^\d+$/.test(t) || t === '[object Object]') return undefined;
    return t;
  }
  if (typeof val === 'object' && !Array.isArray(val)) return val;
  return undefined;
}, z.union([z.string(), mediaObject]).optional());

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
    heroImage: mediaField,
    imageAlt: z.string().optional(),
    featuredImageAlt: z.string().optional(),
    slug: z.string().optional(),
    draft: z.boolean().optional(),
    _status: z.string().optional(),
  }),
});

export const collections = { blog };
