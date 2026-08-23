"""Primitive cho rule chay tren CA 1 BAN VE (nhieu trang gop lai theo drawing_no), khac voi
primitives.py (chay tren 1 truong cua DUNG 1 trang). Dung cho nhom rule dong bo nhieu to
(rules/15_multisheet.yaml) - vd du to chua, revision cac to co khop nhau khong.

Moi ham tra ve (vi_pham, cac_nguon, bien_bo_sung):
- vi_pham: True neu rule bi vi pham
- cac_nguon: danh sach Provenance.source cua cac truong da dung de xet - de runner quyet dinh
  FAIL/WARN theo dung nguyen tac "OCR/VLM khong bao gio len FAIL" nhu primitives.py/runner.py
- bien_bo_sung: bien rieng de dien vao message_vi (vd danh sach gia tri khac nhau tim thay)
"""

from __future__ import annotations

from typing import Any

from drawing_check.core.model import DrawingDoc


def sheets_du_so_luong(
    drawing: DrawingDoc, params: dict, context: dict
) -> tuple[bool, list[str], dict[str, Any]]:
    cac_nguon = [p.title_block.sheet.prov.source for p in drawing.pages]
    if drawing.sheets_expected is None:
        return False, cac_nguon, {}
    return drawing.sheets_found != drawing.sheets_expected, cac_nguon, {}


def field_khop_giua_cac_to(
    drawing: DrawingDoc, params: dict, context: dict
) -> tuple[bool, list[str], dict[str, Any]]:
    duong_dan = params["field"]
    cac_nguon: list[str] = []
    gia_tri_list: list[Any] = []
    for page in drawing.pages:
        field: Any = page
        for phan in duong_dan.split("."):
            field = getattr(field, phan)
        cac_nguon.append(field.prov.source)
        if field.value is not None:
            gia_tri_list.append(field.value)

    cac_gia_tri_khac_nhau = sorted({str(v) for v in gia_tri_list})
    vi_pham = len(cac_gia_tri_khac_nhau) > 1
    return vi_pham, cac_nguon, {"cac_gia_tri": ", ".join(cac_gia_tri_khac_nhau)}


PRIMITIVES_BAN_VE: dict[str, Any] = {
    "sheets_du_so_luong": sheets_du_so_luong,
    "field_khop_giua_cac_to": field_khop_giua_cac_to,
}
