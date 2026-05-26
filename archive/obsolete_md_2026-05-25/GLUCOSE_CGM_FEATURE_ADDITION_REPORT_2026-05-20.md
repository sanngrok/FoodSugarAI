# FoodSugar AI 혈당 기능 추가 작업 보고서

- 작성일: 2026-05-20
- 작업 목표: 기존 FoodSugar AI 프로젝트에 혈당 위험도 점수와 OhioT1DM 기반 CGM 예측 기능 추가
- 중요 원칙: 기존 K-Food 음식분류 모델, ensemble weight, checkpoint, classifier 학습 코드는 수정하지 않음
- 의료 문구 원칙: 모든 혈당 관련 응답/리포트에 참고용 문구 포함

## 1. 지킨 조건

요청 조건별 처리 상태:

| 조건 | 상태 |
|---|---|
| 기존 음식분류 모델은 절대 건드리지 말 것 | 완료 |
| 음식 영양성분으로 혈당 위험도 점수 계산 기능 추가 | 완료 |
| OhioT1DM XML 데이터를 CGM 시계열 데이터로 변환 | 완료 |
| 30분 / 60분 / 90분 뒤 혈당 예측 모델 생성 | 완료 |
| 성능 평가 리포트 자동 생성 | 완료 |
| 의료 진단처럼 말하지 않고 참고용 문구 항상 포함 | 완료 |

수정하지 않은 영역:

- `config/kfood_production_ensemble_config.json`
- `src/classifier/`
- `data/models/`
- 기존 ensemble checkpoint
- 기존 classifier training code

## 2. 추가된 주요 모듈

새 패키지:

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

### `src/glucose/constants.py`

혈당 관련 기능에서 공통으로 사용하는 참고용 문구를 정의했다.

```text
이 결과는 참고용이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리 결정은 의료진과 상의하세요.
```

### `src/glucose/risk.py`

영양성분 기반 혈당 위험도 점수 기능을 추가했다.

입력:

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
- `factors`: 점수 산출에 사용된 주요 feature/component
- `reference_notice`: 참고용 문구

### `src/glucose/ohiot1dm.py`

OhioT1DM XML parser를 추가했다.

처리 대상:

- `glucose_level/event`

출력 컬럼:

- `timestamp`
- `glucose_mg_dl`
- `patient_id`
- `year`
- `split`
- `source_file`
- `weight`
- `insulin_type`

### `src/glucose/forecasting.py`

CGM 예측 feature engineering, 학습, 평가, 저장/로드 기능을 추가했다.

사용 feature:

- 현재 glucose
- lag 1/2/3/6/12
- diff 1/3/6
- rolling mean 3/6/12
- rolling std 6/12
- hour sin/cos

예측 horizon:

- 30분
- 60분
- 90분

모델:

- horizon별 `HistGradientBoostingRegressor`

## 3. 추가된 스크립트

### OhioT1DM XML 변환

새 파일:

`scripts/prepare_ohiot1dm_cgm.py`

실행:

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
| total rows | `166533` |
| train rows | `134790` |
| test rows | `31743` |
| patients | `12` |
| years | `2018`, `2020` |
| glucose min | `40.0` |
| glucose max | `400.0` |

### CGM 예측 모델 학습/평가

새 파일:

`scripts/train_glucose_forecaster.py`

실행:

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries.csv \
  --model-dir data/processed/glucose_models \
  --report-dir reports/glucose_forecasting
