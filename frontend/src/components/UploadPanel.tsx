import { Camera, ImagePlus, Loader2, UploadCloud } from "lucide-react";
import { ChangeEvent, DragEvent, useRef } from "react";

type UploadPanelProps = {
  previewUrl?: string;
  isLoading: boolean;
  onFileSelect: (file: File) => void;
  onAnalyze: () => void;
};

export function UploadPanel({ previewUrl, isLoading, onFileSelect, onAnalyze }: UploadPanelProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFiles = (files: FileList | null) => {
    const file = files?.[0];
    if (file) onFileSelect(file);
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    handleFiles(event.target.files);
  };

  return (
    <section
      id="food-upload"
      className="grid overflow-hidden rounded-[2.25rem] border border-black/[0.06] bg-white shadow-[0_28px_90px_rgba(15,23,42,0.08)] lg:grid-cols-[1fr_360px]"
    >
      <div
        className="grid min-h-[360px] place-items-center border-2 border-dashed border-[#D8E8D2] bg-[#FAFAF7] p-6 text-center sm:m-6 sm:rounded-[1.75rem]"
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        {previewUrl ? (
          <div className="w-full space-y-4">
            <img
              src={previewUrl}
              alt="업로드한 음식 미리보기"
              className="mx-auto aspect-[4/3] max-h-72 w-full rounded-[1.75rem] object-cover shadow-[0_22px_60px_rgba(15,23,42,0.16)]"
            />
            <p className="text-sm font-semibold text-[#65716A]">이미지가 준비됐어요. 분석을 시작해볼게요.</p>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="mx-auto grid h-24 w-24 place-items-center rounded-[2rem] bg-[#E8F3E8] text-leaf shadow-sm">
              <Camera className="h-10 w-10" />
            </div>
            <div>
              <h2 className="text-2xl font-black tracking-[-0.01em] text-[#101827]">
                여기를 클릭하거나 드래그해서 업로드
              </h2>
              <p className="mt-2 text-sm font-semibold text-[#65716A]">JPG, PNG 파일, 최대 10MB</p>
            </div>
          </div>
        )}
      </div>

      <input ref={inputRef} type="file" accept="image/png,image/jpeg" className="hidden" onChange={handleChange} />

      <aside className="border-t border-black/[0.06] bg-[#071F18] p-6 text-white lg:border-l lg:border-t-0">
        <p className="text-sm font-black text-[#58D68D]">Scan workspace</p>
        <h2 className="mt-2 text-3xl font-black leading-tight tracking-[-0.02em]">사진을 넣고 바로 분석</h2>
        <p className="mt-3 text-sm leading-6 text-white/68">
          음식명, 영양성분, 혈당 부담 참고 점수를 한 번에 확인합니다.
        </p>
        <div className="mt-5 space-y-3">
          <button
            onClick={() => inputRef.current?.click()}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full border border-white/15 bg-white px-5 py-4 font-black text-[#101827]"
          >
            <ImagePlus className="h-5 w-5" />
            갤러리에서 선택
          </button>
          <button
            onClick={onAnalyze}
            disabled={!previewUrl || isLoading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[#58D68D] px-5 py-4 font-black text-[#071F18] shadow-soft disabled:cursor-not-allowed disabled:bg-white/20 disabled:text-white/45"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <UploadCloud className="h-5 w-5" />}
            분석 시작하기
          </button>
        </div>
        <div className="mt-6 space-y-3 rounded-[1.5rem] bg-white/10 p-4">
          <p className="text-sm font-black text-white">촬영 체크</p>
          {["밝은 조명", "음식 전체 노출", "한 끼 단위 사진"].map((item) => (
            <div key={item} className="flex items-center gap-2 text-sm font-semibold text-white/72">
              <span className="h-2 w-2 rounded-full bg-[#58D68D]" />
              {item}
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs leading-5 text-white/48">업로드된 이미지는 분석 데모를 위해서만 사용됩니다.</p>
      </aside>
    </section>
  );
}
