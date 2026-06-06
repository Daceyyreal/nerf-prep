"""nerf-prep command-line interface."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer

from . import engine, inputs, summary

app = typer.Typer(
    add_completion=False,
    help="Turn a folder of photos into a Nerfstudio-ready dataset in one command.",
)


@app.callback()
def _main() -> None:
    """nerf-prep: photos in, a Nerfstudio-ready dataset out."""


@app.command()
def run(
    input_path: Path = typer.Argument(..., help="Folder of images (or a video file with --capture video)."),
    output_dir: Path = typer.Argument(..., help="Where the processed dataset is written."),
    capture: str = typer.Option("photos", help="photos | video"),
    matcher: str = typer.Option("auto", help="auto | exhaustive | sequential | vocab_tree"),
    downscales: int = typer.Option(3, help="Number of downscaled image pyramids COLMAP/Nerfstudio generate."),
    gpu: str = typer.Option("auto", help="auto | on | off  (auto detects nvidia-smi)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the command instead of running it."),
) -> None:
    """Validate input, pick sane COLMAP settings, run ns-process-data, then summarise."""
    report = inputs.validate(input_path) if capture == "photos" else inputs.InputReport(images=[])
    n_input = report.count if capture == "photos" else 0

    if capture == "photos":
        for w in report.warnings:
            typer.secho(f"  warning: {w}", fg=typer.colors.YELLOW)
        if not report.ok:
            raise typer.Exit(code=1)
        typer.echo(f"Found {n_input} images.")

    use_gpu = engine.detect_gpu() if gpu == "auto" else (gpu == "on")
    chosen = engine.choose_matcher(n_input, capture) if matcher == "auto" else matcher
    typer.echo(f"Matcher: {chosen}   GPU: {'yes' if use_gpu else 'no (COLMAP on CPU)'}")

    cmd = engine.build_command(
        input_path, output_dir, matcher=chosen, downscales=downscales, gpu=use_gpu, capture=capture
    )

    if dry_run:
        typer.echo("DRY RUN, would execute:")
        typer.echo("  " + " ".join(cmd))
        raise typer.Exit()

    typer.echo("Running: " + " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        typer.secho("ns-process-data failed; see the log above.", fg=typer.colors.RED)
        raise typer.Exit(code=result.returncode)

    if capture == "photos":
        s = summary.summarize(output_dir, n_input)
        colour = typer.colors.GREEN if s.healthy else typer.colors.YELLOW
        typer.secho(
            f"Registered {s.registered}/{s.n_input} images ({s.rate:.0%}).", fg=colour
        )
        if not s.healthy:
            typer.secho(
                "  Low registration: try more overlapping captures or a textured background.",
                fg=typer.colors.YELLOW,
            )
        typer.echo("\nNext:\n  " + s.next_command())


if __name__ == "__main__":
    app()
