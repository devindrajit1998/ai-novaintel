import { useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ArrowLeft, Mail } from "lucide-react";
import { toast } from "sonner";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        setEmailSent(true);
        toast.success("Password reset link sent to your email");
      } else {
        const error = await response.json();
        toast.error(error.detail || "Failed to send reset link");
      }
    } catch (error: any) {
      toast.error(error.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
        <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
          <div className="text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-to-br from-green-500/10 to-green-500/5">
              <Mail className="h-7 w-7 text-green-600" />
            </div>
            <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Check Your Email</h1>
            <p className="mb-6 text-sm sm:text-base text-muted-foreground">
              We've sent a password reset link to <strong>{email}</strong>. 
              Please check your email and follow the instructions to reset your password.
            </p>
            <Button asChild variant="outline" className="w-full">
              <Link to="/login">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Login
              </Link>
            </Button>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-6 sm:p-8">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-gradient-primary shadow-lg">
            <Mail className="h-7 w-7 text-primary-foreground" />
          </div>
          <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Forgot Password?</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Enter your email address and we'll send you a link to reset your password.
          </p>
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

          <Button 
            type="submit" 
            variant="gradient"
            className="w-full shadow-md hover:shadow-lg" 
            disabled={isLoading}
          >
            {isLoading ? "Sending..." : "Send Reset Link"}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <Link to="/login" className="flex items-center justify-center text-sm text-primary hover:underline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Login
          </Link>
        </div>
      </Card>
    </div>
  );
}
