"""Primitive cho rule chay tren `page.dimensions` (list, khong phai 1 Field don) - tang thu 3
cua rule engine (khac primitives.py cho 1 truong/1 trang, primitives_drawing.py cho quan he giua
nhieu trang). Phase 3, lat cat dau tien - xem docs/Source/Project-Remember.md.

Moi ham tra ve LIST cac vi pham (1 trang co the co NHIEU Dimension sai cung luc, khac quy uoc
primitives.py/primitives_drawing.py chi tra ve 1 vi pham). Moi phan tu vi pham la dict co it nhat
{'gia_tri', 'nguon', 'do_tin_cay', 'bbox'} de runner dung dinh dang message + xac dinh muc FAIL/WARN.
"""

from __future__ import annotations

import re
from typing import Any

from drawing_check.core.model import PageDoc

_MAU_FIT_CODE = re.compile(r"([A-Za-z]{1,2})(\d{1,2})")


def fit_code_sai_cu_phap(page: PageDoc, params: dict, context: dict) -> list[dict[str, Any]]:
    """Kiem tra tung Dimension co fit_code: cu phap phai la <chu cai lech chuan><cap chinh xac>
    hop le theo ISO 286/JIS B 0401 (config/catalogs/iso286_letters.yaml). Danh muc rong (chua nap)
    thi KHONG ket luan (giong field_in_catalog trong primitives.py), tranh bao sai hang loat."""
    danh_muc = context.get("catalogs", {}).get("iso286", {})
    chu_cai_hop_le = set(danh_muc.get("chu_cai_lech_chuan", []))
    cap_hop_le = set(danh_muc.get("cap_chinh_xac", []))
    if not chu_cai_hop_le or not cap_hop_le:
        return []

    vi_pham = []
    for dim in page.dimensions:
        if not dim.fit_code:
            continue
        m = _MAU_FIT_CODE.fullmatch(dim.fit_code)
        hop_le = bool(m) and m.group(1).upper() in chu_cai_hop_le and m.group(2) in cap_hop_le
        if not hop_le:
            vi_pham.append(
                {
                    "gia_tri": f"{dim.nominal:g}{dim.fit_code}",
                    "nguon": dim.prov.source,
                    "do_tin_cay": dim.prov.confidence,
                    "bbox": dim.prov.bbox,
                }
            )
    return vi_pham


_RE_PCD_CO_KY_HIEU = re.compile(r"P\.?C\.?D\.?[φΦ⌀]", re.IGNORECASE)


def pcd_thieu_ky_hieu_duong_kinh(page: PageDoc, params: dict, context: dict) -> list[dict[str, Any]]:
    """DIM-002: nhan P.C.D (duong tron chia lo bulong) phai kem ky hieu duong kinh (phi/⌀) truoc
    con so - vd "P.C.Dφ38" dung, "P.C.D.44" sai (thieu ky hieu). Nguoi dung phat hien 2026-08-25,
    xem docs/Source/Project-Remember.md. Kiem tra bang regex tren raw_text - dung nguyen tac
    "extractor khong phan xu": extract/dimension.py::trich_nhan_pcd chi tra ve nhan tim duoc,
    KHONG tu xac dinh dung/sai, rule engine (o day) moi la noi quyet dinh."""
    vi_pham = []
    for nhan in page.pcd_labels:
        if not _RE_PCD_CO_KY_HIEU.match(nhan.raw_text):
            vi_pham.append(
                {
                    "gia_tri": nhan.raw_text,
                    "nguon": nhan.prov.source,
                    "do_tin_cay": nhan.prov.confidence,
                    "bbox": nhan.prov.bbox,
                }
            )
    return vi_pham


_NGUONG_NOI_CHUOI = 3.0  # pt - 2 doan duoc coi la "noi tiep nhau" neu dau mut cach nhau <= nguong
_NGUONG_KHOP_TONG = 4.0  # pt - tong 1 chuoi phai khop kich thuoc bao trong khoang nay moi bi bao
# pt - kich thuoc bao phai nam GAN chuoi theo TRUC CON LAI (cross) - vd 2 duong ngang xep chong
# nhau de tranh de len chu, dat CACH NHAU vai chuc-vai tram pt, KHONG phai hang nghin pt. Da hieu
# chinh tren du lieu that 2026-08-25: vi du dung xa nhat quan sat duoc la 128pt (trang 28 MH612,
# chuoi cross=765.4, kich thuoc bao "215" cross=637.4) - loi that tung gap (trang 26 MH612) la 1
# duong CACH XA 945pt bi ghep nham chi vi trung hop khop dau mut, du CUNG 1 cum hinh chieu.
_NGUONG_KHOP_CROSS = 200.0
# Sai so TUONG DOI toi da giua tong chuoi va gia tri kich thuoc bao (vd 215.5 vs "215" ghi tren
# ban ve = lech 0.23%, van la ca that) - loi that tung gap (trang 27 MH612): 1 duong khop VI TRI
# (co the do doc nham 1 gia tri khac, vd "520" thay vi "24") nhung gia tri SO lech toi 775%
# (560 vs "64") van bi chap nhan vi la ung vien DUY NHAT khop vi tri - phai co nguong hop ly rieng
# cho do lech gia tri, khong chi dua vao vi tri hinh hoc.
_TY_LE_LECH_TOI_DA = 0.10
_NGUONG_LECH_TUYET_DOI_TOI_THIEU = 2.0  # mm - san cho chuoi gia tri nho (vd tong=5, 10% chi la 0.5)


