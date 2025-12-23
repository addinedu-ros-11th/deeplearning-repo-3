import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import type { ProductSalesData } from "@/api/types";
import { mockProductSales } from "@/api/mockData";

const COLORS = [
  "hsl(16 56% 56%)",   // Terracotta
  "hsl(30 89% 67%)",   // Orange
  "hsl(20 41% 39%)",   // Brown
  "hsl(25 70% 55%)",   // Warm orange
  "hsl(35 80% 60%)",   // Light orange
  "hsl(15 45% 50%)",   // Dark terracotta
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
        <p className="font-semibold text-foreground">{data.name}</p>
        <p className="text-sm text-muted-foreground">{data.nameEn}</p>
        <p className="text-lg font-bold text-primary mt-1">{data.value}개 ({data.percentage}%)</p>
      </div>
    );
  }
  return null;
};

interface ProductSalesChartProps {
  data?: ProductSalesData[];
}

const ProductSalesChart = ({ data = mockProductSales }: ProductSalesChartProps) => {
  const totalSales = data.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="rounded-2xl border border-border bg-card p-6">
      <div className="flex items-center gap-2 mb-6">
        <span className="text-xl">🍞</span>
        <h3 className="text-lg font-semibold text-foreground">Product Sales</h3>
        <span className="text-sm text-muted-foreground ml-2">상품별 판매량</span>
      </div>

      <div className="h-64 relative">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={3}
              dataKey="value"
            >
              {data.map((_, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={COLORS[index % COLORS.length]}
                  stroke="hsl(0 0% 18%)"
                  strokeWidth={2}
                />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        
        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-sm text-muted-foreground">총 판매량</span>
          <span className="text-2xl font-bold text-foreground">{totalSales}개</span>
        </div>
      </div>

      {/* Custom Legend */}
      <div className="grid grid-cols-2 gap-2 mt-4 pt-4 border-t border-border">
        {data.map((item, index) => (
          <div key={item.name} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-full flex-shrink-0" 
              style={{ backgroundColor: COLORS[index % COLORS.length] }}
            />
            <span className="text-xs text-muted-foreground truncate">
              {item.name}
            </span>
            <span className="text-xs font-medium text-foreground ml-auto">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProductSalesChart;
