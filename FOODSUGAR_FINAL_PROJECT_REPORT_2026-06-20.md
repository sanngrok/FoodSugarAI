# FoodSugar AI 최종 프로젝트 결과 보고서

- 작성일: 2026-06-20
- 프로젝트명: FoodSugar AI
- 최종 범위: 한국 음식 이미지 분류, 영양성분 기반 혈당 부담 참고 점수, CGM 기반 30/60/90분 예측, 웹앱 MVP, Vercel/Render 배포
- 핵심 주의문: 본 프로젝트의 혈당 관련 결과는 식습관 관리와 서비스 검증을 위한 참고용 정보이며, 의료 진단이나 치료 지침이 아니다.

## 1. Executive Summary

FoodSugar AI는 음식 사진을 출발점으로 하여 사용자가 먹으려는 음식의 종류를 추정하고, 그 음식의 영양성분을 바탕으로 혈당 부담 가능성을 낮음/주의/높음 형태로 보여주는 웰니스 앱 프로젝트이다. 프로젝트는 단순한 음식 분류 데모에서 시작했지만, 진행 과정에서 한국 음식 56-class 분류 모델, Food-LeWM 계열 실험, EfficientNet B0/B2/B3 실험, hard class 분석, label noise 검수, 7-model weighted ensemble, OhioT1DM 기반 CGM forecasting, range-aware calibration, hypo/hyper 가능성 신호, React 기반 웹앱, Vercel 프론트 배포, Render 백엔드 배포까지 확장되었다.

최고 성능 이미지 분류 모델은 `data/raw/korean_food_fixed_v1/val` 기준 hflip TTA를 적용한 7-model weighted ensemble이며, 검증 지표는 Top-1 0.920238, Top-3 0.979464, Macro F1 0.920038이다. 이 모델은 6,720개 validation sample 중 6,184개를 맞추었고, 설정 파일은 `config/kfood_production_ensemble_config.json`에 저장되어 있다. 다만 Render Free 플랜은 512MB 메모리 제한이 있어 7개 모델을 모두 로드하는 운영은 불가능했고, 실제 무료 서버 배포에서는 단일 Food-LeWM B0 seed123 모델을 사용하도록 전환했다. 이 단일 모델의 검증 성능은 Top-1 0.882887, Top-3 0.965179, Macro F1 0.882682이다.

혈당 기능은 두 축으로 구성했다. 첫째, 음식 영양성분 기반 0-100 혈당 부담 참고 점수 API를 만들었다. 이 API는 탄수화물, 당류, 식이섬유, 단백질, 지방, GI proxy, 섭취량을 종합하여 점수를 산출하고, UI에서는 위험이라는 표현 대신 낮음/주의/높음 표현을 사용한다. 둘째, OhioT1DM XML 데이터를 CGM 시계열로 변환하고, 30/60/90분 뒤 혈당을 예측하는 모델을 만들었다. 최종 enriched calibrated 모델은 test split에서 30분 MAE 12.998, 60분 MAE 22.633, 90분 MAE 29.606을 기록했다. 또한 90분 예측에는 uncertainty와 prediction interval을 강조하는 UI 정책을 적용했다.

웹앱은 React + Vite 기반으로 구현했다. 초기에는 데모/목업 중심이었지만, 이후 실제 `/predict/analyze`, `/predict/glucose-risk`, `/predict/cgm-forecast-enriched-events` API 연결 구조를 갖추었다. 디자인은 의료기기처럼 보이지 않도록 Levels, Signos, January AI, MyFitnessPal, Noom, Lingo 계열의 웰니스 앱 패턴을 참고하여 음식 스캔 우선 UX, 실제 모델 결과/데모 데이터 source badge, 낮은 confidence의 음식 확인 단계, 90분 예측 range-first card, target range band가 있는 glucose chart, weekly insight card, 안전 문구를 포함하도록 개선했다.

배포는 두 단계로 완료했다. 프론트엔드는 Vercel에 배포했고, 백엔드는 처음에는 Vercel Function으로 시도했으나 PyTorch, pandas, scikit-learn, checkpoint 크기 제한 때문에 경량 API만 가능했다. 최종적으로 Render Docker 기반 서버형 백엔드로 전환했다. Render Free 플랜에서는 7-model ensemble이 메모리 초과로 실패했기 때문에 `CLASSIFIER_MODE=single` 및 `CLASSIFIER_MODEL_PATH=data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` 설정으로 단일 모델 운영을 선택했다. 최종 `/health` 확인 결과는 `classifier_ready=true`, `predictor_ready=true`, `classifier_error=null`이었다.

## 2. 프로젝트 목표와 문제 정의

이 프로젝트의 출발점은 음식 사진 한 장으로 사용자가 먹는 음식의 종류를 추정하고, 그 음식이 혈당에 줄 수 있는 부담을 쉽게 이해하도록 돕는 것이다. 사용자는 음식을 찍거나 업로드하고, 앱은 음식명을 예측한 뒤 영양성분과 혈당 부담 점수를 보여준다. 혈당 예측 기능은 의료 판단이 아니라 식습관 관리 참고용으로 제한되며, UI와 API 응답 모두에서 이 원칙을 반복적으로 명시한다.

초기 목표는 한국 음식 이미지 분류 정확도를 높이는 것이었다. 이후 목표는 다음과 같이 확장되었다.

1. K-Food 56-class 음식 이미지 분류 모델을 학습하고 운영 후보를 만든다.
2. 단일 모델 성능의 한계를 보완하기 위해 seed ensemble, architecture diversity, B2/B3, Food-LeWM 계열을 실험한다.
3. label noise, hard class, hard pair 문제를 분석하고 cleaned split 후보를 만든다.
4. 92% Top-1 달성 가능한 production candidate ensemble을 구성한다.
5. 음식 영양성분으로 혈당 부담 점수를 계산한다.
6. OhioT1DM XML을 CGM 시계열 데이터로 변환하고 30/60/90분 예측 모델을 만든다.
7. low/high glucose bias를 보정하기 위해 range-aware calibration과 hypo/hyper event classifier를 추가한다.
8. 프론트엔드 웹앱을 만들어 음식 스캔 우선의 웰니스 dashboard UX로 제공한다.
9. Vercel/Render에 실제 배포하여 외부 URL에서 접근 가능하게 만든다.
10. 의료 진단/치료처럼 보이지 않도록 안전 문구와 참고용 표현을 모든 혈당 관련 결과에 유지한다.

프로젝트의 중요한 설계 원칙은 기존 음식분류 모델과 checkpoint를 함부로 수정하지 않는 것이었다. 음식 분류 학습 코드와 `data/models`의 checkpoint는 실험 결과를 재현하기 위한 기준이므로, 웹앱과 혈당 기능을 붙이는 과정에서도 기존 classifier training code를 건드리지 않는 방향을 우선했다. 배포 과정에서 필요한 변경은 inference wrapper와 배포 설정 중심으로 제한했다.

