from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from src.ingestion.models import EvidenceSpan


class ReferralExtract(BaseModel):
    referral_id: str
    source: Optional[str] = None
    channel: Optional[str] = None
    received_at: Optional[str] = None
    target_facility_id: Optional[str] = None

    patient_initials: Optional[str] = None
    age: Optional[int] = None

    payer: Optional[str] = None
    authorization_status: Optional[str] = None

    primary_diagnosis: Optional[str] = None
    current_course_of_illness: Optional[str] = None

    current_medications_or_mar: Optional[str] = None
    allergies: Optional[str] = None
    mobility_transfer_status: Optional[str] = None
    therapy_need: Optional[str] = None
    wound_skin_needs: Optional[str] = None
    oxygen_respiratory_needs: Optional[str] = None
    dialysis_need: Optional[str] = None
    cognitive_status: Optional[str] = None
    behavioral_safety_concerns: Optional[str] = None
    infection_isolation_status: Optional[str] = None
    advance_directive_code_status: Optional[str] = None
    durable_medical_equipment_needs: Optional[str] = None

    missing_or_unclear_items: List[str] = Field(default_factory=list)

    # Backwards-compatible evidence map used by existing flow.
    evidence: Dict[str, str] = Field(default_factory=dict)

    # Phase 2 grounded extraction fields (optional so old flows remain valid).
    evidence_spans: Dict[str, List[EvidenceSpan]] = Field(default_factory=dict)
    extraction_confidence: Dict[str, float] = Field(default_factory=dict)
    conflicting_fields: List[dict] = Field(default_factory=list)
    source_document_ids: List[str] = Field(default_factory=list)

    def short_summary(self) -> str:
        return (
            f"{self.referral_id}: {self.patient_initials}, age {self.age}, "
            f"{self.primary_diagnosis}, payer={self.payer}, auth={self.authorization_status}"
        )

    def ensure_evidence_spans_from_legacy(self) -> Dict[str, List[EvidenceSpan]]:
        """Populate unverified evidence spans from legacy evidence strings when missing."""
        if self.evidence_spans:
            return self.evidence_spans

        converted: Dict[str, List[EvidenceSpan]] = {}
        for field_name, quote in self.evidence.items():
            if not quote:
                continue
            converted[field_name] = [
                EvidenceSpan(
                    field_name=field_name,
                    source_doc_id=None,
                    quote=quote,
                    char_start=None,
                    char_end=None,
                    quote_verified=False,
                )
            ]

        self.evidence_spans = converted
        return self.evidence_spans

    def get_best_evidence(self, field_name: str) -> Optional[EvidenceSpan]:
        spans = self.evidence_spans.get(field_name, [])
        if not spans:
            spans = self.ensure_evidence_spans_from_legacy().get(field_name, [])
        if not spans:
            return None

        verified = [s for s in spans if s.quote_verified]
        if verified:
            return verified[0]
        return spans[0]

    def has_verified_evidence(self, field_name: str) -> bool:
        spans = self.evidence_spans.get(field_name, [])
        return any(span.quote_verified for span in spans)

    def fields_missing_verified_evidence(self) -> List[str]:
        fields_to_check = set(self.evidence.keys()) | set(self.evidence_spans.keys())
        missing = []
        for field_name in sorted(fields_to_check):
            if not self.has_verified_evidence(field_name):
                missing.append(field_name)
        return missing


def legacy_evidence_to_spans(evidence: Dict[str, str]) -> Dict[str, List[EvidenceSpan]]:
    """Convert legacy evidence map values to unverified EvidenceSpan entries."""
    converted: Dict[str, List[EvidenceSpan]] = {}
    for field_name, quote in evidence.items():
        if not quote:
            continue
        converted[field_name] = [
            EvidenceSpan(
                field_name=field_name,
                source_doc_id=None,
                quote=quote,
                char_start=None,
                char_end=None,
                quote_verified=False,
            )
        ]
    return converted
