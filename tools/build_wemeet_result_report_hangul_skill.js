const fs = require("fs");
const path = require("path");
const {
  AlignmentType,
  BorderStyle,
  Document,
  Footer,
  HeadingLevel,
  ImageRun,
  LevelFormat,
  PageBreak,
  PageNumber,
  Paragraph,
  Packer,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  VerticalAlign,
  WidthType,
} = require("docx");

const H = require("/tmp/hangul-docx-skill/hangul-docx/scripts/build_hangul_docx.js");

const OUT = "/Users/sangrok/foodsugar-ai/outputs/FoodSugarAI_WE-Meet_3개월_결과보고서_15p_hangul_skill.docx";

const COMPACT_MARGIN = { top: 360, right: 360, bottom: 360, left: 360 };
const COMPACT_CONTENT_WIDTH = H.A4.width - COMPACT_MARGIN.left - COMPACT_MARGIN.right;

const IMG = {
  home: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.27.png",
  upload: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.39.png",
  analysis: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.18.57.png",
  predictionTop: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.20.png",
  predictionChart: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.31.png",
  history: "/Users/sangrok/Desktop/스크린샷 2026-06-20 오후 8.19.48.png",
};

const IMAGE_SIZE = {
  home: [2732, 1566],
  upload: [2728, 1476],
  analysis: [2740, 1530],
  predictionTop: [2526, 1484],
  predictionChart: [2528, 1534],
  history: [2590, 1516],
};

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}

function center(text, size = 22, bold = false) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: 300, after: 120 },
    children: [new TextRun({ text, font: H.FONT.GOTHIC, size, bold })],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { line: 260, after: 120 },
    children: [new TextRun({ text, font: H.FONT.GOTHIC, size: 18 })],
  });
}

function image(name, width = 520) {
  const file = IMG[name];
  const [w, h] = IMAGE_SIZE[name];
  const height = Math.round((width * h) / w);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
    children: [
      new ImageRun({
        data: fs.readFileSync(file),
        transformation: { width, height },
        type: "png",
      }),
    ],
  });
}

function normalizedWidths(widths, n) {
  if (!widths) return Array(n).fill(Math.floor(COMPACT_CONTENT_WIDTH / n));
  const sourceTotal = widths.reduce((sum, value) => sum + value, 0);
  const scaled = widths.map((value) => Math.floor((value / sourceTotal) * COMPACT_CONTENT_WIDTH));
  scaled[scaled.length - 1] += COMPACT_CONTENT_WIDTH - scaled.reduce((sum, value) => sum + value, 0);
  return scaled;
}

function table(headers, rows, widths = null) {
  const n = headers.length;
  const colWidths = normalizedWidths(widths, n);
  const bd = { style: BorderStyle.SINGLE, size: 4, color: "808080" };
  const borders = { top: bd, bottom: bd, left: bd, right: bd };
  const margins = { top: 50, bottom: 50, left: 80, right: 80 };

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "D9E2F3", type: ShadingType.CLEAR },
      verticalAlign: VerticalAlign.CENTER,
      margins,
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 0, line: 260 },
        children: [new TextRun({ text: String(h), bold: true, font: H.FONT.GOTHIC, size: 18 })],
      })],
    })),
  });

  const dataRows = rows.map((r) => new TableRow({
    children: r.map((c, i) => new TableCell({
      borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "FFFFFF", type: ShadingType.CLEAR },
      verticalAlign: VerticalAlign.CENTER,
      margins,
      children: [new Paragraph({
        alignment: i === 0 ? AlignmentType.CENTER : AlignmentType.LEFT,
        spacing: { after: 0, line: 260 },
        children: [new TextRun({ text: String(c), font: H.FONT.GOTHIC, size: 18 })],
      })],
    })),
  }));

  return new Table({
    width: { size: COMPACT_CONTENT_WIDTH, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...dataRows],
  });
}

function sectionTitle(text) {
  return H.heading(text, 1);
}

function subTitle(text) {
  return H.heading(text, 2);
}

function body(text, bold = false) {
  return H.body(text, { size: 20, bold });
}

function b(text, level = 0, bold = false) {
  return H.bullet(text, level, { size: 20, bold });
}

