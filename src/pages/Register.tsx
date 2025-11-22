import { Link, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { PasswordStrengthIndicator, validatePasswordStrength } from "@/components/PasswordStrengthIndicator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function Register() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [role, setRole] = useState<string>("pre_sales_analyst");
  const [isLoading, setIsLoading] = useState(false);
  const { register, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate]);

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
      const response = await register(email, password, fullName, role);
      // Check if email verification is required
      if (response && (response as any).email_verified === false) {
        toast.success("Account created! Please check your email to verify your account before logging in.", {
          duration: 5000,
        });
        // Redirect to login with a message
        setTimeout(() => {
          navigate("/login");
        }, 2000);
      } else {
        toast.success("Account created successfully!");
        navigate("/dashboard");
      }
    } catch (error: any) {
      toast.error(error.message || "Registration failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4 py-12">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-primary shadow-lg">
            <span className="text-2xl font-bold text-primary-foreground">N</span>
          </div>
          <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Create Account</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Start your presales journey with NovaIntel</p>
        </div>

        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="name">Full Name</Label>
            <Input
              id="name"
              type="text"
              placeholder="John Doe"
              className="bg-background/50"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

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
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Create a strong password"
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
              placeholder="Confirm your password"
              className="bg-background/50"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Select value={role} onValueChange={setRole} disabled={isLoading}>
              <SelectTrigger className="bg-background/50">
                <SelectValue placeholder="Select your role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="pre_sales_analyst">
                  <div className="flex flex-col">
                    <span className="font-medium">Pre-Sales Analyst</span>
                    <span className="text-xs text-muted-foreground">Create and submit proposals</span>
                  </div>
                </SelectItem>
                <SelectItem value="pre_sales_manager">
                  <div className="flex flex-col">
                    <span className="font-medium">Pre-Sales Manager</span>
                    <span className="text-xs text-muted-foreground">Review and approve proposals</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Analysts create proposals, Managers review and approve them
            </p>
          </div>

          <Button type="submit" variant="gradient" className="w-full shadow-md hover:shadow-lg" disabled={isLoading}>
            {isLoading ? "Creating account..." : "Create Account"} <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </form>

        <div className="mt-6 text-center text-sm">
          <span className="text-muted-foreground">Already have an account? </span>
          <Link to="/login" className="font-medium text-primary hover:underline">
            Sign in
          </Link>
        </div>
      </Card>
    </div>
  );
}
