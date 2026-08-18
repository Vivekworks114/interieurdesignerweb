import { mkdirSync, writeFileSync, existsSync, readdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const origin = 'https://interieurdesignerweb.nl';

const extraDownloads = [
  {
    url: 'https://images.pexels.com/photos/1571460/pexels-photo-1571460.jpeg?auto=compress&cs=tinysrgb&w=1600',
    dest: 'public/wp-content/uploads/2026/08/recreatiewoning-interieur.jpg',
  },
  {
    url: 'https://images.pexels.com/photos/3662667/pexels-photo-3662667.jpeg?auto=compress&cs=tinysrgb&w=1600',
    dest: 'public/wp-content/uploads/2026/08/speelgoed-peuter-interieur.jpg',
  },
  {
    url: 'https://images.pexels.com/photos/356049/pexels-photo-356049.jpeg?auto=compress&cs=tinysrgb&w=1600',
    dest: 'public/wp-content/uploads/2026/08/duurzame-energie-woning.jpg',
  },
];

function walkFiles(dir, acc = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === 'dist' || entry.name === '.git') continue;
      walkFiles(full, acc);
    } else if (/\.(astro|md|mdx|json|ts|css|html)$/i.test(entry.name)) {
      acc.push(full);
    }
  }
  return acc;
}

function collectPaths() {
  const files = walkFiles(join(root, 'src'));
  const paths = new Set();
  const re = /(?:src|href|image|ogImage|featuredImage|heroImage)=["']([^"']+)["']|["'](\/(?:wp-content|images)\/[^"']+)["']/g;
  for (const file of files) {
    const text = readFileSync(file, 'utf8');
    let m;
    while ((m = re.exec(text))) {
      const value = m[1] || m[2];
      if (!value) continue;
      if (value.startsWith('/wp-content/') || value.startsWith('/images/')) {
        paths.add(value.split('?')[0]);
      }
    }
  }
  paths.add('/wp-content/uploads/2023/02/Frame-700-1.svg');
  paths.add('/wp-content/uploads/2023/02/cropped-Group-78-32x32.png');
  paths.add('/wp-content/uploads/2023/02/cropped-Group-78-180x180.png');
  paths.add('/images/2023/02/Frame-700-1.svg');
  paths.add('/images/2023/02/cropped-Group-78-32x32.png');
  paths.add('/images/2023/02/cropped-Group-78-180x180.png');
  paths.add('/images/2023/02/image-1-3.png');
  return [...paths];
}

async function download(url, destRel) {
  const dest = join(root, destRel.replace(/^\//, destRel.startsWith('public') ? '' : `public${destRel.startsWith('/') ? '' : '/'}`));
  const out = destRel.startsWith('public/') ? join(root, destRel) : join(root, 'public', destRel);
  mkdirSync(dirname(out), { recursive: true });
  if (existsSync(out)) return 'exists';
  const res = await fetch(url, { redirect: 'follow', headers: { 'user-agent': 'Mozilla/5.0 image-sync' } });
  if (!res.ok) return `fail ${res.status}`;
  const buf = Buffer.from(await res.arrayBuffer());
  if (buf.length < 80) return 'too-small';
  writeFileSync(out, buf);
  return `ok ${buf.length}`;
}

async function main() {
  const paths = collectPaths();
  console.log(`Found ${paths.length} local media paths`);
  for (const path of paths) {
    const result = await download(`${origin}${path}`, `public${path}`);
    console.log(path, result);
  }
  for (const item of extraDownloads) {
    const result = await download(item.url, item.dest);
    console.log(item.dest, result);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
