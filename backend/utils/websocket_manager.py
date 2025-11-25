"""
Global WebSocket manager for system-wide real-time updates.
Handles connections and broadcasts for proposals, projects, users, etc.
"""
from typing import Dict, Set
from fastapi import WebSocket
import json


class GlobalWebSocketManager:
    """Manages all WebSocket connections for real-time system updates"""
    
    def __init__(self):
        # Map of user_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of subscription_type -> Set of user_ids
        # subscription_type: "proposals", "projects", "users", "notifications", "all"
        self.subscriptions: Dict[str, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        """Connect a user's WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)
        
        # Subscribe to all updates by default
        if "all" not in self.subscriptions:
            self.subscriptions["all"] = set()
        self.subscriptions["all"].add(user_id)

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Disconnect a user's WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        # Remove from all subscriptions
        for sub_type in self.subscriptions:
            self.subscriptions[sub_type].discard(user_id)

    async def send_to_user(self, user_id: int, message: dict):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in list(self.active_connections[user_id]):  # Use list to avoid modification during iteration
                try:
                    # Check if WebSocket is in a valid state before sending
                    if not hasattr(connection, 'client_state'):
                        disconnected.add(connection)
                        continue
                    
                    state_name = connection.client_state.name
                    if state_name == "DISCONNECTED":
                        disconnected.add(connection)
                        continue
                    
                    # Only send if connection is CONNECTED
                    if state_name != "CONNECTED":
                        continue
                    
                    await connection.send_json(message)
                except Exception as e:
                    error_str = str(e).lower()
                    # Silently handle expected connection errors
                    if "not connected" in error_str or "accept" in error_str or "disconnected" in error_str:
                        disconnected.add(connection)
                    else:
                        # Log unexpected errors
                        print(f"Error sending to user {user_id}: {e}")
                        disconnected.add(connection)
            
            # Clean up disconnected connections
            for conn in disconnected:
                self.active_connections[user_id].discard(conn)

    async def broadcast(self, message: dict, subscription_type: str = "all", exclude_user_id: int = None):
        """Broadcast message to all users subscribed to a type"""
        user_ids = self.subscriptions.get(subscription_type, set())
        if subscription_type != "all":
            # Also include users subscribed to "all"
            user_ids = user_ids | self.subscriptions.get("all", set())
        
        for user_id in user_ids:
            if user_id != exclude_user_id:
                await self.send_to_user(user_id, message)

    async def broadcast_to_role(self, message: dict, role: str, exclude_user_id: int = None):
        """Broadcast message to all users with a specific role"""
        # This will be used with user role information from database
        # For now, broadcast to all and let frontend filter
        await self.broadcast(message, "all", exclude_user_id)

    def subscribe(self, user_id: int, subscription_type: str):
        """Subscribe a user to a specific update type"""
        if subscription_type not in self.subscriptions:
            self.subscriptions[subscription_type] = set()
        self.subscriptions[subscription_type].add(user_id)

    def unsubscribe(self, user_id: int, subscription_type: str):
        """Unsubscribe a user from a specific update type"""
        if subscription_type in self.subscriptions:
            self.subscriptions[subscription_type].discard(user_id)


# Global instance
global_ws_manager = GlobalWebSocketManager()

