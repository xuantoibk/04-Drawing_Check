"""Xuat ket qua kiem tra ra 1 file Excel - dung xlsxwriter, khong doc lai duoc (write-only,
dung dung muc dich bao cao).

2 sheet: "Tom tat" (so luong FAIL/WARN/INFO theo ban ve) va "Chi tiet" (tung Finding 1 dong,
mau nen theo muc do de nguoi xem quet mat nhanh).
"""

from __future__ import annotations

from pathlib import Path

import xlsxwriter

from drawing_check.core.finding import Finding

_MAU_NEN = {
    "FAIL": "#F8CBCB",
    "WARN": "#FCEBA8",
    "INFO": "#D6E9F8",
}

_CAC_COT_CHI_TIET = [
    ("drawing_no", "Ma ban ve", 22),
    ("page_no", "Trang", 8),
    ("level", "Muc do", 10),
    ("severity", "Nghiem trong", 12),
    ("rule_id", "Ma quy tac", 12),
    ("message_vi", "Noi dung", 60),
    ("fix_hint", "Goi y sua", 45),
]


def xuat_excel(findings: list[Finding], duong_dan_ra: Path) -> None:
    duong_dan_ra.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(str(duong_dan_ra))

    dinh_dang_tieu_de = workbook.add_format(
        {"bold": True, "bg_color": "#D9D9D9", "border": 1}
    )
    dinh_dang_theo_muc_do = {
        muc: workbook.add_format({"bg_color": mau, "border": 1, "text_wrap": True, "valign": "top"})
        for muc, mau in _MAU_NEN.items()
    }
    dinh_dang_thuong = workbook.add_format({"border": 1, "text_wrap": True, "valign": "top"})

    _ghi_sheet_tom_tat(workbook, findings, dinh_dang_tieu_de, dinh_dang_thuong)
    _ghi_sheet_chi_tiet(workbook, findings, dinh_dang_tieu_de, dinh_dang_theo_muc_do)

    workbook.close()


def _ghi_sheet_tom_tat(workbook, findings, dinh_dang_tieu_de, dinh_dang_thuong) -> None:
    sheet = workbook.add_worksheet("Tom tat")
    sheet.set_column(0, 0, 24)
    sheet.set_column(1, 3, 10)

    theo_ban_ve: dict[str, dict[str, int]] = {}
    for f in findings:
        ma = f.drawing_no or "(khong xac dinh)"
        so_luong = theo_ban_ve.setdefault(ma, {"FAIL": 0, "WARN": 0, "INFO": 0})
        so_luong[f.level] += 1

    tieu_de = ["Ma ban ve", "FAIL", "WARN", "INFO"]
    for col, ten in enumerate(tieu_de):
        sheet.write(0, col, ten, dinh_dang_tieu_de)

    hang = 1
    for ma in sorted(theo_ban_ve):
        so_luong = theo_ban_ve[ma]
        sheet.write(hang, 0, ma, dinh_dang_thuong)
        sheet.write(hang, 1, so_luong["FAIL"], dinh_dang_thuong)
        sheet.write(hang, 2, so_luong["WARN"], dinh_dang_thuong)
        sheet.write(hang, 3, so_luong["INFO"], dinh_dang_thuong)
        hang += 1

    if not theo_ban_ve:
        sheet.write(1, 0, "Khong co phat hien nao.", dinh_dang_thuong)

    sheet.freeze_panes(1, 0)


def _ghi_sheet_chi_tiet(workbook, findings, dinh_dang_tieu_de, dinh_dang_theo_muc_do) -> None:
    sheet = workbook.add_worksheet("Chi tiet")
    for col, (_, ten, rong) in enumerate(_CAC_COT_CHI_TIET):
        sheet.set_column(col, col, rong)
        sheet.write(0, col, ten, dinh_dang_tieu_de)

    cac_finding_sap_xep = sorted(
        findings, key=lambda f: (f.drawing_no or "", f.page_no, f.level != "FAIL")
    )
    for hang, f in enumerate(cac_finding_sap_xep, start=1):
        dinh_dang = dinh_dang_theo_muc_do[f.level]
        for col, (ten_truong, _, _) in enumerate(_CAC_COT_CHI_TIET):
            gia_tri = getattr(f, ten_truong)
            sheet.write(hang, col, gia_tri if gia_tri is not None else "", dinh_dang)

    sheet.freeze_panes(1, 0)
    sheet.autofilter(0, 0, len(cac_finding_sap_xep), len(_CAC_COT_CHI_TIET) - 1)
