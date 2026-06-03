type ResultSourceBadgeProps = {
  isDemo?: boolean;
};

export function ResultSourceBadge({ isDemo }: ResultSourceBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-black ${
        isDemo ? "bg-[#FFF1D6] text-[#A4560A]" : "bg-sage text-leaf"
      }`}
    >
      {isDemo ? "데모 데이터" : "실제 모델 결과"}
    </span>
  );
}
