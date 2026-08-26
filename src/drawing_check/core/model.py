"""Drawing Document Model - hop dong du lieu giua extractor va rule engine.

Theo dung dinh nghia trong DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 5.2. Moi truong du lieu
mang theo Provenance (nguon, confidence, page, bbox) de biet ket luan den tu dau va ve khoanh do
len PDF duoc. Cac model GDTFrame/SurfaceFinish/WeldSymbol/Thread/Note hien chi la stub toi thieu
(chua co field chi tiet) - se mo rong dung luc trien khai Phase 3/4, khong lam truoc o Phase 1.
"""

from __future__ import annotations

from typing import Generic, Literal, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Provenance(BaseModel):
    """Nguon goc va do tin cay cua 1 truong du lieu da trich xuat."""

    source: Literal["pdf_text", "pdf_text_loose", "ocr", "vlm", "vision", "manual", "dxf"]
    confidence: float
    page: int
    bbox: Optional[tuple[float, float, float, float]] = None


class Field(BaseModel, Generic[T]):
    """1 truong du lieu bat ky, luon di kem Provenance."""

    value: Optional[T] = None
    prov: Provenance


class TitleBlock(BaseModel):
    """Khung ten cua 1 trang ban ve - pham vi duy nhat cua Phase 1 (nhom loi A)."""

    drawing_no: Field[str]
    title: Field[str]
    material: Field[str]
    mass_kg: Field[float]
    scale: Field[str]
    revision: Field[str]
    projection: Field[Literal["first", "third"]]
    general_tol: Field[str]
    unit: Field[str]
    drawn_by: Field[str]
    checked_by: Field[str]
    approved_by: Field[str]
    date_drawn: Field[str]
    sheet: Field[str]
    size: Field[str]


class Dimension(BaseModel):
    """1 kich thuoc tren ban ve - Phase 3."""

    nominal: float
    tol_upper: Optional[float] = None
    tol_lower: Optional[float] = None
    fit_code: Optional[str] = None
    dim_type: Literal["linear", "radial", "diameter", "angular", "ordinate"]
    is_reference: bool = False
    is_basic: bool = False
    prov: Provenance
    # 3 truong duoi day CHI duoc dien khi ghep duoc voi 1 duong kich thuoc hinh hoc that (DIM-007,
    # xem extract/dimension_chain.py) - None nghia la khong ghep duoc/khong ap dung (vd fit-code).
    axis: Optional[Literal["horizontal", "vertical"]] = None
    line_span: Optional[tuple[float, float]] = None  # 2 dau mut doc truc chinh (pt, goc duoi-trai)
    line_cross: Optional[float] = None  # toa do truc con lai (vd y cho duong ngang)
    # cum hinh hoc (HINH CHIEU) ma duong kich thuoc nay thuoc ve - cac duong noi lien nhau (duong
    # bao chi tiet + duong giong + duong kich thuoc) duoc gom chung 1 id qua union-find (xem
    # extract/dimension_chain.py::_gom_cum_hinh_hoc). Dung de KHONG ghep nham kich thuoc bao cua
    # HINH CHIEU nay voi chuoi kich thuoc cua HINH CHIEU khac (loi that phat hien 2026-08-25,
    # trang 28 MH612 - xem docs/Source/Project-Remember.md muc DIM-007).
    view_id: Optional[int] = None


class GDTFrame(BaseModel):
    """Khung dung sai hinh hoc (GD&T) - stub, mo rong o Phase 3."""

    raw_text: str
    prov: Provenance


class SurfaceFinish(BaseModel):
    """Ky hieu do nham be mat - stub, mo rong o Phase 4."""

    raw_text: str
    prov: Provenance


class WeldSymbol(BaseModel):
    """Ky hieu han - stub, mo rong o Phase 4."""

    raw_text: str
    prov: Provenance


class Thread(BaseModel):
    """Ky hieu ren - stub, mo rong o Phase 3/4."""

    raw_text: str
    prov: Provenance


class Note(BaseModel):
    """Ghi chu ky thuat tu do tren ban ve."""

    raw_text: str
    prov: Provenance


PageKind = Literal["vector_text_ok", "vector_no_text", "raster_scan", "mixed", "low_text"]


class PageDoc(BaseModel):
    """Don vi xu ly co ban = MOT TRANG PDF, khong phai mot file.

    Xem bay 5 (DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 1.4) - doi tu per-file sang per-page
    giua du an la sua lai toan bo model/report/database, nen khong duoc doi thiet ke nay.
    """

    file_hash: str
    file_name: str
    page_no: int
    pages_total: int
    page_kind: PageKind
    sheet_size: str
    rotation: int
    title_block: TitleBlock
    dimensions: list[Dimension] = []
    gdt_frames: list[GDTFrame] = []
    surface_finishes: list[SurfaceFinish] = []
    welds: list[WeldSymbol] = []
    threads: list[Thread] = []
    notes: list[Note] = []
    # Nhan "P.C.D" (duong tron chia lo bulong) tim duoc tren trang - phuc vu DIM-002 (thieu ky
    # hieu duong kinh phi, xem extract/dimension.py::trich_nhan_pcd). raw_text la chuoi khop
    # duoc (vd "P.C.D.44" hoac "P.C.Dφ38") - rule tu kiem tra co ky hieu phi hay khong qua regex,
    # KHONG phan xu o buoc trich xuat (dung nguyen tac kien truc "extractor khong phan xu").
    pcd_labels: list[Note] = []


class DrawingDoc(BaseModel):
    """Mot BAN VE = cac trang co cung drawing_no, sap theo sheet x/y."""

    drawing_no: str
    pages: list[PageDoc]
    sheets_expected: Optional[int] = None
    sheets_found: int
