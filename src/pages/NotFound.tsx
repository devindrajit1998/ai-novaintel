import { useLocation } from "react-router-dom";
import { useEffect } from "react";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-hero px-4">
      <Card className="w-full max-w-md border-border/40 bg-card/80 backdrop-blur-sm shadow-xl p-8 sm:p-12 text-center">
        <div className="mb-6">
          <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5">
            <span className="text-4xl font-bold text-primary">404</span>
          </div>
          <h1 className="mb-2 font-heading text-2xl sm:text-3xl font-bold">Page Not Found</h1>
          <p className="text-sm sm:text-base text-muted-foreground">
            Oops! The page you're looking for doesn't exist.
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild variant="gradient" className="shadow-md hover:shadow-lg">
            <a href="/">Return to Home</a>
          </Button>
          <Button asChild variant="outline">
            <a href="/dashboard">Go to Dashboard</a>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default NotFound;