function buildNumberingConfig() {
  const ind = (lv) => ({ paragraph: { indent: { left: 360 + lv * 360, hanging: 300 } } });
  return [
    {
      reference: "gaejo",
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: "□", alignment: AlignmentType.LEFT, style: ind(0) },
        { level: 1, format: LevelFormat.BULLET, text: "○", alignment: AlignmentType.LEFT, style: ind(1) },
        { level: 2, format: LevelFormat.BULLET, text: "-", alignment: AlignmentType.LEFT, style: ind(2) },
        { level: 3, format: LevelFormat.BULLET, text: "·", alignment: AlignmentType.LEFT, style: ind(3) },
      ],
    },
    {
      reference: "kornum",
      levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: ind(0) },
        { level: 1, format: LevelFormat.GANADA, text: "%2.", alignment: AlignmentType.LEFT, style: ind(1) },
        { level: 2, format: LevelFormat.DECIMAL, text: "%3)", alignment: AlignmentType.LEFT, style: ind(2) },
        { level: 3, format: LevelFormat.GANADA, text: "%4)", alignment: AlignmentType.LEFT, style: ind(3) },
      ],
    },
  ];
}

function compactKoreanDoc(children) {
  const footers = {
    default: new Footer({
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: ["- ", PageNumber.CURRENT, " -"], font: H.FONT.GOTHIC, size: 18 })],
      })],
    }),
  };

  return new Document({
    styles: {
      default: { document: { run: { font: H.FONT.GOTHIC, size: 22 } } },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 28, bold: true, font: H.FONT.GOTHIC },
          paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 0 },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 24, bold: true, font: H.FONT.GOTHIC },
          paragraph: { spacing: { before: 120, after: 80 }, outlineLevel: 1 },
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: 22, bold: true, font: H.FONT.GOTHIC },
          paragraph: { spacing: { before: 100, after: 60 }, outlineLevel: 2 },
        },
      ],
    },
    numbering: { config: buildNumberingConfig() },
    sections: [{
      properties: { page: { size: H.A4, margin: COMPACT_MARGIN } },
      footers,
      children,
    }],
  });
}

function page1(children) {
  children.push(center("WE-Meet 3개월 수행 결과보고서", 22, true));
  children.push(H.title("FoodSugar AI", { size: 36 }));
  children.push(center("음식 이미지 빅데이터 기반 AI 혈당 예측 보조 시스템", 24));
  children.push(H.spacer());
  children.push(table(
    ["핵심 지표", "수행 결과", "의미"],
    [
      ["음식 이미지 분류", "K-Food 56 class top1 92.02%", "계획서의 이미지 분류 모델 개발 목표 달성"],
      ["CGM 예측", "30/60/90분 혈당 변화 가능성 예측", "단일 수치보다 범위와 불확실성 중심 제공"],
      ["제품 형태", "FastAPI + React Web MVP", "사진 업로드부터 분석·예측·기록 화면까지 구현"],
      ["배포 준비", "Docker 서버형 백엔드 및 artifact bundle", "대형 모델 운영 전환 경로 확보"],
    ],
    [2100, 3600, 4046],
  ));
  children.push(H.spacer());
  children.push(b("계획서의 데이터 수집, 모델 개발, 혈당 예측, 통합 데모, 최종 보고 흐름을 실제 코드·모델·웹 화면으로 구현함", 0, true));
  children.push(b("혈당 기능은 의료 판단이 아닌 식습관 관리 참고용으로 제한하고, 안전 문구와 불확실성 표현을 화면·API에 반영함"));
  children.push(b("보고서에는 foodsugar-ai 레포지토리의 모델 산출물, API, 프론트엔드, 테스트, 배포 준비 결과를 종합 반영함"));
  children.push(H.spacer());
  children.push(center("작성 기준일: 2026. 06. 20. / 전남대학교 AI 융합대학 인공지능학부 FoodSugar AI Team", 18));
}