## 3. 전체 시스템 구성

FoodSugar AI는 크게 네 계층으로 구성된다.

### 3.1 이미지 분류 계층

이미지 분류 계층은 `src/classifier/` 아래의 모델 wrapper와 `data/models/` 아래 checkpoint로 구성된다. 최종 production candidate는 `config/kfood_production_ensemble_config.json`에 정의된 7-model weighted ensemble이다. 이 ensemble은 Food-LeWM B0, B0 seed123 fixed_v1, B3 full fixed_v1, B0 seed7 fixed_v1, B3 probe fixed_v1, B3 continued fixed_v1, B0 supervised only 모델을 가중 평균한다. hflip TTA를 사용하며, class order는 모든 멤버에서 동일해야 한다.

### 3.2 영양성분 및 혈당 부담 계층

영양성분 계층은 `src/nutrition/nutrition_db.py`와 `data/processed/kfood_nutrition_db.json`, `data/processed/nutrition_db_real.json`을 기반으로 한다. K-Food 56개 class에 대해서 GI proxy mapping을 보강했고, 기본 GI=50 placeholder를 그대로 쓰지 않도록 음식별 보수적 proxy 값을 적용했다. 혈당 부담 점수는 `src/glucose/risk.py`의 `score_glucose_risk` 계열 로직을 통해 0-100 점수와 낮음/주의/높음 level을 산출한다.

### 3.3 CGM forecasting 계층

CGM 계층은 `src/glucose/ohiot1dm.py`, `src/glucose/forecasting.py`, `scripts/prepare_ohiot1dm_cgm.py`, `scripts/train_glucose_forecaster.py`를 중심으로 구성된다. OhioT1DM XML 데이터를 5분 간격 CGM reading, meal, insulin, basal, exercise, biosignal event로 변환하고, lag/rolling/time-of-day/event/long-horizon feature를 생성한다. 저장된 모델은 `data/processed/glucose_models`와 `data/processed/glucose_models_enriched`에 위치한다.

### 3.4 API 및 웹앱 계층

API는 FastAPI 기반이며 주요 진입점은 `api/main.py`이다. router는 `api/routers/predict.py`, `api/routers/health.py`로 나뉜다. 웹앱은 `frontend/` 아래 React + Vite 프로젝트이며 `frontend/src/pages`와 `frontend/src/components`에 주요 화면과 컴포넌트가 있다. API client는 `frontend/src/lib/api.ts`에서 관리한다. 프론트엔드는 Vercel, 백엔드는 Render Docker 서버로 배포했다.

## 4. 한국 음식 이미지 분류 데이터와 split

음식 분류 데이터는 K-Food 56-class 구성을 사용했다. 프로젝트 중간에 fixed_v1 split을 만들었고, 이후 모든 공정 비교의 기준은 `data/raw/korean_food_fixed_v1/val`로 유지했다. 이는 label cleaning 후보가 validation에만 영향을 주어 성능이 과대평가되는 것을 막기 위한 결정이었다. cleaned_v1 후보 실험에서도 `val_original_fixed`와 `val_cleaned`를 분리하는 정책을 세웠고, 운영 후보 비교는 언제나 fixed validation 기준을 사용했다.

split leakage audit에서는 train/val 간 path overlap과 filename overlap을 점검했다. `reports/split_leakage_audit/`와 `reports/fixed_v1_split_audit/`에 관련 결과가 저장되어 있다. 프로젝트가 진행되면서 AI visual draft 기반 label review와 human review 후보를 만들었지만, 사람이 확정하지 않은 검수본은 운영용 cleaned split으로 승격하지 않고 `candidate`로만 취급했다.

hard class / hard pair 분석도 수행했다. confusion matrix, low precision, low recall class, high-confidence error를 기반으로 검수 우선순위를 만들었고, top300 review sheet와 train hard-pair candidate를 준비했다. 이 과정의 목적은 단순히 모델을 더 오래 학습시키는 것이 아니라, label boundary noise와 클래스 간 시각적 경계가 불명확한 문제를 먼저 파악하는 것이었다.

## 5. 이미지 분류 모델 실험 흐름

이미지 분류 실험은 B0 baseline에서 시작하여 Food-LeWM, seed ensemble, B2, B3, weighted ensemble로 확장되었다. 처음에는 EfficientNet 계열 단일 모델의 성능을 확인했고, 이후 supervised-only B0 seed123 및 seed7 모델을 학습했다. B0 계열은 계산량이 낮고 Render Free 배포에서도 현실적인 선택지였지만, 단일 성능은 88%대에 머물렀다.

Food-LeWM 계열은 pretraining과 classifier fine-tuning을 분리하여 실험했다. `food_lewm_b0_classifier_3ep_ft10` 모델과 supervised-only seed 모델들이 ensemble diversity를 제공했다. B2 실험은 단일 성능이 기대만큼 높지 않았지만, diversity member로 남길 가치가 있었다. B3 실험은 probe, continuation, full run 순서로 진행했다. B3 full fixed_v1은 7-model ensemble에서 가장 큰 weight를 받았으며, 최종 ensemble 성능 상승에 핵심 기여를 했다.

주요 실험 중 Render Free에서 실제 운영 중인 단일 모델은 `food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`이다. 이 모델은 10 epoch 학습 결과 `val_top1=0.8828869047619048`, `val_top3=0.9651785714285714`, `macro_f1=0.8826821359505763`을 기록했다. 학습 시간은 metrics 기록상 약 3142.4초이며, 모델 타입은 `food_lewm_classifier`, backbone은 `efficientnet_b0`, image size는 224, latent_dim은 192이다.

최고 성능 모델은 7-model hflip weighted ensemble이다. 구성과 weight는 다음과 같다.

| Model | Weight | Type | Image Size |
|---|---:|---|---:|
| food_lewm_b0 | 0.1423605732 | Food-LeWM B0 | 224 |
| b0_seed123_fixed_v1 | 0.2567350688 | Food-LeWM B0 supervised-only | 224 |
| b3_full_fixed_v1 | 0.5294900340 | EfficientNet-B3 | 300 |
| b0_seed7_fixed_v1 | 0.0621204284 | Food-LeWM B0 supervised-only | 224 |
| b3_probe_fixed_v1 | 0.0010083267 | EfficientNet-B3 | 300 |
| b3_cont_fixed_v1 | 0.0049645202 | EfficientNet-B3 | 300 |
| b0_supervised_only | 0.0033210488 | Food-LeWM B0 supervised-only | 224 |

최종 7-model ensemble metrics는 다음과 같다.

