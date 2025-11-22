import { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { CheckCircle, XCircle } from "lucide-react";
import { toast } from "sonner";
import { PasswordStrengthIndicator, validatePasswordStrength } from "@/components/PasswordStrengthIndicator";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setTokenValid(false);
    } else {
      setTokenValid(true);
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    // Validate password strength
    const validation = validatePasswordStrength(password);
    if (!validation.isValid) {
      toast.error(validation.message || "Password does not meet security requirements");
      return;
    }

    setIsLoading(true);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          token, 
          new_password: password 
        }),
      });

      if (response.ok) {
        toast.success("Password reset successfully!");
        setTimeout(() => {
          navigate("/login");
        }, 1500);
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to reset password");
        if (error.detail?.includes("expired") || error.detail?.includes("invalid")) {
          setTokenValid(false);
        }
      }
    } catch (error: any) {
      toast.error(error.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (tokenValid === false) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
        <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-red-500/10 to-red-500/5">
              <XCircle className="h-7 w-7 text-destructive" />
            </div>
            <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Invalid Link</h1>
            <p className="mb-6 text-sm sm:text-base text-muted-foreground">
              This password reset link is invalid or has expired. Please request a new one.
            </p>
            <Button asChild variant="gradient" className="shadow-md hover:shadow-lg">
              <Link to="/forgot-password">Request New Link</Link>
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  if (tokenValid === null) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
        <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
          <div className="text-center">
            <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <p className="text-sm sm:text-base text-muted-foreground">Loading...</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4 py-12">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-primary shadow-lg">
            <span className="text-2xl font-bold text-primary-foreground">🔒</span>
          </div>
          <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Reset Password</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Enter your new password below</p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="password">New Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Enter new password"
              className="bg-background/50"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
            <PasswordStrengthIndicator password={password} />
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm Password</Label>
            <Input
              id="confirmPassword"
              type="password"
              placeholder="Confirm new password"
              className="bg-background/50"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <Button 
            type="submit" 
            variant="gradient"
            className="w-full shadow-md hover:shadow-lg" 
            disabled={isLoading}
          >
            {isLoading ? "Resetting..." : "Reset Password"}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="text-sm text-primary hover:underline">
            Back to Login
          </Link>
        </div>
      </Card>
    </div>
  );
}
