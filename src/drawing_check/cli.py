"""CLI cua Drawing Check (typer). Lenh 'run' dung extractor khung ten mau "Alpha Vina A3/A4"
(extract/titleblock.py) - mau khung ten CONG TY duy nhat da co cua Phase 1, xem docstring dau
file titleblock.py."""

from __future__ import annotations

import glob as glob_module
from datetime import datetime
from pathlib import Path

import typer
import yaml

from drawing_check import __version__
from drawing_check.core.finding import Finding
from drawing_check.core.grouping import gom_trang_thanh_ban_ve
from drawing_check.core.model import PageDoc
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.runner import chay_rule_tren_ban_ve
from drawing_check.pipeline import chay_1_file
from drawing_check.report.console import in_bao_cao
from drawing_check.report.excel import xuat_excel
from drawing_check.report.pdf_markup import khoanh_do_1_file

THU_MUC_GOC = Path(__file__).resolve().parent.parent.parent

app = typer.Typer(help="Drawing Check - kiem tra ban ve ky thuat PDF tu dong")


@app.command()
def version() -> None:
    """In phien ban hien tai."""
    typer.echo(__version__)


@app.command()
def run(
    pattern: str,
    du_an: str = typer.Option(
        "mh612", "--du-an", help="Ten profile du an trong config/projects/ (khong can duoi .yaml)"
    ),
) -> None:
    """Chay kiem tra tren cac file PDF khop PATTERN (vd "D:\\BanVe\\*.pdf")."""
    duong_dan_khop = sorted(glob_module.glob(pattern))
    if not duong_dan_khop:
        typer.echo(f"Khong tim thay file PDF nao khop '{pattern}'.")
        raise typer.Exit(code=1)

    du_an_path = THU_MUC_GOC / "config" / "projects" / f"{du_an}.yaml"
    if not du_an_path.exists():
        typer.echo(f"Khong tim thay profile du an '{du_an_path}'.")
        raise typer.Exit(code=1)
    project = yaml.safe_load(du_an_path.read_text(encoding="utf-8")) or {}

    vat_lieu_path = THU_MUC_GOC / "config" / "catalogs" / "materials.yaml"
    danh_muc_vat_lieu = yaml.safe_load(vat_lieu_path.read_text(encoding="utf-8")) or {}
    context = {
        "project": project,
        "catalogs": {"materials": danh_muc_vat_lieu.get("materials", [])},
    }

    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")

    dau_thoi_gian = datetime.now().strftime("%Y%m%d-%H%M%S")
    thu_muc_output = THU_MUC_GOC / "output"
    duong_dan_excel = thu_muc_output / f"{dau_thoi_gian}-ket_qua.xlsx"
    thu_muc_pdf_khoanh = thu_muc_output / f"{dau_thoi_gian}-pdf_da_khoanh"

    trang_list: list[PageDoc] = []
    findings: list[Finding] = []
    for duong_dan_str in duong_dan_khop:
        duong_dan = Path(duong_dan_str)
        trang_1_file, findings_1_file = chay_1_file(duong_dan, rules, context)
        trang_list.extend(trang_1_file)
        findings.extend(findings_1_file)
        khoanh_do_1_file(duong_dan, findings_1_file, thu_muc_pdf_khoanh / duong_dan.name)

    ban_ve_list = gom_trang_thanh_ban_ve(trang_list)
    for ban_ve in ban_ve_list:
        findings.extend(chay_rule_tren_ban_ve(ban_ve, rules, context))

    in_bao_cao(findings, so_trang=len(trang_list), so_ban_ve=len(ban_ve_list))
    xuat_excel(findings, duong_dan_excel)

    typer.echo(f"Da ghi Excel: {duong_dan_excel}")
    typer.echo(f"Da ghi PDF khoanh do: {thu_muc_pdf_khoanh}")

    if any(f.level == "FAIL" for f in findings):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
