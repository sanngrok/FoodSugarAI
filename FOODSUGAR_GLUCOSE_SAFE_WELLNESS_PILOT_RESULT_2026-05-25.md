# FoodSugar AI Safe Wellness Pilot 진행 결과 - 2026-05-25

## Summary

`FOODSUGAR_GLUCOSE_SAFE_WELLNESS_PILOT_NEXT_DIRECTION_2026-05-24.md`의 방향에 따라 혈당 기능을 의료 판단 도구가 아니라 **웰니스/식습관 관리 보조 기능**으로 고정하는 작업을 진행했다.

기존 K-Food 음식분류 모델, ensemble weight, classifier checkpoint, `src/classifier/`, `data/models/`는 수정하지 않았다.

## Implemented

### 1. Product Positioning

Created:

- `docs/GLUCOSE_PRODUCT_POSITIONING.md`
- `docs/GLUCOSE_SAFETY_WORDING_GUIDE.md`
- `reports/glucose_forecasting/safety_wording_audit.md`

결과:

- 혈당 기능을 wellness/dietary management support로 명확히 제한
- 진단/치료/인슐린 조절 목적이 아님을 문서화
- 90분 예측은 range/uncertainty 중심으로 표시하도록 고정

### 2. Pilot Study Preparation

Created:

- `docs/PILOT_STUDY_PROTOCOL.md`
- `docs/PILOT_USER_CONSENT_DRAFT.md`
- `docs/PILOT_DATA_SCHEMA.md`
- `reports/pilot/pilot_metric_plan.md`

결과:

- 10-30명, 2-4주 소규모 파일럿 설계
- 수집 데이터, 사용자 동의 항목, 삭제 요청 흐름, 안전 이벤트 기준 정리
- 모델 성능 지표와 UX 오해 지표를 분리

### 3. Data Governance and Privacy

Created:

- `docs/GLUCOSE_DATA_GOVERNANCE.md`
- `docs/GLUCOSE_PRIVACY_SECURITY_CHECKLIST.md`
- `docs/GLUCOSE_LOGGING_POLICY.md`
- `src/glucose/privacy.py`

결과:

- CGM/insulin/meal 관련 데이터를 민감 데이터로 분류
- 저장 기간, 삭제 요청 흐름, ID 분리 원칙 정리
- raw glucose, insulin, timestamp가 로그에 직접 남지 않도록 masking helper 추가

### 4. UX/API Safety Upgrade

Created:

- `docs/GLUCOSE_UX_SPEC.md`
- `docs/GLUCOSE_API_RESPONSE_EXAMPLES.md`
- `reports/glucose_forecasting/ux_safety_review.md`

Updated:

- `src/glucose/constants.py`
- `api/schemas/models.py`

결과:

- 안전 문구를 “식습관 관리 참고용” 중심으로 강화
- 90분 예측은 불확실성 메시지를 요구하는 방향으로 문서화
- CGM timestamp parse validation 추가
- CGM glucose 입력 범위 상한 `<= 600 mg/dL` 추가

### 5. Robustness Reports

Created:

- `reports/glucose_forecasting/robustness_missing_input_report.csv`
- `reports/glucose_forecasting/timestamp_error_robustness_report.csv`
- `reports/glucose_forecasting/low_confidence_food_handling_report.md`

결과:

- missing meal/bolus/basal 입력은 fallback 가능
- CGM readings 부족, invalid timestamp, out-of-range glucose는 reject/주의 대상으로 정리
- low-confidence food classification은 사용자 확인 후 nutrition/risk로 넘어가는 UX 정책으로 정리

### 6. External Validation Planning

Created:

- `docs/EXTERNAL_VALIDATION_PLAN.md`
- `docs/KOREAN_FOOD_CGM_VALIDATION_PLAN.md`
- `reports/glucose_forecasting/external_dataset_candidates.md`

결과:

- OhioT1DM-only 평가의 한계 명시
- 한국 음식 사진 -> 영양성분 -> CGM 반응 연결 검증 설계
- 외부/파일럿 데이터 검증 전에는 일반화 claim을 확장하지 않도록 정리

### 7. Tests

Added:

- `tests/test_glucose_safety_wording.py`
- `tests/test_glucose_uncertainty_response.py`
- `tests/test_glucose_robustness_inputs.py`
- `tests/test_glucose_privacy_logging.py`

검증 기준:

- 안전 문구에 진단/치료 지시 표현이 없는지
- 90분 response에 uncertainty warning이 있는지
- missing meal/bolus/basal fallback이 동작하는지
- invalid timestamp/out-of-range glucose가 막히는지
- 로그 masking helper가 raw health data를 숨기는지

검증 결과:

```text
python3 -m py_compile api/schemas/models.py src/glucose/constants.py src/glucose/privacy.py
pass

python3 -m pytest tests/test_glucose_safety_wording.py tests/test_glucose_uncertainty_response.py tests/test_glucose_robustness_inputs.py tests/test_glucose_privacy_logging.py -q
9 passed

python3 -m pytest tests/ -q
72 passed
```

## Current Product Interpretation

- 30분: 참고용 수치 예측
- 60분: 수치 + 범위 + 가능성 신호
- 90분: 범위 + 높은 불확실성 + 가능성 신호 중심

모든 혈당 관련 결과는 의료 진단이나 치료 지침이 아니다.

## Remaining Work

1. 실제 frontend에서 90분 point estimate를 크게 표시하지 않도록 UI 반영
2. 파일럿 동의서 법무/개인정보 검토
3. 실제 배포 환경의 storage encryption과 access control 확인
4. API latency 측정
5. 외부 CGM 또는 한국 사용자 파일럿 데이터로 재검증
