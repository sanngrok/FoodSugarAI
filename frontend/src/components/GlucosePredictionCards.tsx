import { AlertTriangle, Clock3, Timer } from "lucide-react";
import { GlucosePredictionResult } from "../data/mockData";

type GlucosePredictionCardsProps = {
  prediction: GlucosePredictionResult;
};

export function GlucosePredictionCards({ prediction }: GlucosePredictionCardsProps) {
  const cards = [
    {
      horizon: "30",
      title: "30분 후",
      body: `${prediction.predictions["30"]} mg/dL`,
      sub: `예상 범위 ${prediction.intervals["30"][0]}~${prediction.intervals["30"][1]} mg/dL`,
      icon: Timer,
      emphasis: "number",
    },
    {
      horizon: "60",
      title: "60분 후",
      body: `${prediction.intervals["60"][0]}~${prediction.intervals["60"][1]} mg/dL`,
      sub: `참고 수치 ${prediction.predictions["60"]} mg/dL · 불확실성 ${prediction.uncertainty["60"]}`,
      icon: Clock3,
      emphasis: "range",
    },
    {
      horizon: "90",
      title: "90분 후",
      body: `${prediction.intervals["90"][0]}~${prediction.intervals["90"][1]} mg/dL`,
      sub: `불확실성 ${prediction.uncertainty["90"]} · 범위 중심으로 확인`,
      icon: AlertTriangle,
      emphasis: "warning",
    },
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      {cards.map((card) => {
        const Icon = card.icon;
        const isNinety = card.horizon === "90";
        return (
          <article
            key={card.horizon}
            className={`rounded-[2rem] border p-5 shadow-soft ${
              isNinety ? "border-[#F97316]/30 bg-[#FFF8E8]" : "border-line bg-surface"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-sage text-leaf">
                <Icon className="h-5 w-5" />
              </div>
              {isNinety && <span className="rounded-full bg-[#FFF1D6] px-3 py-1 text-xs font-black text-[#A4560A]">범위 우선</span>}
            </div>
            <p className="mt-5 text-sm font-bold text-stone-500">{card.title}</p>
            <p className={`${isNinety ? "mt-2 text-3xl" : "mt-2 text-4xl"} font-black text-forest`}>{card.body}</p>
            <p className="mt-2 text-sm text-stone-500">{card.sub}</p>
          </article>
        );
      })}
    </section>
  );
}
