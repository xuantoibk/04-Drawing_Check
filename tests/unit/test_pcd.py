"""Test rule DIM-002 (pcd_thieu_ky_hieu_duong_kinh, engine/primitives_dimension.py) - P.C.D
(duong tron chia lo bulong) phai kem ky hieu duong kinh (chu phi) truoc con so. Nguoi dung phat
hien 2026-08-25 tren du lieu that (trang 1/6 MH612 ghi "P.C.D.44"/"P.C.D.42" thieu ky hieu, cac
trang khac ghi dung "P.C.Dφ.."). Xem docs/Source/Project-Remember.md muc DIM-002."""

from __future__ import annotations

from pathlib import Path

import pytest

from drawing_check.core.model import Note, Provenance
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.primitives_dimension import pcd_thieu_ky_hieu_duong_kinh
from drawing_check.engine.runner import chay_rule_tren_trang_kich_thuoc
from drawing_check.extract.dimension import RE_PCD
from factories import page_mau

THU_MUC_RULES = Path(__file__).resolve().parents[2] / "rules"


@pytest.fixture(scope="module")
def rules():
    return doc_thu_muc_rule(THU_MUC_RULES)


def _nhan(raw_text: str, confidence: float = 0.9) -> Note:
    return Note(raw_text=raw_text, prov=Provenance(source="pdf_text", confidence=confidence, page=1))


@pytest.mark.parametrize(
    "text,co_ky_hieu",
    [
        ("P.C.D.44", False),  # loi that trang 1 MH612
        ("P.C.D.42", False),  # loi that trang 6 MH612
        ("P.C.Dφ38", True),  # dung, trang 5 MH612
        ("P.C.Dφ30", True),  # dung, trang 28 MH612
        ("PCDφ38", True),  # dang khong dau cham, nguoi dung neu vi du
        ("PCD38", False),  # dang khong dau cham, thieu ky hieu
    ],
)
def test_re_pcd_nhan_dung_co_hay_khong_ky_hieu(text, co_ky_hieu):
    m = RE_PCD.search(text)
    assert m is not None
    assert (m.group(1) is not None) == co_ky_hieu


def test_pcd_co_ky_hieu_khong_bao_loi():
    trang = page_mau()
    trang.pcd_labels = [_nhan("P.C.Dφ38"), _nhan("PCDφ30")]
    assert pcd_thieu_ky_hieu_duong_kinh(trang, {}, {}) == []


def test_pcd_thieu_ky_hieu_bi_bao():
    """Tai hien dung ca that tren trang 1 MH612: 'P.C.D.44' thieu ky hieu phi truoc con so."""
    trang = page_mau()
    trang.pcd_labels = [_nhan("P.C.D.44")]
    vi_pham = pcd_thieu_ky_hieu_duong_kinh(trang, {}, {})
    assert len(vi_pham) == 1
    assert vi_pham[0]["gia_tri"] == "P.C.D.44"


def test_khong_co_nhan_pcd_khong_bao():
    trang = page_mau()
    trang.pcd_labels = []
    assert pcd_thieu_ky_hieu_duong_kinh(trang, {}, {}) == []


def test_qua_rule_engine_len_muc_WARN(rules):
    """confidence=0.9 < confidence_gate=0.95 cua DIM-002 - CO Y luon WARN, moi kiem chung tren 1
    file that (xem rules/20_dimension.yaml)."""
    trang = page_mau()
    trang.pcd_labels = [_nhan("P.C.D.44")]
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, {})
    dim002 = [f for f in findings if f.rule_id == "DIM-002"]
    assert len(dim002) == 1
    assert dim002[0].level == "WARN"
