#!/usr/bin/env python3
"""Migrate all product guide pages from live site into structured JSON + images."""

from __future__ import annotations

import html as html_lib
import json
import re
import ssl
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag

SITE = "https://interieurdesignerweb.nl"
BASE = Path(__file__).resolve().parent.parent
PRODUCTS_JSON = BASE / "src" / "data" / "products.json"
OUT_DIR = BASE / "src" / "data" / "product-guides"
IMG_ROOT = BASE / "public" / "images" / "products"
PUBLIC = BASE / "public"

SSL_CTX = ssl.create_default_context()
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)

SKIP_H2 = {
    "veel gestelde vragen",
    "onze laatste woorden",
    "auteur",
    "laatste artikelen",
}


def fetch(url: str, binary: bool = False, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90, context=SSL_CTX) as resp:
                data = resp.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"  fetch fail ({attempt + 1}/{retries}) {url}: {exc}")
            if attempt == retries - 1:
                return b"" if binary else ""
            time.sleep(1.2 * (attempt + 1))
    return b"" if binary else ""


def decode(text: str) -> str:
    return html_lib.unescape(text or "").strip()


def clean_text(node) -> str:
    if node is None:
        return ""
    text = node.get_text(" ", strip=True) if hasattr(node, "get_text") else str(node)
    text = re.sub(r"\s+", " ", text).strip()
    return decode(text)


def slugify_id(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:80] or "item"


def download_image(url: str, slug: str, index: int) -> str:
    """Prefer local copies for site assets; keep remote CDN URLs as-is for speed."""
    if not url or url.startswith("data:"):
        return url or ""
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url

    # Already local public path
    if url.startswith("/") and not url.startswith("//"):
        return url

    # Hotlink external product images (bol CDN / myfreeimagehost) — avoid slow downloads
    if "myfreeimagehost.com" in url or "bol.com" in url or "media.s-bol.com" in url:
        return url

    if url.startswith(SITE):
        local = url[len(SITE) :]
        # Keep wp-content / images paths as site-relative
        if local.startswith("/wp-content/") or local.startswith("/images/"):
            return local

    # Fallback: try a quick local download for remaining assets
    dest_dir = IMG_ROOT / slug
    dest_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(url)
    name = Path(parsed.path).name or f"img-{index}"
    name = re.sub(r"[^a-zA-Z0-9._-]", "-", name)
    if not Path(name).suffix:
        name = f"{name}.jpg"
    dest = dest_dir / f"{index:02d}-{name}"
    public_path = "/" + dest.relative_to(PUBLIC).as_posix()
    if dest.exists() and dest.stat().st_size > 0:
        return public_path
    data = fetch(url, binary=True)
    if not data:
        return url
    dest.write_bytes(data)
    return public_path


def extract_meta(soup: BeautifulSoup) -> dict:
    title_el = soup.find("title")
    title = decode(title_el.get_text()) if title_el else ""
    title = re.sub(r"\s*\|\s*Vind ze hier\s*$", "", title).strip()

    desc_el = soup.find("meta", attrs={"name": "description"})
    description = decode(desc_el.get("content", "")) if desc_el else ""

    og = soup.find("meta", attrs={"property": "og:image"})
    og_image = og.get("content", "") if og else ""
    if og_image.startswith(SITE):
        og_image = og_image[len(SITE) :]

    return {"title": title, "description": description, "ogImage": og_image or "/images/2023/02/image-2.jpg"}


def extract_breadcrumbs(main: Tag) -> list[dict]:
    crumbs = [{"label": "Home", "href": "/"}]
    for li in main.select(".zbmp-breadcrumb li"):
        a = li.find("a")
        name = li.find(attrs={"itemprop": "name"})
        label = clean_text(name or a or li)
        if not label or label.lower() == "home":
            continue
        href = a.get("href") if a else None
        if href and href.startswith(SITE):
            href = href[len(SITE) :]
        crumbs.append({"label": label, "href": href})
    return crumbs