function page2(children) {
  children.push(sectionTitle("Ⅰ. 계획 대비 수행 요약"));
  children.push(body("초기 계획서는 Phase 0부터 Phase 6까지의 실행 흐름을 제시했다. 본 프로젝트는 해당 흐름을 실제 데이터·모델·API·웹 MVP·배포 준비 산출물로 전환하였다."));
  children.push(table(
    ["Phase", "계획서 과업", "수행 결과"],
    [
      ["0", "개발 환경과 협업 도구 준비", "Python, FastAPI, React/Vite, Docker, 테스트 환경 구성"],
      ["1", "데이터 수집 및 EDA", "K-Food, 영양 DB, OhioT1DM CGM 데이터 구조화"],
      ["2", "전처리 및 영양 매핑", "split audit, label patch, nutrition DB, GI proxy mapping"],
      ["3", "이미지 분류 모델 개발", "EfficientNet/Food-LeWM/ensemble 실험 후 92.02% 후보 고정"],
      ["4", "혈당 예측 모델 개발", "30/60/90분 CGM 예측, interval, event signal 구현"],
      ["5", "통합 파이프라인 및 데모", "FastAPI endpoint와 React 웹 MVP 연결"],
      ["6", "최종 보고 및 발표", "모델·API·UX·배포 결과를 15쪽 보고서로 정리"],
    ],
    [1200, 3900, 4646],
  ));
  children.push(subTitle("수행 방향"));
  children.push(b("단순 모델 학습보다 음식 인식 → 영양성분 → 혈당 변화 가능성 → 사용자 화면까지 연결되는 end-to-end 전달력을 우선함"));
  children.push(b("모델 성능 수치와 한계를 함께 제시하여 결과의 신뢰도를 높임"));
  children.push(b("혈당 예측은 참고용·가능성 신호·예측 범위 중심으로 표현함"));
}

function page3(children) {
  children.push(sectionTitle("Ⅱ. 3개월 추진 경과"));
  children.push(table(
    ["기간", "중점 과업", "대표 산출물"],
    [
      ["1단계", "데이터 구조화 및 기준선 모델", "Food-101/K-Food 분류 파이프라인, 영양성분 조회 구조"],
      ["2단계", "K-Food 성능 고도화", "cleaned split, hard class review, B0/B2/B3 실험"],
      ["3단계", "혈당 예측 확장", "OhioT1DM 전처리, 30/60/90분 horizon, long-window feature"],
      ["4단계", "API 통합", "FastAPI 모델 로딩, glucose_risk 응답 추가"],
      ["5단계", "웹 MVP 구현", "Home/Analysis/Prediction/History/Settings 화면 구현"],
      ["6단계", "배포 준비", "Dockerfile, render.yaml, railway.json, server artifact"],
    ],
    [1700, 3300, 4746],
  ));
  children.push(subTitle("마일스톤"));
  children.push(b("2026.05.16: K-Food 56 class 기준 top1 92.02% 운영 후보 달성"));
  children.push(b("2026.05.24~25: CGM 장기 예측, validation/test 분리, leakage audit, 안전 문서화"));
  children.push(b("2026.05.31~06.02: 프리미엄 웰니스 대시보드 스타일의 프론트 UX 재구성"));
  children.push(b("2026.06.04~06.05: /predict/analyze에 glucose_risk score 기반 표시 우선순위 적용"));
  children.push(b("2026.06.19: Docker 서버형 백엔드 배포 전략과 모델 artifact bundle 준비"));
}

function page4(children) {
  children.push(sectionTitle("Ⅲ. 시스템 구조 및 레포지토리 산출물"));
  children.push(body("FoodSugar AI는 음식 사진을 입력으로 받아 음식 분류, 영양성분 조회, 혈당 부담 참고 점수, CGM 기반 혈당 변화 가능성 예측을 연결하는 구조로 구현되었다."));
  children.push(table(
    ["영역", "주요 경로", "역할"],
    [
      ["Backend", "api/main.py, api/routers/predict.py", "FastAPI 앱 및 예측 endpoint 제공"],
      ["Classifier", "src/classifier/", "EfficientNet, Food-LeWM, weighted ensemble 추론"],
      ["Glucose", "src/glucose/", "CGM feature, forecasting, interval, event signal"],
      ["Nutrition", "src/nutrition/", "K-Food label과 영양성분·GI proxy 연결"],
      ["Frontend", "frontend/src/", "React 웹 MVP와 안전 UX 구현"],
      ["Tests", "tests/, frontend/src/test/", "API, 모델 artifact, 안전 문구, fallback 검증"],
      ["Deployment", "Dockerfile, render.yaml, railway.json", "서버형 백엔드 배포 전환 준비"],
    ],
    [1700, 3300, 4746],
  ));
  children.push(subTitle("End-to-end 흐름"));
  children.push(b("음식 이미지 업로드 → K-Food classifier → 음식명·신뢰도·top5 반환"));
  children.push(b("음식명 → nutrition DB → 탄수화물·당류·단백질·식이섬유·GI proxy 조회"));
  children.push(b("영양성분 → glucose_risk score → 낮음·주의·높음 참고 신호 표시"));
  children.push(b("CGM readings + event → 30/60/90분 예측·범위·불확실성 표시"));
}

