from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt, RGBColor


ROOT = Path("/Users/sangrok/foodsugar-ai")
OUT = ROOT / "outputs" / "FoodSugarAI_WE-Meet_3개월_결과보고서_15p.docx"

SCREENSHOTS = {
    "home": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.27.png"),
    "upload": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.39.png"),
    "analysis": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.57.png"),
    "prediction_top": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.20.png"),
    "prediction_chart": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.31.png"),
    "history": Path("/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.48.png"),
}

GREEN = RGBColor(22, 63, 42)
MINT = "E9F4EC"
MINT_DARK = "D8EBDD"
CREAM = "FFF8EA"
ORANGE = RGBColor(159, 91, 35)
GRAY = RGBColor(95, 95, 95)
LIGHT_GRAY = "F3F6F2"
BLACK = RGBColor(25, 25, 25)


def set_run_font(run, size: float | None = None, bold: bool | None = None, color=None):
    run.font.name = "맑은 고딕"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    run._element.rPr.rFonts.set(qn("w:ascii"), "맑은 고딕")
    run._element.rPr.rFonts.set(qn("w:hAnsi"), "맑은 고딕")
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if color is not None:
        run.font.color.rgb = color


def shade_cell(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_text(cell, text: str, *, bold=False, size=8.8, color=BLACK, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    run = p.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def set_cell_border(cell, color="D2DED2"):
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    borders = tc_pr.first_child_found_in("w:tcBorders")
    if borders is None:
        borders = OxmlElement("w:tcBorders")
        tc_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = f"w:{edge}"
        element = borders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            borders.append(element)
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), "4")
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)


def table(doc, headers, rows, widths=None, font_size=8.4):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Cm(w)
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        shade_cell(cell, MINT_DARK)
        set_cell_border(cell)
        set_cell_text(cell, h, bold=True, size=font_size, color=GREEN, align=WD_ALIGN_PARAGRAPH.CENTER)
    for row in rows:
        cells = t.add_row().cells
        for i, value in enumerate(row):
            shade_cell(cells[i], "FFFFFF")
            set_cell_border(cells[i])
            align = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_cell_text(cells[i], str(value), size=font_size, align=align)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return t


def setup_doc():
    doc = Document()
    section = doc.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Mm(17)
    section.bottom_margin = Mm(15)
    section.left_margin = Mm(16)
    section.right_margin = Mm(16)
    section.header_distance = Mm(8)
    section.footer_distance = Mm(8)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "맑은 고딕"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
    normal.font.size = Pt(9.2)
    normal.paragraph_format.line_spacing = 1.12
    normal.paragraph_format.space_after = Pt(3)

    for style_name, size, color in [
        ("Heading 1", 14, GREEN),
        ("Heading 2", 11, GREEN),
        ("Heading 3", 9.8, ORANGE),
    ]:
        style = styles[style_name]
        style.font.name = "맑은 고딕"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "맑은 고딕")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = color
        style.paragraph_format.space_before = Pt(2)
        style.paragraph_format.space_after = Pt(4)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run("FoodSugar AI WE-Meet 결과보고서")
    set_run_font(run, size=8, color=GRAY)
    return doc


def h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    return p


def p(doc, text="", *, bold=False, size=9.2, color=BLACK, align=None, after=3):
    para = doc.add_paragraph()
    if align is not None:
        para.alignment = align
    para.paragraph_format.space_after = Pt(after)
    para.paragraph_format.line_spacing = 1.12
    run = para.add_run(text)
    set_run_font(run, size=size, bold=bold, color=color)
    return para


def bullet(doc, text, level=0, *, bold=False, size=9.0):
    prefix = ["□", "○", "-", "·"][min(level, 3)]
    para = doc.add_paragraph()
    para.paragraph_format.left_indent = Cm(0.0 + 0.45 * level)
    para.paragraph_format.first_line_indent = Cm(-0.18)
    para.paragraph_format.space_after = Pt(2)
    para.paragraph_format.line_spacing = 1.08
    run = para.add_run(f"{prefix} {text}")
    set_run_font(run, size=size, bold=bold)
    return para


