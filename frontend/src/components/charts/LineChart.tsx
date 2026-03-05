import {
  LineChart as RechartsLineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Spinner from "@/components/ui/Spinner";
import { colors } from "@/styles/theme";

export interface LineChartProps {
  data: Record<string, unknown>[];
  xKey: string;
  lines: { dataKey: string; name?: string; color?: string }[];
  height?: number;
  isLoading?: boolean;
  className?: string;
}

const DEFAULT_COLORS = [
  colors.cuRed,
  "#2563EB",
  "#16A34A",
  "#D97706",
  "#7C3AED",
];

export default function LineChart({
  data,
  xKey,
  lines,
  height = 280,
  isLoading = false,
  className = "",
}: LineChartProps) {
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
        <RechartsLineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
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
          {lines.length > 1 && <Legend wrapperStyle={{ fontSize: "12px" }} />}
          {lines.map((line, idx) => (
            <Line
              key={line.dataKey}
              type="monotone"
              dataKey={line.dataKey}
              name={line.name ?? line.dataKey}
              stroke={line.color ?? DEFAULT_COLORS[idx % DEFAULT_COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3, strokeWidth: 2 }}
              activeDot={{ r: 5 }}
            />
          ))}
        </RechartsLineChart>
      </ResponsiveContainer>
    </div>
  );
}
