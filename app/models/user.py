from datetime import datetime, date
from typing import Optional, List
from beanie import Document
from pydantic import BaseModel, Field
# Note: If you have `email-validator` installed, you can use `EmailStr` from pydantic instead of `str` for email fields.

class YouTubeChannelData(BaseModel):
    """Stores minimal YouTube channel data fetched if user links their account."""
    channel_id: str
    title: str
    description: Optional[str] = None
    subscriber_count: Optional[int] = 0
    video_count: Optional[int] = 0
    view_count: Optional[int] = 0
    thumbnail_url: Optional[str] = None

class User(Document):
    """Main User Model for authentication and profile data."""
    first_name: str
    last_name: str
    email: str  # Use EmailStr for auto-validation if email-validator is installed
    gender: Optional[str] = None
    dob: Optional[date] = None
    profile_picture: Optional[str] = None
    
    # Auth fields
    hashed_password: Optional[str] = None  # Will be None for Google OAuth users
    auth_provider: str = Field(default="manual", description="Can be 'manual' or 'google'")
    is_email_verified: bool = False
    
    # Custom User Data integration
    youtube_channel_data: Optional[YouTubeChannelData] = None
    analyzed_videos: List[str] = Field(default_factory=list, description="List of Video IDs the user has analyzed")
    
    # General Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users" # MongoDB collection name

class OTPRecord(Document):
    """Model for storing Email OTP codes temporarily for verification."""
    email: str
    otp_code: str
    purpose: str = Field(default="signup", description="E.g., signup, reset_password")
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "otps"
