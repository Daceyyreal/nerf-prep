"""Validate an input folder before handing it to COLMAP.

Catches the failure modes that waste a full COLMAP run: too few images to
register, double file extensions (``IMG_001.jpg.jpg``) that COLMAP silently
skips, and mixed/non-image files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SUPPORTED = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}

# Below this, COLMAP often fails to build a connected model.
MIN_RECOMMENDED = 20


@dataclass
class InputReport:
    images: list[Path]
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.images)

    @property
    def ok(self) -> bool:
        # Warnings are advisory; a run is blocked only if there are no images.
        return self.count > 0


def scan_images(folder: Path) -> list[Path]:
    """Return sorted image files directly inside ``folder`` (non-recursive)."""
    return sorted(
        p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED
    )


def _has_double_extension(p: Path) -> bool:
    # e.g. "IMG_1.jpg.jpg" -> stem "IMG_1.jpg" whose own suffix is an image ext.
    return Path(p.stem).suffix.lower() in SUPPORTED


def validate(folder: Path) -> InputReport:
    if not folder.is_dir():
        raise NotADirectoryError(f"input folder does not exist: {folder}")

    images = scan_images(folder)
    report = InputReport(images=images)

    if report.count == 0:
        report.warnings.append(
            f"no supported images found in {folder} "
            f"(looked for {', '.join(sorted(SUPPORTED))})"
        )
        return report

    if report.count < MIN_RECOMMENDED:
        report.warnings.append(
            f"only {report.count} images; COLMAP often fails to register a "
            f"connected model below ~{MIN_RECOMMENDED}. Capture more overlap."
        )

    doubles = [p.name for p in images if _has_double_extension(p)]
    if doubles:
        sample = ", ".join(doubles[:3])
        report.warnings.append(
            f"{len(doubles)} file(s) have a double extension (e.g. {sample}); "
            "COLMAP may skip these. Rename to a single extension."
        )

    exts = {p.suffix.lower() for p in images}
    if len(exts) > 1:
        report.warnings.append(
            f"mixed image extensions ({', '.join(sorted(exts))}); harmless but "
            "worth a glance in case a non-image file slipped in."
        )

    return report
