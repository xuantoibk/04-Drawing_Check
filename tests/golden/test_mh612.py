"""Golden test cho du an MH612 (Alpha Vina) - chay THAT extractor + rule engine tren PDF khach
hang, khong dung du lieu gia nhu tests/unit/.

File PDF nguon la bi mat kinh doanh, KHONG commit git (xem .gitignore) - test nay TU DONG BO QUA
(skip, khong fail) tren may khong co ban sao trong tests/golden/mh612/. Ket qua da xac nhan thu
cong luu o expected.yaml (xem file do de biet gioi han: chi 1 mau khung ten, coi la TAM THOI).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drawing_check.core.grouping import gom_trang_thanh_ban_ve
from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.engine.runner import chay_rule_tren_ban_ve
from drawing_check.pipeline import chay_1_file, tim_du_an_khop

THU_MUC_GOC = Path(__file__).resolve().parents[2]
THU_MUC_GOLDEN = Path(__file__).resolve().parent / "mh612"
FILE_PDF = THU_MUC_GOLDEN / "MH612-DATA GIA CONG FULL.pdf"
FILE_KY_VONG = THU_MUC_GOLDEN / "expected.yaml"

pytestmark = pytest.mark.skipif(
    not FILE_PDF.exists(),
    reason="Khong co ban sao PDF khach hang tren may nay (bi mat kinh doanh, khong commit git)",
)


@pytest.fixture(scope="module")
def ky_vong() -> dict:
    return yaml.safe_load(FILE_KY_VONG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ket_qua():
    project = yaml.safe_load(
        (THU_MUC_GOC / "config/projects/mh612.yaml").read_text(encoding="utf-8")
    )
    vat_lieu = yaml.safe_load(
        (THU_MUC_GOC / "config/catalogs/materials.yaml").read_text(encoding="utf-8")
    )
    iso286 = yaml.safe_load(
        (THU_MUC_GOC / "config/catalogs/iso286_letters.yaml").read_text(encoding="utf-8")
    )
    danh_sach_du_an = [project]
    catalogs = {"materials": vat_lieu["materials"], "iso286": iso286}
    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")
    # chay_dimension_chain=False: dong bang baseline DA duoc nguoi dung xac nhan thu cong truoc
    # khi co DIM-007 (2026-08-25, doc duong hinh hoc qua pdfplumber) - DIM-007 chua qua review,
    # khong duoc tu dong lam vao phep so khop expected.yaml (dimension_chain mac dinh BAT o
    # CLI/chay thuong ngay, nhung KHONG bat o day).
    trang_list, findings = chay_1_file(
        FILE_PDF, rules, danh_sach_du_an, catalogs, chay_dimension_chain=False
    )
    for ban_ve in gom_trang_thanh_ban_ve(trang_list):
        context_ban_ve = {"project": tim_du_an_khop(ban_ve.drawing_no, danh_sach_du_an) or {}}
        findings.extend(chay_rule_tren_ban_ve(ban_ve, rules, context_ban_ve))
    return trang_list, findings


def test_so_trang_khop_ky_vong(ket_qua, ky_vong):
    trang_list, _ = ket_qua
    assert len(trang_list) == ky_vong["so_trang"]


def test_tong_ket_finding_khop_ky_vong(ket_qua, ky_vong):
    _, findings = ket_qua
    so_luong = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for f in findings:
        so_luong[f.level] += 1
    assert so_luong == ky_vong["tong_ket"]


def test_loi_biet_truoc_van_con_bi_bat(ket_qua, ky_vong):
    _, findings = ket_qua
    for loi in ky_vong["loi_biet_truoc"]:
        khop = [
            f
            for f in findings
            if f.page_no == loi["trang"]
            and f.rule_id == loi["rule_id"]
            and f.drawing_no == loi["drawing_no"]
        ]
        assert khop, f"Khong con bat duoc loi da biet: trang {loi['trang']} {loi['rule_id']}"
