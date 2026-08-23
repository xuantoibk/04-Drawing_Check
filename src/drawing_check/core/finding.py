"""Finding - ket qua sinh ra tu rule engine, luon truy duoc ve 1 ma quy tac cu the.

3 muc ket luan (Level) va 3 muc nghiem trong (Severity) la 2 truc doc lap - xem
DATA_DOC/DrawingCheck_KeHoachXayDung.md muc 3.2/3.3. AI/OCR khong bao gio duoc sinh Level FAIL.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel

Level = Literal["FAIL", "WARN", "INFO"]
Severity = Literal["critical", "major", "minor"]


class Finding(BaseModel):
    rule_id: str
    level: Level
    severity: Severity
    message_vi: str
    drawing_no: str
    page_no: int
    field: Optional[str] = None
    fix_hint: Optional[str] = None
    bbox: Optional[tuple[float, float, float, float]] = None
