import { ReactNode } from "react";
import { PageKey } from "../data/mockData";
import { BottomNav } from "./BottomNav";
import { HeaderBar } from "./HeaderBar";

type AppShellProps = {
  currentPage: PageKey;
  onNavigate: (page: PageKey) => void;
  children: ReactNode;
};

export function AppShell({ currentPage, onNavigate, children }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[#FAFAF7] text-[#111827]">
      <div className="sticky top-0 z-40 border-b border-black/[0.04] bg-[#FAFAF7]/92 backdrop-blur-xl">
        <div className="mx-auto w-full max-w-[1500px] px-5 py-5 sm:px-8 lg:px-10">
          <HeaderBar onNavigate={onNavigate} />
        </div>
      </div>
      <div className="mx-auto flex min-h-[calc(100vh-89px)] w-full max-w-[1500px] flex-col px-5 pb-6 sm:px-8 lg:px-10">
        <main className="flex-1 py-6 lg:py-10">{children}</main>
        <BottomNav currentPage={currentPage} onNavigate={onNavigate} />
      </div>
    </div>
  );
}
