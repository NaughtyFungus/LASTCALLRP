#!/usr/bin/env python3
"""
fetch_docs.py
Reads config.json, fetches each Google Doc as HTML, strips Google's
styles and markup, and saves a clean fragment to the rules/ directory.

Run manually:  python3 fetch_docs.py
Run via CI:    see .github/workflows/fetch-docs.yml
"""

import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser


CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")


# ── HTML cleaner ──────────────────────────────────────────────────────────────

class DocCleaner(HTMLParser):
    """
    Walks a Google Doc's exported HTML, keeps only the body content,
    and strips inline styles, class attributes, and Google-specific spans.
    """

    SKIP_TAGS = {"script", "style", "head", "html", "body", "meta", "link"}
    PASS_TAGS = {"h1","h2","h3","h4","h5","h6","p","ul","ol","li","strong",
                 "b","em","i","a","hr","br","table","thead","tbody","tr",
                 "th","td","blockquote","span","div"}
    KEEP_ATTRS = {"href"}          # keep only these attributes

    def __init__(self):
        super().__init__()
        self.in_body  = False
        self.depth    = 0
        self.buf      = []
        self._skip    = 0           # depth counter for skipped tags

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        if not self.in_body:
            return
        if tag in self.SKIP_TAGS:
            self._skip += 1
            return
        if self._skip:
            return

        if tag in self.PASS_TAGS:
            safe = {k: v for k, v in attrs if k in self.KEEP_ATTRS}
            attr_str = "".join(f' {k}="{v}"' for k, v in safe.items())
            self.buf.append(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
            return
        if not self.in_body:
            return
        if tag in self.SKIP_TAGS:
            self._skip = max(0, self._skip - 1)
            return
        if self._skip:
            return
        if tag in self.PASS_TAGS:
            self.buf.append(f"</{tag}>")

    def handle_data(self, data):
        if self.in_body and not self._skip:
            self.buf.append(data)

    def handle_entityref(self, name):
        if self.in_body and not self._skip:
            self.buf.append(f"&{name};")

    def handle_charref(self, name):
        if self.in_body and not self._skip:
            self.buf.append(f"&#{name};")

    def result(self):
        html = "".join(self.buf)
        # Collapse 3+ blank lines to 1
        html = re.sub(r"\n{3,}", "\n\n", html)
        # Remove empty paragraph tags
        html = re.sub(r"<p>\s*</p>", "", html)
        return html.strip()


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_doc(doc_id: str) -> str:
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; lastcall-rp-fetcher/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def process_section(section: dict, rules_dir: str) -> bool:
    doc_id   = (section.get("docId") or "").strip()
    filename = (section.get("file") or "").lstrip("/")
    title    = section.get("title", "Untitled")

    if not doc_id:
        print(f"  [skip] {title} — no docId configured")
        return False

    if not filename:
        print(f"  [skip] {title} — no file path configured")
        return False

    print(f"  [fetch] {title} ...")
    try:
        raw_html = fetch_doc(doc_id)
    except Exception as exc:
        print(f"  [error] Could not fetch {title}: {exc}")
        return False

    cleaner = DocCleaner()
    cleaner.feed(raw_html)
    clean = cleaner.result()

    out_path = os.path.join(os.path.dirname(__file__), filename)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(clean)

    print(f"  [ok]    Saved → {filename}")
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found. Run from the repo root.", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_FILE, encoding="utf-8") as f:
        config = json.load(f)

    sections = config.get("sections", [])
    if not sections:
        print("No sections found in config.json.")
        sys.exit(0)

    print(f"Fetching {len(sections)} section(s)...\n")
    results = [process_section(s, "rules") for s in sections]
    fetched = sum(1 for r in results if r)
    print(f"\nDone. {fetched}/{len(sections)} section(s) updated.")


if __name__ == "__main__":
    main()
