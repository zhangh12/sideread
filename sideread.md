# sideread

Convert any document or URL into a **side-by-side bilingual HTML** where:
- **Left column** — original text, pinned with `translate="no"` (never touched by translation)
- **Right column** — same text, translatable via the embedded Google Translate widget or Chrome's built-in translate

Supported input types: PDF, Word (.docx), EPUB, HTML, Markdown, plain text, reStructuredText, LaTeX, ODT, and web URLs.

---

## Instructions

The user has invoked `/sideread` with: **$ARGUMENTS**

Parse `$ARGUMENTS` as: `<input> [pages] [output]`

| Argument | Required | Description |
|----------|----------|-------------|
| `input` | yes | File path (absolute or relative, `~` expanded) or a URL (`http`/`https`) |
| `pages` | no | Page range for PDFs, e.g. `1-10`, `3`, `5-20`. Only meaningful for PDF input. Omit to process the whole file. |
| `output` | no | Output HTML path. Default: same directory as input, same stem, `.html` extension. For URLs: `/tmp/sideread_output.html`. |

**Parsing `pages`:** if the second token looks like a page range (digits, `-`, or a single number), treat it as `pages`; otherwise treat it as `output`.
Examples: `paper.pdf 1-20` → pages=`1-20`; `paper.pdf out.html` → output=`out.html`; `paper.pdf 5 out.html` → pages=`5`, output=`out.html`.

The builder script lives at: `~/Documents/Github/sideread/build.py`

---

## Step-by-step

### 1. Resolve paths, validate input, and detect type

- Expand `~` and resolve relative paths to absolute using the current working directory.
- **Check the file exists before doing anything else.**
  - Run `ls "<absolute_path>"` (or `test -f`).
  - If the file is not found, stop immediately and tell the user:
    - The exact path you looked for
    - List the files in that directory (`ls "<directory>"`) so the user can spot the typo
    - Suggest the closest-looking filename if one is visible
  - Do NOT proceed with a missing file.
- Detect input type from file extension or URL scheme:
  - URL (`http://` or `https://`) → **web**
  - `.pdf` → **pdf**
  - `.docx`, `.doc` → **word**
  - `.epub` → **epub**
  - `.html`, `.htm` → **html**
  - `.md`, `.markdown` → **markdown**
  - `.rst` → **rst**
  - `.tex` → **latex**
  - `.odt` → **odt**
  - `.txt` → **plain**
  - anything else → try pandoc, fallback to Read tool

- Derive the output path if not provided:
  - For files: replace extension with `.html`, keep same directory
  - For URLs: use `/tmp/sideread_output.html`

- Derive a human-readable title:
  - For files: the filename stem, prettified (replace `-_` with spaces, title-case)
  - For URLs: the URL hostname + path stem

### 2. Extract content → `/tmp/sideread_input.md`

**For URLs:**
1. Use the WebFetch tool with the URL and prompt: "Return the full main body text of this page in clean markdown, preserving all headings, lists, tables, and paragraphs. Do not summarize."
2. Write the returned markdown to `/tmp/sideread_input.md`
3. Go to Step 3.

**For PDF:**

First, check whether a hand-crafted markdown file already exists alongside the PDF
(same directory, same filename stem, `.md` extension, e.g. `paper.pdf` → `paper.md`).
If it exists, use it directly as `/tmp/sideread_input.md` and skip to Step 3 —
it is higher quality than anything extracted from the PDF.

Otherwise, extract from the PDF:
1. Use the Read tool to read the file with the following page strategy:
   - **If the user supplied a `pages` argument** (e.g. `1-10`, `5`, `3-7`):
     read only those pages: `pages: "<pages>"`. Mention to the user which pages
     were processed so they know the output is partial.
   - **If no `pages` argument** and the PDF is ≤ 20 pages: read all at once.
   - **If no `pages` argument** and the PDF is > 20 pages: read in chunks of 20
     (e.g. `pages: "1-20"`, then `"21-40"`, etc.) and concatenate all chunks.
   - If the Read tool returns empty or garbled text for a page range, warn the
     user: the PDF may be scanned/image-only for those pages and has no text layer.
     Suggest: (a) use `pages` to skip the problematic range, or (b) pre-process
     with `ocrmypdf input.pdf output.pdf` to add a text layer.
