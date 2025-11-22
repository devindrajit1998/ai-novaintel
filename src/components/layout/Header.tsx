import { User, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SidebarTrigger } from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import { NotificationCenter } from "@/components/notifications/NotificationCenter";
import { GlobalSearch } from "@/components/search/GlobalSearch";

export function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const userInitials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : user?.email?.[0].toUpperCase() || "U";

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 glass-effect shadow-sm">
      <div className="flex h-16 items-center gap-4 px-4 lg:px-6">
        <SidebarTrigger className="lg:hidden -ml-2" />
        
        <div className="flex flex-1 items-center gap-4">
          <div className="ml-auto w-full max-w-md">
            <GlobalSearch />
          </div>
        </div>

        <div className="flex items-center gap-3">
          <NotificationCenter />
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-9 w-9 rounded-full hover:bg-accent/50 transition-colors">
                <Avatar className="h-9 w-9 ring-2 ring-primary/20 hover:ring-primary/40 transition-all">
                  <AvatarFallback className="bg-gradient-primary text-primary-foreground font-semibold text-sm">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-64" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1.5">
                  <p className="text-sm font-semibold leading-none">
                    {user?.full_name || "User"}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground truncate">
                    {user?.email}
                  </p>
                  {user?.role && (
                    <span className="inline-flex items-center w-fit rounded-md bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary mt-1">
                      {user.role.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  )}
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={() => navigate("/settings")}
                className="cursor-pointer transition-colors"
              >
                <User className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={handleLogout} 
                className="cursor-pointer text-destructive focus:text-destructive focus:bg-destructive/10 transition-colors"
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
