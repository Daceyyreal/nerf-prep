# nerf-prep

**One command, a folder of photos in, a Nerfstudio-ready dataset out — no install hell.**

[![Release](https://img.shields.io/github/v/release/Daceyyreal/nerf-prep?sort=semver)](https://github.com/Daceyyreal/nerf-prep/releases/latest)
[![CI](https://github.com/Daceyyreal/nerf-prep/actions/workflows/ci.yml/badge.svg)](https://github.com/Daceyyreal/nerf-prep/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Getting from raw photos to a trainable 3D Gaussian Splatting / NeRF dataset means
getting COLMAP and Nerfstudio to cooperate — matching strategy, GPU vs CPU,
headless display, and a pile of small gotchas that each cost a full re-run.
`nerf-prep` wraps that into one Dockerized command with sensible defaults baked
in, so the same call works on a cloud T4 or a CPU-only laptop.

```bash
docker run --gpus all --ipc=host \
  -v "$(pwd)/images:/workspace/images" \
  -v "$(pwd)/dataset:/workspace/dataset" \
  ghcr.io/daceyyreal/nerf-prep:latest \
  run /workspace/images /workspace/dataset
# -> dataset/ ready for:  ns-train splatfacto --data dataset
```

## What it does for you

- **Picks the matcher for you** — exhaustive for small unordered photo sets,
  vocab-tree once they get large, sequential for video frames.
- **GPU/CPU auto-detect** — drops `--no-gpu` automatically when no NVIDIA GPU is
  visible, so COLMAP still runs (just slower) instead of crashing.
- **Headless by default** — runs inside a virtual framebuffer, so COLMAP's GL/Qt
  feature extractor works on servers and CI.
- **Pre-empts the input mistakes** — flags double extensions (`IMG.jpg.jpg`),
  too-few images, and stray non-image files *before* a 40-minute COLMAP run.
- **Honest summary** — reports the registration rate (how many photos actually
  got a pose) and prints the exact `ns-train` command to run next.

The image also patches the well-known Nerfstudio-in-Docker bug where
`ns-process-data` crashes on an unset `$HOME` (unwritable
`~/.local/share/nerfstudio` and matplotlib cache).

## Usage

```bash
# Inside the container (or any box with COLMAP + nerfstudio installed):
nerf-prep run images/ dataset/                 # photos, auto everything
nerf-prep run clip.mp4 dataset/ --capture video
nerf-prep run images/ dataset/ --gpu off       # force CPU COLMAP
nerf-prep run images/ dataset/ --dry-run       # print the command, run nothing
```

| Option | Default | Notes |
|--------|---------|-------|
| `--capture` | `photos` | `photos` or `video` |
| `--matcher` | `auto` | `auto`/`exhaustive`/`sequential`/`vocab_tree` |
| `--downscales` | `3` | image pyramid levels |
| `--gpu` | `auto` | `auto`/`on`/`off` |
| `--dry-run` | off | print the `ns-process-data` command only |

## Local install (without Docker)

Requires COLMAP and Nerfstudio already on your `PATH`.

```bash
pip install -e ".[dev]"
nerf-prep run images/ dataset/ --dry-run
```

## Roadmap

- [ ] Direct COLMAP orchestration (`--engine colmap`) for full control over the
  feature/match/map stages, instead of going through `ns-process-data`.
- [ ] Resume a partially-finished run.
- [ ] Optional point-cloud init export for splatfacto.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Stands on [COLMAP](https://colmap.github.io/) and
[Nerfstudio](https://github.com/nerfstudio-project/nerfstudio).
