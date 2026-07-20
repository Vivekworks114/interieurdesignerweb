#!/usr/bin/env python3
"""Migrate live /blog/ and /blog/2/ Elementor pages into Astro data files."""

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
TMP = BASE / ".tmp" / "blog"
PUBLIC = BASE / "public"
CSS_DIR = PUBLIC / "wp-assets" / "css"
FONT_DIR = PUBLIC / "wp-assets" / "fonts"
IMG_DIR = PUBLIC / "wp-content" / "uploads"
HTML_DIR = BASE / "src" / "data" / "elementor" / "blog"
META_DIR = BASE / "src" / "data" / "blog"

SSL_CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

downloaded: dict[str, str] = {}

BASE_CSS = [
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
    "/wp-assets/css/article-page.css",
]

EXTRA_WIDGET_CSS = {
    "widget-posts.min.css": (
        "pro",
        f"{SITE}/wp-content/plugins/elementor-pro/assets/css/widget-posts.min.css",
    ),
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
    for d in (TMP, CSS_DIR, FONT_DIR, IMG_DIR, HTML_DIR, META_DIR):
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
    if url.startswith("/"):
        url = SITE + url
    parsed = urlparse(url)
    if parsed.netloc and "interieurdesignerweb.nl" not in parsed.netloc:
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
    if dest.exists() and dest.stat().st_size > 0 and not name.startswith("post-268"):
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
        # Prefer real src over SVG lazy placeholder
        src = img.get("src") or ""
        if src.startswith("data:image") and img.get("data-lazy-src"):
            img["src"] = img["data-lazy-src"]

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
        elif href.startswith("/blog/page/"):
            # normalize WP alternate pagination if present
            a["href"] = href

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

    return str(soup)


def extract_json_ld(soup: BeautifulSoup) -> list:
    items = []
    for script in soup.select('script[type="application/ld+json"]'):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            items.append(json.loads(raw))
        except Exception:
            pass
    return items


def migrate_page(page_key: str, path: str) -> dict | None:
    url = f"{SITE}{path}"
    cache = TMP / f"{page_key}.html"
    if cache.exists() and cache.stat().st_size > 1000:
        html = cache.read_text(encoding="utf-8", errors="replace")
        print(f"[{path}] cache")
    else:
        print(f"[{path}] fetch")
        html = fetch(url)
        if not html:
            return None
        cache.write_text(html, encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "Blog").strip() if soup.title else "Blog"
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = (
        desc_tag["content"]
        if desc_tag and desc_tag.get("content")
        else "Handige tips en informatie voor je interieur op Interieurdesignerweb.nl"
    )
    og = soup.find("meta", property="og:image")
    og_image = download_image(og["content"]) if og and og.get("content") else ""
    body_class = " ".join(soup.body.get("class", [])) + " article-page"

    main = soup.select_one("main.site-main")
    if not main:
        print(f"  no main for {path}")
        return None

    stylesheets = list(BASE_CSS)

    for link in soup.select('link[rel="stylesheet"]'):
        href = link.get("href") or ""
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = SITE + href
        path_url = urlparse(href).path
        name = Path(path_url).name.split("?")[0]

        if "/uploads/elementor/css/post-268" in path_url:
            local = ensure_css("post-268.css", href.split("?")[0])
            if local not in stylesheets:
                stylesheets.append(local)
        elif name in EXTRA_WIDGET_CSS:
            prefix, src = EXTRA_WIDGET_CSS[name]
            local_name = f"{prefix}-{name}"
            local = ensure_css(local_name, src)
            if local not in stylesheets:
                if "/wp-assets/css/article-page.css" in stylesheets:
                    stylesheets.insert(stylesheets.index("/wp-assets/css/article-page.css"), local)
                else:
                    stylesheets.append(local)
        elif "/google-fonts/css/" in path_url:
            local_name = f"font-{name}"
            local = ensure_css(local_name, f"{SITE}{path_url}" if path_url.startswith("/") else href)
            if local not in stylesheets:
                stylesheets.append(local)

    # Ensure post-268 is present
    if "/wp-assets/css/post-268.css" not in stylesheets:
        stylesheets.append(
            ensure_css("post-268.css", f"{SITE}/wp-content/uploads/elementor/css/post-268.css")
        )

    content_html = str(main)
    if 'id="content"' not in content_html and "id='content'" not in content_html:
        content_html = content_html.replace("<main", '<main id="content"', 1)
    content_html = rewrite_html(content_html)
    (HTML_DIR / f"{page_key}.html").write_text(content_html, encoding="utf-8")

    # Clean title
    clean_title = re.sub(r"\s*[-|]\s*interieurdesignerweb\.nl.*$", "", title, flags=re.I).strip() or "Blog"

    meta = {
        "slug": page_key,
        "path": path,
        "title": clean_title if page_key == "index" else f"{clean_title}",
        "description": description,
        "canonical": f"{SITE}{path}",
        "ogImage": og_image,
        "ogType": "website",
        "bodyClass": body_class,
        "stylesheets": stylesheets,
        "jsonLd": extract_json_ld(soup),
        "htmlFile": f"elementor/blog/{page_key}.html",
    }
    (META_DIR / f"{page_key}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  OK articles={content_html.count('elementor-post ')} css={len(stylesheets)}")
    return meta


def main():
    ensure_dirs()
    pages = [
        ("page-1", "/blog/"),
        ("page-2", "/blog/2/"),
    ]
    results = []
    for key, path in pages:
        meta = migrate_page(key, path)
        if meta:
            results.append(meta)
    (META_DIR / "listing.json").write_text(
        json.dumps([{"slug": m["slug"], "path": m["path"]} for m in results], indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"\nMigrated {len(results)}/{len(pages)} blog pages")


if __name__ == "__main__":
    main()
