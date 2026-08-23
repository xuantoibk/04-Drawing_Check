"""Cac primitive dung chung cho rule YAML (check: field_present | field_matches | ...).

Theo dung dinh dang rule o DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 7.1. Moi ham nhan vao
(field, params, context) va tra ve True neu VI PHAM (rule bi fail), False neu on. field.value la
None duoc coi la "chua kiem tra duoc" o cac primitive khac field_present, de tranh bao trung voi
loi "thieu truong" (da co rule field_present rieng bat loi do).
"""

from __future__ import annotations

import re
from typing import Any

from drawing_check.core.model import Field


def field_present(field: Field, params: dict, context: dict) -> bool:
    gia_tri = field.value
    if gia_tri is None:
        return True
    if isinstance(gia_tri, str) and gia_tri.strip() == "":
        return True
    return False


def field_matches(field: Field, params: dict, context: dict) -> bool:
    if field.value is None:
        return False
    mau = params.get("pattern")
    if mau is None:
        khoa = params.get("pattern_from_project")
        mau = context.get("project", {}).get(khoa) if khoa else None
    if not mau:
        return False
    return re.fullmatch(mau, str(field.value)) is None


def field_in_catalog(field: Field, params: dict, context: dict) -> bool:
    if field.value is None:
        return False
    ten_danh_muc = params["catalog"]
    danh_muc = context.get("catalogs", {}).get(ten_danh_muc)
    if not danh_muc:
        # Chua co danh muc that (Phase 0 chua hoan tat) - khong the ket luan, coi nhu khong vi pham
        # de tranh bao sai hang loat khi danh muc con rong.
        return False
    return str(field.value) not in danh_muc


def field_equals_project(field: Field, params: dict, context: dict) -> bool:
    if field.value is None:
        return False
    khoa = params["project_key"]
    ky_vong = context.get("project", {}).get(khoa)
    if ky_vong is None:
        return False
    return str(field.value) != str(ky_vong)


PRIMITIVES: dict[str, Any] = {
    "field_present": field_present,
    "field_matches": field_matches,
    "field_in_catalog": field_in_catalog,
    "field_equals_project": field_equals_project,
}
