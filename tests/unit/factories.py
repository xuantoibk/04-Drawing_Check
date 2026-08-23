"""Helper dung chung cho test - tao PageDoc/TitleBlock gia (khong can PDF that), dung y tuong
"test rule engine bang JSON gia" tu DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 5.2/9."""

from __future__ import annotations

from drawing_check.core.model import Field, PageDoc, Provenance, TitleBlock

_TRUONG_TITLE_BLOCK = [
    "drawing_no", "title", "material", "mass_kg", "scale", "revision", "projection",
    "general_tol", "unit", "drawn_by", "checked_by", "approved_by", "date_drawn", "sheet", "size",
]


def prov_mau(source: str = "pdf_text", confidence: float = 1.0, page: int = 1) -> Provenance:
    return Provenance(source=source, confidence=confidence, page=page)


def title_block_mau(**gia_tri) -> TitleBlock:
    """Tao TitleBlock voi moi truong mac dinh None (kem Provenance pdf_text), ghi de qua gia_tri.

    vd title_block_mau(drawing_no="KB-00123-A01", checked_by="NVA")
    """
    du_lieu = {}
    for ten in _TRUONG_TITLE_BLOCK:
        gia = gia_tri.get(ten)
        du_lieu[ten] = Field(value=gia, prov=prov_mau())
    return TitleBlock.model_validate(du_lieu)


def page_mau(
    *,
    page_no: int = 1,
    pages_total: int = 1,
    file_name: str = "mau.pdf",
    title_block: TitleBlock | None = None,
    **title_block_overrides,
) -> PageDoc:
    return PageDoc(
        file_hash="0" * 8,
        file_name=file_name,
        page_no=page_no,
        pages_total=pages_total,
        page_kind="vector_text_ok",
        sheet_size="A3",
        rotation=0,
        title_block=title_block or title_block_mau(**title_block_overrides),
    )
