#!/usr/bin/env bash
# Run nerf-prep inside a virtual framebuffer so COLMAP's GL/Qt code works on a
# headless box (servers, Kaggle, CI). Falls back to running directly if xvfb
# is unavailable.
set -euo pipefail

# Belt-and-braces: make sure the nerfstudio/matplotlib dirs exist and are ours.
mkdir -p "${HOME}/.local/share/nerfstudio" "${HOME}/.config" "${MPLCONFIGDIR:-/tmp/mpl}" 2>/dev/null || true

if command -v xvfb-run >/dev/null 2>&1; then
  exec xvfb-run -a nerf-prep "$@"
else
  exec nerf-prep "$@"
fi
