import { apiClient } from "./api";

export type SystemWebSocketMessageType = 
  | "connection" 
  | "proposal_updated" 
  | "proposal_submitted" 
  | "proposal_reviewed"
  | "project_created"
  | "project_updated"
  | "user_updated"
  | "user_status_changed"
  | "notification_new"
  | "subscription";

export interface SystemWebSocketMessage {
  type: SystemWebSocketMessageType;
  proposal?: any;
  project?: any;
  user?: any;
  notification?: any;
  status?: string;
  user_id?: number;
  role?: string;
  subscription_type?: string;
  [key: string]: any;
}

export class SystemWebSocket {
  private ws: WebSocket | null = null;
  private userId: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, Set<(data: SystemWebSocketMessage) => void>> = new Map();
  private isConnecting = false;

  connect(userId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      // If already connected or connecting, resolve immediately
      if (this.isConnecting) {
        resolve();
        return;
      }
      
      if (this.ws) {
        if (this.ws.readyState === WebSocket.OPEN) {
          resolve();
          return;
        }
        // If WebSocket exists but not open, close it first
        try {
          this.ws.close();
        } catch (e) {
          // Ignore errors when closing
        }
        this.ws = null;
      }

      this.userId = userId;
      this.isConnecting = true;

      const token = localStorage.getItem("access_token");
      if (!token) {
        reject(new Error("No access token found"));
        return;
      }

      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const wsUrl = apiUrl.replace("http://", "ws://").replace("https://", "wss://") + `/ws/system/${userId}?token=${token}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("System WebSocket connected");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: SystemWebSocketMessage = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("System WebSocket error:", error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log("System WebSocket disconnected", event.code, event.reason);
          this.isConnecting = false;
          this.ws = null;
          
          // Only attempt to reconnect if it wasn't a manual disconnect (code 1000)
          // and we haven't exceeded max attempts
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts && this.userId) {
            this.reconnectAttempts++;
            setTimeout(() => {
              // Check if we still have a user ID before reconnecting
              if (this.userId && localStorage.getItem("access_token")) {
                this.connect(this.userId!).catch(console.error);
              }
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  disconnect(): void {
    // Prevent reconnection attempts
    this.userId = null;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    
    if (this.ws) {
      try {
        // Close with code 1000 (normal closure) to prevent auto-reconnect
        this.ws.close(1000, "Manual disconnect");
      } catch (e) {
        // Ignore errors
      }
      this.ws = null;
    }
    this.isConnecting = false;
  }

  subscribe(subscriptionType: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "subscribe",
        subscription_type: subscriptionType
      }));
    }
  }

  unsubscribe(subscriptionType: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "unsubscribe",
        subscription_type: subscriptionType
      }));
    }
  }

  on(event: string, handler: (data: SystemWebSocketMessage) => void): void {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event)!.add(handler);
  }

  off(event: string, handler: (data: SystemWebSocketMessage) => void): void {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  private handleMessage(data: SystemWebSocketMessage): void {
    // Call all handlers for this event type
    const handlers = this.messageHandlers.get(data.type);
    if (handlers) {
      handlers.forEach(handler => handler(data));
    }

    // Also call "all" handlers
    const allHandlers = this.messageHandlers.get("all");
    if (allHandlers) {
      allHandlers.forEach(handler => handler(data));
    }
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

export const systemWebSocket = new SystemWebSocket();

