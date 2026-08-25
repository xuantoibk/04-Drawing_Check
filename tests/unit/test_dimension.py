"""Test rule DIM-001 (fit_code_sai_cu_phap) - dung du lieu gia vi 130 trang that hien co KHONG co
ca nao vi pham that (ca 22 ma lap ghep tim duoc deu dung cu phap) - can du lieu gia de xac nhan
rule THUC SU bat duoc loi khi co, khong chi "im lang vi khong co gi de bat"."""

from __future__ import annotations

from pathlib import Path

import pytest

from drawing_check.core.model import Dimension, Provenance
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.runner import chay_rule_tren_trang_kich_thuoc
from factories import page_mau

THU_MUC_RULES = Path(__file__).resolve().parents[2] / "rules"
CATALOG_DAY_DU = {
    "chu_cai_lech_chuan": ["A", "H", "G", "P", "JS"],
    "cap_chinh_xac": ["6", "7", "8"],
}
CONTEXT_MAU = {"catalogs": {"iso286": CATALOG_DAY_DU}}


@pytest.fixture(scope="module")
def rules():
    return doc_thu_muc_rule(THU_MUC_RULES)


def _dim(nominal: float, fit_code: str, confidence: float = 0.8) -> Dimension:
    return Dimension(
        nominal=nominal,
        fit_code=fit_code,
        dim_type="diameter",
        prov=Provenance(source="pdf_text", confidence=confidence, page=1),
    )


def test_fit_code_dung_khong_bao_loi(rules):
    trang = page_mau()
    trang.dimensions = [_dim(6, "H7"), _dim(36, "G6")]
    assert chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_MAU) == []


def test_chu_cai_khong_co_trong_danh_muc_bao_DIM001(rules):
    trang = page_mau()
    trang.dimensions = [_dim(6, "W7")]  # "W" khong co trong danh muc
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_MAU)
    ma_loi = {f.rule_id for f in findings}
    assert "DIM-001" in ma_loi


def test_cap_chinh_xac_khong_hop_le_bao_DIM001(rules):
    trang = page_mau()
    trang.dimensions = [_dim(6, "H99")]  # cap "99" khong co trong danh muc
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_MAU)
    ma_loi = {f.rule_id for f in findings}
    assert "DIM-001" in ma_loi


def test_do_tin_cay_thap_chi_len_muc_WARN_khong_bao_gio_FAIL(rules):
    """confidence=0.8 (mac dinh cua extract/dimension.py hien tai) < confidence_gate=0.9 cua
    DIM-001 - CO Y luon WARN cho toi khi extractor duoc kiem chung nhieu hon (xem rules/
    20_dimension.yaml)."""
    trang = page_mau()
    trang.dimensions = [_dim(6, "W7", confidence=0.8)]
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_MAU)
    dim001 = [f for f in findings if f.rule_id == "DIM-001"]
    assert len(dim001) == 1
    assert dim001[0].level == "WARN"


def test_danh_muc_rong_khong_ket_luan(rules):
    trang = page_mau()
    trang.dimensions = [_dim(6, "W7")]
    findings = chay_rule_tren_trang_kich_thuoc(trang, rules, {"catalogs": {}})
    assert findings == []


def test_khong_co_fit_code_khong_bao_loi(rules):
    trang = page_mau()
    trang.dimensions = [
        Dimension(
            nominal=10, dim_type="linear", prov=Provenance(source="pdf_text", confidence=1.0, page=1)
        )
    ]
    assert chay_rule_tren_trang_kich_thuoc(trang, rules, CONTEXT_MAU) == []
