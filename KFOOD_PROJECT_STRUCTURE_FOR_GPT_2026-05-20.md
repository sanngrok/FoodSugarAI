# K-Food / FoodSugar AI 프로젝트 구조 정리

- 작성일: 2026-05-20
- 프로젝트 경로: `/Users/sangrok/foodsugar-ai`
- 목적: 현재 진행 중인 K-Food 이미지 분류/혈당 위험도 프로젝트 구조를 GPT 검증용으로 정리
- 현재 운영 후보 모델: `kfood_92_hflip_7model_weighted_2026_05_16`
- 현재 운영 후보 성능: `top1 = 0.9202380952380952`
- 평가 기준: `data/raw/korean_food_fixed_v1/val`

## 1. 프로젝트 한 줄 요약

FoodSugar AI는 음식 이미지를 분류한 뒤, 음식별 영양정보를 조회하고 혈당 위험도를 예측하는 프로젝트다.

현재 핵심 작업은 기존 Food-101 중심 구조에서 한국음식 56-class K-Food classifier로 확장하고, validation 기준 92%를 넘긴 ensemble 모델을 운영 후보로 고정하는 단계다.

## 2. 현재 전체 구조

```text
foodsugar-ai/
├── api/                         # FastAPI 서버
├── config/                      # 앱 설정 및 운영 모델 config
├── data/
│   ├── raw/                     # 원본/분할 데이터셋
│   ├── processed/               # 전처리 산출물, nutrition DB, patch CSV
│   └── models/                  # 학습된 checkpoint, metadata, class json
├── demo/                        # Streamlit 데모
├── reports/                     # 실험/검증/분석 리포트
├── scripts/                     # 학습, 평가, audit, report 생성 스크립트
├── src/
│   ├── classifier/              # 이미지 분류 모델/학습/추론 코드
│   ├── data/                    # 데이터 준비/분할/수집 코드
│   ├── nutrition/               # 영양 DB 로딩 및 생성 코드
│   ├── predictor/               # 혈당 위험도 예측 코드
│   └── utils/                   # 이미지 유틸
├── tests/                       # pytest 테스트
├── README.md
└── KFOOD_*.md                   # 진행상황/결정/검증 브리프 문서들
```

## 3. 서비스 코드 구조

### `api/`

FastAPI 앱 진입점과 API 라우터가 있다.

```text
api/
├── main.py
├── routers/
│   ├── health.py
│   └── predict.py
└── schemas/
    └── models.py
```

중요 파일:

- `api/main.py`
  - FastAPI 앱 생성
  - startup 시 predictor/classifier 로드
  - 현재는 production ensemble config가 있으면 `EnsembleFoodClassifier`를 우선 로드
  - XGBoost와 torch/MPS 충돌 위험 때문에 API 기본값은 rule-based sugar predictor fallback

- `api/routers/predict.py`
  - `/predict/classify`
  - `/predict/risk`
  - `/predict/analyze`
  - 이미지 업로드 후 classification, nutrition lookup, risk prediction 수행

- `api/schemas/models.py`
  - API 요청/응답 Pydantic schema

## 4. 설정 구조

```text
config/
├── settings.py
└── kfood_production_ensemble_config.json
```

중요 파일:

- `config/settings.py`
  - 앱 이름/버전
  - classifier/predictor model path
  - `classifier_ensemble_config_path`
  - `use_xgboost_predictor_model`

- `config/kfood_production_ensemble_config.json`
  - 현재 운영 후보 7-model weighted ensemble 설정
  - checkpoint, metadata, classes, weight 고정
  - verified metric 포함

현재 production config 요약:

| 항목 | 값 |
|---|---|
| name | `kfood_92_hflip_7model_weighted_2026_05_16` |
| status | `production_candidate` |
| data_dir | `data/raw/korean_food_fixed_v1` |
| val_subdir | `val` |
| TTA | `hflip` |
| top1 | `0.9202380952380952` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| correct | `6184 / 6720` |
| num_classes | `56` |

## 5. 분류 모델 코드 구조

```text
src/classifier/
├── food_classifier.py
├── ensemble_food_classifier.py
├── food_lewm_model.py
├── lewm_sigreg.py
├── train_classifier.py
├── train_classifier_korean.py
├── train_food_lewm_classifier.py  # scripts 쪽에도 관련 실행 스크립트 존재
├── train_b2.py
├── train_b2_finetune.py
├── train_b4.py
├── resume_train.py
└── eval_tta.py
```

중요 파일:

