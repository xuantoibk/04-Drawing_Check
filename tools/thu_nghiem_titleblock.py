#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
thu_nghiem_titleblock.py - Chay thu extractor khung ten (mau Alpha Vina A3/A4, tu dong xu ly ca
trang bi xoay) + rule engine tren 1 file PDF that, in chi tiet tung truong/finding ra man hinh.
KHONG phai CLI chinh thuc (drawing-check run) - day la cong cu dev de kiem tra extractor.

Dung:
    .venv/Scripts/python.exe tools/thu_nghiem_titleblock.py "duong/dan/file.pdf" --so-trang 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Mot so terminal Windows dung codepage khong phai UTF-8 (vd cp1252), se crash UnicodeEncodeError
# khi in ky tu co dau tieng Viet (vd ten nguoi "MẠ ANODE TRẮNG") - thay the bang '?' thay vi crash.
sys.stdout.reconfigure(errors="replace")

THU_MUC_GOC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(THU_MUC_GOC / "src"))

import pypdfium2 as pdfium  # noqa: E402
import yaml  # noqa: E402

from drawing_check.core.grouping import gom_trang_thanh_ban_ve  # noqa: E402
from drawing_check.engine.loader import doc_thu_muc_rule  # noqa: E402
from drawing_check.engine.runner import chay_rule_tren_ban_ve  # noqa: E402
from drawing_check.pipeline import chay_1_file, tim_du_an_khop  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pdf", help="Duong dan file PDF")
    ap.add_argument(
        "--so-trang", type=int, default=2,
        help="Chi IN CHI TIET may trang dau (mac dinh 2) - van xu ly toan bo file, chi gioi han in",
    )
    args = ap.parse_args()

    duong_dan = Path(args.pdf)

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

    trang_list, findings = chay_1_file(duong_dan, rules, danh_sach_du_an, catalogs)
    findings_theo_trang: dict[int, list] = {}
    for f in findings:
        findings_theo_trang.setdefault(f.page_no, []).append(f)

    doc = pdfium.PdfDocument(str(duong_dan))
    so_trang_in = min(args.so_trang, len(trang_list))
    for trang in trang_list[:so_trang_in]:
        w, h = doc[trang.page_no - 1].get_size()
        print(f"\n{'='*70}")
        print(
            f"TRANG {trang.page_no}/{trang.pages_total}  ({w:.1f}x{h:.1f}pt, {trang.page_kind}, "
            f"rotation={trang.rotation})"
        )
        print(f"{'='*70}")
        khung_ten = trang.title_block
        for ten_truong in [
            "drawing_no", "title", "material", "scale", "revision", "projection",
            "general_tol", "drawn_by", "checked_by", "approved_by", "date_drawn", "sheet",
        ]:
            f = getattr(khung_ten, ten_truong)
            print(f"  {ten_truong:<14}: {f.value!r:<30} (conf={f.prov.confidence:.2f})")

        if trang.dimensions:
            print(f"  kich_thuoc     : {[(d.nominal, d.fit_code) for d in trang.dimensions]}")

        cac_finding = findings_theo_trang.get(trang.page_no, [])
        print(f"\n  --- FINDINGS ({len(cac_finding)}) ---")
        if not cac_finding:
            print("  (khong co finding nao)")
        for f in cac_finding:
            print(f"  [{f.level:<4}] {f.rule_id:<8} ({f.severity:<8}) {f.message_vi}")

    ban_ve_list = gom_trang_thanh_ban_ve(trang_list)
    for ban_ve in ban_ve_list:
        context_ban_ve = {"project": tim_du_an_khop(ban_ve.drawing_no, danh_sach_du_an) or {}}
        findings.extend(chay_rule_tren_ban_ve(ban_ve, rules, context_ban_ve))

    print(f"\n{'='*70}")
    print(f"GOM TRANG -> BAN VE: {len(ban_ve_list)} ban ve tu {len(trang_list)} trang")
    for bv in ban_ve_list:
        print(f"  {bv.drawing_no}: {bv.sheets_found} trang (sheets_expected={bv.sheets_expected})")

    so_luong = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for f in findings:
        so_luong[f.level] += 1
    print(f"\nTONG KET CA FILE: {so_luong['FAIL']} FAIL, {so_luong['WARN']} WARN, {so_luong['INFO']} INFO.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
