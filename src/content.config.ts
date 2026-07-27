import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const blog = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/blog' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    // CMS posts may omit image; keep WP-style path used by existing posts
    image: z.string().optional().default('/wp-content/uploads/2023/02/image-2.jpg'),
    slug: z.string(),
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
