# FoodSugar AI CGM Enriched Forecasting 진행 결과

- 작성일: 2026-05-20
- 기준 계획: `/Users/sangrok/Downloads/FOODSUGAR_GLUCOSE_NEXT_STEPS_2026-05-20.md`
- 프로젝트: `/Users/sangrok/foodsugar-ai`
- 작업 범위: 혈당/CGM 기능만 확장
- 기존 K-Food 음식분류 모델/ensemble/checkpoint/classifier 학습 코드는 수정하지 않음

## 1. 완료 요약

이번 단계에서 CGM history-only baseline을 meal/insulin/exercise/sleep/wearable enriched 모델로 확장했다.

완료한 항목:

1. OhioT1DM XML parser 확장
2. meal / bolus / basal / exercise / sleep / hypo / wearable event parsing
3. leakage-safe enriched CGM CSV 생성
4. persistence / history-only / enriched 모델 비교
5. 30분 / 60분 / 90분 예측 모델 재학습
6. patient별 성능 리포트 생성
7. low/normal/high 혈당 구간별 평가 생성
8. `/predict/cgm-forecast` lazy model cache 적용
9. 테스트 추가 및 전체 테스트 통과
10. 모든 혈당 관련 결과에 참고용 문구 유지

## 2. 수정/추가된 주요 파일

### Glucose 코드

```text
src/glucose/ohiot1dm.py
src/glucose/forecasting.py
```

### 스크립트

```text
scripts/prepare_ohiot1dm_cgm.py
scripts/train_glucose_forecaster.py
```

### API

```text
api/routers/predict.py
```

변경 내용:

- `/predict/cgm-forecast`가 model directory를 매 요청마다 로드하지 않고 lazy singleton cache를 사용한다.
- 모델 파일이 없으면 `503` 반환을 유지한다.

### 테스트

```text
tests/test_api.py
tests/test_glucose_forecasting_eval.py
tests/test_ohiot1dm_enriched_features.py
```

## 3. OhioT1DM Event Parser 확장

기존 parser는 `glucose_level`만 읽었다.

이번에 추가로 아래 section을 안전하게 파싱하도록 확장했다.

```text
meal
bolus
basal
exercise
sleep
hypo_event
basis_gsr
basis_skin_temperature
acceleration
```

특징:

- optional section이 없어도 crash하지 않음
- timestamp를 안전하게 parse
- numeric value를 안전하게 변환
- patient_id, year, split, source_file 보존
- train/test XML을 섞지 않음

## 4. Enriched CGM CSV 생성

실행 명령:

```bash
python3 scripts/prepare_ohiot1dm_cgm.py \
  --input-dir /Users/sangrok/Downloads/OhioT1DM \
  --output-dir data/processed/ohiot1dm \
  --enriched
```

생성 산출물:

```text
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
data/processed/ohiot1dm/cgm_train_enriched.csv
data/processed/ohiot1dm/cgm_test_enriched.csv
reports/glucose_forecasting/feature_enrichment_audit.csv
```

row 수:

| Split | Rows |
|---|---:|
| train enriched | `134790` |
| test enriched | `31743` |
| total enriched | `166533` |

기존 CGM row 수와 동일하게 유지됐다.

## 5. Enriched Feature 목록

추가된 주요 feature:

```text
carbs_current
carbs_last_30m
carbs_last_60m
carbs_last_120m
carbs_last_180m

bolus_current
bolus_last_30m
bolus_last_60m
bolus_last_120m
bolus_last_180m

basal_current
basal_mean_60m
basal_mean_120m

exercise_active
exercise_last_60m
exercise_last_120m

sleep_indicator
hypo_event_current

gsr_current
skin_temperature_current
acceleration_current

day_of_week
patient_id_numeric
```

Leakage 방지:

- 모든 event feature는 현재 timestamp `t` 또는 그 이전 event만 사용한다.
- `t+30`, `t+60`, `t+90` glucose는 target으로만 사용한다.
- train XML과 test XML을 분리 유지한다.

## 6. Feature Enrichment Audit

리포트:

`reports/glucose_forecasting/feature_enrichment_audit.csv`

주요 coverage:

