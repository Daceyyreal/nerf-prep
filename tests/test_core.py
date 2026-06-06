"""Unit tests for the parts that don't need COLMAP installed."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from nerf_prep import engine, inputs, summary


# --- matcher selection ---------------------------------------------------

def test_video_is_sequential():
    assert engine.choose_matcher(500, "video") == "sequential"


def test_small_photo_set_exhaustive():
    assert engine.choose_matcher(50, "photos") == "exhaustive"
    assert engine.choose_matcher(engine.EXHAUSTIVE_MAX, "photos") == "exhaustive"


def test_large_photo_set_vocab_tree():
    assert engine.choose_matcher(engine.EXHAUSTIVE_MAX + 1, "photos") == "vocab_tree"


def test_bad_capture_raises():
    with pytest.raises(ValueError):
        engine.choose_matcher(10, "lidar")


# --- command building ----------------------------------------------------

def test_command_adds_no_gpu_when_cpu():
    cmd = engine.build_command(Path("in"), Path("out"), matcher="exhaustive", gpu=False)
    assert "--no-gpu" in cmd
    assert cmd[1] == "images"


def test_command_omits_no_gpu_with_gpu():
    cmd = engine.build_command(Path("in"), Path("out"), matcher="exhaustive", gpu=True)
    assert "--no-gpu" not in cmd
    assert "--matching-method" in cmd and "exhaustive" in cmd


def test_video_subcommand():
    cmd = engine.build_command(Path("v.mp4"), Path("out"), matcher="sequential", capture="video")
    assert cmd[1] == "video"


# --- input validation ----------------------------------------------------

def test_double_extension_flagged(tmp_path: Path):
    (tmp_path / "IMG_1.jpg.jpg").write_bytes(b"x")
    (tmp_path / "IMG_2.jpg").write_bytes(b"x")
    rep = inputs.validate(tmp_path)
    assert rep.count == 2
    assert any("double extension" in w for w in rep.warnings)


def test_too_few_images_warns(tmp_path: Path):
    for i in range(3):
        (tmp_path / f"{i}.png").write_bytes(b"x")
    rep = inputs.validate(tmp_path)
    assert any("only 3 images" in w for w in rep.warnings)


def test_empty_folder_not_ok(tmp_path: Path):
    rep = inputs.validate(tmp_path)
    assert not rep.ok


# --- summary -------------------------------------------------------------

def test_summary_rate_and_health(tmp_path: Path):
    (tmp_path / "transforms.json").write_text(json.dumps({"frames": [{}] * 90}))
    s = summary.summarize(tmp_path, n_input=100)
    assert s.registered == 90
    assert s.healthy
    assert s.next_command().startswith("ns-train splatfacto")


def test_summary_low_registration_unhealthy(tmp_path: Path):
    (tmp_path / "transforms.json").write_text(json.dumps({"frames": [{}] * 40}))
    s = summary.summarize(tmp_path, n_input=100)
    assert not s.healthy


def test_summary_missing_transforms(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        summary.summarize(tmp_path, n_input=10)
