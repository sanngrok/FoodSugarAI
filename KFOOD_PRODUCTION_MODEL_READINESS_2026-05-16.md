# K-Food 운영모델 확정 준비 상태

- 작성일: 2026-05-16
- 프로젝트: `/Users/sangrok/foodsugar-ai`
- 목표: 현재 92% 달성 모델을 운영모델로 확정할 수 있도록 재현성/검증/로딩 경로 개선
- 현재 후보: `kfood_92_hflip_7model_weighted_2026_05_16`
- 상태: 운영 후보로 고정 가능한 형태까지 정리 완료

## 현재 운영 후보

현재 운영 후보는 7-model weighted ensemble이다.

설정 파일:

`config/kfood_production_ensemble_config.json`

검증 결과:

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| validation split | `data/raw/korean_food_fixed_v1/val` |
| TTA | `hflip` |

## 이번에 개선한 부분

### 1. 운영용 production config 고정

새 파일:

`config/kfood_production_ensemble_config.json`

이 파일에 다음 항목을 고정했다.

- ensemble name
- status
- verified metrics
- TTA 방식
- 7개 모델 checkpoint 경로
- metadata 경로
- classes 경로
- weight
- 운영 확정 전 주의사항

이제 실험 리포트 폴더 안의 config에 의존하지 않고, 앱에서 사용할 production config가 별도로 존재한다.

### 2. Config 기반 ensemble classifier 추가

새 파일:

`src/classifier/ensemble_food_classifier.py`

추가된 클래스:

`EnsembleFoodClassifier`

기능:

- JSON config에서 ensemble 구성 로드
- checkpoint/metadata/classes 파일 존재 확인
- 모델별 class order 일치 확인
- weight normalize
- `none` / `hflip` TTA 지원
- 기존 `FoodClassifier.predict()`와 같은 형태의 `ClassificationResult` 반환

즉, 기존 API 코드가 기대하는 `predict(image)` 인터페이스를 유지하면서 운영 ensemble을 사용할 수 있게 만들었다.

### 3. FastAPI startup에서 production ensemble 우선 로드

수정 파일:

`api/main.py`

추가된 함수:

`load_classifier()`

동작:

1. `settings.classifier_ensemble_config_path`가 존재하면 `EnsembleFoodClassifier`를 로드한다.
2. production config가 없으면 기존 단일 `FoodClassifier`로 fallback한다.
3. torch 미설치 등 ImportError가 나면 기존처럼 classifier를 `None`으로 두고 fallback 경로를 유지한다.
4. macOS torch/MPS ensemble 추론과 XGBoost eager import 충돌을 피하기 위해 `api/main.py`의 시작 시점 `import xgboost`를 제거했다.

### 4. Settings에 production config path 추가

수정 파일:

`config/settings.py`

추가된 설정:

`classifier_ensemble_config_path`

기본값:

`config/kfood_production_ensemble_config.json`

환경변수로 다른 config를 지정할 수 있다.

추가된 설정:

`use_xgboost_predictor_model`

기본값:

`False`

이유:

- 현재 운영 목표는 K-Food classifier 안정화다.
- macOS Python 3.14 환경에서 XGBoost eager import 또는 trained XGBoost model load가 torch/MPS ensemble inference와 충돌할 수 있다.
- API 기본값은 rule-based sugar predictor fallback을 사용한다.
- trained XGBoost predictor가 꼭 필요하면 환경변수로 명시적으로 켠 뒤 별도 smoke test를 수행해야 한다.

### 5. 운영 preflight 검증 스크립트 추가

새 파일:

`scripts/validate_kfood_production_config.py`

검증 항목:

- config JSON 존재 여부
- `models` 목록 존재 여부
- `verified_metrics.top1 >= 0.92`
- `tta`가 운영 지원 범위인지 확인
- checkpoint/metadata/classes 파일 존재 확인
- class count `56` 확인
- 모든 모델의 class order 동일 여부 확인
- weight 합이 양수인지 확인

실행 명령:

```bash
python3 scripts/validate_kfood_production_config.py
```

현재 실행 결과:

