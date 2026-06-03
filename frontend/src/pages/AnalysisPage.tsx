import { ArrowRight } from "lucide-react";
import { FoodConfirmationCard } from "../components/FoodConfirmationCard";
import { FoodPreviewCard } from "../components/FoodPreviewCard";
import { GlucoseRiskCard } from "../components/GlucoseRiskCard";
import { NutritionCard } from "../components/NutritionCard";
import { ResultSourceBadge } from "../components/ResultSourceBadge";
import { SafetyNotice } from "../components/SafetyNotice";
import { AnalysisResult } from "../data/mockData";

type AnalysisPageProps = {
  analysis: AnalysisResult;
  onPrediction: () => void;
};

export function AnalysisPage({ analysis, onPrediction }: AnalysisPageProps) {
  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[2rem] border border-line bg-forest text-white shadow-soft">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_360px]">
          <div>
            <p className="text-sm font-bold text-[#A7E7B6]">분석 결과</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="text-4xl font-black tracking-tight sm:text-5xl">음식과 영양성분을 확인했어요</h1>
              <ResultSourceBadge isDemo={analysis.isDemo} />
            </div>
            <p className="mt-4 max-w-2xl leading-7 text-white/70">
              먼저 음식명을 확인하고, 영양성분과 혈당 부담 참고 점수를 함께 봅니다.
            </p>
          </div>
          <div className="rounded-3xl bg-white/10 p-5">
            <p className="text-sm font-bold text-[#A7E7B6]">현재 인식 음식</p>
            <p className="mt-2 text-4xl font-black">{analysis.foodName}</p>
            <div className="mt-4 flex items-center justify-between rounded-2xl bg-[#FFFDF5] px-4 py-3 text-forest">
              <span className="text-sm font-bold text-stone-500">분류 신뢰도</span>
              <span className="text-2xl font-black">{analysis.confidence}%</span>
            </div>
          </div>
        </div>
      </section>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-sm font-bold text-leaf">Wellness summary</p>
          <h2 className="text-2xl font-black text-forest">식사 영향 요약</h2>
        </div>
        <button
          onClick={onPrediction}
          className="inline-flex items-center gap-2 rounded-2xl bg-leaf px-5 py-3 font-bold text-white shadow-soft"
        >
          혈당 변화 보기
          <ArrowRight className="h-5 w-5" />
        </button>
      </div>
      <div className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div className="space-y-6">
          <FoodPreviewCard analysis={analysis} />
          <FoodConfirmationCard analysis={analysis} />
        </div>
        <div className="space-y-6">
          <NutritionCard analysis={analysis} />
          <GlucoseRiskCard analysis={analysis} />
          <SafetyNotice />
        </div>
      </div>
    </div>
  );
}