| Metric | Value |
|---|---:|
| Top-1 | 0.9202380952380952 |
| Top-3 | 0.9794642857142857 |
| Macro F1 | 0.9200379850437458 |
| Correct | 6184 / 6720 |
| Classes | 56 |
| TTA | hflip |

중요한 운영 판단은 92% ensemble과 Render Free 단일 모델을 구분하는 것이다. 연구/성능 목표에서는 7-model ensemble이 최종 후보이지만, Render Free 인스턴스에서는 512MB RAM 제한 때문에 7개 모델을 모두 로드할 수 없었다. 따라서 실제 무료 배포에서는 단일 B0 seed123 모델을 사용하고, 유료 RAM 환경에서는 7-model ensemble로 전환하는 정책을 문서화했다.

## 6. Label noise, cleaned_v1 candidate, hard-pair 검토

프로젝트 중반에는 단순 학습 epoch 증가보다 label noise와 hard pair를 먼저 다루는 방향으로 전환했다. high-confidence error, low recall class, low precision class를 기반으로 review sheet top300을 만들고, AI visual draft와 human review 후보를 분리했다. 중요한 원칙은 AI draft는 운영 확정 label이 아니라 `cleaned_v1_candidate` 실험용으로만 사용하는 것이었다.

label patch 생성 로직은 wrong_label은 relabel, multi_food/ambiguous/bad_crop은 remove, model_error/correct는 keep으로 분류하는 방향이었다. 다만 사람이 확정하지 않은 검수본은 운영 cleaned split으로 만들지 않았고, patch impact audit를 통해 train/val 영향이 어느 쪽에 집중되는지 확인하도록 했다. 이 판단은 모델 성능 향상을 validation correction 효과와 혼동하지 않기 위한 안전장치였다.

hard class / hard pair 분석의 목적은 모델이 진짜로 어려워하는 클래스 쌍을 파악하는 것이다. 김치찌개/된장찌개/순두부찌개 같은 찌개류, 볶음밥/비빔밥/김치볶음밥 같은 밥류, 전류, 면류, 치킨류처럼 시각적으로 유사하거나 음식 구성 요소가 섞인 클래스는 label boundary가 모호할 수 있다. 따라서 성능 개선은 단순히 더 큰 모델을 쓰는 방식뿐 아니라 클래스 정의와 데이터 품질 관리가 함께 필요하다는 결론을 냈다.

## 7. 영양성분 데이터베이스와 GI proxy

영양성분 DB는 `data/processed/nutrition_db_real.json`과 `data/processed/kfood_nutrition_db.json`을 우선순위로 로드한다. Food-101 계열 영어 key는 한국어 이름 mapping을 적용하고, K-Food 56-class는 한국어 class name을 그대로 key로 사용한다. 프로젝트 후반에는 `/predict/analyze`에서 예측된 음식이 모두 낮음으로 표시되는 문제가 발견되었다. 단독 `/predict/glucose-risk` API는 bibimbap_like, high_sugar_drink, very_high_carb를 잘 구분했지만, 통합 API는 기존 risk_label을 우선 사용하여 UI에서 낮음으로 보이는 문제가 있었다.

이를 해결하기 위해 `/predict/analyze` 응답에 `glucose_risk` 객체를 포함했고, 프론트에서는 기존 `risk_label`보다 `glucose_risk.score`와 `glucose_risk.level`을 우선 표시하도록 바꿨다. 또한 K-Food 56개 class에 대한 GI proxy mapping을 보강했다. 예를 들어 김치찌개, 된장찌개, 순두부찌개는 낮은 GI proxy를, 떡볶이, 라볶이, 라면, 수제비, 칼국수, 쫄면 등은 높은 GI proxy를 사용한다. UI 문구는 위험 대신 낮음/주의/높음으로 유지했다.

혈당 부담 점수는 의료적 혈당 반응 예측이 아니라 영양성분 기반 참고 지표다. 점수 산출에는 scaled carbs, scaled sugar, scaled fiber, scaled protein, scaled fat, glycemic_index, portion_g가 포함된다. fiber/protein/fat은 흡수 완충 요인으로 점수를 낮추는 방향으로 반영되며, 탄수화물과 GI는 점수를 높이는 방향으로 반영된다. 이 설계는 사용자에게 과도한 확정 표현을 하지 않으면서도 음식 선택에 참고 가능한 정보를 제공하기 위한 것이다.

## 8. OhioT1DM CGM 데이터 처리

혈당 예측 기능은 OhioT1DM XML 데이터를 기반으로 만들었다. XML에는 CGM reading, meal, bolus insulin, basal insulin, exercise, sleep, biosignal 등이 포함된다. `scripts/prepare_ohiot1dm_cgm.py`와 `src/glucose/ohiot1dm.py`는 XML을 읽어 timestamp 기반 tabular 시계열 데이터로 변환한다. 이후 `src/glucose/forecasting.py`에서 feature engineering과 모델 학습/추론 로직을 담당한다.

초기 CGM 모델은 최근 reading 기반 history model이었다. 이후 meal/insulin/event feature가 추가된 enriched model로 확장했다. 최종 enriched feature set에는 glucose lag, diff, rolling mean/std, hour sin/cos, carbs_current, carbs_last_30m/60m/120m/180m, bolus_current, bolus_last_*m, basal feature, exercise, sleep, biosignal, patient_id_numeric, long-horizon proxy feature가 포함된다. long-horizon feature에는 time_since_last_meal, time_since_last_bolus, carb/insulin decay, carbs_on_board_proxy, insulin_on_board_proxy, net_glucose_pressure_proxy, glucose slope/volatility/mean, recent low/high event count가 포함된다.

데이터 분할은 leakage를 막기 위해 time-based per source/patient/year 방식을 사용했다. test split을 model selection에 쓰지 않기 위해 train 내부에서 validation split을 만들고, calibration strategy, threshold, event classifier selection은 validation에서 선택한 뒤 test에서 최종 평가했다. `reports/glucose_forecasting/validation_split_summary.json`에는 validation fraction 0.2, train_inner_rows 107,827, validation_rows 26,963, groups 12, time_order_safe true로 기록되어 있다.

## 9. CGM forecasting 성능

최종 test evaluation은 validation에서 선택한 model family, threshold, calibration strategy를 고정한 뒤 test split에서 평가했다. Forecast metrics는 다음과 같다.

