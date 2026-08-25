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
from drawing_check.pipeline import chay_1_file, tim_du_an_khop
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
    vision: bool = typer.Option(
        False,
        "--vision/--no-vision",
        help="Bat detector RT-DETR (Phase 4, symbol WARN) - can GPU/torch/transformers + model "
        "da train (models/rtdetr_symbols_v1/best/), cham hon nhieu. Mac dinh TAT.",
    ),
) -> None:
    """Chay kiem tra tren cac file PDF khop PATTERN (vd "D:\\BanVe\\*.pdf").

    Tu dong nap TOAN BO profile trong config/projects/*.yaml (bo qua file bat dau bang "_", vd
    _vi_du.yaml - chi la mau minh hoa) va tu khop dung profile theo TUNG TRANG qua drawing_no (xem
    pipeline.py::tim_du_an_khop) - khong con option chon 1 profile cho ca luot chay, vi 1 file PDF
    co the tron nhieu du an khac nhau (da gap thuc te 2026-08-24: MH612 lan voi M2613/VPK25-01/03).
    """
    duong_dan_khop = sorted(glob_module.glob(pattern))
    if not duong_dan_khop:
        typer.echo(f"Khong tim thay file PDF nao khop '{pattern}'.")
        raise typer.Exit(code=1)

    danh_sach_du_an = [
        yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        for p in sorted((THU_MUC_GOC / "config" / "projects").glob("*.yaml"))
        if not p.name.startswith("_")
    ]

    vat_lieu_path = THU_MUC_GOC / "config" / "catalogs" / "materials.yaml"
    danh_muc_vat_lieu = yaml.safe_load(vat_lieu_path.read_text(encoding="utf-8")) or {}
    iso286_path = THU_MUC_GOC / "config" / "catalogs" / "iso286_letters.yaml"
    danh_muc_iso286 = yaml.safe_load(iso286_path.read_text(encoding="utf-8")) or {}
    catalogs = {"materials": danh_muc_vat_lieu.get("materials", []), "iso286": danh_muc_iso286}

    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")

    dau_thoi_gian = datetime.now().strftime("%Y%m%d-%H%M%S")
    thu_muc_output = THU_MUC_GOC / "output"
    duong_dan_excel = thu_muc_output / f"{dau_thoi_gian}-ket_qua.xlsx"
    thu_muc_pdf_khoanh = thu_muc_output / f"{dau_thoi_gian}-pdf_da_khoanh"

    trang_list: list[PageDoc] = []
    findings: list[Finding] = []
    for duong_dan_str in duong_dan_khop:
        duong_dan = Path(duong_dan_str)
        trang_1_file, findings_1_file = chay_1_file(
            duong_dan, rules, danh_sach_du_an, catalogs, chay_vision=vision
        )
        trang_list.extend(trang_1_file)
        findings.extend(findings_1_file)
        khoanh_do_1_file(duong_dan, findings_1_file, thu_muc_pdf_khoanh / duong_dan.name)

    ban_ve_list = gom_trang_thanh_ban_ve(trang_list)
    for ban_ve in ban_ve_list:
        context_ban_ve = {"project": tim_du_an_khop(ban_ve.drawing_no, danh_sach_du_an) or {}}
        findings.extend(chay_rule_tren_ban_ve(ban_ve, rules, context_ban_ve))

    in_bao_cao(findings, so_trang=len(trang_list), so_ban_ve=len(ban_ve_list))
    xuat_excel(findings, duong_dan_excel)

    typer.echo(f"Da ghi Excel: {duong_dan_excel}")
    typer.echo(f"Da ghi PDF khoanh do: {thu_muc_pdf_khoanh}")

    if any(f.level == "FAIL" for f in findings):
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
