import {
  AnalysisResult,
  CGMForecastPayload,
  GlucosePredictionResult,
  mockAnalysis,
  mockPrediction,
} from "../data/mockData";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export function getMockAnalysis(
  imageUrl?: string,
  sourceNotice = "데모 데이터입니다. 실제 모델 분석 결과가 아닙니다.",
  overrides: Partial<AnalysisResult> = {},
): AnalysisResult {
  return { ...mockAnalysis, ...overrides, imageUrl, isDemo: true, sourceNotice };
}

export function getMockPrediction(): GlucosePredictionResult {
  return { ...mockPrediction, isDemo: true };
}

export async function analyzeFoodImage(file: File): Promise<AnalysisResult> {
  const imageUrl = URL.createObjectURL(file);
  const formData = new FormData();
  formData.append("file", file);
  formData.append("portion_g", "150");

  try {
    const response = await fetch(`${API_BASE_URL}/predict/analyze`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("analysis request failed");
    }
    const data = await response.json();
    const nutrition = data.nutrition || {};
    const risk = data.risk || {};
    const glucoseRisk = data.glucose_risk || {};
    return {
      foodName: data.classification?.food_name_ko || data.classification?.food_key || "분석된 음식",
      confidence: Math.round((data.classification?.confidence || 0) * 100),
      calories: Math.round(nutrition.calories || mockAnalysis.calories),
      carbs: Math.round(nutrition.carbs || mockAnalysis.carbs),
      sugar: Math.round(nutrition.sugar || mockAnalysis.sugar),
      protein: Math.round(nutrition.protein || mockAnalysis.protein),
      fat: Math.round(nutrition.fat || mockAnalysis.fat),
      fiber: Math.round(nutrition.fiber || mockAnalysis.fiber),
      glucoseRiskLevel: normalizeRiskLevel(glucoseRisk.level || risk.risk_label),
      glucoseRiskScore: typeof glucoseRisk.score === "number" ? Math.round(glucoseRisk.score) : undefined,
      glucoseRiskFactors: glucoseRisk.factors,
      predictedRise: mockAnalysis.predictedRise,
      peakTime: mockAnalysis.peakTime,
      explanation:
        typeof glucoseRisk.score === "number"
          ? `영양성분 기반 참고 점수 ${Math.round(glucoseRisk.score)}점입니다. ${glucoseRisk.level || "참고"} 수준으로 확인하세요.`
          : risk.serving_advice || mockAnalysis.explanation,
      imageUrl,
      isDemo: false,
    };
  } catch {
    return getMockAnalysis(
      imageUrl,
      "백엔드 서버 연결에 실패해 업로드한 이미지를 실제로 분석하지 못했습니다. 아래 값은 화면 확인용 데모 예시입니다.",
      {
        foodName: "비빔밥 데모 예시",
        confidence: 0,
        explanation: "실제 이미지 분석 결과가 아니라 backend 연결 실패 시 표시되는 데모 예시입니다.",
      },
    );
  }
}

export async function predictGlucose(payload: CGMForecastPayload): Promise<GlucosePredictionResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/predict/cgm-forecast-enriched-events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      throw new Error("glucose forecast request failed");
    }
    const data = await response.json();
    const predictions = data.calibrated_predictions_mg_dl || data.predictions_mg_dl || {};
    const intervals = data.prediction_intervals_mg_dl || {};
    const uncertainty = data.uncertainty_level || {};
    return {
      currentGlucose: payload.readings[payload.readings.length - 1]?.glucose_mg_dl || mockPrediction.currentGlucose,
      predictions: {
        "30": Math.round(predictions["30"] || predictions[30] || mockPrediction.predictions["30"]),
        "60": Math.round(predictions["60"] || predictions[60] || mockPrediction.predictions["60"]),
        "90": Math.round(predictions["90"] || predictions[90] || mockPrediction.predictions["90"]),
      },
      intervals: {
        "30": normalizeInterval(intervals["30"] || intervals[30], mockPrediction.intervals["30"]),
        "60": normalizeInterval(intervals["60"] || intervals[60], mockPrediction.intervals["60"]),
        "90": normalizeInterval(intervals["90"] || intervals[90], mockPrediction.intervals["90"]),
      },
      uncertainty: {
        "30": toKoreanUncertainty(uncertainty["30"] || uncertainty[30] || "medium"),
        "60": toKoreanUncertainty(uncertainty["60"] || uncertainty[60] || "medium"),
        "90": toKoreanUncertainty(uncertainty["90"] || uncertainty[90] || "high"),
      },
      riskSignals: mockPrediction.riskSignals,
      uncertaintyMessage90:
        data.uncertainty_message?.["90"] ||
        data.uncertainty_message?.[90] ||
        mockPrediction.uncertaintyMessage90,
      isDemo: false,
    };
  } catch {
    return getMockPrediction();
  }
}

function normalizeRiskLevel(value: unknown): AnalysisResult["glucoseRiskLevel"] {
  if (value === "낮음") return "낮음";
  if (value === "주의" || value === "보통") return "주의";
  if (value === "위험" || value === "높음") return "높음";
  return "주의";
}

function normalizeInterval(value: unknown, fallback: [number, number]): [number, number] {
  if (Array.isArray(value) && value.length >= 2) {
    return [Math.round(Number(value[0])), Math.round(Number(value[1]))];
  }
  return fallback;
}

function toKoreanUncertainty(value: string): string {
  if (value === "low") return "낮음";
  if (value === "high") return "높음";
  if (value === "medium") return "중간";
  return value || "중간";
}
