#!/usr/bin/env bash
# Remove the symlinks created by install.sh.
set -euo pipefail

bin_dir="$HOME/.local/bin"
skill_dir="$HOME/.claude/skills/browser"

for f in "$bin_dir/browser" "$skill_dir/SKILL.md"; do
    [[ -L "$f" ]] && rm -v "$f" || true
done
[[ -d "$skill_dir" && -z "$(ls -A "$skill_dir" 2>/dev/null)" ]] && rmdir -v "$skill_dir" || true

echo "Uninstalled. (The repo's ./.venv and the profile at ~/.browser-skill are left in place — remove them by hand if you want.)"
