#!/usr/bin/env bash
# Run nerf-prep inside a virtual framebuffer so COLMAP's GL/Qt code works on a
# headless box (servers, Kaggle, CI). Falls back to running directly if xvfb
# is unavailable.
set -euo pipefail

# Belt-and-braces: make sure the nerfstudio/matplotlib dirs exist and are ours.
mkdir -p "${HOME}/.local/share/nerfstudio" "${HOME}/.config" "${MPLCONFIGDIR:-/tmp/mpl}" 2>/dev/null || true

# Start a virtual framebuffer manually rather than via `xvfb-run`, which can
# hang indefinitely under some container runtimes (observed on Docker Desktop /
# WSL2: the wrapper blocks before exec'ing the command). Launching Xvfb directly
# and exporting DISPLAY is equivalent and reliable.
if command -v Xvfb >/dev/null 2>&1; then
  Xvfb :99 -screen 0 1280x1024x24 >/dev/null 2>&1 &
  XVFB_PID=$!
  export DISPLAY=:99
  # Give Xvfb a moment to come up before COLMAP tries to open a GL context.
  for _ in $(seq 1 25); do
    if [ -S /tmp/.X11-unix/X99 ]; then break; fi
    sleep 0.2
  done
  trap 'kill "${XVFB_PID}" 2>/dev/null || true' EXIT
fi

exec nerf-prep "$@"
