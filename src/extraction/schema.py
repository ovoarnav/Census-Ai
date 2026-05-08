from typing import Optional, Dict, List
from pydantic import BaseModel, Field


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
    evidence: Dict[str, str] = Field(default_factory=dict)

    def short_summary(self) -> str:
        return (
            f"{self.referral_id}: {self.patient_initials}, age {self.age}, "
            f"{self.primary_diagnosis}, payer={self.payer}, auth={self.authorization_status}"
        )
