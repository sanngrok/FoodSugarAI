import { Activity, Camera, History, Leaf, LineChart, Settings } from "lucide-react";
import { PageKey } from "../data/mockData";

type HeaderBarProps = {
  onNavigate: (page: PageKey) => void;
};

export function HeaderBar({ onNavigate }: HeaderBarProps) {
  return (
    <header className="flex items-center justify-between gap-6">
      <button className="flex items-center gap-3 text-left" onClick={() => onNavigate("home")} aria-label="홈으로 이동">
        <span className="grid h-11 w-11 place-items-center rounded-[1.15rem] bg-[#071F18] text-white shadow-soft">
          <Leaf className="h-5 w-5" />
        </span>
        <span>
          <span className="block text-2xl font-black tracking-[-0.02em] text-[#111827]">WeMeet</span>
          <span className="hidden text-xs font-semibold text-stone-500 sm:block">Food scan wellness AI</span>
        </span>
      </button>

      <nav className="hidden items-center gap-8 text-sm font-black text-[#111827] lg:flex" aria-label="주요 화면">
        <button onClick={() => onNavigate("home")} className="transition hover:text-leaf">
          음식스캔
        </button>
        <button onClick={() => onNavigate("analysis")} className="transition hover:text-leaf">
          분석결과
        </button>
        <button onClick={() => onNavigate("prediction")} className="transition hover:text-leaf">
          90분예측
        </button>
        <button
          onClick={() => onNavigate("history")}
          className="transition hover:text-leaf"
        >
          기록
        </button>
        <button onClick={() => onNavigate("settings")} className="transition hover:text-leaf">
          안전안내
        </button>
      </nav>

      <div className="flex items-center gap-2">
        <div className="hidden items-center gap-1 rounded-full border border-black/[0.06] bg-white p-1 shadow-sm md:flex">
          <span className="inline-flex items-center gap-2 rounded-full bg-sage px-4 py-2 text-sm font-black text-leaf">
            <Activity className="h-4 w-4" />
            Wellness
          </span>
          <button
            onClick={() => onNavigate("history")}
            className="inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-bold text-[#111827] hover:bg-[#F5F2E8]"
          >
            <History className="h-4 w-4" />
            기록
          </button>
          <button
            onClick={() => onNavigate("settings")}
            className="grid h-9 w-9 place-items-center rounded-full text-[#111827] hover:bg-[#F5F2E8]"
            aria-label="설정"
          >
            <Settings className="h-4 w-4" />
          </button>
        </div>
        <button
          onClick={() => onNavigate("home")}
          className="hidden items-center gap-2 rounded-full bg-[#071F18] px-5 py-3 text-sm font-black text-white shadow-soft transition hover:bg-[#123524] sm:inline-flex"
        >
          <Camera className="h-4 w-4 text-[#58D68D]" />
          음식 분석 시작하기
        </button>
        <button
          onClick={() => onNavigate("prediction")}
          className="grid h-11 w-11 place-items-center rounded-full bg-sage text-leaf lg:hidden"
          aria-label="예측 보기"
        >
          <LineChart className="h-5 w-5" />
        </button>
      </div>
    </header>
  );
}
