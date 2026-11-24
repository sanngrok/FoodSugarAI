# FoodSugarAI

음식 사진 한 장으로 **한국 음식 56종을 분류**하고, 영양성분을 바탕으로 **혈당 부담 참고 점수(0~100)** 를 보여 주는 웰니스 앱입니다. 연속혈당측정(CGM) 값으로 **30/60/90분 뒤 혈당 범위를 예측**하는 기능도 포함합니다.

> 이 프로젝트의 혈당 관련 결과는 식습관 관리를 위한 **참고용 정보**이며, 의료 진단이나 치료 지침이 아닙니다.

| | 주소 |
|---|---|
| 웹앱 (Vercel) | https://frontend-jade-theta-40.vercel.app |
| 백엔드 API (Render) | https://foodsugarai.onrender.com |
| API 문서 (Swagger) | https://foodsugarai.onrender.com/docs |

백엔드는 한동안 요청이 없으면 잠들기 때문에, 첫 요청은 1~2분 걸릴 수 있습니다.

## 동작 흐름

```
음식 사진 업로드
     │
     ▼
음식 분류 (K-Food 56 클래스, EfficientNet 계열)
     │  음식명 + 확신도 + top-5
     ▼
영양성분 DB 조회 (100g 기준: 칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유, GI)
     │
     ▼
혈당 부담 참고 점수 0~100  →  낮음 / 주의 / 높음


최근 CGM 값 (5분 간격) + 식사·인슐린·운동 기록
     │
     ▼
30 / 60 / 90분 뒤 혈당 예측  +  예측 구간  +  저혈당·고혈당 가능성 신호
```

두 흐름은 서로 독립적입니다. 웹앱의 예측 화면은 현재 앱에 들어 있는 샘플 CGM 값으로 모델을 호출합니다.

## 현재 성능

### 음식 분류 (K-Food 56 클래스, 검증 6,720장)

| 모델 | Top-1 | Top-3 | Macro F1 | 쓰이는 곳 |
|---|---:|---:|---:|---|
| 4개 모델 가중 앙상블 (좌우 반전 TTA) | 91.99% | 97.95% | 91.97% | 로컬 기본값 |
| 단일 모델 (Food-LeWM B0, seed123) | 88.29% | 96.52% | 88.27% | 실제 서버 (메모리 512MB 제한) |

앙상블 가중치는 점수를 잰 것과 같은 검증 세트에서 골랐기 때문에 91.99%는 다소 낙관적인 수치입니다. 별도 holdout에서의 재검증은 아직 하지 않았습니다.

원래는 7개 모델(92.02%, 6,184/6,720)이었는데, 가중치 합이 약 1%였던 3개(`b3_probe_fixed_v1`, `b3_cont_fixed_v1`, `b0_supervised_only`)를 뺐습니다. 검증 세트에서 결과가 바뀐 사진은 4장(1장 개선, 3장 악화, 모두 1·2등 확률이 거의 같던 경우)이고, CPU 추론은 사진당 93ms에서 50ms로 빨라졌습니다.

### CGM 예측 (OhioT1DM, 테스트 29,536건)

| 예측 시점 | 오차 (MAE) | "현재 값 유지" 기준 대비 | R² |
|---|---:|---:|---:|
| 30분 | 13.0 mg/dL | 23% 감소 | 0.905 |
| 60분 | 22.6 mg/dL | 21% 감소 | 0.735 |
| 90분 | 29.6 mg/dL | 20% 감소 | 0.564 |

- 고혈당 가능성 신호의 ROC-AUC는 30/60/90분 기준 0.975 / 0.927 / 0.869입니다.
- 저혈당 가능성 신호는 놓치지 않는 쪽으로 맞춰져 있어 오경보가 많습니다 (90분 기준 precision 0.16, recall 0.64).
- 90분 예측은 불확실성이 커서, 화면에서는 단일 수치보다 범위를 먼저 보여 줍니다.

근거 파일은 `reports/b3/verified_92_hflip_7model_weighted_2026_05_16/`와 `reports/glucose_forecasting/test_final_*.csv`에 있습니다.

## 프로젝트 구조

