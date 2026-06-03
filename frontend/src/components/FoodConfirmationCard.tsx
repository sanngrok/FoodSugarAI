import { CheckCircle2, CircleHelp } from "lucide-react";
import { AnalysisResult, foodConfirmationOptions } from "../data/mockData";

type FoodConfirmationCardProps = {
  analysis: AnalysisResult;
};

export function FoodConfirmationCard({ analysis }: FoodConfirmationCardProps) {
  const needsConfirm = analysis.confidence < 80;

  return (
    <section
      className={`rounded-[2rem] border p-5 shadow-soft ${
        needsConfirm ? "border-[#F97316]/30 bg-[#FFF8E8]" : "border-line bg-surface"
      }`}
    >
      <div className="flex items-start gap-3">
        <div className={`grid h-11 w-11 shrink-0 place-items-center rounded-2xl ${needsConfirm ? "bg-[#FFF1D6] text-[#A4560A]" : "bg-sage text-leaf"}`}>
          {needsConfirm ? <CircleHelp className="h-5 w-5" /> : <CheckCircle2 className="h-5 w-5" />}
        </div>
        <div>
          <p className={`text-sm font-black ${needsConfirm ? "text-[#A4560A]" : "text-leaf"}`}>
            음식 확인
          </p>
          <h3 className="mt-1 text-xl font-black text-forest">
            {needsConfirm ? "음식명을 먼저 확인해주세요" : `${analysis.foodName}로 분석했어요`}
          </h3>
          <p className="mt-2 text-sm leading-6 text-stone-500">
            혈당 부담과 영양성분 요약은 음식명과 섭취량에 따라 달라질 수 있어요. 신뢰도가 낮을 때는
            음식명을 확인한 뒤 참고 결과를 보는 흐름으로 사용합니다.
          </p>
        </div>
      </div>
      <div className="mt-5 flex flex-wrap gap-2">
        {foodConfirmationOptions.map((option) => (
          <button
            key={option}
            type="button"
            className={`rounded-full border px-4 py-2 text-sm font-bold ${
              option === analysis.foodName
                ? "border-leaf bg-leaf text-white"
                : "border-line bg-surface text-forest"
            }`}
          >
            {option}
          </button>
        ))}
      </div>
    </section>
  );
}
