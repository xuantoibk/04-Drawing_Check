#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
train_symbol_detector.py — Fine-tune RT-DETR tren du lieu da gan nhan (Phase 4, muc 4.3)

Lan train "tham do" dau tien - tap du lieu con nho (~217 anh, xem
tools/export_vision_dataset.py), muc dich kiem tra pipeline chay dung, chua phai model chat
luong san xuat. Checkpoint goc: PekingU/rtdetr_r18vd_coco_o365 (ban nho, hop voi du lieu it).

Dung:
    python tools/train_symbol_detector.py
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

CHECKPOINT = "PekingU/rtdetr_r18vd_coco_o365"
DATASET_DIR = Path("01_vision_labeling/dataset_v1")
OUT_DIR = Path("models/rtdetr_symbols_v1")
NUM_EPOCHS = 100
BATCH_SIZE = 4
LR = 1e-4
CONF_THRESHOLD_EVAL = 0.5
IOU_MATCH_THRESHOLD = 0.5

ID2LABEL = {0: "surface_finish", 1: "gdt_datum"}
LABEL2ID = {v: k for k, v in ID2LABEL.items()}


class CocoSymbolDataset(Dataset):
    def __init__(self, coco_path: Path):
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
                "category_id": a["category_id"] - 1,  # COCO 1-based -> model 0-based
                "area": a["area"],
                "iscrowd": a["iscrowd"],
            }
            for a in self.anns_by_image[img_id]
        ]
        target = {"image_id": img_id, "annotations": anns}
        return image, target


def make_collate_fn(processor: RTDetrImageProcessor):
    def collate(batch):
        images = [b[0] for b in batch]
        targets = [b[1] for b in batch]
        enc = processor(images=images, annotations=targets, return_tensors="pt")
        return enc["pixel_values"], enc["labels"]

    return collate


def box_iou(box_a, box_b) -> float:
    """box = [x0,y0,x1,y1] pixel."""
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
def evaluate(model, processor, val_dataset: CocoSymbolDataset, device) -> dict:
    """Danh gia don gian bang IoU matching (khong dung mAP chinh thuc - du de biet huong)."""
    model.eval()
    stats = {c: {"tp": 0, "fp": 0, "fn": 0} for c in ID2LABEL}

    for idx in range(len(val_dataset)):
        image, target = val_dataset[idx]
        w, h = image.size
        enc = processor(images=[image], return_tensors="pt").to(device)
        outputs = model(**enc)
        results = processor.post_process_object_detection(
            outputs, target_sizes=torch.tensor([[h, w]]), threshold=CONF_THRESHOLD_EVAL
        )[0]

        gt_by_cls: dict[int, list] = {c: [] for c in ID2LABEL}
        for a in target["annotations"]:
            x, y, bw, bh = a["bbox"]
            gt_by_cls[a["category_id"]].append([x, y, x + bw, y + bh])

        pred_by_cls: dict[int, list] = {c: [] for c in ID2LABEL}
        for box, label in zip(results["boxes"].tolist(), results["labels"].tolist()):
            if label in pred_by_cls:
                pred_by_cls[label].append(box)

        for c in ID2LABEL:
            gts = gt_by_cls[c]
            preds = pred_by_cls[c]
            matched_gt = set()
            for p in preds:
                best_iou, best_j = 0.0, -1
                for j, g in enumerate(gts):
                    if j in matched_gt:
                        continue
                    iou = box_iou(p, g)
                    if iou > best_iou:
                        best_iou, best_j = iou, j
                if best_iou >= IOU_MATCH_THRESHOLD:
                    stats[c]["tp"] += 1
                    matched_gt.add(best_j)
                else:
                    stats[c]["fp"] += 1
            stats[c]["fn"] += len(gts) - len(matched_gt)

    report = {}
    for c, name in ID2LABEL.items():
        tp, fp, fn = stats[c]["tp"], stats[c]["fp"], stats[c]["fn"]
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        report[name] = {"tp": tp, "fp": fp, "fn": fn, "precision": round(precision, 3), "recall": round(recall, 3)}
    return report


def main() -> int:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Dung thiet bi: {device}")

    processor = RTDetrImageProcessor.from_pretrained(CHECKPOINT)
    model = RTDetrForObjectDetection.from_pretrained(
        CHECKPOINT,
        num_labels=2,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        ignore_mismatched_sizes=True,
    ).to(device)

    train_ds = CocoSymbolDataset(DATASET_DIR / "train.json")
    val_ds = CocoSymbolDataset(DATASET_DIR / "val.json")
    print(f"Train: {len(train_ds)} anh, Val: {len(val_ds)} anh")

    # num_workers=0: DataLoader nhieu tien trinh tren Windows dung "spawn", khong pickle duoc
    # closure cua collate_fn - du lieu chi 184 anh nen chay 1 tien trinh van du nhanh.
    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=0, collate_fn=make_collate_fn(processor)
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=1e-4)
    lr_scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=NUM_EPOCHS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUT_DIR / "train_log.csv"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write("epoch,avg_loss,lr,elapsed_sec\n")

    t0 = time.time()
    for epoch in range(1, NUM_EPOCHS + 1):
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
        print(f"[{epoch:03d}/{NUM_EPOCHS}] avg_loss={avg_loss:.4f} lr={cur_lr:.2e} elapsed={elapsed:.0f}s")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{epoch},{avg_loss:.4f},{cur_lr:.6e},{elapsed:.0f}\n")

        if epoch % 20 == 0 or epoch == NUM_EPOCHS:
            ckpt_dir = OUT_DIR / f"checkpoint-epoch{epoch}"
            model.save_pretrained(ckpt_dir)
            processor.save_pretrained(ckpt_dir)
            print(f"  -> da luu checkpoint: {ckpt_dir}")

    total_elapsed = time.time() - t0
    print(f"\nXONG TRAIN sau {total_elapsed:.0f} giay ({total_elapsed/60:.1f} phut)")

    print("\nDanh gia tren tap val (IoU matching >= 0.5, threshold conf >= 0.5)...")
    report = evaluate(model, processor, val_ds, device)
    report_path = OUT_DIR / "eval_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for name, m in report.items():
        print(f"  {name}: precision={m['precision']} recall={m['recall']} (tp={m['tp']} fp={m['fp']} fn={m['fn']})")

    final_dir = OUT_DIR / "final"
    model.save_pretrained(final_dir)
    processor.save_pretrained(final_dir)
    print(f"\nDa luu model cuoi cung: {final_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
