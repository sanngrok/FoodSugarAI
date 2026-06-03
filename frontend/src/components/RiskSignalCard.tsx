import { BellRing } from "lucide-react";
import { GlucosePredictionResult } from "../data/mockData";

type RiskSignalCardProps = {
  prediction: GlucosePredictionResult;
};

export function RiskSignalCard({ prediction }: RiskSignalCardProps) {
  return (
    <section className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <div className="flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-sage text-leaf">
          <BellRing className="h-5 w-5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-leaf">가능성 신호</p>
          <h3 className="text-xl font-black text-forest">저혈당/고혈당 참고 신호</h3>
        </div>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        {(["30", "60", "90"] as const).map((horizon) => (
          <div key={horizon} className="rounded-2xl bg-sage/70 p-4">
            <p className="text-sm font-black text-forest">{horizon}분</p>
            <p className="mt-2 text-sm text-stone-500">저혈당 가능성 신호</p>
            <p className="font-bold text-forest">{prediction.riskSignals[`hypo${horizon}`]}</p>
            <p className="mt-3 text-sm text-stone-500">고혈당 가능성 신호</p>
            <p className="font-bold text-forest">{prediction.riskSignals[`hyper${horizon}`]}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
