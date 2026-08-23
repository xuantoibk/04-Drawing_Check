from pathlib import Path

import pytest

from drawing_check.core.model import Field, Provenance
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.runner import chay_rule_tren_trang
from factories import page_mau

THU_MUC_RULES = Path(__file__).resolve().parents[2] / "rules"

CONTEXT_MAU = {
    "project": {
        "drawing_no_pattern": r"^KB-\d{5}-[A-Z]\d{2}$",
        "projection_angle": "third",
    },
    "catalogs": {"materials": ["SS400", "S45C", "SUS304"]},
}


@pytest.fixture(scope="module")
def rules():
    return doc_thu_muc_rule(THU_MUC_RULES)


def test_doc_duoc_du_rule_khung_ten(rules):
    ma_rule = {r.id for r in rules}
    assert {"TB-001", "TB-002", "TB-007", "TB-011", "PROJ-001", "PROJ-002"} <= ma_rule


def test_thieu_ma_ban_ve_bao_TB001_muc_fail(rules):
    trang = page_mau()  # khong dien gi ca
    findings = chay_rule_tren_trang(trang, rules, CONTEXT_MAU)
    tb001 = [f for f in findings if f.rule_id == "TB-001"]
    assert len(tb001) == 1
    assert tb001[0].level == "FAIL"
    assert tb001[0].severity == "critical"


def test_ban_ve_day_du_dung_khong_bao_loi_khung_ten(rules):
    trang = page_mau(
        drawing_no="KB-00123-A01",
        material="SS400",
        checked_by="NVA",
        projection="third",
        sheet="1/1",
    )
    findings = chay_rule_tren_trang(trang, rules, CONTEXT_MAU)
    assert findings == []


def test_goc_chieu_sai_chuan_du_an_bao_PROJ002(rules):
    trang = page_mau(
        drawing_no="KB-00123-A01",
        material="SS400",
        checked_by="NVA",
        projection="first",  # du an dung "third"
        sheet="1/1",
    )
    findings = chay_rule_tren_trang(trang, rules, CONTEXT_MAU)
    ma_loi = {f.rule_id for f in findings}
    assert "PROJ-002" in ma_loi


def test_du_lieu_tu_ocr_khong_bao_gio_len_muc_fail(rules):
    khung_ten = page_mau().title_block
    khung_ten.checked_by = Field(value=None, prov=Provenance(source="ocr", confidence=0.6, page=1))
    trang = page_mau(title_block=khung_ten)

    findings = chay_rule_tren_trang(trang, rules, CONTEXT_MAU)
    tb007 = [f for f in findings if f.rule_id == "TB-007"]
    assert len(tb007) == 1
    assert tb007[0].level == "WARN"
