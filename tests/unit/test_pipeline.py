"""Test tim_du_an_khop (pipeline.py) - xac dinh du an theo TIEN TO project_id (khong phai theo
drawing_no_pattern day du - xem docstring ham nay de biet ly do: ma ban ve SAI dinh dang van
phai duoc gan dung du an de TB-002 con bat loi duoc, khong duoc am tham bo qua)."""

from __future__ import annotations

from drawing_check.pipeline import tim_du_an_khop

DU_AN_MH612 = {"project_id": "MH612", "drawing_no_pattern": r"^MH612-M\d{4}-[A-Z0-9]+-[A-Z]$"}
DU_AN_VPK25 = {"project_id": "VPK25", "drawing_no_pattern": r"^VPK25-M\d{4}-[A-Z0-9]+-[A-Z]$"}
DANH_SACH_DU_AN = [DU_AN_MH612, DU_AN_VPK25]


def test_khop_dung_project_dau_tien():
    assert tim_du_an_khop("MH612-M1001-A6-P", DANH_SACH_DU_AN) == DU_AN_MH612


def test_khop_dung_project_thu_hai():
    assert tim_du_an_khop("VPK25-M1007-S4-L", DANH_SACH_DU_AN) == DU_AN_VPK25


def test_ma_ban_ve_sai_dinh_dang_van_khop_dung_du_an_theo_tien_to():
    """Ma sai quy uoc (co them so nhanh "-03") van phai duoc gan du an VPK25 - de rule TB-002
    (kiem tra dung/sai pattern) con co co hoi bat loi, khong bi bo qua am tham."""
    assert tim_du_an_khop("VPK25-03-M1007-S4-L", DANH_SACH_DU_AN) == DU_AN_VPK25


def test_khong_khop_project_nao_tra_ve_none():
    assert tim_du_an_khop("M2613-M1110-SS-L", DANH_SACH_DU_AN) is None


def test_ma_ban_ve_rong_tra_ve_none():
    assert tim_du_an_khop(None, DANH_SACH_DU_AN) is None
    assert tim_du_an_khop("", DANH_SACH_DU_AN) is None


def test_danh_sach_du_an_rong_tra_ve_none():
    assert tim_du_an_khop("MH612-M1001-A6-P", []) is None
