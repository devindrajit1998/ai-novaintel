// API client for backend communication

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface ApiError {
  detail: string;
}

// Custom error class that includes HTTP status code
export class HttpError extends Error {
  constructor(message: string, public statusCode: number) {
    super(message);
    this.name = 'HttpError';
  }
}

// Types for API requests/responses
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  full_name: string;
  password: string;
  role?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active?: boolean;
  email_verified?: boolean;
  role?: string;
}

export interface Project {
  id: number;
  name: string;
  client_name: string;
  industry: string;
  region: string;
  project_type: string;
  description?: string;
  status: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  client_name: string;
  industry: string;
  region: string;
  project_type: string;
  description?: string;
}

export interface RFPUploadResponse {
  id: number;
  filename: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  message: string;
  rfp_document_id: number;
}

export interface Insights {
  id: number;
  project_id: number;
  executive_summary?: string;
  rfp_summary?: any;
  challenges?: any[];
  value_propositions?: any[];
  discovery_questions?: any;
  matching_case_studies?: any[];
  proposal_draft?: any;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  project_id: number;
  query: string;
  conversation_history?: Array<{ role: string; content: string }>;
  top_k?: number;
}

export interface ChatResponse {
  success?: boolean;
  answer?: string;
  response?: string;
  sources?: any[];
  query?: string;
  error?: string;
}

export interface Proposal {
  id: number;
  project_id: number;
  title: string;
  sections?: any[];
  template_type: string;
  status: string;
  submitter_message?: string;
  admin_feedback?: string;
  submitted_at?: string;
  reviewed_at?: string;
  reviewed_by?: number;
  created_at: string;
  updated_at: string;
}

export interface ProposalSubmitRequest {
  message?: string;
}

