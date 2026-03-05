import {
  BarChart as RechartsBarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Spinner from "@/components/ui/Spinner";
import { colors } from "@/styles/theme";

export interface BarChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  bars: { dataKey: string; name?: string; color?: string }[];
  height?: number;
  isLoading?: boolean;
  xLabel?: string;
  yLabel?: string;
  className?: string;
}

const DEFAULT_COLORS = [
  colors.cuRed,
  "#2563EB",
  "#16A34A",
  "#D97706",
  "#7C3AED",
  "#DB2777",
];

export default function BarChart({
  data,
  xKey,
  bars,
  height = 280,
  isLoading = false,
  className = "",
}: BarChartProps) {
  if (isLoading) {
    return (
      <div style={{ height }} className={`flex items-center justify-center ${className}`}>
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className={className} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsBarChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 11, fill: "#6B7280" }}
            tickLine={false}
            axisLine={{ stroke: "#E5E7EB" }}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6B7280" }}
            tickLine={false}
            axisLine={false}
            width={36}
          />
          <Tooltip
            contentStyle={{
              borderRadius: "0.375rem",
              border: "1px solid #E5E7EB",
              fontSize: "12px",
            }}
          />
          {bars.length > 1 && <Legend wrapperStyle={{ fontSize: "12px" }} />}
          {bars.map((bar, idx) => (
            <Bar
              key={bar.dataKey}
              dataKey={bar.dataKey}
              name={bar.name ?? bar.dataKey}
              fill={bar.color ?? DEFAULT_COLORS[idx % DEFAULT_COLORS.length]}
              radius={[3, 3, 0, 0]}
              maxBarSize={48}
            />
          ))}
        </RechartsBarChart>
      </ResponsiveContainer>
    </div>
  );
}
