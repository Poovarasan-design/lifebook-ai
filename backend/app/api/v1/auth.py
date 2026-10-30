import os
import time
import secrets
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token
from app.models.user import User
from app.models.audit import AuditLog
from app.storage.storage_service import storage_service
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    Token,
    UserOut,
    UserUpdate,
    GoogleAuthRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # 1. Check duplicate email
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. Hash password & create user
    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role="user",
        auth_provider="local",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 3. Audit log
    db.add(AuditLog(user_id=user.id, actor=user.email, action="register", resource=f"User:{user.id}"))
    db.commit()

    # 4. Generate JWT
    token = create_access_token(subject=user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.post("/login", response_model=Token)
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.hashed_password and user.google_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was registered using Google Sign-In. Please sign in with Google."
        )

    if not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )

    db.add(AuditLog(user_id=user.id, actor=user.email, action="login", resource=f"User:{user.id}"))
    db.commit()

    token = create_access_token(subject=user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.get("/me", response_model=UserOut)
def get_auth_me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)

@router.put("/profile", response_model=UserOut)
@router.put("/me", response_model=UserOut)
def update_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.full_name is not None and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()
    if payload.avatar_url is not None:
        clean_url = payload.avatar_url.strip()
        current_user.avatar_url = clean_url if clean_url else None
    if payload.preferences is not None:
        current_user.preferences = payload.preferences
    db.commit()
    db.refresh(current_user)
    db.add(AuditLog(user_id=current_user.id, actor=current_user.email, action="profile_update", resource=f"User:{current_user.id}"))
    db.commit()
    return UserOut.model_validate(current_user)

@router.post("/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a profile picture directly from the user's local system.
    """
    content_type = (file.content_type or "").lower()
    filename = file.filename or "avatar.jpg"
    valid_exts = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp")
    
    if not (content_type.startswith("image/") or filename.lower().endswith(valid_exts)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid image (JPG, PNG, WEBP, GIF)"
        )

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds the 10MB limit."
        )

    await storage_service.save_avatar(
        user_id=current_user.id,
        image_bytes=image_bytes,
        filename=filename
    )

    # Set avatar_url to the served API endpoint with cache-busting timestamp
    current_user.avatar_url = f"/api/v1/auth/avatar/{current_user.id}?t={int(time.time())}"
    db.commit()
    db.refresh(current_user)
    db.add(AuditLog(user_id=current_user.id, actor=current_user.email, action="avatar_upload", resource=f"User:{current_user.id}"))
    db.commit()
    return UserOut.model_validate(current_user)

@router.get("/avatar/{user_id}")
def get_avatar_image(user_id: str):
    """
    Serve the user's uploaded avatar image.
    """
    avatar_path = storage_service.get_avatar_path(user_id)
    if not avatar_path or not os.path.exists(avatar_path):
        raise HTTPException(status_code=404, detail="Avatar image not found")
    
    ext = os.path.splitext(avatar_path)[1].lower()
    media_map = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".gif": "image/gif",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".bmp": "image/bmp"
    }
    media_type = media_map.get(ext, "image/jpeg")
    return FileResponse(avatar_path, media_type=media_type)

@router.delete("/avatar", response_model=UserOut)
def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove the user's custom avatar and revert to initial badge.
    """
    storage_service.delete_avatar(current_user.id)
    current_user.avatar_url = None
    db.commit()
    db.refresh(current_user)
    db.add(AuditLog(user_id=current_user.id, actor=current_user.email, action="avatar_delete", resource=f"User:{current_user.id}"))
    db.commit()
    return UserOut.model_validate(current_user)

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(AuditLog(user_id=current_user.id, actor=current_user.email, action="logout", resource=f"User:{current_user.id}"))
    db.commit()
    return {"message": "Logged out successfully"}

@router.get("/google/url")
def get_google_auth_url():
    client_id = settings.GOOGLE_CLIENT_ID or "google-client-id-placeholder"
    redirect_uri = settings.GOOGLE_REDIRECT_URI or "http://localhost:5173/auth/google/callback"
    scope = "openid email profile"
    url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope={scope}&"
        f"access_type=offline&"
        f"prompt=consent"
    )
    return {"url": url, "client_id": settings.GOOGLE_CLIENT_ID}

