import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { TooltipProps } from "recharts";
import type { HourlyRevenuePoint } from "@/api/types";

const formatCurrency = (value: number) => {
  if (value >= 1000000) {
    return `₩${(value / 1000000).toFixed(1)}M`;
  }
  return `₩${(value / 1000).toFixed(0)}K`;
};

const CustomTooltip = ({ active, payload, label }: TooltipProps<number, string>) => {
  if (active && payload && payload.length && payload[0].value !== undefined) {
    return (
      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
        <p className="text-sm text-muted-foreground mb-1">{label}</p>
        <p className="text-lg font-bold text-primary">
          ₩{payload[0].value.toLocaleString()}
        </p>
      </div>
    );
  }
  return null;
};

interface HourlyRevenueChartProps {
  data?: HourlyRevenuePoint[];
}

const HourlyRevenueChart = ({ data = [] }: HourlyRevenueChartProps) => {
  const maxRevenue = data.length > 0 ? Math.max(...data.map(d => d.revenue)) : 0;
  const totalRevenue = data.reduce((sum, d) => sum + d.revenue, 0);
  const peakTime = data.find(d => d.revenue === maxRevenue)?.time || "N/A";

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-xl">📊</span>
        <h3 className="text-lg font-semibold text-foreground">Hourly Revenue</h3>
        <span className="text-sm text-muted-foreground ml-2">시간대별 매출</span>
      </div>

      {data.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-muted-foreground">
          매출 데이터가 없습니다
        </div>
      ) : (
        <>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(0 0% 25%)" vertical={false} />
                <XAxis
                  dataKey="time"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "hsl(0 0% 74%)", fontSize: 11 }}
                />
                <YAxis
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: "hsl(0 0% 74%)", fontSize: 11 }}
                  tickFormatter={formatCurrency}
                />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: "hsl(0 0% 25% / 0.3)" }} />
                <Bar
                  dataKey="revenue"
                  radius={[6, 6, 0, 0]}
                >
                  {data.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.revenue === maxRevenue ? "hsl(30 89% 67%)" : "hsl(16 56% 56%)"}
                      fillOpacity={0.8 + (entry.revenue / maxRevenue) * 0.2}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 pt-4 border-t border-border flex justify-between items-center">
            <div>
              <p className="text-sm text-muted-foreground">오늘 총 매출</p>
              <p className="text-xl font-bold text-foreground">₩{totalRevenue.toLocaleString()}</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">피크 시간</p>
              <p className="text-lg font-semibold text-accent">{peakTime}</p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default HourlyRevenueChart;
