import { AlertTriangle, ArrowRight } from "lucide-react";
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
      {analysis.isDemo && (
        <section className="flex gap-3 rounded-[2rem] border border-[#F97316]/30 bg-[#FFF8E8] p-5 text-[#8A4B0D] shadow-soft">
          <AlertTriangle className="mt-0.5 h-6 w-6 shrink-0" />
          <div>
            <p className="font-black">실제 이미지 분석 결과가 아닙니다</p>
            <p className="mt-1 text-sm leading-6">
              {analysis.sourceNotice ||
                "현재 화면은 데모 데이터입니다. 실제 모델 결과를 보려면 backend 서버가 켜져 있어야 합니다."}
            </p>
          </div>
        </section>
      )}
      <section className="overflow-hidden rounded-[2.25rem] border border-black/[0.06] bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_380px] lg:p-10">
          <div>
            <p className="text-sm font-black text-leaf">분석 결과</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-[-0.02em] text-[#101827] sm:text-6xl">
                음식과 영양성분을 확인했어요
              </h1>
              <ResultSourceBadge isDemo={analysis.isDemo} />
            </div>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-[#65716A]">
              먼저 음식명을 확인하고, 영양성분과 혈당 부담 참고 점수를 함께 봅니다.
            </p>
          </div>
          <div className="rounded-[2rem] bg-[#071F18] p-5 text-white shadow-soft">
            <p className="text-sm font-black text-[#58D68D]">현재 인식 음식</p>
            <p className="mt-2 text-4xl font-black tracking-[-0.02em]">{analysis.foodName}</p>
            <div className="mt-5 flex items-center justify-between rounded-[1.35rem] bg-white px-4 py-3 text-[#101827]">
              <span className="text-sm font-bold text-[#65716A]">분류 신뢰도</span>
              <span className="text-2xl font-black">{analysis.confidence}%</span>
            </div>
            <p className="mt-4 text-xs leading-5 text-white/52">
              결과가 애매하면 음식 확인 단계에서 사용자가 직접 확인할 수 있습니다.
            </p>
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
