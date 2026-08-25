#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""So sanh toan bo checkpoint da luu tren tap val, chon ban tot nhat khach quan (Phase 4, 4.3)."""

from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("HF_HOME", r"G:\ThuvienAI\huggingface")

import torch
from PIL import Image
from transformers import RTDetrForObjectDetection, RTDetrImageProcessor

DATASET_DIR = Path("01_vision_labeling/dataset_v1")
MODELS_DIR = Path("models/rtdetr_symbols_v1")
THRESHOLDS = [0.03, 0.05, 0.08, 0.1, 0.15, 0.2]
IOU_MATCH_THRESHOLD = 0.5
ID2LABEL = {0: "surface_finish", 1: "gdt_datum"}


def box_iou(a, b) -> float:
    xa0, ya0, xa1, ya1 = a
    xb0, yb0, xb1, yb1 = b
    ix0, iy0 = max(xa0, xb0), max(ya0, yb0)
    ix1, iy1 = min(xa1, xb1), min(ya1, yb1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    area_a = max(0.0, xa1 - xa0) * max(0.0, ya1 - ya0)
    area_b = max(0.0, xb1 - xb0) * max(0.0, yb1 - yb0)
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def load_val():
    coco = json.loads((DATASET_DIR / "val.json").read_text(encoding="utf-8"))
    images = {im["id"]: im for im in coco["images"]}
    anns_by_image = {i: [] for i in images}
    for a in coco["annotations"]:
        anns_by_image[a["image_id"]].append(a)
    return images, anns_by_image


@torch.no_grad()
def eval_checkpoint(ckpt_dir: Path, images, anns_by_image, device):
    processor = RTDetrImageProcessor.from_pretrained(ckpt_dir)
    model = RTDetrForObjectDetection.from_pretrained(ckpt_dir).to(device)
    model.eval()

    all_preds, all_gts = [], []
    for img_id, im_info in images.items():
        image = Image.open(im_info["file_name"]).convert("RGB")
        w, h = image.size
        enc = processor(images=[image], return_tensors="pt").to(device)
        out = model(**enc)
        results = processor.post_process_object_detection(out, target_sizes=torch.tensor([[h, w]]), threshold=0.01)[0]
        for box, label, score in zip(results["boxes"].tolist(), results["labels"].tolist(), results["scores"].tolist()):
            all_preds.append((img_id, box, label, score))
        for a in anns_by_image[img_id]:
            x, y, bw, bh = a["bbox"]
            all_gts.append((img_id, [x, y, x + bw, y + bh], a["category_id"] - 1))

    best = {"f1": -1}
    per_threshold = {}
    for thr in THRESHOLDS:
        stats = {c: {"tp": 0, "fp": 0, "fn": 0} for c in ID2LABEL}
        preds_thr = [p for p in all_preds if p[3] >= thr]
        for img_id in images:
            for c in ID2LABEL:
                gts_c = [(j, g) for j, g in enumerate(all_gts) if g[0] == img_id and g[2] == c]
                preds_c = [p for p in preds_thr if p[0] == img_id and p[2] == c]
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
        row = {}
        f1_avg = []
        for c, name in ID2LABEL.items():
            tp, fp, fn = stats[c]["tp"], stats[c]["fp"], stats[c]["fn"]
            precision = tp / (tp + fp) if (tp + fp) else 0.0
            recall = tp / (tp + fn) if (tp + fn) else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
            row[name] = {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}
            f1_avg.append(f1)
        avg_f1 = sum(f1_avg) / len(f1_avg)
        row["avg_f1"] = round(avg_f1, 3)
        per_threshold[thr] = row
        if avg_f1 > best["f1"]:
            best = {"f1": avg_f1, "threshold": thr, "row": row}

    del model
    torch.cuda.empty_cache()
    return per_threshold, best


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    images, anns_by_image = load_val()

    checkpoints = sorted(
        [p for p in MODELS_DIR.iterdir() if p.is_dir() and (p / "config.json").exists()],
        key=lambda p: p.name,
    )
    print(f"So checkpoint se danh gia: {len(checkpoints)}")

    summary = []
    for ckpt in checkpoints:
        print(f"\n--- Dang danh gia: {ckpt.name} ---")
        try:
            per_threshold, best = eval_checkpoint(ckpt, images, anns_by_image, device)
        except Exception as e:
            print(f"  LOI: {e}")
            continue
        print(f"  Threshold tot nhat (theo avg F1): {best['threshold']} -> avg_f1={best['f1']:.3f}")
        print(f"  {best['row']}")
        summary.append({"checkpoint": ckpt.name, "best_threshold": best["threshold"], "best_avg_f1": best["f1"], "detail": best["row"]})

    summary.sort(key=lambda x: x["best_avg_f1"], reverse=True)
    print("\n\n=== XEP HANG TOAN BO CHECKPOINT (theo avg F1 tot nhat) ===")
    for s in summary:
        print(f"{s['checkpoint']:<35} best_thr={s['best_threshold']:<6} avg_f1={s['best_avg_f1']:.3f}  {s['detail']}")

    out_path = MODELS_DIR / "checkpoint_comparison.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDa luu: {out_path}")


if __name__ == "__main__":
    main()
