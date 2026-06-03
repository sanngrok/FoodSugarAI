import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { GlucosePredictionResult } from "../data/mockData";

type GlucoseChartProps = {
  prediction: GlucosePredictionResult;
};

export function GlucoseChart({ prediction }: GlucoseChartProps) {
  const data: ChartPoint[] = [
    {
      label: "현재",
      value: prediction.currentGlucose,
      low: prediction.currentGlucose,
      high: prediction.currentGlucose,
      rangeBase: prediction.currentGlucose,
      rangeSize: 0,
    },
    {
      label: "30분",
      value: prediction.predictions["30"],
      low: prediction.intervals["30"][0],
      high: prediction.intervals["30"][1],
      rangeBase: prediction.intervals["30"][0],
      rangeSize: prediction.intervals["30"][1] - prediction.intervals["30"][0],
    },
    {
      label: "60분",
      value: prediction.predictions["60"],
      low: prediction.intervals["60"][0],
      high: prediction.intervals["60"][1],
      rangeBase: prediction.intervals["60"][0],
      rangeSize: prediction.intervals["60"][1] - prediction.intervals["60"][0],
    },
    {
      label: "90분",
      value: prediction.predictions["90"],
      low: prediction.intervals["90"][0],
      high: prediction.intervals["90"][1],
      rangeBase: prediction.intervals["90"][0],
      rangeSize: prediction.intervals["90"][1] - prediction.intervals["90"][0],
    },
    {
      label: "120분",
      value: 134,
      low: 98,
      high: 188,
      rangeBase: 98,
      rangeSize: 90,
    },
  ];

  return (
    <section className="rounded-[2rem] border border-line bg-surface p-5 shadow-soft">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-leaf">CGM 예측 그래프</p>
          <h3 className="text-xl font-black text-forest">혈당 변화 가능성</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <p className="rounded-full bg-sage px-3 py-1 text-xs font-bold text-forest">목표 범위 70~180 mg/dL</p>
          <p className="rounded-full bg-[#FFF1D6] px-3 py-1 text-xs font-bold text-[#A4560A]">예측 범위 band</p>
        </div>
      </div>
      <div className="mt-5 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 8, bottom: 0, left: -16 }}>
            <CartesianGrid stroke="#D8E8D2" strokeDasharray="4 4" />
            <XAxis dataKey="label" tick={{ fill: "#6B7280", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#6B7280", fontSize: 12 }} axisLine={false} tickLine={false} domain={[50, 230]} />
            <Tooltip content={<PredictionTooltip />} />
            <ReferenceArea y1={70} y2={180} fill="#E8F3E8" fillOpacity={0.7} />
            <ReferenceLine y={70} stroke="#1F7A43" strokeDasharray="3 3" strokeOpacity={0.45} />
            <ReferenceLine y={180} stroke="#1F7A43" strokeDasharray="3 3" strokeOpacity={0.45} />
            <Area
              type="monotone"
              dataKey="rangeBase"
              stackId="interval"
              stroke="none"
              fill="transparent"
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="rangeSize"
              stackId="interval"
              stroke="none"
              fill="#F97316"
              fillOpacity={0.18}
              isAnimationActive={false}
            />
            <Line type="monotone" dataKey="value" stroke="#1F7A43" strokeWidth={3} dot={{ r: 5, fill: "#1F7A43" }} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

type ChartPoint = {
  label: string;
  value: number;
  low: number;
  high: number;
  rangeBase: number;
  rangeSize: number;
};

type TooltipPayload = {
  payload: ChartPoint;
};

type PredictionTooltipProps = {
  active?: boolean;
  payload?: TooltipPayload[];
};

function PredictionTooltip({ active, payload }: PredictionTooltipProps) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;

  return (
    <div className="rounded-2xl border border-line bg-surface p-3 shadow-soft">
      <p className="text-sm font-black text-forest">{point.label}</p>
      <p className="mt-1 text-sm text-stone-600">참고 수치 {point.value} mg/dL</p>
      <p className="text-sm text-stone-600">
        예측 범위 {point.low}~{point.high} mg/dL
      </p>
    </div>
  );
}
