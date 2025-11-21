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
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all hover:bg-accent/50 hover:shadow-sm group"
          activeClassName="bg-gradient-to-r from-primary/15 to-primary/5 text-primary font-medium border-l-2 border-primary shadow-sm"
        >
          <div className="flex items-center justify-center w-9 h-9 rounded-md bg-muted/50 group-hover:bg-primary/10 transition-colors">
            <item.icon className="h-5 w-5" />
          </div>
          {open && (
            <div className="flex-1 flex items-center justify-between">
              <div className="flex flex-col">
                <span className="font-medium">{item.name}</span>
                {item.description && (
                  <span className="text-xs text-muted-foreground">{item.description}</span>
                )}
              </div>
              {item.badge && (
                <Badge variant="secondary" className="ml-auto text-xs px-1.5 py-0.5 bg-primary/10 text-primary border-0">
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
    <Sidebar className="border-r border-border/40 bg-gradient-to-b from-background to-muted/20">
      <SidebarHeader className="border-b border-border/40 p-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-primary/60 shadow-lg">
            <Sparkles className="h-6 w-6 text-primary-foreground" />
          </div>
          {open && (
            <div className="flex flex-col">
              <h2 className="text-lg font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                NovaIntel
              </h2>
              <p className="text-xs text-muted-foreground">AI Proposal Platform</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent className="px-2 py-4">
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

      <SidebarFooter className="border-t border-border/40 p-3">
        {user && open && (
          <div className="mb-2 px-2 py-2 rounded-lg bg-muted/50">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-9 h-9 rounded-full bg-gradient-to-br from-primary to-primary/60 text-primary-foreground font-semibold text-sm">
                {user.email?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.email}</p>
                <p className="text-xs text-muted-foreground">Active Account</p>
              </div>
            </div>
          </div>
        )}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={handleLogout}
              className="w-full justify-start gap-3 px-3 py-2.5 text-sm hover:bg-destructive/10 hover:text-destructive transition-colors rounded-lg"
            >
              <div className="flex items-center justify-center w-9 h-9 rounded-md bg-muted/50">
                <LogOut className="h-5 w-5" />
              </div>
              {open && <span className="font-medium">Logout</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
