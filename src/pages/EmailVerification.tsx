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
        console.error("[Email Verification] No token found in URL");
        setStatus("error");
        return;
      }

      console.log(`[Email Verification] Starting verification for token: ${token.substring(0, 20)}...`);

      try {
        // Call backend API to verify the token
        const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
        const url = `${API_BASE_URL}/auth/verify-email/${token}`;
        console.log(`[Email Verification] Calling backend: ${url.replace(token, 'TOKEN')}`);
        
        const response = await fetch(url);
        const data = await response.json().catch(() => ({}));
        
        console.log(`[Email Verification] Response status: ${response.status}`);
        console.log(`[Email Verification] Response data:`, data);
        
        if (response.ok) {
          console.log("[Email Verification] SUCCESS - Email verified");
          setStatus("success");
        } else {
          console.error(`[Email Verification] FAILED - Status: ${response.status}, Error:`, data.detail || data.message || "Unknown error");
          setStatus("error");
        }
      } catch (error) {
        console.error("[Email Verification] Exception during verification:", error);
        setStatus("error");
      }
    };

    verifyEmail();
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
        <div className="text-center">
          {status === "loading" && (
            <>
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-primary/10 to-primary/5">
                <Mail className="h-7 w-7 text-primary animate-pulse" />
              </div>
              <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Verifying Email</h1>
              <p className="text-sm sm:text-base text-muted-foreground">Please wait while we verify your email address...</p>
            </>
          )}

          {status === "success" && (
            <>
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5">
                <CheckCircle className="h-7 w-7 text-green-600" />
              </div>
              <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Email Verified!</h1>
              <p className="mb-6 text-sm sm:text-base text-muted-foreground">
                Your email has been successfully verified. You can now log in to your account.
              </p>
              <Button asChild variant="gradient" className="shadow-md hover:shadow-lg">
                <Link to="/login">Go to Login</Link>
              </Button>
            </>
          )}

          {status === "error" && (
            <>
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-red-500/10 to-red-500/5">
                <XCircle className="h-7 w-7 text-destructive" />
              </div>
              <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Verification Failed</h1>
              <p className="mb-6 text-sm sm:text-base text-muted-foreground">
                The verification link is invalid or has expired. Please try registering again.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Button asChild variant="outline" size="sm" className="text-xs sm:text-sm">
                  <Link to="/register">Register Again</Link>
                </Button>
                <Button asChild variant="gradient" size="sm" className="text-xs sm:text-sm shadow-md hover:shadow-lg">
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
