"""Summarise a finished run by reading the Nerfstudio ``transforms.json``.

The single number that tells you whether COLMAP succeeded is the *registration
rate*: how many input images actually got a camera pose. A low rate means weak
overlap or texture, not a training problem.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunSummary:
    registered: int
    n_input: int
    output_dir: Path

    @property
    def rate(self) -> float:
        return self.registered / self.n_input if self.n_input else 0.0

    @property
    def healthy(self) -> bool:
        # COLMAP dropping a few frames is normal; losing a third is a red flag.
        return self.rate >= 0.7

    def next_command(self, model: str = "splatfacto") -> str:
        return f"ns-train {model} --data {self.output_dir}"


def summarize(output_dir: Path, n_input: int) -> RunSummary:
    transforms = output_dir / "transforms.json"
    if not transforms.is_file():
        raise FileNotFoundError(
            f"no transforms.json in {output_dir}; COLMAP did not finish. "
            "Check the log above for the failing stage."
        )
    data = json.loads(transforms.read_text())
    registered = len(data.get("frames", []))
    return RunSummary(registered=registered, n_input=n_input, output_dir=output_dir)