export interface ProposalReviewRequest {
  action: "approve" | "reject" | "hold";
  feedback?: string;
}

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  private getAuthToken(): string | null {
    return localStorage.getItem("access_token");
  }

  private getRefreshToken(): string | null {
    return localStorage.getItem("refresh_token");
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
  }

  private clearTokens(): void {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getAuthToken();
    const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...options.headers,
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers,
    });

    // Handle authentication errors (401/403)
    if (response.status === 401 || response.status === 403) {
      // Try to refresh token if we have one
      if (token) {
        const refreshToken = this.getRefreshToken();
        if (refreshToken) {
          try {
            const refreshed = await this.refreshAccessToken(refreshToken);
            this.setTokens(refreshed.access_token, refreshed.refresh_token);

            // Retry original request with new token
            const newHeaders = {
              ...headers,
              Authorization: `Bearer ${refreshed.access_token}`,
            };
            const retryResponse = await fetch(url, {
              ...options,
              headers: newHeaders,
            });

            if (retryResponse.ok) {
              return retryResponse.json();
            }
          } catch (error) {
            // Refresh failed, clear tokens
            this.clearTokens();
            // Don't redirect here - let the component handle it
            throw new Error("Session expired. Please login again.");
          }
        }
      }

      // No token or refresh failed
      this.clearTokens();
      // Don't redirect here - let ProtectedRoute handle it
      throw new Error("Authentication required. Please login.");
    }

    if (!response.ok) {
      // Suppress console errors for expected 404s on insights endpoint
      const isInsights404 = response.status === 404 && endpoint.includes('/insights/get');
      
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      
      // Don't log expected 404s to console
      if (!isInsights404) {
        console.error(`API Error [${response.status}]: ${error.detail || "An error occurred"}`);
      }
      
      throw new HttpError(error.detail || "An error occurred", response.status);
    }

    // Handle empty responses
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return response.json();
    }

    return {} as T;
  }

  // Auth endpoints
  async login(credentials: LoginRequest): Promise<TokenResponse> {
    const response = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    this.setTokens(response.access_token, response.refresh_token);
    return response;
  }

  async register(userData: RegisterRequest): Promise<User> {
    const response = await this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify(userData),
    });
    // Don't auto-login after registration if email verification is required
    // Return response so frontend can handle verification message
    return response;
  }

  async refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
    return this.request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
  }

  logout(): void {
    this.clearTokens();
  }

  // User profile endpoints
  async getCurrentUser(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  async updateUserProfile(data: {
    full_name?: string;
    role?: string;
  }): Promise<User> {
    return this.request<User>("/auth/me", {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async getUserSettings(): Promise<any> {
    return this.request<any>("/auth/me/settings");
  }

  async updateUserSettings(settings: {
    proposal_tone?: string;
    ai_response_style?: string;
    secure_mode?: boolean;
    auto_save_insights?: boolean;
  }): Promise<any> {
    return this.request<any>("/auth/me/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    });
  }

  // Project endpoints
  async createProject(project: ProjectCreate): Promise<Project> {
    return this.request<Project>("/projects/create", {
      method: "POST",
      body: JSON.stringify(project),
    });
  }

  async listProjects(): Promise<Project[]> {
    return this.request<Project[]>("/projects/list");
  }

  async getProject(projectId: number): Promise<Project> {
    return this.request<Project>(`/projects/${projectId}`);
  }

  async updateProject(
    projectId: number,
    project: Partial<ProjectCreate>
  ): Promise<Project> {
    return this.request<Project>(`/projects/${projectId}`, {
      method: "PUT",
      body: JSON.stringify(project),
    });
  }

  async deleteProject(projectId: number): Promise<void> {
    return this.request<void>(`/projects/${projectId}`, {
      method: "DELETE",
    });
  }

  // Upload endpoints
  async uploadRFP(projectId: number, file: File): Promise<RFPUploadResponse> {
    const token = this.getAuthToken();
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${this.baseURL}/upload/rfp?project_id=${projectId}`,
      {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error: ApiError = await response.json().catch(() => ({
        detail: `HTTP ${response.status}: ${response.statusText}`,
      }));
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  // Insights endpoints
  async getInsights(projectId: number): Promise<Insights | null> {
    try {
      return await this.request<Insights>(`/insights/get?project_id=${projectId}`);
    } catch (error: any) {
      // If insights don't exist yet (404), return null instead of throwing
      // This is expected when insights are still being generated
      if (error instanceof HttpError && error.statusCode === 404) {
        // Silently return null - don't log expected 404s
        return null;
      }
      throw error;
    }
  }

  // RAG endpoints
  async buildIndex(
    rfpDocumentId: number
  ): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(
      "/rag/build-index",
      {
        method: "POST",
        body: JSON.stringify({ rfp_document_id: rfpDocumentId }),
      }
    );
  }

  async getRagStatus(projectId: number): Promise<any> {
    return this.request<any>(`/rag/status/${projectId}`);
  }

  async chatWithRFP(
    projectId: number,
    query: string,
    conversationHistory?: Array<{ role: string; content: string }>
  ): Promise<ChatResponse> {
    try {
      const response = await this.request<ChatResponse>("/rag/chat", {
        method: "POST",
        body: JSON.stringify({
          project_id: projectId,
          query,
          conversation_history: conversationHistory || [],
          top_k: 5,
        }),
      });
      // Backend returns 'answer' field, ensure both fields are populated for compatibility
      return {
        ...response,
        answer: response.answer || "",
        response: response.answer || response.response || "",
        success: response.success !== undefined ? response.success : true, // Default to true if not provided
      };
    } catch (error: any) {
      // Return a proper error response if the request fails
      return {
        success: false,
        error: error.message || "Failed to connect to chat service",
        answer: "",
        response: "",
        sources: [],
        query: query
      };
    }
  }

  // Agents/Workflow endpoints
  async runWorkflow(
    projectId: number,
    rfpDocumentId: number,
    selectedTasks?: {
      challenges?: boolean;
      questions?: boolean;
      cases?: boolean;
      proposal?: boolean;
    }
  ): Promise<any> {
    return this.request<any>("/agents/run-all", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        rfp_document_id: rfpDocumentId,
        selected_tasks: selectedTasks,
      }),
    });
  }

  async getWorkflowState(stateId: string): Promise<any> {
    return this.request<any>("/agents/get-state", {
      method: "POST",
      body: JSON.stringify({ state_id: stateId }),
    });
  }

  async getWorkflowStatus(projectId: number): Promise<any> {
    return this.request<any>(`/agents/status?project_id=${projectId}`);
  }

  // Case studies endpoints
  async listCaseStudies(): Promise<any[]> {
    return this.request<any[]>("/case-studies");
  }

  async getCaseStudy(id: number): Promise<any> {
    return this.request<any>(`/case-studies/${id}`);
  }

  async createCaseStudy(caseStudy: {
    title: string;
    industry: string;
    impact: string;
    description?: string;
  }): Promise<any> {
    return this.request<any>("/case-studies", {
      method: "POST",
      body: JSON.stringify(caseStudy),
    });
  }

  async updateCaseStudy(
    id: number,
    caseStudy: {
      title?: string;
      industry?: string;
      impact?: string;
      description?: string;
    }
  ): Promise<any> {
    return this.request<any>(`/case-studies/${id}`, {
      method: "PUT",
      body: JSON.stringify(caseStudy),
    });
  }

  async deleteCaseStudy(id: number): Promise<void> {
    return this.request<void>(`/case-studies/${id}`, {
      method: "DELETE",
    });
  }

  // Case study document endpoints
  async uploadCaseStudyDocument(file: File): Promise<any> {
    const token = this.getAuthToken();
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${this.baseURL}/case-study-documents/upload`,
      {
        method: "POST",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Upload failed");
    }

    return response.json();
  }

  async listCaseStudyDocuments(): Promise<any[]> {
    return this.request<any[]>("/case-study-documents/list");
  }

  async deleteCaseStudyDocument(id: number): Promise<void> {
    return this.request<void>(`/case-study-documents/${id}`, {
      method: "DELETE",
    });
  }

  // Proposal endpoints
  async getProposal(proposalId: number): Promise<any> {
    return this.request<any>(`/proposal/${proposalId}`);
  }

  async getProposalByProject(projectId: number): Promise<any> {
    // Get proposal for a project (if exists)
    try {
      return await this.request<any>(`/proposal/by-project/${projectId}`);
    } catch (error: any) {
      // Return null if 404 (proposal doesn't exist yet)
      if (
        error.message?.includes("404") ||
        error.message?.includes("not found")
      ) {
        return null;
      }
      throw error;
    }
  }

  async saveProposal(proposal: any): Promise<any> {
    return this.request<any>("/proposal/save", {
      method: "POST",
      body: JSON.stringify(proposal),
    });
  }

  async updateProposal(proposalId: number, proposal: any): Promise<any> {
    return this.request<any>(`/proposal/${proposalId}`, {
      method: "PUT",
      body: JSON.stringify(proposal),
    });
  }

  async generateProposal(
    projectId: number,
    templateType: string = "full",
    useInsights: boolean = true,
    selectedCaseStudyIds?: number[]
  ): Promise<any> {
    return this.request<any>("/proposal/generate", {
      method: "POST",
      body: JSON.stringify({
        project_id: projectId,
        template_type: templateType,
        use_insights: useInsights,
        selected_case_study_ids: selectedCaseStudyIds || undefined,
      }),
    });
  }

  async saveProposalDraft(
    proposalId: number,
    sections: any[],
    title?: string
  ): Promise<any> {
    return this.request<any>("/proposal/save-draft", {
      method: "POST",
      body: JSON.stringify({
        proposal_id: proposalId,
        sections,
        title,
      }),
    });
  }

  async getProposalPreview(proposalId: number): Promise<any> {
    return this.request<any>(`/proposal/${proposalId}/preview`);
  }

  async regenerateSection(
    proposalId: number,
    sectionId: number,
    sectionTitle: string
  ): Promise<any> {
    return this.request<any>("/proposal/regenerate-section", {
      method: "POST",
      body: JSON.stringify({
        proposal_id: proposalId,
        section_id: sectionId,
        section_title: sectionTitle,
      }),
    });
  }

  async exportProposal(
    proposalId: number,
    format: "pdf" | "docx" | "pptx"
  ): Promise<Blob> {
    const token = this.getAuthToken();
    const formatMap: Record<string, string> = {
      pdf: "pdf",
      docx: "docx",
      pptx: "pptx",
    };
    const endpoint = formatMap[format] || "pdf";

    const response = await fetch(
      `${this.baseURL}/proposal/export/${proposalId}/${endpoint}`,
      {
        method: "GET",
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
      }
    );

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: "Export failed" }));
      throw new Error(error.detail || "Export failed");
    }

    return response.blob();
  }

  // Global Search
  async globalSearch(query: string): Promise<any[]> {
    return this.request<any[]>(`/search?q=${encodeURIComponent(query)}`);
  }

  // Notifications
  async getNotifications(): Promise<any[]> {
    return this.request<any[]>("/notifications");
  }

  async markNotificationAsRead(id: number): Promise<void> {
    return this.request<void>(`/notifications/${id}/read`, {
      method: "PUT",
    });
  }

  async markAllNotificationsAsRead(): Promise<void> {
    return this.request<void>("/notifications/read-all", {
      method: "PUT",
    });
  }

  // Publish Project as Case Study
  async publishProjectAsCaseStudy(projectId: number): Promise<any> {
    return this.request<any>(`/projects/${projectId}/publish-case-study`, {
      method: "POST",
    });
  }

  async submitProposal(proposalId: number, message?: string, managerId?: number): Promise<Proposal> {
    return this.request<Proposal>(`/proposal/${proposalId}/submit`, {
      method: "POST",
      body: JSON.stringify({ message, manager_id: managerId }),
    });
  }

  async getManagers(): Promise<User[]> {
    return this.request<User[]>("/auth/managers");
  }

  async reviewProposal(proposalId: number, action: "approve" | "reject" | "hold", feedback?: string): Promise<Proposal> {
    return this.request<Proposal>(`/proposal/${proposalId}/review`, {
      method: "POST",
      body: JSON.stringify({ action, feedback }),
    });
  }

  async getAdminDashboardProposals(status?: string): Promise<Proposal[]> {
    const query = status ? `?status=${status}` : "";
    return this.request<Proposal[]>(`/proposal/admin/dashboard${query}`);
  }

  async getAdminAnalytics(): Promise<any> {
    return this.request<any>("/proposal/admin/analytics");
  }
}

export const apiClient = new ApiClient(API_BASE_URL);
