import { Apple, Beef, Droplets, Flame, Wheat } from "lucide-react";
import { AnalysisResult } from "../data/mockData";

type NutritionCardProps = {
  analysis: AnalysisResult;
};

export function NutritionCard({ analysis }: NutritionCardProps) {
  const nutrients = [
    { label: "칼로리", value: `${analysis.calories} kcal`, icon: Flame },
    { label: "탄수화물", value: `${analysis.carbs} g`, icon: Wheat },
    { label: "당류", value: `${analysis.sugar} g`, icon: Droplets },
    { label: "단백질", value: `${analysis.protein} g`, icon: Beef },
    { label: "지방", value: `${analysis.fat} g`, icon: Apple },
    { label: "식이섬유", value: `${analysis.fiber} g`, icon: Wheat },
  ];

  return (
    <section className="overflow-hidden rounded-[2rem] border border-line bg-surface shadow-soft">
      <div className="border-b border-line bg-cream px-5 py-4">
        <p className="text-sm font-bold text-leaf">Nutrition map</p>
        <h3 className="text-xl font-black text-forest">영양성분</h3>
      </div>
      <div className="p-5">
        <div className="mb-4 rounded-3xl bg-sage/70 p-4">
          <div className="flex items-end justify-between">
            <div>
              <p className="text-xs font-bold text-stone-500">총 열량</p>
              <p className="text-3xl font-black text-forest">{analysis.calories} kcal</p>
            </div>
            <span className="rounded-full bg-surface px-3 py-1 text-xs font-black text-leaf">한 끼 기준</span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
          {nutrients.slice(1).map((item) => {
            const Icon = item.icon;
            return (
              <div key={item.label} className="rounded-2xl border border-line bg-[#FFF8E8] p-4">
                <Icon className="h-5 w-5 text-leaf" />
                <p className="mt-3 text-xs font-semibold text-stone-500">{item.label}</p>
                <p className="mt-1 text-lg font-black text-forest">{item.value}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