function page5(children) {
  children.push(sectionTitle("Ⅳ. 데이터 및 영양성분 파이프라인"));
  children.push(table(
    ["데이터", "활용 목적", "구현 내용"],
    [
      ["K-Food 이미지", "한국 음식 이미지 분류", "56개 class, fixed_v1 split, label patch, hard class 검토"],
      ["식품/영양 DB", "음식별 영양성분 조회", "kfood_nutrition_db.json 및 nutrition_db_real.json 구성"],
      ["OhioT1DM CGM", "혈당 시계열 예측", "12명, 2018/2020, enriched time-series, validation/test 분리"],
      ["웹 업로드 이미지", "MVP 입력", "JPG/PNG 업로드, 실패 시 데모 fallback과 출처 표시"],
    ],
    [2300, 3000, 4446],
  ));
  children.push(subTitle("품질 관리"));
  children.push(b("split leakage audit, overlap summary, class count, label patch 영향 분석 등 데이터 품질 검토 산출물을 유지함"));
  children.push(b("영양성분이 부족한 K-Food label은 GI proxy mapping을 보강해 혈당 부담 참고 점수의 변별력을 개선함"));
  children.push(b("CGM 모델은 test를 선택에 사용하지 않고 validation에서 전략을 고정한 뒤 test에서 최종 평가함"));
  children.push(table(
    ["항목", "값", "비고"],
    [
      ["CGM train raw", "134,790 rows", "OhioT1DM enriched"],
      ["CGM test raw", "31,743 rows", "선택에 사용하지 않는 평가 분리"],
      ["Feature 수", "66", "long-window 및 proxy feature 포함"],
    ],
    [2500, 2500, 4746],
  ));
}

function page6(children) {
  children.push(sectionTitle("Ⅴ. 음식 이미지 분류 모델 개발 결과"));
  children.push(body("K-Food 분류 파트의 핵심 성과는 56개 class에서 7-model hflip weighted ensemble을 운영 후보로 고정한 점이다."));
  children.push(table(
    ["지표", "결과", "설명"],
    [
      ["Top-1", "92.02%", "6,184 / 6,720"],
      ["Top-3", "97.95%", "validation 기준"],
      ["Macro F1", "0.9200", "56 class 평균 성능"],
      ["TTA", "hflip", "좌우 반전 test-time augmentation"],
    ],
    [2200, 2400, 5146],
  ));
  children.push(table(
    ["모델 구성", "가중치", "역할"],
    [
      ["b3_full_fixed_v1", "0.5295", "주력 고성능 EfficientNet-B3 모델"],
      ["b0_seed123_fixed_v1", "0.2567", "B0 supervised-only seed 다양성"],
      ["food_lewm_b0", "0.1424", "Food-LeWM 계열 diversity member"],
      ["b0_seed7_fixed_v1", "0.0621", "seed 다양성 보완"],
      ["기타 B3/B0 후보", "0.0093", "잔여 보정 member"],
    ],
    [4100, 1800, 3846],
  ));
  children.push(b("B0/B2/B3, supervised-only, Food-LeWM pretraining, hflip TTA, cached logits 기반 weight search를 단계적으로 수행함"));
  children.push(b("동일 validation split에서 ensemble weight를 탐색했으므로 별도 holdout 및 실사용 이미지 검증은 후속 과제로 남김"));
}

