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
    <section className="grid overflow-hidden rounded-[2rem] border border-line bg-surface shadow-soft lg:grid-cols-[1fr_320px]">
      <div
        className="grid min-h-[330px] place-items-center border-2 border-dashed border-line bg-[#FFF8E8] p-6 text-center sm:m-5 sm:rounded-[1.5rem]"
        onDragOver={(event) => event.preventDefault()}
        onDrop={handleDrop}
      >
        {previewUrl ? (
          <div className="w-full space-y-4">
            <img
              src={previewUrl}
              alt="업로드한 음식 미리보기"
              className="mx-auto aspect-[4/3] max-h-64 w-full rounded-3xl object-cover shadow-sm"
            />
            <p className="text-sm text-stone-500">이미지가 준비됐어요. 분석을 시작해볼게요.</p>
          </div>
        ) : (
          <div className="space-y-5">
            <div className="mx-auto grid h-20 w-20 place-items-center rounded-3xl bg-sage text-leaf">
              <Camera className="h-10 w-10" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-forest">여기를 클릭하거나 드래그해서 업로드</h2>
              <p className="mt-2 text-sm text-stone-500">JPG, PNG 파일, 최대 10MB</p>
            </div>
          </div>
        )}
      </div>

      <input ref={inputRef} type="file" accept="image/png,image/jpeg" className="hidden" onChange={handleChange} />

      <aside className="border-t border-line bg-cream p-5 lg:border-l lg:border-t-0">
        <p className="text-sm font-black text-leaf">Scan workspace</p>
        <h2 className="mt-1 text-2xl font-black text-forest">사진을 넣고 바로 분석</h2>
        <div className="mt-5 space-y-3">
          <button
            onClick={() => inputRef.current?.click()}
            className="inline-flex w-full items-center justify-center gap-2 rounded-2xl border border-line bg-white px-5 py-3 font-bold text-forest"
          >
            <ImagePlus className="h-5 w-5" />
            갤러리에서 선택
          </button>
          <button
            onClick={onAnalyze}
            disabled={!previewUrl || isLoading}
            className="inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-leaf px-5 py-3 font-bold text-white shadow-soft disabled:cursor-not-allowed disabled:bg-stone-300"
          >
            {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <UploadCloud className="h-5 w-5" />}
            분석 시작하기
          </button>
        </div>
        <div className="mt-6 space-y-3 rounded-3xl bg-surface p-4">
          <p className="text-sm font-black text-forest">촬영 체크</p>
          {["밝은 조명", "음식 전체 노출", "한 끼 단위 사진"].map((item) => (
            <div key={item} className="flex items-center gap-2 text-sm font-semibold text-stone-600">
              <span className="h-2 w-2 rounded-full bg-leaf" />
              {item}
            </div>
          ))}
        </div>
        <p className="mt-4 text-xs leading-5 text-stone-500">업로드된 이미지는 분석 데모를 위해서만 사용됩니다.</p>
      </aside>
    </section>
  );
}
