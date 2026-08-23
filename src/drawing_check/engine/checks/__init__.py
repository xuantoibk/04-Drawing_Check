"""Cac custom check khong dien ta duoc bang primitive co san (field_present/field_matches/
field_in_catalog/field_equals_project) - dang ky trong HANDLERS, tra cuu theo params.handler
cua rule check: custom trong file YAML."""

from __future__ import annotations

from typing import Any

from drawing_check.engine.checks.sheet import sheet_khong_hop_le

HANDLERS: dict[str, Any] = {
    "sheet_khong_hop_le": sheet_khong_hop_le,
}
