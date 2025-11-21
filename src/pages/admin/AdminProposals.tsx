import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
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
import { 
    CheckCircle, 
    XCircle, 
    Clock, 
    FileText, 
    Loader2, 
    Search,
    Eye,
    Download,
    Filter,
    Calendar
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, Proposal } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { formatDistanceToNow, format } from "date-fns";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";

export default function AdminProposals() {
    const queryClient = useQueryClient();
    const { user } = useAuth();
    const navigate = useNavigate();
    const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null);
    const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [feedback, setFeedback] = useState("");
    const [activeTab, setActiveTab] = useState("pending_approval");
    const [searchQuery, setSearchQuery] = useState("");
    const [pendingAction, setPendingAction] = useState<"approve" | "reject" | "hold" | null>(null);

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

    // Fetch all proposals for counting (always fetch all to get accurate counts)
    const { data: allProposals = [] } = useQuery({
        queryKey: ["admin-proposals-all"],
        queryFn: () => apiClient.getAdminDashboardProposals(),
    });

    // Fetch filtered proposals for display
    const { data: proposals = [], isLoading } = useQuery({
        queryKey: ["admin-proposals", activeTab],
        queryFn: () => apiClient.getAdminDashboardProposals(activeTab === "all" ? undefined : activeTab),
    });

    const reviewMutation = useMutation({
        mutationFn: ({ proposalId, action, feedback }: { proposalId: number; action: "approve" | "reject" | "hold"; feedback?: string }) =>
            apiClient.reviewProposal(proposalId, action, feedback),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-proposals"] });
            queryClient.invalidateQueries({ queryKey: ["admin-proposals-all"] });
            queryClient.invalidateQueries({ queryKey: ["admin-analytics"] });
            toast.success("Proposal reviewed successfully");
            setReviewDialogOpen(false);
            setSelectedProposal(null);
            setFeedback("");
            setPendingAction(null);
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to review proposal");
            setPendingAction(null);
        },
    });

    const handleReview = (action: "approve" | "reject" | "hold") => {
        if (!selectedProposal) return;
        setPendingAction(action);
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

    const filteredProposals = proposals.filter((p) =>
        p.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.submitter_message?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    // Calculate counts from all proposals, not filtered ones
    const statusCounts = {
        all: allProposals.length,
        pending_approval: allProposals.filter((p) => p.status === "pending_approval").length,
        approved: allProposals.filter((p) => p.status === "approved").length,
        rejected: allProposals.filter((p) => p.status === "rejected").length,
        on_hold: allProposals.filter((p) => p.status === "on_hold").length,
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Proposal Management</h1>
                        <p className="text-muted-foreground">Review, approve, and manage all proposals</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search proposals..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 w-64"
                            />
                        </div>
                    </div>
                </div>

                {/* Status Cards */}
                <div className="grid gap-4 md:grid-cols-5">
                    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveTab("pending_approval")}>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Pending</p>
                                <p className="text-2xl font-bold">{statusCounts.pending_approval}</p>
                            </div>
                            <Clock className="h-8 w-8 text-yellow-500" />
                        </div>
                    </Card>
                    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveTab("approved")}>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Approved</p>
                                <p className="text-2xl font-bold">{statusCounts.approved}</p>
                            </div>
                            <CheckCircle className="h-8 w-8 text-green-500" />
                        </div>
                    </Card>
                    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveTab("rejected")}>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Rejected</p>
                                <p className="text-2xl font-bold">{statusCounts.rejected}</p>
                            </div>
                            <XCircle className="h-8 w-8 text-red-500" />
                        </div>
                    </Card>
                    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveTab("on_hold")}>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">On Hold</p>
                                <p className="text-2xl font-bold">{statusCounts.on_hold}</p>
                            </div>
                            <FileText className="h-8 w-8 text-blue-500" />
                        </div>
                    </Card>
                    <Card className="p-4 hover:shadow-md transition-shadow cursor-pointer" onClick={() => setActiveTab("all")}>
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total</p>
                                <p className="text-2xl font-bold">{statusCounts.all}</p>
                            </div>
                            <FileText className="h-8 w-8 text-indigo-500" />
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
                            ) : filteredProposals.length === 0 ? (
                                <div className="text-center py-12">
                                    <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                                    <p className="text-muted-foreground">
                                        {searchQuery ? "No proposals match your search" : "No proposals found"}
                                    </p>
                                </div>
                            ) : (
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead>Title</TableHead>
                                            <TableHead>Project ID</TableHead>
                                            <TableHead>Status</TableHead>
                                            <TableHead>Submitted</TableHead>
                                            <TableHead>Message</TableHead>
                                            <TableHead>Actions</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {filteredProposals.map((proposal) => (
                                            <TableRow key={proposal.id}>
                                                <TableCell className="font-medium">{proposal.title}</TableCell>
                                                <TableCell>
                                                    <Badge variant="outline">#{proposal.project_id}</Badge>
                                                </TableCell>
                                                <TableCell>{getStatusBadge(proposal.status)}</TableCell>
                                                <TableCell>
                                                    {proposal.submitted_at ? (
                                                        <div className="flex flex-col">
                                                            <span className="text-sm">
                                                                {formatDistanceToNow(new Date(proposal.submitted_at), { addSuffix: true })}
                                                            </span>
                                                            <span className="text-xs text-muted-foreground">
                                                                {format(new Date(proposal.submitted_at), "MMM d, yyyy")}
                                                            </span>
                                                        </div>
                                                    ) : (
                                                        "N/A"
                                                    )}
                                                </TableCell>
                                                <TableCell className="max-w-xs truncate">
                                                    {proposal.submitter_message || "No message"}
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex items-center gap-2">
                                                        <Button
                                                            size="sm"
                                                            variant="outline"
                                                            onClick={() => {
                                                                setSelectedProposal(proposal);
                                                                setViewDialogOpen(true);
                                                            }}
                                                        >
                                                            <Eye className="h-4 w-4 mr-1" />
                                                            View
                                                        </Button>
                                                        {(proposal.status === "pending_approval" || proposal.status === "on_hold") && (
                                                            <Button
                                                                size="sm"
                                                                onClick={() => {
                                                                    setSelectedProposal(proposal);
                                                                    setReviewDialogOpen(true);
                                                                }}
                                                            >
                                                                Review
                                                            </Button>
                                                        )}
                                                    </div>
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
                <Dialog 
                    open={reviewDialogOpen} 
                    onOpenChange={(open) => {
                        setReviewDialogOpen(open);
                        if (!open) {
                            setPendingAction(null);
                        }
                    }}
                >
                    <DialogContent className="max-w-2xl">
                        <DialogHeader>
                            <DialogTitle>Review Proposal</DialogTitle>
                            <DialogDescription>
                                {selectedProposal?.status === "on_hold" 
                                    ? `Update proposal from On Hold status: ${selectedProposal?.title}`
                                    : `Review and provide feedback for: ${selectedProposal?.title}`}
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                            <div>
                                <p className="text-sm font-medium mb-1">Submitter Message:</p>
                                <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
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
                                {pendingAction === "reject" && reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                Reject
                            </Button>
                            {selectedProposal?.status !== "on_hold" && (
                                <Button
                                    variant="secondary"
                                    onClick={() => handleReview("hold")}
                                    disabled={reviewMutation.isPending}
                                >
                                    {pendingAction === "hold" && reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                    Hold
                                </Button>
                            )}
                            <Button
                                onClick={() => handleReview("approve")}
                                disabled={reviewMutation.isPending}
                            >
                                {pendingAction === "approve" && reviewMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                Approve
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>

                {/* View Dialog */}
                <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
                    <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>{selectedProposal?.title}</DialogTitle>
                            <DialogDescription>
                                Proposal Details
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm font-medium mb-1">Status:</p>
                                    <div>{selectedProposal && getStatusBadge(selectedProposal.status)}</div>
                                </div>
                                <div>
                                    <p className="text-sm font-medium mb-1">Project ID:</p>
                                    <Badge variant="outline">#{selectedProposal?.project_id}</Badge>
                                </div>
                            </div>
                            {selectedProposal?.submitted_at && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Submitted:</p>
                                    <p className="text-sm text-muted-foreground">
                                        {format(new Date(selectedProposal.submitted_at), "PPpp")}
                                    </p>
                                </div>
                            )}
                            {selectedProposal?.reviewed_at && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Reviewed:</p>
                                    <p className="text-sm text-muted-foreground">
                                        {format(new Date(selectedProposal.reviewed_at), "PPpp")}
                                    </p>
                                </div>
                            )}
                            {selectedProposal?.submitter_message && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Submitter Message:</p>
                                    <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                                        {selectedProposal.submitter_message}
                                    </p>
                                </div>
                            )}
                            {selectedProposal?.admin_feedback && (
                                <div>
                                    <p className="text-sm font-medium mb-1">Admin Feedback:</p>
                                    <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                                        {selectedProposal.admin_feedback}
                                    </p>
                                </div>
                            )}
                        </div>

                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => setViewDialogOpen(false)}
                            >
                                Close
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}

