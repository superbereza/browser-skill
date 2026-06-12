#!/usr/bin/env bash
# Put the `browser` CLI on your shell PATH (~/.local/bin). The launcher bootstraps
# its own venv on first run — no manual pip needed. The skill itself is delivered by
# the plugin/marketplace (or your agent's manifest), so this does NOT symlink it.
set -euo pipefail

repo_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

bin_dir="$HOME/.local/bin"

chmod +x "$repo_dir/bin/browser"
mkdir -p "$bin_dir"

ln -sfn "$repo_dir/bin/browser"               "$bin_dir/browser"

echo "Installed: $bin_dir/browser"
echo
echo "First run will create a venv and install deps. Try: browser --help"
