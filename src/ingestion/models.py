from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    source_doc_id: str
    document_type: Optional[str] = None
    source_name: Optional[str] = None
    captured_at: Optional[str] = None
    text: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EvidenceSpan(BaseModel):
    field_name: Optional[str] = None
    source_doc_id: Optional[str] = None
    quote: str
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    quote_verified: bool = False


class MismatchFinding(BaseModel):
    mismatch_type: str
    severity: Literal["low", "medium", "high", "critical"]
    field: Optional[str] = None
    message: str
    why_it_matters: str
    recommended_action: str
    facility_rule_triggered: Optional[str] = None
    evidence: Optional[EvidenceSpan] = None


class ReferralDocumentBundle(BaseModel):
    referral_id: str
    source: Optional[str] = None
    channel: Optional[str] = None
    received_at: Optional[str] = None
    target_facility_id: Optional[str] = None
    source_documents: List[SourceDocument] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
