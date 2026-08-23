"""Test rule cap BAN VE (dong bo nhieu to) - rules/15_multisheet.yaml, chay boi
engine/runner.py::chay_rule_tren_ban_ve. Dung du lieu gia (factories.page_mau) vi 51 trang du
lieu that hien co (00_input/MH612-DATA GIA CONG FULL.pdf) deu la ban ve 1 to - chua co vi du
ban ve nhieu to that de kiem chung, xem ghi chu dau file rules/15_multisheet.yaml."""

from __future__ import annotations

from pathlib import Path

import pytest

from drawing_check.core.grouping import gom_trang_thanh_ban_ve
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.runner import chay_rule_tren_ban_ve
from factories import page_mau

THU_MUC_RULES = Path(__file__).resolve().parents[2] / "rules"


@pytest.fixture(scope="module")
def rules():
    return doc_thu_muc_rule(THU_MUC_RULES)


def test_du_to_va_cung_revision_khong_bao_loi(rules):
    trang = [
        page_mau(page_no=1, drawing_no="KB-00123-A01", sheet="1/2", revision="B"),
        page_mau(page_no=2, drawing_no="KB-00123-A01", sheet="2/2", revision="B"),
    ]
    ban_ve = gom_trang_thanh_ban_ve(trang)[0]
    assert chay_rule_tren_ban_ve(ban_ve, rules, {}) == []


def test_thieu_to_bao_MS001(rules):
    trang = [
        page_mau(page_no=1, drawing_no="KB-00123-A01", sheet="1/3", revision="B"),
        page_mau(page_no=2, drawing_no="KB-00123-A01", sheet="2/3", revision="B"),
    ]  # thieu to 3/3
    ban_ve = gom_trang_thanh_ban_ve(trang)[0]
    findings = chay_rule_tren_ban_ve(ban_ve, rules, {})
    ma_loi = {f.rule_id for f in findings}
    assert "MS-001" in ma_loi


def test_revision_khac_nhau_bao_MS002(rules):
    trang = [
        page_mau(page_no=1, drawing_no="KB-00123-A01", sheet="1/2", revision="A"),
        page_mau(page_no=2, drawing_no="KB-00123-A01", sheet="2/2", revision="B"),
    ]
    ban_ve = gom_trang_thanh_ban_ve(trang)[0]
    findings = chay_rule_tren_ban_ve(ban_ve, rules, {})
    ma_loi = {f.rule_id for f in findings}
    assert "MS-002" in ma_loi


def test_ban_ve_1_to_khong_bao_loi_dong_bo(rules):
    trang = [page_mau(page_no=1, drawing_no="KB-00123-A01", sheet="1/1", revision="-")]
    ban_ve = gom_trang_thanh_ban_ve(trang)[0]
    assert chay_rule_tren_ban_ve(ban_ve, rules, {}) == []
