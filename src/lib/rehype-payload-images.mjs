import { resolveMediaUrl } from './media-url.mjs';

function altFromSrc(src) {
  try {
    const path = /^https?:\/\//i.test(src) ? new URL(src).pathname : src;
    const name = decodeURIComponent((path.split('/').pop() || '').replace(/\.[a-z0-9]+$/i, ''));
    const cleaned = name.replace(/[-_]+/g, ' ').replace(/\d{3,4}x\d{3,4}/g, '').trim();
    if (!cleaned) return 'Afbeelding bij artikel';
    return cleaned.charAt(0).toUpperCase() + cleaned.slice(1);
  } catch {
    return 'Afbeelding bij artikel';
  }
}

function walk(node, visit) {
  visit(node);
  if (Array.isArray(node?.children)) {
    for (const child of node.children) walk(child, visit);
  }
}

export function rehypePayloadImages() {
  return (tree) => {
    walk(tree, (node) => {
      if (node?.type !== 'element' || node.tagName !== 'img') return;
      const props = node.properties || (node.properties = {});
      if (typeof props.src === 'string') {
        props.src = resolveMediaUrl(props.src);
      }
      const alt = typeof props.alt === 'string' ? props.alt.trim() : '';
      if (!alt) {
        props.alt = altFromSrc(String(props.src || ''));
      }
    });
  };
}
