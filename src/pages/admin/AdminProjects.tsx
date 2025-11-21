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
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">Project Management</h1>
                        <p className="text-muted-foreground">View and manage all projects across users</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search projects..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="pl-9 w-64"
                            />
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-4">
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Projects</p>
                                <p className="text-2xl font-bold">{projectStats.total}</p>
                            </div>
                            <Briefcase className="h-8 w-8 text-blue-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Active</p>
                                <p className="text-2xl font-bold">{projectStats.active}</p>
                            </div>
                            <Building2 className="h-8 w-8 text-green-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Submitted</p>
                                <p className="text-2xl font-bold">{projectStats.submitted}</p>
                            </div>
                            <Globe className="h-8 w-8 text-purple-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Completed</p>
                                <p className="text-2xl font-bold">{projectStats.completed}</p>
                            </div>
                            <Briefcase className="h-8 w-8 text-orange-500" />
                        </div>
                    </Card>
                </div>

                {/* Filters */}
                <Card className="p-4">
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
                <Card>
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

