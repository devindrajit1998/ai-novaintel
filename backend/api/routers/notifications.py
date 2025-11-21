"""
Notifications API for job status updates and system notifications.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime
from db.database import get_db
from models.user import User
from models.notification import Notification
from utils.dependencies import get_current_user
from utils.timezone import now_ist
from api.schemas.notification import NotificationResponse, NotificationCreate

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 20
):
    """Get notifications for current user."""
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(desc(Notification.created_at)).limit(limit).all()
    
    # Convert to response format
    result = []
    for notif in notifications:
        notif_dict = {
            "id": notif.id,
            "user_id": notif.user_id,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "status": notif.status,
            "is_read": notif.is_read,
            "read_at": notif.read_at,
            "metadata": notif.metadata_,  # Use metadata_ attribute directly
            "created_at": notif.created_at,
            "updated_at": notif.updated_at,
        }
        result.append(NotificationResponse(**notif_dict))
    
    return result

@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notification.is_read = True
        notification.read_at = now_ist()
        db.commit()
        
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for current user."""
    try:
        db.query(Notification).filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        ).update({"is_read": True, "read_at": now_ist()})
        db.commit()
        
        return {"message": "All notifications marked as read"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )

@router.post("/notifications", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification (internal use)."""
    try:
        notification = Notification(
            user_id=current_user.id,
            type=notification_data.type,
            title=notification_data.title,
            message=notification_data.message,
            status=notification_data.status or "pending",
            metadata_=notification_data.metadata  # Use metadata_ attribute directly
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        return NotificationResponse(
            id=notification.id,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            status=notification.status,
            is_read=notification.is_read,
            read_at=notification.read_at,
            metadata=notification.metadata_,  # Use metadata_ attribute directly
            created_at=notification.created_at,
            updated_at=notification.updated_at,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