```
FoodSugarAI/
├── api/                      # FastAPI 백엔드
│   ├── main.py               #   앱 진입점, 시작 시 모델 로드
│   ├── routers/              #   /health, /predict/*
│   └── schemas/models.py     #   요청/응답 스키마
├── src/
│   ├── classifier/           # 음식 분류 모델 (단일, 앙상블, Food-LeWM) 및 학습 코드
│   ├── nutrition/            # 영양성분 DB 조회
│   ├── glucose/              # 혈당 부담 점수(risk.py), CGM 예측(forecasting.py), OhioT1DM 처리
│   ├── predictor/            # 초기 위험도 예측기 (규칙 기반, XGBoost 선택)
│   └── data/, utils/         # 데이터 준비, 이미지 유틸
├── config/
│   ├── settings.py                            # 환경변수 기반 설정
│   └── kfood_production_ensemble_config.json  # 4개 모델 앙상블 구성과 가중치
├── frontend/                 # React + Vite 웹앱
├── scripts/                  # 학습, 평가, 데이터 점검, 배포용 모델 묶음 스크립트
├── tests/                    # 백엔드 테스트 (pytest)
├── data/
│   ├── models/               # 체크포인트 (git 제외), 클래스/메타 JSON
│   ├── processed/            # 영양 DB, CGM 모델 (git 제외)
│   └── raw/                  # 원본 데이터 (git 제외)
├── reports/                  # 실험, 평가, 검증 결과
├── docs/                     # 안전 문구, 개인정보, 파일럿, 외부 검증 계획
├── Dockerfile, render.yaml, railway.json   # 서버형 백엔드 배포
└── requirements.txt
```

모델 체크포인트와 데이터는 용량 때문에 git에 들어 있지 않습니다. 아래 "모델 파일 받기"를 참고하세요.

## 백엔드 실행

Python 3.12 기준입니다 (3.11 이상 필요).

### 1. 환경 설정

```bash
python3.12 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt`의 scikit-learn, numpy, scipy, pandas, joblib은 버전이 고정되어 있습니다. 저장된 CGM 모델은 **scikit-learn 1.8.0에서만** 읽히므로, 모델을 다시 학습해 저장하기 전에는 이 버전을 올리지 마세요.

### 2. 모델 파일 받기

서버 실행에 필요한 파일(분류 체크포인트 7개, 영양 DB, CGM 모델)은 GitHub Release에 묶음으로 올라가 있습니다. 약 205MB이며, 프로젝트 루트에서 실행하면 `data/` 아래에 풀립니다.

```bash
FOODSUGAR_MODEL_BUNDLE_URL=https://github.com/sanngrok/FoodSugarAI/releases/download/foodsugar-model-v1/foodsugar_server_artifacts.tar.gz \
  python scripts/download_server_artifacts.py
```

### 3. 서버 실행

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

- 상태 확인: http://localhost:8000/health
- Swagger UI: http://localhost:8000/docs

`/health`에서 `classifier_ready`, `predictor_ready`, `cgm_forecast_ready`가 모두 `true`면 정상입니다. 문제가 있으면 `classifier_error`나 `cgm_forecast_error`에 원인이 표시됩니다. 모델 파일이 없어도 서버는 뜨지만, 음식 분류는 색상 기반 추정으로 대체되고 CGM 예측은 503을 반환합니다.

### 주요 환경변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `CLASSIFIER_MODE` | `ensemble` | `ensemble`(4개 모델), `single`(모델 1개), `none`(분류기 끔) |
| `CLASSIFIER_MODEL_PATH` | | `single` 모드에서 쓸 체크포인트 경로 |
| `USE_XGBOOST_PREDICTOR_MODEL` | `false` | `true`면 XGBoost 위험도 모델 사용, 아니면 규칙 기반 |
| `FOODSUGAR_MODEL_BUNDLE_URL` | | 모델 묶음 주소 (서버 시작 시 자동 다운로드에 사용) |
| `FOODSAFETY_API_KEY` | | 식품안전나라 영양성분 API 키 (영양 DB를 다시 만들 때만 필요) |

`.env` 파일에 적어 두면 자동으로 읽습니다. 메모리가 적은 환경에서는 실제 서버와 같은 단일 모델 설정을 쓰세요.

```bash
CLASSIFIER_MODE=single \
CLASSIFIER_MODEL_PATH=data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt \
  uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## 프론트엔드 실행

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

`VITE_API_BASE_URL`은 백엔드 주소입니다. 지정하지 않으면 `http://127.0.0.1:8000`을 씁니다. 이 값은 빌드할 때 앱에 포함되므로, 바꾼 뒤에는 다시 빌드해야 합니다.

