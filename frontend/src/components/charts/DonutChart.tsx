import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import Spinner from "@/components/ui/Spinner";
import { colors } from "@/styles/theme";

export interface DonutChartProps {
  data: { name: string; value: number; color?: string }[];
  height?: number;
  isLoading?: boolean;
  innerRadius?: number;
  outerRadius?: number;
  /** Center label text */
  centerLabel?: string;
  className?: string;
}

const DEFAULT_COLORS = [
  colors.cuRed,
  "#2563EB",
  "#16A34A",
  "#D97706",
  "#7C3AED",
  "#DB2777",
  "#0891B2",
];

export default function DonutChart({
  data,
  height = 280,
  isLoading = false,
  innerRadius = 60,
  outerRadius = 90,
  centerLabel: _centerLabel,
  className = "",
}: DonutChartProps) {
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
        <PieChart margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            dataKey="value"
            paddingAngle={2}
          >
            {data.map((entry, idx) => (
              <Cell
                key={`cell-${idx}`}
                fill={entry.color ?? DEFAULT_COLORS[idx % DEFAULT_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              borderRadius: "0.375rem",
              border: "1px solid #E5E7EB",
              fontSize: "12px",
            }}
            formatter={(value: number, name: string) => [value.toLocaleString(), name]}
          />
          <Legend
            wrapperStyle={{ fontSize: "12px" }}
            formatter={(value) => <span style={{ color: "#374151" }}>{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
