import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export default function Settings() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  
  const [profileData, setProfileData] = useState({
    full_name: "",
    email: "",
    role: "",
  });
  
  const [settingsData, setSettingsData] = useState({
    proposal_tone: "professional",
    ai_response_style: "balanced",
    secure_mode: false,
    auto_save_insights: true,
  });

  // Load user profile
  const { data: currentUser, isLoading: isLoadingUser } = useQuery({
    queryKey: ["currentUser"],
    queryFn: () => apiClient.getCurrentUser(),
    enabled: !!user,
  });

  // Load user settings
  const { data: userSettings, isLoading: isLoadingSettings } = useQuery({
    queryKey: ["userSettings"],
    queryFn: () => apiClient.getUserSettings(),
    enabled: !!user,
  });

  // Initialize form data when user data loads
  useEffect(() => {
    if (currentUser) {
      setProfileData({
        full_name: currentUser.full_name || "",
        email: currentUser.email || "",
        role: (currentUser as any).role || "presales_manager",
      });
    }
  }, [currentUser]);

  useEffect(() => {
    if (userSettings) {
      setSettingsData({
        proposal_tone: userSettings.proposal_tone || "professional",
        ai_response_style: userSettings.ai_response_style || "balanced",
        secure_mode: userSettings.secure_mode || false,
        auto_save_insights: userSettings.auto_save_insights !== false,
      });
    }
  }, [userSettings]);

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: { full_name?: string; role?: string }) =>
      apiClient.updateUserProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      toast.success("Profile updated successfully");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to update profile");
    },
  });

  // Update settings mutation
  const updateSettingsMutation = useMutation({
    mutationFn: (settings: typeof settingsData) =>
      apiClient.updateUserSettings(settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userSettings"] });
      // Also save to localStorage for immediate use
      localStorage.setItem("userSettings", JSON.stringify(settingsData));
      toast.success("Settings saved successfully");
    },
    onError: (error: any) => {
      toast.error(error.message || "Failed to save settings");
    },
  });

  const handleSaveChanges = () => {
    // Update profile
    updateProfileMutation.mutate({
      full_name: profileData.full_name,
      role: profileData.role,
    });

    // Update settings
    updateSettingsMutation.mutate(settingsData);
  };

  const handleResetDefaults = () => {
    const defaultSettings = {
      proposal_tone: "professional",
      ai_response_style: "balanced",
      secure_mode: false,
      auto_save_insights: true,
    };
    setSettingsData(defaultSettings);
    updateSettingsMutation.mutate(defaultSettings);
    toast.success("Settings reset to defaults");
  };


  if (isLoadingUser || isLoadingSettings) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background p-8 border border-border/40">
          <div className="relative z-10">
            <h1 className="mb-2 font-heading text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">Settings</h1>
            <p className="text-muted-foreground text-lg">Manage your account preferences and AI configurations</p>
          </div>
          <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl"></div>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            {/* Profile Settings */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold">Profile Settings</h2>
              <div className="space-y-6">
                <div className="grid gap-6 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={profileData.full_name}
                      onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                      className="bg-background/50"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileData.email}
                      disabled
                      className="bg-background/50 opacity-60"
                    />
                    <p className="text-xs text-muted-foreground">Email cannot be changed</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Input
                    id="role"
                    value={profileData.role}
                    onChange={(e) => setProfileData({ ...profileData, role: e.target.value })}
                    placeholder="e.g., Presales Manager"
                    className="bg-background/50"
                  />
                </div>
              </div>
            </Card>

            {/* Preferences */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold">Preferences</h2>
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="tone">Proposal Tone</Label>
                  <Select
                    value={settingsData.proposal_tone}
                    onValueChange={(value) => setSettingsData({ ...settingsData, proposal_tone: value })}
                  >
                    <SelectTrigger className="bg-background/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="professional">Professional</SelectItem>
                      <SelectItem value="friendly">Friendly</SelectItem>
                      <SelectItem value="technical">Technical</SelectItem>
                      <SelectItem value="executive">Executive</SelectItem>
                      <SelectItem value="consultative">Consultative</SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-muted-foreground">
                    This tone will be applied when generating proposals.
                  </p>
                </div>
              </div>
            </Card>

            {/* AI Settings */}
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h2 className="mb-6 font-heading text-xl font-semibold">AI Settings</h2>
              <div className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="response">AI Response Style</Label>
                  <Select
                    value={settingsData.ai_response_style}
                    onValueChange={(value) => setSettingsData({ ...settingsData, ai_response_style: value })}
                  >
                    <SelectTrigger className="bg-background/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="concise">Concise</SelectItem>
                      <SelectItem value="balanced">Balanced</SelectItem>
                      <SelectItem value="detailed">Detailed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Separator />
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Secure Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Enhanced data privacy for sensitive documents
                    </p>
                  </div>
                  <Switch
                    checked={settingsData.secure_mode}
                    onCheckedChange={(checked) => setSettingsData({ ...settingsData, secure_mode: checked })}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <Label>Auto-Save Insights</Label>
                    <p className="text-sm text-muted-foreground">
                      Automatically save AI-generated insights
                    </p>
                  </div>
                  <Switch
                    checked={settingsData.auto_save_insights}
                    onCheckedChange={(checked) => setSettingsData({ ...settingsData, auto_save_insights: checked })}
                  />
                </div>
              </div>
            </Card>

          </div>

          <div className="space-y-6">
            <Card className="border-border/40 bg-gradient-to-br from-background to-muted/20 p-6 backdrop-blur-sm shadow-xl">
              <h3 className="mb-4 font-heading text-lg font-semibold">Actions</h3>
              <div className="space-y-3">
                <Button
                  className="w-full bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary/70 shadow-lg"
                  onClick={handleSaveChanges}
                  disabled={updateProfileMutation.isPending || updateSettingsMutation.isPending}
                >
                  {updateProfileMutation.isPending || updateSettingsMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleResetDefaults}
                  disabled={updateSettingsMutation.isPending}
                >
                  Reset to Defaults
                </Button>
              </div>
            </Card>

          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
