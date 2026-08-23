"""CLI cua Drawing Check (typer). Lenh 'run' that su can extractor PDF - chua san sang toi Phase 1
co du du lieu tu Phase 0 (template khung ten do tu ban ve that)."""

from __future__ import annotations

import typer

from drawing_check import __version__

app = typer.Typer(help="Drawing Check - kiem tra ban ve ky thuat PDF tu dong")


@app.command()
def version() -> None:
    """In phien ban hien tai."""
    typer.echo(__version__)


@app.command()
def run(pattern: str) -> None:
    """Chay kiem tra tren cac file PDF khop PATTERN (vd "D:\\BanVe\\*.pdf")."""
    typer.echo(
        "Chua san sang: extractor PDF that (extract/pdf_page.py, extract/titleblock.py) can "
        "template khung ten do tu ban ve that (Phase 0) truoc khi lenh nay chay duoc."
    )
    raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
