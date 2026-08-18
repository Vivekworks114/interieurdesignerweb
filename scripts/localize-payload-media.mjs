/**
 * Copy Payload / remote featured images into public/wp-content/uploads/YYYY/MM/
 * so deployed Workers URLs match Takenweb:
 *   https://<site>.workers.dev/wp-content/uploads/2024/10/photo.png
 *
 * Runs automatically before `astro build`.
 */
import { mkdirSync, writeFileSync, existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { fetchSourceUrl, resolveMediaUrl, looksLikeImageUrl } from '../src/lib/media-url.mjs';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const blogDir = join(root, 'src/content/blog');

function loadEnvFile(file) {
  if (!existsSync(file)) return;
  for (const line of readFileSync(file, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([A-Z0-9_]+)=(.*)$/);
    if (m && !process.env[m[1]]) process.env[m[1]] = m[2].replace(/^["']|["']$/g, '');
  }
}

loadEnvFile(join(root, '.env'));
loadEnvFile(join(root, '.env.astropayload'));

function collectUrls(text) {
  const urls = new Set();
  const patterns = [
    /(?:featuredImage|image):\s*["']?([^\s"']+)/g,
    /!\[[^\]]*\]\(([^)]+)\)/g,
    /src=["']([^"']+)["']/g,
  ];
  for (const re of patterns) {
    let m;
    while ((m = re.exec(text))) {
      const value = m[1].trim();
      if (looksLikeImageUrl(value)) urls.add(value);
    }
  }
  return [...urls];
}

async function saveUpload(source, destPath) {
  const out = join(root, 'public', destPath.replace(/^\//, ''));
  mkdirSync(dirname(out), { recursive: true });
  if (existsSync(out)) return 'exists';

  let url = fetchSourceUrl(source);
  if (!url) return 'skip';
  if (url.startsWith('/')) {
    const local = join(root, 'public', url.replace(/^\//, ''));
    if (existsSync(local)) return 'local';
    return 'missing-local';
  }

  const res = await fetch(url, {
    redirect: 'follow',
    headers: { 'user-agent': 'Mozilla/5.0 interieurdesignerweb-media-sync' },
  });
  if (!res.ok) return `fail ${res.status}`;
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length < 80) return 'too-small';
  writeFileSync(out, buf);
  return `ok ${buf.length}`;
}

function rewriteText(text, date) {
  return text.replace(
    /((?:featuredImage|image):\s*)(["']?)([^"'\s]+)\2/g,
    (full, prefix, quote, value) => {
      if (!looksLikeImageUrl(value)) return full;
      const next = resolveMediaUrl(value, value, date);
      return `${prefix}${quote}${next}${quote}`;
    },
  ).replace(/(!\[[^\]]*\]\()([^)]+)(\))/g, (full, open, value, close) => {
    if (!looksLikeImageUrl(value)) return full;
    return `${open}${resolveMediaUrl(value, value, date)}${close}`;
  });
}

async function main() {
  if (!existsSync(blogDir)) return;
  const files = readdirSync(blogDir).filter((f) => /\.mdx?$/.test(f));
  for (const file of files) {
    const full = join(blogDir, file);
    const raw = readFileSync(full, 'utf8');
    const dateMatch = raw.match(/^(?:pubDate|date):\s*["']?([0-9-]+)/m);
    const date = dateMatch ? new Date(dateMatch[1]) : new Date();
    for (const url of collectUrls(raw)) {
      const dest = resolveMediaUrl(url, url, date);
      if (!dest.startsWith('/wp-content/uploads/')) continue;
      const result = await saveUpload(url, dest);
      if (result.startsWith('fail') || result === 'too-small') {
        console.warn(file, url, '→', dest, result);
      }
    }
    const next = rewriteText(raw.replace(/\r\n/g, '\n'), date);
    if (next !== raw.replace(/\r\n/g, '\n')) writeFileSync(full, next);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
