#!/usr/bin/env python3
"""Extract homepage Elementor page + assets into the Astro project."""

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
PAGE_URL = f"{SITE}/"
BASE = Path(__file__).resolve().parent.parent
TMP = BASE / ".tmp"
PUBLIC = BASE / "public"
DATA = BASE / "src" / "data" / "pages"
CSS_DIR = PUBLIC / "wp-assets" / "css"
FONT_DIR = PUBLIC / "wp-assets" / "fonts"
IMG_DIR = PUBLIC / "wp-content" / "uploads"
HTML_DIR = BASE / "src" / "data" / "elementor"

SSL_CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

downloaded: dict[str, str] = {}

# Prefer original (non-Rocket-cache) CSS URLs when possible
CSS_UNCACHE_MAP = {
    "reset.css": f"{SITE}/wp-content/themes/hello-elementor/assets/css/reset.css",
    "theme.css": f"{SITE}/wp-content/themes/hello-elementor/assets/css/theme.css",
    "header-footer.css": f"{SITE}/wp-content/themes/hello-elementor/assets/css/header-footer.css",
    "elementor-icons.min.css": f"{SITE}/wp-content/plugins/elementor/assets/lib/eicons/css/elementor-icons.min.css",
    "jost.css": f"{SITE}/wp-content/uploads/elementor/google-fonts/css/jost.css",
    "solid.min.css": f"{SITE}/wp-content/plugins/elementor/assets/lib/font-awesome/css/solid.min.css",
}


def fetch(url: str, binary: bool = False, retries: int = 4):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=90, context=SSL_CTX) as resp:
                data = resp.read()
                return data if binary else data.decode("utf-8", errors="replace")
        except Exception as exc:
            print(f"  fetch fail ({attempt+1}/{retries}) {url}: {exc}")
            if attempt == retries - 1:
                return b"" if binary else ""
            time.sleep(1.5 * (attempt + 1))
    return b"" if binary else ""


def ensure_dirs():
    for d in (TMP, CSS_DIR, FONT_DIR, IMG_DIR, DATA, HTML_DIR):
        d.mkdir(parents=True, exist_ok=True)


def local_css_name(url: str) -> str:
    path = urlparse(url).path
    name = Path(path).name.split("?")[0]
    # unwrap rocket cache paths
    if "/cache/min/" in path:
        # .../cache/min/1/wp-content/themes/.../reset.css
        pass
    if "/uploads/elementor/css/" in path:
        return name
    if "/uploads/elementor/google-fonts/css/" in path or name in ("jost.css", "syne.css", "poppins.css", "sourcesanspro.css"):
        return f"font-{name}"
    if "hello-elementor" in path or name in ("reset.css", "theme.css", "header-footer.css"):
        return f"hello-{name}"
    if "elementor-pro" in path:
        return f"pro-{name}"
    if "/eicons/" in path or name == "elementor-icons.min.css":
        return f"eicons-{name}"
    if "font-awesome" in path:
        return f"fa-{name}"
    if "elementor" in path and name.startswith("frontend"):
        return f"el-{name}"
    if name.startswith("widget-"):
        if "elementor-pro" in path:
            return f"pro-{name}"
        return f"el-{name}"
    return name


def resolve_css_url(url: str) -> str:
    name = Path(urlparse(url).path).name.split("?")[0]
    if name in CSS_UNCACHE_MAP:
        return CSS_UNCACHE_MAP[name]
    # unwrap rocket min path to original when possible
    m = re.search(r"/cache/min/\d+/(wp-content/.+\.css)", urlparse(url).path)
    if m:
        return f"{SITE}/{m.group(1)}"
    return url


