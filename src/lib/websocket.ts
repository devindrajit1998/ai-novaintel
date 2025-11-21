import { apiClient } from "./api";
import { ChatMessage } from "./api";

export type WebSocketMessageType = "message" | "typing" | "read_receipt" | "connection";

export interface WebSocketMessage {
  type: WebSocketMessageType;
  message?: ChatMessage;
  conversation_id?: number;
  user_id?: number;
  user_name?: string;
  is_typing?: boolean;
  status?: string;
}

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private userId: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, Set<(data: WebSocketMessage) => void>> = new Map();
  private isConnecting = false;

  connect(userId: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
        resolve();
        return;
      }

      this.userId = userId;
      this.isConnecting = true;

      const token = localStorage.getItem("access_token");
      if (!token) {
        reject(new Error("No access token found"));
        return;
      }

      const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const wsUrl = apiUrl.replace("http://", "ws://").replace("https://", "wss://") + `/chat/ws/${userId}?token=${token}`;
      
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log("WebSocket connected");
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error("Error parsing WebSocket message:", error);
          }
        };

        this.ws.onerror = (error) => {
          console.error("WebSocket error:", error);
          this.isConnecting = false;
          reject(error);
        };

        this.ws.onclose = () => {
          console.log("WebSocket disconnected");
          this.isConnecting = false;
          this.ws = null;
          
          // Attempt to reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts && this.userId) {
            this.reconnectAttempts++;
            setTimeout(() => {
              this.connect(this.userId!).catch(console.error);
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
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.userId = null;
    this.reconnectAttempts = 0;
  }

  sendMessage(conversationId: number, content: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "message",
        conversation_id: conversationId,
        content: content
      }));
    } else {
      console.error("WebSocket is not connected");
    }
  }

  sendTyping(conversationId: number, isTyping: boolean): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "typing",
        conversation_id: conversationId,
        is_typing: isTyping
      }));
    }
  }

  sendReadReceipt(conversationId: number): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "read_receipt",
        conversation_id: conversationId
      }));
    }
  }

  on(event: string, handler: (data: WebSocketMessage) => void): void {
    if (!this.messageHandlers.has(event)) {
      this.messageHandlers.set(event, new Set());
    }
    this.messageHandlers.get(event)!.add(handler);
  }

  off(event: string, handler: (data: WebSocketMessage) => void): void {
    const handlers = this.messageHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  private handleMessage(data: WebSocketMessage): void {
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

export const chatWebSocket = new ChatWebSocket();

