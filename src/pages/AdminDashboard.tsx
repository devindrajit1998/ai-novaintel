import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CheckCircle, XCircle, Clock, FileText, Loader2, TrendingUp, Users, Briefcase, BarChart3 } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, Proposal } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { formatDistanceToNow } from "date-fns";
import { useAuth } from "@/contexts/AuthContext";

export default function AdminDashboard() {
    const queryClient = useQueryClient();
    const { user } = useAuth();
    const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);
    const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
    const [feedback, setFeedback] = useState("");
    const [activeTab, setActiveTab] = useState("pending_approval");

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

    const { data: proposals = [], isLoading } = useQuery({
        queryKey: ["admin-proposals", activeTab],
        queryFn: () => apiClient.getAdminDashboardProposals(activeTab === "all" ? undefined : activeTab),
    });

    const { data: analytics, isLoading: isLoadingAnalytics } = useQuery({
        queryKey: ["admin-analytics"],
        queryFn: () => apiClient.getAdminAnalytics(),
    });

    const reviewMutation = useMutation({
        mutationFn: ({ proposalId, action, feedback }: { proposalId: number; action: "approve" | "reject" | "hold"; feedback?: string }) =>
            apiClient.reviewProposal(proposalId, action, feedback),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-proposals"] });
            toast.success("Proposal reviewed successfully");
            setReviewDialogOpen(false);
            setSelectedProposal(null);
            setFeedback("");
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to review proposal");
        },
    });

    const handleReview = (action: "approve" | "reject" | "hold") => {
        if (!selectedProposal) return;
        reviewMutation.mutate({
            proposalId: selectedProposal.id,
            action,
            feedback: feedback.trim() || undefined,
        });
    };

    const getStatusBadge = (status: string) => {
        const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
            draft: { variant: "outline", label: "Draft" },
            pending_approval: { variant: "secondary", label: "Pending" },
            approved: { variant: "default", label: "Approved" },
            rejected: { variant: "destructive", label: "Rejected" },
            on_hold: { variant: "outline", label: "On Hold" },
        };
        const config = variants[status] || { variant: "outline" as const, label: status };
        return <Badge variant={config.variant}>{config.label}</Badge>;
    };

    const statusCounts = {
        all: proposals.length,
        pending_approval: proposals.filter((p) => p.status === "pending_approval").length,
        approved: proposals.filter((p) => p.status === "approved").length,
        rejected: proposals.filter((p) => p.status === "rejected").length,
        on_hold: proposals.filter((p) => p.status === "on_hold").length,
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div>
                    <h1 className="text-3xl font-bold">Admin Dashboard</h1>
                    <p className="text-muted-foreground">Complete overview and management of all proposals and data</p>
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

                {/* Proposal Status Cards */}
                <div className="grid gap-4 md:grid-cols-5">
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Pending</p>
                                <p className="text-2xl font-bold">{statusCounts.pending_approval}</p>
                            </div>
                            <Clock className="h-8 w-8 text-yellow-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Approved</p>
                                <p className="text-2xl font-bold">{statusCounts.approved}</p>
                            </div>
                            <CheckCircle className="h-8 w-8 text-green-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Rejected</p>
                                <p className="text-2xl font-bold">{statusCounts.rejected}</p>
                            </div>
                            <XCircle className="h-8 w-8 text-red-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">On Hold</p>
                                <p className="text-2xl font-bold">{statusCounts.on_hold}</p>
                            </div>
                            <FileText className="h-8 w-8 text-blue-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total</p>
                                <p className="text-2xl font-bold">{statusCounts.all}</p>
                            </div>
                            <BarChart3 className="h-8 w-8 text-indigo-500" />
                        </div>
                    </Card>
                </div>

                {/* Proposals Table */}
                <Card>
                    <Tabs value={activeTab} onValueChange={setActiveTab}>
                        <TabsList className="w-full justify-start rounded-none border-b">
                            <TabsTrigger value="pending_approval">Pending ({statusCounts.pending_approval})</TabsTrigger>
                            <TabsTrigger value="approved">Approved ({statusCounts.approved})</TabsTrigger>
                            <TabsTrigger value="rejected">Rejected ({statusCounts.rejected})</TabsTrigger>
                            <TabsTrigger value="on_hold">On Hold ({statusCounts.on_hold})</TabsTrigger>
                            <TabsTrigger value="all">All ({statusCounts.all})</TabsTrigger>
                        </TabsList>

                        <TabsContent value={activeTab} className="p-6">
                            {isLoading ? (
                                <div className="flex items-center justify-center py-12">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : proposals.length === 0 ? (
                                <div className="text-center py-12">
                                    <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                    <p className="text-muted-foreground">No proposals found</p>
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Title</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Submitted</TableHead>
                                            <TableHead>Message</TableHead>
                                            <TableHead>Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {proposals.map((proposal) => (
                                            <TableRow key={proposal.id}>
                                                <TableCell className="font-medium">{proposal.title}</TableCell>
                                                <TableCell>
                                                    <Badge variant="outline">#{proposal.project_id}</Badge>
                                                </TableCell>
                                                <TableCell>{getStatusBadge(proposal.status)}</TableCell>
                                                <TableCell>
                                                    {proposal.submitted_at
                                                        ? formatDistanceToNow(new Date(proposal.submitted_at), { addSuffix: true })
                                                        : "N/A"}
                                                </TableCell>
                                                <TableCell className="max-w-xs truncate">
                                                    {proposal.submitter_message || "No message"}
                                                </TableCell>
                                                <TableCell>
                                                    {proposal.status === "pending_approval" ? (
                                                        <Button
                                                            size="sm"
                                                            onClick={() => {
                                                                setSelectedProposal(proposal);
                                                                setReviewDialogOpen(true);
                                                            }}
                                                        >
                                                            Review
                                                        </Button>
                                                    ) : (
                                                        <span className="text-sm text-muted-foreground">
                                                            {proposal.status === "approved" && "✓ Approved"}
                                                            {proposal.status === "rejected" && "✗ Rejected"}
                                                            {proposal.status === "on_hold" && "⏸ On Hold"}
                                                        </span>
                                                    )}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            )}
                        </TabsContent>
                    </Tabs>
                </Card>

                {/* Review Dialog */}
                <Dialog open={reviewDialogOpen} onOpenChange={setReviewDialogOpen}>
                    <DialogContent className="max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>Review Proposal</DialogTitle>
                            <DialogDescription>
                                Review and provide feedback for: {selectedProposal?.title}
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                            <div>
                                <p className="text-sm font-medium mb-1">Submitter Message:</p>
                                <p className="text-sm text-muted-foreground">
                                    {selectedProposal?.submitter_message || "No message provided"}
                                </p>
                            </div>

                            <div>
                                <p className="text-sm font-medium mb-1">Your Feedback (Optional):</p>
                                <Textarea
                                    placeholder="Provide feedback or comments..."
                                    value={feedback}
                                    onChange={(e) => setFeedback(e.target.value)}
                                    rows={4}
                                />
                            </div>
                        </div>

                        <DialogFooter className="gap-2">
                            <Button
                                variant="outline"
                                onClick={() => setReviewDialogOpen(false)}
                                disabled={reviewMutation.isPending}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="destructive"
                                onClick={() => handleReview("reject")}
                                disabled={reviewMutation.isPending}
                            >
                                {reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Reject"}
                            </Button>
                            <Button
                                variant="secondary"
                                onClick={() => handleReview("hold")}
                                disabled={reviewMutation.isPending}
                            >
                                {reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Hold"}
                            </Button>
                            <Button
                                onClick={() => handleReview("approve")}
                                disabled={reviewMutation.isPending}
                            >
                                {reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Approve"}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}
