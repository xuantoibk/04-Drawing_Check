"""Primitive doi chieu CHEO giua page.dimensions (Phase 3) va page.surface_finishes/gdt_frames
(Phase 4, tu vision) - tang thu 3 cua rule engine, dung chung 1 runner voi primitives_dimension.py
(engine/runner.py::chay_rule_tren_trang_kich_thuoc) vi cung nhan vao ca 'page' va tra ve list vi
pham theo dung dinh dang {'gia_tri','nguon','do_tin_cay','bbox'}.

Ket qua tu vision LUON WARN (khong bao gio FAIL) - runner tu ha muc qua NGUON_KHONG_CHAC_CHAN khi
thay nguon='vision', dung nguyen tac kien truc cot loi "AI chi trich xuat, khong bao gio phan xu".
"""

from __future__ import annotations

from typing import Any

from drawing_check.core.model import PageDoc


def thieu_do_nham_khi_co_dung_sai_lap_ghep(
    page: PageDoc, params: dict, context: dict
) -> list[dict[str, Any]]:
    """Trang co it nhat 1 kich thuoc voi ma lap ghep (fit_code, vd G6/H7 - can gia cong chinh
    xac) nhung KHONG phat hien duoc bat ky ky hieu do nham be mat nao tren ca trang - dang nghi,
    can nguoi xem lai (co the ky hieu nam o vung anh detector bo sot, hoac that su thieu sot tren
    ban ve goc). Kiem tra CA TRANG (khong doi chieu vi tri tung ky hieu voi tung kich thuoc) - lan
    dau lam don gian, chua du du lieu de kiem chung ghep cap theo toa do.

    QUAN TRONG: chi ket luan khi VISION DA THUC SU CHAY tren trang nay (context['vision_enabled']
    = True, do pipeline.py truyen vao khi chay_vision=True) - neu khong se KHONG PHAN BIET DUOC
    "vision da chay va khong thay ky hieu nao" voi "vision chua chay" (page.surface_finishes rong
    trong CA 2 truong hop, vi day la gia tri mac dinh cua PageDoc) - da tung gay WARN sai hang loat
    tren test/CLI mac dinh (chay_vision=False) truoc khi phat hien va sua (2026-08-25)."""
    if not context.get("vision_enabled"):
        return []
    dims_co_fit = [d for d in page.dimensions if d.fit_code]
    if not dims_co_fit or page.surface_finishes:
        return []

    d = dims_co_fit[0]
    return [
        {
            "gia_tri": f"{d.nominal:g}{d.fit_code}",
            "nguon": "vision",
            "do_tin_cay": 0.5,
            "bbox": d.prov.bbox,
        }
    ]


PRIMITIVES_KY_HIEU: dict[str, Any] = {
    "thieu_do_nham_khi_co_dung_sai_lap_ghep": thieu_do_nham_khi_co_dung_sai_lap_ghep,
}