def metric_strip(doc, items):
    t = doc.add_table(rows=1, cols=len(items))
    t.autofit = False
    for i, (label, value, note) in enumerate(items):
        c = t.rows[0].cells[i]
        shade_cell(c, MINT if i % 2 == 0 else CREAM)
        set_cell_border(c, "E0E8DD")
        c.text = ""
        p1 = c.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p1.add_run(label)
        set_run_font(r, size=7.8, bold=True, color=GREEN if i % 2 == 0 else ORANGE)
        p2 = c.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p2.paragraph_format.space_after = Pt(0)
        r = p2.add_run(value)
        set_run_font(r, size=15, bold=True, color=GREEN)
        p3 = c.add_paragraph()
        p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p3.add_run(note)
        set_run_font(r, size=7.6, color=GRAY)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def note_box(doc, title, lines, fill=CREAM):
    t = doc.add_table(rows=1, cols=1)
    c = t.rows[0].cells[0]
    shade_cell(c, fill)
    set_cell_border(c, "F0D8B8" if fill == CREAM else "CFDFCF")
    c.text = ""
    p0 = c.paragraphs[0]
    r = p0.add_run(title)
    set_run_font(r, size=9, bold=True, color=ORANGE if fill == CREAM else GREEN)
    for line in lines:
        pp = c.add_paragraph()
        pp.paragraph_format.space_after = Pt(0)
        r = pp.add_run(f"· {line}")
        set_run_font(r, size=8.3, color=BLACK)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)


def add_image(doc, path: Path, width_cm=16.0, caption=""):
    if path.exists():
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        run.add_picture(str(path), width=Cm(width_cm))
        para.paragraph_format.space_after = Pt(2)
    if caption:
        cap = p(doc, caption, size=8, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=1)
        cap.paragraph_format.keep_with_next = True


