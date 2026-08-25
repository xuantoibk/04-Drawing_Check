"""Chay danh sach Rule tren 1 PageDoc, sinh ra danh sach Finding.

Nguyen tac bat buoc (DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 3.2): khong bao gio de mot ket
qua tu OCR/VLM roi vao FAIL - luon ha xuong WARN, bat ke rule khai bao severity gi.
"""

from __future__ import annotations

from typing import Any

from drawing_check.core.finding import Finding, Level
from drawing_check.core.model import DrawingDoc, Field, PageDoc
from drawing_check.engine.checks import HANDLERS
from drawing_check.engine.loader import Rule
from drawing_check.engine.primitives import PRIMITIVES
from drawing_check.engine.primitives_dimension import PRIMITIVES_KICH_THUOC
from drawing_check.engine.primitives_drawing import PRIMITIVES_BAN_VE
from drawing_check.engine.primitives_symbols import PRIMITIVES_KY_HIEU

NGUON_KHONG_CHAC_CHAN = {"ocr", "vlm", "vision", "pdf_text_loose"}

# Tang "list nhieu vi pham/trang" - dung chung 1 runner (chay_rule_tren_trang_kich_thuoc) cho ca
# rule kich thuoc (Phase 3) va rule doi chieu ky hieu (Phase 4), vi ca 2 nhan 'page' day du va
# tra ve cung 1 dinh dang vi pham.
PRIMITIVES_THEO_TRANG_LIST: dict = {**PRIMITIVES_KICH_THUOC, **PRIMITIVES_KY_HIEU}


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
            ten_handler = rule.params.get("handler")
            ham = HANDLERS.get(ten_handler)
            if ham is None:
                raise NotImplementedError(
                    f"Rule {rule.id}: check 'custom' voi handler='{ten_handler}' chua dang ky "
                    "trong engine/checks/HANDLERS."
                )
        elif rule.check in PRIMITIVES_BAN_VE or rule.check in PRIMITIVES_THEO_TRANG_LIST:
            # Rule cap BAN VE (nhieu trang) hoac cap DANH SACH (page.dimensions/surface_finishes)
            # - khong chay o day, danh cho chay_rule_tren_ban_ve / chay_rule_tren_trang_kich_thuoc.
            continue
        else:
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


def chay_rule_tren_ban_ve(
    drawing: DrawingDoc, rules: list[Rule], context: dict | None = None
) -> list[Finding]:
    """Chay cac rule cap BAN VE (kiem tra quan he GIUA nhieu trang cung drawing_no, vd du to
    chua/revision co khop nhau khong) - khac voi chay_rule_tren_trang (chay tren 1 truong cua
    dung 1 trang). Chi goi SAU KHI da gom trang thanh ban ve (core/grouping.py). Rule khong
    thuoc PRIMITIVES_BAN_VE (vd rule khung ten thuong) bi bo qua, danh cho chay_rule_tren_trang."""
    context = context or {}
    ket_qua: list[Finding] = []

    for rule in rules:
        if rule.requires or rule.check not in PRIMITIVES_BAN_VE:
            continue
        ham = PRIMITIVES_BAN_VE[rule.check]
        vi_pham, cac_nguon, bien_bo_sung = ham(drawing, rule.params, context)
        if not vi_pham:
            continue

        muc: Level = "WARN" if any(n in NGUON_KHONG_CHAC_CHAN for n in cac_nguon) else "FAIL"
        bien = dict(rule.params)
        bien.update(bien_bo_sung)
        bien["drawing_no"] = drawing.drawing_no
        bien["sheets_found"] = drawing.sheets_found
        bien["sheets_expected"] = drawing.sheets_expected
        try:
            noi_dung = rule.message_vi.format(**bien)
        except (KeyError, IndexError):
            noi_dung = rule.message_vi

        ket_qua.append(
            Finding(
                rule_id=rule.id,
                level=muc,
                severity=rule.severity,
                message_vi=noi_dung,
                drawing_no=drawing.drawing_no,
                page_no=drawing.pages[-1].page_no,
                field=rule.params.get("field"),
                fix_hint=rule.fix_hint,
            )
        )
    return ket_qua


def chay_rule_tren_trang_kich_thuoc(
    page: PageDoc, rules: list[Rule], context: dict | None = None
) -> list[Finding]:
    """Chay cac rule nhan 'page' day du va tra ve list vi pham (khac 1 Field don) - tang thu 3
    cua rule engine, gom ca rule tren page.dimensions (Phase 3) va rule doi chieu ky hieu vision
    tren page.surface_finishes/gdt_frames (Phase 4, xem primitives_symbols.py). Khac
    chay_rule_tren_trang: 1 trang co the sinh NHIEU Finding tu CUNG 1 rule. Rule khong thuoc
    PRIMITIVES_THEO_TRANG_LIST bi bo qua."""
    context = context or {}
    ket_qua: list[Finding] = []
    ma_ban_ve = page.title_block.drawing_no.value or ""

    for rule in rules:
        if rule.requires or rule.check not in PRIMITIVES_THEO_TRANG_LIST:
            continue
        ham = PRIMITIVES_THEO_TRANG_LIST[rule.check]
        for vi_pham in ham(page, rule.params, context):
            nguon = vi_pham.get("nguon", "pdf_text")
            do_tin_cay = vi_pham.get("do_tin_cay", 1.0)
            if nguon in NGUON_KHONG_CHAC_CHAN:
                muc: Level = "WARN"
            elif rule.confidence_gate is not None and do_tin_cay < rule.confidence_gate:
                muc = "WARN"
            else:
                muc = "FAIL"

            bien = dict(rule.params)
            bien.update(vi_pham)
            try:
                noi_dung = rule.message_vi.format(**bien)
            except (KeyError, IndexError):
                noi_dung = rule.message_vi

            ket_qua.append(
                Finding(
                    rule_id=rule.id,
                    level=muc,
                    severity=rule.severity,
                    message_vi=noi_dung,
                    drawing_no=ma_ban_ve,
                    page_no=page.page_no,
                    fix_hint=rule.fix_hint,
                    bbox=vi_pham.get("bbox"),
                )
            )
    return ket_qua
