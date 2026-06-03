import { BarChart3, Home, LineChart, Settings, Utensils } from "lucide-react";
import { PageKey } from "../data/mockData";

const items: Array<{ page: PageKey; label: string; icon: typeof Home }> = [
  { page: "home", label: "홈", icon: Home },
  { page: "analysis", label: "분석", icon: Utensils },
  { page: "prediction", label: "예측", icon: LineChart },
  { page: "history", label: "기록", icon: BarChart3 },
  { page: "settings", label: "설정", icon: Settings },
];

type BottomNavProps = {
  currentPage: PageKey;
  onNavigate: (page: PageKey) => void;
};

export function BottomNav({ currentPage, onNavigate }: BottomNavProps) {
  return (
    <nav className="sticky bottom-4 z-20 mx-auto mt-8 grid w-full max-w-2xl grid-cols-5 rounded-[1.5rem] border border-line bg-surface/95 p-2 shadow-soft backdrop-blur">
      {items.map((item) => {
        const Icon = item.icon;
        const active = item.page === currentPage;
        return (
          <button
            key={item.page}
            onClick={() => onNavigate(item.page)}
            className={`flex flex-col items-center gap-1 rounded-2xl px-2 py-3 text-xs font-semibold transition ${
              active ? "bg-leaf text-white" : "text-stone-500 hover:bg-sage hover:text-forest"
            }`}
            title={item.label}
          >
            <Icon className="h-4 w-4" />
            <span>{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
