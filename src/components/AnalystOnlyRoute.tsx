import { Navigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";

interface AnalystOnlyRouteProps {
  children: React.ReactNode;
}

/**
 * Route that is only accessible to analysts (not managers).
 * Managers will be redirected to admin dashboard.
 */
export function AnalystOnlyRoute({ children }: AnalystOnlyRouteProps) {
  return (
    <ProtectedRoute>
      <AnalystOnlyContent>{children}</AnalystOnlyContent>
    </ProtectedRoute>
  );
}

function AnalystOnlyContent({ children }: AnalystOnlyRouteProps) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Redirect managers to admin dashboard
  if (user?.role === "pre_sales_manager") {
    return <Navigate to="/admin" replace />;
  }

  return <>{children}</>;
}