```

중요:

- 모델 저장 위치는 `data/processed/glucose_models`
- 요청에서 금지한 `data/models/`는 건드리지 않았다.

생성 모델:

```text
data/processed/glucose_models/
├── glucose_forecast_30m.joblib
├── glucose_forecast_60m.joblib
├── glucose_forecast_90m.joblib
└── metadata.joblib
```

생성 리포트:

```text
reports/glucose_forecasting/
├── README.md
├── metrics.csv
└── summary.json
```

## 4. CGM 예측 평가 결과

평가 split:

- OhioT1DM `test`

학습에 사용된 feature rows:

- train: `126867`
- test: `29677`

성능:

| Horizon | Samples | MAE | RMSE | R2 |
|---:|---:|---:|---:|---:|
| 30m | `29677` | `13.463` | `19.051` | `0.8995` |
| 60m | `29677` | `23.948` | `32.570` | `0.7075` |
| 90m | `29677` | `31.062` | `41.214` | `0.5345` |

리포트 파일:

`reports/glucose_forecasting/README.md`

## 5. API 확장

수정 파일:

- `api/schemas/models.py`
- `api/routers/predict.py`
- `config/settings.py`

### 새 응답/요청 schema

추가된 schema:

- `GlucoseRiskResponse`
- `CGMReading`
- `CGMForecastRequest`
- `CGMForecastResponse`

기존 `RiskResponse`에도 `reference_notice`를 추가했다.

### 새 API: 영양성분 기반 혈당 위험도 점수

Endpoint:

```text
POST /predict/glucose-risk
```

입력:

기존 `NutritionInput`

출력:

- `score`
- `level`
- `factors`
- `reference_notice`

### 새 API: CGM 30/60/90분 예측

Endpoint:

```text
POST /predict/cgm-forecast
```

입력 예시:

```json
{
  "readings": [
    {"timestamp": "2026-01-01 00:00:00", "glucose_mg_dl": 110},
    {"timestamp": "2026-01-01 00:05:00", "glucose_mg_dl": 112}
  ]
}
```

주의:

- 실제 요청에는 최소 13개의 최근 5분 간격 CGM 값이 필요하다.
- 모델 파일이 없으면 `503`을 반환한다.

출력:

- `predictions_mg_dl`
- `horizons_minutes`
- `reference_notice`

## 6. 참고용 문구 처리

모든 혈당 관련 기능에 아래 문구를 포함한다.

```text
이 결과는 참고용이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리 결정은 의료진과 상의하세요.
```

포함 위치:

- `RiskResponse.reference_notice`
- `GlucoseRiskResponse.reference_notice`
- `CGMForecastResponse.reference_notice`
- `reports/glucose_forecasting/README.md`
- `reports/glucose_forecasting/summary.json`

## 7. 테스트 추가

새 파일:

`tests/test_glucose_features.py`

테스트 내용:

- 영양성분 기반 glucose risk score가 0-100 범위인지 확인
- 참고용 문구 포함 확인
- OhioT1DM XML parser가 glucose row를 추출하는지 확인
- recent CGM readings에서 30/60/90 예측 결과를 만드는지 확인

수정 파일:

`tests/test_api.py`

추가 확인:

- `/predict/risk` 응답에 참고용 문구 포함
- `/predict/glucose-risk` endpoint 정상 응답

## 8. 검증 결과

문법 검사:

```bash
python3 -m py_compile \
  src/glucose/constants.py \
  src/glucose/risk.py \
  src/glucose/ohiot1dm.py \
  src/glucose/forecasting.py \
  scripts/prepare_ohiot1dm_cgm.py \
  scripts/train_glucose_forecaster.py \
  api/schemas/models.py \
  api/routers/predict.py \
  config/settings.py \
  tests/test_glucose_features.py \
  tests/test_api.py
```

결과:

`pass`

전체 테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
26 passed in 4.97s
```

## 9. 현재 남은 개선 포인트

### 9.1 CGM 모델은 baseline production candidate

현재 CGM forecasting model은 빠르게 붙일 수 있는 tabular baseline이다.

운영 품질을 높이려면 다음 개선이 가능하다.

- meal carbs feature 추가
- bolus/basal insulin feature 추가
- patient-specific model 또는 patient embedding
- time-based leakage audit 강화
- calibration report 추가
- low/high glucose 구간별 MAE 별도 평가

### 9.2 API model loading 최적화

`/predict/cgm-forecast`는 현재 요청 시 model directory에서 모델을 로드한다.

트래픽이 생기면 startup cache 또는 lazy singleton cache로 바꾸는 것이 좋다.

### 9.3 의료/안전 UX

참고용 문구는 포함했지만, 운영 서비스에서는 다음도 추가하는 것이 좋다.

- 저혈당/고혈당 수치가 나와도 진단적 표현 금지
- 응급 상황 안내 문구는 별도 안전정책으로 설계
- 사용자 데이터 입력 오류 방지
- CGM 단위 mg/dL 명확화

## 10. 요약

이번 작업으로 기존 음식분류 모델을 건드리지 않고 혈당 기능을 추가했다.

추가된 기능:

1. 음식 영양성분 기반 0-100 혈당 위험도 점수
2. OhioT1DM XML -> CGM CSV 변환
3. 30/60/90분 CGM 예측 모델 학습
4. test split 성능 평가 리포트 자동 생성
5. FastAPI endpoint 확장
6. 모든 혈당 관련 응답에 참고용 문구 포함

현재 검증 상태:

- XML 변환 완료
- 모델 학습 완료
- 평가 리포트 생성 완료
- API schema/route 추가 완료
- 테스트 `26 passed`