def _tim_kich_thuoc_bao(
    cung_truc: list,
    x_min: float,
    x_max: float,
    id_chuoi: set[int],
    tong_nominal: float,
    view_id_chuoi,
    cross_chuoi: float,
):
    """Tra ve ung vien kich thuoc bao KHOP VI TRI TOT NHAT, CUNG 1 CUM HINH CHIEU voi chuoi.

    3 tang loc, tat ca deu tu loi that phat hien tren du lieu 2026-08-25:
    1. CUNG HINH CHIEU (view_id) - truoc do "10+50.5+50+60+45" (hinh chieu tren, trang 28 MH612)
       tung bi ghep nham voi "215"/"213.5" (thuoc hinh chieu DUOI, chi tinh co vi tri X gan nhau
       tren trang) - nguoi dung phat hien va de xuat dung cum hinh hoc (duong noi nhau) de phan
       biet hinh chieu, xem extract/dimension_chain.py::_gom_cum_hinh_hoc.
    2. GAN theo TRUC CON LAI (_NGUONG_KHOP_CROSS) - truoc do 1 duong "64" cach chuoi toi 945pt
       (trang 26 MH612) van bi ghep nham vi CUNG view_id va khop dau mut truc chinh - can gioi
       han khoang cach hop ly theo truc kia, khong chi dua vao view_id.
    3. Neu NHIEU ung vien cung khop (vd trong CUNG 1 hinh chieu van co "215" va "213.5"), uu tien
       ung vien co GIA TRI SO gan dung TONG chuoi nhat."""
    ung_vien = []
    for d in cung_truc:
        if id(d) in id_chuoi or d.view_id != view_id_chuoi:
            continue
        if abs(d.line_cross - cross_chuoi) > _NGUONG_KHOP_CROSS:
            continue
        lo, hi = d.line_span
        if abs(lo - x_min) <= _NGUONG_KHOP_TONG and abs(hi - x_max) <= _NGUONG_KHOP_TONG:
            ung_vien.append(d)
    if not ung_vien:
        return None
    nguong_lech = max(_TY_LE_LECH_TOI_DA * tong_nominal, _NGUONG_LECH_TUYET_DOI_TOI_THIEU)
    ung_vien = [d for d in ung_vien if abs(d.nominal - tong_nominal) <= nguong_lech]
    if not ung_vien:
        return None
    return min(ung_vien, key=lambda d: abs(d.nominal - tong_nominal))


_DEM_KHOANH_DO = 8.0  # pt - nong them quanh 2 duong (chuoi + kich thuoc bao) de nhin ro khi khoanh


def _bbox_khoanh_do(chuoi: list, bao, x_min: float, x_max: float):
    """Tinh bbox de KHOANH DO tren PDF - theo dung DUONG KICH THUOC (line_span/line_cross) cua
    ca chuoi VA kich thuoc bao, KHONG theo bbox cua tung CHU SO rieng le (truoc do dung
    prov.bbox hop cua cac chu so, tao ra vung khoanh rong rac/khong dung vi tri thuc te cua
    duong - nguoi dung phat hien 2026-08-25 tren file CYS-M1004-SC-NI-T: 'nhan dien chuoi chuan
    nhung danh dau do chua chuan'). Vi chuoi va bao thuong nam O 2 HANG/COT KHAC NHAU (xep chong
    de tranh de len chu), vung khoanh phai trai dai tu truc chinh (x_min..x_max) VA phu ca 2
    cross (chuoi + bao), khong chi 1 duong."""
    cross_min = min(chuoi[0].line_cross, bao.line_cross)
    cross_max = max(chuoi[0].line_cross, bao.line_cross)
    if chuoi[0].axis == "horizontal":
        return (x_min, cross_min - _DEM_KHOANH_DO, x_max, cross_max + _DEM_KHOANH_DO)
    return (cross_min - _DEM_KHOANH_DO, x_min, cross_max + _DEM_KHOANH_DO, x_max)


