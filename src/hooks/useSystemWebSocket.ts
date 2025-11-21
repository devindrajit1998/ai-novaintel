import { useEffect, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { systemWebSocket, SystemWebSocketMessage } from "@/lib/systemWebSocket";
import { toast } from "sonner";

/**
 * Hook to set up system-wide WebSocket listeners for real-time updates
 */
export function useSystemWebSocket() {
  const queryClient = useQueryClient();

  // Memoize handlers to prevent re-registration
  const handleProposalUpdate = useCallback((data: SystemWebSocketMessage) => {
    if (data.proposal) {
      // Invalidate proposal-related queries
      queryClient.invalidateQueries({ queryKey: ["proposals"] });
      queryClient.invalidateQueries({ queryKey: ["admin-proposals"] });
      queryClient.invalidateQueries({ queryKey: ["admin-analytics"] });
      
      // Show toast notification
      if (data.type === "proposal_submitted") {
        toast.info(`New proposal submitted: ${data.proposal.title}`);
      } else if (data.type === "proposal_reviewed") {
        toast.success(`Proposal ${data.proposal.status}: ${data.proposal.title}`);
      }
    }
  }, [queryClient]);

  const handleProjectUpdate = useCallback((data: SystemWebSocketMessage) => {
    if (data.project) {
      // Invalidate project-related queries
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.invalidateQueries({ queryKey: ["admin-projects"] });
      queryClient.invalidateQueries({ queryKey: ["admin-analytics"] });
      
      if (data.type === "project_created") {
        toast.info(`New project created: ${data.project.name}`);
      }
    }
  }, [queryClient]);

  const handleUserUpdate = useCallback((data: SystemWebSocketMessage) => {
    if (data.user) {
      // Invalidate user-related queries
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["chat-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-analytics"] });
      
      if (data.type === "user_status_changed") {
        toast.info(`User ${data.user.is_active ? "activated" : "deactivated"}: ${data.user.full_name}`);
      }
    }
  }, [queryClient]);

  const handleNotification = useCallback((data: SystemWebSocketMessage) => {
    if (data.notification) {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    }
  }, [queryClient]);

  useEffect(() => {
    // Subscribe to all update types
    systemWebSocket.on("proposal_updated", handleProposalUpdate);
    systemWebSocket.on("proposal_submitted", handleProposalUpdate);
    systemWebSocket.on("proposal_reviewed", handleProposalUpdate);
    systemWebSocket.on("project_created", handleProjectUpdate);
    systemWebSocket.on("project_updated", handleProjectUpdate);
    systemWebSocket.on("user_updated", handleUserUpdate);
    systemWebSocket.on("user_status_changed", handleUserUpdate);
    systemWebSocket.on("notification_new", handleNotification);

    return () => {
      // Cleanup listeners
      systemWebSocket.off("proposal_updated", handleProposalUpdate);
      systemWebSocket.off("proposal_submitted", handleProposalUpdate);
      systemWebSocket.off("proposal_reviewed", handleProposalUpdate);
      systemWebSocket.off("project_created", handleProjectUpdate);
      systemWebSocket.off("project_updated", handleProjectUpdate);
      systemWebSocket.off("user_updated", handleUserUpdate);
      systemWebSocket.off("user_status_changed", handleUserUpdate);
      systemWebSocket.off("notification_new", handleNotification);
    };
  }, [handleProposalUpdate, handleProjectUpdate, handleUserUpdate, handleNotification]);
}
