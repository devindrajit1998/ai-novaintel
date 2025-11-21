import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { FileText, MessageSquare, Send, Sparkles, CheckCircle2, Loader2, Plus, Eye, Check } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useSearchParams, useNavigate } from "react-router-dom";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { MarkdownText } from "@/components/ui/markdown-text";
import { Switch } from "@/components/ui/switch";
import { DialogDescription, DialogFooter } from "@/components/ui/dialog";

export default function Insights() {
  const [searchParams] = useSearchParams();
  const projectId = parseInt(searchParams.get("project_id") || "0");
  const navigate = useNavigate();
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<Array<{ role: string; content: string }>>([]);
  const [isSending, setIsSending] = useState(false);
  
  // Get selected tasks from URL params
  const selectedTasks = {
    challenges: searchParams.get("challenges") === "true",
    questions: searchParams.get("questions") === "true",
    cases: searchParams.get("cases") === "true",
  };
  
  // Build dynamic analysis steps based on selected tasks
  // Value propositions depend on challenges, so show if challenges is selected
  const analysisSteps = [
    { id: "rfp_analyzer", label: "Analyzing RFP Document", workflowStep: "rfp_analyzer" },
    ...(selectedTasks.challenges ? [{ id: "challenges", label: "Extracting Business Challenges", workflowStep: "challenge_extractor" }] : []),
    ...(selectedTasks.challenges ? [{ id: "value_props", label: "Generating Value Propositions", workflowStep: "value_proposition" }] : []),
    ...(selectedTasks.questions ? [{ id: "questions", label: "Creating Discovery Questions", workflowStep: "discovery_question" }] : []),
    ...(selectedTasks.cases ? [{ id: "cases", label: "Matching Case Studies", workflowStep: "case_study_matcher" }] : []),
  ];

  const { data: insights, isLoading, error, refetch } = useQuery({
    queryKey: ["insights", projectId],
    queryFn: async () => {
      try {
        return await apiClient.getInsights(projectId);
      } catch (err: any) {
        // Silently handle 404s - they're expected when insights don't exist yet
        if (err instanceof Error && err.message.includes('404')) {
          return null;
        }
        throw err;
      }
    },
    enabled: !!projectId,
    retry: false,
    throwOnError: false, // Don't throw errors since 404 is expected
    refetchInterval: (query) => {
      // Poll every 3 seconds if insights don't exist yet
      const data = query.state.data;
      if (!data || !data.executive_summary) {
        return 3000; // Poll every 3 seconds
      }
      return false; // Stop polling once we have data
    },
  });

  // Track if we're waiting for analysis
  const isAnalyzing = !!projectId && (!insights || !insights.executive_summary);

  // Poll for workflow status to show dynamic progress
  const { data: workflowStatus } = useQuery({
    queryKey: ["workflow-status", projectId],
    queryFn: () => apiClient.getWorkflowStatus(projectId),
    enabled: !!projectId && isAnalyzing,
    refetchInterval: 2000, // Poll every 2 seconds while analyzing
    retry: false,
  });
  
  // Check for workflow errors
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  
  // If we've been loading for more than 5 minutes, show an error
  const [loadStartTime] = useState(Date.now());
  const loadDuration = Date.now() - loadStartTime;
  const isStuck = isAnalyzing && loadDuration > 5 * 60 * 1000; // 5 minutes

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || !projectId || isSending) return;

    // Check RAG status before sending message
    try {
      const ragStatus = await apiClient.getRagStatus(projectId);
      if (!ragStatus.ready) {
        toast.error("RAG index not ready. Please wait for insights to be generated.");
        return;
      }
    } catch (error: any) {
      console.warn("Could not check RAG status:", error);
      // Continue anyway as the chat endpoint will handle this
    }

    const userMessage = chatMessage.trim();
    setChatMessage("");
    setChatHistory(prev => [...prev, { role: "user", content: userMessage }]);
    setIsSending(true);

    try {
      const response = await apiClient.chatWithRFP(projectId, userMessage, chatHistory);
      
      // Check if there was an error in the response
      if (!response.success && response.error) {
        toast.error(response.error);
        setChatHistory(prev => prev.slice(0, -1));
        setIsSending(false);
        return;
      }
      
      // Backend returns 'answer' field
      const assistantMessage = response.answer || response.response || "Sorry, I couldn't process that request.";
      
      setChatHistory(prev => [...prev, { role: "assistant", content: assistantMessage }]);
    } catch (error: any) {
      console.error("Chat error:", error);
      toast.error(error.message || "Failed to send message");
      setChatHistory(prev => prev.slice(0, -1));
    } finally {
      setIsSending(false);
    }
  };

  // Add state for adding case study
  const [showAddCaseStudy, setShowAddCaseStudy] = useState(false);
  const [newCaseStudy, setNewCaseStudy] = useState({
    title: "",
    industry: "",
    impact: "",
    description: ""
  });
  const [selectedCaseStudyIds, setSelectedCaseStudyIds] = useState<Set<number>>(new Set());
  const [viewingCaseStudy, setViewingCaseStudy] = useState<any | null>(null);
  const [isViewDialogOpen, setIsViewDialogOpen] = useState(false);

  // Add mutation for creating case study
  const createCaseStudyMutation = useMutation({
    mutationFn: (data: any) => apiClient.createCaseStudy(data),
    onSuccess: () => {
      toast.success("Case study added successfully!");
      setShowAddCaseStudy(false);
      setNewCaseStudy({ title: "", industry: "", impact: "", description: "" });
      // Optionally refresh insights
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to add case study");
    }
  });

  if (!projectId) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center">
          <Card className="p-6">
            <p className="text-muted-foreground">No project selected. Please select a project from the dashboard.</p>
            <Button onClick={() => navigate("/dashboard")} className="mt-4">
              Go to Dashboard
            </Button>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // Show analyzing loader if insights are being generated
  if (isAnalyzing) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center p-6">
          <Card className="border-border/40 bg-gradient-card p-8 backdrop-blur-sm w-full max-w-2xl">
            <div className="flex flex-col items-center justify-center space-y-6">
              {/* Animated Sparkles Icon */}
              <div className="relative">
                <div className="absolute inset-0 rounded-full bg-primary/20 animate-ping" />
                <div className="relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-primary shadow-glass">
                  <Sparkles className="h-10 w-10 text-primary-foreground animate-pulse" />
                </div>
              </div>

              {/* Title */}
              <div className="text-center space-y-2">
                <h2 className="font-heading text-2xl font-bold">Analyzing Your RFP</h2>
                <p className="text-muted-foreground">
                  Our AI is extracting insights, identifying challenges, and generating recommendations...
                </p>
              </div>

              {/* Progress Steps */}
              <div className="w-full space-y-4">
                {analysisSteps.map((step, index) => {
                  // Determine step status from workflow status
                  let isActive = false;
                  let isComplete = false;
                  
                  if (workflowStatus) {
                    const progress = workflowStatus.progress || {};
                    const currentStep = workflowStatus.current_step;
                    const workflowStepId = step.workflowStep;
                    
                    // Check if step is complete
                    isComplete = progress[workflowStepId] === true;
                    
                    // Check if step is currently active
                    if (workflowStatus.status === "running") {
                      // Step is active if it matches the current_step from workflow
                      isActive = currentStep === workflowStepId;
                    } else if (workflowStatus.status === "completed") {
                      // All steps should be complete when workflow is done
                      isComplete = true;
                    }
                  } else {
                    // No workflow status yet, show first step as active
                    isActive = index === 0;
                  }
                  
                  return (
                    <AnalysisStep 
                      key={step.id}
                      label={step.label} 
                      isActive={isActive}
                      isComplete={isComplete}
                    />
                  );
                })}
              </div>

              {/* Loading Indicator */}
              <div className="flex flex-col items-center gap-2 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>This may take 2-3 minutes</span>
                </div>
                {isStuck && (
                  <div className="mt-4 w-full rounded-lg bg-yellow-500/10 border border-yellow-500/20 p-4 text-center space-y-3">
                    <p className="text-sm text-yellow-600">
                      Analysis is taking longer than expected. The workflow might not have started or encountered an error.
                    </p>
                    <div className="flex gap-2 justify-center">
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={async () => {
                          toast.info("Checking status...");
                          await refetch();
                        }}
                      >
                        Check Status
                      </Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={async () => {
                          try {
                            toast.info("Please check the browser console and backend logs for errors");
                            console.log("Project ID:", projectId);
                            console.log("Check backend console for workflow execution logs");
                          } catch (err) {
                            console.error("Error:", err);
                          }
                        }}
                      >
                        View Logs
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  if (!insights && !isAnalyzing) {
    return (
      <DashboardLayout>
        <div className="flex h-full items-center justify-center p-6">
          <Card className="border-border/40 bg-gradient-card p-8 backdrop-blur-sm max-w-md">
            <div className="text-center space-y-4">
              <div className="flex justify-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
                  <Sparkles className="h-8 w-8 text-muted-foreground" />
                </div>
              </div>
              <div>
                <h2 className="font-heading text-xl font-bold mb-2">No Insights Found</h2>
                <p className="text-muted-foreground text-sm mb-4">
                  Insights haven't been generated for this project yet. The workflow might not have started or may have failed.
                </p>
              </div>
              <div className="flex flex-col gap-2">
                <Button 
                  onClick={() => navigate("/new-project")} 
                  className="bg-gradient-primary"
                >
                  Create New Project
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => {
                    console.log("Project ID:", projectId);
                    console.log("Check backend console for workflow execution logs");
                    toast.info("Check the browser console and backend logs");
                  }}
                >
                  Check Logs
                </Button>
              </div>
            </div>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  const challenges = insights.challenges || [];
  const valueProps = insights.value_propositions || [];
  const discoveryQuestions = insights.discovery_questions || {};
  const matchingCaseStudies = insights.matching_case_studies || [];
  const rfpSummary = insights.executive_summary || "";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="mb-2 font-heading text-3xl font-bold">AI Insights</h1>
            <p className="text-muted-foreground">Project ID: {projectId}</p>
          </div>
          <div className="flex gap-3">
            <Button 
              variant="outline"
              onClick={async () => {
                try {
                  await apiClient.publishProjectAsCaseStudy(projectId);
                  toast.success("Publishing project as case study... You'll receive a notification when complete.");
                } catch (error: any) {
                  toast.error(error.message || "Failed to publish case study");
                }
              }}
            >
              <FileText className="mr-2 h-4 w-4" />
              Publish as Case Study
            </Button>
            <Button 
              className="bg-gradient-primary" 
              onClick={() => {
                const selectedIds = Array.from(selectedCaseStudyIds);
                const params = new URLSearchParams();
                params.set('project_id', projectId.toString());
                if (selectedIds.length > 0) {
                  params.set('selected_case_study_ids', selectedIds.join(','));
                }
                navigate(`/proposal?${params.toString()}`);
              }}
            >
              <FileText className="mr-2 h-4 w-4" />
              Generate Proposal
            </Button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <Tabs defaultValue="summary" className="w-full">
              <TabsList className="grid w-full grid-cols-4 bg-muted/50">
                <TabsTrigger value="summary">Summary</TabsTrigger>
                <TabsTrigger value="challenges">Challenges</TabsTrigger>
                <TabsTrigger value="questions">Questions</TabsTrigger>
                <TabsTrigger value="cases">Case Studies</TabsTrigger>
              </TabsList>

              <TabsContent value="summary" className="mt-6">
                <Card className="border-border/40 bg-gradient-card p-6 backdrop-blur-sm">
                  <div className="mb-6 flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                      <Sparkles className="h-5 w-5 text-primary" />
                    </div>
                    <h2 className="font-heading text-xl font-semibold">Executive Summary</h2>
                  </div>
                  <div className="space-y-4">
                    {rfpSummary ? (
                      <div className="rounded-lg bg-background/40 p-5 border border-border/30">
                        <MarkdownText 
                          content={typeof rfpSummary === 'string' ? rfpSummary : JSON.stringify(rfpSummary)} 
                          className="text-foreground/90"
                        />
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground italic">No summary available yet. Run analysis to generate insights.</p>
                    )}
                  </div>
                </Card>

                <Card className="mt-6 border-border/40 bg-gradient-card p-6 backdrop-blur-sm">
                  <h2 className="mb-6 font-heading text-xl font-semibold">Value Propositions</h2>
                  <div className="space-y-4">
                    {valueProps.length > 0 ? (
                      valueProps.map((prop: any, index: number) => {
                        const propText = typeof prop === 'string' ? prop : prop.text || JSON.stringify(prop);
                        return (
                          <div 
                            key={index} 
                            className="group flex items-start gap-4 rounded-lg bg-background/40 p-5 border border-border/30 transition-all hover:border-primary/30 hover:bg-background/50"
                          >
                            <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                              {index + 1}
                            </div>
                            <div className="flex-1">
                              <MarkdownText 
                                content={propText} 
                                className="text-sm text-foreground/90 leading-relaxed"
                              />
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-sm text-muted-foreground italic">No value propositions identified yet.</p>
                    )}
                  </div>
                </Card>
              </TabsContent>

              <TabsContent value="challenges" className="mt-6">
                <Card className="border-border/40 bg-gradient-card p-6 backdrop-blur-sm">
                  <h2 className="mb-6 font-heading text-xl font-semibold">Business Challenges Identified</h2>
                  <div className="space-y-4">
                    {challenges.length > 0 ? (
                      challenges.map((challenge: any, index: number) => {
                        // Handle different challenge formats
                        let challengeDescription = "";
                        let challengeType = "";
                        let challengeImpact = "";
                        let challengeCategory = "";
                        let solutionDirection = "";
                        let recommendation = null;
                        
                        if (typeof challenge === 'string') {
                          challengeDescription = challenge;
                        } else if (typeof challenge === 'object') {
                          challengeDescription = challenge.description || challenge.text || challenge.challenge || "";
                          challengeType = challenge.type || "";
                          challengeImpact = challenge.impact || "";
                          challengeCategory = challenge.category || "";
                          solutionDirection = challenge.solution_direction || challenge.recommendation || "";
                          recommendation = challenge.recommendation || null;
                        }
                        
                        return (
                          <div 
                            key={index} 
                            className="group flex gap-4 rounded-lg bg-background/40 p-5 border border-border/30 transition-all hover:border-primary/30 hover:bg-background/50"
                          >
                            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 font-semibold text-primary">
                              {index + 1}
                            </div>
                            <div className="flex-1 space-y-3">
                              {/* Challenge Description */}
                              {challengeDescription && (
                                <div className="text-foreground/90">
                                  <MarkdownText 
                                    content={challengeDescription} 
                                    className="text-sm font-medium leading-relaxed"
                                  />
                                </div>
                              )}
                              
                              {/* Challenge Metadata */}
                              {(challengeType || challengeImpact || challengeCategory) && (
                                <div className="flex flex-wrap gap-2">
                                  {challengeType && (
                                    <Badge variant="secondary" className="text-xs">
                                      Type: {challengeType}
                                    </Badge>
                                  )}
                                  {challengeImpact && (
                                    <Badge variant={challengeImpact === 'High' ? 'destructive' : challengeImpact === 'Medium' ? 'default' : 'secondary'} className="text-xs">
                                      Impact: {challengeImpact}
                                    </Badge>
                                  )}
                                  {challengeCategory && (
                                    <Badge variant="outline" className="text-xs">
                                      {challengeCategory}
                                    </Badge>
                                  )}
                                </div>
                              )}
                              
                              {/* Solution Direction */}
                              {solutionDirection && !recommendation && (
                                <div className="mt-3 rounded-lg bg-primary/5 border-l-4 border-primary/30 p-3">
                                  <p className="text-xs font-semibold text-primary mb-1.5">Solution Direction</p>
                                  <MarkdownText 
                                    content={solutionDirection} 
                                    className="text-sm text-foreground/80"
                                  />
                                </div>
                              )}
                              
                              {/* AI Recommendation */}
                              {recommendation && (
                                <div className="mt-3 rounded-lg bg-primary/5 border-l-4 border-primary/30 p-3">
                                  <p className="text-xs font-semibold text-primary mb-1.5">AI Recommendation</p>
                                  <MarkdownText 
                                    content={recommendation} 
                                    className="text-sm text-foreground/80"
                                  />
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-sm text-muted-foreground italic">No challenges identified yet.</p>
                    )}
                  </div>
                </Card>
              </TabsContent>

              <TabsContent value="questions" className="mt-6">
                <Card className="border-border/40 bg-gradient-card p-6 backdrop-blur-sm">
                  <h2 className="mb-6 font-heading text-xl font-semibold">Discovery Questions</h2>
                  {typeof discoveryQuestions === 'object' && Object.keys(discoveryQuestions).length > 0 ? (
                    <Accordion type="single" collapsible className="w-full">
                      {Object.entries(discoveryQuestions).map(([category, questions]: [string, any], index) => (
                        <AccordionItem key={index} value={`item-${index}`} className="border-border/30">
                          <AccordionTrigger className="hover:no-underline py-4 font-semibold text-foreground">
                            <span>{category}</span>
                          </AccordionTrigger>
                          <AccordionContent className="pt-2">
                            <ul className="space-y-3">
                              {(Array.isArray(questions) ? questions : []).map((question: any, qIndex: number) => {
                                const questionText = typeof question === 'string' ? question : question.text || JSON.stringify(question);
                                return (
                                  <li key={qIndex} className="flex items-start gap-3 rounded-lg bg-background/30 p-3 border border-border/20">
                                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary" />
                                    <div className="flex-1">
                                      <MarkdownText 
                                        content={questionText} 
                                        className="text-sm text-foreground/90 leading-relaxed"
                                      />
                                    </div>
                                  </li>
                                );
                              })}
                            </ul>
                          </AccordionContent>
                        </AccordionItem>
                      ))}
                    </Accordion>
                  ) : (
                    <p className="text-sm text-muted-foreground italic">No discovery questions generated yet.</p>
                  )}
                </Card>
              </TabsContent>

              <TabsContent value="cases" className="mt-6">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-heading text-xl font-semibold">Case Studies</h2>
                  {/* <Dialog open={showAddCaseStudy} onOpenChange={setShowAddCaseStudy}>
                    <DialogTrigger asChild>
                      <Button size="sm">
                        <Plus className="mr-2 h-4 w-4" />
                        Add Case Study
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Add New Case Study</DialogTitle>
                      </DialogHeader>
                      <div className="space-y-4">
                        <div>
                          <Label>Title</Label>
                          <Input
                            value={newCaseStudy.title}
                            onChange={(e) => setNewCaseStudy({ ...newCaseStudy, title: e.target.value })}
                          />
                        </div>
                        <div>
                          <Label>Industry</Label>
                          <Select
                            value={newCaseStudy.industry}
                            onValueChange={(value) => setNewCaseStudy({ ...newCaseStudy, industry: value })}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Select industry" />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="BFSI">BFSI</SelectItem>
                              <SelectItem value="Healthcare">Healthcare</SelectItem>
                              <SelectItem value="Retail">Retail</SelectItem>
                              <SelectItem value="Technology">Technology</SelectItem>
                              <SelectItem value="Manufacturing">Manufacturing</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div>
                          <Label>Impact</Label>
                          <Input
                            value={newCaseStudy.impact}
                            onChange={(e) => setNewCaseStudy({ ...newCaseStudy, impact: e.target.value })}
                            placeholder="e.g., 45% Faster Processing"
                          />
                        </div>
                        <div>
                          <Label>Description</Label>
                          <Textarea
                            value={newCaseStudy.description}
                            onChange={(e) => setNewCaseStudy({ ...newCaseStudy, description: e.target.value })}
                            rows={4}
                          />
                        </div>
                        <Button
                          onClick={() => createCaseStudyMutation.mutate(newCaseStudy)}
                          disabled={createCaseStudyMutation.isPending}
                        >
                          {createCaseStudyMutation.isPending ? "Adding..." : "Add Case Study"}
                        </Button>
                      </div>
                    </DialogContent>
                  </Dialog> */}
                </div>
                {matchingCaseStudies.length > 0 ? (
                  matchingCaseStudies.map((caseStudy: any, index: number) => {
                    const caseStudyId = caseStudy.id || index;
                    const isSelected = selectedCaseStudyIds.has(caseStudyId);
                    const matchPercentage = caseStudy.relevance_score 
                      ? Math.round((caseStudy.relevance_score || 0) * 100)
                      : caseStudy.similarity_score 
                      ? Math.round((caseStudy.similarity_score || 0) * 100)
                      : null;
                    
                    return (
                      <Card 
                        key={caseStudyId} 
                        className={`border-border/40 bg-gradient-card p-6 backdrop-blur-sm transition-all hover:-translate-y-1 hover:shadow-glass hover:border-primary/30 ${isSelected ? 'ring-2 ring-primary' : ''}`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 space-y-3">
                            <div className="flex items-center gap-3">
                              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-xs font-semibold text-primary">
                                {index + 1}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2">
                                  <h3 className="font-heading text-lg font-semibold text-foreground">
                                    {caseStudy.title || caseStudy.name || `Case Study ${index + 1}`}
                                  </h3>
                                  {matchPercentage !== null && (
                                    <Badge variant="outline" className="text-xs">
                                      {matchPercentage}% Match
                                    </Badge>
                                  )}
                                </div>
                                {caseStudy.creator_name && (
                                  <p className="text-xs text-muted-foreground mt-1">
                                    Created by {caseStudy.creator_name}
                                  </p>
                                )}
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2 ml-11">
                              {caseStudy.industry && (
                                <Badge variant="secondary">{caseStudy.industry}</Badge>
                              )}
                            </div>
                            {caseStudy.impact && (
                              <div className="ml-11">
                                <p className="text-xs font-semibold text-primary mb-1">Impact</p>
                                <div className="text-sm text-foreground/80">
                                  <MarkdownText 
                                    content={typeof caseStudy.impact === 'string' ? caseStudy.impact : JSON.stringify(caseStudy.impact)} 
                                    className="text-sm"
                                  />
                                </div>
                              </div>
                            )}
                            {caseStudy.description && (
                              <div className="ml-11 mt-2">
                                <MarkdownText 
                                  content={typeof caseStudy.description === 'string' ? caseStudy.description : JSON.stringify(caseStudy.description)} 
                                  className="text-sm text-foreground/70 line-clamp-2"
                                />
                              </div>
                            )}
                          </div>
                          <div className="flex flex-col items-end gap-2 shrink-0">
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-muted-foreground">Include in proposal</span>
                              <Switch
                                checked={isSelected}
                                onCheckedChange={(checked) => {
                                  const newSet = new Set(selectedCaseStudyIds);
                                  if (checked) {
                                    newSet.add(caseStudyId);
                                  } else {
                                    newSet.delete(caseStudyId);
                                  }
                                  setSelectedCaseStudyIds(newSet);
                                }}
                              />
                            </div>
                            <Button 
                              variant="outline" 
                              size="sm"
                              onClick={() => {
                                setViewingCaseStudy(caseStudy);
                                setIsViewDialogOpen(true);
                              }}
                            >
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </Button>
                          </div>
                        </div>
                      </Card>
                    );
                  })
                ) : (
                  <p className="text-sm text-muted-foreground italic">No matching case studies found yet.</p>
                )}
                
                {/* View Case Study Details Dialog */}
                <Dialog open={isViewDialogOpen} onOpenChange={setIsViewDialogOpen}>
                  <DialogContent className="sm:max-w-[700px] max-h-[90vh] flex flex-col">
                    <DialogHeader>
                      <DialogTitle>Case Study Details</DialogTitle>
                      <DialogDescription>
                        View complete information about this case study.
                      </DialogDescription>
                    </DialogHeader>
                    <ScrollArea className="flex-1 pr-4">
                      {viewingCaseStudy && (
                        <div className="space-y-4 py-4">
                          <div className="space-y-2">
                            <Label className="text-sm font-semibold">Title</Label>
                            <p className="text-sm">{viewingCaseStudy.title || viewingCaseStudy.name || "N/A"}</p>
                          </div>
                          <div className="flex gap-4">
                            <div className="space-y-2 flex-1">
                              <Label className="text-sm font-semibold">Industry</Label>
                              <Badge variant="secondary" className="bg-primary/10 text-primary">
                                {viewingCaseStudy.industry || "N/A"}
                              </Badge>
                            </div>
                            {(viewingCaseStudy.relevance_score || viewingCaseStudy.similarity_score) && (
                              <div className="space-y-2 flex-1">
                                <Label className="text-sm font-semibold">Match Score</Label>
                                <Badge variant="outline" className="text-sm">
                                  {Math.round(((viewingCaseStudy.relevance_score || viewingCaseStudy.similarity_score || 0) * 100))}% Match
                                </Badge>
                              </div>
                            )}
                          </div>
                          {viewingCaseStudy.creator_name && (
                            <div className="space-y-2">
                              <Label className="text-sm font-semibold">Created By</Label>
                              <p className="text-sm text-muted-foreground">{viewingCaseStudy.creator_name}</p>
                            </div>
                          )}
                          {viewingCaseStudy.impact && (
                            <div className="space-y-2">
                              <Label className="text-sm font-semibold">Impact</Label>
                              <div className="rounded-lg bg-primary/5 p-3">
                                <MarkdownText 
                                  content={typeof viewingCaseStudy.impact === 'string' ? viewingCaseStudy.impact : JSON.stringify(viewingCaseStudy.impact)}
                                  className="text-sm font-semibold text-primary"
                                />
                              </div>
                            </div>
                          )}
                          {viewingCaseStudy.description && (
                            <div className="space-y-2">
                              <Label className="text-sm font-semibold">Description</Label>
                              <div className="text-sm text-muted-foreground">
                                <MarkdownText 
                                  content={typeof viewingCaseStudy.description === 'string' ? viewingCaseStudy.description : JSON.stringify(viewingCaseStudy.description)}
                                  className="whitespace-pre-wrap"
                                />
                              </div>
                            </div>
                          )}
                          {viewingCaseStudy.project_description && (
                            <div className="space-y-2">
                              <Label className="text-sm font-semibold">Project Description</Label>
                              <div className="text-sm text-muted-foreground">
                                <MarkdownText 
                                  content={viewingCaseStudy.project_description}
                                  className="whitespace-pre-wrap"
                                />
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </ScrollArea>
                    <DialogFooter>
                      <Button variant="outline" onClick={() => setIsViewDialogOpen(false)}>
                        Close
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </TabsContent>
            </Tabs>
          </div>

          {/* Chat Panel */}
          <div>
            <Card className="border-border/40 bg-gradient-card backdrop-blur-sm sticky top-6">
              <div className="border-b border-border/40 p-4">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-5 w-5 text-primary" />
                  <h3 className="font-heading font-semibold">Chat with RFP</h3>
                </div>
              </div>
              <ScrollArea className="h-[400px] p-4">
                <div className="space-y-4">
                  {chatHistory.length === 0 && (
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                        <Sparkles className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 rounded-lg bg-background/50 p-4 text-sm border border-border/30">
                        <MarkdownText 
                          content="Hi! I can help you understand the RFP better. Ask me anything about requirements, timeline, or client needs." 
                          className="text-foreground/90"
                        />
                      </div>
                    </div>
                  )}
                  {chatHistory.map((msg, index) => (
                    <div key={index} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                      {msg.role === 'assistant' && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                          <Sparkles className="h-4 w-4 text-primary" />
                        </div>
                      )}
                      <div className={`flex-1 rounded-lg p-4 text-sm ${msg.role === 'user' ? 'bg-primary/10 text-primary' : 'bg-background/50 border border-border/30'}`}>
                        <MarkdownText 
                          content={msg.content} 
                          className={msg.role === 'user' ? 'text-primary' : 'text-foreground/90'}
                        />
                      </div>
                      {msg.role === 'user' && (
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                          <span className="text-xs">You</span>
                        </div>
                      )}
                    </div>
                  ))}
                  {isSending && (
                    <div className="flex gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                        <Sparkles className="h-4 w-4 text-primary animate-pulse" />
                      </div>
                      <div className="flex-1 rounded-lg bg-background/50 p-3 text-sm">
                        Thinking...
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>
              <div className="border-t border-border/40 p-4">
                <div className="flex gap-2">
                  <Input 
                    placeholder="Ask a question..." 
                    className="bg-background/50" 
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage();
                      }
                    }}
                    disabled={isSending}
                  />
                  <Button 
                    size="icon" 
                    className="bg-gradient-primary shrink-0"
                    onClick={handleSendMessage}
                    disabled={isSending || !chatMessage.trim()}
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

// Analysis Step Component
function AnalysisStep({ 
  label, 
  isActive, 
  isComplete 
}: { 
  label: string; 
  isActive: boolean; 
  isComplete: boolean;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center">
        {isComplete ? (
          <CheckCircle2 className="h-6 w-6 text-green-500" />
        ) : isActive ? (
          <Loader2 className="h-6 w-6 text-primary animate-spin" />
        ) : (
          <div className="h-6 w-6 rounded-full border-2 border-muted-foreground/30" />
        )}
      </div>
      <span className={`text-sm ${isActive ? 'text-foreground font-medium' : isComplete ? 'text-muted-foreground' : 'text-muted-foreground/60'}`}>
        {label}
      </span>
    </div>
  );
}