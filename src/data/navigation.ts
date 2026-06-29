export interface NavItem {
  label: string;
  href: string;
  children?: { label: string; href: string }[];
}

export const mainNavigation: NavItem[] = [
  { label: 'Home', href: '/' },
  {
    label: 'Bedden en beddengoed',
    href: '/bedden-en-beddengoed/',
    children: [
      { label: 'Donzen dekbed', href: '/beste-donzen-dekbed/' },
      { label: 'Boxspring matras', href: '/beste-boxspring-matras/' },
      { label: 'Hoeslaken 90×200', href: '/beste-hoeslaken-90x200/' },
      { label: 'Matrasbeschermer', href: '/beste-matrasbeschermer/' },
      { label: 'Latex hoofdkussen', href: '/beste-latex-hoofdkussen/' },
      { label: '4 seizoenen dekbed', href: '/beste-4-seizoenen-dekbed/' },
      { label: 'Satijnen dekbedovertrek', href: '/beste-satijnen-dekbedovertrek/' },
      { label: 'Katoenen dekbedovertrek', href: '/beste-katoenen-dekbedovertrek/' },
      { label: 'Boxspring met opbergruimte', href: '/beste-boxspring-met-opbergruimte/' },
      { label: 'Hoogslaper met bureau en kast', href: '/beste-hoogslaper-met-bureau-en-kast/' },
    ],
  },
  {
    label: 'Elektronica',
    href: '/elektronica/',
    children: [
      { label: 'TV', href: '/beste-tv/' },
      { label: '32 inch tv', href: '/beste-32-inch-tv/' },
      { label: '55 inch tv', href: '/beste-55-inch-tv/' },
      { label: 'Hifi speakers', href: '/beste-hifi-speakers/' },
      { label: 'TV box Android', href: '/beste-tv-box-android/' },
      { label: 'Radio CD speler', href: '/beste-radio-cd-speler/' },
      { label: 'Speaker receiver', href: '/beste-speaker-receiver/' },
      { label: 'Beamer voor thuis', href: '/beste-beamer-voor-thuis/' },
      { label: 'Projectiescherm beamer', href: '/beste-projectiescherm-beamer/' },
      { label: 'Soundbar met subwoofer', href: '/beste-soundbar-met-subwoofer/' },
    ],
  },
  {
    label: 'Meubelen',
    href: '/meubelen/',
    children: [
      { label: 'Poef', href: '/beste-poef/' },
      { label: 'Draaistoel', href: '/beste-draaistoel/' },
      { label: 'Grote zitzak', href: '/beste-grote-zitzak/' },
      { label: 'Ronde bijzettafel', href: '/beste-ronde-bijzettafel/' },
      { label: 'Open boekenkast', href: '/beste-open-boekenkast/' },
      { label: 'Hangstoel binnen', href: '/beste-hangstoel-binnen/' },
      { label: 'Schommelstoelen', href: '/beste-schommelstoelen/' },
      { label: 'Smalle boekenkast', href: '/beste-smalle-boekenkast/' },
      { label: 'Bartafel met krukken', href: '/beste-bartafel-met-krukken/' },
      { label: 'Kledingkast kinderkamer', href: '/beste-kledingkast-kinderkamer/' },
    ],
  },
  { label: 'Blog', href: '/blog/' },
  { label: 'Over ons', href: '/over-ons/' },
  { label: 'Contact', href: '/contact/' },
];
