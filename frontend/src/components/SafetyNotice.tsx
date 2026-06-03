import { ShieldCheck } from "lucide-react";

export function SafetyNotice() {
  return (
    <div className="flex gap-3 rounded-2xl border border-line bg-sage/70 p-4 text-sm text-forest">
      <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-leaf" />
      <p>
        본 결과는 의료 진단이나 치료 목적이 아닌 식습관 관리 참고용입니다. 저혈당 또는
        고혈당 증상이 있으면 실제 측정값을 확인하고 의료진과 상의하세요.
      </p>
    </div>
  );
}
