from api.routers.predict import _risk_messages_from_flags
from src.glucose.constants import (
    GLUCOSE_REFERENCE_NOTICE,
    GLUCOSE_RISK_INTERPRETATION,
    GLUCOSE_SAFETY_WARNING,
)
from src.glucose.forecasting import intervals_from_predictions


def test_core_glucose_wording_is_reference_only():
    combined = " ".join([
        GLUCOSE_REFERENCE_NOTICE,
        GLUCOSE_RISK_INTERPRETATION,
        GLUCOSE_SAFETY_WARNING,
    ])

    assert "참고용" in combined
    assert "가능성 신호" in combined
    assert "의료 진단" in combined
    assert "인슐린을 조절" not in combined
    assert "약을 조절" not in combined
    assert "저혈당입니다" not in combined
    assert "고혈당입니다" not in combined


def test_risk_messages_use_possibility_signal_wording():
    messages = _risk_messages_from_flags({
        60: {"hypo_risk": True, "hyper_risk": False},
        90: {"hypo_risk": False, "hyper_risk": True},
    })
    text = " ".join(message for values in messages.values() for message in values)

    assert "가능성 신호" in text
    assert "실제 혈당 측정값" in text
    assert "저혈당입니다" not in text
    assert "고혈당입니다" not in text
    assert "치료" not in text


def test_90m_interval_message_contains_uncertainty_warning():
    _, levels, messages = intervals_from_predictions(
        {90: 170.0},
        {90: {"p90_abs_error": 70.0}},
    )

    assert levels[90] == "high"
    assert "90분" in messages[90]
    assert "불확실성" in messages[90]
    assert "참고용" in messages[90]

