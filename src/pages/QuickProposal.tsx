import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Upload, Sparkles, FileText, CheckCircle2, Loader2, ArrowRight } from "lucide-react";
import { useState, useRef, useCallback, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

type Status = "idle" | "uploading" | "indexing" | "analyzing" | "ready";

interface ProgressStep {
  label: string;
  status: "pending" | "active" | "complete";
}

export default function QuickProposal() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [file, setFile] = useState<File | null>(null);
  const [projectName, setProjectName] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [progress, setProgress] = useState(0);
  const [projectId, setProjectId] = useState<number | null>(null);
  const [steps, setSteps] = useState<ProgressStep[]>([
    { label: "Uploading RFP", status: "pending" },
    { label: "Building Index", status: "pending" },
    { label: "Analyzing RFP", status: "pending" },
    { label: "Extracting Challenges", status: "pending" },
    { label: "Generating Questions", status: "pending" },
    { label: "Matching Case Studies", status: "pending" },
    { label: "Building Proposal", status: "pending" },
  ]);
  
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleFileSelect = useCallback((selectedFile: File) => {
    // Validate file type
    const allowedTypes = [".pdf", ".docx"];
    const fileExt = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf("."));
    
    if (!allowedTypes.includes(fileExt)) {
      toast.error("Please upload a PDF or DOCX file");
      return;
    }
    
    // Validate file size (20MB)
    if (selectedFile.size > 20 * 1024 * 1024) {
      toast.error("File size must be less than 20MB");
      return;
    }
    
    setFile(selectedFile);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: async () => {
      const name = projectName.trim() || `Project ${new Date().toLocaleDateString()}`;
      return await apiClient.createProject({
        name,
        client_name: "Client",
        industry: "Other",
        region: "Global",
        project_type: "new",  // Valid values: "new", "expansion", "renewal"
        description: `Quick proposal generated from ${file?.name || "RFP"}`
      });
    },
  });

  // Upload and generate proposal mutation
  const generateProposalMutation = useMutation({
    mutationFn: async (projId: number) => {
      if (!file) throw new Error("No file selected");
      
      // Upload with auto-index and auto-analyze
      const uploadResult = await apiClient.uploadRFP(projId, file, {
        auto_index: true,
        auto_analyze: true
      });
      
      return { projectId: projId, uploadResult };
    },
  });

  const handleGenerate = async () => {
    if (!file) {
      toast.error("Please select an RFP file");
      return;
    }

    try {
      setStatus("uploading");
      setProgress(5);
      updateStep(0, "active");

      // Step 1: Create project
      const project = await createProjectMutation.mutateAsync();
      setProjectId(project.id);
      setProgress(10);
      updateStep(0, "complete");

      // Step 2: Upload, index, and analyze
      setStatus("indexing");
      updateStep(1, "active");
      setProgress(20);

      const { uploadResult } = await generateProposalMutation.mutateAsync(project.id);
      
      if (uploadResult.indexed) {
        updateStep(1, "complete");
        setProgress(40);
      }

      // Check if workflow completed immediately (unlikely but possible)
      if (uploadResult.analyzed && uploadResult.proposal_ready && !uploadResult.analyzing) {
        // All steps complete
        steps.forEach((_, index) => {
          if (index > 1) updateStep(index, "complete");
        });
        setProgress(100);
        setStatus("ready");
        toast.success("Proposal generated successfully!");
        
        // Navigate to proposal page
        setTimeout(() => {
          navigate(`/proposal?project_id=${project.id}`);
        }, 1500);
        return;
      }
      
      // If workflow is running in background, show message
      if (uploadResult.analyzing) {
        toast.info("Analysis started! This may take 60-90 seconds.");
      }

      // If not ready yet, poll for completion
      setStatus("analyzing");
      updateStep(2, "active");
      setProgress(50);

      let pollCount = 0;
      const maxPolls = 90; // 3 minutes (90 * 2 seconds)
      
      // Poll for insights/proposal with better error handling
      pollIntervalRef.current = setInterval(async () => {
        pollCount++;
        
        try {
          // Try to get workflow status first (more detailed)
          let workflowStatus = null;
          try {
            workflowStatus = await apiClient.getWorkflowStatus(project.id);
          } catch (e) {
            // Workflow status endpoint might not be available, continue with insights check
          }
          
          // Update progress based on workflow status if available
          // Don't check insights yet - workflow status is the source of truth
          if (workflowStatus?.progress) {
            const progress = workflowStatus.progress;
            if (progress.rfp_analyzer) {
              updateStep(2, "complete");
              updateStep(3, "active");
              setProgress(60);
            }
            if (progress.challenge_extractor) {
              updateStep(3, "complete");
              updateStep(4, "active");
              setProgress(70);
            }
            if (progress.value_proposition) {
              updateStep(4, "complete");
            }
            if (progress.discovery_question) {
              updateStep(4, "complete");
              updateStep(5, "active");
              setProgress(80);
            }
            if (progress.case_study_matcher) {
              updateStep(5, "complete");
              updateStep(6, "active");
              setProgress(90);
            }
            if (progress.proposal_builder) {
              updateStep(6, "complete");
              setProgress(100);
            }
          }
          
          // Check workflow status
          if (workflowStatus?.status === "completed") {
            // Workflow completed - check if proposal is ready
            const proposalReady = workflowStatus.progress?.proposal_builder === true;
            const hasData = workflowStatus.has_data !== false; // Default to true if not specified
            
            // Always try to get insights to check for proposal_draft
            try {
              const insights = await apiClient.getInsights(project.id);
              
              // Check if we have a proposal draft (most important for Quick Proposal)
              if (insights?.proposal_draft) {
                // Proposal is ready!
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current);
                  pollIntervalRef.current = null;
                }
                steps.forEach((_, index) => {
                  if (index >= 2) updateStep(index, "complete");
                });
                setProgress(100);
                setStatus("ready");
                toast.success("Proposal generated successfully!");
                
                setTimeout(() => {
                  navigate(`/proposal?project_id=${project.id}`);
                }, 1500);
                return;
              }
              
              // If no proposal_draft but we have other insights, still proceed (user can generate proposal manually)
              if (insights && (insights.executive_summary || insights.challenges || hasData)) {
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current);
                  pollIntervalRef.current = null;
                }
                steps.forEach((_, index) => {
                  if (index >= 2) updateStep(index, "complete");
                });
                setProgress(100);
                setStatus("ready");
                toast.success("Analysis completed! Generating proposal...");
                
                // Navigate to proposal page - it will generate from insights
                setTimeout(() => {
                  navigate(`/proposal?project_id=${project.id}`);
                }, 1500);
                return;
              }
            } catch (e: any) {
              // Insights not found - continue polling a bit more
              if (pollCount < maxPolls - 3) {
                return;
              } else {
                // After many polls, if status says completed but no insights, something is wrong
                console.error("Workflow status says completed but insights not found:", e);
                if (pollIntervalRef.current) {
                  clearInterval(pollIntervalRef.current);
                  pollIntervalRef.current = null;
                }
                setStatus("error");
                toast.error("Analysis completed but results not found. Please check the Insights page.");
                return;
              }
            }
          } else if (workflowStatus?.status === "pending") {
            // Workflow is pending/initializing - continue polling
            if (pollCount % 5 === 0) {
              console.log("Workflow is initializing...");
            }
          } else if (workflowStatus?.status === "running") {
            // Workflow is running - progress is already updated above
            // Continue polling
          }
          
          // Check for workflow errors
          if (workflowStatus?.status === "error" || workflowStatus?.status === "failed") {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
            setStatus("idle");
            toast.error("Workflow failed. Please try again or check the console for details.");
            return;
          }
          
        } catch (error: any) {
          // Handle errors gracefully - most are expected (404s for insights not ready)
          // Only log unexpected errors occasionally to avoid spam
          if (pollCount % 10 === 0 && !error?.message?.includes('404')) {
            console.warn("Polling error (will continue):", error);
          }
          
          // Continue polling unless we've hit max polls
          // 404s are expected when insights aren't ready yet
        }
        
        // Timeout after max polls
        if (pollCount >= maxPolls) {
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
          setStatus("idle");
          toast.warning("Processing is taking longer than expected. The proposal may still be generating in the background. You can check the Insights page or come back later.");
        }
      }, 2000);

    } catch (error: any) {
      console.error("Error generating proposal:", error);
      toast.error(error.message || "Failed to generate proposal");
      setStatus("idle");
      setProgress(0);
      steps.forEach(step => step.status = "pending");
    }
  };

  const updateStep = (index: number, newStatus: "pending" | "active" | "complete") => {
    setSteps(prev => prev.map((step, i) => 
      i === index ? { ...step, status: newStatus } : step
    ));
  };

  return (
    <DashboardLayout>
      <div className="container mx-auto p-6 max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2 bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Quick Proposal Generator
          </h1>
          <p className="text-muted-foreground">
            Upload your RFP and get a complete proposal in one click. All analysis and proposal generation happens automatically.
          </p>
        </div>

        {status === "idle" && (
          <Card className="p-8 border-border/40 bg-gradient-card backdrop-blur-sm">
            <div className="space-y-6">
              {/* File Upload Area */}
              <div>
                <Label className="text-base font-semibold mb-3 block">RFP Document</Label>
                <div
                  className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
                    file
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50 cursor-pointer"
                  }`}
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.docx"
                    className="hidden"
                    onChange={(e) => {
                      const selectedFile = e.target.files?.[0];
                      if (selectedFile) handleFileSelect(selectedFile);
                    }}
                  />
                  
                  {file ? (
                    <div className="space-y-2">
                      <FileText className="h-12 w-12 text-primary mx-auto" />
                      <p className="font-medium">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFile(null);
                        }}
                      >
                        Change File
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="h-12 w-12 text-muted-foreground mx-auto" />
                      <p className="font-medium">Drag & drop your RFP file here</p>
                      <p className="text-sm text-muted-foreground">or click to browse</p>
                      <p className="text-xs text-muted-foreground mt-2">
                        Supported formats: PDF, DOCX (Max 20MB)
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Project Name (Optional) */}
              <div>
                <Label htmlFor="project-name" className="text-base font-semibold mb-3 block">
                  Project Name (Optional)
                </Label>
                <Input
                  id="project-name"
                  placeholder="Leave empty for auto-generated name"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  className="bg-background/50"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  If not provided, a name will be generated automatically
                </p>
              </div>

              {/* Generate Button */}
              <Button
                onClick={handleGenerate}
                disabled={!file || status !== "idle"}
                className="w-full bg-gradient-primary text-lg py-6"
                size="lg"
              >
                <Sparkles className="mr-2 h-5 w-5" />
                Generate Proposal
              </Button>

              <p className="text-xs text-center text-muted-foreground">
                This will automatically: index the document, analyze the RFP, extract challenges,
                generate questions, match case studies, and build a complete proposal.
              </p>
            </div>
          </Card>
        )}

        {(status === "uploading" || status === "indexing" || status === "analyzing") && (
          <Card className="p-8 border-border/40 bg-gradient-card backdrop-blur-sm">
            <div className="space-y-6">
              <div className="text-center">
                <Loader2 className="h-12 w-12 text-primary animate-spin mx-auto mb-4" />
                <h2 className="text-2xl font-semibold mb-2">Generating Your Proposal</h2>
                <p className="text-muted-foreground mb-4">
                  This usually takes 60-90 seconds. Please don't close this page.
                </p>
                {projectId && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => navigate(`/insights?project_id=${projectId}`)}
                    className="mt-2"
                  >
                    View Progress on Insights Page
                  </Button>
                )}
              </div>

              <Progress value={progress} className="h-2" />

              <div className="space-y-3">
                {steps.map((step, index) => (
                  <div
                    key={index}
                    className="flex items-center gap-3 p-3 rounded-lg bg-background/50"
                  >
                    <div className="flex-shrink-0">
                      {step.status === "complete" ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      ) : step.status === "active" ? (
                        <Loader2 className="h-5 w-5 text-primary animate-spin" />
                      ) : (
                        <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
                      )}
                    </div>
                    <span
                      className={`text-sm ${
                        step.status === "complete"
                          ? "text-green-600 dark:text-green-400"
                          : step.status === "active"
                          ? "text-primary font-medium"
                          : "text-muted-foreground"
                      }`}
                    >
                      {step.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        )}

        {status === "ready" && (
          <Card className="p-8 border-border/40 bg-gradient-card backdrop-blur-sm">
            <div className="text-center space-y-4">
              <CheckCircle2 className="h-16 w-16 text-green-500 mx-auto" />
              <h2 className="text-2xl font-semibold">Proposal Ready!</h2>
              <p className="text-muted-foreground">
                Your proposal has been generated successfully.
              </p>
              <Button
                onClick={() => navigate(`/proposal?project_id=${projectId}`)}
                className="bg-gradient-primary"
                size="lg"
              >
                View Proposal
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}

