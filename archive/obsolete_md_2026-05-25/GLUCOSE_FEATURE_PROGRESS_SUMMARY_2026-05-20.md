# 혈당 기능 추가 진행상황 정리

- 작성일: 2026-05-20
- 프로젝트: `/Users/sangrok/foodsugar-ai`
- 목표: 기존 FoodSugar AI에 혈당 위험도 점수와 CGM 예측 기능 추가
- 상태: 1차 구현, 데이터 변환, 모델 학습, 평가 리포트, API 확장, 테스트 완료

## 1. 핵심 원칙

이번 작업에서는 기존 음식분류 모델을 건드리지 않았다.

수정하지 않은 영역:

- `config/kfood_production_ensemble_config.json`
- `src/classifier/`
- `data/models/`
- 기존 K-Food 7-model ensemble checkpoint
- 기존 classifier training code

추가한 혈당 기능은 모두 별도 모듈/스크립트/API 확장으로 붙였다.

## 2. 추가된 기능 요약

이번에 추가한 기능은 크게 4개다.

1. 음식 영양성분 기반 혈당 위험도 점수 계산
2. OhioT1DM XML -> CGM 시계열 CSV 변환
3. CGM 기반 30분 / 60분 / 90분 혈당 예측 모델 학습
4. FastAPI 혈당 관련 endpoint 추가

모든 혈당 관련 결과에는 아래 참고용 문구를 포함하도록 했다.

```text
이 결과는 참고용이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리 결정은 의료진과 상의하세요.
```

## 3. 새로 추가된 코드 구조

### Glucose package

새 디렉터리:

`src/glucose/`

구성:

```text
src/glucose/
├── __init__.py
├── constants.py
├── risk.py
├── ohiot1dm.py
└── forecasting.py
```

역할:

- `constants.py`
  - 혈당 관련 공통 참고용 문구
- `risk.py`
  - 영양성분 기반 0-100 혈당 위험도 점수 계산
- `ohiot1dm.py`
  - OhioT1DM XML parser
- `forecasting.py`
  - CGM feature engineering, 30/60/90분 모델 학습/평가/예측

## 4. 영양성분 기반 혈당 위험도 점수

구현 파일:

`src/glucose/risk.py`

입력 feature:

- calories
- carbs
- sugar
- protein
- fat
- fiber
- glycemic_index
- portion_g

출력:

- `score`: 0-100
- `level`: `낮음`, `주의`, `높음`
- `factors`: 계산에 사용된 component
- `reference_notice`: 참고용 문구

API:

```text
POST /predict/glucose-risk
```

기존 `/predict/risk` 응답에도 `reference_notice`를 추가했다.

## 5. OhioT1DM XML 변환

입력 데이터:

`/Users/sangrok/Downloads/OhioT1DM`

XML 구조:

- `patient`
- `glucose_level`
- `event ts="..." value="..."`

변환 스크립트:

`scripts/prepare_ohiot1dm_cgm.py`

실행 명령:

```bash
python3 scripts/prepare_ohiot1dm_cgm.py \
  --input-dir /Users/sangrok/Downloads/OhioT1DM \
  --output-dir data/processed/ohiot1dm
```

생성 산출물:

```text
data/processed/ohiot1dm/
├── README.md
├── summary.json
├── cgm_timeseries.csv
├── cgm_train.csv
└── cgm_test.csv
```

변환 결과:

| 항목 | 값 |
|---|---:|
| total CGM rows | `166533` |
| train rows | `134790` |
| test rows | `31743` |
| patients | `12` |
| years | `2018`, `2020` |
| glucose min | `40.0` |
| glucose max | `400.0` |

## 6. CGM 예측 모델

구현 파일:

`src/glucose/forecasting.py`

학습 스크립트:

`scripts/train_glucose_forecaster.py`

실행 명령:

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries.csv \
  --model-dir data/processed/glucose_models \
  --report-dir reports/glucose_forecasting
