from pathlib import Path
import json
import logging
import typer
from .core.batch_runner import run_batch

app = typer.Typer(no_args_is_help=True, add_completion=False, help="Batch image background removal and normalization.")

@app.command("version")
def version() -> None:
    """Print the installed pixel-strip version."""
    from . import __version__
    typer.echo(__version__)

@app.command()
def run(
    input: Path = typer.Option(..., "--input", exists=True, file_okay=False, dir_okay=True, readable=True),
    output: Path = typer.Option(..., "--output", file_okay=False, dir_okay=True),
    workers: int = typer.Option(1, "--workers", min=1),
    backend: str = typer.Option("rembg", "--backend"),
    width: int | None = typer.Option(None, "--width", min=1),
    height: int | None = typer.Option(None, "--height", min=1),
    padding: int = typer.Option(0, "--padding", min=0),
    output_format: str = typer.Option("png", "--format", case_sensitive=False),
    dpi: int = typer.Option(72, "--dpi", min=1),
    overwrite: bool = typer.Option(False, "--overwrite"),
) -> None:
    """Process every supported image recursively and write normalized output."""
    if (width is None) != (height is None):
        raise typer.BadParameter("--width and --height must be supplied together")
    fmt = output_format.lower()
    if fmt not in {"png", "webp"}:
        raise typer.BadParameter("--format must be png or webp")
    if input.resolve() == output.resolve() or output.resolve().is_relative_to(input.resolve()):
        raise typer.BadParameter("--output must not be the input directory or a directory inside it")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        results = run_batch(input, output, backend, workers, width, height, padding, fmt, dpi, overwrite,
                            lambda r: logging.getLogger("pixelstrip").info(json.dumps(r, sort_keys=True)))
    except (ValueError, RuntimeError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    counts = {s: sum(r["status"] == s for r in results) for s in ("processed", "skipped", "failed")}
    typer.echo(f"processed={counts['processed']} skipped={counts['skipped']} failed={counts['failed']}")
    if counts["failed"]:
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
