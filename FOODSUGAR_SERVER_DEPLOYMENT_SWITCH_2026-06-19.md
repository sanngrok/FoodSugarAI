# FoodSugar AI 서버형 백엔드 배포 전환 정리

작성일: 2026-06-19

## 목적

기존 Vercel Function 백엔드는 Python 함수 번들 제한 때문에 다음 기능을 온전히 실행하기 어렵다.

- PyTorch / timm 기반 7-model hflip weighted ensemble
- `data/models/*.pt` checkpoint 로딩
- pandas / scikit-learn 기반 CGM forecasting
- enriched CGM event classifier / prediction interval / range-aware calibration

따라서 백엔드는 Docker 기반 서버형 배포로 전환한다.

## 추가된 서버형 배포 파일

- `Dockerfile`
  - `python:3.12-slim` 기반 FastAPI 서버 실행
  - `requirements.txt` 전체 설치
  - `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}` 실행
  - 시작 전 `scripts/download_server_artifacts.py`로 모델 artifact 준비

- `.dockerignore`
  - raw data, reports, frontend build, local cache 제외
  - Docker image는 코드 중심으로 만들고, 큰 모델은 artifact bundle로 주입

- `render.yaml`
  - Render Docker web service용 설정
  - `/health` health check
  - `FOODSUGAR_MODEL_BUNDLE_URL` 환경변수 자리 포함

- `railway.json`
  - Railway Dockerfile 배포용 설정
  - `/health` health check

- `scripts/create_server_artifact.py`
  - 운영 서버에 필요한 모델/데이터만 tar.gz로 묶음
  - 생성 결과: `artifacts/foodsugar_server_artifacts.tar.gz`

- `scripts/download_server_artifacts.py`
  - 서버 시작 시 `FOODSUGAR_MODEL_BUNDLE_URL`이 있으면 bundle 다운로드 후 압축 해제
  - 로컬에 artifact가 이미 있으면 다운로드 생략

## 생성된 서버 artifact

실행 명령:

```bash
python3 scripts/create_server_artifact.py
```

생성 결과:

```text
artifacts/foodsugar_server_artifacts.tar.gz
크기: 약 205.2 MB
파일 수: 42개
```

포함 내용:

- `config/kfood_production_ensemble_config.json`
- 7-model weighted ensemble checkpoint / metadata / class json
- `data/models/xgboost_sugar.pkl`
- `data/processed/kfood_nutrition_db.json`
- `data/processed/nutrition_db_real.json`
- `data/processed/glucose_models/*`
- `data/processed/glucose_models_enriched/*`

## 로컬 서버형 검증 결과

실행:

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8010
```

확인 결과:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "classifier_ready": true,
  "predictor_ready": true
}
```

서버 로그에서 확인된 내용:

- `food_lewm_b0`
- `b0_seed123_fixed_v1`
- `b3_full_fixed_v1`
- `b0_seed7_fixed_v1`
- `b3_probe_fixed_v1`
- `b3_cont_fixed_v1`
- `b0_supervised_only`

위 7개 ensemble member가 모두 로드됨.

## API 검증

### `/predict/glucose-risk`

비빔밥 예시 입력 결과:

```json
{
  "score": 52.18,
  "level": "주의"
}
```

### `/predict/cgm-forecast-enriched-events`

40개 5분 간격 CGM readings + meal/bolus/basal 이벤트 입력 결과:

```json
{
  "predictions_mg_dl": {
    "30": 150.55,
    "60": 138.8,
    "90": 143.06
  },
  "calibrated_predictions_mg_dl": {
    "30": 150.29,
    "60": 137.91,
    "90": 141.21
  },
  "prediction_intervals_mg_dl": {
    "30": [118.05, 182.53],
    "60": [84.36, 191.46],
    "90": [73.15, 209.27]
  }
}
```

주의:

- 현재 enriched 모델은 long-horizon feature를 사용하므로 13개 readings만으로는 부족할 수 있다.
- 180분 rolling feature를 안정적으로 만들려면 5분 간격 기준 약 40개 readings를 보내는 것이 안전하다.

## 테스트 결과

문법 확인:

```bash
python3 -m py_compile scripts/create_server_artifact.py scripts/download_server_artifacts.py api/main.py
```

통과.

API / CGM 관련 테스트:

```bash
python3 -m pytest tests/test_api.py tests/test_glucose_api_uncertainty.py tests/test_enriched_events_api_safety.py -q
```

결과:

```text
15 passed
```

## 실제 클라우드 배포 절차

### 1. 모델 bundle 업로드

`artifacts/foodsugar_server_artifacts.tar.gz`를 다음 중 하나에 업로드한다.

- Render private/static file
- Railway volume 또는 object storage
- S3 / Cloudflare R2
- GitHub Release asset

업로드 후 다운로드 가능한 URL을 준비한다.

### 2. Render 배포

Render에서 GitHub repo를 연결하고 `render.yaml`을 사용한다.

환경변수:

```text
FOODSUGAR_MODEL_BUNDLE_URL=<artifact tar.gz 다운로드 URL>
PORT=8000
USE_XGBOOST_PREDICTOR_MODEL=false
CLASSIFIER_MODE=single
CLASSIFIER_MODEL_PATH=data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
```

Render Free 512MB 인스턴스에서는 7-model weighted ensemble이 메모리 초과로 실패할 수 있다.
무료 플랜에서는 `CLASSIFIER_MODE=single`을 사용하고, 7-model 92% ensemble은 최소 1GB 이상 RAM이 있는 유료 인스턴스에서 사용한다.

배포 후 확인:

```bash
curl https://<render-backend-url>/health
```

기대:

```json
{
  "classifier_ready": true,
  "predictor_ready": true
}
```

### 3. Railway 배포

Railway에서 GitHub repo를 연결하면 `railway.json`과 `Dockerfile`을 사용한다.

환경변수:

```text
FOODSUGAR_MODEL_BUNDLE_URL=<artifact tar.gz 다운로드 URL>
PORT=8000
USE_XGBOOST_PREDICTOR_MODEL=false
```

### 4. 프론트엔드 연결 변경

서버형 백엔드 URL이 확정되면 Vercel frontend 프로젝트의 환경변수를 교체한다.

```text
VITE_API_BASE_URL=https://<server-backend-url>
```

그 뒤 frontend를 다시 production deploy한다.

## 현재 상태

- Vercel 경량 백엔드: 유지됨
  - `/predict/glucose-risk` 가능
  - PyTorch classifier / CGM full forecast는 제한됨

- 서버형 백엔드 준비: 완료
  - Docker 배포 파일 생성
  - Render/Railway 설정 생성
  - 운영 model artifact bundle 생성
  - 로컬 서버형 실행 검증 완료
  - classifier_ready true 확인
  - enriched CGM 예측 확인

## 남은 작업

1. 사용 플랫폼 선택: Render 또는 Railway 권장
2. `artifacts/foodsugar_server_artifacts.tar.gz` 업로드
3. `FOODSUGAR_MODEL_BUNDLE_URL` 환경변수 등록
4. 서버형 백엔드 배포
5. 새 백엔드 URL로 Vercel frontend `VITE_API_BASE_URL` 교체
6. 프론트 재배포
7. 실제 음식 이미지 업로드 end-to-end 테스트
