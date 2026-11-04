#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
continue_train_v2_rebalanced.py — Train tiep voi trong so loss can bang lai (Phase 4, muc 4.3)

Chan doan tu 2 lan train truoc (xem models/rtdetr_symbols_v1/train_log*.csv): dinh vi box da RAT
TOT (IoU 0.94-0.99 voi ground truth ngay ca luc confidence con thap), nhung confidence phan loai
lai GIAM DAN qua cac checkpoint (epoch50->100->150: 0.10->0.065->0.058) thay vi tang. Nguyen nhan:
RTDetrConfig mac dinh weight_loss_bbox=5.0 + weight_loss_giou=2.0 (dinh vi) >> weight_loss_vfl=1.0
(phan loai) - hop ly cho COCO 80 lop du lieu lon, nhung voi bai toan 2 lop + dinh vi da gan nhu
hoan hao, ty le nay khien loss tong giam chu yeu nho dinh vi, "bo doi" tin hieu hoc cho phan loai.

Sua: tang weight_loss_vfl len 8.0 (ngang trong so dinh vi), train tiep tu checkpoint tot nhat da co
(continue-epoch150, dinh vi da tot san).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

os.environ.setdefault("HF_HOME", r"D:\Claude\Library\huggingface")

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

RESUME_FROM = "models/rtdetr_symbols_v1/checkpoint-continue-epoch150"
DATASET_DIR = Path("01_vision_labeling/dataset_v1")
OUT_DIR = Path("models/rtdetr_symbols_v1")
NUM_EXTRA_EPOCHS = 150
BATCH_SIZE = 4
LR = 1e-4
NEW_WEIGHT_LOSS_VFL = 8.0
THRESHOLDS_EVAL = [0.05, 0.1, 0.2, 0.3, 0.5]
IOU_MATCH_THRESHOLD = 0.5

ID2LABEL = {0: "surface_finish", 1: "gdt_datum"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}


class CocoSymbolDataset(Dataset):
    def __init__(self, coco_path):
        coco = json.loads(Path(coco_path).read_text(encoding="utf-8"))
        self.images = {im["id"]: im for im in coco["images"]}
        self.image_ids = list(self.images.keys())
        self.anns_by_image: dict[int, list[dict]] = {i: [] for i in self.image_ids}
        for a in coco["annotations"]:
            self.anns_by_image[a["image_id"]].append(a)

    def __len__(self) -> int:
        return len(self.image_ids)

    def __getitem__(self, idx: int):
        img_id = self.image_ids[idx]
        im_info = self.images[img_id]
        image = Image.open(im_info["file_name"]).convert("RGB")
        anns = [
            {
                "bbox": a["bbox"],
                "category_id": a["category_id"] - 1,
                "area": a["area"],
                "iscrowd": a["iscrowd"],
            }
            for a in self.anns_by_image[img_id]
        ]
        return image, {"image_id": img_id, "annotations": anns}


def make_collate_fn(processor: RTDetrImageProcessor):
    def collate(batch):
        images = [b[0] for b in batch]
        targets = [b[1] for b in batch]
        enc = processor(images=images, annotations=targets, return_tensors="pt")
        return enc["pixel_values"], enc["labels"]

    return collate


