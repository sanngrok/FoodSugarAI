import { BadgeCheck, Utensils } from "lucide-react";
import { AnalysisResult } from "../data/mockData";
import { ResultSourceBadge } from "./ResultSourceBadge";

type FoodPreviewCardProps = {
  analysis: AnalysisResult;
};

export function FoodPreviewCard({ analysis }: FoodPreviewCardProps) {
  const needsConfirm = analysis.confidence < 80;
  return (
    <section className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">음식 분석 결과</p>
          <h2 className="mt-1 text-3xl font-black text-forest">{analysis.foodName}</h2>
          <p className="mt-2 flex items-center gap-2 text-sm text-stone-500">
            <BadgeCheck className="h-4 w-4 text-leaf" />
            분류 신뢰도 {analysis.confidence}%
          </p>
        </div>
        <ResultSourceBadge isDemo={analysis.isDemo} />
      </div>
      {analysis.imageUrl ? (
        <img src={analysis.imageUrl} alt={analysis.foodName} className="mt-5 aspect-video w-full rounded-3xl object-cover" />
      ) : (
        <div className="mt-5 grid aspect-video place-items-center rounded-3xl bg-sage text-leaf">
          <Utensils className="h-16 w-16" />
        </div>
      )}
      {analysis.isDemo && analysis.sourceNotice && (
        <div className="mt-4 rounded-2xl bg-[#FFF8E8] p-4 text-sm font-semibold leading-6 text-[#8A4B0D]">
          {analysis.sourceNotice}
        </div>
      )}
      {needsConfirm && (
        <div className="mt-4 rounded-2xl bg-[#FFF1D6] p-4 text-sm font-semibold text-[#8A4B0D]">
          음식 인식 신뢰도가 낮습니다. 혈당 위험도는 음식명과 섭취량에 민감하므로 먼저 음식명을 확인하세요.
        </div>
      )}
    </section>
  );
}
