"""Decide COLMAP settings and assemble the ``ns-process-data`` command.

The opinionated bits live here: pick a matcher that fits the image count and
capture style, and drop ``--no-gpu`` automatically when there is no usable GPU
(so the same command works on a Kaggle T4 *and* a CPU-only box).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Exhaustive matching is O(n^2) pairs but most accurate. It stays cheap enough
# for a few hundred unordered photos; beyond that, vocab-tree scales better.
EXHAUSTIVE_MAX = 200

VALID_MATCHERS = {"exhaustive", "sequential", "vocab_tree"}
VALID_CAPTURES = {"photos", "video"}


def choose_matcher(n_images: int, capture: str = "photos") -> str:
    """Pick a matching method.

    - video frames are temporally ordered -> ``sequential``
    - unordered photos -> ``exhaustive`` while small, else ``vocab_tree``
    """
    if capture not in VALID_CAPTURES:
        raise ValueError(f"capture must be one of {sorted(VALID_CAPTURES)}; got {capture!r}")
    if capture == "video":
        return "sequential"
    return "exhaustive" if n_images <= EXHAUSTIVE_MAX else "vocab_tree"


def detect_gpu() -> bool:
    """True if an NVIDIA GPU appears usable (``nvidia-smi`` runs cleanly)."""
    if shutil.which("nvidia-smi") is None:
        return False
    try:
        return subprocess.run(["nvidia-smi"], capture_output=True, timeout=10).returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def build_command(
    input_path: Path,
    output_dir: Path,
    *,
    matcher: str,
    downscales: int = 3,
    gpu: bool = True,
    capture: str = "photos",
) -> list[str]:
    """Assemble the ``ns-process-data`` argv.

    ``input_path`` is a folder for photos and a video file for video.
    """
    if matcher not in VALID_MATCHERS:
        raise ValueError(f"matcher must be one of {sorted(VALID_MATCHERS)}; got {matcher!r}")

    subcmd = "video" if capture == "video" else "images"
    cmd = [
        "ns-process-data",
        subcmd,
        "--data",
        str(input_path),
        "--output-dir",
        str(output_dir),
        "--matching-method",
        matcher,
        "--num-downscales",
        str(downscales),
    ]
    if not gpu:
        cmd.append("--no-gpu")
    return cmd
