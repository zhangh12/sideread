# sideread

A [Claude Code](https://claude.ai/code) slash command that converts any document or URL into a **side-by-side bilingual HTML page** — original text on the left, machine-translatable copy on the right.

## Motivation

Sometimes I just want to read something in my native language — a rental agreement, a legal letter, a government form, a journal PDF that Chrome has no way to translate, an article full of medical terms, a novel, a recipe, a product manual — without sitting down to wrestle with every sentence.

The obvious tools both fall short.

**Chrome's built-in Translate** replaces the entire page. The original is gone. When the translation sounds off — and for technical, legal, or literary content it often does — there is no way to check the source without switching back and losing my place.

**LLM chatbots** are worse for this. Ask one to "translate this article" and I get bullet points, paraphrased summaries, skipped paragraphs. They are built to compress, not to translate. The original sentence structure and nuance are gone.

What I actually want is simple: **original and translation, sentence by sentence, side by side** — so I can read at speed and glance left whenever something sounds wrong. `sideread` produces exactly that.

## How it works

Feed it any document — PDF, Word file, webpage, markdown note, ebook — and it builds a single self-contained HTML file where:

- The **left column** is the original text, frozen (`translate="no"` prevents any tool from touching it)
- The **right column** is the same content, ready for Google Translate with one click from a dropdown in the header

No tokens spent on translation. No summarization. Every sentence is there.

## Installation

**Prerequisites:** [Claude Code](https://claude.ai/code), [pandoc](https://pandoc.org) ≥ 3.0, Python 3, beautifulsoup4

```bash
git clone https://github.com/zhangh12/sideread.git ~/Documents/Github/sideread
cd ~/Documents/Github/sideread
bash install.sh
```

Restart Claude Code after installing.

## Usage

```
/sideread <input> [pages] [output]
```

| Argument | Required | Description |
|----------|----------|-------------|
| `input` | yes | File path or URL |
| `pages` | no | PDF page range, e.g. `1-20` |
| `output` | no | Output path (default: same folder, `.html` extension) |

**Supported formats:** PDF, Word (.docx), EPUB, HTML, Markdown, reStructuredText, LaTeX, ODT, plain text, web URLs

**Examples:**
```bash
/sideread ~/Downloads/lease-agreement.pdf
/sideread ~/Downloads/paper.pdf 5-30
/sideread https://www.nejm.org/doi/full/10.1056/NEJMoa2400000
/sideread ~/Documents/report.docx
```

Open the output in Chrome, pick a target language from the dropdown — the right column translates, the left never changes. Internet required for Google Translate.

## Tips

- **Scanned PDFs** (no text layer): pre-process with `ocrmypdf input.pdf input-ocr.pdf` first
- **Long PDFs**: use `pages` to work on sections rather than the whole file
- **Best quality**: place a hand-crafted `paper.md` alongside `paper.pdf` — sideread will use it instead of extracting from the PDF

## Repo structure

```
sideread/
├── sideread.md   ← Claude Code skill (the /sideread slash command)
├── build.py      ← HTML builder: body fragment → bilingual page
├── install.sh    ← Installs the slash command, checks dependencies
└── README.md
```
