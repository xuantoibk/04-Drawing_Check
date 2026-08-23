"""Doc cac file rules/*.yaml thanh danh sach Rule (pydantic) - dinh dang theo muc 7.1 tai lieu ke hoach."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel

from drawing_check.core.finding import Severity


class Rule(BaseModel):
    id: str
    name: str
    severity: Severity
    check: str
    params: dict = {}
    message_vi: str
    message_en: Optional[str] = None
    fix_hint: Optional[str] = None
    confidence_gate: Optional[float] = None
    applies_to: Optional[dict] = None
    requires: Optional[str] = None


class RuleSet(BaseModel):
    version: int
    ruleset: str
    applies_to: Optional[dict] = None
    rules: list[Rule]


def doc_1_file_rule(duong_dan: Path) -> RuleSet:
    du_lieu = yaml.safe_load(duong_dan.read_text(encoding="utf-8"))
    return RuleSet.model_validate(du_lieu)


def doc_thu_muc_rule(thu_muc: Path) -> list[Rule]:
    """Doc tat ca file *.yaml trong thu muc, theo dung thu tu ten file (vd 10_..., 20_...)."""
    ket_qua: list[Rule] = []
    for duong_dan in sorted(thu_muc.glob("*.yaml")):
        ket_qua.extend(doc_1_file_rule(duong_dan).rules)
    return ket_qua
