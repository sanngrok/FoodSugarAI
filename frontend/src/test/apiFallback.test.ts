import { afterEach, describe, expect, it, vi } from "vitest";
import { analyzeFoodImage, predictGlucose } from "../lib/api";
import { makeSampleCgmPayload } from "../data/mockData";

describe("API fallback", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("uses mock analysis when backend analysis fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    const result = await analyzeFoodImage(new File(["x"], "food.jpg", { type: "image/jpeg" }));

    expect(result.isDemo).toBe(true);
    expect(result.foodName).toBe("비빔밥 데모 예시");
    expect(result.confidence).toBe(0);
    expect(result.sourceNotice).toContain("실제로 분석하지 못했습니다");
    expect(result.imageUrl).toBe("blob:foodsugar-test-preview");
  });

  it("uses mock glucose prediction when backend forecast fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));

    const result = await predictGlucose(makeSampleCgmPayload());

    expect(result.isDemo).toBe(true);
    expect(result.intervals["90"]).toEqual([104, 205]);
    expect(result.uncertaintyMessage90).toContain("참고용");
  });

  it("shows the backend's risk flags, not demo risk signals, for a real forecast", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          calibrated_predictions_mg_dl: { "30": 156.59, "60": 205.92, "90": 198.29 },
          prediction_intervals_mg_dl: { "30": [124.35, 188.83], "60": [152.37, 259.47], "90": [130.23, 266.35] },
          uncertainty_level: { "30": "high", "60": "high", "90": "high" },
          risk_flags: {
            "30": { hypo_risk: false, hyper_risk: false },
            "60": { hypo_risk: false, hyper_risk: true },
            "90": { hypo_risk: false, hyper_risk: true },
          },
        }),
      }),
    );

    const result = await predictGlucose(makeSampleCgmPayload());

    expect(result.isDemo).toBe(false);
    expect(result.riskSignals).toEqual({
      hypo30: "낮음",
      hypo60: "낮음",
      hypo90: "낮음",
      hyper30: "낮음",
      hyper60: "주의",
      hyper90: "주의",
    });
  });

  it("marks risk signals as unavailable when a real forecast has no risk flags", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          predictions_mg_dl: { "30": 131, "60": 141, "90": 150 },
          risk_flags: null,
        }),
      }),
    );

    const result = await predictGlucose(makeSampleCgmPayload());

    expect(result.isDemo).toBe(false);
    expect(Object.values(result.riskSignals)).toEqual(Array(6).fill("정보 없음"));
  });

  it("prefers score-based glucose_risk over legacy risk label", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          classification: {
            food_key: "비빔밥",
            food_name_ko: "비빔밥",
            confidence: 0.91,
          },
          nutrition: {
            calories: 171.1,
            carbs: 29.74,
            sugar: 1.98,
            protein: 4.63,
            fat: 3.7,
            fiber: 0.96,
          },
          risk: {
            risk_label: "낮음",
            serving_advice: "legacy risk",
          },
          glucose_risk: {
            score: 52.44,
            level: "주의",
            factors: { scaled_carbs_g: 44.61 },
          },
        }),
      }),
    );

    const result = await analyzeFoodImage(new File(["x"], "food.jpg", { type: "image/jpeg" }));

    expect(result.isDemo).toBe(false);
    expect(result.glucoseRiskLevel).toBe("주의");
    expect(result.glucoseRiskScore).toBe(52);
    expect(result.explanation).toContain("참고 점수 52점");
  });
});