- `src/classifier/food_classifier.py`
  - 단일 checkpoint 추론 wrapper
  - EfficientNet/timm classifier와 Food-LeWM classifier 모두 로드 가능
  - `predict(image)` 인터페이스 제공

- `src/classifier/ensemble_food_classifier.py`
  - 현재 운영 후보용 config-driven weighted ensemble
  - `config/kfood_production_ensemble_config.json`에서 7개 모델 로드
  - class order 검증
  - weight normalize
  - `hflip` TTA 지원
  - 기존 `FoodClassifier.predict()`와 같은 `ClassificationResult` 반환

- `src/classifier/food_lewm_model.py`
  - Food-LeWM 계열 모델 정의

- `src/classifier/train_classifier_korean.py`
  - 한국음식 classifier 학습 코드

## 6. 현재 운영 후보 Ensemble 구조

현재 최고 모델은 단일 모델이 아니라 7개 모델의 weighted ensemble이다.

| Model | Weight | Model type | Image size |
|---|---:|---|---:|
| `food_lewm_b0` | `0.14236057323734336` | `food_lewm_classifier` | `224` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` | `food_lewm_classifier` | `224` |
| `b3_full_fixed_v1` | `0.52949003398239` | `timm_classifier` | `300` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` | `food_lewm_classifier` | `224` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` | `timm_classifier` | `300` |
| `b3_cont_fixed_v1` | `0.00496452020109459` | `timm_classifier` | `300` |
| `b0_supervised_only` | `0.0033210487744569726` | `food_lewm_classifier` | `224` |

Checkpoint/config 위치:

```text
data/models/
├── food_lewm_b0_classifier_3ep_ft10.pt
├── food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
├── efficientnet_korean_b3_full_fixed_v1.pt
├── food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt
├── efficientnet_korean_b3_probe_fixed_v1.pt
├── efficientnet_korean_b3_cont_fixed_v1.pt
└── food_lewm_b0_supervised_only_ft10.pt
```

각 checkpoint는 대응되는 `*_meta*.json`, `*_classes*.json` 파일을 함께 가진다.

## 7. 데이터 구조

```text
data/
├── raw/
│   ├── korean_food_fixed_v1/
│   │   ├── train/
│   │   ├── val/
│   │   ├── train_manifest.csv
│   │   ├── val_manifest.csv
│   │   └── split_meta.json
│   └── food-101/
├── processed/
│   ├── kfood_nutrition_db.json
│   ├── nutrition_db_real.json
│   ├── train_data.csv
│   ├── kfood_label_patch_v1.csv
│   ├── kfood_exclude_list_v1.csv
│   ├── kfood_train_hard_pair_patch_v2.csv
│   └── kfood_train_hard_pair_exclude_v2.csv
└── models/
```

중요 데이터:

- `data/raw/korean_food_fixed_v1`
  - 현재 주요 학습/평가 split
  - validation sample 수: `6720`
  - class 수: `56`

- `data/processed/kfood_nutrition_db.json`
  - K-Food 56-class용 nutrition lookup DB
  - 현재 56개 class 전체 커버

- `data/processed/train_data.csv`
  - 식품안전나라 기반 영양정보 학습/lookup 원천

- `data/processed/nutrition_db_real.json`
  - 기존 Food-101용 nutrition DB

## 8. K-Food 56 클래스

현재 classifier class 목록:

```text
갈비구이, 갈비찜, 갈비탕, 감자전, 감자탕, 계란말이, 고등어구이, 곰탕_설렁탕,
김밥, 김치볶음밥, 김치전, 김치찌개, 김치찜, 닭갈비, 닭계장, 닭볶음탕,
동태찌개, 된장찌개, 떡갈비, 떡볶이, 라면, 라볶이, 만두, 물냉면,
보쌈, 불고기, 비빔냉면, 비빔밥, 삼겹살, 삼계탕, 새우볶음밥, 수정과,
수제비, 순대, 순두부찌개, 식혜, 알밥, 약과, 약식, 양념치킨,
유부초밥, 잔치국수, 잡곡밥, 족발, 주먹밥, 짜장면, 짬뽕, 쫄면,
찜닭, 칼국수, 파전, 피자, 한과, 호박전, 후라이드치킨, 훈제오리
```

## 9. Nutrition / 혈당 예측 구조

```text
src/nutrition/
├── nutrition_db.py
└── nutrition_db_builder.py

