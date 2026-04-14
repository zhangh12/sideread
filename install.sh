#!/usr/bin/env bash
# install.sh — register sideread as a Claude Code user-level slash command
# Usage: bash install.sh

set -e

SKILL_SRC="$(cd "$(dirname "$0")" && pwd)/sideread.md"
COMMANDS_DIR="$HOME/.claude/commands"
SKILL_DST="$COMMANDS_DIR/sideread.md"

echo "=== sideread installer ==="

# ── 1. Claude commands directory ──────────────────────────────────────────
mkdir -p "$COMMANDS_DIR"

if [ -L "$SKILL_DST" ]; then
  echo "  Updating existing symlink: $SKILL_DST"
  ln -sf "$SKILL_SRC" "$SKILL_DST"
elif [ -f "$SKILL_DST" ]; then
  echo "  WARNING: $SKILL_DST already exists as a regular file."
  read -r -p "  Overwrite with symlink? [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]] && ln -sf "$SKILL_SRC" "$SKILL_DST" || echo "  Skipped."
else
  ln -s "$SKILL_SRC" "$SKILL_DST"
  echo "  Installed: $SKILL_DST → $SKILL_SRC"
fi

# ── 2. Check dependencies ─────────────────────────────────────────────────
echo ""
echo "=== Checking dependencies ==="

check() {
  if command -v "$1" &>/dev/null; then
    echo "  ✓ $1 ($(command -v "$1"))"
  else
    echo "  ✗ $1 — NOT FOUND.  Install with: $2"
  fi
}

check pandoc   "brew install pandoc"
check python3  "brew install python3"

if python3 -c "import bs4" &>/dev/null; then
  echo "  ✓ beautifulsoup4"
else
  echo "  ✗ beautifulsoup4 — NOT FOUND.  Install with: pip3 install beautifulsoup4"
fi

# ── 3. Done ───────────────────────────────────────────────────────────────
echo ""
echo "=== Done ==="
echo "  Restart Claude Code (or reload commands), then use:"
echo "    /sideread <file-or-url>"
echo ""
echo "  Examples:"
echo "    /sideread ~/Downloads/paper.pdf"
echo "    /sideread ~/Documents/report.docx"
echo "    /sideread https://example.com/article"
