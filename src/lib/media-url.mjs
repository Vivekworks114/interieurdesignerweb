/**
 * Resolve WP uploads and Payload CMS Media (R2).
 * Bare R2 keys 404; they must be rewritten to /tenants/interieurdesignerweb/{file}.
 * Do not rewrite working R2 URLs into invented /wp-content/uploads/YYYY/MM/ paths.
 */

export const TENANT_SLUG = 'interieurdesignerweb';
export const R2_PUBLIC = 'https://pub-d4024ad3e57841448e0ee58a19abe46b.r2.dev';
export const FALLBACK_IMAGE = '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg';

const UNIQUE_STOCK = [
  '/wp-content/uploads/2025/12/pexels-pixabay-271639.jpg',
  '/wp-content/uploads/2025/12/pexels-castorlystock-3609956.jpg',
  '/wp-content/uploads/2025/12/pexels-christa-grover-977018-1910472-6.jpg',
  '/wp-content/uploads/2025/11/Laminaatvloer.jpg',
  '/wp-content/uploads/2025/10/pexels-itsterrymag-2635038-3.jpg',
  '/wp-content/uploads/2025/07/window-2628519_1280.jpg',
  '/wp-content/uploads/2023/02/image-2.jpg',
  '/wp-content/uploads/2024/05/stolmeijer-vijfhuizen-01-web-1536x864.webp',
];

const IMAGE_EXT = /\.(avif|gif|jpe?g|png|svg|webp|bmp|tiff?)($|\?)/i;

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

export function isLocalBlogCoverPath(src) {
  return /^\/?images\/blog\/cover-/i.test(String(src || '').trim());
}

export function isR2Host(hostname = '') {
  const host = hostname.toLowerCase();
  return host.endsWith('.r2.dev') || host.includes('r2.cloudflarestorage.com');
}

/** https://xxx.r2.dev/file.jpg → https://xxx.r2.dev/tenants/interieurdesignerweb/file.jpg */
export function repairTenantR2Url(url, tenantSlug = TENANT_SLUG) {
  const trimmed = String(url || '').trim();
  if (!trimmed || !tenantSlug || !isHttp(trimmed)) return trimmed;
  if (trimmed.includes(`/tenants/${tenantSlug}/`)) return trimmed;

  try {
    const parsed = new URL(trimmed);
    if (!isR2Host(parsed.hostname)) return trimmed;
    const path = parsed.pathname.replace(/^\/+/, '');
    if (!path || path.includes('/')) return trimmed;
    parsed.pathname = `/tenants/${tenantSlug}/${path}`;
    return parsed.toString();
  } catch {
    return trimmed;
  }
}

function hashSlug(slug) {
  let h = 0;
  for (const ch of String(slug || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return h;
}

export function uniqueStockCover(slug) {
  return UNIQUE_STOCK[hashSlug(slug) % UNIQUE_STOCK.length];
}

export function looksLikeImageUrl(value) {
  if (!value) return false;
  if (IMAGE_EXT.test(value)) return true;
  if (isCmsMediaPath(value) || isLocalAssetPath(value)) return true;
  if (isHttp(value) && /\/(media|uploads|files|images|wp-content|tenants)\//i.test(value)) return true;
  if (isHttp(value) && /\.r2\.dev\//i.test(value)) return true;
  return false;
}

/**
 * Return a usable img src: local WP path, local asset, or repaired R2 URL.
 */
export function resolveMediaUrl(input, fallback = '', date) {
  let src = typeof input === 'string' ? input.trim() : '';
  if (!src) return fallback;
  src = src.replace(/\\/g, '/');
  if (src.startsWith('//')) src = `https:${src}`;

  if (isHttp(src)) {
    const repaired = repairTenantR2Url(src);
    try {
      const url = new URL(repaired);
      if (isR2Host(url.hostname)) return repaired;
      if (isWpUploadsPath(url.pathname) || isLocalAssetPath(url.pathname)) {
        return url.pathname.split('?')[0];
      }
      if (isCmsMediaPath(url.pathname)) {
        const file = filenameFromPath(url.pathname);
        return `${R2_PUBLIC}/tenants/${TENANT_SLUG}/${file}`;
      }
      if (IMAGE_EXT.test(url.pathname)) return repaired;
      return fallback;
    } catch {
      return fallback;
    }
  }

  const path = src.startsWith('/') ? src : `/${src}`;
  if (isLocalBlogCoverPath(path)) return fallback;
  if (isLocalAssetPath(path)) return path.split('?')[0];
  if (isCmsMediaPath(path)) {
    const file = filenameFromPath(path);
    return `${R2_PUBLIC}/tenants/${TENANT_SLUG}/${file}`;
  }
  if (looksLikeImageUrl(path)) return path.split('?')[0];
  return fallback;
}

export function fetchSourceUrl(input, date) {
  const src = typeof input === 'string' ? input.trim() : '';
  if (!src) return '';
  if (isHttp(src)) return repairTenantR2Url(src);
  const path = src.startsWith('/') ? src : `/${src}`;
  const origin = cmsOrigin();
  if (isCmsMediaPath(path) && origin) return `${origin}${path}`;
  if (isLocalAssetPath(path)) return path;
  if (origin) return `${origin}${path}`;
  return path;
}

export { cmsOrigin };