| Feature | Nonzero rows | Coverage |
|---|---:|---:|
| `carbs_last_60m` | `23133` | `13.89%` |
| `carbs_last_180m` | `63012` | `37.84%` |
| `bolus_last_60m` | `35745` | `21.46%` |
| `bolus_last_180m` | `88847` | `53.35%` |
| `basal_current` | `165651` | `99.47%` |
| `exercise_last_120m` | `4657` | `2.80%` |
| `sleep_indicator` | `91` | `0.05%` |
| `gsr_current` | `134989` | `81.06%` |
| `skin_temperature_current` | `134989` | `81.06%` |
| `acceleration_current` | `51019` | `30.64%` |

## 7. Enriched 모델 재학습

실행 명령:

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting
```

저장된 모델:

```text
data/processed/glucose_models_enriched/glucose_forecast_30m.joblib
data/processed/glucose_models_enriched/glucose_forecast_60m.joblib
data/processed/glucose_models_enriched/glucose_forecast_90m.joblib
data/processed/glucose_models_enriched/metadata.joblib
```

중요:

- `data/models/`는 건드리지 않았다.
- 기존 음식분류 모델 저장소와 분리했다.

## 8. Baseline vs History vs Enriched 성능 비교

리포트:

`reports/glucose_forecasting/metrics_baseline_vs_enriched.csv`

| Model | Horizon | MAE | RMSE | R2 | MAE vs persistence | MAE vs history |
|---|---:|---:|---:|---:|---:|---:|
| enriched | 30m | `12.923` | `18.342` | `0.9068` | `23.69%` | `4.01%` |
| history | 30m | `13.463` | `19.051` | `0.8995` | `20.50%` | `0.00%` |
| persistence | 30m | `16.935` | `23.385` | `0.8486` | `0.00%` | `-25.79%` |
| enriched | 60m | `22.564` | `30.821` | `0.7380` | `20.84%` | `5.78%` |
| history | 60m | `23.948` | `32.570` | `0.7075` | `15.98%` | `0.00%` |
| persistence | 60m | `28.503` | `38.506` | `0.5911` | `0.00%` | `-19.02%` |
| enriched | 90m | `29.585` | `39.652` | `0.5692` | `20.03%` | `4.75%` |
| history | 90m | `31.062` | `41.214` | `0.5345` | `16.03%` | `0.00%` |
| persistence | 90m | `36.993` | `49.254` | `0.3352` | `0.00%` | `-19.10%` |

해석:

- enriched model은 모든 horizon에서 history-only보다 개선됐다.
- MAE 개선폭은 history-only 대비 30분 `4.01%`, 60분 `5.78%`, 90분 `4.75%`.
- persistence 대비로는 약 `20~24%` 개선됐다.

## 9. Patient별 성능 리포트

생성 파일:

```text
reports/glucose_forecasting/per_patient_metrics.csv
reports/glucose_forecasting/per_patient_horizon_metrics.csv
reports/glucose_forecasting/worst_patients.csv
reports/glucose_forecasting/best_patients.csv
```

포함 지표:

- patient_id
- year
- split
- model_type
- horizon_minutes
- sample_count
- MAE
- RMSE
- R2

예시:

- enriched 30분 예측에서 patient `570`은 MAE `10.917`
- enriched 30분 예측에서 patient `540`은 MAE `15.394`

환자별 편차가 있으므로 다음 단계에서는 patient-specific feature/model 검토가 필요하다.

## 10. 혈당 구간별 평가 리포트

생성 파일:

```text
reports/glucose_forecasting/per_glucose_range_metrics.csv
reports/glucose_forecasting/hypoglycemia_case_errors.csv
reports/glucose_forecasting/hyperglycemia_case_errors.csv
```

구간 정의:

```text
low: glucose < 70
normal: 70 <= glucose <= 180
high: glucose > 180
```

주요 관찰:

| Model | Horizon | Range | MAE | Mean error | Under pred. | Over pred. |
|---|---:|---|---:|---:|---:|---:|
| enriched | 30m | low | `15.161` | `14.745` | `5.38%` | `94.62%` |
| enriched | 30m | normal | `11.391` | `2.483` | `40.95%` | `59.05%` |
| enriched | 30m | high | `15.475` | `-7.485` | `63.92%` | `36.08%` |
| enriched | 90m | low | `47.239` | `47.239` | `0.00%` | `100.00%` |
| enriched | 90m | high | `38.641` | `-32.366` | `80.66%` | `19.34%` |

해석:

- 저혈당 구간에서는 실제보다 높게 예측하는 경향이 강하다.
- 고혈당 구간에서는 실제보다 낮게 예측하는 경향이 강하다.
- 특히 90분 horizon에서 위험 구간 오차가 크다.
- 운영용으로 쓰려면 low/high 구간 보정 또는 별도 safety calibration이 필요하다.

## 11. API Model Loading Cache

수정 파일:

```text
src/glucose/forecasting.py
api/routers/predict.py
```

추가 기능:

- `load_forecast_models_cached(model_dir)`
- `clear_forecast_model_cache()`
- `forecast_model_cache_load_count(model_dir)`

동작:

```text
첫 요청: model_dir에서 joblib 모델 로드 후 cache 저장
두 번째 요청부터: 메모리 cache 재사용
모델 디렉터리 없음: 503 반환
```

테스트로 확인한 것:

- 모델 파일이 있으면 정상 예측
- 모델 파일이 없으면 503
- 같은 프로세스에서 두 번째 요청부터 모델 재로드하지 않음

## 12. 추가/수정 테스트

추가/수정 파일:

```text
tests/test_api.py
tests/test_glucose_forecasting_eval.py
tests/test_ohiot1dm_enriched_features.py
```

검증 항목:

- enriched CSV 생성 확인
- meal/bolus/basal/exercise/sleep feature column 확인
- train/test split 보존 확인
- target이 feature column으로 들어가지 않는지 확인
- patient-level report 생성 확인
- glucose-range report 생성 확인
- baseline/history/enriched 비교 리포트 생성 확인
- API response reference_notice 확인
- model loading cache 동작 확인
- missing model directory 503 확인

전체 테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
35 passed in 3.42s
```