백엔드 연결에 실패하면 화면에 "데모 데이터" 배지와 함께 예시 값이 표시되고, 성공하면 "실제 모델 결과" 배지가 표시됩니다.

## API

| Method | 경로 | 설명 |
|---|---|---|
| GET | `/health` | 서버, 분류기, CGM 모델 준비 상태 |
| POST | `/predict/analyze` | 사진 → 분류 → 영양 조회 → 혈당 부담 점수 (웹앱이 쓰는 통합 API) |
| POST | `/predict/classify` | 사진 → 음식 분류 (top-5) |
| POST | `/predict/glucose-risk` | 영양성분 → 혈당 부담 참고 점수 0~100 |
| POST | `/predict/risk` | 영양성분 → 초기 방식의 위험도 (낮음/주의/높음) |
| POST | `/predict/cgm-forecast` | 최근 CGM 값 → 30/60/90분 예측 (최소 13개 값) |
| POST | `/predict/cgm-forecast-enriched` | CGM 값 + 가공된 식사·인슐린 feature → 보정 예측, 구간, 가능성 신호 |
| POST | `/predict/cgm-forecast-enriched-events` | CGM 값 + 식사·인슐린·운동 원본 기록 → 위와 같은 결과 (웹앱이 쓰는 API) |

enriched 예측 두 가지는 5분 간격 값이 25개 이상(2시간 분량) 있어야 하고, 그보다 적으면 422를 반환합니다. 모델이 3시간 분량의 feature까지 쓰므로 37개를 보내는 것을 권장합니다. 웹앱도 37개를 보냅니다.

### `/predict/analyze` 예시

```bash
curl -X POST http://localhost:8000/predict/analyze \
  -F "file=@bibimbap.jpg" \
  -F "portion_g=150"
```

응답 (일부 생략):

```json
{
  "classification": {
    "food_key": "비빔밥",
    "food_name_ko": "비빔밥",
    "confidence": 0.91,
    "top5": [["비빔밥", 0.91], ["김치볶음밥", 0.03]]
  },
  "nutrition": {
    "food_name": "비빔밥",
    "calories": 171.1, "carbs": 29.74, "sugar": 1.98,
    "protein": 4.63, "fat": 3.7, "fiber": 0.96,
    "glycemic_index": 68.0, "portion_g": 150.0
  },
  "risk": { "risk_label": "주의", "serving_advice": "..." },
  "glucose_risk": {
    "score": 41.98,
    "level": "주의",
    "factors": { "scaled_carbs_g": 44.61 },
    "reference_notice": "이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다. ..."
  }
}
```

화면에는 `glucose_risk`의 점수와 수준을 우선 표시합니다.

### `/predict/cgm-forecast-enriched-events` 예시

```bash
curl -X POST http://localhost:8000/predict/cgm-forecast-enriched-events \
  -H "Content-Type: application/json" \
  -d '{
    "readings": [
      {"timestamp": "2026-05-26T12:00:00", "glucose_mg_dl": 100},
      {"timestamp": "2026-05-26T12:05:00", "glucose_mg_dl": 101}
    ],
    "meals": [{"timestamp": "2026-05-26T15:00:00", "carbs_g": 58}]
  }'
```

위 `readings`는 형식만 보여 주는 것이고, 실제로는 25개 이상을 보내야 합니다. 응답에는 `predictions_mg_dl`, `calibrated_predictions_mg_dl`, `prediction_intervals_mg_dl`, `uncertainty_level`, `event_probabilities`, `risk_flags`가 들어 있습니다.

## 테스트

```bash
pytest                      # 백엔드
cd frontend && npm run test # 프론트엔드
```

- 모델 파일이 `data/` 아래에 있어야 통과하는 백엔드 테스트가 있습니다. 먼저 "모델 파일 받기"를 실행하세요.
- OhioT1DM 원본으로 만든 학습용 CSV가 필요한 테스트 4개는 그 데이터가 없으면 실패합니다.
- 일부 테스트는 실행할 때 `reports/glucose_forecasting/`의 점검 보고서를 다시 씁니다. 데이터 없이 돌리면 보고서가 "fail"로 덮어써지니, 그럴 때는 `git restore reports/glucose_forecasting`으로 되돌리세요.

## 배포

