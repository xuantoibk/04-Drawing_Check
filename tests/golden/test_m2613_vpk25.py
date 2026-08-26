"""Golden test cho du an M2613/VPK25 (Alpha Vina) - chay THAT extractor + rule engine tren 3 file
PDF khach hang that (00_input/BVCT*.pdf goc), dung 2 profile config/projects/m2613.yaml +
config/projects/vpk25.yaml da chot 2026-08-24.

Khac tests/golden/test_mh612.py: day la lo du lieu THAT SU CO NHIEU LOI (nguoi dung xac nhan
truc tiep khi dung ho so nay) - phan lon FAIL (TB-002 tren ~69/79 trang VPK25 ghi sai so nhanh)
la CO Y, khong phai dau hieu cong cu bi loi. Xem chu thich chi tiet trong m2613_vpk25/expected.yaml.

File PDF nguon la bi mat kinh doanh, KHONG commit git (xem .gitignore) - test nay TU DONG BO QUA
(skip, khong fail) tren may khong co ban sao trong tests/golden/m2613_vpk25/.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drawing_check.engine.loader import doc_thu_muc_rule
from drawing_check.pipeline import chay_1_file

THU_MUC_GOC = Path(__file__).resolve().parents[2]
THU_MUC_GOLDEN = Path(__file__).resolve().parent / "m2613_vpk25"
FILE_KY_VONG = THU_MUC_GOLDEN / "expected.yaml"


def _cac_file_pdf(ky_vong: dict) -> list[Path]:
    return [THU_MUC_GOLDEN / ten for ten in ky_vong["files"]]


def _thieu_file_nao() -> bool:
    if not FILE_KY_VONG.exists():
        return True
    ky_vong = yaml.safe_load(FILE_KY_VONG.read_text(encoding="utf-8"))
    return not all(p.exists() for p in _cac_file_pdf(ky_vong))


pytestmark = pytest.mark.skipif(
    _thieu_file_nao(),
    reason="Khong co du ban sao 3 file PDF khach hang tren may nay (bi mat kinh doanh, khong commit git)",
)


@pytest.fixture(scope="module")
def ky_vong() -> dict:
    return yaml.safe_load(FILE_KY_VONG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ket_qua_theo_file(ky_vong):
    project = [
        yaml.safe_load(p.read_text(encoding="utf-8"))
        for p in (THU_MUC_GOC / "config/projects/m2613.yaml", THU_MUC_GOC / "config/projects/vpk25.yaml")
    ]
    vat_lieu = yaml.safe_load((THU_MUC_GOC / "config/catalogs/materials.yaml").read_text(encoding="utf-8"))
    iso286 = yaml.safe_load((THU_MUC_GOC / "config/catalogs/iso286_letters.yaml").read_text(encoding="utf-8"))
    context_catalogs = {"materials": vat_lieu["materials"], "iso286": iso286}
    rules = doc_thu_muc_rule(THU_MUC_GOC / "rules")

    ket_qua: dict[str, tuple[list, list]] = {}
    for duong_dan in _cac_file_pdf(ky_vong):
        # chay_dimension_chain=False: golden set nay dong bang baseline DA duoc nguoi dung xac
        # nhan thu cong truoc khi co DIM-007 (2026-08-25) - DIM-007 chua qua review, khong duoc
        # tu dong lam vao phep so khop expected.yaml (dimension_chain mac dinh BAT o CLI/chay
        # thuong ngay, nhung KHONG bat o day). Xem tests/golden/test_mh612.py ghi chu tuong tu.
        ket_qua[duong_dan.name] = chay_1_file(
            duong_dan, rules, project, context_catalogs, chay_dimension_chain=False
        )
    return ket_qua


def test_tong_so_trang_khop_ky_vong(ket_qua_theo_file, ky_vong):
    tong = sum(len(trang_list) for trang_list, _ in ket_qua_theo_file.values())
    assert tong == ky_vong["so_trang"]


def test_tong_ket_finding_khop_ky_vong(ket_qua_theo_file, ky_vong):
    so_luong = {"FAIL": 0, "WARN": 0, "INFO": 0}
    for _, findings in ket_qua_theo_file.values():
        for f in findings:
            so_luong[f.level] += 1
    assert so_luong == ky_vong["tong_ket"]


def test_loi_biet_truoc_van_con_bi_bat(ket_qua_theo_file, ky_vong):
    for loi in ky_vong["loi_biet_truoc"]:
        _, findings = ket_qua_theo_file[loi["file"]]

        if loi.get("khong_co_fail"):
            fail_cua_ban_ve = [
                f for f in findings if f.drawing_no == loi["drawing_no"] and f.level == "FAIL"
            ]
            assert not fail_cua_ban_ve, f"Ban ve {loi['drawing_no']} khong duoc co FAIL nao"
            continue

        khop = [
            f
            for f in findings
            if f.page_no == loi["trang"]
            and f.rule_id == loi["rule_id"]
            and f.drawing_no == loi["drawing_no"]
        ]
        assert khop, f"Khong con bat duoc loi da biet: {loi['file']} trang {loi['trang']} {loi['rule_id']}"
