import { LayoutDashboard, PlusCircle, Sparkles, FileText, FolderKanban, Settings, Lightbulb, Users, TrendingUp, HelpCircle, LogOut, Shield, BarChart3, Briefcase, MessageCircle } from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useAuth } from "@/contexts/AuthContext";
import { useNavigate } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const mainMenuItems = [
  { name: "Dashboard", icon: LayoutDashboard, route: "/dashboard", description: "Overview & analytics" },
  { name: "New Project", icon: PlusCircle, route: "/new-project", description: "Create RFP", badge: "Start" },
];

const workspaceItems = [
  { name: "Case Studies", icon: FolderKanban, route: "/case-studies", description: "Your portfolio" },
  { name: "Chat", icon: MessageCircle, route: "/chat", description: "Internal messaging" },
];

const adminItems = [
  { name: "Dashboard", icon: LayoutDashboard, route: "/admin", description: "Overview" },
  { name: "Proposals", icon: FileText, route: "/admin/proposals", description: "Review & approve" },
  { name: "Users", icon: Users, route: "/admin/users", description: "User management" },
  { name: "Projects", icon: Briefcase, route: "/admin/projects", description: "All projects" },
  { name: "Analytics", icon: BarChart3, route: "/admin/analytics", description: "Reports & metrics" },
  { name: "Case Studies", icon: FolderKanban, route: "/admin/case-studies", description: "Manage portfolio" },
  { name: "Chat", icon: MessageCircle, route: "/admin/chat", description: "Monitor conversations" },
];

const settingsItems = [
  { name: "Settings", icon: Settings, route: "/settings", description: "Preferences" },
];

export function AppSidebar() {
  const { open } = useSidebar();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const MenuItem = ({ item }: { item: typeof mainMenuItems[0] }) => (
    <SidebarMenuItem>
      <SidebarMenuButton asChild className="h-auto py-0">
        <NavLink
          to={item.route}
          end={true}
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all duration-200 hover:bg-accent/50 hover:shadow-sm group"
          activeClassName="bg-gradient-to-r from-primary/15 to-primary/5 text-primary font-medium border-l-2 border-primary shadow-sm"
        >
          <div className="flex items-center justify-center w-9 h-9 rounded-md bg-muted/50 group-hover:bg-primary/10 transition-all duration-200 group-hover:scale-110">
            <item.icon className="h-5 w-5" />
          </div>
          {open && (
            <div className="flex-1 flex items-center justify-between">
              <div className="flex flex-col">
                <span className="font-medium text-sm">{item.name}</span>
                {item.description && (
                  <span className="text-xs text-muted-foreground">{item.description}</span>
                )}
              </div>
              {item.badge && (
                <Badge variant="secondary" className="ml-auto text-xs px-1.5 py-0.5 bg-primary/10 text-primary border-0 shadow-sm">
                  {item.badge}
                </Badge>
              )}
            </div>
          )}
        </NavLink>
      </SidebarMenuButton>
    </SidebarMenuItem>
  );

  return (
    <Sidebar className="border-r border-border/40 bg-gradient-to-b from-background/95 to-muted/20 backdrop-blur-sm">
      <SidebarHeader className="border-b border-border/40 p-3 sm:p-4">
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-primary to-primary/60 shadow-md hover:shadow-lg transition-shadow duration-200">
            <Sparkles className="h-5 w-5 sm:h-6 sm:w-6 text-primary-foreground" />
          </div>
          {open && (
            <div className="flex flex-col">
              <h2 className="text-base sm:text-lg font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                NovaIntel
              </h2>
              <p className="text-[10px] sm:text-xs text-muted-foreground">AI Proposal Platform</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2 py-3 sm:py-4 scrollbar-hide">
        {user?.role !== "pre_sales_manager" && (
          <>
            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu className="space-y-1">
                  {mainMenuItems.map((item) => (
                    <MenuItem key={item.name} item={item} />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <Separator className="my-4" />

            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu className="space-y-1">
                  {workspaceItems.map((item) => (
                    <MenuItem key={item.name} item={item} />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <Separator className="my-4" />
          </>
        )}

        {user?.role === "pre_sales_manager" && (
          <>
            <Separator className="my-4" />
            <SidebarGroup>
              <SidebarGroupLabel className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                Administration
              </SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu className="space-y-1">
                  {adminItems.map((item) => (
                    <MenuItem key={item.name} item={item} />
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}

        <Separator className="my-4" />

        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu className="space-y-1">
              {settingsItems.map((item) => (
                <MenuItem key={item.name} item={item} />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="border-t border-border/40 p-2 sm:p-3">
        {user && open && (
          <div className="mb-2 px-2 py-2 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors duration-200">
            <div className="flex items-center gap-2 sm:gap-3">
              <div className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-gradient-to-br from-primary to-primary/60 text-primary-foreground font-semibold text-xs sm:text-sm shadow-sm">
                {user.email?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs sm:text-sm font-medium truncate">{user.email}</p>
                <p className="text-[10px] sm:text-xs text-muted-foreground">Active Account</p>
              </div>
            </div>
          </div>
        )}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={handleLogout}
              className="w-full justify-start gap-2 sm:gap-3 px-2 sm:px-3 py-2 sm:py-2.5 text-xs sm:text-sm hover:bg-destructive/10 hover:text-destructive transition-all duration-200 rounded-lg"
            >
              <div className="flex items-center justify-center w-8 h-8 sm:w-9 sm:h-9 rounded-md bg-muted/50 hover:bg-destructive/10 transition-colors duration-200">
                <LogOut className="h-4 w-4 sm:h-5 sm:w-5" />
              </div>
              {open && <span className="font-medium">Logout</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
