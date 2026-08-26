"""Test logic so khop mau anh cho ky hieu goc chieu (vision/projection_symbol.py) - dung anh gia
lap (numpy), KHONG can trang PDF that/GPU, khac voi luong --vision day du (RT-DETR). Nguong IOU/
INK da hieu chinh tren du lieu that (51 trang MH612, xem docstring module) - o day chi kiem tra
LOGIC quyet dinh dung voi cac nguong do, khong chay lai toan bo qua trinh hieu chinh."""

from __future__ import annotations

import numpy as np

from drawing_check.vision.projection_symbol import _quyet_dinh_tu_anh_nhi_phan

_MAU_GIA_LAP = np.zeros((50, 50), dtype=bool)
_MAU_GIA_LAP[10:40, 10:40] = True  # 1 khoi vuong "muc den" gia lap, ty le ~36%


def test_khop_tuyet_doi_voi_mau_tra_ve_first():
    gia_tri, do_tin_cay = _quyet_dinh_tu_anh_nhi_phan(_MAU_GIA_LAP.copy(), _MAU_GIA_LAP)
    assert gia_tri == "first"
    assert do_tin_cay >= 0.5


def test_anh_trong_hoan_toan_tra_ve_none():
    trong = np.zeros((50, 50), dtype=bool)
    gia_tri, _ = _quyet_dinh_tu_anh_nhi_phan(trong, _MAU_GIA_LAP)
    assert gia_tri is None


def test_co_muc_den_nhung_khong_khop_mau_tra_ve_third():
    # 1 khoi vuong o VI TRI KHAC hoan toan, khong giao voi mau -> IoU thap nhung ink_ratio cao
    khac_vi_tri = np.zeros((50, 50), dtype=bool)
    khac_vi_tri[0:5, 0:5] = True  # 25/2500 = 1% - qua nho, se roi vao truong hop "trong"
    khac_vi_tri[0:15, 0:15] = True  # 225/2500 = 9% > NGUONG_INK_TRONG (3%), du lon de tinh la "co muc den"
    gia_tri, do_tin_cay = _quyet_dinh_tu_anh_nhi_phan(khac_vi_tri, _MAU_GIA_LAP)
    assert gia_tri == "third"
    assert do_tin_cay < 0.5


def test_net_mong_hon_van_khop_neu_iou_du_cao():
    """Mo phong truong hop that (trang 46/47 MH612): net ve mong hon (it muc den hon) nhung van
    dung ky hieu - IoU van phai vuot nguong neu phan giao du lon."""
    net_mong = np.zeros((50, 50), dtype=bool)
    net_mong[15:35, 15:35] = True  # nam gon trong khoi cua _MAU_GIA_LAP, nho hon nhieu
    gia_tri, _ = _quyet_dinh_tu_anh_nhi_phan(net_mong, _MAU_GIA_LAP)
    assert gia_tri == "first"
