from src.ingestion.document_bundle_loader import (
    list_available_referral_ids,
    load_referral_document_bundle,
)


def test_list_available_referral_ids_includes_legacy_text_packets() -> None:
    referral_ids = list_available_referral_ids()
    assert referral_ids
    assert all(ref_id.startswith("REF-") for ref_id in referral_ids)


def test_load_referral_document_bundle_wraps_legacy_text_packets() -> None:
    referral_id = list_available_referral_ids()[0]
    bundle = load_referral_document_bundle(referral_id)

    assert bundle.referral_id == referral_id
    assert bundle.source_documents
    assert bundle.source_documents[0].text
