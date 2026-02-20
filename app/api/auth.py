from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from datetime import datetime, timedelta, date
from typing import Optional
import os
import bcrypt
import random
import json
import urllib.request
import urllib.error
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.models.user import User, OTPRecord, YouTubeChannelData

router = APIRouter()
security = HTTPBearer()

# Get the Google Client ID from environment variable, fallback to dummy
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com")

# The secret key to sign your custom JWTs
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key")
ALGORITHM = "HS256"

class GoogleAuthRequest(BaseModel):
    token: str

class LinkYoutubeRequest(BaseModel):
    app_token: str
    google_access_token: str

class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    gender: Optional[str] = None
    dob: Optional[date] = None
    auth_provider: str = "manual"
    profile_picture: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp_code: str

class ResendOTPRequest(BaseModel):
    email: str

def verify_password(plain_password: str, hashed_password: str):
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_password_hash(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(user: User):
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    app_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {
        "access_token": app_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_picture": getattr(user, "profile_picture", None),
            "youtube_channel_data": user.youtube_channel_data.dict() if getattr(user, "youtube_channel_data", None) else None,
            "gender": user.gender,
            "dob": user.dob,
            "auth_provider": user.auth_provider,
            "analyzed_videos": user.analyzed_videos,
        }
    }

async def generate_and_send_otp(email: str):
    # delete old otps for this email to avoid clutter
    await OTPRecord.find(OTPRecord.email == email).delete()
    
    otp_code = str(random.randint(100000, 999999))
    expires = datetime.utcnow() + timedelta(minutes=10)
    
    new_otp = OTPRecord(email=email, otp_code=otp_code, purpose="verification", expires_at=expires)
    await new_otp.insert()
    
    # Get Email Configuration
    sender_email = os.getenv("SMTP_USERNAME")
    sender_password = os.getenv("SMTP_PASSWORD")
    
    if sender_email and sender_password:
        try:
            # Setup the MIME
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = email
            message["Subject"] = "Your Verification OTP Code"
            
            # The body of the email
            body = f"Hello,\n\nYour Verification OTP code is: {otp_code}\n\nIt will expire in 10 minutes.\n\nThank you!"
            message.attach(MIMEText(body, "plain"))
            
            # Connect to SMTP server (assuming Gmail for general use)
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, email, text)
            server.quit()
        except Exception as e:
            print(f"Failed to send email via SMTP: {str(e)}")
            # Fallback to mock block in case of network/auth error during testing
            print(f"\n\n{'='*50}\nMOCK EMAIL (Failed SMTP): To {email}\nSubject: Your Verification OTP\nBody: Your OTP code is {otp_code}. It will expire in 10 minutes.\n{'='*50}\n\n")
    else:
        # Mock sending email when config is not set
        print(f"\n\n{'='*50}\nMOCK EMAIL: To {email}\nSubject: Your Verification OTP\nBody: Your OTP code is {otp_code}. It will expire in 10 minutes.\n{'='*50}\n\n")

@router.post("/auth/register")
async def register_user(request: RegisterRequest):
    hashed_pw = get_password_hash(request.password)
    existing_user = await User.find_one(User.email == request.email)
    
    if existing_user:
        # If they previously tried Google login but missing fields, just update their account!
        if existing_user.auth_provider == "google" and not existing_user.hashed_password:
            existing_user.first_name = request.first_name
            existing_user.last_name = request.last_name
            existing_user.hashed_password = hashed_pw
            existing_user.gender = request.gender
            existing_user.dob = request.dob
            if request.profile_picture:
                existing_user.profile_picture = request.profile_picture
            await existing_user.replace()
            return create_access_token(existing_user)
        else:
            raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_user = User(
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        hashed_password=hashed_pw,
        gender=request.gender,
        dob=request.dob,
        auth_provider=request.auth_provider,
        profile_picture=request.profile_picture,
        is_email_verified=True if request.auth_provider == "google" else False
    )
    
    await new_user.insert()
    if not new_user.is_email_verified:
        await generate_and_send_otp(new_user.email)
        return {"requires_otp": True, "message": "Please verify your email. OTP sent.", "email": new_user.email}
        
    return create_access_token(new_user)

