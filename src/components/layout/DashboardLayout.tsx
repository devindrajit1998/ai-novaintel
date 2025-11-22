import { ReactNode } from "react";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Header } from "./Header";
import { AppSidebar } from "./AppSidebar";

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <div className="flex min-h-screen w-full bg-gradient-hero">
        <AppSidebar />
        <div className="flex flex-1 flex-col min-w-0">
          <Header />
          <main className="flex-1 p-4 lg:p-6 overflow-x-hidden">
            <div className="mx-auto w-full max-w-[1600px]">{children}</div>
          </main>
          <footer className="border-t border-border/40 bg-background/50 backdrop-blur-sm py-3 px-6">
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <span>© {new Date().getFullYear()} NovaIntel. All rights reserved.</span>
              <span className="hidden sm:inline">AI-Powered Proposal Intelligence</span>
            </div>
          </footer>
        </div>
      </div>
    </SidebarProvider>
  );
}
