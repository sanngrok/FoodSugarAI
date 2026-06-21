import { ArrowRight, Camera, CheckCircle2, LineChart, ShieldCheck, Sparkles, Utensils } from "lucide-react";
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
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[2.5rem] bg-white px-5 py-8 shadow-[0_28px_90px_rgba(15,23,42,0.08)] sm:px-8 lg:min-h-[690px] lg:px-14 lg:py-12">
        <div className="pointer-events-none absolute left-10 top-10 h-28 w-28 rounded-full bg-sage blur-3xl" />
        <div className="pointer-events-none absolute bottom-12 right-[42%] h-36 w-36 rounded-full bg-[#FFF1D6] blur-3xl" />

        <div className="relative grid h-full items-center gap-10 lg:grid-cols-[0.95fr_1.05fr]">
          <div className="space-y-9">
            <div className="inline-flex items-center gap-2 rounded-full border border-black/[0.06] bg-[#FAFAF7] px-4 py-2 text-sm font-black text-[#59645D]">
              <Sparkles className="h-4 w-4 text-leaf" />
              Food scan first wellness dashboard
            </div>

            <div>
              <p className="text-lg font-semibold leading-8 text-[#65716A]">
                음식 사진에서 시작하는 식습관 관리 참고 프로그램
              </p>
              <h1 className="mt-7 max-w-3xl text-5xl font-black leading-[1.05] tracking-[-0.02em] text-[#101827] sm:text-6xl lg:text-7xl">
                음식 사진을
                <br />
                업로드해주세요
              </h1>
              <p className="mt-7 max-w-2xl text-lg leading-8 text-[#65716A]">
                WeMeet은 음식 스캔, 영양성분 확인, 90분 혈당 변화 가능성까지 한 흐름으로 보여주는
                웰니스 AI 앱입니다. 혈당 관련 결과는 의료 판단이 아닌 참고용으로만 제공합니다.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <a
                href="#food-upload"
                className="inline-flex items-center gap-2 rounded-full bg-[#071F18] px-6 py-4 text-sm font-black text-white shadow-soft transition hover:bg-[#123524]"
              >
                사진 넣고 분석하기
                <ArrowRight className="h-4 w-4 text-[#58D68D]" />
              </a>
              <button
                type="button"
                className="inline-flex items-center gap-2 rounded-full border border-black/[0.08] bg-white px-6 py-4 text-sm font-black text-[#101827] shadow-sm"
              >
                <ShieldCheck className="h-4 w-4 text-leaf" />
                비진단 참고용
              </button>
            </div>

            <div className="grid max-w-3xl gap-3 sm:grid-cols-3">
              {demoScenarios.map((scenario) => (
                <button
                  key={scenario.title}
                  type="button"
                  className="group rounded-[1.4rem] border border-black/[0.06] bg-[#FAFAF7] p-4 text-left shadow-sm transition hover:-translate-y-1 hover:border-leaf/40 hover:bg-sage"
                >
                  <span className="rounded-full bg-white px-3 py-1 text-xs font-black text-leaf shadow-sm">
                    {scenario.tag}
                  </span>
                  <strong className="mt-4 block text-sm font-black text-[#101827]">{scenario.title}</strong>
                  <span className="mt-1 block text-xs leading-5 text-[#65716A]">{scenario.body}</span>
                </button>
              ))}
            </div>

            <div className="grid max-w-2xl gap-3 sm:grid-cols-3">
              <FlowStep icon={Camera} label="사진 스캔" value="1" />
              <FlowStep icon={Utensils} label="음식 확인" value="2" />
              <FlowStep icon={LineChart} label="범위 예측" value="3" />
            </div>
          </div>

          <div className="relative min-h-[560px] lg:min-h-[620px]">
            <div className="absolute inset-x-4 top-0 overflow-hidden rounded-[2rem] bg-[#EDE7D6] shadow-[0_28px_90px_rgba(15,23,42,0.14)] sm:inset-x-10 lg:left-10 lg:right-0">
              <img
                src="https://images.unsplash.com/photo-1498837167922-ddd27525d352?auto=format&fit=crop&w=1100&q=80"
                alt="식사와 웰니스 루틴을 보여주는 참고 이미지"
                className="h-[440px] w-full object-cover opacity-80 grayscale-[8%]"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-white/10 via-white/25 to-[#FAFAF7]/90" />
            </div>

            <div className="absolute bottom-4 left-0 right-0 mx-auto w-[88%] rounded-[2rem] border border-white/70 bg-white/78 p-5 shadow-[0_28px_90px_rgba(15,23,42,0.18)] backdrop-blur-xl sm:w-[76%] lg:left-4 lg:right-auto lg:w-[74%]">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-black text-leaf">AI 식사 분석</p>
                  <p className="mt-1 text-3xl font-black tracking-[-0.02em] text-[#101827]">비빔밥</p>
                </div>
                <span className="rounded-full bg-[#E8F3E8] px-4 py-2 text-xs font-black text-leaf">
                  실제 모델 / 데모 구분
                </span>
              </div>

              <div className="mt-5 grid grid-cols-3 gap-2 text-center">
                <MiniMetric label="탄수" value="85g" />
                <MiniMetric label="단백질" value="22g" />
                <MiniMetric label="섬유" value="6g" />
              </div>

              <div className="mt-4 rounded-[1.5rem] bg-[#F2F8F2] p-4 text-[#101827]">
                <div className="flex items-end justify-between gap-3">
                  <div>
                    <p className="text-xs font-black text-leaf">90분 예상 범위</p>
                    <p className="mt-1 text-4xl font-black tracking-[-0.02em]">104~205</p>
                  </div>
                  <span className="rounded-full bg-[#FFF1D6] px-3 py-1 text-xs font-black text-[#A4560A]">
                    불확실성 높음
                  </span>
                </div>
                <div className="mt-5 flex h-20 items-end gap-2">
                  {[32, 46, 58, 50, 66, 45, 36].map((height, index) => (
                    <span
                      key={index}
                      className="flex-1 rounded-t-full bg-leaf"
                      style={{ height: `${height}px`, opacity: 0.36 + index * 0.07 }}
                    />
                  ))}
                </div>
              </div>
            </div>

            <div className="absolute left-2 top-20 hidden rounded-[1.5rem] border border-white/70 bg-white/72 p-4 shadow-soft backdrop-blur-xl xl:block">
              <div className="flex items-center gap-2 text-sm font-black text-[#101827]">
                <CheckCircle2 className="h-5 w-5 text-leaf" />
                참고용 안전 문구 포함
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
    <div className="flex items-center gap-3 rounded-full border border-black/[0.06] bg-white px-4 py-3 shadow-sm">
      <span className="grid h-9 w-9 place-items-center rounded-full bg-[#071F18] text-sm font-black text-white">
        {value}
      </span>
      <Icon className="h-5 w-5 text-leaf" />
      <span className="text-sm font-black text-[#101827]">{label}</span>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.25rem] bg-white p-3 shadow-sm">
      <p className="text-xs font-bold text-[#7B857E]">{label}</p>
      <p className="font-black text-[#101827]">{value}</p>
    </div>
  );
}