def _phat_hien_chuoi_khep_kin_1_truc(cung_truc: list) -> list[dict[str, Any]]:
    """cung_truc: danh sach Dimension CUNG 1 TRUC (deu horizontal hoac deu vertical), da co
    line_span/line_cross. Nhom theo line_cross (cung 1 hang/cot) de tim CHUOI noi tiep nhau, roi
    doi chieu tong chuoi voi 1 kich thuoc bao (CHUC NANG khac hang/cot, mien tong dau mut khop)."""
    theo_cross: dict[float, list] = {}
    for d in cung_truc:
        theo_cross.setdefault(round(d.line_cross, 1), []).append(d)

    vi_pham: list[dict[str, Any]] = []
    for nhom in theo_cross.values():
        nhom_sap = sorted(nhom, key=lambda d: d.line_span[0])
        i = 0
        while i < len(nhom_sap):
            chuoi = [nhom_sap[i]]
            j = i + 1
            while (
                j < len(nhom_sap)
                and abs(nhom_sap[j].line_span[0] - chuoi[-1].line_span[1]) <= _NGUONG_NOI_CHUOI
            ):
                chuoi.append(nhom_sap[j])
                j += 1

            if len(chuoi) >= 2 and not any(d.is_reference for d in chuoi):
                x_min, x_max = chuoi[0].line_span[0], chuoi[-1].line_span[1]
                id_chuoi = {id(d) for d in chuoi}
                tong_nominal = sum(d.nominal for d in chuoi)
                bao = _tim_kich_thuoc_bao(
                    cung_truc,
                    x_min,
                    x_max,
                    id_chuoi,
                    tong_nominal,
                    chuoi[0].view_id,
                    chuoi[0].line_cross,
                )
                if bao is not None:
                    ve_chuoi = "+".join(f"{d.nominal:g}" for d in chuoi)
                    vi_pham.append(
                        {
                            "gia_tri": f"{ve_chuoi}={bao.nominal:g}",
                            "nguon": "pdf_text",
                            "do_tin_cay": min(d.prov.confidence for d in [*chuoi, bao]),
                            "bbox": _bbox_khoanh_do(chuoi, bao, x_min, x_max),
                        }
                    )
            i = j if j > i else i + 1
    return vi_pham


def chuoi_kich_thuoc_khep_kin(page: PageDoc, params: dict, context: dict) -> list[dict[str, Any]]:
    """DIM-007: chuoi kich thuoc (>=2 doan noi tiep) + 1 kich thuoc bao co dau mut TRUNG KHOP voi
    tong chuoi, ma KHONG doan nao trong chuoi duoc danh dau tham khao (ngoac don) - ban ve bi
    "khep vong": dung sai cua chuoi va dung sai cua kich thuoc bao co the mau thuan nhau, xuong gia
    cong khong biet uu tien theo cai nao. Xem docs/Source/Project-Remember.md muc DIM-007 de biet
    vi du that (trang 5 MH612) va ly do PHAI so khop CHINH XAC 2 dau mut (khong chi "gan nhau
    trong cung 1 view") - da kiem chung tren du lieu that de tranh bao sai truong hop 2 kich thuoc
    do toi 2 diem khac nhau nhung xep chong nhau tren ban ve.

    QUAN TRONG: chi ket luan khi DIM-007 DA THUC SU CHAY (context['dimension_chain_enabled'] =
    True, pipeline.py truyen vao) - tranh nham "khong co du lieu hinh hoc" voi "co du lieu, khong
    thay vi pham" (giong nguyen tac da ap dung cho SYM-001, xem primitives_symbols.py)."""
    if not context.get("dimension_chain_enabled"):
        return []

    dims_co_duong = [
        d for d in page.dimensions if d.dim_type == "linear" and d.axis is not None
    ]
    ngang = [d for d in dims_co_duong if d.axis == "horizontal"]
    doc = [d for d in dims_co_duong if d.axis == "vertical"]
    return _phat_hien_chuoi_khep_kin_1_truc(ngang) + _phat_hien_chuoi_khep_kin_1_truc(doc)


PRIMITIVES_KICH_THUOC: dict[str, Any] = {
    "fit_code_sai_cu_phap": fit_code_sai_cu_phap,
    "pcd_thieu_ky_hieu_duong_kinh": pcd_thieu_ky_hieu_duong_kinh,
    "chuoi_kich_thuoc_khep_kin": chuoi_kich_thuoc_khep_kin,
}
