"""Chay danh sach Rule tren 1 PageDoc, sinh ra danh sach Finding.

Nguyen tac bat buoc (DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 3.2): khong bao gio de mot ket
qua tu OCR/VLM roi vao FAIL - luon ha xuong WARN, bat ke rule khai bao severity gi.
"""

from __future__ import annotations

from typing import Any

from drawing_check.core.finding import Finding, Level
from drawing_check.core.model import Field, PageDoc
from drawing_check.engine.loader import Rule
from drawing_check.engine.primitives import PRIMITIVES

NGUON_KHONG_CHAC_CHAN = {"ocr", "vlm"}


def lay_field(page: PageDoc, duong_dan: str) -> Field:
    doi_tuong: Any = page
    for phan in duong_dan.split("."):
        doi_tuong = getattr(doi_tuong, phan)
    if not isinstance(doi_tuong, Field):
        raise TypeError(f"'{duong_dan}' khong tro toi 1 Field")
    return doi_tuong


def xac_dinh_level(field: Field, rule: Rule) -> Level:
    if field.prov.source in NGUON_KHONG_CHAC_CHAN:
        return "WARN"
    if rule.confidence_gate is not None and field.prov.confidence < rule.confidence_gate:
        return "WARN"
    return "FAIL"


def dinh_dang_message(mau: str, field: Field, rule: Rule) -> str:
    bien = dict(rule.params)
    bien["value"] = field.value
    try:
        return mau.format(**bien)
    except (KeyError, IndexError):
        return mau


def chay_rule_tren_trang(page: PageDoc, rules: list[Rule], context: dict | None = None) -> list[Finding]:
    context = context or {}
    ket_qua: list[Finding] = []
    ma_ban_ve = page.title_block.drawing_no.value or ""

    for rule in rules:
        if rule.requires:
            # Rule tam hoan - chua co nguon du lieu tuong ung (vd requires: dxf, nhanh CAD dang hoan).
            continue
        if rule.check == "custom":
            raise NotImplementedError(
                f"Rule {rule.id}: check 'custom' (handler={rule.params.get('handler')}) chua co "
                "module xu ly trong engine/checks/ - chua toi Phase can rule nay."
            )
        ham = PRIMITIVES.get(rule.check)
        if ham is None:
            raise ValueError(f"Rule {rule.id}: check '{rule.check}' chua duoc ho tro")

        duong_dan_field = rule.params.get("field")
        if not duong_dan_field:
            raise ValueError(f"Rule {rule.id}: thieu params.field")
        field = lay_field(page, duong_dan_field)

        if not ham(field, rule.params, context):
            continue

        ket_qua.append(
            Finding(
                rule_id=rule.id,
                level=xac_dinh_level(field, rule),
                severity=rule.severity,
                message_vi=dinh_dang_message(rule.message_vi, field, rule),
                drawing_no=ma_ban_ve,
                page_no=page.page_no,
                field=duong_dan_field,
                fix_hint=rule.fix_hint,
                bbox=field.prov.bbox,
            )
        )
    return ket_qua
