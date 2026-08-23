"""Gom trang (PageDoc) thanh ban ve (DrawingDoc) theo drawing_no + sheet.

Xem DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 1.4 bay 5: mot file PDF co the la nhieu ban ve
(nhieu drawing_no khac nhau) hoac mot ban ve nhieu to (sheet "1/3", "2/3"...). Day la buoc bat
buoc chay SAU KHI da trich xuat xong toan bo trang cua tat ca file dau vao trong 1 lan chay CLI.
"""

from __future__ import annotations

import re

from drawing_check.core.model import DrawingDoc, PageDoc

_MAU_SHEET = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def tach_sheet(sheet_text: str | None) -> tuple[int | None, int | None]:
    """Tach chuoi sheet dang "1/3" thanh (to_hien_tai, tong_so_to). Tra ve (None, None) neu khong khop."""
    if not sheet_text:
        return None, None
    m = _MAU_SHEET.match(sheet_text)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def gom_trang_thanh_ban_ve(danh_sach_trang: list[PageDoc]) -> list[DrawingDoc]:
    """Gom danh sach PageDoc (co the tu nhieu file) thanh danh sach DrawingDoc theo drawing_no.

    Trang khong doc duoc drawing_no (title_block.drawing_no.value la None/rong) bi bo qua khoi
    ket qua gom - loi "thieu ma ban ve" da duoc rule TB-001 bat rieng o tang rule engine, khong
    xu ly lai o day.
    """
    theo_ma: dict[str, list[PageDoc]] = {}
    for trang in danh_sach_trang:
        ma = trang.title_block.drawing_no.value
        if not ma:
            continue
        theo_ma.setdefault(ma, []).append(trang)

    ket_qua: list[DrawingDoc] = []
    for ma, cac_trang in theo_ma.items():
        cac_trang_sap_xep = sorted(
            cac_trang,
            key=lambda t: (tach_sheet(t.title_block.sheet.value)[0] or 0, t.page_no),
        )
        to_hien_tai_dau, tong_so_to = tach_sheet(cac_trang_sap_xep[0].title_block.sheet.value)
        ket_qua.append(
            DrawingDoc(
                drawing_no=ma,
                pages=cac_trang_sap_xep,
                sheets_expected=tong_so_to,
                sheets_found=len(cac_trang_sap_xep),
            )
        )
    return ket_qua
