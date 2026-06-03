import { Activity, History, Leaf } from "lucide-react";
import { PageKey } from "../data/mockData";

type HeaderBarProps = {
  onNavigate: (page: PageKey) => void;
};

export function HeaderBar({ onNavigate }: HeaderBarProps) {
  return (
    <header className="flex items-center justify-between gap-4">
      <button className="flex items-center gap-3 text-left" onClick={() => onNavigate("home")}>
        <span className="grid h-12 w-12 place-items-center rounded-2xl bg-forest text-white shadow-soft">
          <Leaf className="h-6 w-6" />
        </span>
        <span>
          <span className="block text-xl font-black tracking-tight text-forest">FoodSugar AI</span>
          <span className="text-xs text-stone-500">식습관 관리 참고용 웰니스 앱</span>
        </span>
      </button>
      <div className="hidden items-center gap-2 rounded-full border border-line bg-cream p-1 shadow-sm sm:flex">
        <span className="inline-flex items-center gap-2 rounded-full bg-sage px-4 py-2 text-sm font-black text-leaf">
          <Activity className="h-4 w-4" />
          Wellness
        </span>
        <button
          onClick={() => onNavigate("history")}
          className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-forest hover:bg-surface"
        >
          <History className="h-4 w-4" />
          분석 기록
        </button>
      </div>
    </header>
  );
}
