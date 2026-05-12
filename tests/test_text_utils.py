from src.scoring.text_utils import contains


def test_contains_is_case_insensitive_for_tokens() -> None:
    assert contains('Needs VENTILATOR support overnight', 'ventilator')