def page_break(doc):
    doc.add_page_break()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = setup_doc()

    # 1
    p(doc, "WE-Meet 3개월 수행 결과보고서", size=10.5, bold=True, color=ORANGE, align=WD_ALIGN_PARAGRAPH.CENTER, after=2)
    p(doc, "FoodSugar AI", size=27, bold=True, color=GREEN, align=WD_ALIGN_PARAGRAPH.CENTER, after=1)
    p(doc, "음식 이미지 빅데이터 기반 AI 혈당 예측 보조 시스템", size=13, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    metric_strip(doc, [
        ("음식 이미지 분류", "92.02%", "K-Food 56 class validation top1"),
        ("CGM 예측", "30/60/90분", "OhioT1DM 기반 장기 horizon"),
        ("제품 형태", "Web MVP", "FastAPI + React + 안전 UX"),
    ])
    note_box(doc, "핵심 결론", [
        "계획서의 데이터 수집, 모델 개발, 혈당 예측, 통합 데모, 최종 보고 흐름을 실제 코드·모델·웹 화면으로 구현함",
        "음식 분류는 7-model weighted ensemble 운영 후보를 고정하고 API 로딩 구조까지 정리함",
        "혈당 기능은 의료 판단이 아닌 식습관 관리 참고용으로 한정하고, 90분 예측은 범위와 불확실성 중심으로 설계함",
        "서버형 배포 아티팩트와 Render/Railway 설정까지 준비해 시연 이후 운영 전환 경로를 확보함",
    ], fill=MINT)
    table(doc, ["구분", "계획서 목표", "수행 결과"], [
        ["데이터", "음식 이미지·영양 DB·CGM 데이터 확보", "K-Food split, nutrition DB, OhioT1DM enriched time-series 구성"],
        ["AI 모델", "음식 분류 및 혈당 예측 모델 개발", "K-Food 92.02%, CGM 30/60/90분 예측 및 event signal 구현"],
        ["서비스", "API와 데모 통합", "FastAPI, Vite React, mock fallback, 안전 UX 적용"],
        ["검증", "정량 평가 및 보고", "모델 리포트, leakage audit, backend/frontend 테스트 결과 축적"],
    ], widths=[2.6, 6.7, 7.5])
    p(doc, "작성 기준일: 2026. 06. 20. / 작성 근거: 제출 계획서, foodsugar-ai 레포지토리, 누적 작업 기록 및 구현 화면", size=8.2, color=GRAY, align=WD_ALIGN_PARAGRAPH.CENTER)
    page_break(doc)

    # 2
    h(doc, "Ⅰ. 계획 대비 수행 요약")
    p(doc, "초기 계획서는 Phase 0~6으로 실행 흐름을 정의했다. 본 결과보고서는 각 phase가 실제 산출물로 어떻게 전환되었는지 중심으로 정리함.", size=9.2)
    table(doc, ["Phase", "계획서상 핵심 과업", "현재 산출물"], [
        ["0", "개발 환경, GitHub, 데이터 접근권 준비", "Python/FastAPI, React/Vite, Docker, 배포 설정 정리"],
        ["1", "데이터 수집 및 EDA", "K-Food split manifest, class count, OhioT1DM 변환, nutrition DB 구축"],
        ["2", "전처리 및 영양 매핑", "kfood_nutrition_db.json, GI proxy, label patch 및 split audit 수행"],
        ["3", "이미지 분류 모델", "EfficientNet B0/B3, Food-LeWM, 7-model ensemble, 92.02% 운영 후보"],
        ["4", "혈당 예측 모델", "30/60/90분 CGM forecasting, prediction interval, hypo/hyper signal"],
        ["5", "통합 파이프라인 및 데모", "/predict/analyze, /predict/glucose-risk, /predict/cgm-forecast-enriched-events, React 웹 MVP"],
        ["6", "최종 보고 및 발표", "모델·API·UX·배포 리포트, 화면 캡처 포함 결과보고서"],
    ], widths=[1.4, 7.4, 8.0], font_size=8.1)
    h(doc, "수행 방향", 2)
    bullet(doc, "단순 모델 학습보다 음식 인식 → 영양성분 → 혈당 변화 가능성 → 사용자 화면까지 연결되는 end-to-end 가치 전달에 집중함", 0)
    bullet(doc, "의료기기처럼 보이지 않도록 모든 혈당 결과를 참고용·가능성 신호·예측 범위 중심으로 제한함", 0)
    bullet(doc, "모델 검증 결과와 한계를 함께 명시해 제출 보고서의 신뢰도를 높이는 방향으로 정리함", 0)
    note_box(doc, "보고서 관점의 메시지", [
        "계획서의 실험형 과업을 실제 시연 가능한 제품형 구조로 확장함",
        "AI 성능 수치, 안전 문구, UI 화면, 배포 준비를 모두 포함해 전달 가능성을 높임",
    ])
    page_break(doc)

    # 3
    h(doc, "Ⅱ. 3개월 추진 경과")
    table(doc, ["기간", "중점 과업", "주요 결과"], [
        ["1단계", "데이터 구조화 및 기준선 모델", "Food-101/K-Food 기반 분류 파이프라인과 영양성분 조회 구조 마련"],
        ["2단계", "K-Food 성능 고도화", "cleaned split, hard class review, B0/B2/B3 계열 실험 및 ensemble 탐색"],
        ["3단계", "혈당 예측 확장", "OhioT1DM 전처리, 30/60/90분 horizon, long-window feature, interval 구성"],
        ["4단계", "API 통합", "FastAPI startup 모델 로딩, schema 확장, glucose_risk 응답 추가"],
        ["5단계", "웹 MVP 구현", "Home/Analysis/Prediction/History/Settings 화면과 안전 notice 적용"],
        ["6단계", "배포 준비", "Docker 서버형 백엔드, artifact bundle, Render/Railway 설정 작성"],
    ], widths=[2.0, 5.5, 9.3], font_size=8.4)
    h(doc, "주요 마일스톤", 2)
    bullet(doc, "2026.05.16: K-Food 56 class 기준 top1 92.02% 운영 후보 달성", 0)
    bullet(doc, "2026.05.24~25: CGM 장기 예측, validation/test 분리, leakage audit, 안전 포지셔닝 문서화", 0)
    bullet(doc, "2026.05.31~06.02: 프리미엄 웰니스 대시보드 스타일로 프론트 UX 재설계", 0)
    bullet(doc, "2026.06.04~06.05: 이미지 분석 API와 glucose_risk score 기반 표시 우선순위 개선", 0)
    bullet(doc, "2026.06.19: Vercel 제한을 고려해 Docker 서버형 백엔드 배포 전략으로 전환", 0)
    metric_strip(doc, [
        ("리포트 산출", "210MB", "reports/ 누적 결과"),
        ("모델 산출", "747MB", "data/models/"),
        ("서버 아티팩트", "205MB", "배포용 bundle"),
    ])
    page_break(doc)

    # 4
    h(doc, "Ⅲ. 시스템 구조 및 레포지토리 산출물")
    p(doc, "FoodSugar AI는 음식 사진을 입력으로 받아 음식 분류, 영양성분 조회, 혈당 부담 참고 점수, CGM 기반 혈당 변화 가능성 예측을 연결하는 구조로 구현됨.", size=9.2)
    table(doc, ["영역", "주요 경로", "역할"], [
        ["Backend", "api/main.py, api/routers/predict.py", "FastAPI 앱, 음식 분석·혈당 예측 endpoint 제공"],
        ["Classifier", "src/classifier/", "EfficientNet/Food-LeWM 추론 및 ensemble 구성"],
        ["Glucose", "src/glucose/", "CGM feature 생성, forecasting, interval, event signal"],
        ["Nutrition", "src/nutrition/", "K-Food label과 영양성분·GI proxy 연결"],
        ["Frontend", "frontend/src/", "React 웹 MVP, 안전 UX, mock fallback"],
        ["Tests", "tests/, frontend/src/test/", "API, 모델 artifact, 안전 문구, 프론트 fallback 검증"],
        ["Deployment", "Dockerfile, render.yaml, railway.json", "서버형 백엔드 배포 전환 준비"],
    ], widths=[2.4, 5.6, 8.8], font_size=8.2)
    h(doc, "End-to-end 흐름", 2)
    bullet(doc, "음식 이미지 업로드 → K-Food classifier → 음식명/신뢰도/top5 반환", 0)
    bullet(doc, "음식명 → nutrition DB → 탄수화물·당류·단백질·식이섬유·GI proxy 조회", 0)
    bullet(doc, "영양성분 → glucose_risk score → 낮음/주의/높음 참고 신호 표시", 0)
    bullet(doc, "CGM readings + meal/bolus/basal event → 30/60/90분 예측·범위·불확실성 표시", 0)
    note_box(doc, "구조상 강점", [
        "모델 파일, API schema, 프론트 표시 정책이 분리되어 있어 기능별 유지보수가 가능함",
        "backend 실패 시에도 프론트가 mock fallback으로 멈추지 않으며, 데모 데이터임을 명시함",
        "대용량 PyTorch 모델은 서버형 배포로, 경량 API는 Vercel fallback으로 나누는 배포 전략을 세움",
    ], fill=MINT)
    page_break(doc)

    # 5
    h(doc, "Ⅳ. 데이터 및 영양성분 파이프라인")
    table(doc, ["데이터", "활용 목적", "구현 내용"], [
        ["K-Food 이미지", "한국 음식 이미지 분류", "56개 class, fixed_v1 split, label patch, hard class 검토"],
        ["식품/영양 DB", "음식별 영양성분 조회", "kfood_nutrition_db.json 및 nutrition_db_real.json 구성"],
        ["OhioT1DM CGM", "혈당 시계열 예측", "12명, 2018/2020, enriched timeseries, validation/test 분리"],
        ["사용자 업로드 이미지", "웹 MVP 입력", "JPG/PNG 업로드, 분석 실패 시 데모 fallback 표시"],
    ], widths=[3.0, 4.8, 9.0], font_size=8.5)
    h(doc, "전처리와 품질 관리", 2)
    bullet(doc, "split leakage audit, overlap summary, class count, label patch 영향 분석 등 데이터 품질 검토 산출물을 유지함", 0)
    bullet(doc, "영양성분이 없는 K-Food label은 기본값으로 처리하지 않고 GI proxy mapping을 보강해 혈당 부담 참고 점수의 변별력을 개선함", 0)
    bullet(doc, "CGM 모델은 test를 선택에 사용하지 않고 validation에서 모델·threshold·calibration 전략을 고정한 뒤 test에서 최종 평가함", 0)
    metric_strip(doc, [
        ("CGM train raw", "134,790", "rows"),
        ("CGM test raw", "31,743", "rows"),
        ("Feature 수", "66", "enriched glucose features"),
    ])
    note_box(doc, "데이터 해석상 주의", [
        "음식 이미지 분류 92.02%는 fixed validation 기준 운영 후보 성능이며, 별도 holdout/실사용 이미지 검증이 추가로 필요함",
        "GI proxy와 CGM 예측은 식습관 관리 참고 목적이며 개인별 치료 판단 근거로 사용하지 않음",
    ])
    page_break(doc)

    # 6
    h(doc, "Ⅴ. 음식 이미지 분류 모델 개발 결과")
    p(doc, "핵심 성과는 K-Food 56개 class에서 7-model hflip weighted ensemble을 운영 후보로 고정한 점임.", size=9.2)
    metric_strip(doc, [
        ("Top-1", "92.02%", "6,184 / 6,720"),
        ("Top-3", "97.95%", "validation 기준"),
        ("Macro F1", "0.9200", "56 class"),
    ])
    table(doc, ["모델 구성", "가중치", "역할"], [
        ["b3_full_fixed_v1", "0.5295", "주력 고성능 EfficientNet-B3 모델"],
        ["b0_seed123_fixed_v1", "0.2567", "B0 supervised-only seed 다양성"],
        ["food_lewm_b0", "0.1424", "Food-LeWM 계열 diversity member"],
        ["b0_seed7_fixed_v1", "0.0621", "seed 다양성 보완"],
        ["b3_probe / b3_cont / b0_supervised", "0.0093", "잔여 보정 member"],
    ], widths=[5.6, 2.0, 9.2], font_size=8.4)
    h(doc, "실험 과정", 2)
    bullet(doc, "B0/B2/B3, supervised-only, Food-LeWM pretraining, hflip TTA, cached logits 기반 weight search를 단계적으로 수행함", 0)
    bullet(doc, "성능만이 아니라 운영 config와 checkpoint/metadata/classes 경로를 고정하여 FastAPI 로딩 가능 형태로 정리함", 0)
    bullet(doc, "단일 모델이 아닌 ensemble을 통해 어려운 class와 seed 편차를 보완함", 0)
    note_box(doc, "결과 해석", [
        "목표 top1 >= 0.92를 소폭 초과 달성함",
        "동일 validation split에서 ensemble weight를 탐색했으므로 별도 실사용 검증은 향후 과제로 명시함",
    ], fill=MINT)
    page_break(doc)

    # 7
    h(doc, "Ⅵ. CGM 기반 혈당 변화 예측 결과")
    p(doc, "혈당 예측은 30분, 60분, 90분 horizon을 모두 제공하되, 90분은 단일 수치보다 예측 범위와 불확실성 중심으로 설계함.", size=9.2)
    table(doc, ["Horizon", "Calibrated MAE", "RMSE", "R2", "운영 표시 원칙"], [
        ["30분", "12.998", "18.476", "0.9054", "참고용 수치 예측 중심"],
        ["60분", "22.633", "31.008", "0.7346", "수치 + 범위 + 가능성 신호"],
        ["90분", "29.606", "39.831", "0.5640", "범위 + 불확실성 + 가능성 신호"],
    ], widths=[2.2, 3.0, 2.6, 2.0, 7.0], font_size=8.2)
    table(doc, ["Event", "30분 F1", "60분 F1", "90분 F1", "해석"], [
        ["Hyper", "0.884", "0.785", "0.694", "고혈당 가능성 신호는 horizon 증가에 따라 약화"],
        ["Hypo", "0.514", "0.331", "0.252", "저혈당 precision 한계로 가능성/주의 신호로만 사용"],
    ], widths=[2.2, 2.2, 2.2, 2.2, 8.0], font_size=8.3)
    h(doc, "기능 구성", 2)
    bullet(doc, "long-window glucose feature, carbs/insulin on board proxy, basal/exercise/sleep proxy를 포함한 enriched feature set 구성", 0)
    bullet(doc, "prediction interval과 uncertainty level을 API 응답에 포함해 UI가 과도한 확정 표현을 피하도록 설계", 0)
    bullet(doc, "validation selection → test evaluation 프로세스를 분리해 모델 선택과 최종 평가의 기준을 분명히 함", 0)
    note_box(doc, "핵심 안전 원칙", [
        "CGM 예측은 의료 진단이나 치료 지침이 아님",
        "특히 90분 값은 '정확한 혈당값'이 아니라 가능한 범위와 불확실성으로 전달함",
    ])
    page_break(doc)

    # 8
    h(doc, "Ⅶ. 안전·윤리·웰니스 포지셔닝")
    p(doc, "FoodSugar AI의 혈당 기능은 의료 판단 도구가 아니라 식습관 관리와 생활 패턴 이해를 돕는 웰니스 기능으로 고정함.", size=9.2)
    table(doc, ["제공하는 것", "제공하지 않는 것"], [
        ["음식 영양성분 기반 혈당 부담 참고 점수", "당뇨 진단 또는 질병 여부 판단"],
        ["CGM 기반 30/60/90분 혈당 변화 가능성", "저혈당/고혈당 확정 판정"],
        ["예측 범위와 불확실성", "인슐린·약물·치료 계획 조절 안내"],
        ["저혈당/고혈당 가능성 신호", "응급상황 판단 또는 실제 CGM 측정값 대체"],
    ], widths=[8.4, 8.4], font_size=8.5)
    h(doc, "화면·API 표현 정책", 2)
    bullet(doc, "30분: 참고용 수치, 실제 측정값 우선", 0)
    bullet(doc, "60분: estimate와 range, 가능성 신호를 함께 표시", 0)
    bullet(doc, "90분: interval first, uncertainty high, 큰 단일 숫자 중심 표시 금지", 0)
    bullet(doc, "금지 표현: '저혈당입니다', '고혈당입니다', '치료가 필요합니다', '인슐린 조절' 등", 0)
    note_box(doc, "고정 안내 문구", [
        "이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다.",
        "혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요.",
    ], fill=CREAM)
    page_break(doc)

    # 9
    h(doc, "Ⅷ. Backend/API 통합 및 배포 준비")
    table(doc, ["Endpoint", "역할", "구현 상태"], [
        ["GET /health", "서버·모델 readiness 확인", "classifier_ready, predictor_ready 확인"],
        ["POST /predict/analyze", "이미지 → 음식분류 → 영양 → 혈당 부담", "glucose_risk 필드 추가 및 프론트 우선 표시"],
        ["POST /predict/glucose-risk", "영양성분 기반 점수형 참고 위험도", "비빔밥 예시 score 52.18, level 주의"],
        ["POST /predict/cgm-forecast-enriched-events", "CGM + event 기반 30/60/90분 예측", "interval, uncertainty, event probability 포함"],
    ], widths=[4.5, 6.2, 6.1], font_size=8.0)
    h(doc, "배포 전략", 2)
    bullet(doc, "Vercel Function은 PyTorch/timm와 대형 checkpoint 로딩에 한계가 있어 경량 fallback 용도로 유지", 0)
    bullet(doc, "운영형 백엔드는 Docker 기반 서버형 배포로 전환하고, 모델은 artifact bundle로 주입하는 구조를 설계", 0)
    bullet(doc, "Render/Railway 설정, Dockerfile, artifact 생성·다운로드 스크립트를 작성함", 0)
    metric_strip(doc, [
        ("서버 artifact", "205.2MB", "42 files"),
        ("로컬 검증", "ready", "classifier/predictor true"),
        ("API 테스트", "15 passed", "배포 전 검증"),
    ])
    note_box(doc, "남은 배포 과제", [
        "모델 bundle을 외부 저장소에 업로드하고 FOODSUGAR_MODEL_BUNDLE_URL 환경변수를 등록해야 함",
        "서버형 백엔드 URL 확정 후 프론트 VITE_API_BASE_URL을 교체해 end-to-end 재검증 필요",
    ])
    page_break(doc)

    # 10
    h(doc, "Ⅸ. 웹 MVP 화면 1: 홈 및 업로드 흐름")
    p(doc, "사용자가 처음 접속했을 때 음식 사진을 업로드하고, 음식 확인·영양성분·혈당 변화 가능성으로 이어지는 흐름을 바로 이해하도록 설계함.", size=9.2)
    add_image(doc, SCREENSHOTS["home"], width_cm=16.0, caption="[그림 1] 홈 화면: 음식 사진 업로드 중심의 웰니스 AI 데모")
    add_image(doc, SCREENSHOTS["upload"], width_cm=15.3, caption="[그림 2] Scan workspace: 사진 선택·촬영 체크·분석 시작 UX")
    bullet(doc, "첫 화면은 앱 설명보다 실제 사용 흐름을 먼저 보여주는 구조로 재설계함", 0, size=8.5)
    bullet(doc, "업로드 전에는 분석 시작 버튼을 비활성화해 사용자의 다음 행동을 명확히 함", 0, size=8.5)
    page_break(doc)

    # 11
    h(doc, "Ⅹ. 웹 MVP 화면 2: 음식 분석 및 영양 요약")
    p(doc, "음식 분석 결과 화면은 실제 모델 결과와 데모 데이터를 구분하고, 음식명·분류 신뢰도·영양성분·혈당 부담 점수를 한 화면에 배치함.", size=9.2)
    add_image(doc, SCREENSHOTS["analysis"], width_cm=16.2, caption="[그림 3] 분석 결과: 음식명, 신뢰도, 영양성분, 데모/실제 결과 구분")
    h(doc, "구현 포인트", 2)
    bullet(doc, "결과 출처 배지를 통해 backend 실제 응답인지 mock fallback인지 명확히 표시함", 0, size=8.6)
    bullet(doc, "낮은 confidence 상황을 고려해 음식 확인 카드 구조를 추가함", 0, size=8.6)
    bullet(doc, "legacy risk보다 glucose_risk score 기반 결과를 우선 표시하도록 API parsing과 UI 표시 기준을 수정함", 0, size=8.6)
    page_break(doc)

    # 12
    h(doc, "Ⅺ. 웹 MVP 화면 3: 혈당 예측 대시보드")
    p(doc, "혈당 예측 화면은 90분 값을 단일 숫자로 확정하지 않고, 예측 범위와 불확실성 신호를 먼저 보여주도록 구성함.", size=9.2)
    add_image(doc, SCREENSHOTS["prediction_top"], width_cm=16.2, caption="[그림 4] 90분 예측 범위 우선 표시")
    add_image(doc, SCREENSHOTS["prediction_chart"], width_cm=16.2, caption="[그림 5] CGM 예측 그래프: 목표 범위 band와 예측 interval band")
    bullet(doc, "30/60/90분 카드와 차트가 같은 예측 결과를 다른 수준의 상세도로 보여주도록 구성함", 0, size=8.4)
    bullet(doc, "90분 예측은 불확실성이 높다는 문구와 함께 range-first UX를 적용함", 0, size=8.4)
    page_break(doc)

    # 13
    h(doc, "Ⅻ. 웹 MVP 화면 4: 기록·리포트 및 주간 인사이트")
    p(doc, "기록 화면은 단순 로그가 아니라 최근 식사와 혈당 영향 패턴을 돌아보는 웰니스 리포트 형태로 구성함.", size=9.2)
    add_image(doc, SCREENSHOTS["history"], width_cm=16.2, caption="[그림 6] 최근 식사와 혈당 영향 요약")
    table(doc, ["화면 요소", "전달 의도"], [
        ["주간 평균 혈당", "최근 흐름을 한눈에 확인"],
        ["혈당 변동성", "사용자 상태를 보통/주의 등 완화 표현으로 전달"],
        ["가장 높은 시간대", "식후 60분 등 반복 패턴을 인사이트화"],
        ["주의해 볼 구간", "90분 예측처럼 불확실성이 큰 영역을 범위 중심으로 확인"],
    ], widths=[4.8, 12.0], font_size=8.4)
    bullet(doc, "하단 고정 navigation으로 홈·분석·예측·기록·설정 흐름을 반복 사용 가능하게 함", 0, size=8.5)
    page_break(doc)

    # 14
    h(doc, "ⅩⅢ. 검증 결과 및 품질 관리")
    table(doc, ["검증 항목", "결과", "의미"], [
        ["K-Food 운영 후보", "top1 92.02%, top3 97.95%, macro_f1 0.9200", "목표 성능 달성"],
        ["CGM artifact validation", "pass, errors 0, warnings 11", "사용 가능하나 90분 hypo 등 주의 필요"],
        ["Backend 전체 테스트", "최대 74 passed 기록", "API·모델 연결 회귀 방지"],
        ["Frontend 테스트", "3 files / 12 tests passed 기록", "fallback·안전 UI 검수"],
        ["서버형 배포 검증", "15 passed, classifier_ready true", "Docker backend 전환 가능성 확인"],
        ["안전 문구 검색", "금지 의료 표현 UI 미사용", "웰니스 포지셔닝 유지"],
    ], widths=[4.2, 5.8, 6.8], font_size=8.2)
    h(doc, "품질 관리 방식", 2)
    bullet(doc, "모델 성능 지표와 함께 leakage audit, split audit, artifact validation을 보고서화함", 0)
    bullet(doc, "API schema 변경 시 backend test와 frontend parsing test를 함께 갱신함", 0)
    bullet(doc, "시연 안정성을 위해 mock fallback과 '데모 데이터' 표기를 유지함", 0)
    note_box(doc, "현실적인 한계", [
        "음식 분류 validation 성능은 독립 unseen test 또는 실제 사용자 이미지 검증으로 보강 필요",
        "혈당 예측은 개인차가 큰 영역이므로 임상/치료 목적 사용은 범위 밖",
        "대형 ensemble은 무료 서버 메모리 한계가 있어 운영 환경별 모델 모드 선택 필요",
    ])
    page_break(doc)

    # 15
    h(doc, "ⅩⅣ. 종합 평가 및 향후 계획")
    p(doc, "FoodSugar AI는 3개월 동안 계획서의 실험 과제를 제품형 MVP로 끌어올렸다. 음식 이미지 인식, 영양성분 연결, 혈당 변화 가능성 예측, 안전 UX, 배포 준비까지 연결된 점이 핵심 성과임.", size=9.2)
    table(doc, ["구분", "현재 수준", "다음 단계"], [
        ["모델", "K-Food 92.02% 운영 후보, CGM 30/60/90분 예측", "독립 holdout, 실제 사용자 이미지, 환자군별 성능 검증"],
        ["데이터", "영양 DB 및 GI proxy 연결", "실측 식사/CGM 페어 데이터 수집, 영양 DB 보강"],
        ["서비스", "React 웹 MVP와 FastAPI 통합", "실제 backend URL 연결, 사용자 테스트, 오류/로딩 UX 개선"],
        ["안전", "참고용·비진단 문구와 금지 표현 정책", "동의서, 로그 마스킹, 삭제 요청 절차를 실제 파일럿에 적용"],
        ["배포", "Docker/Render/Railway 준비", "모델 bundle 업로드, 운영 비용·메모리 기준 확정"],
    ], widths=[2.4, 6.8, 7.6], font_size=8.2)
    h(doc, "제출용 최종 메시지", 2)
    bullet(doc, "본 프로젝트는 음식 사진을 단순 분류하는 수준을 넘어 사용자가 식사와 혈당 흐름을 이해하도록 돕는 AI 웰니스 MVP를 구현함", 0)
    bullet(doc, "모델 성능과 사용자 안전을 함께 고려해 '정확한 진단'이 아니라 '참고 가능한 범위와 신호'를 전달하는 방향으로 설계함", 0)
    bullet(doc, "향후 실제 사용자 파일럿과 외부 검증을 통해 공모전·연구 시연 수준에서 제한적 베타 서비스 수준으로 발전 가능함", 0)
    note_box(doc, "결론", [
        "계획 대비 핵심 과업 이행 완료",
        "정량 성능, 웹 시연 화면, API 구조, 안전 정책, 배포 준비를 모두 확보",
        "후속 과제는 외부 검증과 실제 운영 환경 안정화임",
    ], fill=MINT)

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
