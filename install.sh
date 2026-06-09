#!/usr/bin/env bash
# Symlink `browser` into ~/.local/bin and SKILL.md into ~/.claude/skills.
# The launcher bootstraps its own venv on first run — no manual pip needed.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

bin_dir="$HOME/.local/bin"
skill_dir="$HOME/.claude/skills/browser"

chmod +x "$repo_dir/bin/browser"
mkdir -p "$bin_dir" "$skill_dir"

ln -sfn "$repo_dir/bin/browser"               "$bin_dir/browser"
ln -sfn "$repo_dir/skills/browser/SKILL.md"   "$skill_dir/SKILL.md"

echo "Installed:"
echo "  $bin_dir/browser"
echo "  $skill_dir/SKILL.md"
echo
echo "First run will create a venv and install deps. Try: browser --help"
