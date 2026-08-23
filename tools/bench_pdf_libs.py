#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bench_pdf_libs.py — So sánh thư viện đọc PDF TRÊN CHÍNH BẢN VẼ CỦA BẠN.

Drawing Check / Phase 0

Vì sao cần script này: mọi benchmark PDF trên mạng đều đo trên tài liệu văn xuôi
(thứ tự đọc, nhiều cột, bảng biểu). Bản vẽ kỹ thuật KHÔNG có mấy thứ đó. Số liệu
duy nhất đáng tin là số đo trên bản vẽ thật của bạn.

Đo 2 thứ:
  1. TỐC ĐỘ  — ms cho mỗi trang
  2. CHẤT LƯỢNG — mỗi thư viện đọc ra text khung tên thế nào (in ra để bạn tự so)

Cài đặt (cái nào thiếu thì script tự bỏ qua):
    pip install pypdfium2 pdfplumber pypdf

Dùng:
    python bench_pdf_libs.py duong_dan.pdf
    python bench_pdf_libs.py "D:\\BanVe" --pages 40
"""

from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path

# vùng khung tên: 45% chiều rộng bên phải, 35% chiều cao dưới đáy
TB_W, TB_H = 0.45, 0.35


def _timed(fn, repeat: int):
    ts = []
    out = None
    for _ in range(repeat):
        t0 = time.perf_counter()
        out = fn()
        ts.append(time.perf_counter() - t0)
    return statistics.median(ts), out


# ---------------------------------------------------------------- pypdfium2
def run_pdfium(path: str):
    import pypdfium2 as pdfium
    doc = pdfium.PdfDocument(path)
    res = []
    for i in range(len(doc)):
        pg = doc[i]
        tp = pg.get_textpage()
        w, h = pg.get_width(), pg.get_height()
        res.append(tp.get_text_bounded(left=w * (1 - TB_W), bottom=0,
                                       right=w, top=h * TB_H))
        tp.close(); pg.close()
    doc.close()
    return res


# ---------------------------------------------------------------- pdfplumber
def run_plumber(path: str):
    import pdfplumber
    res = []
    with pdfplumber.open(path) as pdf:
        for pg in pdf.pages:
            crop = pg.crop((pg.width * (1 - TB_W), pg.height * (1 - TB_H),
                            pg.width, pg.height))
            res.append(crop.extract_text(x_tolerance=1.5, y_tolerance=2) or "")
    return res


# ---------------------------------------------------------------- pypdf
def run_pypdf(path: str):
    import pypdf
    r = pypdf.PdfReader(path)
    # pypdf không cắt được theo vùng -> trả text cả trang
    return [p.extract_text() or "" for p in r.pages]


ENGINES = [
    ("pypdfium2", run_pdfium, "Apache-2.0 / BSD-3", "CO"),
    ("pdfplumber", run_plumber, "MIT", "CO"),
    ("pypdf", run_pypdf, "BSD-3", "KHONG"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--repeat", type=int, default=7)
    ap.add_argument("--files", type=int, default=10, help="So file toi da")
    args = ap.parse_args()

    root = Path(args.path)
    pdfs = [root] if root.is_file() else sorted(root.rglob("*.pdf"))[: args.files]
    if not pdfs:
        print("Khong tim thay PDF."); return 1

    total_pages = 0
    try:
        import pypdf
        for p in pdfs:
            try: total_pages += len(pypdf.PdfReader(str(p)).pages)
            except Exception: total_pages += 1
    except ImportError:
        total_pages = len(pdfs)

    print(f"\nDo tren {len(pdfs)} file / ~{total_pages} trang, lay trung vi {args.repeat} lan\n")
    print(f"{'Thu vien':<14}{'ms/trang':>10}{'Nhanh gap':>11}  {'License':<20}{'Cat vung?':<10}")
    print("-" * 70)

    results = {}
    for name, fn, lic, crop in ENGINES:
        try:
            tot = 0.0
            sample = None
            for p in pdfs:
                dt, out = _timed(lambda p=p: fn(str(p)), args.repeat)
                tot += dt
                if sample is None and out:
                    sample = out[0]
            per_page = tot / max(total_pages, 1) * 1000
            results[name] = (per_page, sample)
        except ImportError:
            print(f"{name:<14}{'chua cai':>10}"); continue
        except Exception as e:
            print(f"{name:<14}{'LOI':>10}  {type(e).__name__}: {e}"); continue

    if results:
        fastest = min(v[0] for v in results.values())
        for name, fn, lic, crop in ENGINES:
            if name not in results: continue
            ms, _ = results[name]
            print(f"{name:<14}{ms:>9.2f}{ms/fastest:>10.1f}x  {lic:<20}{crop:<10}")

    print("\n" + "=" * 70)
    print("TEXT KHUNG TEN DOC DUOC (trang dau tien) — TU SO CHAT LUONG")
    print("=" * 70)
    for name in results:
        _, sample = results[name]
        print(f"\n[{name}]\n{'-'*40}")
        print((sample or "(rong)").strip()[:600])

    print("\nGHI CHU: neu mot thu vien tra ve RONG trong khi thu vien khac co text,")
    print("day la trang dinh bay font SHX hoac loi encoding -> xem probe_pdf.py\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
