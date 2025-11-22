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
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { 
    Briefcase, 
    Search,
    Loader2,
    Eye,
    Filter,
    Globe,
    Building2,
    Calendar,
    User
} from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { apiClient, Project } from "@/lib/api";
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

export default function AdminProjects() {
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState<string>("all");
    const [industryFilter, setIndustryFilter] = useState<string>("all");
    const [selectedProject, setSelectedProject] = useState<Project | null>(null);
    const [viewDialogOpen, setViewDialogOpen] = useState(false);

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

    const { data: projects = [], isLoading } = useQuery({
        queryKey: ["admin-projects"],
        queryFn: () => apiClient.getAllProjects(),
    });

    const { data: projectDetails, isLoading: isLoadingDetails } = useQuery({
        queryKey: ["admin-project", selectedProject?.id],
        queryFn: () => apiClient.getAdminProject(selectedProject!.id),
        enabled: !!selectedProject && viewDialogOpen,
    });

    const filteredProjects = projects.filter((p) => {
        const matchesSearch =
            p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            p.client_name.toLowerCase().includes(searchQuery.toLowerCase());
        const matchesStatus = statusFilter === "all" || p.status === statusFilter;
        const matchesIndustry = industryFilter === "all" || p.industry === industryFilter;
        return matchesSearch && matchesStatus && matchesIndustry;
    });

    const industries = Array.from(new Set(projects.map((p) => p.industry))).sort();
    const statuses = Array.from(new Set(projects.map((p) => p.status))).sort();

    const projectStats = {
        total: projects.length,
        active: projects.filter((p) => p.status === "Active").length,
        submitted: projects.filter((p) => p.status === "Submitted").length,
        completed: projects.filter((p) => p.status === "Completed").length,
    };

    return (
        <DashboardLayout>
            <div className="space-y-6 sm:space-y-8">
                {/* Header */}
                <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
                    <div className="relative z-10">
                        <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                            Project Management
                        </h1>
                        <p className="text-sm sm:text-base text-muted-foreground">View and manage all projects across users</p>
                    </div>
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
                </div>

                {/* Search Bar */}
                <div className="flex items-center justify-end gap-2">
                    <div className="relative w-full sm:w-auto">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search projects..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 w-full sm:w-64 bg-background/50"
                        />
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-3 sm:gap-4 grid-cols-2 md:grid-cols-4">
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Total Projects</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{projectStats.total}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-blue-500/10 to-blue-500/5 p-2 text-blue-600">
                                <Briefcase className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Active</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{projectStats.active}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-green-500/10 to-green-500/5 p-2 text-green-600">
                                <Building2 className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Submitted</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{projectStats.submitted}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-purple-500/10 to-purple-500/5 p-2 text-purple-600">
                                <Globe className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                    <Card className="group relative overflow-hidden p-4 border-border/40 bg-card/80 backdrop-blur-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
                        <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                        <div className="relative flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                                <p className="text-xs sm:text-sm text-muted-foreground mb-1">Completed</p>
                                <p className="text-xl sm:text-2xl font-bold text-foreground">{projectStats.completed}</p>
                            </div>
                            <div className="ml-2 rounded-lg bg-gradient-to-br from-orange-500/10 to-orange-500/5 p-2 text-orange-600">
                                <Briefcase className="h-5 w-5 sm:h-6 sm:w-6" />
                            </div>
                        </div>
                    </Card>
                </div>

                {/* Filters */}
                <Card className="p-4 border-border/40 bg-card/80 backdrop-blur-sm shadow-sm">
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <Filter className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm font-medium">Filters:</span>
                        </div>
                        <Select value={statusFilter} onValueChange={setStatusFilter}>
                            <SelectTrigger className="w-48">
                                <SelectValue placeholder="All Statuses" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="all">All Statuses</SelectItem>
                                {statuses.map((status) => (
                                    <SelectItem key={status} value={status}>
                                        {status}
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
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

                {/* Projects Table */}
                <Card className="border-border/40 bg-card/80 backdrop-blur-sm shadow-sm">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : filteredProjects.length === 0 ? (
                        <div className="text-center py-12">
                            <Briefcase className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">
                                {searchQuery || statusFilter !== "all" || industryFilter !== "all"
                                    ? "No projects match your filters"
                                    : "No projects found"}
                            </p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Project Name</TableHead>
                                    <TableHead>Client</TableHead>
                                    <TableHead>Industry</TableHead>
                                    <TableHead>Region</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Type</TableHead>
                                    <TableHead>Created</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredProjects.map((project) => (
                                    <TableRow key={project.id}>
                                        <TableCell className="font-medium">{project.name}</TableCell>
                                        <TableCell>{project.client_name}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{project.industry}</Badge>
                                        </TableCell>
                                        <TableCell>{project.region}</TableCell>
                                        <TableCell>
                                            <Badge
                                                variant={
                                                    project.status === "Active"
                                                        ? "default"
                                                        : project.status === "Completed"
                                                        ? "secondary"
                                                        : "outline"
                                                }
                                            >
                                                {project.status}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant="outline">{project.project_type}</Badge>
                                        </TableCell>
                                        <TableCell>
                                            {format(new Date(project.created_at), "MMM d, yyyy")}
                                        </TableCell>
                                        <TableCell>
                                            <Button
                                                size="sm"
                                                variant="outline"
                                                onClick={() => {
                                                    setSelectedProject(project);
                                                    setViewDialogOpen(true);
                                                }}
                                            >
                                                <Eye className="h-4 w-4 mr-1" />
                                                View Details
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </Card>

                {/* Admin Project View Dialog */}
                <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
                    <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>Project Details</DialogTitle>
                            <DialogDescription>
                                Admin view - Read-only project information
                            </DialogDescription>
                        </DialogHeader>

                        {isLoadingDetails ? (
                            <div className="flex items-center justify-center py-12">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </div>
                        ) : projectDetails ? (
                            <div className="space-y-6">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <p className="text-sm font-medium mb-1">Project Name</p>
                                        <p className="text-sm text-muted-foreground">{projectDetails.name}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Client Name</p>
                                        <p className="text-sm text-muted-foreground">{projectDetails.client_name}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Industry</p>
                                        <Badge variant="outline">{projectDetails.industry}</Badge>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Region</p>
                                        <p className="text-sm text-muted-foreground">{projectDetails.region}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Project Type</p>
                                        <Badge variant="outline">{projectDetails.project_type}</Badge>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Status</p>
                                        <Badge
                                            variant={
                                                projectDetails.status === "Active"
                                                    ? "default"
                                                    : projectDetails.status === "Completed"
                                                    ? "secondary"
                                                    : "outline"
                                            }
                                        >
                                            {projectDetails.status}
                                        </Badge>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Created</p>
                                        <p className="text-sm text-muted-foreground">
                                            {format(new Date(projectDetails.created_at), "PPpp")}
                                        </p>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium mb-1">Last Updated</p>
                                        <p className="text-sm text-muted-foreground">
                                            {format(new Date(projectDetails.updated_at), "PPpp")}
                                        </p>
                                    </div>
                                </div>
                                {projectDetails.description && (
                                    <div>
                                        <p className="text-sm font-medium mb-1">Description</p>
                                        <p className="text-sm text-muted-foreground bg-muted p-3 rounded-md">
                                            {projectDetails.description}
                                        </p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="text-center py-12">
                                <p className="text-muted-foreground">Failed to load project details</p>
                            </div>
                        )}

                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setViewDialogOpen(false);
                                    setSelectedProject(null);
                                }}
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

