import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAuth } from "@/contexts/AuthContext";
import { 
  Download, 
  FileText, 
  Plus, 
  Trash2, 
  Sparkles, 
  Save, 
  ArrowUp, 
  ArrowDown,
  GripVertical,
  Eye,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Send
} from "lucide-react";
import { useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { MarkdownText } from "@/components/ui/markdown-text";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ProposalSection {
  id: number;
  title: string;
  content: string;
  order?: number;
  required?: boolean;
}

interface Proposal {
  id: number;
  project_id: number;
  title: string;
  sections: ProposalSection[];
  template_type: string;
  status?: string;
  submitter_message?: string;
  admin_feedback?: string;
  submitted_at?: string;
  reviewed_at?: string;
  created_at?: string;
  updated_at?: string;
}

export default function ProposalBuilder() {
  const [searchParams] = useSearchParams();
  const projectId = parseInt(searchParams.get("project_id") || "0");
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [title, setTitle] = useState("Proposal");
  const [sections, setSections] = useState<ProposalSection[]>([]);
  const [templateType, setTemplateType] = useState<string>("full");
  const [isGenerating, setIsGenerating] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedSectionId, setSelectedSectionId] = useState<number | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [exportingFormat, setExportingFormat] = useState<string | null>(null);
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [submitMessage, setSubmitMessage] = useState("");
  const [selectedManagerId, setSelectedManagerId] = useState<number | undefined>(undefined);
  const { user } = useAuth();

  // Load project info
  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.getProject(projectId),
    enabled: !!projectId,
  });

  // Load existing proposal
  const { data: proposal, isLoading: isLoadingProposal, refetch: refetchProposal } = useQuery({
    queryKey: ["proposal", projectId],
    queryFn: async () => {
      // Try to find existing proposal for this project
      // First check if there's a proposal_id in URL
      const proposalIdParam = searchParams.get("proposal_id");
      if (proposalIdParam) {
        return await apiClient.getProposal(parseInt(proposalIdParam));
      }
      // Otherwise, try to find by project
      return await apiClient.getProposalByProject(projectId);
    },
    enabled: !!projectId,
    retry: false,
  });

  // Load insights/workflow results for AI generation
  const { data: insights } = useQuery({
    queryKey: ["insights", projectId],
    queryFn: () => apiClient.getInsights(projectId),
    enabled: !!projectId,
    retry: false,
  });

  // Initialize sections from proposal
  useEffect(() => {
    if (proposal) {
      setTitle(proposal.title || "Proposal");
      setSections(proposal.sections || []);
      setTemplateType(proposal.template_type || "full");
      setLastSaved(new Date(proposal.updated_at || proposal.created_at || Date.now()));
    }
  }, [proposal]);

  // Get selected case study IDs from URL params (passed from Insights page)
  const selectedCaseStudyIdsParam = searchParams.get("selected_case_study_ids");
  const selectedCaseStudyIds = selectedCaseStudyIdsParam 
    ? selectedCaseStudyIdsParam.split(",").map(id => parseInt(id)).filter(id => !isNaN(id))
    : undefined;

  // Generate proposal mutation
  const generateMutation = useMutation({
    mutationFn: async ({ templateType, useInsights }: { templateType: string; useInsights: boolean }) => {
      return await apiClient.generateProposal(projectId, templateType, useInsights, selectedCaseStudyIds);
    },
    onSuccess: (data) => {
      setSections(data.sections || []);
      setTitle(data.title || "Proposal");
      setTemplateType(data.template_type || templateType);
      queryClient.invalidateQueries({ queryKey: ["proposal", projectId] });
      toast.success("Proposal generated successfully with AI-powered content!");
      setIsGenerating(false);
      // Refetch proposal to get the latest data
      refetchProposal();
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to generate proposal");
      setIsGenerating(false);
    },
  });

  // Save draft mutation
  const saveDraftMutation = useMutation({
    mutationFn: async (sectionsToSave: ProposalSection[]) => {
      if (!proposal?.id) {
        // Create new proposal
        return await apiClient.saveProposal({
          project_id: projectId,
          title,
          sections: sectionsToSave,
          template_type: templateType,
        });
      } else {
        // Update existing proposal
        return await apiClient.saveProposalDraft(proposal.id, sectionsToSave, title);
      }
    },
    onSuccess: (data) => {
      setLastSaved(new Date());
      queryClient.invalidateQueries({ queryKey: ["proposal", projectId] });
      setIsSaving(false);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to save proposal");
      setIsSaving(false);
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async (format: 'pdf' | 'docx' | 'pptx') => {
      if (!proposal?.id) {
        throw new Error("Please save the proposal before exporting");
      }
      setExportingFormat(format);
      const blob = await apiClient.exportProposal(proposal.id, format);
      return { blob, format };
    },
    onSuccess: ({ blob, format }) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${title.replace(/\s+/g, '_')}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success(`Exported as ${format.toUpperCase()}`);
      setExportingFormat(null);
    },
    onError: (error: any) => {
      toast.error(error.message || "Export failed");
      setExportingFormat(null);
    },
  });

  // Manual save function (autosave disabled)
  const autosave = useCallback(() => {
    if (sections.length === 0) return;
    
    setIsSaving(true);
    saveDraftMutation.mutate(sections);
  }, [sections, title, saveDraftMutation]);

  // Manual save
  const handleSave = () => {
    if (sections.length === 0) {
      toast.error("Please add at least one section");
      return;
    }
    autosave();
  };

  // Generate proposal from AI
  const handleGenerate = async (useInsights: boolean = true) => {
    if (!projectId) {
      toast.error("Project ID is required");
      return;
    }

    setIsGenerating(true);
    generateMutation.mutate({ templateType, useInsights });
  };

  // Add new section
  const handleAddSection = () => {
    const newSection: ProposalSection = {
      id: Date.now(),
      title: "New Section",
      content: "",
      order: sections.length,
    };
    setSections([...sections, newSection]);
    setSelectedSectionId(newSection.id);
  };

  // Delete section
  const handleDeleteSection = (sectionId: number) => {
    if (sections.find(s => s.id === sectionId)?.required) {
      toast.error("Cannot delete required section");
      return;
    }
    setSections(sections.filter(s => s.id !== sectionId));
    if (selectedSectionId === sectionId) {
      setSelectedSectionId(null);
    }
  };

  // Update section
  const handleUpdateSection = (sectionId: number, field: 'title' | 'content', value: string) => {
    setSections(sections.map(s => 
      s.id === sectionId ? { ...s, [field]: value } : s
    ));
  };

  // Reorder sections
  const handleMoveSection = (sectionId: number, direction: 'up' | 'down') => {
    const index = sections.findIndex(s => s.id === sectionId);
    if (index === -1) return;

    const newIndex = direction === 'up' ? index - 1 : index + 1;
    if (newIndex < 0 || newIndex >= sections.length) return;

    const newSections = [...sections];
    [newSections[index], newSections[newIndex]] = [newSections[newIndex], newSections[index]];
    setSections(newSections);
  };

  // Load managers for dropdown (available to all users)
  const { data: managers = [], isLoading: isLoadingManagers, error: managersError } = useQuery({
    queryKey: ["managers"],
    queryFn: () => apiClient.getManagers(),
    enabled: !!user, // Load for all authenticated users
    retry: 1,
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Submit proposal mutation
  const submitMutation = useMutation({
    mutationFn: async (message?: string, managerId?: number) => {
      if (!proposal?.id) {
        throw new Error("Please save the proposal first");
      }
      return await apiClient.submitProposal(proposal.id, message, managerId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["proposal", projectId] });
      toast.success("Proposal submitted for approval!");
      setSubmitDialogOpen(false);
      setSubmitMessage("");
      setSelectedManagerId(undefined);
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to submit proposal");
    },
  });

  // Regenerate section mutation
  const regenerateSectionMutation = useMutation({
    mutationFn: async ({ sectionId, sectionTitle }: { sectionId: number; sectionTitle: string }) => {
      if (!proposal?.id) {
        throw new Error("Please save the proposal first");
      }
      return await apiClient.regenerateSection(proposal.id, sectionId, sectionTitle);
    },
    onSuccess: (data) => {
      // Update the section content
      handleUpdateSection(data.section_id, 'content', data.content);
      queryClient.invalidateQueries({ queryKey: ["proposal", projectId] });
      toast.success("Section regenerated with AI!");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to regenerate section");
    },
  });

  // Regenerate section content with AI
  const handleRegenerateSection = async (sectionId: number) => {
    const section = sections.find(s => s.id === sectionId);
    if (!section) return;

    if (!proposal?.id) {
      toast.error("Please save the proposal first before regenerating sections");
      return;
    }

    if (!insights) {
      toast.error("No insights available. Please run the workflow first.");
      return;
    }

    regenerateSectionMutation.mutate({
      sectionId: section.id,
      sectionTitle: section.title
    });
  };

  // Get status badge
  const getStatusBadge = (status?: string) => {
    if (!status || status === "draft") return null;
    const variants: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      pending_approval: { variant: "secondary", label: "Pending Approval" },
      approved: { variant: "default", label: "Approved" },
      rejected: { variant: "destructive", label: "Rejected" },
      on_hold: { variant: "outline", label: "On Hold" },
    };
    const config = variants[status] || { variant: "outline" as const, label: status };
    return <Badge variant={config.variant}>{config.label}</Badge>;
  };

  if (!projectId) {
    return (
      <DashboardLayout>
        <Card className="p-6">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No Project Selected</h2>
            <p className="text-muted-foreground mb-4">
              Please select a project to build a proposal
            </p>
            <Button onClick={() => navigate("/dashboard")}>
              Go to Dashboard
            </Button>
          </div>
        </Card>
      </DashboardLayout>
    );
  }

  if (isLoadingProposal) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center min-h-[400px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 sm:space-y-8">
        {/* Header */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-6 sm:p-8 border border-border/40">
          <div className="relative z-10 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-2">
                <h1 className="font-heading text-2xl sm:text-3xl lg:text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                  Proposal Builder
                </h1>
                {project && (
                  <Badge variant="outline" className="text-xs sm:text-sm px-2 sm:px-3 py-1">
                    {project.client_name}
                  </Badge>
                )}
                {proposal?.status && getStatusBadge(proposal.status)}
              </div>
              <p className="text-sm sm:text-base lg:text-lg text-muted-foreground">
                {proposal ? "Edit your proposal" : "Create a winning proposal with AI-powered content"}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              {lastSaved && (
                <div className="flex items-center gap-2 text-xs sm:text-sm text-muted-foreground bg-background/50 px-2 sm:px-3 py-1.5 sm:py-2 rounded-lg border border-border/40">
                  <CheckCircle2 className="h-3 w-3 sm:h-4 sm:w-4 text-green-600" />
                  <span className="hidden sm:inline">Saved </span>
                  {lastSaved.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              )}
              {proposal && insights && (
                <Button 
                  variant="outline" 
                  size="sm"
                  className="text-xs sm:text-sm"
                  onClick={() => handleGenerate(true)}
                  disabled={isGenerating}
                >
                  {isGenerating ? (
                    <Loader2 className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                  )}
                  <span className="hidden sm:inline">Regenerate All</span>
                  <span className="sm:hidden">Regenerate</span>
                </Button>
              )}
              <Button 
                variant="outline" 
                size="sm"
                className="text-xs sm:text-sm"
                onClick={handleSave}
                disabled={isSaving || sections.length === 0}
              >
                {isSaving ? (
                  <Loader2 className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4 animate-spin" />
                ) : (
                  <Save className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                )}
                Save
              </Button>
              <Button 
                onClick={() => setPreviewMode(!previewMode)}
                variant={previewMode ? "default" : "outline"}
                size="sm"
                className="text-xs sm:text-sm"
              >
                <Eye className="mr-1 sm:mr-2 h-3 w-3 sm:h-4 sm:w-4" />
                {previewMode ? "Edit" : "Preview"}
              </Button>
              <Select value={templateType} onValueChange={setTemplateType}>
                <SelectTrigger className="w-full sm:w-[180px] text-xs sm:text-sm h-8 sm:h-10">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="full">Full Proposal</SelectItem>
                  <SelectItem value="executive">Executive Summary</SelectItem>
                  <SelectItem value="exclusive">Exclusive</SelectItem>
                  <SelectItem value="short-pitch">Short Pitch</SelectItem>
                  <SelectItem value="executive-summary">Executive Summary (Detailed)</SelectItem>
                  <SelectItem value="one-page">One-Page</SelectItem>
                  <SelectItem value="technical-appendix">Technical Appendix</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
        </div>

        {/* Generate/Regenerate Proposal Card - Show when no sections or when user wants to regenerate */}
        {sections.length === 0 && (
          <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-heading text-lg font-semibold mb-2">
                  {proposal ? "Regenerate Proposal" : "Generate AI-Powered Proposal"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {insights 
                    ? proposal
                      ? "Regenerate the entire proposal with fresh AI-generated content based on your insights"
                      : "Generate a complete proposal with AI-generated content based on your RFP analysis insights"
                    : "Run the workflow first to generate insights, or create a proposal from scratch"}
                </p>
                {insights && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Badge variant="outline" className="text-xs">
                      {insights.challenges?.length || 0} Challenges
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {insights.value_propositions?.length || 0} Value Props
                    </Badge>
                    {insights.matching_case_studies && (
                      <Badge variant="outline" className="text-xs">
                        {insights.matching_case_studies.length} Case Studies
                      </Badge>
                    )}
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                {insights && (
                  <Button
                    onClick={() => handleGenerate(true)}
                    disabled={isGenerating}
                    className="bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        {proposal ? "Regenerating..." : "Generating..."}
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        {proposal ? "Regenerate Best Proposal" : "Generate Best Proposal"}
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </Card>
        )}

        <div className="grid gap-6 lg:grid-cols-3">
          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title Input */}
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <Label htmlFor="proposal-title" className="mb-2 block font-semibold">
                Proposal Title
              </Label>
              <Input
                id="proposal-title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="text-lg font-semibold"
                placeholder="Enter proposal title..."
              />
            </Card>

            {/* Sections */}
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-6 flex items-center justify-between">
                <h2 className="font-heading text-xl font-semibold">Proposal Sections</h2>
                <Button size="sm" variant="outline" onClick={handleAddSection}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Section
                </Button>
              </div>

              {sections.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="mx-auto h-12 w-12 mb-4 opacity-50" />
                  <p>No sections yet. Add a section or generate from template.</p>
                </div>
              ) : previewMode ? (
                /* Modern Proposal Preview */
                <div className="bg-white rounded-lg shadow-2xl p-12 border border-gray-200 max-w-4xl mx-auto">
                  {/* Header Section */}
                  <div className="mb-8">
                    <div className="flex justify-between items-start pb-6 border-b-2 border-blue-800">
                      <div>
                        <h1 className="text-2xl font-bold text-gray-900">NovaIntel AI</h1>
                        <p className="text-gray-600 text-sm">AI-Powered Proposal Platform</p>
                      </div>
                      <div className="text-right">
                        <h2 className="text-3xl font-bold text-blue-800">Request for Proposal</h2>
                        <p className="text-base text-gray-700 mt-1">Project: {title}</p>
                      </div>
                    </div>
                  </div>

                  {/* RFP Details */}
                  <div className="grid grid-cols-2 gap-x-6 gap-y-3 mb-8">
                    <div className="flex">
                      <strong className="w-32 text-gray-700 text-sm">Issue Date:</strong>
                      <span className="text-gray-800 text-sm">{new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</span>
                    </div>
                    <div className="flex">
                      <strong className="w-32 text-gray-700 text-sm">Client:</strong>
                      <span className="text-gray-800 text-sm">{project?.client_name || '[Client Name]'}</span>
                    </div>
                    <div className="flex">
                      <strong className="w-32 text-gray-700 text-sm">Project:</strong>
                      <span className="text-gray-800 text-sm">{project?.name || title}</span>
                    </div>
                    <div className="flex">
                      <strong className="w-32 text-gray-700 text-sm">Document ID:</strong>
                      <span className="text-gray-800 text-sm">RFP-{new Date().getFullYear()}-{Math.random().toString(36).substr(2, 6).toUpperCase()}</span>
                    </div>
                  </div>

                  {/* Confidentiality Notice */}
                  <div className="p-4 border-2 border-red-300 bg-red-50 rounded-lg mb-8">
                    <h3 className="text-base font-bold text-red-800">Confidentiality Notice</h3>
                    <p className="text-sm text-red-700 mt-1">
                      This document contains confidential and proprietary information. 
                      The contents may not be disclosed to any third party without express written consent. 
                      All recipients are required to return or destroy this document upon request.
                    </p>
                  </div>

                  {/* Sections */}
                  {sections.map((section, index) => (
                    <div key={section.id} className="mb-8">
                      <h2 className="text-2xl font-bold text-blue-800 pb-2 mb-4">
                        {index + 1}.0 {section.title}
                      </h2>
                      <div className="text-gray-700 leading-relaxed space-y-3">
                        {section.content ? (
                          section.content.split('\n').map((line, i) => {
                            const trimmedLine = line.trim();
                            if (!trimmedLine) return <div key={i} className="h-3"></div>;
                            
                            // Handle bullet points
                            if (trimmedLine.startsWith('•') || trimmedLine.startsWith('-')) {
                              return (
                                <div key={i} className="flex gap-2">
                                  <span className="text-blue-600">•</span>
                                  <span>{trimmedLine.substring(1).trim()}</span>
                                </div>
                              );
                            }
                            
                            // Handle numbered lists
                            if (/^\d+\./.test(trimmedLine)) {
                              return <p key={i} className="ml-4">{trimmedLine}</p>;
                            }
                            
                            // Regular paragraph
                            return <p key={i} className="text-justify">{trimmedLine}</p>;
                          })
                        ) : (
                          <span className="text-gray-400 italic">No content</span>
                        )}
                      </div>
                    </div>
                  ))}

                  {/* Footer */}
                  <div className="mt-12 pt-6 border-t border-gray-200 text-center">
                    <p className="text-sm text-gray-500">
                      Generated by NovaIntel AI | {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}<br />
                      This is an AI-generated proposal based on your RFP analysis
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {sections.map((section, index) => (
                    <Card 
                      key={section.id} 
                      className={`border-border/40 bg-background/30 p-4 transition-all ${
                        selectedSectionId === section.id ? 'ring-2 ring-primary' : ''
                      }`}
                    >
                      <div className="mb-3 flex items-start gap-3">
                        <button
                          className="mt-2 text-muted-foreground hover:text-foreground"
                          title="Drag to reorder"
                        >
                          <GripVertical className="h-5 w-5" />
                        </button>
                        <div className="flex-1">
                          {previewMode ? (
                            <h3 className="font-semibold text-lg mb-2">{section.title}</h3>
                          ) : (
                            <Input
                              value={section.title}
                              onChange={(e) => handleUpdateSection(section.id, 'title', e.target.value)}
                              className="mb-2 border-none bg-transparent p-0 font-semibold text-lg focus-visible:ring-0"
                              placeholder="Section title..."
                              onClick={() => setSelectedSectionId(section.id)}
                            />
                          )}
                        </div>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Move up"
                            onClick={() => handleMoveSection(section.id, 'up')}
                            disabled={index === 0}
                          >
                            <ArrowUp className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Move down"
                            onClick={() => handleMoveSection(section.id, 'down')}
                            disabled={index === sections.length - 1}
                          >
                            <ArrowDown className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            title="Regenerate with AI"
                            onClick={() => handleRegenerateSection(section.id)}
                            disabled={regenerateSectionMutation.isPending || !proposal?.id || !insights}
                          >
                            {regenerateSectionMutation.isPending ? (
                              <Loader2 className="h-4 w-4 animate-spin text-primary" />
                            ) : (
                              <Sparkles className="h-4 w-4 text-primary" />
                            )}
                          </Button>
                          {!section.required && (
                            <Button
                              variant="ghost"
                              size="icon"
                              title="Delete section"
                              onClick={() => handleDeleteSection(section.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          )}
                        </div>
                      </div>
                      {previewMode ? (
                        <div className="prose prose-sm max-w-none text-foreground">
                          {section.content ? (
                            <MarkdownText 
                              content={section.content} 
                              className="text-foreground"
                            />
                          ) : (
                            <span className="text-muted-foreground italic">No content</span>
                          )}
                        </div>
                      ) : (
                        <Textarea
                          value={section.content}
                          onChange={(e) => handleUpdateSection(section.id, 'content', e.target.value)}
                          className="min-h-[150px] w-full resize-none rounded-lg border border-border/40 bg-background/50 p-3 text-sm focus:ring-2 focus:ring-primary"
                          placeholder="Enter section content..."
                          onClick={() => setSelectedSectionId(section.id)}
                        />
                      )}
                    </Card>
                  ))}
                </div>
              )}
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Template Info */}
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="mb-4 font-heading text-lg font-semibold">Template</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <span className="font-medium capitalize">{templateType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sections:</span>
                  <span className="font-medium">{sections.length}</span>
                </div>
                {proposal && (
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Created:</span>
                    <span className="font-medium">
                      {new Date(proposal.created_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
            </Card>

            {/* Export Options */}
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="mb-4 font-heading text-lg font-semibold">Export</h3>
              <div className="space-y-3">
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => exportMutation.mutate('pdf')}
                  disabled={!proposal?.id || (exportMutation.isPending && exportingFormat !== 'pdf')}
                >
                  {exportMutation.isPending && exportingFormat === 'pdf' ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="mr-2 h-4 w-4" />
                  )}
                  Export as PDF
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => exportMutation.mutate('docx')}
                  disabled={!proposal?.id || (exportMutation.isPending && exportingFormat !== 'docx')}
                >
                  {exportMutation.isPending && exportingFormat === 'docx' ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="mr-2 h-4 w-4" />
                  )}
                  Export as DOCX
                </Button>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => toast.info("PPTX export coming soon!")}
                  disabled={true}
                  title="Coming Soon"
                >
                  <Download className="mr-2 h-4 w-4 opacity-50" />
                  Export as PPTX (Coming Soon)
                </Button>
              </div>
            </Card>

            {/* Approval & Case Study Actions */}
            <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
              <h3 className="mb-4 font-heading text-lg font-semibold">Actions</h3>
              <div className="space-y-3">
                {proposal?.id && proposal?.status !== "pending_approval" && proposal?.status !== "approved" && user?.role !== "pre_sales_manager" && (
                  <Button 
                    onClick={() => setSubmitDialogOpen(true)}
                    className="w-full bg-gradient-to-r from-primary to-primary/80"
                  >
                    <Send className="mr-2 h-4 w-4" />
                    Submit for Approval
                  </Button>
                )}
                {proposal?.status === "approved" && (
                  <Button 
                    onClick={async () => {
                      try {
                        await apiClient.publishProjectAsCaseStudy(projectId);
                        toast.success("Publishing project as case study... You'll receive a notification when complete.");
                      } catch (error: any) {
                        toast.error(error.message || "Failed to publish case study");
                      }
                    }}
                    variant="outline"
                    className="w-full bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white border-0"
                  >
                    <FileText className="mr-2 h-4 w-4" />
                    Publish as Case Study
                  </Button>
                )}
                {proposal?.status === "pending_approval" && (
                  <div className="text-sm text-muted-foreground text-center py-2">
                    Proposal is pending approval
                  </div>
                )}
                {proposal?.status === "rejected" && (
                  <div className="text-sm text-muted-foreground text-center py-2">
                    Proposal was rejected
                  </div>
                )}
                {proposal?.status === "on_hold" && (
                  <div className="text-sm text-muted-foreground text-center py-2">
                    Proposal is on hold
                  </div>
                )}
                {!proposal?.id && (
                  <div className="text-sm text-muted-foreground text-center py-2">
                    Save the proposal to submit for approval
                  </div>
                )}
              </div>
            </Card>

            {/* Quick Actions */}
            {insights && (
              <Card className="border-border/40 bg-card/80 backdrop-blur-sm p-4 sm:p-6 shadow-sm hover:shadow-md transition-shadow">
                <h3 className="mb-4 font-heading text-lg font-semibold">AI Insights</h3>
                <div className="space-y-2 text-sm text-muted-foreground">
                  <p>✓ RFP Analysis Complete</p>
                  <p>✓ Challenges Identified</p>
                  <p>✓ Value Propositions Ready</p>
                  {insights.proposal_draft && (
                    <p>✓ Proposal Draft Available</p>
                  )}
                </div>
                <Button
                  variant="outline"
                  className="w-full mt-4"
                  onClick={() => navigate(`/insights?project_id=${projectId}`)}
                >
                  View Insights
                </Button>
              </Card>
            )}
          </div>
        </div>

        {/* Submit Dialog */}
        <Dialog open={submitDialogOpen} onOpenChange={setSubmitDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Submit Proposal for Approval</DialogTitle>
              <DialogDescription>
                Submit your proposal for review by a Pre-Sales Manager. You can include an optional message.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Select Manager for Approval</label>
                {isLoadingManagers ? (
                  <div className="flex items-center gap-2 p-3 border rounded-md">
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">Loading managers...</span>
                  </div>
                ) : managersError ? (
                  <div className="p-3 border rounded-md bg-destructive/10">
                    <p className="text-sm text-destructive">
                      Failed to load managers. The proposal will be sent to all managers by default.
                    </p>
                  </div>
                ) : managers.length === 0 ? (
                  <div className="p-3 border rounded-md bg-muted/50">
                    <p className="text-sm text-muted-foreground">
                      No managers available. The proposal will be sent to all managers by default.
                    </p>
                  </div>
                ) : (
                  <Select
                    value={selectedManagerId ? selectedManagerId.toString() : "all"}
                    onValueChange={(value) => {
                      if (value === "all") {
                        setSelectedManagerId(undefined);
                      } else {
                        setSelectedManagerId(parseInt(value));
                      }
                    }}
                  >
                    <SelectTrigger className="bg-background/50">
                      <SelectValue placeholder="Select a manager (optional - sends to all if not selected)">
                        {selectedManagerId
                          ? (() => {
                              const selected = managers.find((m) => m.id === selectedManagerId.toString());
                              return selected ? `${selected.full_name} • ${selected.email}` : "Select a manager";
                            })()
                          : "All Managers (Default)"}
                      </SelectValue>
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Managers (Default)</SelectItem>
                      {managers.map((manager) => (
                        <SelectItem key={manager.id} value={manager.id.toString()}>
                          <div className="flex items-center gap-2">
                            <span className="font-medium">{manager.full_name}</span>
                            <span className="text-muted-foreground">•</span>
                            <span className="text-sm text-muted-foreground">{manager.email}</span>
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  {managers.length > 0 
                    ? "Select a specific manager or leave as 'All Managers' to notify everyone"
                    : "If no managers are available, the proposal will be sent to all managers when they are added"}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Message (Optional)</label>
                <Textarea
                  placeholder="Add any notes or context for the reviewer..."
                  value={submitMessage}
                  onChange={(e) => setSubmitMessage(e.target.value)}
                  rows={4}
                />
              </div>
              {proposal?.admin_feedback && (
                <div className="p-3 bg-muted rounded-lg">
                  <p className="text-sm font-medium mb-1">Previous Feedback:</p>
                  <p className="text-sm text-muted-foreground">{proposal.admin_feedback}</p>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setSubmitDialogOpen(false);
                  setSubmitMessage("");
                  setSelectedManagerId(undefined);
                }}
                disabled={submitMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                onClick={() => submitMutation.mutate(submitMessage.trim() || undefined, selectedManagerId)}
                disabled={submitMutation.isPending || !proposal?.id}
              >
                {submitMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="mr-2 h-4 w-4" />
                    Submit
                  </>
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </DashboardLayout>
  );
}
