import { ReactNode } from "react";
import { useSystemWebSocket } from "@/hooks/useSystemWebSocket";

/**
 * Provider component that sets up system WebSocket listeners for real-time updates.
 * The WebSocket connection itself is handled in AuthContext when user logs in.
 */
export function SystemWebSocketProvider({ children }: { children: ReactNode }) {
  // Set up WebSocket listeners for real-time updates
  // This doesn't require auth context - it just sets up listeners
  useSystemWebSocket();
  
  return <>{children}</>;
}

