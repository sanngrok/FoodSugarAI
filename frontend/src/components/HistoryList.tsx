import { CalendarDays, ChevronRight, Utensils } from "lucide-react";
import { historyItems } from "../data/mockData";

export function HistoryList() {
  return (
    <section className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-leaf">식사 기록</p>
          <h2 className="text-2xl font-black text-forest">최근 분석</h2>
        </div>
        <button className="inline-flex items-center gap-2 rounded-full bg-sage px-4 py-2 text-sm font-bold text-forest">
          <CalendarDays className="h-4 w-4" />
          오늘
        </button>
      </div>
      <div className="mt-5 space-y-3">
        {historyItems.map((item) => (
          <article key={item.id} className="grid gap-4 rounded-3xl border border-line bg-[#FFF8E8] p-4 sm:grid-cols-[72px_1fr_120px_24px] sm:items-center">
            <div className="grid h-16 w-16 place-items-center rounded-2xl bg-sage text-leaf">
              <Utensils className="h-7 w-7" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-stone-500">{item.time}</p>
              <h3 className="truncate text-lg font-black text-forest">{item.foodName}</h3>
              <p className="text-sm text-stone-500">{item.calories} kcal · 피크 {item.peak}</p>
            </div>
            <div className="rounded-2xl bg-surface px-4 py-3 text-center">
              <p className="text-xs font-bold text-stone-500">혈당 영향</p>
              <p className="font-black text-forest">{item.impact}</p>
            </div>
            <ChevronRight className="h-5 w-5 text-stone-400" />
          </article>
        ))}
      </div>
    </section>
  );
}
