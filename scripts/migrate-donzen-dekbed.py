#!/usr/bin/env python3
"""Extract beste-donzen-dekbed Elementor page + assets into the Astro project."""

from __future__ import annotations

import json
import re
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote

from bs4 import BeautifulSoup

SITE = "https://interieurdesignerweb.nl"
PAGE_URL = f"{SITE}/beste-donzen-dekbed/"
BASE = Path(__file__).resolve().parent.parent
TMP = BASE / ".tmp"
PUBLIC = BASE / "public"
DATA = BASE / "src" / "data" / "pages"
CSS_DIR = PUBLIC / "wp-assets" / "css"
FONT_DIR = PUBLIC / "wp-assets" / "fonts"
IMG_DIR = PUBLIC / "wp-content" / "uploads"
PRODUCT_IMG_DIR = PUBLIC / "images" / "products" / "donzen-dekbed"
HTML_DIR = BASE / "src" / "data" / "elementor"

SSL_CTX = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

downloaded: dict[str, str] = {}


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
    for d in (TMP, CSS_DIR, FONT_DIR, IMG_DIR, PRODUCT_IMG_DIR, DATA, HTML_DIR):
        d.mkdir(parents=True, exist_ok=True)


def local_css_name(url: str) -> str:
    path = urlparse(url).path
    name = Path(path).name
    # distinguish post CSS files that share similar names
    if "/uploads/elementor/css/" in path:
        return name.split("?")[0]
    if "/uploads/elementor/google-fonts/css/" in path:
        return f"font-{name.split('?')[0]}"
    if "/hello-elementor/" in path:
        return f"hello-{name.split('?')[0]}"
    if "/elementor-pro/" in path:
        return f"pro-{name.split('?')[0]}"
    if "/elementor/" in path:
        if "/eicons/" in path:
            return f"eicons-{name.split('?')[0]}"
        if "/font-awesome/" in path:
            return f"fa-{name.split('?')[0]}"
        return f"el-{name.split('?')[0]}"
    return name.split("?")[0]


def download_binary(url: str, dest: Path) -> str:
    """Download binary asset; return public URL path."""
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

    if "myfreeimagehost.com" in host or "partner.bol.com" in host:
        # product images hosted externally
        name = Path(parsed.path).name or "image"
        if not Path(name).suffix:
            name = name + ".jpg"
        # sanitize
        name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
        dest = PRODUCT_IMG_DIR / name
        return download_binary(url.split("?")[0], dest)

    # other absolute images under wp-content
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
            # keep fonts under wp-assets/fonts preserving basename; avoid collisions
            base = Path(path).name
            # include a short parent folder hint for fa/eicons
            parent = Path(path).parent.name
            dest_name = f"{parent}-{base}" if parent and parent not in ("css", "webfonts", "fonts") else base
            if "font-awesome" in path or "/webfonts/" in path:
                dest = FONT_DIR / "fa" / base
            elif "eicons" in path:
                dest = FONT_DIR / "eicons" / base
            elif "google-fonts" in path or "elementor/google-fonts" in path:
                dest = FONT_DIR / "google" / base
            else:
                dest = FONT_DIR / dest_name
            local = download_binary(abs_url.split("?")[0], dest)
            return f"url({local})"

        if any(path.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico")):
            local = download_image(abs_url.split("?")[0])
            return f"url({local})"

        return match.group(0)

    return re.sub(r"url\(([^)]+)\)", repl, css_text)


def download_stylesheet(url: str) -> str:
    """Download CSS, rewrite urls, return public path."""
    name = local_css_name(url)
    dest = CSS_DIR / name
    public_path = f"/wp-assets/css/{name}"
    if dest.exists() and dest.stat().st_size > 0 and url in downloaded:
        return downloaded[url]

    print(f"CSS {url}")
    text = fetch(url.split("?")[0] if "ver=" in url else url)
    if not text:
        # retry with full URL including query
        text = fetch(url)
    if not text:
        return url
    text = rewrite_css_urls(text, url)
    dest.write_text(text, encoding="utf-8")
    downloaded[url] = public_path
    return public_path


def clean_fragment(html: str) -> str:
    html = re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.I | re.S)
    # keep inline styles on elements; strip only style tags if any slipped in
    html = re.sub(r"<style\b[^>]*>.*?</style>", "", html, flags=re.I | re.S)
    return html.strip()


def rewrite_html(html: str) -> str:
    # absolute site links -> relative
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
        # drop lazy hiding
        if img.get("data-lazy-src") and img.get("src"):
            img["src"] = img.get("data-lazy-src") or img["src"]

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith(SITE):
            path = urlparse(href).path or "/"
            a["href"] = path if path.endswith("/") or "." in Path(path).name else path + "/"

    for el in soup.find_all(style=True):
        style = el["style"]

        def style_repl(m):
            u = m.group(1).strip().strip("'\"")
            if u.startswith("data:"):
                return m.group(0)
            return f"url({download_image(urljoin(SITE, u))})"

        el["style"] = re.sub(r"url\(([^)]+)\)", style_repl, style)

    # remove rocket/lazy leftovers
    for el in soup.select(".rll-youtube-player"):
        el.decompose()

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


def main():
    ensure_dirs()
    print("Fetching page…")
    html_path = TMP / "donzen-page.html"
    if not html_path.exists() or html_path.stat().st_size < 1000:
        html = fetch(PAGE_URL)
        html_path.write_text(html, encoding="utf-8")
    else:
        html = html_path.read_text(encoding="utf-8", errors="replace")
        print(f"Using cached {html_path}")

    soup = BeautifulSoup(html, "html.parser")

    # metadata
    title = (soup.title.string or "").strip() if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"] if desc_tag and desc_tag.get("content") else ""
    og_image = ""
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        og_image = download_image(og["content"])

    body = soup.body
    body_class = " ".join(body.get("class", [])) if body else ""

    # stylesheets
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
    for url in css_urls:
        local_css.append(download_stylesheet(url))

    # favicons
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

    # wrap page in main like original
    main_el = soup.select_one("main.site-main")
    if main_el:
        # rebuild main wrapper with cleaned page only
        main_html = f'<main id="content" class="{" ".join(main_el.get("class", []))}">{str(page)}</main>'
    else:
        main_html = f'<main id="content" class="site-main">{str(page)}</main>'

    header_html = rewrite_html(clean_fragment(str(header))) if header else ""
    footer_html = rewrite_html(clean_fragment(str(footer))) if footer else ""
    content_html = rewrite_html(clean_fragment(main_html))

    (HTML_DIR / "header.html").write_text(header_html, encoding="utf-8")
    (HTML_DIR / "footer.html").write_text(footer_html, encoding="utf-8")
    (HTML_DIR / "beste-donzen-dekbed.html").write_text(content_html, encoding="utf-8")

    # also rewrite og image path if remote still
    if og_image.startswith("http"):
        og_image = download_image(og_image)

    meta = {
        "slug": "beste-donzen-dekbed",
        "title": title,
        "description": description,
        "canonical": f"{SITE}/beste-donzen-dekbed/",
        "ogImage": og_image or "/wp-content/uploads/2023/02/image-2.jpg",
        "bodyClass": body_class,
        "stylesheets": local_css,
        "jsonLd": extract_json_ld(soup),
    }
    (DATA / "beste-donzen-dekbed.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print("\nDone.")
    print(f"  CSS files: {len(local_css)}")
    print(f"  Assets downloaded: {len(downloaded)}")
    print(f"  Title: {title}")


if __name__ == "__main__":
    main()