src/predictor/
├── sugar_predictor.py
└── train_predictor.py
```

중요 파일:

- `src/nutrition/nutrition_db.py`
  - `nutrition_db_real.json`과 `kfood_nutrition_db.json` 로드
  - `get_nutrition(food_key)` 제공
  - K-Food 한국어 label도 직접 조회 가능

- `src/predictor/sugar_predictor.py`
  - 혈당 위험도 예측
  - 현재 운영 기본값은 `use_model=False`
  - XGBoost model 대신 rule-based fallback 사용
  - 이유: macOS Python 3.14 환경에서 XGBoost eager import/model load가 torch/MPS ensemble inference와 충돌 가능

## 10. Scripts 구조

```text
scripts/
├── train_food_lewm_classifier.py
├── pretrain_food_lewm.py
├── eval_kfood_any_model.py
├── eval_kfood_ensemble.py
├── eval_weighted_ensemble_sweep.py
├── eval_fixed_weight_ensemble.py
├── sweep_cached_ensemble_weights.py
├── eval_cached_ensemble_subsets.py
├── check_cached_ensemble_stability.py
├── validate_kfood_production_config.py
├── build_kfood_nutrition_db.py
├── audit_kfood_splits.py
├── audit_label_patch_impact.py
├── build_kfood_label_patch.py
├── build_label_review_contact_sheets.py
├── prepare_label_review_sheet.py
├── score_review_sheet_with_ensemble.py
└── build_hard_class_report.py
```

주요 용도:

- 학습:
  - `train_food_lewm_classifier.py`
  - `pretrain_food_lewm.py`
  - `src/classifier/train_classifier_korean.py`

- 단일/ensemble 평가:
  - `eval_kfood_any_model.py`
  - `eval_kfood_ensemble.py`
  - `eval_fixed_weight_ensemble.py`
  - `eval_weighted_ensemble_sweep.py`

- cache 기반 ensemble 탐색:
  - `sweep_cached_ensemble_weights.py`
  - `eval_cached_ensemble_subsets.py`
  - `check_cached_ensemble_stability.py`

- 운영 검증:
  - `validate_kfood_production_config.py`

- 영양 DB:
  - `build_kfood_nutrition_db.py`

- label/hard pair 검수:
  - `build_kfood_label_patch.py`
  - `audit_label_patch_impact.py`
  - `build_label_review_contact_sheets.py`
  - `score_review_sheet_with_ensemble.py`
  - `build_hard_class_report.py`

## 11. Reports 구조

```text
reports/
├── b3/
├── current_best/
├── cleaned_v1/
├── error_analysis/
├── hard_class_report/
├── fixed_v1_split_audit/
├── split_leakage_audit/
├── weighted_ensemble/
└── production_validation/
```

중요 리포트:

- `reports/b3/verified_92_hflip_7model_weighted_2026_05_16/`
  - 현재 92% 달성 ensemble 검증 결과
  - `metrics.json`
  - `per_class_metrics.csv`
  - `confusion_matrix.csv`
  - `high_confidence_errors.csv`
  - `ensemble_config.json`

- `reports/b3/merged_candidate_random_search_2026_05_16/metrics.json`
  - 92% 넘긴 weight 조합을 찾은 random/local sparse search 결과

- `reports/b3/weighted_ensemble_3model_b3_full_hflip_step001/`
  - 이전 best였던 3-model ensemble 결과

- `reports/current_best/`
  - 사람 검수, current best decision, hard-pair 관련 자료

- `reports/hard_class_report/`
  - hard class/hard pair 분석

- `reports/fixed_v1_split_audit/`, `reports/split_leakage_audit/`
  - split leakage/overlap audit 결과

## 12. 진행상황 문서

프로젝트 root에 진행상황 문서들이 있다.

특히 중요한 문서:

- `KFOOD_92_GOAL_ACHIEVED_2026-05-16.md`
  - 92% 달성 결과 요약

- `KFOOD_92_IMPROVEMENT_SUMMARY_2026-05-16.md`
  - 91.98%에서 92.02%까지 올린 과정

- `KFOOD_PRODUCTION_MODEL_READINESS_2026-05-16.md`
  - 운영모델 준비 상태
  - production config, ensemble loader, nutrition DB, 테스트 결과 정리

- `KFOOD_GPT_VALIDATION_BRIEF_2026-05-14.md`
  - GPT 검증용 이전 브리프

- `KFOOD_CURRENT_BEST_91_NEXT_PROGRESS_2026-05-13.md`
  - 91%대 current best 진행상황

## 13. 현재 서비스 추론 흐름

현재 의도한 운영 흐름:

```text
이미지 업로드
  ↓
