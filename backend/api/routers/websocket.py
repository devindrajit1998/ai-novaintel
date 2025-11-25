"""
WebSocket router for system-wide real-time updates.
Handles proposals, projects, users, notifications, etc.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
import json

from db.database import SessionLocal
from models.user import User
from utils.websocket_manager import global_ws_manager
from utils.security import decode_token

router = APIRouter(prefix="/ws", tags=["websocket"])


def get_user_from_token(token: str, db: Session) -> User:
    """Extract user from JWT token"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user_email = payload.get("sub") or payload.get("email")
    if not user_email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    
    user = db.query(User).filter(User.email == user_email).first()
    if not user or not user.is_active or not user.email_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    
    return user


@router.websocket("/system/{user_id}")
async def system_websocket_endpoint(websocket: WebSocket, user_id: int, token: str = None):
    """WebSocket endpoint for system-wide real-time updates"""
    db = SessionLocal()
    
    try:
        # Get token from query params
        if not token:
            token = websocket.query_params.get("token")
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Verify user
        user = get_user_from_token(token, db)
        if user.id != user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
        # Connect to global manager (this accepts the connection)
        await global_ws_manager.connect(websocket, user.id)
        
        # Small delay to ensure connection is fully established
        import asyncio
        await asyncio.sleep(0.1)
        
        # Send connection confirmation (only if connection is still valid)
        try:
            if websocket.client_state.name == "CONNECTED":
                await global_ws_manager.send_to_user(user.id, {
                    "type": "connection",
                    "status": "connected",
                    "user_id": user.id,
                    "role": user.role
                })
        except Exception as e:
            # Silently handle connection confirmation errors
            pass
        
        # Handle incoming messages (for subscriptions, etc.)
        while True:
            try:
                # Check connection state before receiving
                if websocket.client_state.name != "CONNECTED":
                    break
                
                data = await websocket.receive_text()
                message_data = json.loads(data)
                message_type = message_data.get("type")
                
                if message_type == "subscribe":
                    # Subscribe to specific update types
                    subscription_type = message_data.get("subscription_type", "all")
                    global_ws_manager.subscribe(user.id, subscription_type)
                    # Only send if connection is still valid
                    if websocket.client_state.name == "CONNECTED":
                        await global_ws_manager.send_to_user(user.id, {
                            "type": "subscription",
                            "status": "subscribed",
                            "subscription_type": subscription_type
                        })
                
                elif message_type == "unsubscribe":
                    # Unsubscribe from specific update types
                    subscription_type = message_data.get("subscription_type", "all")
                    global_ws_manager.unsubscribe(user.id, subscription_type)
                    # Only send if connection is still valid
                    if websocket.client_state.name == "CONNECTED":
                        await global_ws_manager.send_to_user(user.id, {
                            "type": "subscription",
                            "status": "unsubscribed",
                            "subscription_type": subscription_type
                        })
                
            except WebSocketDisconnect:
                # Client disconnected, break out of loop
                break
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_str = str(e).lower()
                # Only log non-connection errors to reduce spam
                if "not connected" not in error_str and "accept" not in error_str:
                    print(f"Error processing WebSocket message: {e}")
                # Check if connection is still open before continuing
                if not hasattr(websocket, 'client_state') or websocket.client_state.name == "DISCONNECTED":
                    break
                continue
                
    except WebSocketDisconnect:
        pass  # Already handled in while loop
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        try:
            global_ws_manager.disconnect(websocket, user.id)
        except:
            pass
        if db:
            try:
                db.close()
            except:
                pass

