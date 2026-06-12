#!/usr/bin/env bash
# Remove the symlinks created by install.sh.
set -euo pipefail

bin_dir="$HOME/.local/bin"

[[ -L "$bin_dir/browser" ]] && rm -v "$bin_dir/browser" || true

echo "Uninstalled. (The repo's ./.venv and the profile at ~/.browser-skill are left in place — remove them by hand if you want.)"
