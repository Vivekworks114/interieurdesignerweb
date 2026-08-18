/**
 * Image URLs must stay site-relative like Takenweb on Cloudflare Workers:
 *   /wp-content/uploads/2024/10/klantkompas-software-uitleg-300x185.png
 * After deploy that becomes:
 *   https://<worker>.workers.dev/wp-content/uploads/2024/10/...
 */

export const FALLBACK_IMAGE = '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg';

function isHttp(value) {
  return /^https?:\/\//i.test(value);
}

function cmsOrigin() {
  const raw =
    (typeof process !== 'undefined' &&
      (process.env?.PAYLOAD_URL || process.env?.PUBLIC_PAYLOAD_URL || process.env?.PUBLIC_MEDIA_URL)) ||
    '';
  return String(raw).replace(/\/+$/, '');
}

export function uploadDateParts(date) {
  const d = date instanceof Date && !Number.isNaN(date.valueOf()) ? date : new Date();
  return {
    yyyy: String(d.getUTCFullYear()),
    mm: String(d.getUTCMonth() + 1).padStart(2, '0'),
  };
}

export function safeFilename(name) {
  const base = String(name || 'image')
    .split(/[\\/]/)
    .pop()
    .split('?')[0];
  const cleaned = base.replace(/[^a-zA-Z0-9._-]/g, '-').replace(/-+/g, '-');
  return cleaned || 'image.jpg';
}

export function wpUploadsPath(filename, date) {
  const { yyyy, mm } = uploadDateParts(date);
  return `/wp-content/uploads/${yyyy}/${mm}/${safeFilename(filename)}`;
}

function filenameFromPath(pathname) {
  return safeFilename(decodeURIComponent(pathname.split('/').pop() || 'image.jpg'));
}

export function isWpUploadsPath(pathname) {
  return pathname.startsWith('/wp-content/uploads/');
}

export function isLocalAssetPath(pathname) {
  return (
    isWpUploadsPath(pathname) ||
    pathname.startsWith('/images/') ||
    pathname.startsWith('/wp-assets/') ||
    pathname.startsWith('/favicon')
  );
}

export function isCmsMediaPath(pathname) {
  return (
    pathname.startsWith('/media/') ||
    pathname.startsWith('/api/media/') ||
    pathname.startsWith('/api/files/')
  );
}

export function looksLikeImageUrl(value) {
  if (!value) return false;
  if (/\.(avif|gif|jpe?g|png|svg|webp|bmp|tiff?)($|\?)/i.test(value)) return true;
  if (isCmsMediaPath(value) || isLocalAssetPath(value)) return true;
  if (isHttp(value) && /\/(media|uploads|files|images|wp-content)\//i.test(value)) return true;
  return false;
}

/**
 * Always return a same-origin path. Never leave a CMS or localhost host
 * in the HTML, so Workers deploy URLs match Takenweb.
 */
export function resolveMediaUrl(input, fallback = FALLBACK_IMAGE, date) {
  let src = typeof input === 'string' ? input.trim() : '';
  if (!src) return fallback;
  src = src.replace(/\\/g, '/');
  if (src.startsWith('//')) src = `https:${src}`;

  if (isHttp(src)) {
    try {
      const url = new URL(src);
      if (isWpUploadsPath(url.pathname) || isLocalAssetPath(url.pathname)) {
        return url.pathname;
      }
      if (isCmsMediaPath(url.pathname)) {
        return wpUploadsPath(filenameFromPath(url.pathname), date);
      }
      if (looksLikeImageUrl(src)) {
        return wpUploadsPath(filenameFromPath(url.pathname), date);
      }
      return fallback;
    } catch {
      return fallback;
    }
  }

  const path = src.startsWith('/') ? src : `/${src}`;
  if (isLocalAssetPath(path)) return path.split('?')[0];
  if (isCmsMediaPath(path)) return wpUploadsPath(filenameFromPath(path), date);
  if (looksLikeImageUrl(path)) return wpUploadsPath(filenameFromPath(path), date);
  return fallback;
}

export function fetchSourceUrl(input, date) {
  const src = typeof input === 'string' ? input.trim() : '';
  if (!src) return '';
  if (isHttp(src)) return src;
  const path = src.startsWith('/') ? src : `/${src}`;
  const origin = cmsOrigin();
  if (isCmsMediaPath(path) && origin) return `${origin}${path}`;
  if (isLocalAssetPath(path)) return path;
  if (origin) return `${origin}${path}`;
  return path;
}

export { cmsOrigin };