function page7(children) {
  children.push(sectionTitle("Ⅵ. CGM 기반 혈당 변화 예측 결과"));
  children.push(body("혈당 예측은 30분, 60분, 90분 horizon을 모두 제공하되, 90분은 단일 수치보다 예측 범위와 불확실성 중심으로 설계하였다."));
  children.push(table(
    ["Horizon", "Calibrated MAE", "RMSE", "R2", "운영 표시 원칙"],
    [
      ["30분", "12.998", "18.476", "0.9054", "참고용 수치 예측 중심"],
      ["60분", "22.633", "31.008", "0.7346", "수치 + 범위 + 가능성 신호"],
      ["90분", "29.606", "39.831", "0.5640", "범위 + 불확실성 + 가능성 신호"],
    ],
    [1600, 2100, 1600, 1400, 3046],
  ));
  children.push(table(
    ["Event", "30분 F1", "60분 F1", "90분 F1", "해석"],
    [
      ["Hyper", "0.884", "0.785", "0.694", "horizon 증가에 따라 가능성 신호 약화"],
      ["Hypo", "0.514", "0.331", "0.252", "precision 한계로 가능성/주의 표현만 사용"],
    ],
    [1600, 1600, 1600, 1600, 3346],
  ));
  children.push(b("long-window glucose feature, carbs/insulin on board proxy, basal/exercise/sleep proxy를 포함한 enriched feature set 구성"));
  children.push(b("prediction interval과 uncertainty level을 API 응답에 포함해 UI가 과도한 확정 표현을 피하도록 설계함"));
}

function page8(children) {
  children.push(sectionTitle("Ⅶ. 안전·윤리·웰니스 포지셔닝"));
  children.push(body("FoodSugar AI의 혈당 기능은 의료 판단 도구가 아니라 식습관 관리와 생활 패턴 이해를 돕는 웰니스 기능으로 고정하였다."));
  children.push(table(
    ["제공하는 것", "제공하지 않는 것"],
    [
      ["음식 영양성분 기반 혈당 부담 참고 점수", "당뇨 진단 또는 질병 여부 판단"],
      ["CGM 기반 30/60/90분 혈당 변화 가능성", "저혈당/고혈당 확정 판정"],
      ["예측 범위와 불확실성", "인슐린·약물·치료 계획 조절 안내"],
      ["저혈당/고혈당 가능성 신호", "응급상황 판단 또는 실제 CGM 측정값 대체"],
    ],
    [4873, 4873],
  ));
  children.push(subTitle("표현 정책"));
  children.push(b("30분: 참고용 수치, 실제 측정값 우선"));
  children.push(b("60분: estimate와 range, 가능성 신호를 함께 표시"));
  children.push(b("90분: interval first, uncertainty high, 큰 단일 숫자 중심 표시 금지"));
  children.push(b("금지 표현: '저혈당입니다', '고혈당입니다', '치료가 필요합니다', '인슐린 조절' 등"));
  children.push(H.spacer());
  children.push(body("고정 안내 문구: 이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요.", true));
}

function page9(children) {
  children.push(sectionTitle("Ⅷ. Backend/API 통합 및 배포 준비"));
  children.push(table(
    ["Endpoint", "역할", "구현 상태"],
    [
      ["GET /health", "서버·모델 readiness 확인", "classifier_ready, predictor_ready 확인"],
      ["POST /predict/analyze", "이미지 → 음식분류 → 영양 → 혈당 부담", "glucose_risk 필드 추가 및 프론트 우선 표시"],
      ["POST /predict/glucose-risk", "영양성분 기반 점수형 참고 위험도", "비빔밥 예시 score 52.18, level 주의"],
      ["POST /predict/cgm-forecast-enriched-events", "CGM + event 기반 30/60/90분 예측", "interval, uncertainty, event probability 포함"],
    ],
    [2800, 3300, 3646],
  ));
  children.push(subTitle("배포 전략"));
  children.push(b("Vercel Function은 PyTorch/timm와 대형 checkpoint 로딩에 한계가 있어 경량 fallback 용도로 유지함"));
  children.push(b("운영형 백엔드는 Docker 기반 서버형 배포로 전환하고, 모델은 artifact bundle로 주입하는 구조를 설계함"));
  children.push(b("Render/Railway 설정, Dockerfile, artifact 생성·다운로드 스크립트를 작성함"));
  children.push(table(
    ["항목", "값", "비고"],
    [
      ["서버 artifact", "205.2MB", "42 files"],
      ["로컬 검증", "ready", "classifier_ready/predictor_ready true"],
      ["API 테스트", "15 passed", "배포 전 검증"],
    ],
    [2500, 2500, 4746],
  ));
}