```

중요:

- 모델은 `data/processed/glucose_models`에 저장했다.
- 요청에서 금지한 `data/models/`는 건드리지 않았다.

생성 모델:

```text
data/processed/glucose_models/
├── glucose_forecast_30m.joblib
├── glucose_forecast_60m.joblib
├── glucose_forecast_90m.joblib
└── metadata.joblib
```

예측 horizon:

- 30분
- 60분
- 90분

모델:

- horizon별 `HistGradientBoostingRegressor`

사용 feature:

- 현재 glucose
- lag 1/2/3/6/12
- diff 1/3/6
- rolling mean 3/6/12
- rolling std 6/12
- hour sin/cos

## 7. CGM 예측 성능

평가 리포트:

`reports/glucose_forecasting/README.md`

요약 파일:

`reports/glucose_forecasting/summary.json`

평가 split:

- OhioT1DM `test`

학습/평가 row:

| 항목 | 값 |
|---|---:|
| train raw rows | `134790` |
| test raw rows | `31743` |
| train feature rows | `126867` |
| test feature rows | `29677` |

성능:

| Horizon | Samples | MAE | RMSE | R2 |
|---:|---:|---:|---:|---:|
| 30m | `29677` | `13.463` | `19.051` | `0.8995` |
| 60m | `29677` | `23.948` | `32.570` | `0.7075` |
| 90m | `29677` | `31.062` | `41.214` | `0.5345` |

해석:

- 30분 예측은 baseline으로 꽤 안정적이다.
- 60분부터 오차가 커진다.
- 90분은 아직 baseline 수준이며, meal/insulin feature 없이 CGM history만 쓰기 때문에 개선 여지가 크다.

## 8. API 확장

수정 파일:

- `api/schemas/models.py`
- `api/routers/predict.py`
- `config/settings.py`

추가 schema:

- `GlucoseRiskResponse`
- `CGMReading`
- `CGMForecastRequest`
- `CGMForecastResponse`

추가 endpoint:

```text
POST /predict/glucose-risk
POST /predict/cgm-forecast
```

### `/predict/glucose-risk`

역할:

- 음식 영양성분과 섭취량을 받아 참고용 혈당 위험도 점수 계산

입력:

- 기존 `NutritionInput`

출력:

- `score`
- `level`
- `factors`
- `reference_notice`

### `/predict/cgm-forecast`

역할:

- 최근 5분 간격 CGM readings를 받아 30/60/90분 뒤 혈당 예측

입력:

- 최소 13개 readings 필요
- 각 reading:
  - `timestamp`
  - `glucose_mg_dl`

출력:

- `predictions_mg_dl`
- `horizons_minutes`
- `reference_notice`

모델 파일이 없으면 `503`을 반환하도록 했다.

## 9. 테스트

새 테스트:

`tests/test_glucose_features.py`

테스트 내용:

- 혈당 위험도 점수 범위 확인
- 참고용 문구 포함 확인
- OhioT1DM XML parser 확인
- CGM forecast helper 확인

수정 테스트:

`tests/test_api.py`

추가 확인:

- `/predict/risk` 응답에 `reference_notice` 포함
- `/predict/glucose-risk` endpoint 정상 응답

전체 테스트 결과:

```text
26 passed in 4.97s
```

## 10. 현재 산출물 목록

### 코드

```text
src/glucose/constants.py
src/glucose/risk.py
src/glucose/ohiot1dm.py
src/glucose/forecasting.py
scripts/prepare_ohiot1dm_cgm.py
scripts/train_glucose_forecaster.py
tests/test_glucose_features.py
```

### 데이터

```text
data/processed/ohiot1dm/cgm_timeseries.csv
data/processed/ohiot1dm/cgm_train.csv
data/processed/ohiot1dm/cgm_test.csv
data/processed/ohiot1dm/summary.json
```

### 모델

```text
data/processed/glucose_models/glucose_forecast_30m.joblib
data/processed/glucose_models/glucose_forecast_60m.joblib
data/processed/glucose_models/glucose_forecast_90m.joblib
data/processed/glucose_models/metadata.joblib
```

### 리포트

```text
reports/glucose_forecasting/README.md
reports/glucose_forecasting/metrics.csv
reports/glucose_forecasting/summary.json
GLUCOSE_CGM_FEATURE_ADDITION_REPORT_2026-05-20.md
```

## 11. 현재 한계와 다음 개선 방향

### 11.1 현재 CGM 모델은 baseline

현재 모델은 CGM history만 사용한다.

아직 사용하지 않은 OhioT1DM 정보:

- meal carbs
- bolus insulin
- basal insulin
- exercise
- sleep
- stressors
- heart rate / activity 계열

다음 개선에서는 meal/insulin feature를 추가하는 것이 가장 중요하다.

### 11.2 patient-specific 개선 필요

현재는 전체 환자 데이터를 합쳐 하나의 global model을 학습한다.

개선 방향:

- patient_id feature 추가
- patient-specific model
- train patient/test patient 분리 검증
- 개인화 fine-tuning

### 11.3 평가 리포트 고도화 필요

현재 리포트는 horizon별 MAE/RMSE/R2 중심이다.

추가하면 좋은 평가:

- 저혈당 구간 MAE
- 고혈당 구간 MAE
- 정상 범위 MAE
- Clarke/Parkes error grid 계열 분석
- time-of-day별 성능
- patient별 성능

### 11.4 API 모델 로딩 최적화

현재 `/predict/cgm-forecast`는 요청 시 model directory에서 모델을 로드한다.

트래픽이 생기면 다음 구조가 좋다.

- startup 시 로드
- lazy singleton cache
- model version 관리

### 11.5 의료 안전 문구

참고용 문구는 붙였지만, 운영 단계에서는 더 정교한 안전 UX가 필요하다.

예:

- 저혈당/고혈당 예측 시 진단적 표현 금지
- 응급 상황 안내 문구는 별도 정책으로 관리
- 사용자가 입력한 CGM 단위 확인
- 의료진 상담 권고 문구 유지

## 12. 다음 단계 제안

우선순위:

1. OhioT1DM meal/bolus/basal feature를 CGM time grid에 merge
2. 30/60/90분 모델 재학습
3. patient별 성능 리포트 추가
4. low/normal/high glucose 구간별 평가 추가
5. `/predict/cgm-forecast` 모델 로딩 cache 적용
6. GPT에게 현재 구조 검증 요청

## 13. GPT에게 물어볼 질문

GPT 검증용 질문:

1. 현재 CGM forecasting baseline 구조에서 가장 먼저 개선해야 할 feature는 무엇인가?
2. OhioT1DM의 meal/bolus/basal 데이터를 5분 CGM grid에 merge할 때 leakage를 피하려면 어떻게 해야 하는가?
3. 30/60/90분 예측을 horizon별 별도 모델로 둔 구조가 적절한가?
4. API에서 CGM forecast 모델을 요청마다 로드하는 구조를 어떻게 개선하는 게 좋은가?
5. 의료 진단처럼 보이지 않게 하기 위해 API 응답/문구에 더 넣어야 할 안전장치가 있는가?
6. 현재 성능 평가 MAE/RMSE/R2 외에 반드시 추가해야 할 혈당 예측 평가지표는 무엇인가?

## 14. 최종 요약

현재까지 혈당 기능 추가는 1차 완료 상태다.

완료된 것:

- 영양성분 기반 혈당 위험도 점수
- OhioT1DM XML -> CGM CSV 변환
- 30/60/90분 CGM forecasting model 학습
- test split 성능 리포트 생성
- FastAPI endpoint 추가
- 참고용 의료 안전 문구 적용
- 테스트 통과

남은 핵심:

- meal/insulin feature 추가
- patient별 평가
- low/high glucose 구간별 평가
- API model loading cache
- 운영 수준 안전 문구/UX 강화
