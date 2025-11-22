import { Link, useNavigate, useLocation } from "react-router-dom";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const from = (location.state as any)?.from?.pathname || "/dashboard";
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, location]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(email, password);
      
      // Wait for React state to update (use flushSync or wait for next tick)
      await new Promise(resolve => setTimeout(resolve, 100));
      
      toast.success("Login successful!");
      
      // Get redirect location from state or default to dashboard
      const from = (location.state as any)?.from?.pathname || "/dashboard";
      
      // Navigate after ensuring state is updated
      navigate(from, { replace: true });
    } catch (error: any) {
      // Check if error is about email verification
      const errorMessage = error.message || "";
      if (errorMessage.toLowerCase().includes("verify your email") || errorMessage.toLowerCase().includes("email not confirmed")) {
        toast.error("Please verify your email before logging in. Check your inbox for the verification link.", {
          duration: 6000,
        });
      } else {
        toast.error(errorMessage || "Login failed. Please check your credentials.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state while checking auth
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4 py-12">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-primary shadow-lg">
            <span className="text-2xl font-bold text-primary-foreground">N</span>
          </div>
          <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Welcome Back</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Sign in to continue to NovaIntel</p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@company.com"
              className="bg-background/50"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Password</Label>
              <Link to="/forgot-password" className="text-sm text-primary hover:underline">
                Forgot password?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              placeholder="Enter your password"
              className="bg-background/50"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <Button type="submit" variant="gradient" className="w-full shadow-md hover:shadow-lg" disabled={isLoading}>
            {isLoading ? "Signing in..." : "Sign In"} <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Don't have an account? </span>
          <Link to="/register" className="font-medium text-primary hover:underline">
            Create new account
          </Link>
        </div>
      </Card>
    </div>
  );
}
