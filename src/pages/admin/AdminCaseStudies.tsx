import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { 
    FolderKanban, 
    Search,
    Loader2,
    Eye,
    Filter,
    Building2
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { useState } from "react";
import { format } from "date-fns";
import { useAuth } from "@/contexts/AuthContext";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";

export default function AdminCaseStudies() {
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState("");
    const [industryFilter, setIndustryFilter] = useState<string>("all");

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

    const { data: caseStudies = [], isLoading } = useQuery({
        queryKey: ["admin-case-studies"],
        queryFn: () => apiClient.listCaseStudies(),
    });

    const filteredCaseStudies = caseStudies.filter((cs: any) => {
        const matchesSearch =
            cs.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            cs.description?.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesIndustry = industryFilter === "all" || cs.industry === industryFilter;
        return matchesSearch && matchesIndustry;
    });

    const industries = Array.from(new Set(caseStudies.map((cs: any) => cs.industry).filter(Boolean))).sort();

    const caseStudyStats = {
        total: caseStudies.length,
        indexed: caseStudies.filter((cs: any) => cs.indexed).length,
    };

    return (
        <DashboardLayout>
            <div className="space-y-6 sm:space-y-8">
                {/* Header */}
                <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
                    <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                        <div>
                            <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                                Case Study Management
                            </h1>
                            <p className="text-sm sm:text-base text-muted-foreground">View and manage all case studies</p>
                        </div>
                        <div className="relative w-full sm:w-auto">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search case studies..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 w-full sm:w-64 bg-background/50"
                            />
                        </div>
                    </div>
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-3 sm:gap-4 grid-cols-1 md:grid-cols-2">
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Total Case Studies</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{caseStudyStats.total}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-2 text-blue-600">
                                <FolderKanban className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Indexed in RAG</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{caseStudyStats.indexed}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-green-500/10 to-green-500/5 p-2 text-green-600">
                                <Building2 className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Filters */}
                {industries.length > 0 && (
                    <Card className="p-4 border-border/40 bg-card/80 backdrop-blur-sm shadow-sm">
                        <div className="flex items-center gap-4">
                            <div className="flex items-center gap-2">
                                <Filter className="h-4 w-4 text-muted-foreground" />
                                <span className="text-sm font-medium">Filter:</span>
                            </div>
                            <Select value={industryFilter} onValueChange={setIndustryFilter}>
                                <SelectTrigger className="w-48">
                                    <SelectValue placeholder="All Industries" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Industries</SelectItem>
                                    {industries.map((industry) => (
                                        <SelectItem key={industry} value={industry}>
                                            {industry}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </Card>
                )}

                {/* Case Studies Table */}
                <Card className="border-border/40 bg-card/80 backdrop-blur-sm shadow-sm">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : filteredCaseStudies.length === 0 ? (
                        <div className="text-center py-12">
                            <FolderKanban className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">
                                {searchQuery || industryFilter !== "all"
                                    ? "No case studies match your filters"
                                    : "No case studies found"}
                            </p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Title</TableHead>
                                    <TableHead>Industry</TableHead>
                                    <TableHead>Impact</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Created</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredCaseStudies.map((cs: any) => (
                                    <TableRow key={cs.id}>
                                        <TableCell className="font-medium">{cs.title}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{cs.industry || "N/A"}</Badge>
                                        </TableCell>
                                        <TableCell className="max-w-xs truncate">
                                            {cs.impact || "N/A"}
                                        </TableCell>
                                        <TableCell>
                                            {cs.indexed ? (
                                                <Badge variant="default">Indexed</Badge>
                                            ) : (
                                                <Badge variant="outline">Not Indexed</Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {cs.created_at
                                                ? format(new Date(cs.created_at), "MMM d, yyyy")
                                                : "N/A"}
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </Card>
            </div>
        </DashboardLayout>
    );
}

