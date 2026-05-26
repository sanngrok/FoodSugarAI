# FoodSugar AI

음식 이미지를 **EfficientNet-B0**으로 분류하고, 영양정보 기반 **XGBoost**로 혈당 위험도(낮음 / 주의 / 위험)를 예측하는 AI 시스템.

```
이미지 업로드
     │
     ▼
EfficientNet-B0 (Food-101, 101 클래스)
     │  food_key + confidence
     ▼
영양정보 DB 조회 (100g 기준: 칼로리, 탄수화물, 당류, GI...)
     │  NutritionInfo
     ▼
XGBoost 분류기
     │
     ▼
혈당 위험도: 낮음 ✅ / 주의 ⚠️ / 위험 🚨
```

## 프로젝트 구조

```
foodsugar-ai/
├── config/
│   └── settings.py            # Pydantic 설정 (경로, 하이퍼파라미터)
├── data/
│   ├── raw/                   # 원본 데이터 (Food-101 등)
│   ├── processed/             # 전처리 완료 데이터
│   └── models/
│       ├── efficientnet_food.pt
│       └── xgboost_sugar.pkl
├── src/
│   ├── classifier/
│   │   ├── food_classifier.py  # EfficientNet-B0 추론 래퍼
│   │   └── train_classifier.py # Fine-tuning 스크립트
│   ├── predictor/
│   │   ├── sugar_predictor.py  # XGBoost 추론 래퍼 + rule-based fallback
│   │   └── train_predictor.py  # XGBoost 학습 스크립트
│   ├── nutrition/
│   │   └── nutrition_db.py     # 음식별 영양정보 DB (101개 음식)
│   └── utils/
│       └── image_utils.py      # 이미지 로드/검증 유틸
├── api/
│   ├── main.py                 # FastAPI 앱 (startup에서 모델 로드)
│   ├── routers/
│   │   ├── health.py           # GET /health
│   │   └── predict.py          # POST /predict/{classify|risk|analyze}
│   └── schemas/
│       └── models.py           # Pydantic 요청/응답 스키마
├── demo/
│   └── app.py                  # Streamlit 데모
├── tests/
│   ├── test_predictor.py
│   └── test_api.py
└── requirements.txt
```

## 빠른 시작

### 1. 환경 설정

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. XGBoost 모델 학습 (합성 데이터)

학습된 `.pkl` 파일이 없으면 자동으로 rule-based fallback이 동작합니다.
제대로 된 XGBoost 모델을 사용하려면:

```bash
python -m src.predictor.train_predictor --synthetic
# → data/models/xgboost_sugar.pkl 생성
```

### 3. EfficientNet-B0 Fine-tuning (선택)

Food-101 데이터셋 다운로드 후 실행:

```bash
python -m src.classifier.train_classifier \
    --data-dir ./data/raw \
    --epochs 10 \
    --batch-size 64
# → data/models/efficientnet_food.pt 생성
```

모델 파일 없이도 ImageNet pretrained 가중치로 동작하나 정확도는 낮습니다.

### 4. FastAPI 서버 실행

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 5. Streamlit 데모 실행

```bash
streamlit run demo/app.py
```

## API 엔드포인트

| Method | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 서버 및 모델 상태 확인 |
| POST | `/predict/classify` | 이미지 → 음식 분류 (top-5) |
| POST | `/predict/risk` | 영양정보 → 혈당 위험도 |
| POST | `/predict/analyze` | 이미지 → 분류 → 영양조회 → 위험도 통합 |

### `/predict/analyze` 예시

```bash
curl -X POST http://localhost:8000/predict/analyze \
  -F "file=@pizza.jpg" \
  -F "portion_g=200"
```

응답:
```json
{
  "classification": {
    "food_key": "pizza",
    "food_name_ko": "피자",
    "confidence": 0.89,
    "top5": [["pizza", 0.89], ...]
  },
  "nutrition": {
    "calories": 266, "carbs": 33, "sugar": 3.5,
    "glycemic_index": 60, "portion_g": 200, ...
  },
  "risk": {
    "risk_level": 1,
    "risk_label": "주의",
    "risk_emoji": "⚠️",
    "probabilities": {"낮음": 0.15, "주의": 0.65, "위험": 0.20},
    "serving_advice": "섭취량을 절반으로 줄이거나 단백질·채소와 함께 드세요."
  }
}
```

## 테스트

```bash
pytest tests/ -v
```

## 모델 상세

### EfficientNet-B0 (분류)

- 라이브러리: `timm`
- 데이터셋: Food-101 (101 클래스, 75,750 학습 / 25,250 검증)
- 전처리: RandomResizedCrop → ColorJitter → Normalize(ImageNet)
- 전략: 헤드만 워밍업(2 epoch) → 전체 unfreeze fine-tuning

### XGBoost (위험도)

- 입력 피처 (7개): 칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유, GI 지수
- 출력: 0=낮음, 1=주의, 2=위험
- 학습: 5-Fold StratifiedKFold, F1-macro 평가
- Fallback: 모델 파일 없을 때 당류·GI·탄수화물 기반 규칙으로 대체
