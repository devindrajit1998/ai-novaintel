import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Upload, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  Clock,
  Sparkles
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { useState, useRef, useEffect } from "react";

export default function CaseStudies() {
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedCaseStudy, setSelectedCaseStudy] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [formData, setFormData] = useState({
    title: "",
    industry: "",
    impact: "",
    description: "",
  });
  const queryClient = useQueryClient();

  // Case Studies
  const { data: caseStudies = [], isLoading } = useQuery({
    queryKey: ["caseStudies"],
    queryFn: () => apiClient.listCaseStudies(),
  });

  // Case Study Documents
  const { data: caseStudyDocs = [], refetch: refetchDocs } = useQuery({
    queryKey: ["caseStudyDocuments"],
    queryFn: () => apiClient.listCaseStudyDocuments(),
    refetchInterval: (query) => {
      // Poll every 2 seconds if there are documents processing
      const docs = query.state.data as any[];
      if (docs && docs.some((d: any) => 
        d.processing_status === 'pending' || 
        d.processing_status === 'extracting' || 
        d.processing_status === 'analyzing' || 
        d.processing_status === 'indexing'
      )) {
        return 2000;
      }
      return false;
    },
  });

  // Upload mutation
  const uploadCaseStudyMutation = useMutation({
    mutationFn: (file: File) => apiClient.uploadCaseStudyDocument(file),
    onSuccess: () => {
      toast.success("Document uploaded! Processing started...");
      refetchDocs();
      setUploading(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to upload document");
      setUploading(false);
    },
  });

  // Delete document mutation
  const deleteDocMutation = useMutation({
    mutationFn: (id: number) => apiClient.deleteCaseStudyDocument(id),
    onSuccess: () => {
      toast.success("Document deleted successfully");
      refetchDocs();
      queryClient.invalidateQueries({ queryKey: ["caseStudies"] });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to delete document");
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { title: string; industry: string; impact: string; description?: string }) =>
      apiClient.createCaseStudy(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caseStudies"] });
      toast.success("Case study created successfully");
      setIsCreateOpen(false);
      setFormData({ title: "", industry: "", impact: "", description: "" });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create case study");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { title?: string; industry?: string; impact?: string; description?: string } }) =>
      apiClient.updateCaseStudy(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caseStudies"] });
      toast.success("Case study updated successfully");
      setIsEditOpen(false);
      setSelectedCaseStudy(null);
      setFormData({ title: "", industry: "", impact: "", description: "" });
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update case study");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (caseStudyId: number) => apiClient.deleteCaseStudy(caseStudyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["caseStudies"] });
      toast.success("Case study deleted successfully");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to delete case study");
    },
  });

  const { data: caseStudyDetail, isLoading: isLoadingDetail, error: caseStudyDetailError } = useQuery({
    queryKey: ["caseStudy", selectedCaseStudy?.id],
    queryFn: () => apiClient.getCaseStudy(selectedCaseStudy.id),
    enabled: isViewOpen && !!selectedCaseStudy?.id,
    retry: 1,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'pending':
      case 'extracting':
      case 'analyzing':
      case 'indexing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-600" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-600" />;
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Completed';
      case 'failed':
        return 'Failed';
      case 'pending':
        return 'Pending';
      case 'extracting':
        return 'Extracting Text';
      case 'analyzing':
        return 'Analyzing with AI';
      case 'indexing':
        return 'Indexing in RAG';
      default:
        return status;
    }
  };

  const handleCreate = () => {
    if (!formData.title || !formData.industry || !formData.impact) {
      toast.error("Please fill in all required fields");
      return;
    }
    createMutation.mutate({
      title: formData.title,
      industry: formData.industry,
      impact: formData.impact,
      description: formData.description || undefined,
    });
  };

  const handleEdit = () => {
    if (!selectedCaseStudy) return;
    if (!formData.title || !formData.industry || !formData.impact) {
      toast.error("Please fill in all required fields");
      return;
    }
    updateMutation.mutate({
      id: selectedCaseStudy.id,
      data: {
        title: formData.title,
        industry: formData.industry,
        impact: formData.impact,
        description: formData.description || undefined,
      },
    });
  };

  const handleOpenEdit = (study: any) => {
    setSelectedCaseStudy(study);
    setFormData({
      title: study.title || "",
      industry: study.industry || "",
      impact: study.impact || "",
      description: study.description || "",
    });
    setIsEditOpen(true);
  };

  const handleOpenView = (study: any) => {
    console.log('Opening view for case study:', study);
    setSelectedCaseStudy(study);
    setIsViewOpen(true);
  };

  const handleOpenCreate = () => {
    setFormData({ title: "", industry: "", impact: "", description: "" });
    setIsCreateOpen(true);
  };

  const filteredCaseStudies = caseStudies.filter((study: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      study.title?.toLowerCase().includes(query) ||
      study.industry?.toLowerCase().includes(query) ||
      study.impact?.toLowerCase().includes(query) ||
      study.description?.toLowerCase().includes(query)
    );
  });

  return (
    <DashboardLayout>
      <div className="space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
          <div className="relative z-10">
            <h1 className="mb-2 font-heading text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
              Case Study Management
            </h1>
            <p className="text-sm sm:text-base lg:text-lg text-muted-foreground">
              Upload documents to train your AI system and manage case studies
            </p>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
        </div>

        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList>
            <TabsTrigger value="upload">Upload & Train</TabsTrigger>
            <TabsTrigger value="documents">Documents</TabsTrigger>
            <TabsTrigger value="case-studies">Case Studies</TabsTrigger>
          </TabsList>

          {/* Upload & Train Tab */}
          <TabsContent value="upload" className="space-y-6">
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-6">
                <h2 className="mb-2 font-heading text-xl font-semibold">Upload Case Study Document</h2>
                <p className="text-sm text-muted-foreground">
                  Upload PDF or DOCX files containing case study information. The AI will automatically extract:
                  <ul className="mt-2 ml-4 list-disc space-y-1">
                    <li>Title</li>
                    <li>Industry Type</li>
                    <li>Project Description</li>
                    <li>Impact Metrics</li>
                    <li>Challenges, Solutions, and Results</li>
                  </ul>
                  The document will be indexed in our RAG system for intelligent similarity matching.
                </p>
              </div>
              
              <div
                className="flex items-center justify-center rounded-xl border-2 border-dashed border-border bg-background/30 p-12 transition-colors hover:border-primary/50 cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={(e) => {
                    if (e.target.files?.[0]) {
                      setUploading(true);
                      uploadCaseStudyMutation.mutate(e.target.files[0]);
                    }
                  }}
                  className="hidden"
                />
                <div className="text-center">
                  <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="mb-2 font-medium">
                    {uploading ? "Uploading..." : "Click to upload case study document"}
                  </p>
                  <p className="text-sm text-muted-foreground">Supports PDF, DOCX (Max 20MB)</p>
                </div>
              </div>
            </Card>

            {caseStudyDocs.length > 0 && (
              <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
                <h3 className="mb-4 font-semibold">Recent Uploads</h3>
                <div className="space-y-3">
                  {caseStudyDocs.slice(0, 5).map((doc: any) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between rounded-lg bg-background/40 p-4 border border-border/30"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{doc.filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {getStatusIcon(doc.processing_status)}
                            <span className="text-xs text-muted-foreground">
                              {getStatusLabel(doc.processing_status)}
                            </span>
                            {doc.case_study_id && (
                              <Badge variant="secondary" className="text-xs">
                                Case Study #{doc.case_study_id}
                              </Badge>
                            )}
                          </div>
                          {doc.error_message && (
                            <p className="text-xs text-red-600 mt-1">{doc.error_message}</p>
                          )}
                        </div>
                      </div>
                      {doc.processing_status === 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const study = caseStudies.find((cs: any) => cs.id === doc.case_study_id);
                            if (study) {
                              handleOpenView(study);
                            }
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents" className="space-y-6">
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-heading text-xl font-semibold">Uploaded Documents</h2>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search documents..."
                    className="bg-background/50 pl-9"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
              </div>

              {caseStudyDocs.length === 0 ? (
                <div className="py-12 text-center text-muted-foreground">
                  <FileText className="mx-auto mb-4 h-12 w-12 opacity-50" />
                  <p>No documents uploaded yet</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {caseStudyDocs.map((doc: any) => (
                    <div
                      key={doc.id}
                      className="flex items-center justify-between rounded-lg bg-background/40 p-4 border border-border/30"
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <FileText className="h-5 w-5 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{doc.filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            {getStatusIcon(doc.processing_status)}
                            <span className="text-xs text-muted-foreground">
                              {getStatusLabel(doc.processing_status)}
                            </span>
                            {doc.case_study_id && (
                              <Badge variant="secondary" className="text-xs">
                                Case Study #{doc.case_study_id}
                              </Badge>
                            )}
                          </div>
                          {doc.error_message && (
                            <p className="text-xs text-red-600 mt-1">{doc.error_message}</p>
                          )}
                          <p className="text-xs text-muted-foreground mt-1">
                            Uploaded {new Date(doc.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.processing_status === 'completed' && doc.case_study_id && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const study = caseStudies.find((cs: any) => cs.id === doc.case_study_id);
                              if (study) {
                                handleOpenView(study);
                              }
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            if (window.confirm("Are you sure you want to delete this document?")) {
                              deleteDocMutation.mutate(doc.id);
                            }
                          }}
                          disabled={deleteDocMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </TabsContent>

          {/* Case Studies Tab */}
          <TabsContent value="case-studies" className="space-y-6">
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="font-heading text-xl font-semibold">Case Studies</h2>
                <div className="flex items-center gap-3">
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Search case studies..."
                      className="bg-background/50 pl-9"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  {/* <Button className="bg-gradient-primary" onClick={handleOpenCreate}>
                    <Plus className="mr-2 h-4 w-4" />
                    Add Case Study
                  </Button> */}
                </div>
              </div>

              {isLoading ? (
                <div className="py-8 text-center text-muted-foreground">Loading case studies...</div>
              ) : filteredCaseStudies.length === 0 ? (
                <div className="py-8 text-center text-muted-foreground">
                  {searchQuery ? "No case studies match your search." : "No case studies available."}
                </div>
              ) : (
                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                  {filteredCaseStudies.map((study: any) => (
                    <Card
                      key={study.id}
                      className="group relative overflow-hidden border-border/40 bg-gradient-card backdrop-blur-sm transition-all hover:-translate-y-1 hover:shadow-glass"
                    >
                      <div className="p-6">
                        <div className="mb-4 flex items-start justify-between">
                          {study.industry && (
                            <Badge variant="secondary" className="bg-primary/10 text-primary">
                              {study.industry}
                            </Badge>
                          )}
                          <div className="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8"
                              onClick={() => handleOpenView(study)}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8"
                              onClick={() => handleOpenEdit(study)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              variant="ghost" 
                              size="icon" 
                              className="h-8 w-8"
                              onClick={() => {
                                if (window.confirm("Are you sure you want to delete this case study?")) {
                                  deleteMutation.mutate(study.id);
                                }
                              }}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </div>
                        </div>
                        <h3 className="mb-2 font-heading text-xl font-semibold">{study.title || study.name}</h3>
                        <p className="mb-4 text-sm text-muted-foreground line-clamp-3">{study.description || study.summary}</p>
                        {study.impact && (
                          <div className="rounded-lg bg-primary/5 p-3">
                            <p className="text-sm font-semibold text-primary">{study.impact}</p>
                          </div>
                        )}
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </TabsContent>
        </Tabs>

        {/* Create Case Study Dialog */}
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Create New Case Study</DialogTitle>
              <DialogDescription>
                Add a new success story to showcase your wins and impact.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="title">Title *</Label>
                <Input
                  id="title"
                  placeholder="e.g., Digital Transformation for Bank XYZ"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="industry">Industry *</Label>
                <Select
                  value={formData.industry}
                  onValueChange={(value) => setFormData({ ...formData, industry: value })}
                >
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BFSI">BFSI</SelectItem>
                    <SelectItem value="Retail">Retail</SelectItem>
                    <SelectItem value="Healthcare">Healthcare</SelectItem>
                    <SelectItem value="Technology">Technology</SelectItem>
                    <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                    <SelectItem value="Education">Education</SelectItem>
                    <SelectItem value="Government">Government</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="impact">Impact *</Label>
                <Input
                  id="impact"
                  placeholder="e.g., 40% cost reduction, 2x productivity increase"
                  value={formData.impact}
                  onChange={(e) => setFormData({ ...formData, impact: e.target.value })}
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  placeholder="Provide details about the project, challenges, solution, and results..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="bg-background/50 min-h-[120px]"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
                Cancel
              </Button>
              <Button
                className="bg-gradient-primary"
                onClick={handleCreate}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? "Creating..." : "Create Case Study"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Case Study Dialog */}
        <Dialog open={isEditOpen} onOpenChange={setIsEditOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Edit Case Study</DialogTitle>
              <DialogDescription>
                Update the case study information.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="edit-title">Title *</Label>
                <Input
                  id="edit-title"
                  placeholder="e.g., Digital Transformation for Bank XYZ"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-industry">Industry *</Label>
                <Select
                  value={formData.industry}
                  onValueChange={(value) => setFormData({ ...formData, industry: value })}
                >
                  <SelectTrigger className="bg-background/50">
                    <SelectValue placeholder="Select industry" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BFSI">BFSI</SelectItem>
                    <SelectItem value="Retail">Retail</SelectItem>
                    <SelectItem value="Healthcare">Healthcare</SelectItem>
                    <SelectItem value="Technology">Technology</SelectItem>
                    <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                    <SelectItem value="Education">Education</SelectItem>
                    <SelectItem value="Government">Government</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-impact">Impact *</Label>
                <Input
                  id="edit-impact"
                  placeholder="e.g., 40% cost reduction, 2x productivity increase"
                  value={formData.impact}
                  onChange={(e) => setFormData({ ...formData, impact: e.target.value })}
                  className="bg-background/50"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="edit-description">Description</Label>
                <Textarea
                  id="edit-description"
                  placeholder="Provide details about the project, challenges, solution, and results..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className="bg-background/50 min-h-[120px]"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsEditOpen(false)}>
                Cancel
              </Button>
              <Button
                className="bg-gradient-primary"
                onClick={handleEdit}
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? "Updating..." : "Update Case Study"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* View Case Study Dialog */}
        <Dialog open={isViewOpen} onOpenChange={setIsViewOpen}>
          <DialogContent className="sm:max-w-[700px] max-h-[90vh]">
            <DialogHeader>
              <DialogTitle>Case Study Details</DialogTitle>
              <DialogDescription>
                View complete information about this case study.
              </DialogDescription>
            </DialogHeader>
            {isLoadingDetail && !selectedCaseStudy ? (
              <div className="py-8 text-center text-muted-foreground">Loading...</div>
            ) : (
              <ScrollArea className="h-[60vh] pr-4">
                <div className="space-y-4 py-4">
                  {(caseStudyDetail || selectedCaseStudy) && (
                    <>
                      <div className="space-y-2">
                        <Label className="text-sm font-semibold">Title</Label>
                        <p className="text-sm">{caseStudyDetail?.title || selectedCaseStudy?.title || "N/A"}</p>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm font-semibold">Industry</Label>
                        <Badge variant="secondary" className="bg-primary/10 text-primary">
                          {caseStudyDetail?.industry || selectedCaseStudy?.industry || "N/A"}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm font-semibold">Impact</Label>
                        <div className="rounded-lg bg-primary/5 p-3">
                          <p className="text-sm font-semibold text-primary">
                            {caseStudyDetail?.impact || selectedCaseStudy?.impact || "N/A"}
                          </p>
                        </div>
                      </div>
                      {(caseStudyDetail?.description || selectedCaseStudy?.description) ? (
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold">Description</Label>
                          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {caseStudyDetail?.description || selectedCaseStudy?.description}
                          </p>
                        </div>
                      ) : null}
                      {(caseStudyDetail?.project_description || selectedCaseStudy?.project_description) ? (
                        <div className="space-y-2">
                          <Label className="text-sm font-semibold">Project Description</Label>
                          <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                            {caseStudyDetail?.project_description || selectedCaseStudy?.project_description}
                          </p>
                        </div>
                      ) : null}
                      <div className="space-y-2">
                        <Label className="text-sm font-semibold">Created</Label>
                        <p className="text-sm text-muted-foreground">
                          {(caseStudyDetail?.created_at || selectedCaseStudy?.created_at)
                            ? new Date(caseStudyDetail?.created_at || selectedCaseStudy?.created_at).toLocaleDateString()
                            : "N/A"}
                        </p>
                      </div>
                    </>
                  )}
                  {!caseStudyDetail && !selectedCaseStudy && (
                    <div className="py-8 text-center text-muted-foreground">
                      {caseStudyDetailError ? "Failed to load case study details" : "No case study data available"}
                    </div>
                  )}
                </div>
              </ScrollArea>
            )}
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsViewOpen(false)}>
                Close
              </Button>
              {selectedCaseStudy && (
                <Button
                  className="bg-gradient-primary"
                  onClick={() => {
                    setIsViewOpen(false);
                    handleOpenEdit(selectedCaseStudy);
                  }}
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Button>
              )}
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
