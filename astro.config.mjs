// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import { unified } from '@astrojs/markdown-remark';
import { rehypePayloadImages } from './src/lib/rehype-payload-images.mjs';

export default defineConfig({
  site: 'https://interieurdesignerweb.nl',
  trailingSlash: 'always',
  compressHTML: true,
  integrations: [mdx()],
  markdown: {
    processor: unified({
      rehypePlugins: [rehypePayloadImages],
    }),
  },
});
