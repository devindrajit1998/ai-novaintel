import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { 
    Users, 
    Search,
    Loader2,
    CheckCircle,
    XCircle,
    Edit,
    Shield,
    Mail,
    Calendar
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient, User } from "@/lib/api";
import { toast } from "sonner";
import { useState } from "react";
import { format } from "date-fns";
import { useAuth } from "@/contexts/AuthContext";

export default function AdminUsers() {
    const queryClient = useQueryClient();
    const { user } = useAuth();
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedUser, setSelectedUser] = useState<User | null>(null);
    const [editDialogOpen, setEditDialogOpen] = useState(false);
    const [editName, setEditName] = useState("");
    const [editRole, setEditRole] = useState("");

    if (user?.role !== "pre_sales_manager") {
        return (
            <DashboardLayout>
                <div className="flex items-center justify-center h-full">
                    <Card className="p-6">
                        <p className="text-muted-foreground">Access denied. Manager role required.</p>
                    </Card>
                </div>
            </DashboardLayout>
        );
    }

    const { data: users = [], isLoading } = useQuery({
        queryKey: ["admin-users"],
        queryFn: () => apiClient.getAllUsers(),
    });

    const updateUserMutation = useMutation({
        mutationFn: ({ userId, updates }: { userId: string; updates: { full_name?: string; role?: string } }) =>
            apiClient.updateUser(userId, updates),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["admin-users"] });
            toast.success("User updated successfully");
            setEditDialogOpen(false);
            setSelectedUser(null);
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to update user");
        },
    });

    const toggleActiveMutation = useMutation({
        mutationFn: ({ userId, isActive }: { userId: string; isActive: boolean }) =>
            apiClient.toggleUserActive(userId, isActive),
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ["admin-users"] });
            toast.success(`User ${variables.isActive ? "activated" : "deactivated"} successfully`);
        },
        onError: (error: any) => {
            toast.error(error.message || "Failed to update user status");
        },
    });

    const filteredUsers = users.filter((u) =>
        u.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
        u.full_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const userStats = {
        total: users.length,
        active: users.filter((u) => u.is_active).length,
        managers: users.filter((u) => u.role === "pre_sales_manager").length,
        analysts: users.filter((u) => u.role === "pre_sales_analyst").length,
        verified: users.filter((u) => u.email_verified).length,
    };

    const handleEdit = (user: User) => {
        setSelectedUser(user);
        setEditName(user.full_name);
        setEditRole(user.role || "pre_sales_analyst");
        setEditDialogOpen(true);
    };

    const handleSave = () => {
        if (!selectedUser) return;
        updateUserMutation.mutate({
            userId: selectedUser.id,
            updates: {
                full_name: editName,
                role: editRole,
            },
        });
    };

    return (
        <DashboardLayout>
            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold">User Management</h1>
                        <p className="text-muted-foreground">Manage users, roles, and permissions</p>
                    </div>
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search users..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="pl-9 w-64"
                        />
                    </div>
                </div>

                {/* Stats Cards */}
                <div className="grid gap-4 md:grid-cols-5">
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Users</p>
                                <p className="text-2xl font-bold">{userStats.total}</p>
                            </div>
                            <Users className="h-8 w-8 text-blue-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Active</p>
                                <p className="text-2xl font-bold">{userStats.active}</p>
                            </div>
                            <CheckCircle className="h-8 w-8 text-green-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Managers</p>
                                <p className="text-2xl font-bold">{userStats.managers}</p>
                            </div>
                            <Shield className="h-8 w-8 text-purple-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Analysts</p>
                                <p className="text-2xl font-bold">{userStats.analysts}</p>
                            </div>
                            <Users className="h-8 w-8 text-orange-500" />
                        </div>
                    </Card>
                    <Card className="p-4">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-muted-foreground">Verified</p>
                                <p className="text-2xl font-bold">{userStats.verified}</p>
                            </div>
                            <Mail className="h-8 w-8 text-indigo-500" />
                        </div>
                    </Card>
                </div>

                {/* Users Table */}
                <Card>
                    {isLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        </div>
                    ) : filteredUsers.length === 0 ? (
                        <div className="text-center py-12">
                            <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                            <p className="text-muted-foreground">
                                {searchQuery ? "No users match your search" : "No users found"}
                            </p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow>
                                    <TableHead>Name</TableHead>
                                    <TableHead>Email</TableHead>
                                    <TableHead>Role</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Verified</TableHead>
                                    <TableHead>Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredUsers.map((u) => (
                                    <TableRow key={u.id}>
                                        <TableCell className="font-medium">{u.full_name}</TableCell>
                                        <TableCell>{u.email}</TableCell>
                                        <TableCell>
                                            <Badge variant={u.role === "pre_sales_manager" ? "default" : "secondary"}>
                                                {u.role === "pre_sales_manager" ? "Manager" : "Analyst"}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            {u.is_active ? (
                                                <Badge variant="default" className="bg-green-500">
                                                    <CheckCircle className="h-3 w-3 mr-1" />
                                                    Active
                                                </Badge>
                                            ) : (
                                                <Badge variant="destructive">
                                                    <XCircle className="h-3 w-3 mr-1" />
                                                    Inactive
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            {u.email_verified ? (
                                                <Badge variant="outline" className="text-green-600">
                                                    Verified
                                                </Badge>
                                            ) : (
                                                <Badge variant="outline" className="text-yellow-600">
                                                    Pending
                                                </Badge>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2">
                                                <Button
                                                    size="sm"
                                                    variant="outline"
                                                    onClick={() => handleEdit(u)}
                                                >
                                                    <Edit className="h-4 w-4 mr-1" />
                                                    Edit
                                                </Button>
                                                <Button
                                                    size="sm"
                                                    variant={u.is_active ? "destructive" : "default"}
                                                    onClick={() =>
                                                        toggleActiveMutation.mutate({
                                                            userId: u.id,
                                                            isActive: !u.is_active,
                                                        })
                                                    }
                                                    disabled={toggleActiveMutation.isPending}
                                                >
                                                    {u.is_active ? "Deactivate" : "Activate"}
                                                </Button>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </Card>

                {/* Edit Dialog */}
                <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Edit User</DialogTitle>
                            <DialogDescription>
                                Update user information and role
                            </DialogDescription>
                        </DialogHeader>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium mb-2 block">Full Name</label>
                                <Input
                                    value={editName}
                                    onChange={(e) => setEditName(e.target.value)}
                                    placeholder="Full name"
                                />
                            </div>
                            <div>
                                <label className="text-sm font-medium mb-2 block">Role</label>
                                <Select value={editRole} onValueChange={setEditRole}>
                                    <SelectTrigger>
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="pre_sales_analyst">Analyst</SelectItem>
                                        <SelectItem value="pre_sales_manager">Manager</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                            <div className="p-3 bg-muted rounded-md">
                                <p className="text-sm text-muted-foreground">
                                    <strong>Email:</strong> {selectedUser?.email}
                                </p>
                            </div>
                        </div>

                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => setEditDialogOpen(false)}
                                disabled={updateUserMutation.isPending}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={handleSave}
                                disabled={updateUserMutation.isPending || !editName.trim()}
                            >
                                {updateUserMutation.isPending ? (
                                    <>
                                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        Saving...
                                    </>
                                ) : (
                                    "Save Changes"
                                )}
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </DashboardLayout>
    );
}

