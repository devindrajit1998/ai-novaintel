from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Dict, Set
from datetime import datetime
import json
import asyncio

from db.database import get_db
from models.user import User
from models.conversation import Conversation, ConversationParticipant, Message
from api.schemas.chat import (
    MessageCreate, MessageResponse, ConversationCreate,
    ConversationResponse, ConversationListResponse, WebSocketMessage
)
from utils.dependencies import get_current_user
from utils.security import decode_token

router = APIRouter(prefix="/chat", tags=["chat"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # Map of user_id -> Set of WebSocket connections
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        # Map of conversation_id -> Set of user_ids
        self.conversation_users: Dict[int, Set[int]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
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

    async def send_to_conversation(self, message: dict, conversation_id: int, exclude_user_id: int = None):
        """Send message to all users in a conversation"""
        if conversation_id in self.conversation_users:
            for user_id in self.conversation_users[conversation_id]:
                if user_id != exclude_user_id:
                    await self.send_personal_message(message, user_id)

    def add_user_to_conversation(self, user_id: int, conversation_id: int):
        if conversation_id not in self.conversation_users:
            self.conversation_users[conversation_id] = set()
        self.conversation_users[conversation_id].add(user_id)

    def remove_user_from_conversation(self, user_id: int, conversation_id: int):
        if conversation_id in self.conversation_users:
            self.conversation_users[conversation_id].discard(user_id)


manager = ConnectionManager()


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


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = None):
    """WebSocket endpoint for real-time messaging"""
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        # Get token from query params or headers
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
        
        await manager.connect(websocket, user.id)
        
        # Small delay to ensure connection is fully established
        import asyncio
        await asyncio.sleep(0.1)
        
        # Get user's conversations and add to manager
        conversations = db.query(ConversationParticipant).filter(
            ConversationParticipant.user_id == user.id
        ).all()
        for participant in conversations:
            manager.add_user_to_conversation(user.id, participant.conversation_id)
        
        # Send connection confirmation (only if connection is still valid)
        try:
            if websocket.client_state.name == "CONNECTED":
                await manager.send_personal_message({
                    "type": "connection",
                    "status": "connected",
                    "user_id": user.id
                }, user.id)
        except Exception:
            # Silently handle connection confirmation errors
            pass
        
        while True:
            try:
                # Check connection state before receiving
                if not hasattr(websocket, 'client_state') or websocket.client_state.name != "CONNECTED":
                    break
                
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    message_type = message_data.get("type")
                    
                    if message_type == "message":
                        # Handle new message
                        conversation_id = message_data.get("conversation_id")
                        content = message_data.get("content")
                        
                        if not conversation_id or not content:
                            continue
                        
                        # Verify user is participant
                        participant = db.query(ConversationParticipant).filter(
                            and_(
                                ConversationParticipant.conversation_id == conversation_id,
                                ConversationParticipant.user_id == user.id
                            )
                        ).first()
                        
                        if not participant:
                            continue
                        
                        # Create message
                        new_message = Message(
                            conversation_id=conversation_id,
                            sender_id=user.id,
                            content=content
                        )
                        db.add(new_message)
                        db.commit()
                        db.refresh(new_message)
                        
                        # Update conversation updated_at
                        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
                        if conversation:
                            from utils.timezone import now_utc_from_ist
                            conversation.updated_at = now_utc_from_ist()
                            db.commit()
                        
                        # Prepare message response
                        message_response = {
                            "type": "message",
                            "message": {
                                "id": new_message.id,
                                "conversation_id": new_message.conversation_id,
                                "sender_id": new_message.sender_id,
                                "sender_name": user.full_name,
                                "sender_email": user.email,
                                "content": new_message.content,
                                "is_read": False,
                                "created_at": new_message.created_at.isoformat(),
                                "updated_at": new_message.updated_at.isoformat()
                            }
                        }
                        
                        # Send to all participants in conversation (only if connection is still valid)
                        if websocket.client_state.name == "CONNECTED":
                            await manager.send_to_conversation(message_response, conversation_id, exclude_user_id=user.id)
                            
                            # Send confirmation back to sender
                            await manager.send_personal_message(message_response, user.id)
                    
                    elif message_type == "typing":
                        # Broadcast typing indicator (only if connection is still valid)
                        conversation_id = message_data.get("conversation_id")
                        if conversation_id and websocket.client_state.name == "CONNECTED":
                            typing_msg = {
                                "type": "typing",
                                "conversation_id": conversation_id,
                                "user_id": user.id,
                                "user_name": user.full_name,
                                "is_typing": message_data.get("is_typing", True)
                            }
                            await manager.send_to_conversation(typing_msg, conversation_id, exclude_user_id=user.id)
                    
                    elif message_type == "read_receipt":
                        # Mark messages as read
                        conversation_id = message_data.get("conversation_id")
                        if conversation_id:
                            # Update last_read_at for participant
                            participant = db.query(ConversationParticipant).filter(
                                and_(
                                    ConversationParticipant.conversation_id == conversation_id,
                                    ConversationParticipant.user_id == user.id
                                )
                            ).first()
                            if participant:
                                from utils.timezone import now_utc_from_ist
                                participant.last_read_at = now_utc_from_ist()
                                db.commit()
                            
                            # Mark messages as read
                            db.query(Message).filter(
                                and_(
                                    Message.conversation_id == conversation_id,
                                    Message.sender_id != user.id,
                                    Message.is_read == False
                                )
                            ).update({"is_read": True})
                            db.commit()
                            
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
                # Client disconnected, break out of loop
                break
            except Exception as e:
                print(f"WebSocket receive error: {e}")
                break
                
    except WebSocketDisconnect:
        pass  # Already handled in while loop
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Clean up connection
        try:
            manager.disconnect(websocket, user.id)
        except:
            pass
        if db:
            try:
                db.close()
            except:
                pass


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new conversation"""
    # Add current user to participants
    participant_ids = list(set(conversation_data.participant_ids + [current_user.id]))
    
    if len(participant_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 participants required"
        )
    
    # Check if conversation already exists (for 1-on-1 chats)
    if len(participant_ids) == 2 and not conversation_data.name:
        # More reliable check: find conversations where both users are participants
        user1_id, user2_id = sorted(participant_ids)  # Sort for consistency
        
        # Find conversations where both users are participants (1-on-1 only)
        # Get all conversation IDs where user1 is a participant
        user1_conv_ids = [
            p.conversation_id for p in db.query(ConversationParticipant).filter(
                ConversationParticipant.user_id == user1_id
            ).all()
        ]
        
        # Get all conversation IDs where user2 is a participant
        user2_conv_ids = [
            p.conversation_id for p in db.query(ConversationParticipant).filter(
                ConversationParticipant.user_id == user2_id
            ).all()
        ]
        
        # Find common conversation IDs
        common_conv_ids = set(user1_conv_ids) & set(user2_conv_ids)
        
        if common_conv_ids:
            # Check each common conversation to see if it's a 1-on-1 with exactly these 2 users
            for conv_id in common_conv_ids:
                conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
                if conv and not conv.is_group:
                    # Check if this conversation has exactly these 2 participants
                    participants = db.query(ConversationParticipant).filter(
                        ConversationParticipant.conversation_id == conv_id
                    ).all()
                    participant_user_ids = [p.user_id for p in participants]
                    
                    if len(participant_user_ids) == 2 and set(participant_user_ids) == set(participant_ids):
                        # Return existing conversation
                        return {
                            "id": conv.id,
                            "name": conv.name,
                            "is_group": conv.is_group,
                            "created_at": conv.created_at,
                            "updated_at": conv.updated_at,
                            "participants": [
                                {
                                    "id": p.user_id,
                                    "name": db.query(User).filter(User.id == p.user_id).first().full_name,
                                    "email": db.query(User).filter(User.id == p.user_id).first().email
                                }
                                for p in participants
                            ],
                            "unread_count": 0
                        }
    
    # Create new conversation
    is_group = len(participant_ids) > 2 or conversation_data.name is not None
    conversation = Conversation(
        name=conversation_data.name,
        is_group=is_group
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    # Add participants
    for user_id in participant_ids:
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id
        )
        db.add(participant)
    
    db.commit()
    
    # Get participants with user info
    participants = db.query(ConversationParticipant).filter(
        ConversationParticipant.conversation_id == conversation.id
    ).all()
    
    return {
        "id": conversation.id,
        "name": conversation.name,
        "is_group": conversation.is_group,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "participants": [
            {
                "id": p.user_id,
                "name": db.query(User).filter(User.id == p.user_id).first().full_name,
                "email": db.query(User).filter(User.id == p.user_id).first().email
            }
            for p in participants
        ],
        "unread_count": 0
    }


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """Get all conversations for current user"""
    # Get user's conversations
    participants = db.query(ConversationParticipant).filter(
        ConversationParticipant.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    conversation_ids = [p.conversation_id for p in participants]
    conversations = db.query(Conversation).filter(
        Conversation.id.in_(conversation_ids)
    ).order_by(Conversation.updated_at.desc()).all()
    
    result = []
    for conv in conversations:
        # Get participants
        conv_participants = db.query(ConversationParticipant).filter(
            ConversationParticipant.conversation_id == conv.id
        ).all()
        
        # Get last message
        last_message = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.created_at.desc()).first()
        
        # Get unread count
        user_participant = next((p for p in conv_participants if p.user_id == current_user.id), None)
        unread_count = 0
        if user_participant:
            unread_count = db.query(Message).filter(
                and_(
                    Message.conversation_id == conv.id,
                    Message.sender_id != current_user.id,
                    Message.is_read == False,
                    or_(
                        user_participant.last_read_at == None,
                        Message.created_at > user_participant.last_read_at
                    )
                )
            ).count()
        
        last_msg_response = None
        if last_message:
            sender = db.query(User).filter(User.id == last_message.sender_id).first()
            last_msg_response = {
                "id": last_message.id,
                "conversation_id": last_message.conversation_id,
                "sender_id": last_message.sender_id,
                "sender_name": sender.full_name if sender else "Unknown",
                "sender_email": sender.email if sender else "",
                "content": last_message.content,
                "is_read": last_message.is_read,
                "created_at": last_message.created_at,
                "updated_at": last_message.updated_at
            }
        
        result.append({
            "id": conv.id,
            "name": conv.name,
            "is_group": conv.is_group,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "participants": [
                {
                    "id": p.user_id,
                    "name": db.query(User).filter(User.id == p.user_id).first().full_name,
                    "email": db.query(User).filter(User.id == p.user_id).first().email
                }
                for p in conv_participants
            ],
            "last_message": last_msg_response,
            "unread_count": unread_count
        })
    
    return {"conversations": result, "total": len(result)}


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Get messages for a conversation"""
    # Verify user is participant
    participant = db.query(ConversationParticipant).filter(
        and_(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == current_user.id
        )
    ).first()
    
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a participant in this conversation"
        )
    
    # Get messages
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.desc()).offset(skip).limit(limit).all()
    
    # Mark as read
    participant.last_read_at = datetime.utcnow()
    db.query(Message).filter(
        and_(
            Message.conversation_id == conversation_id,
            Message.sender_id != current_user.id,
            Message.is_read == False
        )
    ).update({"is_read": True})
    db.commit()
    
    # Format response
    result = []
    for msg in reversed(messages):  # Reverse to get chronological order
        sender = db.query(User).filter(User.id == msg.sender_id).first()
        result.append({
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "sender_id": msg.sender_id,
            "sender_name": sender.full_name if sender else "Unknown",
            "sender_email": sender.email if sender else "",
            "content": msg.content,
            "is_read": msg.is_read,
            "created_at": msg.created_at,
            "updated_at": msg.updated_at
        })
    
    return result


@router.get("/users", response_model=List[dict])
async def get_chat_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of users available for chat"""
    users = db.query(User).filter(
        and_(
            User.id != current_user.id,
            User.is_active == True,
            User.email_verified == True
        )
    ).all()
    
    return [
        {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role
        }
        for user in users
    ]

