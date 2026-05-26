# FoodSugar AI Glucose Final Validation Result - 2026-05-21

## Scope

이번 단계는 혈당 모델의 추가 성능 개선이 아니라, 생성된 산출물의 신뢰성 검증, leakage 점검, API safety UX 안정화, 발표/보고서용 evidence 정리를 목표로 진행했다.

기존 K-Food 음식분류 모델, production ensemble config, classifier checkpoint, `src/classifier/`, `data/models/`는 수정하지 않았다.

## Implemented

1. Artifact validation script 추가
   - `scripts/validate_glucose_artifacts.py`
   - JSON/CSV 존재 여부, 필수 metric 범위, horizon 30/60/90, selected model/threshold 구조 검증

2. Artifact validation report 생성
   - `reports/glucose_forecasting/artifact_validation_report.json`
   - `reports/glucose_forecasting/artifact_validation_report.md`

3. Leakage audit 생성
   - `reports/glucose_forecasting/leakage_audit.json`
   - `reports/glucose_forecasting/leakage_audit.md`
   - calibration은 train prediction 기반이며 forbidden target-based column은 발견되지 않음
   - threshold/model selection은 현재 학습 스크립트 기준 test split 사용 가능성이 있어 warning으로 기록

4. API safety UX 강화
   - `/predict/cgm-forecast-enriched-events` 응답에 `risk_messages` 추가
   - 저혈당/고혈당 표현을 “가능성 신호”로 제한
   - “확정”, “저혈당입니다”, “인슐린 조절” 같은 진단/치료 표현을 테스트에서 금지

5. Evidence summary 생성
   - `reports/glucose_forecasting/glucose_next_stage_evidence_summary.md`
   - raw vs calibrated MAE
   - selected hypo classifier
   - hyper classifier
   - artifact validation summary
   - leakage audit summary
   - API safety checklist
   - remaining limitations

6. 테스트 추가
   - `tests/test_glucose_artifact_validation.py`
   - `tests/test_glucose_leakage_audit.py`
   - `tests/test_enriched_events_api_safety.py`

## Validation Result

Artifact validation:

```text
status: pass
errors: 0
warnings: 21
```

Warnings는 대부분 권장 audit column 부족, 90m hypo precision 낮음, patient data quality detail 부족에 대한 개선 권고다. 핵심 artifact 존재 여부와 주요 metric schema는 통과했다.

Leakage audit:

```text
status: pass
calibration_leakage_safe: true
threshold_selection_split: test_inferred_from_current_training_script
```

중요: threshold/model selection은 현재 스크립트 구조상 test metric을 보고 선택됐을 가능성이 있어 warning으로 기록했다. 운영 확정 전에는 train 내부 validation split 또는 CV로 threshold/model selection을 다시 분리하는 것이 필요하다.

## Safety UX Result

신규 enriched-events API는 다음 필드를 반환한다.

```text
reference_notice
risk_interpretation
safety_warning
risk_flags
risk_messages
event_probabilities
model_type
```

`risk_messages`는 확정 진단이 아니라 다음처럼 가능성/주의 신호로만 표현한다.

```text
90분 뒤 저혈당 가능성 신호가 감지되었습니다. 실제 혈당 측정값과 증상을 우선 확인하세요.
```

## Verification

```bash
python3 scripts/validate_glucose_artifacts.py \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting

python3 -m py_compile scripts/validate_glucose_artifacts.py api/schemas/models.py api/routers/predict.py tests/test_glucose_artifact_validation.py tests/test_glucose_leakage_audit.py tests/test_enriched_events_api_safety.py

python3 -m pytest tests/ -q
```

Result:

```text
47 passed in 2.77s
```

## Remaining Action

운영 확정 전 가장 중요한 다음 작업은 threshold/model selection leakage 제거다.

추천 순서:

1. train split 내부에서 시간 기반 validation subset 생성
2. hypo classifier family 선택은 validation에서 수행
3. threshold selection도 validation에서 수행
4. 고정된 model family/threshold로 test set 최종 평가만 수행
5. `event_thresholds.json`에 `selection_split=validation`, `evaluation_split=test`를 명시

이 작업을 끝내면 현재 혈당 모델은 “구현됨”을 넘어 “검증 가능하고 발표 가능한 상태”에 더 가까워진다.
