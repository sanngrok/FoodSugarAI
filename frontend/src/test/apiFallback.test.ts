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
    expect(result.foodName).toBe("비빔밥");
    expect(result.imageUrl).toBe("blob:foodsugar-test-preview");
  });

  it("uses mock glucose prediction when backend forecast fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false }));

    const result = await predictGlucose(makeSampleCgmPayload());

    expect(result.isDemo).toBe(true);
    expect(result.intervals["90"]).toEqual([104, 205]);
    expect(result.uncertaintyMessage90).toContain("참고용");
  });
});