- status: `ok`
- num_models: `7`
- num_classes: `56`
- weight_sum: `1.0`
- verified_top1: `0.9202380952380952`

### 6. 테스트 추가 및 API 테스트 보정

새 파일:

`tests/test_kfood_production_config.py`

검증 항목:

- production config가 valid JSON인지 확인
- top1과 correct가 92% 기준을 넘는지 확인
- 7개 모델이 모두 등록되어 있는지 확인
- 각 모델 checkpoint/metadata/classes 경로가 존재하는지 확인
- class order가 동일한지 확인

수정 파일:

`tests/test_api.py`

기존 API 테스트가 실제 무거운 ensemble을 로드하지 않도록 `load_classifier()`를 mock하도록 변경했다.

### 7. K-Food 56-class 영양 DB 연결

새 파일:

`scripts/build_kfood_nutrition_db.py`

생성된 데이터:

`data/processed/kfood_nutrition_db.json`

수정 파일:

`src/nutrition/nutrition_db.py`

개선 내용:

- K-Food 56-class 한국어 label을 nutrition lookup key로 직접 지원한다.
- `data/processed/train_data.csv`에서 exact match 51개를 생성했다.
- `곰탕_설렁탕`은 `곰탕`, `설렁탕` 평균으로 생성했다.
- exact row가 없는 4개 클래스는 curated alias로 생성했다.
  - `갈비구이`
  - `양념치킨`
  - `한과`
  - `후라이드치킨`
- 이제 `/predict/analyze`에서 K-Food classifier가 반환하는 한국어 label도 nutrition lookup과 risk predictor로 연결될 수 있다.

### 8. SugarPredictor 안전 fallback 옵션 추가

수정 파일:

`src/predictor/sugar_predictor.py`

개선 내용:

- `SugarPredictor(use_model=False)` 옵션을 추가했다.
- `use_model=False`이면 XGBoost model file을 로드하지 않고 rule-based fallback만 사용한다.
- API 기본값은 `settings.use_xgboost_predictor_model=False`라서 운영 classifier 추론 안정성을 우선한다.

## 검증 결과

### 문법 검사

실행:

```bash
python3 -m py_compile src/classifier/ensemble_food_classifier.py scripts/validate_kfood_production_config.py api/main.py config/settings.py
```

결과:

`pass`

### Production config preflight

실행:

```bash
python3 scripts/validate_kfood_production_config.py
```

결과:

`status = ok`

핵심 확인값:

- config: `/Users/sangrok/foodsugar-ai/config/kfood_production_ensemble_config.json`
- tta: `hflip`
- verified_top1: `0.9202380952380952`
- verified_correct: `6184`
- num_models: `7`
- num_classes: `56`
- weight_sum: `1.0`

### 실제 ensemble smoke test

실행 내용:

- `EnsembleFoodClassifier(config/kfood_production_ensemble_config.json)` 로드
- validation 이미지 1장 추론

샘플:

`data/raw/korean_food_fixed_v1/val/떡갈비/Img_006_0424.jpg`

결과:

- pred: `떡갈비`
- confidence: `0.9853736162185669`
- top5:
  - `떡갈비`
  - `갈비구이`
  - `갈비찜`
  - `불고기`
  - `양념치킨`

### 전체 테스트

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

`22 passed in 1.08s`

### K-Food nutrition coverage

확인 내용:

- production class 56개 전체에 대해 `get_nutrition(food_key)`가 `None`이 아님
- missing class: `[]`

샘플 조회:

| Class | calories | carbs | sugar | protein | fat | GI |
|---|---:|---:|---:|---:|---:|---:|
| `떡갈비` | `241.12` | `8.99` | `3.64` | `15.89` | `15.51` | `58.0` |
| `양념치킨` | `266.0` | `35.0` | `8.0` | `9.0` | `10.0` | `50.0` |
| `후라이드치킨` | `279.5` | `14.095` | `0.9725` | `16.695` | `17.645` | `50.0` |
| `곰탕_설렁탕` | `49.375` | `3.945` | `0.285` | `4.085` | `1.83` | `50.0` |

### 운영 통합 smoke test

