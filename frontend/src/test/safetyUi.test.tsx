import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { GlucosePredictionCards } from "../components/GlucosePredictionCards";
import { RiskSignalCard } from "../components/RiskSignalCard";
import { SafetyNotice } from "../components/SafetyNotice";
import { mockPrediction } from "../data/mockData";

const forbiddenWording = [
  "혈당을 정확히 예측",
  "저혈당입니다",
  "고혈당입니다",
  "인슐린을 조절",
  "치료에 사용",
  "당뇨병을 진단",
  "약을 조절",
];

describe("glucose safety UI", () => {
  it("shows reference-only safety notice", () => {
    render(<SafetyNotice />);

    expect(screen.getByText(/식습관 관리 참고용/)).toBeInTheDocument();
    expect(screen.getByText(/실제 측정값/)).toBeInTheDocument();
  });

  it("renders 90m as range-first with uncertainty wording", () => {
    render(<GlucosePredictionCards prediction={mockPrediction} />);

    expect(screen.getByText("90분 후")).toBeInTheDocument();
    expect(screen.getByText("104~205 mg/dL")).toBeInTheDocument();
    expect(screen.getByText(/불확실성 높음/)).toBeInTheDocument();
    expect(screen.getByText("범위 우선")).toBeInTheDocument();
  });

  it("uses possibility signal wording without forbidden medical claims", () => {
    const { container } = render(<RiskSignalCard prediction={mockPrediction} />);
    const text = container.textContent || "";

    expect(text).toContain("저혈당 가능성 신호");
    expect(text).toContain("고혈당 가능성 신호");
    for (const phrase of forbiddenWording) {
      expect(text).not.toContain(phrase);
    }
  });
});
