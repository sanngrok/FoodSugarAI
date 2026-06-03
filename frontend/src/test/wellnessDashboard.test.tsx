import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FoodConfirmationCard } from "../components/FoodConfirmationCard";
import { FoodPreviewCard } from "../components/FoodPreviewCard";
import { GlucoseChart } from "../components/GlucoseChart";
import { mockAnalysis, mockPrediction } from "../data/mockData";
import { HistoryPage } from "../pages/HistoryPage";
import { HomePage } from "../pages/HomePage";
import { SettingsPage } from "../pages/SettingsPage";

describe("wellness dashboard UX", () => {
  it("keeps food scan first and exposes demo scenario buttons", () => {
    render(<HomePage isLoading={false} onAnalyze={() => undefined} onFileSelect={() => undefined} />);

    expect(screen.getByRole("heading", { name: /음식 사진을\s*업로드해주세요/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /비빔밥 식사/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /가벼운 단백질 식사/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /간식 이후 흐름/ })).toBeInTheDocument();
  });

  it("shows result source badges for demo and actual model results", () => {
    render(<FoodPreviewCard analysis={{ ...mockAnalysis, isDemo: true }} />);
    expect(screen.getByText("데모 데이터")).toBeInTheDocument();

    render(<FoodPreviewCard analysis={{ ...mockAnalysis, isDemo: false }} />);
    expect(screen.getByText("실제 모델 결과")).toBeInTheDocument();
  });

  it("shows a food confirmation card for low confidence results", () => {
    render(<FoodConfirmationCard analysis={{ ...mockAnalysis, confidence: 62 }} />);

    expect(screen.getByText("음식 확인")).toBeInTheDocument();
    expect(screen.getByText("음식명을 먼저 확인해주세요")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "비빔밥" })).toBeInTheDocument();
  });

  it("adds CGM target range and prediction interval chart labels", () => {
    render(<GlucoseChart prediction={mockPrediction} />);

    expect(screen.getByText("목표 범위 70~180 mg/dL")).toBeInTheDocument();
    expect(screen.getByText("예측 범위 band")).toBeInTheDocument();
  });

  it("shows weekly insight cards on history", () => {
    render(<HistoryPage />);

    expect(screen.getByText("주간 인사이트")).toBeInTheDocument();
    expect(screen.getByText("식후 피크 패턴")).toBeInTheDocument();
    expect(screen.getByText("주의해서 볼 구간")).toBeInTheDocument();
  });

  it("explains what the app does and does not do in settings", () => {
    render(<SettingsPage />);

    expect(screen.getByText("이 앱이 하는 일 / 하지 않는 일")).toBeInTheDocument();
    expect(screen.getByText("하는 일")).toBeInTheDocument();
    expect(screen.getByText("하지 않는 일")).toBeInTheDocument();
    expect(screen.getByText(/의료 결정을 대신하지 않습니다/)).toBeInTheDocument();
  });
});
