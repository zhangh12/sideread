#!/usr/bin/env python3
"""
sideread/build.py
Wraps a pandoc-generated HTML body fragment into a side-by-side bilingual page.

Left  column: translate="no"  → stays in original language
Right column: (no attribute)  → translatable via Google Translate widget or Chrome

Usage:
    python3 build.py --input body.html --output out.html [--title "My Title"]
"""

import argparse
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    print("ERROR: beautifulsoup4 not installed. Run: pip3 install beautifulsoup4", file=sys.stderr)
    sys.exit(1)

BLOCK_TAGS = {
    "h1","h2","h3","h4","h5","h6",
    "p","ul","ol","dl","blockquote",
    "table","pre","hr","figure","aside",
    "section","div",
}

CSS = """
    /* ── Reset ── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: Georgia, "Times New Roman", serif;
      font-size: 15px;
      line-height: 1.75;
      color: #1a1a1a;
      background: #f5f5f0;
    }

    /* ── Sticky header ── */
    header {
      background: #1a3a5c;
      color: #fff;
      padding: 12px 24px;
      position: sticky;
      top: 0;
      z-index: 100;
      display: flex;
      align-items: center;
      gap: 14px;
      box-shadow: 0 2px 6px rgba(0,0,0,.4);
      flex-wrap: wrap;
    }
    header h1 {
      font-size: 13px;
      font-weight: 600;
      flex: 1;
      line-height: 1.4;
      min-width: 200px;
    }
    .badge {
      background: #e8a020;
      color: #111;
      font-size: 11px;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 3px;
      white-space: nowrap;
    }

    /* ── Google Translate widget ── */
    #gt-wrapper {
      display: flex;
      align-items: center;
      gap: 8px;
      background: rgba(255,255,255,.12);
      padding: 5px 10px;
      border-radius: 5px;
    }
    #gt-wrapper label {
      font-size: 12px;
      color: #cde;
      white-space: nowrap;
    }
    .goog-te-gadget-simple {
      background: transparent !important;
      border: 1px solid rgba(255,255,255,.4) !important;
      border-radius: 4px !important;
      padding: 2px 6px !important;
      font-size: 13px !important;
      cursor: pointer;
    }
    .goog-te-gadget-simple span,
    .goog-te-gadget-simple .goog-te-menu-value span { color: #fff !important; }
    .goog-te-banner-frame.skiptranslate { display: none !important; }
    body { top: 0 !important; }

    /* ── Column label bar ── */
    .label-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      position: sticky;
      top: 49px;
      z-index: 99;
      border-bottom: 2px solid #1a3a5c;
    }
    .label-row span {
      background: #dce8f0;
      padding: 5px 20px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: .06em;
      color: #1a3a5c;
    }
    .label-row span + span {
      border-left: 2px solid #1a3a5c;
      background: #eef4f0;
    }

    /* ── Bilingual table ── */
    #bilingual {
      width: 100%;
      border-collapse: collapse;
    }
    #bilingual td {
      width: 50%;
      vertical-align: top;
      padding: 10px 28px;
      border-bottom: 1px solid #e0e0d8;
    }
    #bilingual td + td {
      border-left: 2px solid #c8d8e8;
      background: #fafaf6;
    }
    #bilingual tr:nth-child(even) td:first-child { background: #f8f8f4; }
    #bilingual tr:nth-child(even) td:last-child  { background: #f5f8f4; }

    /* ── Typography inside cells ── */
    td h1 {
      font-size: 1.45em; margin: .8em 0 .4em; color: #1a3a5c;
      border-bottom: 2px solid #1a3a5c; padding-bottom: .2em;
    }
    td h2 {
      font-size: 1.18em; margin: .7em 0 .35em; color: #1a3a5c;
      border-bottom: 1px solid #b8cfe0; padding-bottom: .12em;
    }
    td h3 { font-size: 1.04em; margin: .6em 0 .25em; color: #2a4a6c; }
    td h4 { font-size: .95em;  margin: .5em 0 .2em;  color: #444; font-style: italic; }
    td p  { margin: .5em 0; }
    td ul, td ol { margin: .5em 0 .5em 1.6em; }
    td li { margin: .25em 0; }
    td blockquote {
      margin: .6em 0; padding: .5em 1em;
      border-left: 4px solid #1a3a5c;
      background: #edf3f8; color: #333; font-style: italic;
    }
    td table {
      border-collapse: collapse; width: 100%;
      margin: .6em 0; font-size: .87em;
    }
    td th, td td { border: 1px solid #bbb; padding: 5px 9px; text-align: left; }
    td th { background: #dde6f0; font-weight: 700; }
    td tr:nth-child(even) td { background: #f4f7fb; }
    td a { color: #1a5a9c; }
    td a:hover { text-decoration: underline; }
    td sup { font-size: .75em; }
    td pre {
      background: #f0f0e8; border: 1px solid #ddd;
      border-radius: 4px; padding: .6em 1em;
      overflow-x: auto; font-size: .85em;
    }
    td code { font-family: monospace; background: #e8e8e0;
              padding: 1px 4px; border-radius: 2px; font-size: .88em; }
    td section.footnotes {
      font-size: .83em; color: #555;
      border-top: 1px solid #ddd; margin-top: 1em; padding-top: .8em;
    }

    /* ── Footer ── */
    footer {
      text-align: center; font-size: 12px; color: #777;
      padding: 10px; background: #eee; border-top: 1px solid #ddd;
    }
    footer code {
      font-family: monospace; background: #e0e0d8;
      padding: 1px 4px; border-radius: 2px;
    }
"""

