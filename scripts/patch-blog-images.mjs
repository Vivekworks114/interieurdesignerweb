import { readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const dir = join(dirname(fileURLToPath(import.meta.url)), '..', 'src', 'content', 'blog');

const bySlug = {
  'betrouwbaar-bouwbedrijf-voor-jouw-droomhuis': {
    image: '/wp-content/uploads/2024/09/Bouwbedrijf.jpeg',
    alt: 'Bouw van een woning door een professioneel bouwbedrijf',
  },
  'op-maat-gemaakt-ontdek-de-kunst-van-de-meubelmakerij': {
    image: '/wp-content/uploads/2024/08/meubels.jpeg',
    alt: 'Op maat gemaakt meubelwerk in een woonkamer',
  },
  '7-kenmerken-van-een-luxe-keuken-die-echt-het-verschil-maken': {
    image: '/wp-content/uploads/2024/05/stolmeijer-vijfhuizen-01-web.webp',
    alt: 'Luxe moderne keuken met strak design',
  },
  'multiplank-eiken-de-voordelen-van-deze-veelzijdige-vloeroptie': {
    image: '/wp-content/uploads/2025/11/Laminaatvloer.jpg',
    alt: 'Eiken houten vloer in een woonruimte',
  },
  'de-onmisbare-keuze-voor-jouw-nieuwe-vloer': {
    image: '/wp-content/uploads/2025/11/Laminaatvloer.jpg',
    alt: 'Laminaatvloer in een modern interieur',
  },
  'de-evolutie-van-energie-hoe-kiezen-we-duurzaam': {
    image: '/wp-content/uploads/2026/08/duurzame-energie-woning.jpg',
    alt: 'Zonnepanelen op een woning voor duurzame energie',
  },
  'moderne-keukens-trends-en-innovaties-voor-2025': {
    image: '/wp-content/uploads/2024/05/stolmeijer-vijfhuizen-01-web.webp',
    alt: 'Moderne keuken met eigentijdse inrichting',
  },
  'de-ideale-inrichting-van-een-recreatiewoning-zo-creeer-je-maximaal-wooncomfort': {
    image: '/wp-content/uploads/2026/08/recreatiewoning-interieur.jpg',
    alt: 'Sfeervol interieur van een recreatiewoning',
  },
  'speelgoed-kiezen-voor-een-kind-van-2-jaar-dat-ook-in-huis-past': {
    image: '/wp-content/uploads/2026/08/speelgoed-peuter-interieur.jpg',
    alt: 'Houten speelgoed dat past in een stijlvol interieur',
  },
  'hello-world': {
    image: '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg',
    alt: 'Sfeervol interieur met natuurlijk licht',
  },
  'hello-world-2': {
    image: '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg',
    alt: 'Sfeervol interieur met natuurlijk licht',
  },
  'hello-world-2-2': {
    image: '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg',
    alt: 'Sfeervol interieur met natuurlijk licht',
  },
  'hello-world-2-2-2': {
    image: '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg',
    alt: 'Sfeervol interieur met natuurlijk licht',
  },
  'hello-world-2-2-2-2': {
    image: '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg',
    alt: 'Sfeervol interieur met natuurlijk licht',
  },
  'goedkope-oliekachels-vergelijken-waar-moet-je-op-letten-bij-het-maken-van-de-juiste-keuze': {
    alt: 'Woonkamer met groot raam en warme sfeer',
  },
  'welke-regendouche-past-bij-jouw-badkamer': {
    alt: 'Moderne badkamer met regendouche',
  },
  'hoe-een-waterkoeler-past-in-je-interieur': {
    alt: 'Waterkoeler in een strak interieur',
  },
  'palmboom-vuurplaat': {
    alt: 'Groene buitenruimte bij de Palmboom Vuurplaat in Rotterdam',
  },
  'de-belangrijke-rol-van-een-bouwbedrijf-in-de-moderne-maatschappij': {
    alt: 'Bouwbedrijf aan het werk op een bouwplaats',
  },
  'budgetvriendelijke-ideeen-voor-een-kleine-keuken': {
    alt: 'Compacte keuken in een woning',
  },
  'ruimtebesparende-oplossingen-voor-kleine-appartementen': {
    alt: 'Slim ingericht klein appartement',
  },
  'behoud-je-tuin-maar-vergroot-je-huis-met-een-glazen-schuifwand': {
    alt: 'Glazen schuifwand tussen woning en tuin',
  },
  'deurknoppen-kiezen-dit-past-bij-jouw-interieur': {
    alt: 'Slaapkamerinterieur met aandacht voor details zoals deurbeslag',
  },
  'sleutelfactoren-voor-een-duurzame-en-stijlvolle-vloerkeuze': {
    alt: 'Stijlvolle duurzame vloer in een woonkamer',
  },
  'douchebak-vergelijken-op-kwaliteit': {
    alt: 'Badkamer met douchebak van hoge kwaliteit',
  },
  'tips-om-de-ruimte-kleine-appartementen-te-maximaliseren': {
    alt: 'Licht interieur in een klein appartement',
  },
  'de-kookwinkel-een-paradijs-voor-iedere-kookliefhebber': {
    alt: 'Keukenwinkel met kookgerei en inspiratie',
  },
  'de-beste-materialen-voor-tuinhuis-deuren': {
    alt: 'Tuin met zwembad en bijgebouw',
  },
  'een-professionele-website-laten-maken-door-bink-online': {
    alt: 'Laptop op een bureau bij het maken van een website',
  },
  'hoe-je-met-slimme-keuzes-je-interieur-laat-stralen': {
    alt: 'Stijlvol interieur met doordachte verlichting',
  },
  'moderne-keukens-het-hart-van-uw-huis-met-db-keukens': {
    alt: 'Moderne keuken als hart van het huis',
  },
  'waar-moet-je-op-letten-bij-het-kopen-van-een-auto': {
    alt: 'Auto bekijken bij aankoop',
  },
  'zo-helpt-een-waterkoeler-bij-een-gezondere-leefstijl': {
    alt: 'Waterkoeler voor dagelijks gebruik thuis',
  },
};

function yamlQuote(value) {
  return `"${value.replace(/"/g, '\\"')}"`;
}

function upsertLine(block, key, value) {
  const line = `${key}: ${yamlQuote(value)}`;
  const re = new RegExp(`^${key}:.*$`, 'm');
  if (re.test(block)) return block.replace(re, line);
  return `${block.trimEnd()}\n${line}`;
}

for (const file of readdirSync(dir).filter((f) => f.endsWith('.mdx') || f.endsWith('.md'))) {
  const full = join(dir, file);
  const raw = readFileSync(full, 'utf8').replace(/\r\n/g, '\n');
  const match = raw.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!match) continue;
  let fm = match[1];
  let body = match[2];
  const slugMatch = fm.match(/^slug:\s*(.+)$/m);
  const slug = slugMatch ? slugMatch[1].trim() : file.replace(/\.mdx?$/, '');
  const titleMatch = fm.match(/^title:\s*["']?(.+?)["']?\s*$/m);
  const title = titleMatch ? titleMatch[1].replace(/^"|"$/g, '') : slug;
  const meta = bySlug[slug] || {};

  const existingImage = fm.match(/^(?:featuredImage|image):\s*(.+)$/m);
  let image = meta.image;
  if (!image && existingImage) {
    image = existingImage[1].trim().replace(/^["']|["']$/g, '');
  }
  if (!image || image.startsWith('https://www.lobbes.nl')) {
    image = meta.image || '/wp-content/uploads/2024/03/pexels-skitterphoto-9312-scaled.jpg';
  }
  const alt = meta.alt || title;

  fm = upsertLine(fm, 'featuredImage', image);
  fm = upsertLine(fm, 'image', image);
  fm = upsertLine(fm, 'imageAlt', alt);
  fm = upsertLine(fm, 'featuredImageAlt', alt);

  body = body.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (_, a, src) => {
    const nextAlt = a && a.trim() ? a.trim() : alt;
    return `![${nextAlt}](${src})`;
  });

  writeFileSync(full, `---\n${fm.trim()}\n---\n${body.startsWith('\n') ? body : `\n${body}`}`);
  console.log('updated', slug);
}
