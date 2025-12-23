import { BarChart3, TrendingUp, TrendingDown, Users, ShoppingBag, Clock } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import type { WeeklyDataPoint, HourlyDataPoint, CategoryData, AnalyticsStat } from "@/api/types";
import { mockWeeklyData, mockHourlyCustomers, mockCategoryData, mockAnalyticsStats } from "@/api/mockData";

const AnalyticsContent = () => {
  // Data from API layer
  const weeklyData: WeeklyDataPoint[] = mockWeeklyData;
  const hourlyCustomers: HourlyDataPoint[] = mockHourlyCustomers;
  const categoryData: CategoryData[] = mockCategoryData;
  const stats: AnalyticsStat[] = mockAnalyticsStats;

  const getStatIcon = (iconType: AnalyticsStat["iconType"]) => {
    switch (iconType) {
      case "trending": return TrendingUp;
      case "users": return Users;
      case "shopping": return ShoppingBag;
      case "clock": return Clock;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <BarChart3 className="w-7 h-7 text-primary" />
          분석
        </h2>
        <p className="text-muted-foreground mt-1">Analytics Dashboard</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, index) => {
          const Icon = getStatIcon(stat.iconType);
          return (
            <div
              key={index}
              className="bg-card rounded-2xl p-5 border border-border hover:shadow-lg transition-all"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="p-2 rounded-lg bg-primary/20">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
                <span className={`text-sm font-medium flex items-center gap-1 ${
                  stat.trend === "up" ? "text-success" : "text-destructive"
                }`}>
                  {stat.trend === "up" ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  {stat.change}
                </span>
              </div>
              <p className="text-2xl font-bold text-foreground">{stat.value}</p>
              <p className="text-sm text-muted-foreground mt-1">{stat.label}</p>
            </div>
          );
        })}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Revenue Chart */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">📊 주간 매출 추이</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => `${(v / 1000000).toFixed(1)}M`} />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
                formatter={(value: number) => [`₩${value.toLocaleString()}`, "매출"]}
              />
              <Bar dataKey="revenue" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Hourly Customer Flow */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">👥 시간대별 고객 수</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={hourlyCustomers}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="hour" stroke="hsl(var(--muted-foreground))" tickFormatter={(v) => `${v}시`} />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))" }}
                formatter={(value: number) => [`${value}명`, "고객 수"]}
              />
              <Line 
                type="monotone" 
                dataKey="customers" 
                stroke="hsl(var(--accent))" 
                strokeWidth={3}
                dot={{ fill: "hsl(var(--accent))", strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Category Distribution */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">🍞 카테고리별 판매 비율</h3>
          <div className="flex items-center">
            <ResponsiveContainer width="60%" height={250}>
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {categoryData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "12px",
                  }}
                  formatter={(value: number) => [`${value}%`, "비율"]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex-1 space-y-2">
              {categoryData.map((item, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm text-muted-foreground flex-1">{item.name}</span>
                  <span className="text-sm font-medium text-foreground">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Customer Stats */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <h3 className="text-lg font-semibold text-foreground mb-4">📈 주간 방문객 추이</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={weeklyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="day" stroke="hsl(var(--muted-foreground))" />
              <YAxis stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "12px",
                }}
                formatter={(value: number) => [`${value}명`, "방문객"]}
              />
              <Bar dataKey="customers" fill="hsl(var(--accent))" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsContent;
