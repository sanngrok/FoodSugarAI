"""
FoodSugar AI — Streamlit 데모

실행:
    streamlit run demo/app.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가 (상대 import 지원)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import io

import plotly.graph_objects as go
import requests
import streamlit as st
from PIL import Image

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FoodSugar AI",
    page_icon="🍱",
    layout="wide",
)

# ── 스타일 ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.risk-card {
    padding: 1.2rem 1.5rem;
    border-radius: 12px;
    margin: 0.5rem 0;
    font-size: 1.05rem;
    font-weight: 600;
}
.risk-low    { background:#d5f5e3; color:#1e8449; border-left: 6px solid #27ae60; }
.risk-caution{ background:#fef9e7; color:#9a6e00; border-left: 6px solid #f39c12; }
.risk-high   { background:#fdedec; color:#922b21; border-left: 6px solid #e74c3c; }
</style>
""", unsafe_allow_html=True)


# ── 유틸 ────────────────────────────────────────────────────────────────────
def call_analyze(image_bytes: bytes, portion_g: float) -> dict | None:
    try:
        resp = requests.post(
            f"{API_URL}/predict/analyze",
            files={"file": ("food.jpg", image_bytes, "image/jpeg")},
            data={"portion_g": portion_g},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("API 서버에 연결할 수 없습니다. `uvicorn api.main:app --reload` 를 먼저 실행하세요.")
        return None
    except Exception as e:
        st.error(f"오류: {e}")
        return None


def call_risk_direct(nutrition: dict) -> dict | None:
    try:
        resp = requests.post(
            f"{API_URL}/predict/risk",
            json=nutrition,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("API 서버에 연결할 수 없습니다.")
        return None
    except Exception as e:
        st.error(f"오류: {e}")
        return None


def render_risk_card(risk: dict) -> None:
    level = risk["risk_level"]
    cls = ["risk-low", "risk-caution", "risk-high"][level]
    emoji = risk["risk_emoji"]
    label = risk["risk_label"]
    st.markdown(
        f'<div class="risk-card {cls}">{emoji} 혈당 위험도: {label}</div>',
        unsafe_allow_html=True,
    )
    st.caption(risk["serving_advice"])


def render_prob_chart(probs: dict) -> None:
    labels = list(probs.keys())
    values = [v * 100 for v in probs.values()]
    colors = ["#2ecc71", "#f39c12", "#e74c3c"]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{v:.1f}%" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        title="위험도별 확률",
        yaxis=dict(range=[0, 110], title="%"),
        xaxis_title="위험도",
        height=300,
        margin=dict(t=40, b=20),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


def render_nutrition_table(nutrition: dict | None) -> None:
    if not nutrition:
        return
    rows = {
        "칼로리": f"{nutrition['calories']} kcal",
        "탄수화물": f"{nutrition['carbs']} g",
        "당류": f"{nutrition['sugar']} g",
        "단백질": f"{nutrition['protein']} g",
        "지방": f"{nutrition['fat']} g",
        "식이섬유": f"{nutrition['fiber']} g",
        "GI 지수": str(nutrition['glycemic_index']),
        "섭취량": f"{nutrition['portion_g']} g",
    }
    import pandas as pd
    df = pd.DataFrame(list(rows.items()), columns=["항목", "값 (100g 기준)"])
    st.dataframe(df, hide_index=True, use_container_width=True)


def render_feature_importance(fi: dict | None) -> None:
    if not fi:
        return
    import pandas as pd
    df = pd.DataFrame(
        sorted(fi.items(), key=lambda x: x[1], reverse=True),
        columns=["피처", "중요도"],
    )
    fig = go.Figure(go.Bar(
        x=df["중요도"],
        y=df["피처"],
        orientation="h",
        marker_color="#3498db",
    ))
    fig.update_layout(
        title="XGBoost 피처 중요도",
        height=280,
        margin=dict(t=40, b=20),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)


# ── 메인 UI ──────────────────────────────────────────────────────────────────
st.title("🍱 FoodSugar AI")
st.caption("음식 이미지 → EfficientNet-B0 분류 → XGBoost 혈당 위험도 예측")

tab1, tab2, tab3 = st.tabs(["📷 이미지 분석", "🍽️ 음식 선택 분석", "📋 영양정보 직접 입력"])

# ── Tab 1: 이미지 분석 ────────────────────────────────────────────────────────
with tab1:
    col_upload, col_result = st.columns([1, 1], gap="large")

    with col_upload:
        st.subheader("이미지 업로드")
        uploaded = st.file_uploader(
            "음식 사진을 올려주세요 (JPG/PNG)",
            type=["jpg", "jpeg", "png"],
            key="img_upload",
        )
        portion_g = st.slider("섭취량 (g)", min_value=30, max_value=500,
                               value=150, step=10)

        if uploaded:
            st.image(uploaded, caption="업로드된 이미지", use_container_width=True)

        analyze_btn = st.button("분석 시작", type="primary",
                                disabled=uploaded is None, key="analyze_btn")

    with col_result:
        st.subheader("분석 결과")

        if analyze_btn and uploaded:
            with st.spinner("분석 중..."):
                result = call_analyze(uploaded.getvalue(), portion_g)

            if result:
                clf = result["classification"]
                risk = result["risk"]
                nutrition = result.get("nutrition")

                st.metric("음식 분류", clf["food_name_ko"],
                          delta=f"신뢰도 {clf['confidence']*100:.1f}%")

                render_risk_card(risk)

                with st.expander("Top-5 분류 결과"):
                    for food_key, prob in clf["top5"]:
                        st.write(f"- **{food_key}**: {prob*100:.1f}%")

                render_prob_chart(risk["probabilities"])

                with st.expander("영양정보 상세"):
                    render_nutrition_table(nutrition)

                with st.expander("XGBoost 피처 중요도"):
                    render_feature_importance(risk.get("feature_importance"))
        else:
            st.info("이미지를 업로드하고 '분석 시작' 버튼을 눌러주세요.")

# ── Tab 2: 음식 선택 분석 (EfficientNet 없이 DB 기반) ───────────────────────────
with tab2:
    st.subheader("음식 선택 → 혈당 위험도 분석")
    st.caption("DB에 등록된 101가지 음식 중 선택하면 영양정보와 혈당 위험도를 즉시 확인합니다.")

    # nutrition_db에서 음식 목록 로드
    try:
        from src.nutrition.nutrition_db import NUTRITION_DB
        food_options = {info.food_name: key for key, info in NUTRITION_DB.items()}
        food_label_list = sorted(food_options.keys())
    except Exception:
        food_options = {}
        food_label_list = []

    col_sel, col_res2 = st.columns([1, 1], gap="large")

    with col_sel:
        selected_food_name = st.selectbox(
            "음식을 선택하세요",
            food_label_list,
            index=food_label_list.index("피자") if "피자" in food_label_list else 0,
        )
        portion_g2 = st.slider("섭취량 (g)", 30, 500, 150, 10, key="portion2")

        # 선택한 음식 영양정보 미리 보기
        if selected_food_name and food_options:
            food_key2 = food_options[selected_food_name]
            from src.nutrition.nutrition_db import get_nutrition
            preview = get_nutrition(food_key2)
            if preview:
                st.markdown("**영양정보 미리보기** (100g 기준)")
                cols = st.columns(4)
                cols[0].metric("칼로리", f"{preview.calories} kcal")
                cols[1].metric("당류", f"{preview.sugar} g")
                cols[2].metric("탄수화물", f"{preview.carbs} g")
                cols[3].metric("GI 지수", str(preview.glycemic_index))

        select_btn = st.button("혈당 위험도 분석", type="primary", key="select_btn",
                               disabled=not food_label_list)

    with col_res2:
        st.subheader("분석 결과")
        if select_btn and selected_food_name:
            food_key2 = food_options[selected_food_name]
            from src.nutrition.nutrition_db import get_nutrition as gn
            info2 = gn(food_key2)
            if info2:
                payload2 = {
                    "food_name": info2.food_name,
                    "calories": info2.calories,
                    "carbs": info2.carbs,
                    "sugar": info2.sugar,
                    "protein": info2.protein,
                    "fat": info2.fat,
                    "fiber": info2.fiber,
                    "glycemic_index": info2.glycemic_index,
                    "portion_g": portion_g2,
                }
                with st.spinner("XGBoost 예측 중..."):
                    risk2 = call_risk_direct(payload2)

                if risk2:
                    st.markdown(f"**{selected_food_name}** ({portion_g2}g 기준 분석")
                    render_risk_card(risk2)
                    render_prob_chart(risk2["probabilities"])

                    with st.expander("영양정보 상세"):
                        render_nutrition_table({**payload2})

                    render_feature_importance(risk2.get("feature_importance"))
        else:
            st.info("음식을 선택하고 '혈당 위험도 분석' 버튼을 눌러주세요.")

# ── Tab 3: 영양정보 직접 입력 ──────────────────────────────────────────────────
with tab3:
    st.subheader("영양정보 직접 입력 (100g 기준)")

    col1, col2, col3 = st.columns(3)  # noqa: E741
    with col1:
        food_name = st.text_input("음식명", "사용자 입력 음식")
        calories = st.number_input("칼로리 (kcal)", 0.0, 900.0, 200.0, step=10.0)
        carbs = st.number_input("탄수화물 (g)", 0.0, 200.0, 30.0, step=1.0)
    with col2:
        sugar = st.number_input("당류 (g)", 0.0, 150.0, 10.0, step=0.5)
        protein = st.number_input("단백질 (g)", 0.0, 100.0, 8.0, step=0.5)
        fat = st.number_input("지방 (g)", 0.0, 100.0, 5.0, step=0.5)
    with col3:
        fiber = st.number_input("식이섬유 (g)", 0.0, 50.0, 2.0, step=0.5)
        gi = st.number_input("GI 지수", 0.0, 100.0, 55.0, step=1.0)
        portion = st.number_input("섭취량 (g)", 10.0, 500.0, 100.0, step=10.0)

    if st.button("혈당 위험도 예측", type="primary", key="risk_btn"):
        payload = {
            "food_name": food_name,
            "calories": calories,
            "carbs": carbs,
            "sugar": sugar,
            "protein": protein,
            "fat": fat,
            "fiber": fiber,
            "glycemic_index": gi,
            "portion_g": portion,
        }
        with st.spinner("예측 중..."):
            risk = call_risk_direct(payload)

        if risk:
            render_risk_card(risk)
            render_prob_chart(risk["probabilities"])
            render_feature_importance(risk.get("feature_importance"))

# ── 사이드바: API 상태 ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("API 상태")
    try:
        resp = requests.get(f"{API_URL}/health", timeout=3)
        data = resp.json()
        st.success(f"서버 연결됨 (v{data['version']})")
        st.write(f"- 분류기: {'✅' if data['classifier_ready'] else '❌'}")
        st.write(f"- 예측기: {'✅' if data['predictor_ready'] else '❌'}")
    except Exception:
        st.error("서버 연결 실패")

    st.divider()
    st.header("사용 방법")
    st.markdown("""
1. `uvicorn api.main:app --reload` 실행
2. 음식 사진 업로드
3. 섭취량 설정
4. **분석 시작** 클릭
    """)
    st.divider()
    st.caption("모델 학습 명령어")
    st.code("python -m src.predictor.train_predictor --synthetic", language="bash")
    st.code("python -m src.classifier.train_classifier --data-dir ./data/raw", language="bash")
