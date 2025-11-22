import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { FileText, Loader2, TrendingUp, Users, Briefcase, BarChart3, FolderKanban, ArrowRight, MessageCircle } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export default function AdminDashboard() {
    const { user } = useAuth();
    const navigate = useNavigate();

    // Check if user is a manager
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

    const { data: analytics, isLoading: isLoadingAnalytics } = useQuery({
        queryKey: ["admin-analytics"],
        queryFn: () => apiClient.getAdminAnalytics(),
    });

    return (
        <DashboardLayout>
            <div className="space-y-6 sm:space-y-8">
                {/* Header */}
                <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
                    <div className="relative z-10">
                        <h1 className="mb-2 font-heading text-3xl sm:text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                            Admin Dashboard
                        </h1>
                        <p className="text-muted-foreground text-base sm:text-lg">
                            Complete overview and management of all proposals and data
                        </p>
                    </div>
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
                </div>

                {/* Quick Access Cards */}
                <div className="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-3">
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/10 hover:-translate-y-1 hover:border-blue-300 cursor-pointer"
                        onClick={() => navigate("/admin/proposals")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-3 text-blue-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <FileText className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">Proposal Management</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">Review, approve, and manage proposals</p>
                        <Badge variant="outline" className="text-xs">View All</Badge>
                    </Card>
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-green-500/10 hover:-translate-y-1 hover:border-green-300 cursor-pointer"
                        onClick={() => navigate("/admin/users")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 p-3 text-green-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <Users className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">User Management</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">Manage users, roles, and permissions</p>
                        <Badge variant="outline" className="text-xs">{analytics?.users?.total || 0} Users</Badge>
                    </Card>
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/10 hover:-translate-y-1 hover:border-purple-300 cursor-pointer"
                        onClick={() => navigate("/admin/projects")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 p-3 text-purple-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <Briefcase className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">Project Management</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">View all projects across users</p>
                        <Badge variant="outline" className="text-xs">{analytics?.projects?.total || 0} Projects</Badge>
                    </Card>
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/10 hover:-translate-y-1 hover:border-orange-300 cursor-pointer"
                        onClick={() => navigate("/admin/analytics")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-orange-500/10 to-orange-500/5 p-3 text-orange-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <BarChart3 className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">Analytics & Reports</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">Comprehensive insights and metrics</p>
                        <Badge variant="outline" className="text-xs">{analytics?.activity?.approval_rate || 0}% Approval Rate</Badge>
                    </Card>
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/10 hover:-translate-y-1 hover:border-indigo-300 cursor-pointer"
                        onClick={() => navigate("/admin/case-studies")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 p-3 text-indigo-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <FolderKanban className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">Case Studies</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">Manage case study portfolio</p>
                        <Badge variant="outline" className="text-xs">View All</Badge>
                    </Card>
                    <Card 
                        className="group relative overflow-hidden p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10 hover:-translate-y-1 hover:border-cyan-300 cursor-pointer"
                        onClick={() => navigate("/admin/chat")}
                    >
                        <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between mb-4">
                            <div className="rounded-xl bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 p-3 text-cyan-600 transition-all duration-300 group-hover:scale-110 group-hover:rotate-3 group-hover:shadow-md">
                                <MessageCircle className="h-6 w-6 sm:h-8 sm:w-8" />
                            </div>
                            <ArrowRight className="h-5 w-5 text-muted-foreground transition-transform duration-300 group-hover:translate-x-1" />
                        </div>
                        <h3 className="font-semibold text-base sm:text-lg mb-1">Chat Management</h3>
                        <p className="text-xs sm:text-sm text-muted-foreground mb-4 leading-relaxed">Monitor all conversations</p>
                        <Badge variant="outline" className="text-xs">View All</Badge>
                    </Card>
                </div>

                {/* Analytics Overview */}
                <div>
                    <h2 className="font-heading text-xl sm:text-2xl font-semibold mb-4 sm:mb-6">Analytics Overview</h2>
                    {isLoadingAnalytics ? (
                        <Card className="p-6 sm:p-8">
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                            </div>
                        </Card>
                    ) : analytics && (
                        <div className="grid gap-4 sm:gap-6 md:grid-cols-2 lg:grid-cols-4">
                            <Card className="group relative overflow-hidden p-4 sm:p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                <div className="relative flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs sm:text-sm text-muted-foreground mb-1">Total Proposals</p>
                                        <p className="text-2xl sm:text-3xl font-bold text-foreground">{analytics.proposals?.total || 0}</p>
                                    </div>
                                    <div className="ml-4 rounded-xl bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-2 sm:p-3 text-blue-600">
                                        <FileText className="h-6 w-6 sm:h-8 sm:w-8" />
                                    </div>
                                </div>
                            </Card>
                            <Card className="group relative overflow-hidden p-4 sm:p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                <div className="relative flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs sm:text-sm text-muted-foreground mb-1">Total Projects</p>
                                        <p className="text-2xl sm:text-3xl font-bold text-foreground">{analytics.projects?.total || 0}</p>
                                    </div>
                                    <div className="ml-4 rounded-xl bg-gradient-to-br from-purple-500/10 to-purple-500/5 p-2 sm:p-3 text-purple-600">
                                        <Briefcase className="h-6 w-6 sm:h-8 sm:w-8" />
                                    </div>
                                </div>
                            </Card>
                            <Card className="group relative overflow-hidden p-4 sm:p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                                <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                <div className="relative flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs sm:text-sm text-muted-foreground mb-1">Total Users</p>
                                        <p className="text-2xl sm:text-3xl font-bold text-foreground">{analytics.users?.total || 0}</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {analytics.users?.analysts || 0} Analysts, {analytics.users?.managers || 0} Managers
                                        </p>
                                    </div>
                                    <div className="ml-4 rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5 p-2 sm:p-3 text-green-600">
                                        <Users className="h-6 w-6 sm:h-8 sm:w-8" />
                                    </div>
                                </div>
                            </Card>
                            <Card className="group relative overflow-hidden p-4 sm:p-6 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                                <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                                <div className="relative flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs sm:text-sm text-muted-foreground mb-1">Approval Rate</p>
                                        <p className="text-2xl sm:text-3xl font-bold text-foreground">{analytics.activity?.approval_rate || 0}%</p>
                                        <p className="text-xs text-muted-foreground mt-1">
                                            {analytics.activity?.recent_approvals || 0} approvals (7 days)
                                        </p>
                                    </div>
                                    <div className="ml-4 rounded-xl bg-gradient-to-br from-orange-500/10 to-orange-500/5 p-2 sm:p-3 text-orange-600">
                                        <TrendingUp className="h-6 w-6 sm:h-8 sm:w-8" />
                                    </div>
                                </div>
                            </Card>
                        </div>
                    )}
                </div>
            </div>
        </DashboardLayout>
    );
}
