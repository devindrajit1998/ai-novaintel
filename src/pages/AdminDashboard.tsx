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
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <p className="text-muted-foreground">Complete overview and management of all proposals and data</p>
                </div>

                {/* Quick Access Cards */}
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/proposals")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <FileText className="h-8 w-8 text-blue-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">Proposal Management</h3>
                        <p className="text-sm text-muted-foreground mb-4">Review, approve, and manage proposals</p>
                        <Badge variant="outline">View All</Badge>
                    </Card>
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/users")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Users className="h-8 w-8 text-green-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">User Management</h3>
                        <p className="text-sm text-muted-foreground mb-4">Manage users, roles, and permissions</p>
                        <Badge variant="outline">{analytics?.users?.total || 0} Users</Badge>
                    </Card>
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/projects")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <Briefcase className="h-8 w-8 text-purple-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">Project Management</h3>
                        <p className="text-sm text-muted-foreground mb-4">View all projects across users</p>
                        <Badge variant="outline">{analytics?.projects?.total || 0} Projects</Badge>
                    </Card>
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/analytics")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <BarChart3 className="h-8 w-8 text-orange-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">Analytics & Reports</h3>
                        <p className="text-sm text-muted-foreground mb-4">Comprehensive insights and metrics</p>
                        <Badge variant="outline">{analytics?.activity?.approval_rate || 0}% Approval Rate</Badge>
                    </Card>
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/case-studies")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <FolderKanban className="h-8 w-8 text-indigo-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">Case Studies</h3>
                        <p className="text-sm text-muted-foreground mb-4">Manage case study portfolio</p>
                        <Badge variant="outline">View All</Badge>
                    </Card>
                    <Card 
                        className="p-6 hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-primary"
                        onClick={() => navigate("/admin/chat")}
                    >
                        <div className="flex items-center justify-between mb-4">
                            <MessageCircle className="h-8 w-8 text-cyan-500" />
                            <ArrowRight className="h-5 w-5 text-muted-foreground" />
                        </div>
                        <h3 className="font-semibold text-lg mb-1">Chat Management</h3>
                        <p className="text-sm text-muted-foreground mb-4">Monitor all conversations</p>
                        <Badge variant="outline">View All</Badge>
                    </Card>
                </div>

                {/* Analytics Overview */}
                {isLoadingAnalytics ? (
                    <Card className="p-6">
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        </div>
                    </Card>
                ) : analytics && (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                        <Card className="p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Proposals</p>
                                    <p className="text-2xl font-bold">{analytics.proposals?.total || 0}</p>
                                </div>
                                <FileText className="h-8 w-8 text-blue-500" />
                            </div>
                        </Card>
                        <Card className="p-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-muted-foreground">Total Projects</p>
                                    <p className="text-2xl font-bold">{analytics.projects?.total || 0}</p>
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
                                    <p className="text-xs text-muted-foreground mt-1">
                                        {analytics.activity?.recent_approvals || 0} approvals (7 days)
                                    </p>
                                </div>
                                <TrendingUp className="h-8 w-8 text-orange-500" />
                            </div>
                        </Card>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