def box_iou(box_a, box_b) -> float:
    xa0, ya0, xa1, ya1 = box_a
    xb0, yb0, xb1, yb1 = box_b
    ix0, iy0 = max(xa0, xb0), max(ya0, yb0)
    ix1, iy1 = min(xa1, xb1), min(ya1, yb1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    area_a = max(0.0, xa1 - xa0) * max(0.0, ya1 - ya0)
    area_b = max(0.0, xb1 - xb0) * max(0.0, yb1 - yb0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


@torch.no_grad()
def evaluate_multi_threshold(model, processor, val_dataset: CocoSymbolDataset, device) -> dict:
    model.eval()
    all_preds = []
    all_gts = []

    for idx in range(len(val_dataset)):
        image, target = val_dataset[idx]
        w, h = image.size
        enc = processor(images=[image], return_tensors="pt").to(device)
        outputs = model(**enc)
        results = processor.post_process_object_detection(
            outputs, target_sizes=torch.tensor([[h, w]]), threshold=0.01
        )[0]
        for box, label, score in zip(results["boxes"].tolist(), results["labels"].tolist(), results["scores"].tolist()):
            all_preds.append((idx, box, label, score))
        for a in target["annotations"]:
            x, y, bw, bh = a["bbox"]
            all_gts.append((idx, [x, y, x + bw, y + bh], a["category_id"]))

    report = {}
    for thr in THRESHOLDS_EVAL:
        stats = {c: {"tp": 0, "fp": 0, "fn": 0} for c in ID2LABEL}
        preds_thr = [p for p in all_preds if p[3] >= thr]
        for img_idx in {g[0] for g in all_gts} | {p[0] for p in preds_thr}:
            gts_i = [(j, g) for j, g in enumerate(all_gts) if g[0] == img_idx]
            preds_i = [p for p in preds_thr if p[0] == img_idx]
            for c in ID2LABEL:
                gts_c = [(j, g) for j, g in gts_i if g[2] == c]
                preds_c = [p for p in preds_i if p[2] == c]
                used = set()
                for p in preds_c:
                    best_iou, best_j = 0.0, -1
                    for j, g in gts_c:
                        if j in used:
                            continue
                        iou = box_iou(p[1], g[1])
                        if iou > best_iou:
                            best_iou, best_j = iou, j
                    if best_iou >= IOU_MATCH_THRESHOLD:
                        stats[c]["tp"] += 1
                        used.add(best_j)
                    else:
                        stats[c]["fp"] += 1
                stats[c]["fn"] += len(gts_c) - len(used)
        report[thr] = {}
        for c, name in ID2LABEL.items():
            tp, fp, fn = stats[c]["tp"], stats[c]["fp"], stats[c]["fn"]
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            report[thr][name] = {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 3), "recall": round(recall, 3)}

    max_conf_by_class = {c: 0.0 for c in ID2LABEL}
    for p in all_preds:
        max_conf_by_class[p[2]] = max(max_conf_by_class[p[2]], p[3])
    report["_max_confidence_seen"] = {ID2LABEL[c]: round(v, 4) for c, v in max_conf_by_class.items()}
    return report


def main() -> int:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dung thiet bi: {device}")
    print(f"Nap lai trong so tu: {RESUME_FROM}")

    processor = RTDetrImageProcessor.from_pretrained(RESUME_FROM)
    model = RTDetrForObjectDetection.from_pretrained(RESUME_FROM).to(device)

    print(f"weight_loss_vfl TRUOC khi sua: {model.config.weight_loss_vfl}")
    model.config.weight_loss_vfl = NEW_WEIGHT_LOSS_VFL
    print(f"weight_loss_vfl SAU khi sua: {model.config.weight_loss_vfl}")

    train_ds = CocoSymbolDataset(DATASET_DIR / "train.json")
    val_ds = CocoSymbolDataset(DATASET_DIR / "val.json")
    print(f"Train: {len(train_ds)} anh, Val: {len(val_ds)} anh")

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, collate_fn=make_collate_fn(processor)
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EXTRA_EPOCHS)

    log_path = OUT_DIR / "train_log_v2rebalanced.csv"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("epoch,avg_loss,lr,elapsed_sec\n")

    t0 = time.time()
    for epoch in range(1, NUM_EXTRA_EPOCHS + 1):
        model.train()
        total_loss = 0.0
        n_batch = 0
        for pixel_values, labels in train_loader:
            pixel_values = pixel_values.to(device)
            labels = [{k: v.to(device) for k, v in t.items()} for t in labels]
            outputs = model(pixel_values=pixel_values, labels=labels)
            loss = outputs.loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=0.1)
            optimizer.step()

            total_loss += loss.item()
            n_batch += 1
        lr_scheduler.step()
        avg_loss = total_loss / max(n_batch, 1)
        elapsed = time.time() - t0
        cur_lr = optimizer.param_groups[0]["lr"]
        print(f"[{epoch:03d}/{NUM_EXTRA_EPOCHS}] avg_loss={avg_loss:.4f} lr={cur_lr:.2e} elapsed={elapsed:.0f}s")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{epoch},{avg_loss:.4f},{cur_lr:.6e},{elapsed:.0f}\n")

        if epoch % 25 == 0 or epoch == NUM_EXTRA_EPOCHS:
            ckpt_dir = OUT_DIR / f"checkpoint-v2-epoch{epoch}"
            model.save_pretrained(ckpt_dir)
            processor.save_pretrained(ckpt_dir)
            report = evaluate_multi_threshold(model, processor, val_ds, device)
            print(f"  -> luu {ckpt_dir} | max_confidence: {report['_max_confidence_seen']}")
            for thr in THRESHOLDS_EVAL:
                m = report[thr]
                print(
                    f"     nguong={thr}: surface_finish P={m['surface_finish']['precision']} R={m['surface_finish']['recall']} | "
                    f"gdt_datum P={m['gdt_datum']['precision']} R={m['gdt_datum']['recall']}"
                )

    total_elapsed = time.time() - t0
    print(f"\nXONG TRAIN V2 sau {total_elapsed:.0f} giay ({total_elapsed/60:.1f} phut)")

    final_report = evaluate_multi_threshold(model, processor, val_ds, device)
    (OUT_DIR / "eval_report_v3.json").write_text(
        json.dumps(final_report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== KET QUA CUOI CUNG V2 (nhieu nguong) ===")
    print("max_confidence:", final_report["_max_confidence_seen"])
    for thr in THRESHOLDS_EVAL:
        m = final_report[thr]
        print(
            f"nguong={thr}: surface_finish P={m['surface_finish']['precision']} R={m['surface_finish']['recall']} "
            f"(tp={m['surface_finish']['tp']} fp={m['surface_finish']['fp']} fn={m['surface_finish']['fn']}) | "
            f"gdt_datum P={m['gdt_datum']['precision']} R={m['gdt_datum']['recall']} "
            f"(tp={m['gdt_datum']['tp']} fp={m['gdt_datum']['fp']} fn={m['gdt_datum']['fn']})"
        )

    final_dir = OUT_DIR / "final_v2"
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    print(f"\nDa luu model cuoi cung (v2 rebalanced): {final_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