def extract_faqs(main: Tag) -> list[dict]:
    faqs = []
    seen = set()
    for item in main.select(".elementor-accordion-item"):
        title = item.select_one(".elementor-tab-title, .elementor-accordion-title, a.elementor-accordion-title")
        body = item.select_one(".elementor-tab-content, .elementor-accordion-content")
        if not title or not body:
            continue
        q = clean_text(title)
        # strip icon / expand markers
        q = re.sub(r"^\s*[+\-–—]\s*", "", q)
        a_html = "".join(str(c) for c in body.children if not isinstance(c, NavigableString) or c.strip())
        a_text = clean_text(body)
        if not q or not a_text or q.lower() in seen:
            continue
        seen.add(q.lower())
        # Prefer structured paragraphs
        paras = [clean_text(p) for p in body.find_all("p") if clean_text(p)]
        faqs.append({"question": q, "answer": paras if paras else [a_text]})
    return faqs


def extract_author(main: Tag) -> dict | None:
    box = main.select_one(".elementor-author-box, .elementor-widget-author-box")
    if not box:
        return None
    name_el = box.select_one(".elementor-author-box__name, .elementor-author-box__name a")
    bio_el = box.select_one(".elementor-author-box__bio")
    img_el = box.select_one("img")
    name = clean_text(name_el) or "Jacob Jones"
    bio = clean_text(bio_el)
    image = img_el.get("src") if img_el else ""
    return {"name": name, "bio": bio, "image": image}


def is_product_heading(text: str) -> bool:
    t = text.strip().lower()
    if not t or t in SKIP_H2:
        return False
    if t.startswith("een mooi interieur"):
        return False
    if t.startswith("beste producten"):
        return False
    return True


def extract_products(main: Tag, slug: str) -> list[dict]:
    products = []
    headings = main.select("h2.elementor-heading-title")
    for i, h2 in enumerate(headings):
        name = clean_text(h2)
        if not is_product_heading(name):
            continue

        # Walk following siblings within page to find the content section
        section = h2.find_parent(class_=re.compile(r"elementor-top-section"))
        content_section = None
        if section:
            nxt = section.find_next_sibling()
            while nxt and content_section is None:
                if isinstance(nxt, Tag) and "elementor-top-section" in (nxt.get("class") or []):
                    # stop if next product heading appears first
                    next_h2 = nxt.select_one("h2.elementor-heading-title")
                    if next_h2 and is_product_heading(clean_text(next_h2)):
                        break
                    if nxt.select_one("a[href*='partner.bol.com'], .elementor-star-rating, img"):
                        content_section = nxt
                        break
                nxt = nxt.find_next_sibling()

        search_root = content_section or (section.find_next("section") if section else h2.parent)

        img = ""
        rating = 5.0
        description = ""
        affiliate = ""

        if search_root:
            img_el = search_root.find("img")
            if img_el and img_el.get("src"):
                img = download_image(img_el["src"], slug, len(products) + 1)

            rating_el = search_root.select_one(".elementor-screen-only, [itemprop='ratingValue']")
            if rating_el:
                m = re.search(r"(\d+(?:[.,]\d+)?)", clean_text(rating_el))
                if m:
                    rating = float(m.group(1).replace(",", "."))

            # description: first substantial text-editor paragraph block without only an image
            for te in search_root.select(".elementor-widget-text-editor .elementor-widget-container"):
                if te.find("img") and not clean_text(te):
                    continue
                paras = [clean_text(p) for p in te.find_all("p")]
                paras = [p for p in paras if p and len(p) > 40]
                if paras:
                    description = "\n\n".join(paras)
                    break
            if not description:
                description = clean_text(search_root.select_one(".elementor-widget-text-editor"))

            btn = search_root.select_one("a[href*='partner.bol.com'], a.elementor-button")
            if btn and btn.get("href"):
                affiliate = html_lib.unescape(btn["href"])

        products.append(
            {
                "id": slugify_id(name),
                "name": name,
                "image": img,
                "rating": rating,
                "description": description,
                "affiliateUrl": affiliate,
                "affiliateLabel": "Bekijk prijs bij Bol",
            }
        )
    return products


