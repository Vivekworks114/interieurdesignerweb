#!/usr/bin/env python3
"""Verify internal links in built Astro site."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def main() -> None:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    dist = root / "dist"
    if not dist.exists():
        print("dist/ not found — run npm run build first")
        raise SystemExit(1)

    html_files = list(dist.rglob("*.html"))
    hrefs: set[str] = set()
    for f in html_files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for href in re.findall(r'href="(/[^"#?]*/?)"', text):
            if href.startswith("/_astro/") or href.startswith("/images/"):
                continue
            hrefs.add(href.rstrip("/") + "/" if href != "/" else "/")

    missing: list[str] = []
    for href in sorted(hrefs):
        if href == "/":
            target = dist / "index.html"
        else:
            target = dist / href.strip("/") / "index.html"
        if not target.exists():
            missing.append(href)

    print(f"Checked {len(hrefs)} unique internal links across {len(html_files)} pages")
    if missing:
        print(f"MISSING ({len(missing)}):")
        for m in missing[:30]:
            print(f"  {m}")
        raise SystemExit(1)
    print("All internal links OK")


if __name__ == "__main__":
    main()
