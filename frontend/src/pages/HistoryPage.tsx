import { Activity, Clock, Lightbulb, TrendingUp } from "lucide-react";
import { HistoryList } from "../components/HistoryList";
import { SafetyNotice } from "../components/SafetyNotice";
import { weeklyInsights } from "../data/mockData";

export function HistoryPage() {
  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-bold text-leaf">기록 / 리포트</p>
        <h1 className="text-3xl font-black text-forest">최근 식사와 혈당 영향 요약</h1>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <SummaryCard icon={TrendingUp} label="주간 평균 혈당" value="132 mg/dL" />
        <SummaryCard icon={Activity} label="혈당 변동성" value="보통" />
        <SummaryCard icon={Clock} label="가장 높은 시간대" value="식후 60분" />
      </div>
      <section className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-2xl bg-sage text-leaf">
            <Lightbulb className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-leaf">주간 인사이트</p>
            <h2 className="text-xl font-black text-forest">이번 주 식사와 혈당 패턴 스냅샷</h2>
          </div>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {weeklyInsights.map((insight) => (
            <article
              key={insight.title}
              className={`rounded-[2rem] border p-5 shadow-soft ${
                insight.tone === "orange" ? "border-[#F97316]/30 bg-[#FFF8E8]" : "border-line bg-surface"
              }`}
            >
              <p className={`text-sm font-black ${insight.tone === "orange" ? "text-[#A4560A]" : "text-leaf"}`}>
                {insight.title}
              </p>
              <p className="mt-2 text-2xl font-black text-forest">{insight.value}</p>
              <p className="mt-2 text-sm leading-6 text-stone-500">{insight.body}</p>
            </article>
          ))}
        </div>
      </section>
      <HistoryList />
      <SafetyNotice />
    </div>
  );
}

type SummaryCardProps = {
  icon: typeof Activity;
  label: string;
  value: string;
};

function SummaryCard({ icon: Icon, label, value }: SummaryCardProps) {
  return (
    <article className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <Icon className="h-6 w-6 text-leaf" />
      <p className="mt-4 text-sm font-semibold text-stone-500">{label}</p>
      <p className="mt-1 text-2xl font-black text-forest">{value}</p>
    </article>
  );
}