def extract_intro(main: Tag) -> dict:
    heading = ""
    h1 = main.select_one("h1.elementor-heading-title")
    if h1:
        heading = clean_text(h1)

    updated = ""
    for p in main.select(".elementor-widget-text-editor p"):
        t = clean_text(p)
        if t.lower().startswith("laatst bijgewerkt"):
            updated = t
            break

    published = ""
    for t in main.find_all(string=re.compile(r"Gepubliceerd op", re.I)):
        published = clean_text(t)
        break

    # Intro body: text editor before first product h2
    intro_paras: list[str] = []
    intro_sections: list[dict] = []

    first_product = None
    for h2 in main.select("h2.elementor-heading-title"):
        if is_product_heading(clean_text(h2)):
            first_product = h2
            break

    # Collect from early text widgets
    for te in main.select(".elementor-widget-text-editor .elementor-widget-container"):
        if first_product and te.find_parent(class_=re.compile("elementor-top-section")):
            sec = te.find_parent(class_=re.compile("elementor-top-section"))
            prod_sec = first_product.find_parent(class_=re.compile("elementor-top-section"))
            if sec and prod_sec and (sec is prod_sec or list(sec.parents).count(prod_sec)):
                pass
            # stop once we're past first product section
            if prod_sec and sec and getattr(sec, "sourceline", 0) and getattr(prod_sec, "sourceline", 0):
                if sec.sourceline and prod_sec.sourceline and sec.sourceline >= prod_sec.sourceline:
                    continue

        # Skip updated-only paragraphs
        texts = []
        current_h2 = None
        for child in te.children:
            if isinstance(child, Tag) and child.name in ("h2", "h3"):
                if texts and current_h2:
                    intro_sections.append({"heading": current_h2, "paragraphs": texts})
                    texts = []
                elif texts and not current_h2:
                    intro_paras.extend(texts)
                    texts = []
                current_h2 = clean_text(child)
                continue
            if isinstance(child, Tag) and child.name == "p":
                t = clean_text(child)
                if not t or t.lower().startswith("laatst bijgewerkt"):
                    continue
                texts.append(t)
        if texts:
            if current_h2:
                intro_sections.append({"heading": current_h2, "paragraphs": texts})
            else:
                intro_paras.extend(texts)

    # Lead text sometimes stuffed into a heading widget as <p class="elementor-heading-title">
    for hw in main.select(".elementor-widget-heading .elementor-heading-title"):
        if hw.name == "h1":
            continue
        t = clean_text(hw)
        if len(t) > 80 and not is_product_heading(t) and t.lower() not in SKIP_H2:
            if t not in intro_paras:
                intro_paras.insert(0, t)

    # Deduplicate while preserving order
    def dedupe(items: list[str]) -> list[str]:
        seen = set()
        out = []
        for x in items:
            key = x.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(x)
        return out

    intro_paras = dedupe(intro_paras)

    return {
        "heading": heading,
        "updated": updated,
        "published": published,
        "lead": intro_paras,
        "sections": intro_sections,
    }


def migrate_slug(slug: str) -> dict | None:
    url = f"{SITE}/{slug}/"
    print(f"Migrating {slug}...")
    html = fetch(url)
    if not html:
        print(f"  SKIP empty: {slug}")
        return None

    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main") or soup

    meta = extract_meta(soup)
    intro = extract_intro(main)
    products = extract_products(main, slug)
    faqs = extract_faqs(main)
    author = extract_author(main)
    breadcrumbs = extract_breadcrumbs(main)

    if author and author.get("image"):
        author["image"] = download_image(author["image"], slug, 0)

    if not products:
        print(f"  WARN no products parsed for {slug}")

    guide = {
        "slug": slug,
        "title": meta["title"],
        "description": meta["description"],
        "ogImage": meta["ogImage"],
        "heading": intro["heading"] or meta["title"],
        "updated": intro["updated"],
        "published": intro["published"],
        "breadcrumbs": breadcrumbs,
        "lead": intro["lead"],
        "introSections": intro["sections"],
        "products": products,
        "faqs": faqs,
        "author": author,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{slug}.json"
    out.write_text(json.dumps(guide, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  OK {len(products)} products, {len(faqs)} faqs -> {out.name}")
    return guide


def main():
    products = json.loads(PRODUCTS_JSON.read_text(encoding="utf-8"))
    slugs = [p["slug"] for p in products]
    if "beste-donzen-dekbed" not in slugs:
        slugs.append("beste-donzen-dekbed")

    ok = 0
    for i, slug in enumerate(slugs, 1):
        out = OUT_DIR / f"{slug}.json"
        if out.exists() and out.stat().st_size > 500:
            print(f"[{i}/{len(slugs)}] SKIP existing {slug}")
            ok += 1
            continue
        print(f"[{i}/{len(slugs)}]", end=" ", flush=True)
        if migrate_slug(slug):
            ok += 1
        time.sleep(0.2)

    print(f"\nDone. Migrated {ok}/{len(slugs)} guides -> {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