## 13. 현재 남은 리스크

### 13.1 Low/high glucose 구간 bias

현재 enriched model은 전체 MAE는 개선했지만, 위험 구간에서 bias가 있다.

- low glucose: 높게 예측하는 경향
- high glucose: 낮게 예측하는 경향

다음 단계에서 보정 필요:

- range-aware calibration
- low/high weighted loss 대체 모델
- threshold event classification 보조 head

### 13.2 Exercise/sleep coverage 낮음

exercise/sleep event coverage가 낮다.

- exercise_active coverage 약 `0.02%`
- sleep_indicator coverage 약 `0.05%`

따라서 현재 개선 효과는 대부분 meal/bolus/basal/wearable에서 나온 것으로 보는 것이 맞다.

### 13.3 API enriched model 사용 조건

enriched 모델은 meal/bolus/basal 등 event feature를 요구한다.

현재 `/predict/cgm-forecast`는 recent CGM readings만 받는 구조라, 기본 API는 history model 또는 CGM-only feature 기준으로 쓰는 것이 안전하다.

enriched API를 운영하려면 request schema에 아래 입력을 추가해야 한다.

- recent meal carbs
- recent bolus
- basal profile
- exercise/sleep indicator

## 14. 다음 단계 제안

우선순위:

1. 위험 구간 low/high calibration 추가
2. patient별 worst case 분석
3. `/predict/cgm-forecast-enriched` 또는 schema 확장으로 meal/insulin 입력 지원
4. patient-specific model 또는 patient embedding 개선
5. range별 weighted model 실험
6. 의료 안전 문구/UX 고도화

## 15. 완료 판정

요청 파일의 완료 기준 대응:

| 완료 기준 | 상태 |
|---|---|
| `cgm_timeseries_enriched.csv` 생성 | 완료 |
| meal/bolus/basal/exercise/sleep feature 생성 | 완료 |
| enriched model 학습 완료 | 완료 |
| baseline vs enriched 성능 비교 완료 | 완료 |
| patient별 성능 리포트 생성 | 완료 |
| low/normal/high 구간별 성능 리포트 생성 | 완료 |
| `/predict/cgm-forecast` 모델 로딩 cache 적용 | 완료 |
| 모든 테스트 통과 | 완료 |
| 기존 음식분류 모델 영향 없음 | 완료 |
| 모든 혈당 관련 응답에 reference_notice 포함 | 완료 |
