export type PageKey = "home" | "analysis" | "prediction" | "history" | "settings";

export type AnalysisResult = {
  foodName: string;
  confidence: number;
  calories: number;
  carbs: number;
  sugar: number;
  protein: number;
  fat: number;
  fiber: number;
  glucoseRiskLevel: "낮음" | "주의" | "높음";
  glucoseRiskScore?: number;
  glucoseRiskFactors?: Record<string, number>;
  predictedRise: number;
  peakTime: string;
  explanation: string;
  isDemo?: boolean;
  imageUrl?: string;
  sourceNotice?: string;
};

export type GlucosePredictionResult = {
  currentGlucose: number;
  predictions: Record<"30" | "60" | "90", number>;
  intervals: Record<"30" | "60" | "90", [number, number]>;
  uncertainty: Record<"30" | "60" | "90", string>;
  riskSignals: {
    hypo30: string;
    hypo60: string;
    hypo90: string;
    hyper30: string;
    hyper60: string;
    hyper90: string;
  };
  uncertaintyMessage90: string;
  isDemo?: boolean;
};

export type CGMForecastPayload = {
  readings: Array<{ timestamp: string; glucose_mg_dl: number }>;
  meals?: Array<{ timestamp: string; carbs_g: number }>;
  bolus?: Array<{ timestamp: string; insulin_units: number }>;
  basal?: Array<{ timestamp: string; rate_units_per_hour: number }>;
  sleep_indicator?: number;
};

export const demoScenarios = [
  {
    title: "비빔밥 식사",
    body: "탄수화물과 채소가 함께 있는 한식 한 그릇",
    tag: "식후 상승 가능성",
  },
  {
    title: "가벼운 단백질 식사",
    body: "탄수화물 부담이 낮은 균형 식사 예시",
    tag: "완만한 변화",
  },
  {
    title: "간식 이후 흐름",
    body: "짧은 시간대 변화와 90분 범위 확인",
    tag: "범위 중심",
  },
];

export const foodConfirmationOptions = ["비빔밥", "덮밥", "채소 비빔밥"];

export const weeklyInsights = [
  {
    title: "식후 피크 패턴",
    value: "60분 구간",
    body: "최근 기록에서는 식후 60분 부근에서 가장 높은 값이 자주 나타났습니다.",
    tone: "green",
  },
  {
    title: "안정적인 선택",
    value: "단백질 포함 식사",
    body: "단백질과 식이섬유가 함께 기록된 식사는 변화 폭이 비교적 완만했습니다.",
    tone: "green",
  },
  {
    title: "주의해서 볼 구간",
    value: "90분 예측",
    body: "90분 값은 불확실성이 높아 단일 수치보다 범위와 가능성 신호를 함께 봅니다.",
    tone: "orange",
  },
];

export const mockAnalysis: AnalysisResult = {
  foodName: "비빔밥",
  confidence: 92,
  calories: 560,
  carbs: 85,
  sugar: 8,
  protein: 22,
  fat: 15,
  fiber: 6,
  glucoseRiskLevel: "높음",
  glucoseRiskScore: 52,
  predictedRise: 48,
  peakTime: "식후 60분",
  explanation: "탄수화물 함량이 높아 식후 혈당 상승 가능성이 있습니다.",
  isDemo: true,
};

export const mockPrediction: GlucosePredictionResult = {
  currentGlucose: 112,
  predictions: {
    "30": 138,
    "60": 160,
    "90": 142,
  },
  intervals: {
    "30": [120, 152],
    "60": [126, 176],
    "90": [104, 205],
  },
  uncertainty: {
    "30": "보통",
    "60": "중간",
    "90": "높음",
  },
  riskSignals: {
    hypo30: "낮음",
    hypo60: "낮음",
    hypo90: "주의",
    hyper30: "낮음",
    hyper60: "주의",
    hyper90: "주의",
  },
  uncertaintyMessage90: "90분 예측은 불확실성이 높을 수 있으므로 참고용 범위와 가능성 신호로만 확인하세요.",
  isDemo: true,
};

export const historyItems = [
  {
    id: 1,
    time: "오늘 12:20",
    foodName: "비빔밥",
    calories: 560,
    impact: "높음",
    peak: "160 mg/dL",
  },
  {
    id: 2,
    time: "어제 18:42",
    foodName: "김치찌개",
    calories: 410,
    impact: "보통",
    peak: "142 mg/dL",
  },
  {
    id: 3,
    time: "어제 08:15",
    foodName: "칼국수",
    calories: 520,
    impact: "높음",
    peak: "171 mg/dL",
  },
];

export function makeSampleCgmPayload(): CGMForecastPayload {
  const start = new Date("2026-05-26T12:00:00");
  const readings = Array.from({ length: 37 }, (_, index) => ({
    timestamp: new Date(start.getTime() + index * 5 * 60 * 1000).toISOString(),
    glucose_mg_dl: 100 + index,
  }));
  const latest = readings[readings.length - 1].timestamp;
  return {
    readings,
    meals: [{ timestamp: latest, carbs_g: 58 }],
    bolus: [],
    basal: [],
    sleep_indicator: 0,
  };
}