def download_binary(url: str, dest: Path) -> str:
    if url in downloaded:
        return downloaded[url]
    dest.parent.mkdir(parents=True, exist_ok=True)
    public_path = "/" + dest.relative_to(PUBLIC).as_posix()
    if dest.exists() and dest.stat().st_size > 0:
        downloaded[url] = public_path
        return public_path
    print(f"  DL {url}")
    data = fetch(url, binary=True)
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
    host = parsed.netloc.lower()
    if "interieurdesignerweb.nl" in host and "/wp-content/uploads/" in parsed.path:
        rel = parsed.path.split("/wp-content/uploads/", 1)[1]
        dest = IMG_DIR / unquote(rel)
        return download_binary(url.split("?")[0], dest)
    if "interieurdesignerweb.nl" in host:
        rel = parsed.path.lstrip("/")
        dest = PUBLIC / rel
        return download_binary(url.split("?")[0], dest)
    return url


def rewrite_css_urls(css_text: str, css_url: str) -> str:
    def repl(match: re.Match) -> str:
        raw = match.group(1).strip().strip("'\"")
        if not raw or raw.startswith("data:") or raw.startswith("#"):
            return match.group(0)
        abs_url = urljoin(css_url, raw)
        parsed = urlparse(abs_url)
        path = parsed.path
        if any(path.lower().endswith(ext) for ext in (".woff2", ".woff", ".ttf", ".eot", ".svg", ".otf")):
            base = Path(path).name
            if "font-awesome" in path or "/webfonts/" in path:
                dest = FONT_DIR / "fa" / base
            elif "eicons" in path:
                dest = FONT_DIR / "eicons" / base
            elif "google-fonts" in path:
                dest = FONT_DIR / "google" / base
            else:
                dest = FONT_DIR / base
            local = download_binary(abs_url.split("?")[0], dest)
            return f"url({local})"
        if any(path.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            local = download_image(abs_url.split("?")[0])
            return f"url({local})"
        return match.group(0)

    return re.sub(r"url\(([^)]+)\)", repl, css_text)


def download_stylesheet(url: str) -> str:
    url = resolve_css_url(url)
    name = local_css_name(url)
    dest = CSS_DIR / name
    public_path = f"/wp-assets/css/{name}"
    if dest.exists() and dest.stat().st_size > 0:
        # still rewrite if file exists but may need image downloads from content
        if name == "post-40.css" or "background" in dest.read_text(encoding="utf-8", errors="ignore")[:500]:
            pass
        else:
            downloaded[url] = public_path
            print(f"CSS reuse {name}")
            return public_path

    print(f"CSS {url}")
    text = fetch(url)
    if not text:
        text = fetch(url.split("?")[0])
    if not text:
        return url
    text = rewrite_css_urls(text, url)
    dest.write_text(text, encoding="utf-8")
    downloaded[url] = public_path
    return public_path


def clean_fragment(html: str) -> str:
    # Keep style tags that style page widgets (e.g. category grids)
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.I | re.S)
    return html.strip()


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
        if img.get("data-lazy-src") and img.get("src"):
            img["src"] = img.get("data-lazy-src") or img["src"]

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(SITE):
            path = urlparse(href).path or "/"
            if path != "/" and not path.endswith("/") and "." not in Path(path).name:
                path = path + "/"
            a["href"] = path

    for el in soup.find_all(style=True):
        style = el["style"]

        def style_repl(m):
            u = m.group(1).strip().strip("'\"")
            if u.startswith("data:"):
                return m.group(0)
            return f"url({download_image(urljoin(SITE, u))})"

        el["style"] = re.sub(r"url\(([^)]+)\)", style_repl, style)

    # Preserve inline <style> blocks inside the fragment
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


def extract_page_inline_styles(soup: BeautifulSoup) -> str:
    """Collect meaningful inline styles from the live page head/body."""
    chunks = []
    for st in soup.select("style"):
        text = (st.string or "").strip()
        if not text:
            continue
        # skip WP emoji / lazy / preset bulk unless homepage-specific
        if "zbmp" in text or "custom" in text.lower() or "category" in text.lower():
            chunks.append(text)
        elif "breadcrumb" in text.lower():
            chunks.append(text)
    return "\n\n".join(chunks)


