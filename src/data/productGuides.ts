export interface ProductGuideCrumb {
  label: string;
  href?: string | null;
}

export interface ProductGuideItem {
  id: string;
  name: string;
  image: string;
  rating: number;
  description: string;
  affiliateUrl: string;
  affiliateLabel: string;
}

export interface ProductGuideFaq {
  question: string;
  answer: string[];
}

export interface ProductGuideAuthor {
  name: string;
  bio: string;
  image?: string;
}

export interface ProductGuide {
  slug: string;
  title: string;
  description: string;
  ogImage: string;
  heading: string;
  updated?: string;
  published?: string;
  breadcrumbs: ProductGuideCrumb[];
  lead: string[];
  introSections: { heading: string; paragraphs: string[] }[];
  products: ProductGuideItem[];
  faqs: ProductGuideFaq[];
  author?: ProductGuideAuthor | null;
}

const modules = import.meta.glob('./product-guides/*.json', { eager: true }) as Record<
  string,
  { default: ProductGuide } | ProductGuide
>;

function unwrap(mod: { default: ProductGuide } | ProductGuide): ProductGuide {
  return 'default' in mod ? mod.default : mod;
}

export function getAllProductGuides(): ProductGuide[] {
  return Object.values(modules).map(unwrap);
}

export function getProductGuide(slug: string): ProductGuide | undefined {
  const key = `./product-guides/${slug}.json`;
  const mod = modules[key];
  return mod ? unwrap(mod) : undefined;
}

export function hasProductGuide(slug: string): boolean {
  return `./product-guides/${slug}.json` in modules;
}