2. **Critically important — reformat as structured markdown before writing:**
   You MUST actively identify and convert document structure. Do NOT dump raw text.
   Apply these rules as you write `/tmp/sideread_input.md`:
   - **Headings:** Any line that is a section title (e.g. "I. INTRODUCTION",
     "A. Definition", numbered or lettered sections, ALL-CAPS titles) → convert
     to the appropriate `#` / `##` / `###` / `####` heading level.
   - **Lists:** Bullet points or numbered items in the PDF → markdown `- ` or `1. ` lists.
   - **Tables:** Tabular content → markdown pipe tables.
   - **Footnotes:** Numbered footnotes → markdown `[^N]` inline + `[^N]: text` at bottom.
   - **Emphasis:** Bold/italic text → `**bold**` / `*italic*`.
   - **Paragraphs:** Separate paragraphs with a blank line.
   - Do NOT include page headers, page footers, or page numbers.
   - Preserve ALL body content — do not summarize or skip any section.
3. Write the fully structured markdown to `/tmp/sideread_input.md`.
4. Go to Step 3.

**For all other file types (docx, epub, html, md, rst, tex, odt, txt):**
1. Run pandoc directly on the file in Step 3 — no pre-extraction needed.
2. Skip to Step 3 but pass the original file to pandoc.

### 3. Quality-check the markdown (PDF and URL only)

Before running pandoc, verify `/tmp/sideread_input.md` has good structure:
- Count lines starting with `#` — there should be **at least one heading per major section**.
- If the file has zero or very few headings (e.g. fewer than 3 for a multi-section document),
  the extraction missed structure. Go back to Step 2 and redo it more carefully,
  explicitly scanning for section titles in the raw text and converting them.

### 4. Convert to HTML body fragment → `/tmp/sideread_body.html`

Run the appropriate pandoc command:

```bash
# For types pre-extracted to /tmp/sideread_input.md (URL, PDF):
pandoc /tmp/sideread_input.md \
  -o /tmp/sideread_body.html \
  --syntax-highlighting=none

# For directly supported file types:
pandoc "<absolute_input_path>" \
  -o /tmp/sideread_body.html \
  --syntax-highlighting=none
```

If pandoc exits with an error, fall back: use the Read tool to read the file, write content to `/tmp/sideread_input.md`, then re-run pandoc on that.

### 5. Build the bilingual HTML

Run:
```bash
python3 ~/Documents/Github/sideread/build.py \
  --input /tmp/sideread_body.html \
  --output "<absolute_output_path>" \
  --title "<derived title>" \
  --source-label "<TYPE>"
```

Where `<TYPE>` is one of: `PDF`, `Word`, `EPUB`, `HTML`, `Markdown`, `URL`, `Text`, etc.

### 6. Clean up temp files

```bash
rm -f /tmp/sideread_input.md /tmp/sideread_body.html
```

### 7. Open the output in the browser

```bash
open "<absolute_output_path>"
```

This opens the file in the system default browser (Chrome on most macOS setups). Run this immediately after cleanup — do not wait for user input.

### 8. Report to user

Tell the user:
- The output file path (as a clickable path)
- How many block elements were processed (printed by build.py)
- That the file has been opened in the browser — select a language from the dropdown in the header to translate the right column; the left column always stays in the original language
- Reminder that an internet connection is needed for the Google Translate widget

---

## Error handling

| Problem | Action |
|---------|--------|
| **File not found** | Stop. Show the exact path tried, list files in that directory, suggest closest match |
| **Typo in filename** | Same as above — never guess silently; always show the directory listing |
| pandoc not installed | Tell user: `brew install pandoc` |
| beautifulsoup4 not installed | Tell user: `pip3 install beautifulsoup4` |
| PDF has no text layer (scanned/image-only) | Warn user; suggest `ocrmypdf input.pdf output.pdf` to add text layer first; or try a narrower `pages` range to skip blank pages |
| PDF output looks unstructured (wall of text, no headings) | A hand-crafted `paper.md` alongside `paper.pdf` will always win — tell the user they can create one for best results |
| `pages` range out of bounds | Warn user and suggest checking total page count |
| URL fetch fails | Tell user and suggest downloading the file manually |
| Very large PDF, no `pages` given | Warn that processing all pages may take a moment; suggest using `pages` to limit scope |

---

## Examples

```
# Basic usage
/sideread ~/Downloads/fda-guidance.pdf

# Specific pages only (e.g. skip front matter, process pages 5–30)
/sideread ~/Downloads/long-report.pdf 5-30

# Single page
/sideread ~/Downloads/paper.pdf 3

# Pages + custom output path
/sideread ~/Downloads/paper.pdf 1-20 ~/Desktop/paper-bilingual.html

# Word / other formats (pages argument not applicable)
/sideread ~/Documents/report.docx ~/Desktop/report-bilingual.html

# URL
/sideread https://www.nejm.org/doi/full/10.1056/NEJMoa2400000

# Markdown
/sideread ~/notes/meeting.md
```