function page10(children) {
  children.push(sectionTitle("Ⅸ. 웹 MVP 화면 1: 홈 및 업로드 흐름"));
  children.push(body("사용자가 처음 접속했을 때 음식 사진을 업로드하고, 음식 확인·영양성분·혈당 변화 가능성으로 이어지는 흐름을 바로 이해하도록 설계하였다."));
  children.push(image("home", 690));
  children.push(caption("[그림 1] 홈 화면: 음식 사진 업로드 중심의 웰니스 AI 데모"));
  children.push(image("upload", 690));
  children.push(caption("[그림 2] Scan workspace: 사진 선택·촬영 체크·분석 시작 UX"));
}

function page11(children) {
  children.push(sectionTitle("Ⅹ. 웹 MVP 화면 2: 음식 분석 및 영양 요약"));
  children.push(body("음식 분석 결과 화면은 실제 모델 결과와 데모 데이터를 구분하고, 음식명·분류 신뢰도·영양성분·혈당 부담 점수를 한 화면에 배치하였다."));
  children.push(image("analysis", 700));
  children.push(caption("[그림 3] 분석 결과: 음식명, 신뢰도, 영양성분, 데모/실제 결과 구분"));
  children.push(subTitle("구현 포인트"));
  children.push(b("결과 출처 배지를 통해 backend 실제 응답인지 mock fallback인지 명확히 표시함"));
  children.push(b("낮은 confidence 상황을 고려해 음식 확인 카드 구조를 추가함"));
  children.push(b("legacy risk보다 glucose_risk score 기반 결과를 우선 표시하도록 API parsing과 UI 표시 기준을 수정함"));
}

function page12(children) {
  children.push(sectionTitle("Ⅺ. 웹 MVP 화면 3: 혈당 예측 대시보드"));
  children.push(body("혈당 예측 화면은 90분 값을 단일 숫자로 확정하지 않고, 예측 범위와 불확실성 신호를 먼저 보여주도록 구성하였다."));
  children.push(image("predictionTop", 675));
  children.push(caption("[그림 4] 90분 예측 범위 우선 표시"));
  children.push(image("predictionChart", 675));
  children.push(caption("[그림 5] CGM 예측 그래프: 목표 범위 band와 예측 interval band"));
}

function page13(children) {
  children.push(sectionTitle("Ⅻ. 웹 MVP 화면 4: 기록·리포트 및 주간 인사이트"));
  children.push(body("기록 화면은 단순 로그가 아니라 최근 식사와 혈당 영향 패턴을 돌아보는 웰니스 리포트 형태로 구성하였다."));
  children.push(image("history", 700));
  children.push(caption("[그림 6] 최근 식사와 혈당 영향 요약"));
  children.push(table(
    ["화면 요소", "전달 의도"],
    [
      ["주간 평균 혈당", "최근 흐름을 한눈에 확인"],
      ["혈당 변동성", "사용자 상태를 보통/주의 등 완화 표현으로 전달"],
      ["가장 높은 시간대", "식후 60분 등 반복 패턴을 인사이트화"],
      ["주의해 볼 구간", "90분 예측처럼 불확실성이 큰 영역을 범위 중심으로 확인"],
    ],
    [3000, 6746],
  ));
  children.push(b("하단 고정 navigation으로 홈·분석·예측·기록·설정 흐름을 반복 사용 가능하게 함"));
}

