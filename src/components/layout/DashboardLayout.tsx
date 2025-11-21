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
      <div className="flex min-h-screen w-full">
        <AppSidebar />
        <div className="flex flex-1 flex-col">
          <Header />
          <main className="flex-1 bg-gradient-hero p-6">
            <div className="mx-auto w-full">{children}</div>
          </main>
          <footer className="border-t border-border/40 py-4 text-center text-sm text-muted-foreground">
            © 2025 NovaIntel. All rights reserved.
          </footer>
        </div>
      </div>
    </SidebarProvider>
  );
}