확인 흐름:

1. `SugarPredictor(use_model=False)` 초기화
2. `EnsembleFoodClassifier(config/kfood_production_ensemble_config.json)` 초기화
3. validation 이미지 1장 추론
4. K-Food nutrition lookup
5. rule-based risk prediction

샘플:

`data/raw/korean_food_fixed_v1/val/떡갈비/Img_006_0424.jpg`

결과:

- classification: `떡갈비`
- classification time: 약 `0.84s`
- nutrition_found: `True`
- risk_label: `낮음`
- risk probabilities: `{'낮음': 0.875, '주의': 0.125, '위험': 0.0}`

## 현재 운영 확정 판단

현재 상태에서 이 모델은 다음 의미로 운영 후보로 고정 가능하다.

- 앱에서 자동 로드 가능한 production config가 있다.
- 실제 ensemble 추론기가 있다.
- config preflight가 통과한다.
- class order와 모델 파일 경로가 검증된다.
- 실제 이미지 smoke inference가 성공한다.
- 이미지 분류 후 nutrition/risk까지 연결되는 통합 smoke test가 성공한다.
- 기존 API 테스트가 깨지지 않는다.
- K-Food 56-class nutrition lookup이 모두 연결된다.
- fixed_v1 validation 기준 92%를 넘긴 검증 결과가 있다.

다만 완전한 운영 확정 전에는 아래 조건을 추가로 만족하는 것이 좋다.

## 운영 확정 전 남은 리스크

### 1. Validation-tuned weight 리스크

현재 weight는 `fixed_v1/val`에서 탐색된 값이다.

따라서:

- 현재 validation 기준 최고 후보로는 유효하다.
- 그러나 unseen test 일반화 성능까지 증명한 것은 아니다.
- 별도 holdout 또는 사람 검수 clean validation에서 frozen config를 다시 평가해야 한다.

### 2. Nutrition quality 리스크

K-Food 56-class nutrition lookup은 모두 연결됐다.

다만 일부 클래스는 exact row가 아니라 curated alias 또는 composite average를 사용한다.

따라서 운영 전에는 다음 5개 항목을 사람이 한 번 확인하는 것이 좋다.

- `갈비구이`
- `양념치킨`
- `한과`
- `후라이드치킨`
- `곰탕_설렁탕`

### 3. Latency 리스크

현재 운영 후보는 7-model ensemble + hflip TTA다.

정확도는 가장 높지만 단일 모델보다 추론 시간이 길다.

운영 배포 전에는 다음을 측정해야 한다.

- CPU latency
- MPS latency
- 동시 요청 처리량
- 메모리 사용량

### 4. XGBoost 재활성화 리스크

현재 API 기본값은 rule-based sugar predictor다.

`use_xgboost_predictor_model=True`로 trained XGBoost predictor를 다시 켤 경우, macOS torch/MPS ensemble inference와 충돌하지 않는지 별도 smoke test가 필요하다.

classifier 운영 안정성이 우선이면 현재 기본값을 유지하는 것이 좋다.

## 운영 확정 권장 순서

1. 현재 config를 freeze한다.
2. 더 이상 같은 `fixed_v1/val`에서 weight를 탐색하지 않는다.
3. 별도 holdout 또는 사람 검수 clean validation에서 이 config를 그대로 평가한다.
4. latency benchmark를 측정한다.
5. K-Food 56-class nutrition alias 품질을 확인한다.
6. XGBoost predictor를 운영에 포함할지 결정한다.
7. 위 조건을 통과하면 이 config를 운영모델로 확정한다.

## 현재 기준 Best 파일

Production config:

`config/kfood_production_ensemble_config.json`

Production classifier:

`src/classifier/ensemble_food_classifier.py`

Preflight validator:

`scripts/validate_kfood_production_config.py`

K-Food nutrition builder:

`scripts/build_kfood_nutrition_db.py`

K-Food nutrition DB:

`data/processed/kfood_nutrition_db.json`

Verified experiment result:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/metrics.json`

Improvement summary:

`KFOOD_92_IMPROVEMENT_SUMMARY_2026-05-16.md`