def main():
    ensure_dirs()
    print("Fetching homepage…")
    html_path = TMP / "homepage.html"
    if not html_path.exists() or html_path.stat().st_size < 1000:
        html = fetch(PAGE_URL)
        html_path.write_text(html, encoding="utf-8")
    else:
        html = html_path.read_text(encoding="utf-8", errors="replace")
        print(f"Using cached {html_path}")

    soup = BeautifulSoup(html, "html.parser")

    title = (soup.title.string or "").strip() if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""
    og_image = ""
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        og_image = download_image(og["content"])

    body = soup.body
    body_class = " ".join(body.get("class", [])) if body else ""

    css_urls = []
    for link in soup.select('link[rel="stylesheet"]'):
        href = link.get("href")
        if not href:
            continue
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = SITE + href
        if "fonts.googleapis.com" in href:
            continue
        css_urls.append(href)

    local_css = []
    seen_names = set()
    for url in css_urls:
        path = download_stylesheet(url)
        if path not in seen_names:
            local_css.append(path)
            seen_names.add(path)

    for link in soup.select('link[rel="icon"], link[rel="apple-touch-icon"]'):
        href = link.get("href")
        if href:
            if href.startswith("/"):
                href = SITE + href
            download_image(href)

    header = soup.select_one('[data-elementor-type="header"]')
    page = soup.select_one('[data-elementor-type="wp-page"]')
    footer = soup.select_one('[data-elementor-type="footer"]')
    if not page:
        raise SystemExit("Could not find wp-page elementor root")

    main_el = soup.select_one("main.site-main")
    # Keep page-content wrapper if present (homepage has it)
    if main_el:
        # rebuild main with cleaned page only, preserve page-content if original had it
        page_content = main_el.select_one(".page-content")
        if page_content:
            main_html = (
                f'<main id="content" class="{" ".join(main_el.get("class", []))}">'
                f'<div class="page-content">{str(page)}</div></main>'
            )
        else:
            main_html = f'<main id="content" class="{" ".join(main_el.get("class", []))}">{str(page)}</main>'
    else:
        main_html = f'<main id="content" class="site-main"><div class="page-content">{str(page)}</div></main>'

    # Always refresh header/footer from homepage (same templates, ensures consistency)
    header_html = rewrite_html(clean_fragment(str(header))) if header else ""
    footer_html = rewrite_html(clean_fragment(str(footer))) if footer else ""
    content_html = rewrite_html(clean_fragment(main_html))

    (HTML_DIR / "header.html").write_text(header_html, encoding="utf-8")
    (HTML_DIR / "footer.html").write_text(footer_html, encoding="utf-8")
    (HTML_DIR / "homepage.html").write_text(content_html, encoding="utf-8")

    inline = extract_page_inline_styles(soup)
    overrides_extra = PUBLIC / "wp-assets" / "css" / "homepage-inline.css"
    if inline:
        overrides_extra.write_text(inline, encoding="utf-8")
        if "/wp-assets/css/homepage-inline.css" not in local_css:
            local_css.append("/wp-assets/css/homepage-inline.css")
    else:
        # ensure file exists empty-ish
        overrides_extra.write_text("/* no homepage-specific inline styles */\n", encoding="utf-8")
        if "/wp-assets/css/homepage-inline.css" not in local_css:
            local_css.append("/wp-assets/css/homepage-inline.css")

    if not og_image:
        # fallback logo
        og_image = "/wp-content/uploads/2023/02/Frame-700-1.svg"

    meta = {
        "slug": "home",
        "title": title,
        "description": description,
        "canonical": f"{SITE}/",
        "ogImage": og_image,
        "ogType": "website",
        "bodyClass": body_class,
        "stylesheets": local_css,
        "jsonLd": extract_json_ld(soup),
    }
    (DATA / "homepage.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    # Ensure hero background images from post-40 are local
    post40 = CSS_DIR / "post-40.css"
    if post40.exists():
        urls = re.findall(r"url\(([^)]+)\)", post40.read_text(encoding="utf-8"))
        print(f"post-40 urls: {len(urls)}")
        for u in urls[:20]:
            print(" ", u.strip())

    print("\nDone.")
    print(f"  CSS files: {len(local_css)}")
    print(f"  Assets downloaded: {len(downloaded)}")
    print(f"  Title: {title}")


if __name__ == "__main__":
    main()