TRANSLATE_WIDGET = """
<script>
  function googleTranslateElementInit() {
    new google.translate.TranslateElement({
      pageLanguage: 'auto',
      includedLanguages: 'zh-CN,zh-TW,ja,ko,de,fr,es,pt,ar,ru,it,nl,pl,sv,vi,th,id,hi,tr,uk',
      layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
      autoDisplay: false
    }, 'google_translate_element');
  }
</script>
<script src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>
"""


def split_into_blocks(body_html: str) -> list[str]:
    """Parse HTML body and return a list of top-level block strings."""
    soup = BeautifulSoup(body_html, "html.parser")
    blocks = []
    for node in soup.children:
        if isinstance(node, NavigableString):
            text = node.strip()
            if text:
                blocks.append(f"<p>{text}</p>")
        elif isinstance(node, Tag):
            blocks.append(str(node))
    return blocks


def build_html(body_html: str, title: str, source_label: str = "") -> str:
    blocks = split_into_blocks(body_html)

    rows = []
    for block in blocks:
        rows.append(
            f'<tr>\n'
            f'  <td translate="no">{block}</td>\n'
            f'  <td>{block}</td>\n'
            f'</tr>'
        )
    table_rows = "\n".join(rows)

    source_badge = f'<span class="badge">{source_label}</span>' if source_label else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>
{CSS}
  </style>
</head>
<body>

<header>
  <h1>{title}</h1>
  {source_badge}
  <div id="gt-wrapper">
    <label>&#127758; Translate right column:</label>
    <div id="google_translate_element"></div>
  </div>
</header>

<div class="label-row">
  <span>&#x1F1EC;&#x1F1E7; Original — pinned with translate="no"</span>
  <span>&#x1F30D; Translation — select language above or use Chrome</span>
</div>

<table id="bilingual">
  <tbody>
{table_rows}
  </tbody>
</table>

<footer>
  Left column is protected by <code>translate="no"</code> and stays in the original language.
  Right column is translated. Powered by Google Translate + pandoc + sideread.
</footer>

{TRANSLATE_WIDGET}
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Wrap an HTML body fragment into a side-by-side bilingual page."
    )
    parser.add_argument("--input",  required=True, help="Pandoc-generated HTML body fragment")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--title",  default="Document", help="Page title")
    parser.add_argument("--source-label", default="", help="Optional badge text (e.g. 'PDF')")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    body_html = input_path.read_text(encoding="utf-8")
    result = build_html(body_html, title=args.title, source_label=args.source_label)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result, encoding="utf-8")

    n_blocks = len(split_into_blocks(body_html))
    print(f"sideread: {n_blocks} blocks → {output_path}  ({len(result):,} bytes)")


if __name__ == "__main__":
    main()