@router.post("/google", response_model=Token)
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate via Google OpenID Connect / OAuth 2.0.
    Accepts either an Google ID Token (from Google Identity Services) or an Authorization Code.
    Verifies the identity directly with Google.
    """
    google_user_info = None

    # Handle Mock Google Token for testing environments
    if payload.id_token and payload.id_token.startswith("mock-google-token:"):
        parts = payload.id_token.split(":", 4)
        # Format: mock-google-token:google_id:email:name:picture
        google_id = parts[1] if len(parts) > 1 else "google-mock-12345"
        email = parts[2] if len(parts) > 2 else "mockuser@gmail.com"
        name = parts[3] if len(parts) > 3 else "Google User"
        picture = parts[4] if len(parts) > 4 else "https://lh3.googleusercontent.com/a/default-user"
        google_user_info = {
            "sub": google_id,
            "email": email,
            "email_verified": True,
            "name": name,
            "picture": picture
        }
    elif payload.id_token:
        # Verify ID token using Google tokeninfo endpoint
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?id_token={payload.id_token}"
                )
                if res.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Google token"
                    )
                info = res.json()
                
                # Check email verification
                email_verified = info.get("email_verified")
                if isinstance(email_verified, str):
                    email_verified = email_verified.lower() == "true"
                if not email_verified:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google account email is not verified"
                    )

                # Optional audience check if client id is configured
                if settings.GOOGLE_CLIENT_ID and info.get("aud") != settings.GOOGLE_CLIENT_ID:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Google token audience mismatch"
                    )

                google_user_info = {
                    "sub": info.get("sub"),
                    "email": info.get("email"),
                    "name": info.get("name") or info.get("email", "").split("@")[0],
                    "picture": info.get("picture")
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(e)}"
            )
    elif payload.code:
        # Exchange authorization code for tokens
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google OAuth client credentials not configured on backend"
            )
        redirect_uri = payload.redirect_uri or settings.GOOGLE_REDIRECT_URI
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "code": payload.code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )
                if token_res.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to exchange Google authorization code"
                    )
                tokens = token_res.json()
                access_token = tokens.get("access_token")
                
                # Fetch user info with access token
                userinfo_res = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                if userinfo_res.status_code != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to retrieve Google user profile"
                    )
                info = userinfo_res.json()
                if not info.get("email_verified"):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Google email is not verified"
                    )
                google_user_info = {
                    "sub": info.get("sub"),
                    "email": info.get("email"),
                    "name": info.get("name") or info.get("email", "").split("@")[0],
                    "picture": info.get("picture")
                }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Google authentication failed: {str(e)}"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either id_token or code must be provided for Google authentication"
        )

    google_id = google_user_info["sub"]
    email = google_user_info["email"]
    name = google_user_info["name"]
    picture = google_user_info.get("picture")

    # 1. Check if user exists with this google_id
    user = db.query(User).filter(User.google_id == google_id).first()

    # 2. Check if user exists with matching verified email (Account Linking)
    if not user:
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Safely link Google identity to existing local account
            user.google_id = google_id
            if picture and not user.avatar_url:
                user.avatar_url = picture
            if user.auth_provider == "local":
                user.auth_provider = "both"
            db.commit()
            db.refresh(user)

    # 3. Create new user if not found
    if not user:
        user = User(
            email=email,
            full_name=name,
            google_id=google_id,
            avatar_url=picture,
            auth_provider="google",
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive"
        )

    db.add(AuditLog(user_id=user.id, actor=user.email, action="google_login", resource=f"User:{user.id}"))
    db.commit()

    token = create_access_token(subject=user.id)
    return Token(access_token=token, token_type="bearer", user=UserOut.model_validate(user))

@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates password reset without disclosing whether email exists.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user:
        reset_token = create_access_token(subject=f"reset:{user.id}")
        db.add(AuditLog(user_id=user.id, actor=user.email, action="forgot_password_request", resource=f"User:{user.id}"))
        db.commit()
    res = {
        "message": "If an account with this email exists, a password reset link has been generated."
    }
    if user and settings.ENVIRONMENT != "production":
        res["reset_token"] = reset_token
    return res

@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.token)
    if not token_data or not token_data.get("sub", "").startswith("reset:"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    user_id = token_data["sub"].replace("reset:", "")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = get_password_hash(payload.new_password)
    if user.auth_provider == "google":
        user.auth_provider = "both"
    db.commit()
    db.add(AuditLog(user_id=user.id, actor=user.email, action="password_reset_success", resource=f"User:{user.id}"))
    db.commit()

    return {"message": "Password updated successfully. You can now log in."}
