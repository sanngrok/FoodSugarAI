import { Camera, CheckCircle2, LineChart, Sparkles, Utensils } from "lucide-react";
import { UploadPanel } from "../components/UploadPanel";
import { demoScenarios } from "../data/mockData";

type HomePageProps = {
  previewUrl?: string;
  isLoading: boolean;
  onFileSelect: (file: File) => void;
  onAnalyze: () => void;
};

export function HomePage({ previewUrl, isLoading, onFileSelect, onAnalyze }: HomePageProps) {
  return (
    <div className="space-y-5">
      <section className="grid overflow-hidden rounded-[2rem] border border-line bg-surface shadow-soft lg:grid-cols-[1fr_430px]">
        <div className="space-y-7 p-6 sm:p-8 lg:p-10">
          <div className="inline-flex items-center gap-2 rounded-full bg-sage px-4 py-2 text-sm font-bold text-leaf">
            <Sparkles className="h-4 w-4" />
            Wellness AI Demo
          </div>
          <div>
            <h1 className="max-w-2xl text-5xl font-black leading-[1.02] tracking-tight text-forest sm:text-6xl">
              음식 사진을
              <br />
              업로드해주세요
            </h1>
            <p className="mt-5 max-w-2xl text-lg leading-8 text-stone-600">
              사진을 먼저 스캔하고, 음식 확인, 영양성분, 90분 혈당 변화 가능성을 한 화면 흐름으로 확인합니다.
            </p>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            {demoScenarios.map((scenario) => (
              <button
                key={scenario.title}
                type="button"
                className="rounded-3xl border border-line bg-cream p-4 text-left shadow-sm transition hover:border-leaf hover:bg-sage/70"
              >
                <span className="rounded-full bg-sage px-3 py-1 text-xs font-black text-leaf">{scenario.tag}</span>
                <strong className="mt-3 block text-sm font-black text-forest">{scenario.title}</strong>
                <span className="mt-1 block text-xs leading-5 text-stone-500">{scenario.body}</span>
              </button>
            ))}
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <FlowStep icon={Camera} label="사진 스캔" value="1" />
            <FlowStep icon={Utensils} label="음식 확인" value="2" />
            <FlowStep icon={LineChart} label="범위 예측" value="3" />
          </div>
        </div>
        <div className="border-t border-line bg-forest p-5 text-white lg:border-l lg:border-t-0">
          <div className="h-full rounded-[1.5rem] border border-white/10 bg-white/[0.08] p-4">
            <div className="flex items-center justify-between">
              <span className="rounded-full bg-[#FFF1D6] px-3 py-1 text-xs font-black text-[#A4560A]">
                예시 미리보기
              </span>
              <span className="rounded-full bg-white/12 px-3 py-1 text-xs font-black text-white">
                실제 분석 결과 아님
              </span>
            </div>
            <div className="mt-6 rounded-3xl bg-[#FFFDF5] p-4 text-forest">
              <div className="mb-3 flex items-center gap-2 rounded-2xl bg-[#FFF8E8] px-3 py-2 text-xs font-bold text-[#A4560A]">
                <CheckCircle2 className="h-4 w-4" />
                아래 값은 화면 구성을 보여주는 데모 예시입니다.
              </div>
              <div className="grid aspect-[4/3] place-items-center rounded-2xl bg-[#FFF1D6] text-leaf">
                <Utensils className="h-16 w-16" />
              </div>
              <p className="mt-4 text-sm font-bold text-leaf">음식 분석 결과</p>
              <p className="text-3xl font-black">비빔밥</p>
              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <MiniMetric label="탄수" value="85g" />
                <MiniMetric label="단백질" value="22g" />
                <MiniMetric label="섬유" value="6g" />
              </div>
            </div>
            <div className="mt-4 rounded-3xl bg-[#E8F3E8] p-4 text-forest">
              <div className="flex items-end justify-between">
                <div>
                  <p className="text-xs font-black text-leaf">90분 예상 범위</p>
                  <p className="text-2xl font-black">104~205</p>
                </div>
                <span className="rounded-full bg-[#FFF1D6] px-3 py-1 text-xs font-black text-[#A4560A]">불확실성 높음</span>
              </div>
              <div className="mt-4 flex h-16 items-end gap-2">
                {[32, 46, 58, 50, 62, 44, 35].map((height, index) => (
                  <span
                    key={index}
                    className="flex-1 rounded-t-full bg-leaf"
                    style={{ height: `${height}px`, opacity: 0.45 + index * 0.06 }}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
      <UploadPanel previewUrl={previewUrl} isLoading={isLoading} onFileSelect={onFileSelect} onAnalyze={onAnalyze} />
    </div>
  );
}

type StepIcon = typeof Camera;

function FlowStep({ icon: Icon, label, value }: { icon: StepIcon; label: string; value: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-line bg-surface px-4 py-3">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-leaf text-sm font-black text-white">{value}</span>
      <Icon className="h-5 w-5 text-leaf" />
      <span className="text-sm font-black text-forest">{label}</span>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-sage p-3">
      <p className="text-xs font-bold text-stone-500">{label}</p>
      <p className="font-black text-forest">{value}</p>
    </div>
  );
}
