import typer

app = typer.Typer(help= "Batch background removal and image normalization pipeline.")


@app.command()
def version() -> None:
    "Show application version."
    typer.echo("pixel-strip v0.1.0")


if __name__ == "__main__":
    app()