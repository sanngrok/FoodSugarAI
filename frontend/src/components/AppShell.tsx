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
    <div className="min-h-screen bg-cream text-[#1F2A24]">
      <div className="border-b border-line/70 bg-surface/80 backdrop-blur">
        <div className="mx-auto w-full max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <HeaderBar onNavigate={onNavigate} />
        </div>
      </div>
      <div className="mx-auto flex min-h-[calc(100vh-81px)] w-full max-w-7xl flex-col px-4 pb-5 sm:px-6 lg:px-8">
        <main className="flex-1 py-6 lg:py-8">{children}</main>
        <BottomNav currentPage={currentPage} onNavigate={onNavigate} />
      </div>
    </div>
  );
}
