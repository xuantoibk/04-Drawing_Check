#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_vision_dataset.py — Xuat nhan Label Studio (Phase 4) ra dinh dang COCO

Doc truc tiep tu SQLite cua Label Studio (API bi khoa JWT tren may nay - xem
docs/Source/... ghi chu 2026-08-24/25), gop annotation tu nhieu project (moi project ung voi 1
thu muc anh nguon rieng), chuyen bbox tu % (Label Studio) sang pixel tuyet doi (COCO), chia
train/val theo ty le --val-ratio va co gang giu it nhat 1 vai anh co gdt_datum trong ca 2 tap
(lop hiem hon surface_finish).

Dung:
    python tools/export_vision_dataset.py
"""

from __future__ import annotations

import json
import random
import re
import sqlite3
import urllib.parse
from pathlib import Path

from PIL import Image

DB_PATH = Path.home() / "AppData/Local/label-studio/label-studio/label_studio.sqlite3"
OUT_DIR = Path("01_vision_labeling/dataset_v1")
VAL_RATIO = 0.15
SEED = 42

# project_id -> thu muc anh nguon tuong ung
PROJECTS = {
    4: Path("01_vision_labeling/images"),
    8: Path("01_vision_labeling/images2"),
}

CATEGORIES = [
    {"id": 1, "name": "surface_finish"},
    {"id": 2, "name": "gdt_datum"},
]
CAT_NAME_TO_ID = {c["name"]: c["id"] for c in CATEGORIES}


def lay_ten_anh_tu_task_data(data: dict, images_dir: Path) -> Path | None:
    """Task du upload file hoac Local Storage deu tra ve 1 duong dan trong data - can quy ve
    dung file that trong images_dir (upload doi ten thanh uuid-<ten_goc>, Local Storage giu
    nguyen ten qua query string ?d=...)."""
    raw = list(data.values())[0]
    if "local-files" in raw:
        decoded = urllib.parse.unquote(raw.split("d=")[-1])
        fname = decoded.replace("\\", "/").split("/")[-1]
        p = images_dir / fname
        return p if p.exists() else None
    # upload: /data/upload/<project>/<uuid>-<ten_goc_da_sanitize>.png
    fname = raw.split("/")[-1]
    if len(fname) > 9 and fname[8] == "-":
        fname_sanitized = fname[9:]
    else:
        fname_sanitized = fname
    # UPLOAD sanitize khoang trang/ky tu dac biet thanh "_" - phai do lai ten that trong thu muc
    norm_target = re.sub(r"[^A-Za-z0-9]+", "_", fname_sanitized).lower()
    for real_file in images_dir.iterdir():
        if re.sub(r"[^A-Za-z0-9]+", "_", real_file.name).lower() == norm_target:
            return real_file
    return None


def main() -> int:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    images: list[dict] = []
    annotations: list[dict] = []
    img_id = 1
    ann_id = 1
    khong_tim_thay = []
    anh_co_gdt: list[int] = []

    for project_id, images_dir in PROJECTS.items():
        cur.execute(
            """SELECT t.id as task_id, t.data as data, tc.result as result
               FROM task t JOIN task_completion tc ON tc.task_id = t.id
               WHERE t.project_id = ?""",
            (project_id,),
        )
        rows = cur.fetchall()
        for r in rows:
            data = json.loads(r["data"])
            img_path = lay_ten_anh_tu_task_data(data, images_dir)
            if img_path is None:
                khong_tim_thay.append((project_id, r["task_id"]))
                continue

            with Image.open(img_path) as im:
                w, h = im.size

            this_img_id = img_id
            img_id += 1
            images.append(
                {
                    "id": this_img_id,
                    "file_name": str(img_path.resolve()),
                    "width": w,
                    "height": h,
                }
            )

            result = json.loads(r["result"])
            has_gdt = False
            for item in result:
                val = item.get("value", {})
                labels = val.get("rectanglelabels", [])
                if not labels or labels[0] not in CAT_NAME_TO_ID:
                    continue
                x = val["x"] / 100.0 * w
                y = val["y"] / 100.0 * h
                bw = val["width"] / 100.0 * w
                bh = val["height"] / 100.0 * h
                annotations.append(
                    {
                        "id": ann_id,
                        "image_id": this_img_id,
                        "category_id": CAT_NAME_TO_ID[labels[0]],
                        "bbox": [round(x, 2), round(y, 2), round(bw, 2), round(bh, 2)],
                        "area": round(bw * bh, 2),
                        "iscrowd": 0,
                    }
                )
                ann_id += 1
                if labels[0] == "gdt_datum":
                    has_gdt = True
            if has_gdt:
                anh_co_gdt.append(this_img_id)

    print(f"Tong anh xuat duoc: {len(images)}, tong box: {len(annotations)}")
    if khong_tim_thay:
        print(f"CANH BAO: {len(khong_tim_thay)} task khong tim thay file anh: {khong_tim_thay[:10]}")

    # ---------- Chia train/val ----------
    random.seed(SEED)
    all_ids = [im["id"] for im in images]
    gdt_set = set(anh_co_gdt)
    non_gdt_ids = [i for i in all_ids if i not in gdt_set]
    gdt_ids = list(gdt_set)
    random.shuffle(non_gdt_ids)
    random.shuffle(gdt_ids)

    def chia(ids: list[int]) -> tuple[set[int], set[int]]:
        n_val = max(1, round(len(ids) * VAL_RATIO)) if ids else 0
        return set(ids[n_val:]), set(ids[:n_val])

    train_gdt, val_gdt = chia(gdt_ids)
    train_non, val_non = chia(non_gdt_ids)
    train_ids = train_gdt | train_non
    val_ids = val_gdt | val_non

    print(f"Anh co gdt_datum: {len(gdt_ids)} (train {len(train_gdt)} / val {len(val_gdt)})")
    print(f"Train: {len(train_ids)} anh, Val: {len(val_ids)} anh")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for split_name, split_ids in (("train", train_ids), ("val", val_ids)):
        split_images = [im for im in images if im["id"] in split_ids]
        split_anns = [a for a in annotations if a["image_id"] in split_ids]
        coco = {"images": split_images, "annotations": split_anns, "categories": CATEGORIES}
        out_path = OUT_DIR / f"{split_name}.json"
        out_path.write_text(json.dumps(coco, ensure_ascii=False, indent=2), encoding="utf-8")
        n_gdt_box = sum(1 for a in split_anns if a["category_id"] == 2)
        n_sf_box = sum(1 for a in split_anns if a["category_id"] == 1)
        print(f"  {split_name}.json: {len(split_images)} anh, {n_sf_box} surface_finish, {n_gdt_box} gdt_datum")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