| Model | Horizon | Samples | MAE | RMSE | R2 | MAE vs persistence | MAE vs history |
|---|---:|---:|---:|---:|---:|---:|---:|
| enriched calibrated | 30m | 29536 | 12.998 | 18.476 | 0.9054 | 23.25% | 3.90% |
| enriched calibrated | 60m | 29536 | 22.633 | 31.008 | 0.7346 | 20.59% | 5.18% |
| enriched calibrated | 90m | 29536 | 29.606 | 39.831 | 0.5640 | 19.97% | 4.73% |
| history | 30m | 29677 | 13.526 | 19.163 | 0.8983 | 20.13% | 0.00% |
| history | 60m | 29677 | 23.869 | 32.411 | 0.7103 | 16.26% | 0.00% |
| history | 90m | 29677 | 31.074 | 41.219 | 0.5344 | 16.00% | 0.00% |
| persistence | 30m | 29677 | 16.935 | 23.385 | 0.8486 | 0.00% | -25.21% |
| persistence | 60m | 29677 | 28.503 | 38.506 | 0.5911 | 0.00% | -19.41% |
| persistence | 90m | 29677 | 36.993 | 49.254 | 0.3352 | 0.00% | -19.05% |

결과적으로 enriched calibrated model은 persistence baseline보다 모든 horizon에서 의미 있게 낮은 MAE를 기록했고, history-only model보다도 소폭 개선되었다. 30분 예측은 가장 안정적이고 R2도 0.9054로 높다. 60분은 중간 수준의 예측력을 보이며, 90분은 MAE 29.606으로 불확실성이 커진다. UI에서 90분 예측을 point estimate가 아니라 range-first, uncertainty-first로 보여주기로 한 이유가 여기에 있다.

event classifier는 hyper/hypo 가능성 신호를 반환한다. Hyper event는 30분 ROC-AUC 0.975, 60분 0.927, 90분 0.869로 비교적 안정적이다. Hypo event는 recall을 높게 유지하도록 threshold를 설정했기 때문에 precision이 낮다. 예를 들어 hypo 90분은 precision 0.157, recall 0.640이다. 따라서 UI에서는 이를 절대 진단처럼 표현하지 않고, “저혈당 가능성 신호” 또는 “고혈당 가능성 신호”라고 표현한다.

prediction interval은 validation/test error 기반으로 산출했다. 예측값 주변에 p90 absolute error 기반 interval을 붙이고, uncertainty level을 low/medium/high로 제공한다. 특히 90분 예측은 high uncertainty가 자주 나타나므로, UI에서 90m card는 범위와 불확실성을 우선 표시한다. 이 설계는 사용자가 특정 mg/dL point value를 과신하지 않도록 하기 위한 안전장치다.

## 10. API 설계

FastAPI 서버의 주요 endpoint는 다음과 같다.

| Endpoint | Method | 목적 |
|---|---|---|
| `/health` | GET | 서버 상태, classifier/predictor readiness 확인 |
| `/predict/classify` | POST | 음식 이미지 분류 |
| `/predict/risk` | POST | 영양정보 기반 기존 risk predictor |
| `/predict/glucose-risk` | POST | 영양성분 기반 0-100 혈당 부담 참고 점수 |
| `/predict/analyze` | POST | 이미지 업로드 → 음식 분류 → 영양정보 조회 → 위험도/점수 통합 |
| `/predict/cgm-forecast` | POST | 최근 CGM readings 기반 30/60/90분 예측 |
| `/predict/cgm-forecast-enriched` | POST | engineered event feature 포함 enriched 예측 |
| `/predict/cgm-forecast-enriched-events` | POST | raw event 입력을 API 내부에서 feature로 변환 후 enriched 예측 |

`/predict/analyze`는 프론트엔드에서 가장 중요한 endpoint다. 파일 업로드와 portion_g를 받아 classifier가 food_key와 confidence, top5를 반환하고, nutrition DB에서 영양성분을 조회한 뒤, 기존 risk response와 새 glucose_risk response를 함께 반환한다. 프론트에서는 `glucose_risk.score`가 있으면 이를 우선 표시하고, 없으면 기존 risk label을 fallback으로 사용한다.

`/health`는 배포 과정에서 매우 중요했다. 처음에는 classifier_ready와 predictor_ready만 제공했지만, Render 배포 debugging 중 classifier_error를 추가했다. 이를 통해 checkpoint 누락, 메모리 부족, class mismatch, path newline 문제를 빠르게 식별할 수 있었다. 최종 성공 상태는 `classifier_ready=true`, `predictor_ready=true`, `classifier_error=null`이다.

## 11. 안전 문구와 비의료 포지셔닝

FoodSugar AI의 혈당 관련 기능은 모두 참고용으로 제한했다. API response에는 `reference_notice`, `risk_interpretation`, `safety_warning`을 포함하고, 프론트엔드도 glucose-related page에서 안전 문구를 노출한다. 핵심 문구는 다음 원칙을 따른다.

1. “진단”, “치료”, “처방”, “인슐린 조절”처럼 의료적 결정으로 오해될 표현을 피한다.
2. 혈당 예측은 가능성 신호와 참고 범위로만 표현한다.
3. hypo/hyper event는 “저혈당/고혈당입니다”가 아니라 “저혈당 가능성 신호”, “고혈당 가능성 신호”로 표현한다.
4. 증상 또는 실제 측정값이 우려되면 앱 예측이 아니라 실제 CGM/혈당 측정값과 의료진 상담을 우선하라고 안내한다.
5. 90분 예측은 point estimate보다 prediction interval과 uncertainty를 우선한다.

이 안전 정책은 기술 구현뿐 아니라 UX에도 반영되었다. PredictionPage의 90m card는 범위와 불확실성을 먼저 보여주고, SettingsPage에는 “what this app does / does not do” 섹션을 넣었다. HistoryPage와 AnalysisPage에서도 wellness dashboard 톤을 유지하고, 의료기기처럼 보이는 warning-heavy UI를 피했다.

## 12. 웹앱 구현

프론트엔드는 `frontend/`에 새로 만든 React + Vite 앱이다. 주요 구성은 다음과 같다.

| 파일/폴더 | 역할 |
|---|---|
| `frontend/src/App.tsx` | route/page state와 주요 앱 흐름 |
| `frontend/src/pages/HomePage.tsx` | 음식 스캔 시작 화면, demo scenario 버튼 |
| `frontend/src/pages/AnalysisPage.tsx` | 음식 분석 결과, 확인 카드, 영양 요약, 위험도 카드 |
| `frontend/src/pages/PredictionPage.tsx` | CGM-style 예측 chart, 30/60/90분 예측 |
| `frontend/src/pages/HistoryPage.tsx` | weekly insight card와 기록 리스트 |
| `frontend/src/pages/SettingsPage.tsx` | 안전/제한사항 안내 |
| `frontend/src/components/GlucoseChart.tsx` | target range band와 prediction interval band |
| `frontend/src/components/ResultSourceBadge.tsx` | 실제 모델 결과/데모 데이터 badge |
| `frontend/src/lib/api.ts` | 백엔드 API client와 mock fallback |

