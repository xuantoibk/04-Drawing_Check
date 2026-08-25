"""Primitive cho rule chay tren `page.dimensions` (list, khong phai 1 Field don) - tang thu 3
cua rule engine (khac primitives.py cho 1 truong/1 trang, primitives_drawing.py cho quan he giua
nhieu trang). Phase 3, lat cat dau tien - xem docs/Source/Project-Remember.md.

Moi ham tra ve LIST cac vi pham (1 trang co the co NHIEU Dimension sai cung luc, khac quy uoc
primitives.py/primitives_drawing.py chi tra ve 1 vi pham). Moi phan tu vi pham la dict co it nhat
{'gia_tri', 'nguon', 'do_tin_cay', 'bbox'} de runner dung dinh dang message + xac dinh muc FAIL/WARN.
"""

from __future__ import annotations

import re
from typing import Any

from drawing_check.core.model import PageDoc

_MAU_FIT_CODE = re.compile(r"([A-Za-z]{1,2})(\d{1,2})")


def fit_code_sai_cu_phap(page: PageDoc, params: dict, context: dict) -> list[dict[str, Any]]:
    """Kiem tra tung Dimension co fit_code: cu phap phai la <chu cai lech chuan><cap chinh xac>
    hop le theo ISO 286/JIS B 0401 (config/catalogs/iso286_letters.yaml). Danh muc rong (chua nap)
    thi KHONG ket luan (giong field_in_catalog trong primitives.py), tranh bao sai hang loat."""
    danh_muc = context.get("catalogs", {}).get("iso286", {})
    chu_cai_hop_le = set(danh_muc.get("chu_cai_lech_chuan", []))
    cap_hop_le = set(danh_muc.get("cap_chinh_xac", []))
    if not chu_cai_hop_le or not cap_hop_le:
        return []

    vi_pham = []
    for dim in page.dimensions:
        if not dim.fit_code:
            continue
        m = _MAU_FIT_CODE.fullmatch(dim.fit_code)
        hop_le = bool(m) and m.group(1).upper() in chu_cai_hop_le and m.group(2) in cap_hop_le
        if not hop_le:
            vi_pham.append(
                {
                    "gia_tri": f"{dim.nominal:g}{dim.fit_code}",
                    "nguon": dim.prov.source,
                    "do_tin_cay": dim.prov.confidence,
                    "bbox": dim.prov.bbox,
                }
            )
    return vi_pham


PRIMITIVES_KICH_THUOC: dict[str, Any] = {
    "fit_code_sai_cu_phap": fit_code_sai_cu_phap,
}
