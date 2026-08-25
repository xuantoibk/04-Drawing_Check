#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_pages_for_labeling.py — Render trang PDF thanh anh PNG de gan nhan (Phase 4, muc 4.2.1)

Dung truoc khi gan nhan bang Label Studio: doc toan bo PDF trong 1 thu muc, render moi trang
thanh 1 anh PNG do phan giai cao (mac dinh 300 DPI - du chi tiet de thay ky hieu GD&T/do nham
nho tren ban ve, dung DPI da chot trong ke hoach goc Phase 4).

Dung:
    python tools/render_pages_for_labeling.py "00_input" --out "01_vision_labeling/images"
    python tools/render_pages_for_labeling.py "00_input/mot_file.pdf" --dpi 300
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pypdfium2 as pdfium


def render_pdf(pdf_path: Path, out_dir: Path, dpi: int) -> int:
    scale = dpi / 72.0
    so_trang_da_render = 0
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        for i in range(len(pdf)):
            page = pdf[i]
            try:
                bitmap = page.render(scale=scale)
                image = bitmap.to_pil()
                ten_anh = f"{pdf_path.stem}_p{i + 1:03d}.png"
                image.save(out_dir / ten_anh)
                so_trang_da_render += 1
            finally:
                page.close()
    finally:
        pdf.close()
    return so_trang_da_render


def main() -> int:
    ap = argparse.ArgumentParser(description="Render trang PDF thanh anh PNG de gan nhan")
    ap.add_argument("path", help="File PDF hoac thu muc chua PDF")
    ap.add_argument("--out", default="01_vision_labeling/images", help="Thu muc luu anh PNG")
    ap.add_argument("--dpi", type=int, default=300, help="Do phan giai (mac dinh 300)")
    args = ap.parse_args()

    root = Path(args.path)
    pdfs = [root] if root.is_file() else sorted(root.rglob("*.pdf"))
    if not pdfs:
        print(f"Khong tim thay PDF nao trong: {root}")
        return 1

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    tong_trang = 0
    print(f"\nDang render {len(pdfs)} file PDF o {args.dpi} DPI vao {out_dir}...\n")
    for pdf_path in pdfs:
        try:
            n = render_pdf(pdf_path, out_dir, args.dpi)
            print(f"  {pdf_path.name:<45} {n:>3} trang")
            tong_trang += n
        except Exception as e:
            print(f"  {pdf_path.name:<45} LOI: {type(e).__name__}: {e}", file=sys.stderr)

    print(f"\nXong: {tong_trang} anh PNG trong {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
