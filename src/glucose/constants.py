"""Shared text and constants for glucose-related features."""

# OhioT1DM(2018 + 2020) 학습 환자 ID. enriched CGM 모델은 patient_id_numeric을
# feature로 쓰므로, 이 목록에 없는 ID(웹앱 기본값 0 포함)는 "모르는 사용자"로 보고
# 12명 모두의 ID로 예측한 뒤 평균한다.
OHIOT1DM_TRAINING_PATIENT_IDS = (540, 544, 552, 559, 563, 567, 570, 575, 584, 588, 591, 596)

GLUCOSE_REFERENCE_NOTICE = (
    "이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다. "
    "혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요."
)

GLUCOSE_RISK_INTERPRETATION = (
    "예측값과 위험도는 최근 입력 패턴을 바탕으로 한 가능성 신호입니다."
)

GLUCOSE_SAFETY_WARNING = (
    "증상이 있거나 실제 측정값이 우려되면 앱 예측에 의존하지 말고 실제 CGM/혈당 측정값을 확인한 뒤 의료진에게 문의하세요."
)
