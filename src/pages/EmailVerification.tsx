import { useEffect, useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle, XCircle, Mail } from "lucide-react";
import { apiClient } from "@/lib/api";

export default function EmailVerification() {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const token = searchParams.get("token");
  const type = searchParams.get("type");

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus("error");
        return;
      }

      try {
        // Call backend API to verify the token
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
        const response = await fetch(`${API_BASE_URL}/auth/verify-email/${token}`);
        
        if (response.ok) {
          setStatus("success");
        } else {
          setStatus("error");
        }
      } catch (error) {
        console.error("Email verification failed:", error);
        setStatus("error");
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
      <Card className="w-full max-w-md border-border/40 bg-gradient-card p-8 shadow-glass backdrop-blur-sm">
        <div className="text-center">
          {status === "loading" && (
            <>
              <Mail className="mx-auto mb-4 h-16 w-16 text-primary animate-pulse" />
              <h1 className="mb-2 font-heading text-3xl font-bold">Verifying Email</h1>
              <p className="text-muted-foreground">Please wait while we verify your email address...</p>
            </>
          )}

          {status === "success" && (
            <>
              <CheckCircle className="mx-auto mb-4 h-16 w-16 text-green-500" />
              <h1 className="mb-2 font-heading text-3xl font-bold">Email Verified!</h1>
              <p className="mb-6 text-muted-foreground">
                Your email has been successfully verified. You can now log in to your account.
              </p>
              <Button asChild className="bg-gradient-primary">
                <Link to="/login">Go to Login</Link>
              </Button>
            </>
          )}

          {status === "error" && (
            <>
              <XCircle className="mx-auto mb-4 h-16 w-16 text-destructive" />
              <h1 className="mb-2 font-heading text-3xl font-bold">Verification Failed</h1>
              <p className="mb-6 text-muted-foreground">
                The verification link is invalid or has expired. Please try registering again.
              </p>
              <div className="flex gap-3 justify-center">
                <Button asChild variant="outline">
                  <Link to="/register">Register Again</Link>
                </Button>
                <Button asChild className="bg-gradient-primary">
                  <Link to="/login">Go to Login</Link>
                </Button>
              </div>
            </>
          )}
        </div>
      </Card>
    </div>
  );
}
