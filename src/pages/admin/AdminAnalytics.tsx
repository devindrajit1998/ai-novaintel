import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
    BarChart3, 
    TrendingUp, 
    FileText, 
    Users, 
    Briefcase,
    Loader2,
    CheckCircle,
    XCircle,
    Clock,
    Activity,
    Calendar
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart";
import { Area, AreaChart, Bar, BarChart, Cell, Line, LineChart, Pie, PieChart, XAxis, YAxis, CartesianGrid, Legend } from "recharts";

const COLORS = {
    pending: "#eab308",
    approved: "#22c55e",
    rejected: "#ef4444",
    on_hold: "#3b82f6",
    draft: "#94a3b8",
};

export default function AdminAnalytics() {
    const { user } = useAuth();

    if (user?.role !== "pre_sales_manager") {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <Card className="p-6">
                        <p className="text-muted-foreground">Access denied. Manager role required.</p>
                    </Card>
                </div>
            </DashboardLayout>
        );
    }

    const { data: analytics, isLoading } = useQuery({
        queryKey: ["admin-analytics"],
        queryFn: () => apiClient.getAdminAnalytics(),
    });

    if (isLoading) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
            </DashboardLayout>
        );
    }

    if (!analytics) {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <Card className="p-6">
                        <p className="text-muted-foreground">No analytics data available</p>
                    </Card>
                </div>
            </DashboardLayout>
        );
    }

    // Prepare chart data
    const statusChartData = [
        { name: "Approved", value: analytics.proposals?.approved || 0, fill: COLORS.approved },
        { name: "Pending", value: analytics.proposals?.pending || 0, fill: COLORS.pending },
        { name: "Rejected", value: analytics.proposals?.rejected || 0, fill: COLORS.rejected },
        { name: "On Hold", value: analytics.proposals?.on_hold || 0, fill: COLORS.on_hold },
        { name: "Draft", value: analytics.proposals?.by_status?.draft || 0, fill: COLORS.draft },
    ].filter(item => item.value > 0);

    const dailyData = analytics.time_series?.daily_submissions?.slice(-14) || []; // Last 14 days
    const weeklyData = analytics.time_series?.weekly || [];

    // Combine daily submissions and approvals for line chart
    const dailyTrendData = dailyData.map((submission, index) => ({
        date: submission.label,
        submissions: submission.value,
        approvals: analytics.time_series?.daily_approvals?.[analytics.time_series.daily_approvals.length - 14 + index]?.value || 0,
    }));

    const chartConfig = {
        submissions: {
            label: "Submissions",
            color: "hsl(var(--chart-1))",
        },
        approvals: {
            label: "Approvals",
            color: "hsl(var(--chart-2))",
        },
        rejections: {
            label: "Rejections",
            color: "hsl(var(--destructive))",
        },
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Analytics & Reports</h1>
                    <p className="text-muted-foreground">Comprehensive insights and metrics</p>
                </div>

                {/* Overview Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Proposals</p>
                                <p className="text-2xl font-bold">{analytics.proposals?.total || 0}</p>
                                <div className="flex items-center gap-2 mt-1">
                                    <TrendingUp className="h-3 w-3 text-green-500" />
                                    <span className="text-xs text-muted-foreground">
                                        {analytics.activity?.recent_submissions || 0} last 7 days
                                    </span>
                                </div>
                            </div>
                            <FileText className="h-8 w-8 text-blue-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Projects</p>
                                <p className="text-2xl font-bold">{analytics.projects?.total || 0}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {analytics.projects?.active || 0} Active
                                </p>
                            </div>
                            <Briefcase className="h-8 w-8 text-purple-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Users</p>
                                <p className="text-2xl font-bold">{analytics.users?.total || 0}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                    {analytics.users?.analysts || 0} Analysts, {analytics.users?.managers || 0} Managers
                                </p>
                            </div>
                            <Users className="h-8 w-8 text-green-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Approval Rate</p>
                                <p className="text-2xl font-bold">{analytics.activity?.approval_rate || 0}%</p>
                                <div className="flex items-center gap-2 mt-1">
                                    <CheckCircle className="h-3 w-3 text-green-500" />
                                    <span className="text-xs text-muted-foreground">
                                        {analytics.activity?.recent_approvals || 0} approvals (7 days)
                                    </span>
                                </div>
                            </div>
                            <TrendingUp className="h-8 w-8 text-orange-500" />
                        </div>
                    </Card>
                </div>

                {/* Charts Grid */}
                <div className="grid gap-6 md:grid-cols-2">
                    {/* Proposal Status Pie Chart */}
                    <Card className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-xl font-semibold">Proposal Status Distribution</h2>
                                <p className="text-sm text-muted-foreground">Total: {analytics.proposals?.total || 0}</p>
                            </div>
                            <Activity className="h-5 w-5 text-muted-foreground" />
                        </div>
                        {statusChartData.length > 0 ? (
                            <ChartContainer config={chartConfig} className="h-[300px]">
                                <PieChart>
                                    <Pie
                                        data={statusChartData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                        outerRadius={100}
                                        fill="#8884d8"
                                        dataKey="value"
                                    >
                                        {statusChartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.fill} />
                                        ))}
                                    </Pie>
                                    <ChartTooltip content={<ChartTooltipContent />} />
                                </PieChart>
                            </ChartContainer>
                        ) : (
                            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                                No data available
                            </div>
                        )}
                    </Card>

                    {/* Daily Trends Line Chart */}
                    <Card className="p-6">
                        <div className="flex items-center justify-between mb-6">
                            <div>
                                <h2 className="text-xl font-semibold">Daily Activity (14 Days)</h2>
                                <p className="text-sm text-muted-foreground">Submissions vs Approvals</p>
                            </div>
                            <Calendar className="h-5 w-5 text-muted-foreground" />
                        </div>
                        {dailyTrendData.length > 0 ? (
                            <ChartContainer config={chartConfig} className="h-[300px]">
                                <LineChart data={dailyTrendData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis 
                                        dataKey="date" 
                                        tick={{ fontSize: 12 }}
                                        angle={-45}
                                        textAnchor="end"
                                        height={60}
                                    />
                                    <YAxis tick={{ fontSize: 12 }} />
                                    <ChartTooltip content={<ChartTooltipContent />} />
                                    <Legend />
                                    <Line 
                                        type="monotone" 
                                        dataKey="submissions" 
                                        stroke="hsl(var(--chart-1))" 
                                        strokeWidth={2}
                                        dot={{ r: 4 }}
                                        name="Submissions"
                                    />
                                    <Line 
                                        type="monotone" 
                                        dataKey="approvals" 
                                        stroke="hsl(var(--chart-2))" 
                                        strokeWidth={2}
                                        dot={{ r: 4 }}
                                        name="Approvals"
                                    />
                                </LineChart>
                            </ChartContainer>
                        ) : (
                            <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                                No data available
                            </div>
                        )}
                    </Card>
                </div>

                {/* Weekly Trends Bar Chart */}
                <Card className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div>
                            <h2 className="text-xl font-semibold">Weekly Trends (Last 4 Weeks)</h2>
                            <p className="text-sm text-muted-foreground">Submissions, Approvals, and Rejections</p>
                        </div>
                        <BarChart3 className="h-5 w-5 text-muted-foreground" />
                    </div>
                    {weeklyData.length > 0 ? (
                        <ChartContainer config={chartConfig} className="h-[350px]">
                            <BarChart data={weeklyData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis 
                                    dataKey="label" 
                                    tick={{ fontSize: 12 }}
                                />
                                <YAxis tick={{ fontSize: 12 }} />
                                <ChartTooltip content={<ChartTooltipContent />} />
                                <Legend />
                                <Bar dataKey="submissions" fill="hsl(var(--chart-1))" name="Submissions" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="approvals" fill="hsl(var(--chart-2))" name="Approvals" radius={[4, 4, 0, 0]} />
                                <Bar dataKey="rejections" fill="hsl(var(--destructive))" name="Rejections" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ChartContainer>
                    ) : (
                        <div className="flex items-center justify-center h-[350px] text-muted-foreground">
                            No data available
                        </div>
                    )}
                </Card>

                {/* Detailed Status Breakdown */}
                <div className="grid gap-6 md:grid-cols-2">
                    <Card className="p-6">
                        <h2 className="text-xl font-semibold mb-4">Proposal Status Breakdown</h2>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.approved }}></div>
                                    <span className="font-medium">Approved</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{analytics.proposals?.approved || 0}</span>
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.pending }}></div>
                                    <span className="font-medium">Pending</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{analytics.proposals?.pending || 0}</span>
                                    <Clock className="h-4 w-4 text-yellow-500" />
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.rejected }}></div>
                                    <span className="font-medium">Rejected</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{analytics.proposals?.rejected || 0}</span>
                                    <XCircle className="h-4 w-4 text-red-500" />
                                </div>
                            </div>
                            <div className="flex items-center justify-between p-3 border rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.on_hold }}></div>
                                    <span className="font-medium">On Hold</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-2xl font-bold">{analytics.proposals?.on_hold || 0}</span>
                                    <Clock className="h-4 w-4 text-blue-500" />
                                </div>
                            </div>
                            {analytics.proposals?.by_status?.draft > 0 && (
                                <div className="flex items-center justify-between p-3 border rounded-lg">
                                    <div className="flex items-center gap-3">
                                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS.draft }}></div>
                                        <span className="font-medium">Draft</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-2xl font-bold">{analytics.proposals?.by_status?.draft || 0}</span>
                                        <FileText className="h-4 w-4 text-muted-foreground" />
                                    </div>
                                </div>
                            )}
                        </div>
                    </Card>

                    <Card className="p-6">
                        <h2 className="text-xl font-semibold mb-4">Activity Metrics</h2>
                        <div className="space-y-4">
                            <div className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-muted-foreground">Recent Submissions (7 days)</span>
                                    <Activity className="h-4 w-4 text-blue-500" />
                                </div>
                                <p className="text-3xl font-bold text-blue-600 dark:text-blue-400">
                                    {analytics.activity?.recent_submissions || 0}
                                </p>
                            </div>
                            <div className="p-4 border rounded-lg bg-gradient-to-r from-green-50 to-green-100 dark:from-green-950 dark:to-green-900">
                                <div className="flex items-center justify-between mb-2">
                                    <span className="text-sm font-medium text-muted-foreground">Recent Approvals (7 days)</span>
                                    <CheckCircle className="h-4 w-4 text-green-500" />
                                </div>
                                <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                                    {analytics.activity?.recent_approvals || 0}
                                </p>
                            </div>
                            <div className="p-4 border rounded-lg">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <p className="text-sm font-medium text-muted-foreground">Approval Rate</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Based on reviewed proposals
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-3xl font-bold">{analytics.activity?.approval_rate || 0}%</p>
                                        <TrendingUp className="h-4 w-4 text-green-500 ml-auto mt-1" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>
        </DashboardLayout>
    );
}