초기 웹앱은 mock 중심이었지만, 실제 API 연동을 고려하여 fallback을 명확히 표시하도록 수정했다. 예를 들어 백엔드 연결 실패 시 바로 비빔밥이라고 단정하지 않고 “비빔밥 데모 예시”, confidence 0, sourceNotice를 표시한다. 분석 시작 시 최소 loading delay도 넣어 사용자가 실제 요청이 수행되는 느낌을 받을 수 있도록 했다. 이는 사용자가 김치찌개 이미지를 넣었는데 즉시 비빔밥이라고 표시되어 혼동했던 문제를 해결하기 위한 조치였다.

디자인 개선은 wellness dashboard 방향으로 진행했다. 배경은 warm cream `#F8F6EC`, card는 `#FFFDF5`, primary green은 `#1F7A43`, soft green은 `#E8F3E8`, warning orange는 `#F97316`을 유지했다. 화면은 의료 경고판처럼 보이지 않도록 차분한 insight card, nutrition summary, range chart, source badge 중심으로 구성했다.

## 13. 프론트엔드 테스트와 빌드

프론트엔드에는 Vitest 기반 테스트가 있다. 주요 테스트는 mock fallback, safety UI, wellness dashboard 관련 검증을 포함한다. 실행 명령은 다음과 같다.

```bash
cd frontend
npm run test
npm run build
```

Vercel 배포 중 `recharts` deprecated warning과 chunk size warning이 나타났지만, build 실패는 아니었다. chunk size warning은 추후 code splitting이나 chart component lazy loading으로 줄일 수 있다. 현재 MVP 수준에서는 기능 동작에 직접적 문제는 없었다.

## 14. Vercel 프론트 배포

프론트엔드는 Vercel에 별도 프로젝트로 배포했다. 루트 repo에는 Python/FastAPI와 큰 data/model 파일이 있기 때문에, 처음 root에서 Vercel 배포를 시도했을 때 FastAPI 감지와 빌드 설정 충돌이 발생했다. 이후 `frontend/`를 별도 Vercel 프로젝트로 배포하도록 정리했다.

프론트 Vercel 설정은 `frontend/vercel.json`에 있다. framework는 Vite, build command는 `npm run build`, output directory는 `dist`, SPA rewrite는 `/{path} -> /index.html`이다. 실제 public URL은 `https://frontend-jade-theta-40.vercel.app`이다.

프론트에서 백엔드 URL은 `VITE_API_BASE_URL` 환경변수로 주입한다. 초기에 Vercel 경량 백엔드 `https://foodsugar-ai.vercel.app`를 사용했지만, 실제 classifier와 CGM을 운영하려면 Render 백엔드 `https://foodsugarai.onrender.com`로 교체해야 한다. Vite 환경변수는 build time에 bundle에 박히므로, 환경변수 변경 후 반드시 Redeploy가 필요하다.

## 15. Vercel 백엔드 시도와 한계

처음에는 FastAPI 백엔드도 Vercel에 올리려고 했다. 이를 위해 root `app.py`, `requirements-vercel.txt`, `.vercelignore`, `vercel.json`을 만들고, PyTorch와 scikit-learn을 제외한 경량 백엔드를 배포했다. `/predict/glucose-risk`는 정상 동작했지만, PyTorch model loading과 CGM forecasting 전체를 포함하기에는 Vercel Function 번들 크기와 runtime 제한이 컸다.

Vercel Python 함수는 dependencies가 커질수록 bundle size 제한에 걸렸다. pandas/scikit-learn/scipy를 포함하면 472MB 수준까지 올라갔고, 기본 제한을 넘었다. numpy까지 제거해도 다른 import 문제들이 반복되었다. 최종적으로 Vercel 백엔드는 영양성분 기반 glucose-risk 같은 경량 API에는 적합하지만, FoodSugar AI의 실제 classifier 및 CGM full model 운영에는 부적합하다고 판단했다.

이 시도는 실패가 아니라 배포 아키텍처 결정을 위한 검증이었다. 프론트는 Vercel, 백엔드는 서버형 플랫폼으로 분리하는 구조가 더 적절하다는 결론을 얻었다.

## 16. Render 서버형 백엔드 배포

최종 백엔드는 Render Docker Web Service로 배포했다. 추가된 파일은 `Dockerfile`, `.dockerignore`, `render.yaml`, `railway.json`, `scripts/create_server_artifact.py`, `scripts/download_server_artifacts.py`이다. Dockerfile은 Python 3.12 slim 기반이며, CPU-only PyTorch wheel을 먼저 설치하고 `requirements.txt`를 설치한다. 서버 시작 시 `scripts/download_server_artifacts.py`를 실행하여 `FOODSUGAR_MODEL_BUNDLE_URL`에서 모델 bundle을 다운로드하고 압축 해제한 뒤 uvicorn으로 FastAPI를 실행한다.

모델 bundle은 Git에 올리지 않고 `artifacts/foodsugar_server_artifacts.tar.gz`로 생성했다. 생성 명령은 `python3 scripts/create_server_artifact.py`이며, 생성된 bundle은 약 205.2MB, 42개 파일을 포함한다. 여기에는 7-model ensemble 구성에 필요한 checkpoint/classes/metadata, xgboost_sugar.pkl, nutrition DB, glucose model artifact가 포함된다.

Render 배포 중 다음 문제를 해결했다.

1. Dockerfile이 GitHub에 push되지 않아 `open Dockerfile: no such file or directory` 발생: server deployment config를 commit/push하여 해결했다.
2. data/processed json 파일이 Git에 없어 Docker build COPY 실패 가능성: Dockerfile에서 해당 COPY를 제거하고 artifact bundle에서 제공하도록 했다.
3. classifier artifact 누락 시 서버가 죽는 문제: `/health`에 `classifier_error`를 추가하고 classifier loading 예외를 잡아 서버가 살아있도록 했다.
4. Food-LeWM class mismatch: ensemble config의 classes/metadata 경로를 FoodClassifier에 명시적으로 넘기도록 수정했다.
5. Render Free 512MB 메모리 초과: 7-model ensemble 대신 `CLASSIFIER_MODE=single`을 추가했다.
6. `CLASSIFIER_MODEL_PATH` 환경변수 끝의 newline 문제: Path field validator로 strip 처리했다.
7. single seed123 모델 companion json 탐색 실패: `food_lewm_*_ft10.pt` 계열 companion metadata 탐색 로직을 추가했다.

최종 Render `/health` 결과는 다음과 같다.

```json
{
  "status": "ok",
  "version": "0.1.0",
  "classifier_ready": true,
  "predictor_ready": true,
  "classifier_error": null
}
```

