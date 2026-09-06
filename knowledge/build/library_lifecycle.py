"""Safe catalogue lifecycle helpers for the Religious Electronic Library.

Catalogue availability is intentionally separate from AI evidence eligibility.
New records are pending by default; only an explicit human approval transition
can make a record eligible for approved-only evidence builds.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATES = frozenset({"pending", "reviewed", "approved", "blocked", "rejected"})


@dataclass(frozen=True)
class LibraryRecord:
    source_id: str
    title: str
    review_status: str = "pending"
    provenance_status: str = "unverified"
    ai_evidence_eligible: bool = False

    def __post_init__(self) -> None:
        if self.review_status not in STATES:
            raise ValueError(f"unknown review status: {self.review_status}")
        eligible = self.review_status == "approved"
        if self.ai_evidence_eligible != eligible:
            raise ValueError("AI eligibility must match explicit approved status")


def normalize_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize catalogue metadata without inventing unknown fields."""
    record = dict(raw)
    record.setdefault("review_status", "pending")
    record.setdefault("provenance_status", "unverified")
    record.setdefault("ai_evidence_eligible", False)
    if record["review_status"] != "approved":
        record["ai_evidence_eligible"] = False
    LibraryRecord(
        source_id=str(record.get("source_id") or record.get("drive_file_id") or ""),
        title=str(record.get("title") or ""),
        review_status=record["review_status"],
        provenance_status=str(record["provenance_status"]),
        ai_evidence_eligible=bool(record["ai_evidence_eligible"]),
    )
    return record


def production_eligible(record: dict[str, Any]) -> bool:
    """Return true only for explicitly approved records."""
    return (
        record.get("review_status") == "approved"
        and record.get("ai_evidence_eligible") is True
    )