function page14(children) {
  children.push(sectionTitle("ⅩⅢ. 검증 결과 및 품질 관리"));
  children.push(table(
    ["검증 항목", "결과", "의미"],
    [
      ["K-Food 운영 후보", "top1 92.02%, top3 97.95%, macro_f1 0.9200", "목표 성능 달성"],
      ["CGM artifact validation", "pass, errors 0, warnings 11", "사용 가능하나 90분 hypo 등 주의 필요"],
      ["Backend 전체 테스트", "최대 74 passed 기록", "API·모델 연결 회귀 방지"],
      ["Frontend 테스트", "3 files / 12 tests passed 기록", "fallback·안전 UI 검수"],
      ["서버형 배포 검증", "15 passed, classifier_ready true", "Docker backend 전환 가능성 확인"],
      ["안전 문구 검색", "금지 의료 표현 UI 미사용", "웰니스 포지셔닝 유지"],
    ],
    [2800, 3600, 3346],
  ));
  children.push(subTitle("품질 관리 방식"));
  children.push(b("모델 성능 지표와 함께 leakage audit, split audit, artifact validation을 보고서화함"));
  children.push(b("API schema 변경 시 backend test와 frontend parsing test를 함께 갱신함"));
  children.push(b("시연 안정성을 위해 mock fallback과 '데모 데이터' 표기를 유지함"));
  children.push(subTitle("현실적인 한계"));
  children.push(b("음식 분류 validation 성능은 독립 unseen test 또는 실제 사용자 이미지 검증으로 보강 필요"));
  children.push(b("혈당 예측은 개인차가 큰 영역이므로 임상/치료 목적 사용은 범위 밖"));
  children.push(b("대형 ensemble은 무료 서버 메모리 한계가 있어 운영 환경별 모델 모드 선택 필요"));
}

function page15(children) {
  children.push(sectionTitle("ⅩⅣ. 종합 평가 및 향후 계획"));
  children.push(body("FoodSugar AI는 3개월 동안 계획서의 실험 과제를 제품형 MVP로 끌어올렸다. 음식 이미지 인식, 영양성분 연결, 혈당 변화 가능성 예측, 안전 UX, 배포 준비까지 연결된 점이 핵심 성과이다."));
  children.push(table(
    ["구분", "현재 수준", "다음 단계"],
    [
      ["모델", "K-Food 92.02% 운영 후보, CGM 30/60/90분 예측", "독립 holdout, 실제 사용자 이미지, 환자군별 성능 검증"],
      ["데이터", "영양 DB 및 GI proxy 연결", "실측 식사/CGM 페어 데이터 수집, 영양 DB 보강"],
      ["서비스", "React 웹 MVP와 FastAPI 통합", "실제 backend URL 연결, 사용자 테스트, 오류/로딩 UX 개선"],
      ["안전", "참고용·비진단 문구와 금지 표현 정책", "동의서, 로그 마스킹, 삭제 요청 절차를 실제 파일럿에 적용"],
      ["배포", "Docker/Render/Railway 준비", "모델 bundle 업로드, 운영 비용·메모리 기준 확정"],
    ],
    [1600, 3900, 4246],
  ));
  children.push(subTitle("제출용 최종 메시지"));
  children.push(b("본 프로젝트는 음식 사진을 단순 분류하는 수준을 넘어 사용자가 식사와 혈당 흐름을 이해하도록 돕는 AI 웰니스 MVP를 구현함"));
  children.push(b("모델 성능과 사용자 안전을 함께 고려해 '정확한 진단'이 아니라 '참고 가능한 범위와 신호'를 전달하는 방향으로 설계함"));
  children.push(b("향후 실제 사용자 파일럿과 외부 검증을 통해 공모전·연구 시연 수준에서 제한적 베타 서비스 수준으로 발전 가능함"));
  children.push(H.spacer());
  children.push(body("결론: 계획 대비 핵심 과업을 이행했으며, 정량 성능·웹 시연 화면·API 구조·안전 정책·배포 준비를 모두 확보하였다.", true));
}

async function main() {
  const children = [];
  const pages = [
    page1, page2, page3, page4, page5,
    page6, page7, page8, page9, page10,
    page11, page12, page13, page14, page15,
  ];
  pages.forEach((fn, index) => {
    fn(children);
    if (index !== pages.length - 1) children.push(pageBreak());
  });

  const doc = compactKoreanDoc(children);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(OUT, buffer);
  console.log(OUT);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
