#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thu_nghiem_titleblock.py - Chay thu extractor khung ten (mau Alpha Vina A3) + rule engine
tren 1-2 trang dau cua 1 file PDF that. KHONG phai CLI chinh thuc (drawing-check run) - day
la cong cu dev de kiem tra extractor dang xay dung, chi ho tro dung 1 mau khung ten duy nhat.

Dung:
    .venv/Scripts/python.exe tools/thu_nghiem_titleblock.py "duong/dan/file.pdf" --so-trang 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

THU_MUC_GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(THU_MUC_GOC / "src"))

import pypdfium2 as pdfium  # noqa: E402
import yaml  # noqa: E402

from drawing_check.core.grouping import gom_trang_thanh_ban_ve  # noqa: E402
from drawing_check.core.model import PageDoc  # noqa: E402
from drawing_check.engine.loader import doc_thu_muc_rule  # noqa: E402
from drawing_check.engine.runner import chay_rule_tren_trang  # noqa: E402
from drawing_check.extract.pdf_page import tinh_hash_file  # noqa: E402
from drawing_check.extract.titleblock import (  # noqa: E402
    phan_loai_trang_don_gian,
    trich_khung_ten_alpha_vina,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="Duong dan file PDF")
    ap.add_argument("--so-trang", type=int, default=2, help="So trang dau xu ly (mac dinh 2)")
    ap.add_argument(
        "--du-an", default="mh612",
        help="Ten file profile du an trong config/projects/ (mac dinh mh612, khong can duoi .yaml)",
    )
    args = ap.parse_args()

    duong_dan = Path(args.pdf)
    ma_file = tinh_hash_file(duong_dan)
    doc = pdfium.PdfDocument(str(duong_dan))
    n_pages = len(doc)
    so_trang = min(args.so_trang, n_pages)

    du_an_path = THU_MUC_GOC / "config" / "projects" / f"{args.du_an}.yaml"
    vat_lieu_path = THU_MUC_GOC / "config" / "catalogs" / "materials.yaml"
    project = yaml.safe_load(du_an_path.read_text(encoding="utf-8")) or {}
    danh_muc_vat_lieu = yaml.safe_load(vat_lieu_path.read_text(encoding="utf-8")) or {}
    context = {
        "project": project,
        "catalogs": {"materials": danh_muc_vat_lieu.get("materials", [])},
    }

    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")

    trang_list: list[PageDoc] = []
    for i in range(so_trang):
        page = doc[i]
        w, h = page.get_size()
        khung_ten = trich_khung_ten_alpha_vina(page, page_no=i + 1)
        trang = PageDoc(
            file_hash=ma_file,
            file_name=duong_dan.name,
            page_no=i + 1,
            pages_total=n_pages,
            page_kind=phan_loai_trang_don_gian(page),
            sheet_size="A3",
            rotation=page.get_rotation(),
            title_block=khung_ten,
        )
        trang_list.append(trang)

        print(f"\n{'='*70}")
        print(f"TRANG {i+1}/{n_pages}  ({w:.1f}x{h:.1f}pt, {trang.page_kind})")
        print(f"{'='*70}")
        for ten_truong in [
            "drawing_no", "title", "material", "scale", "revision", "projection",
            "general_tol", "drawn_by", "checked_by", "approved_by", "date_drawn", "sheet",
        ]:
            f = getattr(khung_ten, ten_truong)
            print(f"  {ten_truong:<14}: {f.value!r:<30} (conf={f.prov.confidence:.2f})")

        findings = chay_rule_tren_trang(trang, rules, context)
        print(f"\n  --- FINDINGS ({len(findings)}) ---")
        if not findings:
            print("  (khong co finding nao)")
        for f in findings:
            print(f"  [{f.level:<4}] {f.rule_id:<8} ({f.severity:<8}) {f.message_vi}")

    ban_ve_list = gom_trang_thanh_ban_ve(trang_list)
    print(f"\n{'='*70}")
    print(f"GOM TRANG -> BAN VE: {len(ban_ve_list)} ban ve tu {len(trang_list)} trang")
    for bv in ban_ve_list:
        print(f"  {bv.drawing_no}: {bv.sheets_found} trang (sheets_expected={bv.sheets_expected})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