api/routers/predict.py
  ↓
request.app.state.classifier
  ↓
EnsembleFoodClassifier
  ↓
7-model weighted ensemble + hflip TTA
  ↓
K-Food 56-class 음식명 반환
  ↓
get_nutrition(food_key)
  ↓
K-Food nutrition DB 조회
  ↓
SugarPredictor(use_model=False)
  ↓
rule-based 혈당 위험도 반환
```

## 14. 검증된 명령어

Production config preflight:

```bash
python3 scripts/validate_kfood_production_config.py
```

K-Food nutrition DB 생성:

```bash
python3 scripts/build_kfood_nutrition_db.py
```

문법 검사:

```bash
python3 -m py_compile \
  api/main.py \
  config/settings.py \
  src/classifier/ensemble_food_classifier.py \
  src/predictor/sugar_predictor.py \
  src/nutrition/nutrition_db.py \
  scripts/validate_kfood_production_config.py \
  scripts/build_kfood_nutrition_db.py
```

전체 테스트:

```bash
python3 -m pytest tests/ -q
```

최근 확인 결과:

```text
22 passed
```

## 15. 현재 남은 리스크

### 15.1 Validation-tuned weight 리스크

현재 92.02% ensemble weight는 `fixed_v1/val`에서 탐색된 값이다.

따라서:

- 현재 validation 기준 최고 후보로는 유효하다.
- unseen test 일반화 성능을 증명한 것은 아니다.
- 운영 확정 전 별도 holdout 또는 사람 검수 clean set 평가가 필요하다.

### 15.2 Latency 리스크

운영 후보는 7-model ensemble + hflip TTA다.

정확도는 높지만 단일 모델보다 느리다.

운영 전 측정 필요:

- CPU latency
- MPS latency
- 메모리 사용량
- 동시 요청 처리량

### 15.3 Nutrition quality 리스크

K-Food 56개 class는 모두 nutrition lookup이 가능하다.

다만 일부 클래스는 exact row가 아니라 curated alias 또는 composite average다.

사람 확인이 필요한 클래스:

- `갈비구이`
- `양념치킨`
- `한과`
- `후라이드치킨`
- `곰탕_설렁탕`

### 15.4 XGBoost 재활성화 리스크

현재 API 기본값은 `use_xgboost_predictor_model=False`다.

이유:

- trained XGBoost predictor 또는 eager `xgboost` import가 torch/MPS ensemble inference와 충돌할 수 있었다.
- 운영 classifier 안정성을 우선하기 위해 rule-based fallback을 기본값으로 둔다.

XGBoost를 다시 켜려면 별도 smoke test가 필요하다.

## 16. GPT에게 검증받고 싶은 질문

아래 질문을 GPT에게 그대로 물어보면 좋다.

1. 이 프로젝트 구조에서 운영모델로 확정하기 전에 빠진 검증 단계가 있는가?
2. 7-model hflip ensemble을 운영에 쓰는 구조가 적절한가, 아니면 distillation/단일모델 경량화가 먼저 필요한가?
3. validation-tuned weight 리스크를 줄이기 위한 가장 현실적인 holdout/검수 전략은 무엇인가?
4. K-Food 56-class nutrition DB를 현재처럼 exact/alias 평균으로 연결한 방식에서 운영상 위험한 부분은 무엇인가?
5. XGBoost predictor를 rule-based fallback으로 둔 현재 구조가 서비스 관점에서 합리적인가?
6. FastAPI startup에서 heavy model ensemble을 로드하는 구조를 운영 배포 관점에서 어떻게 개선해야 하는가?
7. 현재 reports/scripts가 많아진 상태에서 장기 유지보수를 위해 어떤 폴더 정리가 필요한가?

## 17. GPT에게 전달할 핵심 요약

이 프로젝트는 한국음식 56-class 이미지 분류 모델을 운영화하는 단계다.

현재 validation 기준 `92.0238%`를 달성한 7-model hflip weighted ensemble이 production candidate로 고정되어 있다.

운영 config, ensemble loader, preflight validator, K-Food nutrition DB, 테스트는 준비되어 있다.

다만 weight가 validation-tuned라는 점, ensemble latency가 높을 수 있다는 점, 일부 nutrition mapping이 alias 기반이라는 점, XGBoost predictor와 torch/MPS 충돌 가능성 때문에 rule-based fallback을 기본으로 둔 점은 GPT 검증이 필요하다.