이는 Render 백엔드가 정상적으로 뜨고 단일 classifier 모델과 predictor가 모두 준비되었다는 뜻이다. 다만 Render Free는 inactivity 후 sleep 상태로 내려가며, 첫 요청 시 30~60초 이상 지연될 수 있다. 이는 정상 동작이며, 유료 plan을 쓰면 cold start와 sleep 문제를 줄일 수 있다.

## 17. 최종 운영 상태

현재 운영 상태는 다음과 같이 정리된다.

| 항목 | 상태 |
|---|---|
| Frontend | Vercel 배포 완료 |
| Frontend URL | `https://frontend-jade-theta-40.vercel.app` |
| Backend | Render Docker 서버 배포 완료 |
| Backend URL | `https://foodsugarai.onrender.com` |
| Render health | `classifier_ready=true`, `predictor_ready=true` |
| Render classifier mode | `single` |
| Render classifier model | `food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| Render Free limitation | 7-model ensemble 불가, 512MB RAM 제한 |
| Research best model | 7-model hflip weighted ensemble, Top-1 92.02% |
| Deployed model | single Food-LeWM B0 seed123, Top-1 88.29% |
| Blood glucose risk | `/predict/glucose-risk` 정상 |
| CGM enriched forecast | 서버형 artifact 포함, long-horizon feature 사용 |

운영 관점에서는 두 가지 모델 상태를 구분해야 한다. 제출/연구 결과로는 92.02% ensemble이 최고 성능 후보이며, 실제 Render Free 배포에서는 메모리 제한 때문에 88.29% 단일 모델이 올라간 상태다. 유료 Render plan 또는 메모리 1GB 이상 서버로 이전하면 `CLASSIFIER_MODE=ensemble`로 바꾸어 7-model ensemble을 운영할 수 있다.

## 18. 실제 사용자 흐름

사용자 관점의 흐름은 다음과 같다.

1. 사용자가 Vercel 프론트 URL에 접속한다.
2. HomePage에서 음식 사진을 업로드하거나 demo scenario를 선택한다.
3. 프론트는 `VITE_API_BASE_URL`에 설정된 Render 백엔드로 `/predict/analyze` 요청을 보낸다.
4. Render 백엔드는 이미 다운로드된 model artifact에서 단일 Food-LeWM B0 classifier를 로드한다.
5. classifier가 food_key, food_name_ko, confidence, top5를 반환한다.
6. nutrition DB에서 영양성분을 조회한다.
7. 기존 risk와 새 glucose_risk score를 계산한다.
8. 프론트는 실제 모델 결과 badge를 표시하고, 낮은 confidence이면 음식 확인 단계를 보여준다.
9. AnalysisPage는 칼로리/탄수화물/단백질/지방/섬유/혈당 부담 점수를 보여준다.
10. PredictionPage는 CGM-style chart, target range band, prediction interval band, 30/60/90분 예측을 표시한다.

백엔드 연결이 실패하거나 Render가 sleep 상태에서 너무 오래 깨어나지 않으면 프론트는 mock fallback을 표시한다. 이 경우 ResultSourceBadge와 sourceNotice를 통해 데모 데이터임을 명확히 표시한다.

## 19. 검증 요약

프로젝트 전반에서 수행한 검증은 다음과 같다.

### 19.1 이미지 분류 검증

- fixed_v1 validation 기준 단일/ensemble 모델 평가
- hflip TTA 비교
- top1/top3/macro_f1 기록
- confusion matrix와 hard class report 생성
- 7-model weighted ensemble 92.02% 달성 확인

### 19.2 데이터 검증

- split leakage audit
- fixed_v1 split audit
- label patch impact audit
- AI draft 기반 cleaned_v1_candidate 제한 명시
- human review 필요 항목 분리

### 19.3 혈당 모델 검증

- validation/test split 분리
- test split을 selection에 사용하지 않는 구조 확인
- baseline vs enriched vs calibrated metrics 비교
- range-aware calibration
- hypo/hyper event classifier metrics
- prediction interval coverage 관련 artifact 검증
- artifact validation report pass

### 19.4 API 검증

- `/health` readiness 확인
- `/predict/glucose-risk` 비빔밥 예시 점수 확인
- `/predict/analyze` 응답에 `glucose_risk` 포함
- classifier missing/ImportError/fallback 경로 처리
- Render classifier_error debugging

### 19.5 프론트 검증

- `npm run test`
- `npm run build`
- mock fallback source notice
- safety UI wording
- wellness dashboard UI
- Vercel deployment 200 response
- build artifact에 Render backend URL 반영

## 20. 기술적 한계와 리스크

현재 프로젝트의 한계는 명확하다.

첫째, 92% ensemble은 validation split에서 weight를 선택한 production candidate이므로, 완전한 운영 확정 모델로 보려면 별도 holdout이나 human-reviewed clean validation에서 재검증해야 한다. 보고서에서는 92%를 research best 또는 production candidate로 표현하고, 최종 clinical/production guarantee처럼 표현하지 않는다.

둘째, Render Free에서는 7-model ensemble을 운영할 수 없다. 현재 실제 서버는 88.29% 단일 모델을 사용한다. 이것은 비용/메모리 제약에 따른 현실적 운영 선택이다. 92% 모델을 실제 서비스에 올리려면 Render 유료 plan, Railway/Fly/EC2 등 1GB 이상 RAM 환경이 필요하다.

셋째, CGM 예측 모델은 OhioT1DM 데이터 기반이며, 외부 데이터셋에서의 일반화는 아직 검증되지 않았다. 환자별 반응, 식사 기록 정확도, insulin/event 입력 누락, sensor error, timestamp mismatch에 따라 결과가 달라질 수 있다. 따라서 예측값은 참고용으로만 제공한다.

넷째, hypo event classifier는 recall을 높게 잡아 false positive가 많을 수 있다. 이는 안전 측면에서 가능성 신호를 놓치지 않기 위한 선택이지만, UI에서 사용자가 불필요한 불안을 느끼지 않도록 표현과 threshold 조정이 필요하다.

다섯째, 영양성분 DB와 GI proxy는 실제 개인별 혈당 반응을 직접 측정한 값이 아니다. 음식 조리법, 양념, 섭취량, 동반 음식, 개인의 insulin sensitivity, 운동, 수면 등에 따라 실제 혈당 반응은 달라진다.

## 21. 향후 개선 계획

향후 개선 계획은 다음과 같다.

1. Render 유료 plan 또는 1GB 이상 RAM 서버로 이동하여 7-model 92% ensemble을 실제 배포한다.
2. human-reviewed clean validation set을 확정하여 92% ensemble의 실제 운영 적합성을 재검증한다.
3. low-confidence food confirmation UX를 실제 API top5와 더 깊게 연결한다.
4. 이미지 업로드 후 분석 중 loading/progress state를 더 자연스럽게 만든다.
5. CGM enriched model 입력에 필요한 최소 readings 수를 UI/API schema에서 명확히 안내한다.
6. 90분 예측의 uncertainty messaging을 더 직관적으로 개선한다.
7. hypo/hyper event threshold를 사용자 설정 또는 보수/균형 mode로 분리한다.
8. 외부 CGM 데이터셋 또는 파일럿 사용자 데이터로 external validation을 수행한다.
9. nutrition DB를 더 넓은 음식군과 실제 브랜드/식품 데이터로 확장한다.
10. 프론트 bundle size를 줄이기 위해 chart/page lazy loading을 적용한다.
11. 실제 운영 로그에서 개인식별정보가 남지 않도록 privacy logging policy를 강화한다.
12. 사용자가 직접 음식명을 수정했을 때 nutrition/glucose-risk를 재계산하는 flow를 추가한다.

## 22. 최종 결론

FoodSugar AI는 프로젝트 기간 동안 단순 음식 이미지 분류에서 출발해, 혈당 부담 참고 점수와 CGM forecasting을 포함한 웰니스 앱으로 발전했다. 이미지 분류에서는 K-Food 56-class 기준 92.02% Top-1 7-model ensemble을 달성했고, 혈당 기능에서는 30/60/90분 CGM 예측, range-aware calibration, hypo/hyper 가능성 신호, prediction interval을 구현했다. 웹앱은 음식 스캔 우선 UX와 wellness dashboard 스타일을 갖추었고, Vercel/Render 배포를 통해 실제 URL에서 접근 가능한 상태가 되었다.

가장 중요한 성과는 모델 성능 자체뿐 아니라 제품화 과정에서 발생한 현실적 문제를 해결했다는 점이다. Vercel Function의 크기/런타임 제한, Render Free의 512MB 메모리 제한, model artifact 배포, GitHub Release URL, environment variable newline, class metadata mismatch 등 실제 배포에서 자주 발생하는 문제를 하나씩 해결했다. 최종적으로 Render `/health`에서 classifier와 predictor가 모두 ready 상태가 되었으며, 프론트는 Render 백엔드로 연결 가능한 구조가 되었다.

다만 현재 무료 서버 배포는 92% ensemble이 아니라 88.29% 단일 모델이다. 따라서 제출 보고서에서는 연구 성능과 실제 무료 배포 성능을 분리해서 설명해야 한다. 연구 최고 성능은 92.02% ensemble, 현재 Render Free 운영 모델은 88.29% single B0 seed123이다. 이것은 성능 저하가 아니라 인프라 제약에 맞춘 배포 전략이다. 향후 1GB 이상 RAM 환경으로 옮기면 7-model ensemble 운영으로 전환할 수 있다.

마지막으로 혈당 관련 기능은 끝까지 참고용으로 유지해야 한다. FoodSugar AI는 의료기기가 아니라 웰니스 보조 앱이며, 앱의 예측값이나 위험도는 사용자의 실제 혈당 측정값과 의료진의 판단을 대체하지 않는다. 이 원칙은 API, UI, 보고서, 배포 문서 전반에 유지되어야 한다.

## Appendix A. 모델 실험 상세 타임라인

### A.1. 초기 B0 baseline

EfficientNet-B0 기반으로 K-Food split에서 기본 학습과 평가를 수행했다. 이 단계에서는 데이터 loader, class order, checkpoint 저장, validation metric 기록 구조를 검증했다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.2. Food-LeWM pretraining

Food-LeWM 방식의 latent prediction 구조를 실험하고, pretraining 후 classifier fine-tuning이 단일 supervised-only 모델과 어떤 차이를 보이는지 확인했다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.3. B0 seed123 / seed7

seed를 달리한 B0 supervised-only 모델을 학습하여 ensemble diversity를 확보했다. seed123 모델은 Render Free 운영 후보가 되었다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.4. B2 clean fixed_v1

B2 계열은 단일 성능보다 diversity member로서의 가치를 확인하는 데 초점을 두었다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.5. cleaned_v1 candidate 논의

AI draft 검수본을 운영 cleaned_v1이 아니라 candidate로 격리하고, val_original_fixed와 val_cleaned를 분리해야 한다는 원칙을 세웠다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.6. B3 probe

B3 full run 이전에 10 epoch probe를 수행하여 architecture scaling의 가능성을 확인했다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.7. B3 full fixed_v1

B3 full 모델은 최종 ensemble에서 가장 큰 weight를 받았고, 92% 달성에 핵심 기여를 했다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.8. weighted ensemble sweep

weight grid와 random search를 통해 7-model weighted ensemble을 구성했고, 0.920238 Top-1을 달성했다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

### A.9. Render Free deployment

7-model ensemble은 메모리 한계로 운영하지 못했고, 단일 B0 seed123 모델을 Render Free에 올렸다.

이 단계에서 얻은 교훈은 모델 성능은 단일 숫자로만 판단할 수 없고, 데이터 품질, class boundary, validation 기준, 배포 메모리, inference latency, fallback UX와 함께 판단해야 한다는 점이다.

## Appendix B. API 응답 설계 상세

### /health

서비스 상태 확인 endpoint다. classifier_ready, predictor_ready, classifier_error를 반환하여 배포 troubleshooting에 사용한다.

응답에는 가능하면 reference_notice, risk_interpretation, safety_warning을 포함한다. 프론트엔드는 이 정보를 사용하여 사용자가 결과를 의료적 확정 판단으로 오해하지 않도록 한다.

### /predict/analyze

이미지 파일과 portion_g를 입력받아 분류, 영양정보 조회, risk, glucose_risk를 통합 반환한다.

응답에는 가능하면 reference_notice, risk_interpretation, safety_warning을 포함한다. 프론트엔드는 이 정보를 사용하여 사용자가 결과를 의료적 확정 판단으로 오해하지 않도록 한다.

### /predict/glucose-risk

영양성분 JSON을 입력받아 0-100 점수와 낮음/주의/높음 level을 반환한다.

응답에는 가능하면 reference_notice, risk_interpretation, safety_warning을 포함한다. 프론트엔드는 이 정보를 사용하여 사용자가 결과를 의료적 확정 판단으로 오해하지 않도록 한다.

### /predict/cgm-forecast-enriched-events

raw CGM readings와 meal/bolus/basal/exercise event를 받아 API 내부에서 feature를 만들고 enriched model로 30/60/90분 예측을 반환한다.

응답에는 가능하면 reference_notice, risk_interpretation, safety_warning을 포함한다. 프론트엔드는 이 정보를 사용하여 사용자가 결과를 의료적 확정 판단으로 오해하지 않도록 한다.

## Appendix C. 배포 troubleshooting 기록

### C.1. Vercel root deploy failure

루트 repo가 FastAPI로 감지되면서 프론트 빌드와 충돌했다. 해결은 frontend 디렉터리를 별도 Vercel 프로젝트로 배포하는 것이었다.

### C.2. Vercel Python bundle limit

pandas/scikit-learn/scipy/torch 포함 시 함수 크기 제한을 초과했다. 이로 인해 백엔드는 서버형 Render로 분리했다.

### C.3. Render Dockerfile missing

Dockerfile이 로컬에만 있고 GitHub main에 push되지 않아 Render build가 실패했다. 배포 설정 파일을 commit/push하여 해결했다.

### C.4. Artifact URL and missing checkpoints

모델 checkpoint는 Git에 올리지 않고 tar.gz bundle을 Release URL에서 다운로드하도록 했다. 잘못된 URL은 classifier_ready=false로 드러난다.

### C.5. Render 512MB memory limit

7-model ensemble은 Free plan에서 메모리 초과가 발생했다. CLASSIFIER_MODE=single로 전환했다.

### C.6. Environment variable newline

CLASSIFIER_MODEL_PATH 끝에 newline이 들어가 파일을 찾지 못했다. settings에서 path 값을 strip하도록 했다.

### C.7. Food-LeWM class mismatch

단일 seed123 모델에서 classes/meta companion 파일을 찾지 못해 101-class로 로드했다. companion 탐색 로직을 보강했다.

## Appendix D. 제출용 핵심 수치 모음

- K-Food class 수: 56
- 최고 연구 모델: 7-model hflip weighted ensemble
- 최고 연구 모델 Top-1: 92.0238%
- 최고 연구 모델 Top-3: 97.9464%
- 최고 연구 모델 Macro F1: 92.0038%
- 검증 sample 수: 6,720
- 정답 수: 6,184
- Render Free 운영 모델: Food-LeWM B0 seed123 fixed_v1 ft10
- Render Free 운영 모델 Top-1: 88.2887%
- Render Free 운영 모델 Top-3: 96.5179%
- Render Free 운영 모델 Macro F1: 88.2682%
- CGM 30m enriched calibrated MAE: 12.998
- CGM 60m enriched calibrated MAE: 22.633
- CGM 90m enriched calibrated MAE: 29.606
- Frontend hosting: Vercel
- Backend hosting: Render Docker
- Backend health final: classifier_ready=true, predictor_ready=true, classifier_error=null

## Appendix E. 장문 설명: 왜 이 구조가 합리적인가

FoodSugar AI는 모델 연구와 제품 배포가 동시에 진행된 프로젝트이기 때문에, 최고 성능 모델과 실제 무료 배포 모델이 다르다. 이는 모순이 아니라 현실적인 engineering trade-off다. 연구 단계에서는 validation 성능을 극대화하기 위해 7-model ensemble을 구성했고, 이 ensemble은 92%를 넘겼다. 그러나 무료 Render 서버는 512MB 메모리 제한이 있어 7개 PyTorch 모델을 한 번에 올릴 수 없다. 따라서 제출 보고서에서는 research best와 deployed free-tier model을 반드시 분리해서 설명해야 한다.

혈당 기능 역시 단순 회귀 모델을 만드는 데서 끝나지 않았다. low/high glucose 구간에서 bias가 있다는 문제를 발견했고, 이를 range-aware calibration과 event classifier로 보완했다. 특히 high glucose를 낮게 예측하거나 low glucose를 높게 예측하는 경향은 사용자에게 잘못된 안심을 줄 수 있으므로, range-specific residual calibration과 uncertainty interval을 도입했다. 이 선택은 모델 성능뿐 아니라 안전 UX 관점에서도 중요하다.

웹앱 UX는 의료기기처럼 보이지 않도록 wellness dashboard 방향을 채택했다. 혈당이라는 민감한 주제를 다루지만, 앱의 역할은 진단이나 치료가 아니라 식습관 관리 참고이기 때문이다. 따라서 결과는 danger label이 아니라 낮음/주의/높음으로 표현하고, hypo/hyper는 가능성 신호라고 표현한다. 이 접근은 기능의 신뢰성을 낮추는 것이 아니라 사용자가 결과의 한계를 올바르게 이해하게 하는 장치다.

배포 과정에서 가장 큰 교훈은 머신러닝 모델은 학습 성능뿐 아니라 artifact packaging, memory budget, cold start, environment variable, source badge, fallback policy까지 함께 설계해야 실제 서비스가 된다는 점이다. 로컬에서 잘 되는 모델도 서버 메모리 제한, wheel size, function bundle limit, checkpoint 경로 문제로 실패할 수 있다. FoodSugar AI는 이러한 문제를 하나씩 해결하며 실제 외부 URL에서 접근 가능한 상태까지 도달했다.

### Appendix F.1. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.2. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.3. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.4. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.5. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.6. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.7. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.8. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.9. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.10. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.11. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.12. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.13. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.14. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.15. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.16. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.17. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.18. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.19. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.20. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.21. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.22. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.23. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.24. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.25. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.26. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.27. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.28. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.29. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.30. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.31. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.32. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.33. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.34. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.35. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.36. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.37. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.38. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.39. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.40. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.41. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.42. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.43. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.44. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.45. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.46. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.47. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.48. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

### Appendix F.49. 세부 설계 메모

- 이미지 분류: class order와 checkpoint metadata가 일치해야 한다. ensemble member마다 classes json을 명시적으로 확인하는 이유는 서로 다른 class index가 섞이면 softmax 평균이 의미 없어지기 때문이다.
- 영양성분: GI proxy는 실제 임상 측정값이 아니라 보수적 참고값이다. 따라서 UI에서는 점수를 확정적 혈당 반응으로 설명하지 않고 영양성분 기반 참고 신호로 설명한다.
- CGM 예측: long-horizon feature는 90분 예측에서 의미가 있지만 입력 readings가 충분해야 한다. 5분 간격 40개 정도가 있으면 180분 rolling feature를 안정적으로 만들 수 있다.
- 배포: Render Free에서는 sleep과 cold start가 있다. 첫 요청이 느린 것은 실패가 아니라 free-tier 특성이다. 다만 사용성 측면에서는 유료 플랜 또는 keep-alive 전략을 검토할 수 있다.
- 프론트 UX: mock fallback은 숨기면 안 된다. 사용자가 실제 모델 결과와 데모 데이터를 구분할 수 있도록 source badge와 notice를 표시해야 한다.

이 메모는 제출서류에서 세부 구현 의도를 설명할 때 사용할 수 있다. 프로젝트는 단순히 모델 정확도를 높이는 데 그치지 않고, 데이터 품질, 사용자 해석, 안전 문구, 비용 제약, 배포 가능성까지 함께 다루었다. 이러한 점은 실제 서비스형 AI 프로젝트에서 중요하게 평가될 수 있다.

