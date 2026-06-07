# nerf-prep image: COLMAP + Nerfstudio + nerf-prep, with the common docker
# gotchas pre-fixed (writable HOME, matplotlib cache, headless display).
#
# Pin the tag to a build you have verified; :latest drifts.
FROM ghcr.io/nerfstudio-project/nerfstudio:latest

# Links the published ghcr package to the repo (populates "Connect repository").
LABEL org.opencontainers.image.source="https://github.com/Daceyyreal/nerf-prep"
LABEL org.opencontainers.image.description="One command: a folder of photos -> a Nerfstudio-ready dataset."
LABEL org.opencontainers.image.licenses="MIT"

# --- Fix the well-known "ns-process-data crashes on unset $HOME" bug --------
# (FileNotFoundError: '/.local/share/nerfstudio'; matplotlib cache not writable)
ENV HOME=/opt/nerfprep-home \
    MPLCONFIGDIR=/tmp/mpl
RUN mkdir -p "$HOME/.local/share/nerfstudio" "$HOME/.config" "$MPLCONFIGDIR" \
    && chmod -R 777 "$HOME" "$MPLCONFIGDIR"

# --- Headless display so COLMAP's GL/Qt feature extractor doesn't choke ------
USER root
RUN apt-get update && apt-get install -y --no-install-recommends xvfb \
    && rm -rf /var/lib/apt/lists/*

# --- Install nerf-prep -------------------------------------------------------
COPY . /opt/nerf-prep
RUN python -m pip install --no-cache-dir /opt/nerf-prep

WORKDIR /workspace
COPY docker-entrypoint.sh /usr/local/bin/nerf-prep-entry
RUN chmod +x /usr/local/bin/nerf-prep-entry

# Wrap every invocation in a virtual framebuffer for headless COLMAP.
ENTRYPOINT ["/usr/local/bin/nerf-prep-entry"]
CMD ["--help"]
