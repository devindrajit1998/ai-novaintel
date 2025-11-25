import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { PublicRoute } from "@/components/PublicRoute";
import { AnalystOnlyRoute } from "@/components/AnalystOnlyRoute";
import { SystemWebSocketProvider } from "@/components/SystemWebSocketProvider";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import EmailVerification from "./pages/EmailVerification";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import Dashboard from "./pages/Dashboard";
import NewProject from "./pages/NewProject";
import QuickProposal from "./pages/QuickProposal";
import Insights from "./pages/Insights";
import ProposalBuilder from "./pages/ProposalBuilder";
import CaseStudies from "./pages/CaseStudies";
import Settings from "./pages/Settings";
import Chat from "./pages/Chat";
import AdminDashboard from "./pages/AdminDashboard";
import AdminProposals from "./pages/admin/AdminProposals";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminProjects from "./pages/admin/AdminProjects";
import AdminAnalytics from "./pages/admin/AdminAnalytics";
import AdminCaseStudies from "./pages/admin/AdminCaseStudies";
import AdminChat from "./pages/admin/AdminChat";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <BrowserRouter>
        <AuthProvider>
          <SystemWebSocketProvider>
            <Toaster />
            <Sonner />
            <Routes>
            <Route path="/" element={<Landing />} />
            <Route
              path="/login"
              element={
                <PublicRoute>
                  <Login />
                </PublicRoute>
              }
            />
            <Route
              path="/register"
              element={
                <PublicRoute>
                  <Register />
                </PublicRoute>
              }
            />
            <Route path="/verify-email" element={<EmailVerification />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route
              path="/dashboard"
              element={
                <AnalystOnlyRoute>
                  <Dashboard />
                </AnalystOnlyRoute>
              }
            />
            <Route
              path="/new-project"
              element={
                <AnalystOnlyRoute>
                  <NewProject />
                </AnalystOnlyRoute>
              }
            />
            <Route
              path="/quick-proposal"
              element={
                <AnalystOnlyRoute>
                  <QuickProposal />
                </AnalystOnlyRoute>
              }
            />
            <Route
              path="/insights"
              element={
                <ProtectedRoute>
                  <Insights />
                </ProtectedRoute>
              }
            />
            <Route
              path="/proposal"
              element={
                <ProtectedRoute>
                  <ProposalBuilder />
                </ProtectedRoute>
              }
            />
            <Route
              path="/case-studies"
              element={
                <AnalystOnlyRoute>
                  <CaseStudies />
                </AnalystOnlyRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings />
                </ProtectedRoute>
              }
            />
            <Route
              path="/chat"
              element={
                <ProtectedRoute>
                  <Chat />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/proposals"
              element={
                <ProtectedRoute>
                  <AdminProposals />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/users"
              element={
                <ProtectedRoute>
                  <AdminUsers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/projects"
              element={
                <ProtectedRoute>
                  <AdminProjects />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/analytics"
              element={
                <ProtectedRoute>
                  <AdminAnalytics />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/case-studies"
              element={
                <ProtectedRoute>
                  <AdminCaseStudies />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/chat"
              element={
                <ProtectedRoute>
                  <AdminChat />
                </ProtectedRoute>
              }
            />
            {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
            <Route path="*" element={<NotFound />} />
          </Routes>
          </SystemWebSocketProvider>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
