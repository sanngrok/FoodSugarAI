import { Activity, Clock, TrendingUp } from "lucide-react";
import { AnalysisResult } from "../data/mockData";

type GlucoseRiskCardProps = {
  analysis: AnalysisResult;
};

export function GlucoseRiskCard({ analysis }: GlucoseRiskCardProps) {
  const score = analysis.glucoseRiskScore;
  const scoreWidth = `${Math.max(0, Math.min(score ?? 0, 100))}%`;
  const riskStyle =
    analysis.glucoseRiskLevel === "높음"
      ? "bg-[#FFF1D6] text-[#A4560A]"
      : analysis.glucoseRiskLevel === "주의"
        ? "bg-sage text-forest"
        : "bg-[#E8F3E8] text-leaf";

  return (
    <section className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold text-leaf">혈당 부담 참고 점수</p>
          <h3 className="mt-2 text-3xl font-black text-forest">{analysis.glucoseRiskLevel}</h3>
          {typeof score === "number" && (
            <p className="mt-1 text-sm font-bold text-stone-500">영양성분 기반 {score}/100점</p>
          )}
        </div>
        <span className={`rounded-full px-4 py-2 text-sm font-black ${riskStyle}`}>{analysis.glucoseRiskLevel}</span>
      </div>
      <div className="mt-5">
        <div className="flex h-4 overflow-hidden rounded-full bg-sage">
          <span className="w-1/3 bg-leaf" />
          <span className="w-1/3 bg-[#F5C26B]" />
          <span className="w-1/3 bg-[#F97316]" />
        </div>
        <div className="mt-2 grid grid-cols-3 text-xs font-bold text-stone-500">
          <span>낮음</span>
          <span className="text-center">주의</span>
          <span className="text-right">높음</span>
        </div>
        {typeof score === "number" && (
          <div className="mt-4 rounded-2xl bg-[#FFF8E8] p-3">
            <div className="h-3 overflow-hidden rounded-full bg-[#FFF1D6]">
              <div className="h-full rounded-full bg-leaf" style={{ width: scoreWidth }} />
            </div>
            <p className="mt-2 text-xs font-semibold text-stone-500">
              기존 위험도 라벨보다 0~100 참고 점수 결과를 우선 표시합니다.
            </p>
          </div>
        )}
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        <div className="rounded-2xl bg-sage/70 p-4">
          <TrendingUp className="h-5 w-5 text-leaf" />
          <p className="mt-2 text-sm text-stone-500">예상 혈당 상승 가능성</p>
          <p className="text-2xl font-black text-forest">+{analysis.predictedRise} mg/dL</p>
        </div>
        <div className="rounded-2xl bg-sage/70 p-4">
          <Clock className="h-5 w-5 text-leaf" />
          <p className="mt-2 text-sm text-stone-500">피크 예상 시간</p>
          <p className="text-2xl font-black text-forest">{analysis.peakTime}</p>
        </div>
      </div>
      <div className="mt-4 flex gap-3 rounded-2xl bg-[#FFF8E8] p-4 text-sm text-forest">
        <Activity className="mt-0.5 h-5 w-5 shrink-0 text-leaf" />
        <p>{analysis.explanation}</p>
      </div>
    </section>
  );
}
