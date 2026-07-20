#!/usr/bin/env python3
"""Convert migrated article HTML into Astro blog Markdown files."""

from __future__ import annotations

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag
from markdownify import markdownify as html_to_md

BASE = Path(__file__).resolve().parent.parent
HTML_DIR = BASE / "src" / "data" / "elementor" / "articles"
META_DIR = BASE / "src" / "data" / "articles"
OUT_DIR = BASE / "src" / "content" / "blog"
BLOG_JSON = BASE / "src" / "data" / "blog-posts.json"


def yaml_escape(value: str) -> str:
    value = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{value}"'


def clean_title(title: str) -> str:
    return re.sub(r"\s*[-|]\s*interieurdesignerweb\.nl.*$", "", title, flags=re.I).strip()


def extract_dates(meta: dict) -> tuple[str, str]:
    published = ""
    modified = ""
    for block in meta.get("jsonLd") or []:
        graph = block.get("@graph") if isinstance(block, dict) else None
        if not graph:
            continue
        for node in graph:
            if not isinstance(node, dict):
                continue
            if node.get("@type") == "Article":
                published = (node.get("datePublished") or "")[:10]
                modified = (node.get("dateModified") or published)[:10]
                break
    return published or "2023-01-01", modified or published or "2023-01-01"


def extract_description(meta: dict, soup: BeautifulSoup) -> str:
    desc = (meta.get("description") or "").strip()
    if desc and "Lees " not in desc[:12]:
        return desc[:220]
    p = soup.select_one(".page-content p, .elementor-widget-text-editor p, .elementor-widget-theme-post-content p")
    if p:
        text = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
        return (text[:180] + "…") if len(text) > 180 else text
    title = clean_title(meta.get("title") or meta.get("slug") or "Artikel")
    return f"Lees {title} op Interieurdesignerweb.nl"


def prepare_content_root(soup: BeautifulSoup) -> Tag | None:
    # Prefer classic Gutenberg content
    page_content = soup.select_one(".page-content")
    if page_content and not page_content.select_one("[data-elementor-type='wp-post']"):
        # remove empty wrappers but keep content
        header = soup.select_one(".page-header")
        root = soup.new_tag("div")
        if header:
            # keep h1 only once via frontmatter; skip header
            pass
        for child in list(page_content.children):
            if isinstance(child, (Tag, NavigableString)):
                root.append(child)
        return root

    # Elementor posts: keep meaningful widgets only
    el = soup.select_one("[data-elementor-type='wp-post']")
    if not el:
        main = soup.select_one("main") or soup
        return main if isinstance(main, Tag) else None

    root = soup.new_tag("div")
    keep_widgets = {
        "theme-post-title",
        "theme-post-featured-image",
        "theme-post-content",
        "text-editor",
        "image",
        "heading",
        "post-info",
    }
    skip_widgets = {
        "author-box",
        "posts",
        "table-of-contents",
        "nav-menu",
    }

    for widget in el.select(".elementor-widget"):
        wtype = (widget.get("data-widget_type") or "").split(".")[0]
        if wtype in skip_widgets:
            continue
        if wtype and wtype not in keep_widgets:
            # keep unknown content-ish widgets unless clearly chrome
            if wtype.startswith("nav") or "menu" in wtype:
                continue
        container = widget.select_one(".elementor-widget-container") or widget
        # Avoid duplicate H1 from theme-post-title (frontmatter has title)
        if wtype in {"theme-post-title", "heading"} and container.find(["h1"]):
            continue
        root.append(BeautifulSoup(str(container), "html.parser"))
    return root


def html_fragment_to_markdown(fragment: Tag) -> str:
    # Normalize images
    for img in fragment.find_all("img"):
        src = img.get("src") or img.get("data-lazy-src") or img.get("data-src")
        if src:
            img["src"] = src
        for attr in list(img.attrs):
            if attr.startswith("data-") or attr in {"srcset", "sizes", "decoding", "fetchpriority", "loading"}:
                del img[attr]
        if not img.get("alt"):
            img["alt"] = ""

    # Drop scripts/styles
    for tag in fragment.find_all(["script", "style", "noscript", "svg"]):
        tag.decompose()

    md = html_to_md(
        str(fragment),
        heading_style="ATX",
        bullets="-",
        strip=["span"],
    )
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"
    return md


def convert_one(slug: str) -> dict | None:
    html_path = HTML_DIR / f"{slug}.html"
    meta_path = META_DIR / f"{slug}.json"
    if not html_path.exists() or not meta_path.exists():
        print(f"  skip missing {slug}")
        return None

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    root = prepare_content_root(soup)
    if root is None:
        print(f"  no content {slug}")
        return None

    title = clean_title(meta.get("title") or slug)
    # Prefer visible h1 if cleaner
    h1 = soup.select_one("h1.entry-title, h1.elementor-heading-title, h1")
    if h1:
        h1_text = h1.get_text(" ", strip=True)
        if h1_text:
            title = h1_text

    description = extract_description(meta, soup)
    published, modified = extract_dates(meta)
    image = meta.get("ogImage") or ""
    blog_json_item = next((p for p in json.loads(BLOG_JSON.read_text(encoding="utf-8")) if p["slug"] == slug), None)
    if not image and blog_json_item:
        image = blog_json_item.get("image") or ""

    body_md = html_fragment_to_markdown(root)
    # Remove leading duplicate title heading if present
    body_md = re.sub(rf"^#\s+{re.escape(title)}\s*\n+", "", body_md)

    frontmatter = "\n".join(
        [
            "---",
            f"title: {yaml_escape(title)}",
            f"description: {yaml_escape(description)}",
            f"pubDate: {published}",
            f"updatedDate: {modified}",
            f"image: {yaml_escape(image or '/wp-content/uploads/2023/02/image-2.jpg')}",
            f"slug: {yaml_escape(slug)}",
            "draft: false",
            "---",
            "",
            body_md,
        ]
    )

    out = OUT_DIR / f"{slug}.md"
    out.write_text(frontmatter, encoding="utf-8")
    return {
        "slug": slug,
        "title": title,
        "image": image or "/wp-content/uploads/2023/02/image-2.jpg",
        "href": f"/{slug}/",
        "pubDate": published,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # clear old md
    for old in OUT_DIR.glob("*.md"):
        old.unlink()

    slugs = sorted(p.stem for p in HTML_DIR.glob("*.html"))
    posts = []
    for slug in slugs:
        print(f"[{slug}]")
        item = convert_one(slug)
        if item:
            posts.append(item)
            print(f"  OK -> content/blog/{slug}.md")

    posts.sort(key=lambda p: p["pubDate"], reverse=True)
    BLOG_JSON.write_text(
        json.dumps([{k: p[k] for k in ("slug", "title", "image", "href")} for p in posts], indent=2, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    print(f"\nWrote {len(posts)} markdown posts + updated blog-posts.json")


if __name__ == "__main__":
    main()
