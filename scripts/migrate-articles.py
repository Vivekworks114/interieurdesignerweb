#!/usr/bin/env python3
"""Migrate all blog articles from live WordPress into Astro Elementor data files."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup

SITE = "https://interieurdesignerweb.nl"
BASE = Path(__file__).resolve().parent.parent
TMP = BASE / ".tmp" / "articles"
PUBLIC = BASE / "public"
CSS_DIR = PUBLIC / "wp-assets" / "css"
FONT_DIR = PUBLIC / "wp-assets" / "fonts"
IMG_DIR = PUBLIC / "wp-content" / "uploads"
ARTICLES_HTML = BASE / "src" / "data" / "elementor" / "articles"
ARTICLES_META = BASE / "src" / "data" / "articles"
BLOG_JSON = BASE / "src" / "data" / "blog-posts.json"

SSL_CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

downloaded: dict[str, str] = {}

BASE_CLASSIC_CSS = [
    "/wp-assets/css/hello-reset.css",
    "/wp-assets/css/hello-theme.css",
    "/wp-assets/css/hello-header-footer.css",
    "/wp-assets/css/el-frontend.min.css",
    "/wp-assets/css/post-7.css",
    "/wp-assets/css/el-widget-image.min.css",
    "/wp-assets/css/pro-widget-nav-menu.min.css",
    "/wp-assets/css/el-widget-heading.min.css",
    "/wp-assets/css/pro-widget-posts.min.css",
    "/wp-assets/css/eicons-elementor-icons.min.css",
    "/wp-assets/css/post-11.css",
    "/wp-assets/css/post-9.css",
    "/wp-assets/css/font-jost.css",
    "/wp-assets/css/fa-fontawesome.min.css",
    "/wp-assets/css/fa-solid.min.css",
    "/wp-assets/css/wp-block-library.min.css",
    "/wp-assets/css/article-page.css",
]

EXTRA_WIDGET_CSS = {
    "widget-post-info.min.css": ("pro", f"{SITE}/wp-content/plugins/elementor-pro/assets/css/widget-post-info.min.css"),
    "widget-author-box.min.css": ("el", f"{SITE}/wp-content/plugins/elementor/assets/css/widget-author-box.min.css"),
    "widget-table-of-contents.min.css": ("pro", f"{SITE}/wp-content/plugins/elementor-pro/assets/css/widget-table-of-contents.min.css"),
    "widget-text-editor.min.css": ("el", f"{SITE}/wp-content/plugins/elementor/assets/css/widget-text-editor.min.css"),
}


def fetch(url: str, binary: bool = False, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90, context=SSL_CTX) as resp:
                data = resp.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except Exception as exc:
            if attempt == retries - 1:
                print(f"  FAIL {url}: {exc}")
                return b"" if binary else ""
            time.sleep(1.2 * (attempt + 1))
    return b"" if binary else ""


def ensure_dirs():
    for d in (TMP, CSS_DIR, FONT_DIR, IMG_DIR, ARTICLES_HTML, ARTICLES_META):
        d.mkdir(parents=True, exist_ok=True)


def download_binary(url: str, dest: Path) -> str:
    if not url or url.startswith("data:"):
        return url
    if url in downloaded:
        return downloaded[url]
    dest.parent.mkdir(parents=True, exist_ok=True)
    public_path = "/" + dest.relative_to(PUBLIC).as_posix()
    if dest.exists() and dest.stat().st_size > 0:
        downloaded[url] = public_path
        return public_path
    data = fetch(url.split("?")[0], binary=True)
    if not data:
        downloaded[url] = url
        return url
    dest.write_bytes(data)
    downloaded[url] = public_path
    return public_path


def download_image(url: str) -> str:
    if not url or url.startswith("data:"):
        return url
    url = url.strip()
    if url.startswith("//"):
        url = "https:" + url
    parsed = urlparse(url)
    if "interieurdesignerweb.nl" not in parsed.netloc and parsed.netloc:
        # keep external hotlinks as-is (rare)
        return url
    if "/wp-content/uploads/" in parsed.path:
        rel = parsed.path.split("/wp-content/uploads/", 1)[1]
        return download_binary(url.split("?")[0], IMG_DIR / unquote(rel))
    if parsed.netloc and "interieurdesignerweb.nl" in parsed.netloc:
        return download_binary(url.split("?")[0], PUBLIC / parsed.path.lstrip("/"))
    return url


def rewrite_css_urls(css_text: str, css_url: str) -> str:
    def repl(match: re.Match) -> str:
        raw = match.group(1).strip().strip("'\"")
        if not raw or raw.startswith("data:") or raw.startswith("#"):
            return match.group(0)
        abs_url = urljoin(css_url, raw)
        path = urlparse(abs_url).path
        if any(path.lower().endswith(ext) for ext in (".woff2", ".woff", ".ttf", ".eot", ".otf", ".svg")):
            base = Path(path).name
            if "font-awesome" in path or "/webfonts/" in path:
                dest = FONT_DIR / "fa" / base
            elif "eicons" in path:
                dest = FONT_DIR / "eicons" / base
            elif "google-fonts" in path:
                dest = FONT_DIR / "google" / base
            else:
                dest = FONT_DIR / base
            return f"url({download_binary(abs_url.split('?')[0], dest)})"
        if any(path.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            return f"url({download_image(abs_url.split('?')[0])})"
        return match.group(0)

    return re.sub(r"url\(([^)]+)\)", repl, css_text)


def ensure_css(name: str, url: str) -> str:
    dest = CSS_DIR / name
    public = f"/wp-assets/css/{name}"
    if dest.exists() and dest.stat().st_size > 0 and name != f"post-{url}.css":
        # always rewrite post CSS for images
        if not name.startswith("post-") or name in ("post-7.css", "post-9.css", "post-11.css"):
            return public
    print(f"  CSS {name}")
    text = fetch(url)
    if not text:
        return url
    text = rewrite_css_urls(text, url)
    dest.write_text(text, encoding="utf-8")
    return public


def rewrite_html(html: str) -> str:
    html = html.replace(f'href="{SITE}/', 'href="/')
    html = html.replace(f"href='{SITE}/", "href='/")
    html = html.replace(f'src="{SITE}/', 'src="/')
    html = html.replace(f"src='{SITE}/", "src='/")
    soup = BeautifulSoup(html, "html.parser")

    for img in soup.find_all("img"):
        for attr in ("src", "data-src", "data-lazy-src", "data-litespeed-src"):
            val = img.get(attr)
            if val and not str(val).startswith("data:"):
                img[attr] = download_image(str(val))
        for attr in ("srcset", "data-srcset"):
            val = img.get(attr)
            if not val:
                continue
            parts = []
            for chunk in str(val).split(","):
                chunk = chunk.strip()
                if not chunk:
                    continue
                bits = chunk.split()
                bits[0] = download_image(bits[0])
                parts.append(" ".join(bits))
            img[attr] = ", ".join(parts)
        if img.get("data-lazy-src"):
            img["src"] = img["data-lazy-src"]

    # Elementor JS normally adds this; bake it in for static thumbnail ratios
    for container in soup.select(".elementor-posts-container.elementor-posts"):
        classes = container.get("class") or []
        if "elementor-has-item-ratio" not in classes:
            container["class"] = list(classes) + ["elementor-has-item-ratio"]

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(SITE):
            path = urlparse(href).path or "/"
            if path != "/" and not path.endswith("/") and "." not in Path(path).name:
                path += "/"
            a["href"] = path

    for el in soup.find_all(style=True):
        def style_repl(m):
            u = m.group(1).strip().strip("'\"")
            if u.startswith("data:"):
                return m.group(0)
            return f"url({download_image(urljoin(SITE, u))})"

        el["style"] = re.sub(r"url\(([^)]+)\)", style_repl, el["style"])

    for el in soup.find_all(True):
        for k in list(el.attrs.keys()):
            if k.startswith("data-rocket"):
                del el[k]

    for s in soup.select("script"):
        s.decompose()

    return str(soup)


def extract_json_ld(soup: BeautifulSoup) -> list:
    items = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = (script.string or "").strip()
        if not raw:
            continue
        try:
            items.append(json.loads(raw))
        except json.JSONDecodeError:
            pass
    return items


def write_article_css():
    # Keep in sync with public/wp-assets/css/article-page.css tuned against live.
    css = Path(__file__).resolve().parents[1] / "public" / "wp-assets" / "css" / "article-page.css"
    if css.exists():
        # Do not clobber hand-tuned article CSS during re-migration.
        return
    (CSS_DIR / "article-page.css").write_text("/* article-page.css missing – restore from repo */\n", encoding="utf-8")


def migrate_slug(slug: str) -> dict | None:
    url = f"{SITE}/{slug}/"
    cache = TMP / f"{slug}.html"
    if cache.exists() and cache.stat().st_size > 1000:
        html = cache.read_text(encoding="utf-8", errors="replace")
        print(f"[{slug}] cache")
    else:
        print(f"[{slug}] fetch")
        html = fetch(url)
        if not html:
            return None
        cache.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "").strip() if soup.title else slug
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"] if desc_tag and desc_tag.get("content") else f"Lees {title} op Interieurdesignerweb.nl"
    og = soup.find("meta", property="og:image")
    og_image = download_image(og["content"]) if og and og.get("content") else ""
    body_class = " ".join(soup.body.get("class", [])) + " article-page"

    el_post = soup.select_one('[data-elementor-type="wp-post"]')
    main = soup.select_one("main.site-main")
    template = "elementor" if el_post else "classic"

    stylesheets = list(BASE_CLASSIC_CSS)

    # CSS from page
    for link in soup.select('link[rel="stylesheet"]'):
        href = link.get("href") or ""
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = SITE + href
        path = urlparse(href).path
        name = Path(path).name.split("?")[0]

        if "/uploads/elementor/css/post-" in path and name not in ("post-7.css", "post-9.css", "post-11.css"):
            local = ensure_css(name, href.split("?")[0] if "ver=" in href else href)
            if local not in stylesheets:
                stylesheets.append(local)
        elif name in EXTRA_WIDGET_CSS:
            prefix, src = EXTRA_WIDGET_CSS[name]
            local_name = f"{prefix}-{name}"
            local = ensure_css(local_name, src)
            if local not in stylesheets:
                # insert before article-page.css
                if "/wp-assets/css/article-page.css" in stylesheets:
                    stylesheets.insert(stylesheets.index("/wp-assets/css/article-page.css"), local)
                else:
                    stylesheets.append(local)
        elif "/google-fonts/css/" in path:
            local_name = f"font-{name}"
            local = ensure_css(local_name, f"{SITE}{path}" if path.startswith("/") else href)
            if local not in stylesheets:
                stylesheets.append(local)

    if main:
        content_html = str(main)
        if 'id="content"' not in content_html and "id='content'" not in content_html:
            content_html = content_html.replace("<main", '<main id="content"', 1)
    elif template == "elementor" and el_post:
        classes = ["site-main"]
        content_html = f'<main id="content" class="{" ".join(classes)}">{str(el_post)}</main>'
    else:
        print(f"  no main for {slug}")
        return None

    content_html = rewrite_html(content_html)
    (ARTICLES_HTML / f"{slug}.html").write_text(content_html, encoding="utf-8")

    # featured image fallback from content
    if not og_image:
        m = re.search(r'src="(/wp-content/uploads/[^"]+)"', content_html)
        if m:
            og_image = m.group(1)

    meta = {
        "slug": slug,
        "title": title,
        "description": description,
        "canonical": f"{SITE}/{slug}/",
        "ogImage": og_image or "/wp-content/uploads/2023/02/image-2.jpg",
        "ogType": "article",
        "bodyClass": body_class,
        "template": template,
        "stylesheets": stylesheets,
        "jsonLd": extract_json_ld(soup),
        "htmlFile": f"elementor/articles/{slug}.html",
    }
    (ARTICLES_META / f"{slug}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main():
    ensure_dirs()
    write_article_css()
    # ensure block library exists
    bl = CSS_DIR / "wp-block-library.min.css"
    if not bl.exists() or bl.stat().st_size < 100:
        ensure_css(
            "wp-block-library.min.css",
            f"{SITE}/wp-includes/css/dist/block-library/style.min.css",
        )

    blogs = json.loads(BLOG_JSON.read_text(encoding="utf-8"))
    index = []
    for post in blogs:
        slug = post["slug"]
        meta = migrate_slug(slug)
        if meta:
            index.append(
                {
                    "slug": slug,
                    "title": meta["title"],
                    "href": f"/{slug}/",
                    "template": meta["template"],
                    "ogImage": meta["ogImage"],
                }
            )
            # sync image into blog-posts for cards/listings
            post["image"] = meta["ogImage"]
            post["title"] = BeautifulSoup(meta["title"].split(" - ")[0] if " - interieur" in meta["title"].lower() else meta["title"], "html.parser").get_text()
            # keep title clean: use h1 from page ideally already in title tag "X - site"
            if " - interieurdesignerweb.nl" in meta["title"]:
                post["title"] = meta["title"].replace(" - interieurdesignerweb.nl", "").strip()
            elif " | " in meta["title"]:
                post["title"] = meta["title"].split(" | ")[0].strip()

    BLOG_JSON.write_text(json.dumps(blogs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ARTICLES_META / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nMigrated {len(index)}/{len(blogs)} articles")


if __name__ == "__main__":
    main()
