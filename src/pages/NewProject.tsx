import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Combobox } from "@/components/ui/combobox";
import { Switch } from "@/components/ui/switch";
import { Upload, Sparkles } from "lucide-react";
import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

export default function NewProject() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [clientName, setClientName] = useState("");
  const [industry, setIndustry] = useState("");
  const [region, setRegion] = useState("");
  const [projectType, setProjectType] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [workflowRunning, setWorkflowRunning] = useState(false);

  // Options for searchable dropdowns
  const industryOptions = [
    { value: "BFSI", label: "BFSI (Banking, Financial Services & Insurance)" },
    { value: "Healthcare", label: "Healthcare & Life Sciences" },
    { value: "Technology", label: "Technology & Software" },
    { value: "Telecommunications", label: "Telecommunications" },
    { value: "Manufacturing", label: "Manufacturing & Industrial" },
    { value: "Retail", label: "Retail & E-commerce" },
    { value: "Energy", label: "Energy & Utilities" },
    { value: "Government", label: "Government & Public Sector" },
    { value: "Education", label: "Education" },
    { value: "Media", label: "Media & Entertainment" },
    { value: "Transportation", label: "Transportation & Logistics" },
    { value: "Real Estate", label: "Real Estate & Construction" },
    { value: "Hospitality", label: "Hospitality & Travel" },
    { value: "Aerospace", label: "Aerospace & Defense" },
    { value: "Automotive", label: "Automotive" },
    { value: "Pharmaceuticals", label: "Pharmaceuticals" },
    { value: "Consulting", label: "Consulting & Professional Services" },
    { value: "Other", label: "Other" },
  ];

  const regionOptions = [
    { value: "North America", label: "North America (US, Canada, Mexico)" },
    { value: "South America", label: "South America" },
    { value: "Europe", label: "Europe (UK, Germany, France, etc.)" },
    { value: "APAC", label: "Asia Pacific (India, China, Japan, Australia, etc.)" },
    { value: "Middle East", label: "Middle East (UAE, Saudi Arabia, etc.)" },
    { value: "Africa", label: "Africa" },
    { value: "India", label: "India" },
    { value: "Southeast Asia", label: "Southeast Asia (Singapore, Malaysia, etc.)" },
    { value: "LATAM", label: "Latin America" },
    { value: "Global", label: "Global/Multi-region" },
  ];

  const projectTypeOptions = [
    { value: "new", label: "New Business / Greenfield" },
    { value: "expansion", label: "Expansion / Upsell" },
    { value: "renewal", label: "Renewal / Contract Extension" },
  ];
  const [selectedTasks, setSelectedTasks] = useState({
    challenges: true,
    questions: true,
    cases: true,
  });
  const [projectId, setProjectId] = useState<number | null>(null);

  const handleTaskToggle = (taskId: string) => {
    setSelectedTasks(prev => ({
      ...prev,
      [taskId]: !prev[taskId as keyof typeof prev]
    }));
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const createProjectMutation = useMutation({
    mutationFn: async () => {
      if (!clientName || !industry || !region || !projectType) {
        throw new Error("Please fill in all required fields");
      }
      
      // Normalize project_type value (handle legacy "new_business" value)
      const normalizedProjectType = projectType === "new_business" ? "new" : projectType;
      
      const project = await apiClient.createProject({
        name: `${clientName} - ${projectType}`,
        client_name: clientName,
        industry,
        region,
        project_type: normalizedProjectType,
        description: description || undefined,
      });
      
      setProjectId(project.id);
      return project;
    },
    onSuccess: async (project) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast.success("Project created successfully!");
      
      // If file is selected, upload it
      if (selectedFile && project.id) {
        try {
          // Upload with auto-index enabled (but not auto-analyze, since we need to use selected tasks)
          const uploadResult = await apiClient.uploadRFP(project.id, selectedFile, {
            auto_index: true,
            auto_analyze: false  // We'll run workflow manually with selected tasks
          });
          
          if (uploadResult.indexed) {
            toast.success("RFP uploaded and indexed successfully!");
          } else {
            toast.success("RFP uploaded successfully!");
          }
          
          // Navigate to insights page immediately after upload
          const tasksParam = new URLSearchParams();
          tasksParam.set('project_id', project.id.toString());
          if (selectedTasks.challenges) tasksParam.set('challenges', 'true');
          if (selectedTasks.questions) tasksParam.set('questions', 'true');
          if (selectedTasks.cases) tasksParam.set('cases', 'true');
          navigate(`/insights?${tasksParam.toString()}`);
          
          // Run workflow in the background if tasks are selected (only once)
          if ((selectedTasks.challenges || selectedTasks.questions || selectedTasks.cases) && !workflowRunning) {
            setWorkflowRunning(true);
            (async () => {
              try {
                // Ensure index is built before running workflow
                if (!uploadResult.indexed) {
                  // Poll for index completion (max 30 seconds)
                  let indexReady = false;
                  for (let i = 0; i < 15; i++) {
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    try {
                      const ragStatus = await apiClient.getRagStatus(project.id);
                      // Check if index is ready (either indexed_documents_count or next_steps.ready)
                      if (ragStatus.indexed_documents_count > 0 || ragStatus.next_steps?.ready) {
                        indexReady = true;
                        break;
                      }
                    } catch (e) {
                      // Continue polling
                    }
                  }
                  
                  if (!indexReady) {
                    toast.error("Index building is taking too long. Please try again later.");
                    setWorkflowRunning(false);
                    return;
                  }
                }
                
                console.log(`Starting workflow for project ${project.id}, RFP document ${uploadResult.rfp_document_id}`);
                const workflowResult = await apiClient.runWorkflow(project.id, uploadResult.rfp_document_id, selectedTasks);
                console.log("Workflow result:", workflowResult);
                
                if (!workflowResult.success) {
                  console.error(`Workflow failed: ${workflowResult.error || 'Unknown error'}`);
                  toast.error(`Analysis failed: ${workflowResult.error || 'Unknown error'}`);
                } else {
                  toast.success("Analysis started! Results will appear shortly.");
                }
              } catch (error: any) {
                const errorMessage = error.message || error.detail || 'Unknown error';
                console.error(`Failed to start analysis: ${errorMessage}`);
                toast.error(`Failed to start analysis: ${errorMessage}`);
              } finally {
                setWorkflowRunning(false);
              }
            })();
          } else {
            if (workflowRunning) {
              console.log("Workflow already running, skipping duplicate request");
            } else {
              console.log("No tasks selected, skipping workflow");
            }
          }
        } catch (error: any) {
          toast.error(`Failed to upload RFP: ${error.message}`);
          // Still navigate to dashboard even if upload fails
          navigate("/dashboard");
        }
      } else {
        // No file selected - just navigate to dashboard
        navigate("/dashboard");
      }
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to create project");
    },
  });

  const handleAnalyze = async () => {
    // If no project created yet, create it first
    if (!projectId) {
      if (!selectedFile) {
        toast.error("Please select an RFP file to analyze");
        return;
      }
      // Create project first, then handleAnalyze will be called again via onSuccess
      createProjectMutation.mutate();
      return;
    }
    
    // If no file selected, show error
    if (!selectedFile) {
      toast.error("Please select an RFP file to analyze");
      return;
    }

    try {
      // Upload file with auto-index enabled (but not auto-analyze, since we need to use selected tasks)
      const uploadResult = await apiClient.uploadRFP(projectId, selectedFile, {
        auto_index: true,
        auto_analyze: false  // We'll run workflow manually with selected tasks
      });
      
      if (uploadResult.indexed) {
        toast.success("RFP uploaded and indexed successfully!");
      } else {
        toast.success("RFP uploaded successfully!");
      }
      
      // Navigate to insights page immediately after upload
      const tasksParam = new URLSearchParams();
      tasksParam.set('project_id', projectId.toString());
      if (selectedTasks.challenges) tasksParam.set('challenges', 'true');
      if (selectedTasks.questions) tasksParam.set('questions', 'true');
      if (selectedTasks.cases) tasksParam.set('cases', 'true');
      navigate(`/insights?${tasksParam.toString()}`);
      
      // Run workflow in the background if tasks are selected (only once)
      if ((selectedTasks.challenges || selectedTasks.questions || selectedTasks.cases) && !workflowRunning) {
        setWorkflowRunning(true);
        (async () => {
          try {
            // Ensure index is built before running workflow
            if (!uploadResult.indexed) {
              // Poll for index completion (max 30 seconds)
              let indexReady = false;
              for (let i = 0; i < 15; i++) {
                await new Promise(resolve => setTimeout(resolve, 2000));
                try {
                  const ragStatus = await apiClient.getRagStatus(projectId);
                  // Check if index is ready (either indexed_documents_count or next_steps.ready)
                  if (ragStatus.indexed_documents_count > 0 || ragStatus.next_steps?.ready) {
                    indexReady = true;
                    break;
                  }
                } catch (e) {
                  // Continue polling
                }
              }
              
              if (!indexReady) {
                toast.error("Index building is taking too long. Please try again later.");
                setWorkflowRunning(false);
                return;
              }
            }
            
            console.log(`Starting workflow for project ${projectId}, RFP document ${uploadResult.rfp_document_id}`);
            const workflowResult = await apiClient.runWorkflow(projectId, uploadResult.rfp_document_id, selectedTasks);
            console.log("Workflow result:", workflowResult);
            
            if (!workflowResult.success) {
              console.error(`Workflow failed: ${workflowResult.error || 'Unknown error'}`);
              toast.error(`Analysis failed: ${workflowResult.error || 'Unknown error'}`);
            } else {
              toast.success("Analysis started! Results will appear shortly.");
            }
          } catch (error: any) {
            const errorMessage = error.message || error.detail || 'Unknown error';
            console.error(`Failed to start analysis: ${errorMessage}`);
            toast.error(`Failed to start analysis: ${errorMessage}`);
          } finally {
            setWorkflowRunning(false);
          }
        })();
      } else {
        if (workflowRunning) {
          console.log("Workflow already running, skipping duplicate request");
        } else {
          console.log("No tasks selected, skipping workflow");
        }
      }
    } catch (error: any) {
      toast.error(error.message || "Upload failed");
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-8">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-8 border border-border/40">
          <div className="relative z-10">
            <h1 className="mb-2 font-heading text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">Create New Project</h1>
            <p className="text-muted-foreground text-lg">
              Upload your RFP and let AI extract insights to jumpstart your presales process
            </p>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Client Information */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground text-sm font-bold">1</span>
                Client Information
              </h2>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="clientName">Client Name</Label>
                  <Input 
                    id="clientName" 
                    placeholder="Enter client name" 
                    className="bg-background/50"
                    value={clientName}
                    onChange={(e) => setClientName(e.target.value)}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="industry">Industry</Label>
                  <Combobox
                    options={industryOptions}
                    value={industry}
                    onValueChange={setIndustry}
                    placeholder="Select industry"
                    searchPlaceholder="Search industries..."
                    emptyMessage="No industry found."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="region">Region</Label>
                  <Combobox
                    options={regionOptions}
                    value={region}
                    onValueChange={setRegion}
                    placeholder="Select region"
                    searchPlaceholder="Search regions..."
                    emptyMessage="No region found."
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="projectType">Project Type</Label>
                  <Combobox
                    options={projectTypeOptions}
                    value={projectType}
                    onValueChange={setProjectType}
                    placeholder="Select project type"
                    searchPlaceholder="Search project types..."
                    emptyMessage="No project type found."
                  />
                </div>
              </div>
              <div className="mt-6 space-y-2">
                <Label htmlFor="description">Project Description (Optional)</Label>
                <Textarea
                  id="description"
                  placeholder="Brief overview of the opportunity..."
                  className="bg-background/50"
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
            </Card>

            {/* Upload RFP */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground text-sm font-bold">2</span>
                Upload RFP Document <span className="text-destructive">*</span>
              </h2>
              <p className="text-sm text-muted-foreground mb-4">RFP document upload is required before analysis can proceed.</p>
              <div
                className="flex items-center justify-center rounded-xl border-2 border-dashed border-border bg-background/30 p-12 transition-colors hover:border-primary/50 cursor-pointer"
                onDrop={handleFileDrop}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  className="hidden"
                />
                <div className="text-center">
                  <Upload className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="mb-2 font-medium">
                    {selectedFile ? (
                      <span className="text-primary">{selectedFile.name}</span>
                    ) : (
                      <>
                        Drag and drop your RFP file here, or{" "}
                        <button 
                          type="button"
                          className="text-primary hover:underline"
                          onClick={(e) => {
                            e.stopPropagation();
                            fileInputRef.current?.click();
                          }}
                        >
                          browse
                        </button>
                      </>
                    )}
                  </p>
                  <p className="text-sm text-muted-foreground">Supports PDF, DOCX (Max 20MB)</p>
                </div>
              </div>
            </Card>

            {/* AI Tasks */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold flex items-center gap-2">
                <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-primary-foreground text-sm font-bold">3</span>
                Select AI Analysis Tasks
              </h2>
              <div className="space-y-4">
                {[
                  { id: "challenges", label: "Extract Business Challenges", description: "Identify key pain points and requirements" },
                  { id: "questions", label: "Generate Discovery Questions", description: "Create tailored questionnaires" },
                  { id: "cases", label: "Recommend Case Studies", description: "Match relevant success stories" },
                ].map((task) => (
                  <div 
                    key={task.id} 
                    className="flex items-center justify-between gap-4 rounded-xl border-2 border-border/50 bg-background/80 p-5 transition-all hover:border-primary/40 hover:bg-background hover:shadow-md"
                  >
                    <div className="flex-1 space-y-1.5">
                      <div className="font-semibold text-foreground">{task.label}</div>
                      <p className="text-sm text-muted-foreground/80">{task.description}</p>
                    </div>
                    <Switch 
                      checked={selectedTasks[task.id as keyof typeof selectedTasks]}
                      onCheckedChange={() => handleTaskToggle(task.id)}
                    />
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Actions Sidebar */}
          <div className="space-y-6">
            <Card className="border-border/40 bg-gradient-to-br from-primary via-primary/95 to-primary/80 p-6 text-primary-foreground shadow-2xl">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm shadow-lg">
                <Sparkles className="h-6 w-6" />
              </div>
              <h3 className="mb-2 font-heading text-xl font-semibold">AI-Powered Analysis</h3>
              <p className="mb-6 text-sm opacity-95">
                Our AI will analyze your RFP and extract key insights, generate discovery questions, and recommend relevant case studies.
              </p>
              <div className="space-y-3">
                <Button 
                  className="w-full bg-white text-primary hover:bg-white/90 shadow-lg hover:shadow-xl transition-all" 
                  size="lg"
                  onClick={handleAnalyze}
                  disabled={createProjectMutation.isPending || !clientName || !industry || !region || !projectType || !selectedFile || (!selectedTasks.challenges && !selectedTasks.questions && !selectedTasks.cases)}
                >
                  {createProjectMutation.isPending ? "Creating..." : "Analyze RFP"}
                </Button>
                <Button 
                  className="w-full border-2 border-white/30 bg-white/10 text-white backdrop-blur-sm hover:bg-white/20 hover:border-white/50 transition-all" 
                  size="lg"
                  onClick={() => {
                    if (!projectId) {
                      // Create project without file - will navigate to dashboard in onSuccess
                      createProjectMutation.mutate();
                    } else {
                      // Project already exists, just navigate to dashboard
                      queryClient.invalidateQueries({ queryKey: ["projects"] });
                      navigate("/dashboard");
                    }
                  }}
                  disabled={createProjectMutation.isPending || !clientName || !industry || !region || !projectType}
                >
                  {createProjectMutation.isPending ? "Creating..." : "Save Draft"}
                </Button>
              </div>
            </Card>

            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h3 className="mb-4 font-semibold flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-primary text-xs">💡</span>
                Quick Tips
              </h3>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li className="flex gap-2">
                  <span className="text-primary">•</span>
                  <span>Upload clear, text-based RFP documents for best results</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary">•</span>
                  <span>Select all relevant AI tasks to get comprehensive insights</span>
                </li>
                <li className="flex gap-2">
                  <span className="text-primary">•</span>
                  <span>Analysis typically takes 2-3 minutes</span>
                </li>
              </ul>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
