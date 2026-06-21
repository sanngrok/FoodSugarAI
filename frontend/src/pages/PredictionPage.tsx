import { RefreshCw } from "lucide-react";
import { GlucoseChart } from "../components/GlucoseChart";
import { GlucosePredictionCards } from "../components/GlucosePredictionCards";
import { ResultSourceBadge } from "../components/ResultSourceBadge";
import { RiskSignalCard } from "../components/RiskSignalCard";
import { SafetyNotice } from "../components/SafetyNotice";
import { GlucosePredictionResult } from "../data/mockData";

type PredictionPageProps = {
  prediction: GlucosePredictionResult;
  onRefresh: () => void;
  isLoading: boolean;
};

export function PredictionPage({ prediction, onRefresh, isLoading }: PredictionPageProps) {
  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-[2.25rem] border border-black/[0.06] bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)]">
        <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_430px] lg:p-10">
          <div>
            <p className="text-sm font-black text-leaf">CGM 기반 참고 예측</p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <h1 className="max-w-3xl text-4xl font-black leading-tight tracking-[-0.02em] text-[#101827] sm:text-6xl">
                식후 혈당 변화 가능성
              </h1>
              <ResultSourceBadge isDemo={prediction.isDemo} />
            </div>
            <p className="mt-5 text-lg font-semibold text-[#65716A]">
              현재 혈당 {prediction.currentGlucose} mg/dL 기준 · 참고용 범위 예측
            </p>
          </div>
          <div className="rounded-[2rem] bg-[#071F18] p-5 text-white shadow-soft">
            <p className="text-sm font-black text-[#58D68D]">90분 예상 범위</p>
            <p className="mt-2 text-5xl font-black tracking-[-0.03em]">
              {prediction.intervals["90"][0]}~{prediction.intervals["90"][1]}
            </p>
            <p className="mt-1 text-sm font-bold text-white/58">mg/dL · 불확실성 {prediction.uncertainty["90"]}</p>
            <div className="mt-5 h-3 rounded-full bg-white/14">
              <div className="h-3 w-3/4 rounded-full bg-[#58D68D]" />
            </div>
          </div>
        </div>
      </section>
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-[2rem] border border-black/[0.06] bg-white p-4 shadow-sm">
        <p className="text-sm font-semibold text-[#65716A]">예측은 참고용 범위와 가능성 신호 중심으로 확인합니다.</p>
        <button
          onClick={onRefresh}
          className="inline-flex items-center gap-2 rounded-full border border-black/[0.08] bg-[#FAFAF7] px-5 py-3 font-black text-[#101827] shadow-sm"
        >
          <RefreshCw className={`h-5 w-5 ${isLoading ? "animate-spin" : ""}`} />
          예측 새로고침
        </button>
      </div>
      {prediction.isDemo && (
        <div className="rounded-2xl bg-[#FFF1D6] px-4 py-3 text-sm font-bold text-[#A4560A]">
          backend 연결이 없거나 실패해 데모 데이터를 표시 중입니다.
        </div>
      )}
      <section className="rounded-[2rem] border border-[#F97316]/30 bg-[#FFF8E8] p-6 shadow-soft">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm font-black text-[#A4560A]">90분 범위 우선 예측</p>
            <h2 className="mt-2 text-4xl font-black leading-tight text-forest">
              {prediction.intervals["90"][0]}~{prediction.intervals["90"][1]} mg/dL
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-stone-600">
              90분 예측은 불확실성이 높아 단일 수치보다 가능한 범위를 먼저 확인합니다. 이 값은 식습관
              관리 참고용이며 실제 측정값과 함께 해석해주세요.
            </p>
          </div>
          <div className="rounded-2xl bg-surface px-4 py-3 text-sm font-black text-[#A4560A]">
            불확실성 {prediction.uncertainty["90"]}
          </div>
        </div>
      </section>
      <GlucosePredictionCards prediction={prediction} />
      <div className="rounded-[2rem] border border-[#F97316]/30 bg-[#FFF8E8] p-5 text-forest shadow-soft">
        <p className="text-sm font-bold text-[#A4560A]">90분 예측 안내</p>
        <p className="mt-2 text-lg font-black">{prediction.uncertaintyMessage90}</p>
      </div>
      <GlucoseChart prediction={prediction} />
      <RiskSignalCard prediction={prediction} />
      <SafetyNotice />
    </div>
  );
}