### 백엔드 (Render, Docker)

`Dockerfile`이 CPU용 PyTorch와 `requirements.txt`를 설치하고, 시작할 때 `scripts/download_server_artifacts.py`로 모델 묶음을 받은 뒤 서버를 띄웁니다. 환경변수는 `render.yaml`을 참고하세요.

1. `main`에 push합니다.
2. `render.yaml`이 `autoDeploy: false`라서 자동 배포되지 않습니다. Render 대시보드에서 **Manual Deploy**를 누릅니다.
3. 배포 후 `/health`에서 세 가지 준비 상태가 모두 `true`인지 확인합니다.

메모리 512MB 인스턴스에서는 앙상블을 올릴 수 없어 `CLASSIFIER_MODE=single`로 운영합니다. 1GB 이상이면 `ensemble`로 바꿀 수 있습니다.

### 프론트엔드 (Vercel CLI)

GitHub 연동이 아니라 CLI로 배포합니다. push만으로는 반영되지 않습니다.

```bash
cd frontend
npx vercel --prod
```

`--prod`가 없으면 미리보기로만 올라갑니다. `VITE_API_BASE_URL`은 Vercel 프로젝트의 환경변수에 저장된 값이 쓰입니다.

루트의 `app.py`, `vercel.json`, `requirements-vercel.txt`는 초기에 시도한 Vercel용 경량 백엔드 설정입니다. PyTorch와 CGM 모델을 올릴 수 없어 현재 웹앱은 사용하지 않습니다.

### 모델 묶음 새로 만들기

모델을 다시 학습했다면 묶음을 새로 만들어 Release에 올리고 `FOODSUGAR_MODEL_BUNDLE_URL`을 바꿉니다.

```bash
python scripts/create_server_artifact.py   # → artifacts/foodsugar_server_artifacts.tar.gz
```

## 학습과 평가

학습용 데이터는 저장소에 없습니다. 음식 이미지는 `data/raw/korean_food_fixed_v1/{train,val}`(56 클래스, 학습 49,243장 / 검증 6,720장) 구조를 쓰고, CGM 데이터는 OhioT1DM을 별도로 받아야 합니다. 각 스크립트의 옵션은 `--help`로 확인하세요.

| 스크립트 | 용도 |
|---|---|
| `scripts/train_food_lewm_classifier.py` | Food-LeWM 계열 56 클래스 분류기 학습 |
| `scripts/eval_fixed_weight_ensemble.py` | 고정 가중치 앙상블 평가 |
| `scripts/validate_kfood_production_config.py` | 운영 앙상블 구성 사전 점검 |
| `scripts/build_kfood_nutrition_db.py` | 56 클래스용 영양성분 DB 생성 |
| `scripts/prepare_ohiot1dm_cgm.py` | OhioT1DM XML → CGM 시계열 CSV |
| `scripts/train_glucose_forecaster.py` | 30/60/90분 CGM 예측 모델 학습과 평가 |
| `scripts/validate_glucose_artifacts.py` | CGM 모델 파일과 데이터 누수 점검 |

## 문서

- `FOODSUGAR_FINAL_PROJECT_REPORT_2026-06-20.md`: 프로젝트 전체 결과 보고서
- `FOODSUGAR_MODEL_TRAINING_PROCESS_SUMMARY_2026-05-24.md`: 모델 학습 과정
- `FOODSUGAR_SERVER_DEPLOYMENT_SWITCH_2026-06-19.md`: 서버 배포 구성
- `docs/`: 안전 문구 가이드, 개인정보·로그 정책, 파일럿 계획, 외부 검증 계획
- `reports/`: 실험별 평가 결과와 점검 보고서

## 한계

- 혈당 부담 점수는 영양성분과 GI 추정값으로 계산한 참고 지표이며, 개인의 실제 혈당 반응을 측정한 값이 아닙니다.
- CGM 예측은 OhioT1DM(1형 당뇨 환자 데이터)으로만 학습하고 평가했습니다. 다른 데이터에서의 성능은 검증하지 않았습니다.
- 웹앱의 예측 화면은 사용자의 혈당이 아니라 앱에 들어 있는 샘플 CGM 값을 입력으로 쓰고, 기록 화면은 예시 데이터를 보여 줍니다.
- 실제 서버의 음식 분류는 단일 모델(Top-1 88.29%)입니다.
