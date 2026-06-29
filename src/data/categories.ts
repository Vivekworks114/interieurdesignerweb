import { mainNavigation } from './navigation';

export interface CategoryPage {
  slug: string;
  title: string;
  description: string;
}

export const categoryPages: CategoryPage[] = [
  {
    slug: 'bedden-en-beddengoed',
    title: 'Bedden en beddengoed',
    description: 'Ontdek de beste bedden, matrassen, dekbedden en beddengoed voor een comfortabele nachtrust.',
  },
  {
    slug: 'elektronica',
    title: 'Elektronica',
    description: 'Vergelijk de beste tv\'s, speakers, beamers en andere elektronica voor in huis.',
  },
  {
    slug: 'meubelen',
    title: 'Meubelen',
    description: 'Vind de beste meubels voor je woonkamer, slaapkamer en andere ruimtes in huis.',
  },
  {
    slug: 'verkoeling-en-verwarming',
    title: 'Verkoeling en verwarming',
    description: 'De beste airco\'s, kachels, ventilatoren en verwarmingsoplossingen voor je woning.',
  },
  {
    slug: 'woonaccessoires',
    title: 'Woonaccessoires',
    description: 'Stylische woonaccessoires om je interieur compleet te maken.',
  },
  {
    slug: 'wasmachines-en-accessoires',
    title: 'Wasmachines en accessoires',
    description: 'Alles over wasmachines, drogers en wasruimte-accessoires.',
  },
  {
    slug: 'veiligheid',
    title: 'Veiligheid',
    description: 'Veiligheidsproducten voor een veilig en beschermd thuis.',
  },
];

export function getCategoryItems(slug: string) {
  const navItem = mainNavigation.find((item) => item.href === `/${slug}/`);
  if (navItem?.children) return navItem.children;

  const categoryProducts: Record<string, string[]> = {
    'verkoeling-en-verwarming': [
      'beste-aircooler', 'beste-kleine-mobiele-airco', 'beste-infrarood-verwarming',
      'beste-elektrische-onderdeken', 'beste-elektrische-kachel-woonkamer',
      'beste-energiezuinige-elektrische-kachel', 'beste-elektrische-bovendeken',
      'beste-radiatorombouw', 'beste-ventilator', 'beste-cv-ketel',
    ],
    'woonaccessoires': [
      'beste-oosterse-hanglamp', 'beste-kunstkerstboom-met-verlichting',
      'beste-douchekop-met-slang', 'beste-hoofdkussen-zijslaper',
    ],
    'wasmachines-en-accessoires': [
      'beste-lekbak-wasmachine', 'beste-inbouw-wasmachine', 'beste-bovenlader-wasmachine',
      'beste-kast-voor-wasmachine-en-droger', 'beste-elektrische-droogrek',
      'beste-tussenstuk-wasmachine-droger', 'beste-wasmand-met-deksel',
      'beste-dubbele-wasmand',
    ],
    'veiligheid': [
      'beste-beveiligingscamera', 'beste-bewegingssensoren', 'beste-prullenbak-met-sensor',
    ],
  };

  const slugs = categoryProducts[slug] ?? [];
  return slugs.map((s) => ({
    label: s.replace('beste-', '').replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
    href: `/${s}/`,
  }));
}

export function getCategoryBySlug(slug: string) {
  return categoryPages.find((c) => c.slug === slug);
}
