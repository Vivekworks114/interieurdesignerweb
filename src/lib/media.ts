import {
  FALLBACK_IMAGE,
  resolveMediaUrl,
} from './media-url.mjs';

export {
  FALLBACK_IMAGE,
  resolveMediaUrl,
  wpUploadsPath,
  looksLikeImageUrl,
  isWpUploadsPath,
} from './media-url.mjs';

type MediaObject = {
  url?: string | null;
  filename?: string | null;
  alt?: string | null;
  sizes?: Record<string, { url?: string | null } | undefined>;
};

export type MediaInput = string | number | MediaObject | null | undefined;

export const SITE_ORIGIN = 'https://interieurdesignerweb.nl';

export function extractMediaUrl(input: MediaInput): string {
  if (!input) return '';
  if (typeof input === 'number') return '';
  if (typeof input === 'string') return input.trim();

  const fromSizes =
    input.sizes?.large?.url ||
    input.sizes?.medium?.url ||
    input.sizes?.thumbnail?.url ||
    '';
  return String(input.url || fromSizes || input.filename || '').trim();
}

export function extractMediaAlt(input: MediaInput, fallback = ''): string {
  if (input && typeof input === 'object' && input.alt) return input.alt.trim();
  return fallback;
}

export function altFromSrc(src: string, fallback = 'Afbeelding'): string {
  try {
    const path = /^https?:\/\//i.test(src) ? new URL(src).pathname : src;
    const name = decodeURIComponent(path.split('/').pop() || '').replace(/\.[a-z0-9]+$/i, '');
    const cleaned = name
      .replace(/[-_]+/g, ' ')
      .replace(/\d{3,4}x\d{3,4}/g, '')
      .replace(/\b(scaled|web|pexels|photo)\b/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (!cleaned || /^[a-f0-9-]{8,}$/i.test(cleaned)) return fallback;
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  } catch {
    return fallback;
  }
}

export function absoluteUrl(src: string, site = SITE_ORIGIN): string {
  const resolved = resolveMediaUrl(src, src);
  if (!resolved) return site;
  if (/^https?:\/\//i.test(resolved)) return resolved;
  return `${site}${resolved.startsWith('/') ? resolved : `/${resolved}`}`;
}

export function getPostMedia(
  data: {
    title?: string;
    pubDate?: Date;
    image?: MediaInput;
    featuredImage?: MediaInput;
    imageAlt?: string;
    featuredImageAlt?: string;
  },
  fallback = FALLBACK_IMAGE,
): { src: string; alt: string } {
  const alt =
    data.imageAlt?.trim() ||
    data.featuredImageAlt?.trim() ||
    extractMediaAlt(data.featuredImage) ||
    extractMediaAlt(data.image) ||
    data.title ||
    'Blogafbeelding';

  const raw = extractMediaUrl(data.featuredImage) || extractMediaUrl(data.image);
  const src = resolveMediaUrl(raw, fallback, data.pubDate);
  return { src, alt };
}