@router.post("/auth/login")
async def login_user(request: LoginRequest):
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.hashed_password or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_email_verified:
        await generate_and_send_otp(user.email)
        return {"requires_otp": True, "message": "Please verify your email. OTP sent.", "email": user.email}
        
    return create_access_token(user)

@router.post("/auth/verify-otp")
async def verify_otp(request: VerifyOTPRequest):
    otp_record = await OTPRecord.find_one(OTPRecord.email == request.email, OTPRecord.otp_code == request.otp_code)
    
    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    if otp_record.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP has expired")
        
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_email_verified = True
    await user.replace()
    
    await otp_record.delete()
    
    return create_access_token(user)

@router.post("/auth/resend-otp")
async def resend_otp(request: ResendOTPRequest):
    user = await User.find_one(User.email == request.email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email is already verified")
        
    await generate_and_send_otp(user.email)
    return {"message": "OTP sent out successfully"}

@router.post("/auth/google")
async def verify_google_token(request: GoogleAuthRequest):
    try:
        # 1. Verify the Google ID Token
        idinfo = id_token.verify_oauth2_token(
            request.token, requests.Request(), GOOGLE_CLIENT_ID
        )

        email = idinfo.get("email")
        
        # 2. Check if user exists in the database
        user = await User.find_one(User.email == email)
        
        if not user:
            # Tell frontend this user needs to sign up (incomplete profile)
            raise HTTPException(status_code=404, detail="User not found. Please complete sign up.")

        # Update profile picture if missing, or verify email since google verified it
        changed = False
        google_picture = idinfo.get("picture")
        if google_picture and not user.profile_picture:
            user.profile_picture = google_picture
            changed = True
            
        if not user.is_email_verified:
            user.is_email_verified = True
            changed = True
            
        if changed:
            await user.replace()

        # 3. Generate your App's Custom JWT Token
        return create_access_token(user)

    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google Token: {str(e)}")

@router.get("/auth/me")
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        # Return exact same structure as login to easily refresh frontend state
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "profile_picture": getattr(user, "profile_picture", None),
            "youtube_channel_data": user.youtube_channel_data.dict() if getattr(user, "youtube_channel_data", None) else None,
            "gender": user.gender,
            "dob": user.dob,
            "auth_provider": user.auth_provider,
            "analyzed_videos": user.analyzed_videos,
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.post("/auth/link-youtube")
async def link_youtube(request: LinkYoutubeRequest):
    try:
        # 1. Decode our app token to find the user
        payload = jwt.decode(request.app_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid application token")
            
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in system")
            
        # 2. Fetch YouTube Data using Google Access Token
        import ssl
        # This fixes a common MacOS issue where Python doesn't have local SSL certs installed
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        req = urllib.request.Request(
            "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true"
        )
        req.add_header('Authorization', f'Bearer {request.google_access_token}')
        req.add_header('Accept', 'application/json')
        
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                result = json.loads(response.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise HTTPException(status_code=400, detail=f"Failed to fetch YouTube data: {error_body}")
        except urllib.error.URLError as e:
            raise HTTPException(status_code=400, detail=f"Network Error reaching YouTube: {str(e.reason)}")
            
        items = result.get('items', [])
        if not items:
            raise HTTPException(status_code=404, detail="No YouTube channel found for this Google Account")
            
        channel = items[0]
        snippet = channel.get('snippet', {})
        statistics = channel.get('statistics', {})
        
        # 3. Create the YouTubeChannelData object
        def safe_int(val):
            if not val:
                return 0
            try:
                return int(val)
            except (ValueError, TypeError):
                return 0

        thumbnails = snippet.get('thumbnails') or {}
        default_thumb = thumbnails.get('default') or {}
        
        yt_data = YouTubeChannelData(
            channel_id=channel.get('id', ""),
            title=snippet.get('title', ""),
            description=snippet.get('description', ""),
            subscriber_count=safe_int(statistics.get('subscriberCount')),
            video_count=safe_int(statistics.get('videoCount')),
            view_count=safe_int(statistics.get('viewCount')),
            thumbnail_url=default_thumb.get('url', "")
        )
        
        # 4. Save to MongoDB
        user.youtube_channel_data = yt_data
        await user.replace()
        
        # 5. Return updated token so frontend can display the new data instantly!
        return create_access_token(user)
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Unexpected error: {str(e)}")
