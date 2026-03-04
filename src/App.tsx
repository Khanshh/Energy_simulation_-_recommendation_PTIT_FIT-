import React, { useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  BarChart, Bar
} from 'recharts';
import {
  Zap, DollarSign, Activity, AlertTriangle, CheckCircle,
  ArrowUpRight, ArrowDownRight, Globe
} from 'lucide-react';
import { MOCK_TIME_SERIES, MOCK_ZONE_DATA, MOCK_METRICS, MOCK_SUGGESTIONS } from './data/mockData';
import { cn } from './lib/utils';

// Import Logos
import riptLogo from './assets/ript.png';
import ptitLogo from './assets/ptit.png';
import fitLogo from './assets/FIT_new.png';

// UI Components
const Card = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <div className={cn("rounded-xl border bg-card text-card-foreground shadow-sm", className)}>
    {children}
  </div>
);

const CardHeader = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <div className={cn("flex flex-col space-y-1.5 p-6", className)}>{children}</div>
);

const CardTitle = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <h3 className={cn("font-semibold leading-none tracking-tight text-lg", className)}>{children}</h3>
);

const CardContent = ({ children, className }: { children: React.ReactNode, className?: string }) => (
  <div className={cn("p-6 pt-0", className)}>{children}</div>
);

const Badge = ({ children, variant = "default", className }: { children: React.ReactNode, variant?: "default" | "destructive" | "success" | "warning", className?: string }) => {
  const variants = {
    default: "bg-primary text-primary-foreground",
    destructive: "bg-destructive text-destructive-foreground",
    success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
    warning: "bg-amber-500/15 text-amber-700 dark:text-amber-400"
  };
  return (
    <span className={cn("inline-flex items-center rounded-md px-2.5 py-0.5 text-xs font-semibold transition-colors", variants[variant], className)}>
      {children}
    </span>
  );
};

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'suggestions'>('overview');
  const [language, setLanguage] = useState<string>('vi');

  const handleLanguageChange = (value: string) => {
    setLanguage(value);
    // Gợi ý: Sau này bạn có thể dùng react-i18next để đổi text
    console.log(`Đã chuyển ngôn ngữ sang: ${value}`);
  };

  const metricCards = [
    {
      title: "Total Energy (24h)",
      simulated: MOCK_METRICS.totalSimulatedkWh.toFixed(1),
      actual: MOCK_METRICS.totalActualkWh.toFixed(1),
      unit: "kWh",
      icon: Zap,
      variance: ((MOCK_METRICS.totalActualkWh - MOCK_METRICS.totalSimulatedkWh) / MOCK_METRICS.totalSimulatedkWh) * 100
    },
    {
      title: "Estimated Cost",
      simulated: MOCK_METRICS.estimatedCostSimulated.toFixed(2),
      actual: MOCK_METRICS.estimatedCostActual.toFixed(2),
      unit: "$",
      icon: DollarSign,
      variance: ((MOCK_METRICS.estimatedCostActual - MOCK_METRICS.estimatedCostSimulated) / MOCK_METRICS.estimatedCostSimulated) * 100
    },
    {
      title: "Peak Demand",
      simulated: MOCK_METRICS.peakDemandSimulated.toFixed(1),
      actual: MOCK_METRICS.peakDemandActual.toFixed(1),
      unit: "kW",
      icon: Activity,
      variance: ((MOCK_METRICS.peakDemandActual - MOCK_METRICS.peakDemandSimulated) / MOCK_METRICS.peakDemandSimulated) * 100
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground dark">
      {/* ===== HEADER: CHỨA LOGO VÀ BỘ CHUYỂN ĐỔI NGÔN NGỮ ===== */}
      <header className="border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80 sticky top-0 z-10 shadow-sm">
        <div className="container mx-auto px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-4 min-h-[70px]">
          {/* Cụm Logo đối tác */}
          <div className="flex items-center gap-[15px] bg-[#1a1f2c] p-[10px] rounded-[5px] shrink-0">
            <div className="flex justify-center items-center w-[60px] h-[60px] md:w-[80px] md:h-[80px] bg-white rounded-[5px] overflow-hidden shrink-0">
              <img src={riptLogo} alt="RIPT Logo" className="w-full h-full object-cover object-center bg-white" />
            </div>
            <div className="flex justify-center items-center w-[60px] h-[60px] md:w-[80px] md:h-[80px] bg-white rounded-[5px] overflow-hidden shrink-0">
              <img src={ptitLogo} alt="PTIT Logo" className="w-full h-full object-cover object-center bg-white scale-[1.7] md:scale-[1.8]" />
            </div>
            <div className="flex justify-center items-center w-[60px] h-[60px] md:w-[80px] md:h-[80px] bg-white rounded-[5px] overflow-hidden shrink-0">
              <img src={fitLogo} alt="FIT Logo" className="w-full h-full object-cover object-center bg-white invert hue-rotate-180 brightness-110 contrast-125 saturate-[1.2]" />
            </div>
          </div>

          {/* Cụm Đổi Ngôn ngữ */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 border border-border rounded-md px-3 py-1.5 bg-background shadow-sm hover:border-primary/50 transition-colors">
              <Globe size={18} className="text-primary" />
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="bg-transparent text-sm font-medium outline-none border-none cursor-pointer text-foreground appearance-none pr-4"
              >
                <option value="vi">🇻🇳 Tiếng Việt</option>
                <option value="en">🇬🇧 English</option>
                <option value="ja">🇯🇵 日本語</option>
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* ===== PHẦN 1: GIỚI THIỆU DỰ ÁN (ABOUT & GOALS) ===== */}
        <Card className="mb-8 border-border shadow-sm">
          <CardHeader className="pb-3 border-b border-border/50 bg-muted/20">
            <CardTitle className="text-xl">About Project</CardTitle>
          </CardHeader>
          <CardContent className="pt-5 space-y-4">
            <p className="text-[15px] leading-relaxed text-foreground/90">
              Interactive sensor data analysis and correlation system. This is a collaborative research platform between the <strong className="font-semibold text-foreground">Research Institute of Posts and Telecommunications (RIPT - PTIT)</strong> and <strong className="font-semibold text-foreground">Fukuoka Institute of Technology (FIT)</strong>.
            </p>
            <p className="text-[15px] leading-relaxed text-foreground/90">
              <strong className="font-semibold text-foreground">Goals:</strong> Visualize the deviation between software-simulated data and real-world user data, allowing the system to automatically provide actionable recommendations to improve sensor accuracy.
            </p>
          </CardContent>
        </Card>

        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">Dashboard Overview</h2>
            <p className="text-muted-foreground mt-1">Comparing real-time sensor data with digital twin simulation.</p>
          </div>

          <div className="bg-muted p-1 rounded-lg flex inline-flex">
            <button
              onClick={() => setActiveTab('overview')}
              className={cn("px-4 py-2 text-sm font-medium rounded-md transition-all", activeTab === 'overview' ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground")}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab('suggestions')}
              className={cn("px-4 py-2 text-sm font-medium rounded-md transition-all flex items-center gap-2", activeTab === 'suggestions' ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground")}
            >
              Optimization <Badge variant="warning" className="ml-1 px-1.5 py-0 h-4 text-[10px]">3</Badge>
            </button>
          </div>
        </div>

        {activeTab === 'overview' ? (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {metricCards.map((metric, i) => {
                const isPositiveVariance = metric.variance > 0;
                return (
                  <Card key={i} className="relative overflow-hidden group hover:border-primary/50 transition-colors">
                    <div className="absolute right-0 top-0 w-24 h-24 bg-gradient-to-bl from-primary/10 to-transparent rounded-bl-full opacity-50 group-hover:opacity-100 transition-opacity" />
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-center">
                        <p className="text-sm font-medium text-muted-foreground">{metric.title}</p>
                        <metric.icon size={18} className="text-muted-foreground" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-end justify-between">
                        <div>
                          <div className="text-3xl font-bold">
                            {metric.unit === '$' && '$'}
                            {metric.actual}
                            {metric.unit !== '$' && <span className="text-sm font-normal text-muted-foreground ml-1">{metric.unit}</span>}
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">
                            Simulated: {metric.unit === '$' && '$'}{metric.simulated}
                          </p>
                        </div>
                        <div className={cn("flex flex-col items-end text-sm font-medium", isPositiveVariance ? "text-destructive" : "text-emerald-500")}>
                          <div className="flex items-center">
                            {isPositiveVariance ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                            {Math.abs(metric.variance).toFixed(1)}%
                          </div>
                          <span className="text-[10px] text-muted-foreground">vs Simulated</span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>

            {/* Main Chart */}
            <Card className="col-span-1 lg:col-span-3">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div>
                  <CardTitle className="text-xl">Power Consumption (24h)</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">Sensor data vs Digital Twin Model</p>
                </div>
                <div className="flex items-center gap-4 text-sm bg-muted/50 px-3 py-1.5 rounded-md border">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-primary"></div>
                    <span className="text-muted-foreground">Simulated</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-destructive"></div>
                    <span className="text-muted-foreground">Actual</span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-[400px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={MOCK_TIME_SERIES} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                      <XAxis
                        dataKey="time"
                        stroke="var(--muted-foreground)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickMargin={10}
                      />
                      <YAxis
                        yAxisId="left"
                        stroke="var(--muted-foreground)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value}kW`}
                        tickMargin={10}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        stroke="var(--muted-foreground)"
                        fontSize={12}
                        tickLine={false}
                        axisLine={false}
                        tickFormatter={(value) => `${value}°C`}
                      />
                      <RechartsTooltip
                        contentStyle={{
                          backgroundColor: 'var(--popover)',
                          border: '1px solid var(--border)',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
                        }}
                        itemStyle={{ color: 'var(--foreground)' }}
                        labelStyle={{ color: 'var(--muted-foreground)', marginBottom: '8px' }}
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="simulated"
                        name="Simulated (kW)"
                        stroke="var(--primary)"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                      />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="actual"
                        name="Actual (kW)"
                        stroke="var(--destructive)"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6, strokeWidth: 0 }}
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="temperature"
                        name="Temp (°C)"
                        stroke="var(--muted-foreground)"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Bottom Row: Zones & Impact */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>Consumption by Zone</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">Where is the deviation occurring?</p>
                </CardHeader>
                <CardContent>
                  <div className="h-[300px] w-full mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={MOCK_ZONE_DATA} margin={{ top: 20, right: 30, left: 0, bottom: 5 }} layout="vertical">
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="var(--border)" />
                        <XAxis type="number" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis dataKey="name" type="category" stroke="var(--muted-foreground)" fontSize={12} tickLine={false} axisLine={false} width={100} />
                        <RechartsTooltip
                          cursor={{ fill: 'var(--muted)' }}
                          contentStyle={{
                            backgroundColor: 'var(--popover)',
                            border: '1px solid var(--border)',
                            borderRadius: '8px'
                          }}
                        />
                        <Legend wrapperStyle={{ paddingTop: '20px' }} />
                        <Bar dataKey="simulated" name="Simulated" fill="var(--primary)" radius={[0, 4, 4, 0]} />
                        <Bar dataKey="actual" name="Actual" fill="var(--destructive)" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Zone Variances</CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">Percentage deviance from simulation</p>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6 mt-4">
                    {MOCK_ZONE_DATA.map((zone, idx) => (
                      <div key={idx} className="flex items-center justify-between group">
                        <div className="space-y-1">
                          <p className="text-sm font-medium leading-none">{zone.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {zone.actual}kW vs {zone.simulated}kW
                          </p>
                        </div>
                        <div className={cn(
                          "flex items-center gap-2 px-2.5 py-1 rounded-md text-sm font-medium transition-colors",
                          zone.variance > 0 ? "bg-destructive/10 text-destructive" : "bg-emerald-500/10 text-emerald-500"
                        )}>
                          {zone.variance > 0 ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                          {Math.abs(zone.variance)}%
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-8">
                    <button
                      onClick={() => setActiveTab('suggestions')}
                      className="w-full py-2.5 rounded-lg bg-secondary/50 hover:bg-secondary text-secondary-foreground font-medium text-sm transition-colors flex items-center justify-center gap-2"
                    >
                      View Optimization Suggestions <ArrowUpRight size={16} />
                    </button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="mb-6 max-w-2xl">
              <h3 className="text-xl font-semibold flex items-center gap-2">
                <AlertTriangle className="text-amber-500" /> Actionable Insights
              </h3>
              <p className="text-muted-foreground mt-2">
                Based on the discrepancies between the simulated digital twin and the actual sensor data, we have identified these optimization opportunities to reduce energy waste.
              </p>
            </div>

            <div className="grid gap-6">
              {MOCK_SUGGESTIONS.map((suggestion) => (
                <Card key={suggestion.id} className="border-l-4 border-l-primary overflow-hidden">
                  <div className="flex flex-col md:flex-row">
                    <div className="p-6 md:w-2/3 border-b md:border-b-0 md:border-r border-border">
                      <div className="flex items-center gap-2 mb-3">
                        <Badge variant="default">{suggestion.category}</Badge>
                        <Badge variant={suggestion.impact === 'High' ? 'destructive' : 'warning'}>
                          {suggestion.impact} Impact
                        </Badge>
                      </div>
                      <h4 className="text-lg font-semibold mb-2">{suggestion.title}</h4>
                      <p className="text-muted-foreground text-sm mb-4 leading-relaxed">
                        {suggestion.description}
                      </p>
                      <div className="bg-muted p-4 rounded-lg flex gap-3 items-start border border-border/50">
                        <CheckCircle className="text-emerald-500 shrink-0 mt-0.5" size={18} />
                        <div>
                          <span className="text-sm font-medium block mb-1">Recommended Action:</span>
                          <span className="text-sm text-foreground/80">{suggestion.action}</span>
                        </div>
                      </div>
                    </div>
                    <div className="p-6 md:w-1/3 flex flex-col justify-center bg-card/30">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground mb-1">Potential Savings</p>
                        <p className="text-3xl font-bold text-emerald-500">{suggestion.potentialSavings}</p>
                        <p className="text-xs text-muted-foreground mt-2">Estimated directly from variance data</p>
                      </div>
                      <button className="mt-6 w-full py-2 bg-primary text-primary-foreground rounded-md font-medium text-sm hover:opacity-90 transition-opacity">
                        Apply Configuration
                      </button>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>

      {/* ===== FOOTER: THÔNG TIN LIÊN HỆ & BẢN QUYỀN ===== */}
      <footer className="bg-[#2a2a2a] text-gray-300 mt-12">
        <div className="container mx-auto px-6 max-w-6xl py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-12 mb-4">
            {/* Cột 1: Thông tin liên hệ */}
            <div className="space-y-8">
              <div className="flex items-center gap-4">
                <img src={ptitLogo} alt="PTIT Logo" className="w-[60px] h-[60px] object-contain grayscale opacity-60 brightness-0" />
                <div className="flex flex-col gap-0.5">
                  <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-widest">Posts and Telecommunications Institute of Technology</span>
                  <span className="text-lg font-bold text-gray-200">Research Institute of Posts and Telecommunications</span>
                </div>
              </div>

              <div className="space-y-5 text-[15px] leading-relaxed text-gray-300">
                <p>122 đường Hoàng Quốc Việt – phường Nghĩa Tân – quận Cầu Giấy – TP. Hà Nội</p>
                <p>Số 271/10, An Dương Vương – Phường 3 – Quận 5 – Thành phố Hồ Chí Minh.</p>
                <p className="font-bold text-gray-100 mt-2">Điện thoại : 024 375 40103</p>
              </div>
            </div>

            {/* Cột 2: Điều hướng bổ sung */}
            <div>
              <h5 className="text-white text-lg font-semibold mb-4">Quick Links</h5>
              <div className="flex flex-col space-y-2">
                <a href="https://ptit.edu.vn/" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors w-fit">Trang chủ PTIT</a>
                <a href="https://www.fit.ac.jp/" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors w-fit">Fukuoka Institute of Technology (FIT)</a>
                <a href="https://docs.google.com/document/d/1MKaHJVLQTptc894-qXeJ7jyeBk0QaMviyIXQs0hKBhg/edit?tab=t.0#heading=h.kx3gjpttft68" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors w-fit">Tài liệu dự án (Docs)</a>
              </div>
            </div>

            {/* Cột 3: Chính sách */}
            <div>
              <h5 className="text-white text-lg font-semibold mb-4">Legal</h5>
              <div className="flex flex-col space-y-2">
                <a href="https://www.fit.ac.jp/en/privacy" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors w-fit">Chính sách bảo mật (Privacy Policy)</a>
                <a href="https://www.fit.ac.jp/en/sitepolicy" target="_blank" rel="noopener noreferrer" className="text-sm hover:text-white transition-colors w-fit">Điều khoản sử dụng (Site Policy)</a>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#1f1f1f] py-6 flex justify-center items-center">
          <p className="text-[14px] text-gray-400 flex items-center gap-3">
            Copyright © {new Date().getFullYear()} Viện Khoa học Kỹ thuật Bưu Điện <span className="w-2.5 h-2.5 rounded-full bg-indigo-700 opacity-80"></span>
          </p>
        </div>
      </footer>
    </div>
  );
}
