import { CheckCircle2, Database, Link2, LockKeyhole, Settings, XCircle } from "lucide-react";
import { SafetyNotice } from "../components/SafetyNotice";

export function SettingsPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <p className="text-sm font-bold text-leaf">설정 / 소개</p>
        <h1 className="text-3xl font-black text-forest">FoodSugar AI 소개</h1>
      </div>
      <section className="rounded-[2rem] border border-line bg-surface p-6 shadow-soft">
        <p className="text-lg leading-8 text-stone-600">
          FoodSugar AI는 음식 사진과 영양성분, CGM 데이터를 바탕으로 혈당 변화 가능성을 참고용으로 보여주는
          웰니스 서비스입니다. 본 결과는 의료 진단이나 치료 지침이 아닙니다.
        </p>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        <InfoCard icon={Link2} title="CGM 연결 상태" body="데모 모드에서는 샘플 CGM 데이터를 사용합니다." />
        <InfoCard icon={Database} title="데이터 처리 안내" body="업로드 이미지는 분석 흐름을 보여주기 위한 데모 입력으로 처리됩니다." />
        <InfoCard icon={LockKeyhole} title="개인정보 원칙" body="혈당, 식사, 인슐린 관련 값은 민감 정보로 보고 로그에 직접 남기지 않습니다." />
        <InfoCard icon={Settings} title="모델 한계" body="90분 예측은 불확실성이 높아 범위와 가능성 신호 중심으로 확인해야 합니다." />
      </div>
      <section className="rounded-[2rem] border border-line bg-surface p-6 shadow-soft">
        <div>
          <p className="text-sm font-bold text-leaf">안전한 사용 범위</p>
          <h2 className="mt-1 text-2xl font-black text-forest">이 앱이 하는 일 / 하지 않는 일</h2>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-3xl bg-sage/70 p-5">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-leaf" />
              <h3 className="font-black text-forest">하는 일</h3>
            </div>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-stone-600">
              <li>음식 사진을 바탕으로 음식명과 영양성분을 요약합니다.</li>
              <li>CGM 흐름이 있을 때 30분, 60분, 90분 혈당 변화 가능성을 범위로 보여줍니다.</li>
              <li>저혈당/고혈당 가능성 신호를 식습관 관리 참고 정보로 표시합니다.</li>
            </ul>
          </div>
          <div className="rounded-3xl bg-[#FFF8E8] p-5">
            <div className="flex items-center gap-2">
              <XCircle className="h-5 w-5 text-[#A4560A]" />
              <h3 className="font-black text-forest">하지 않는 일</h3>
            </div>
            <ul className="mt-4 space-y-3 text-sm leading-6 text-stone-600">
              <li>질병 여부를 판단하거나 의료 결정을 대신하지 않습니다.</li>
              <li>약물, 인슐린, 치료 계획에 대한 지시를 제공하지 않습니다.</li>
              <li>긴급 상황 판단이나 실제 CGM 측정값을 대체하지 않습니다.</li>
            </ul>
          </div>
        </div>
      </section>
      <SafetyNotice />
    </div>
  );
}

type InfoCardProps = {
  icon: typeof Settings;
  title: string;
  body: string;
};

function InfoCard({ icon: Icon, title, body }: InfoCardProps) {
  return (
    <article className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <Icon className="h-6 w-6 text-leaf" />
      <h2 className="mt-4 text-lg font-black text-forest">{title}</h2>
      <p className="mt-2 leading-7 text-stone-500">{body}</p>
    </article>
  );
}
