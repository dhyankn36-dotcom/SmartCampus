
from dotenv import load_dotenv

load_dotenv()

import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Complaint, User
from schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
)

# --------------------------------------------------
# SECURITY CONFIGURATION
# --------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing. Check backend/.env.")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Create missing tables only. Existing tables and rows are preserved.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartCampus Complaint Management System",
    description="API for campus complaints and grievances",
    version="2.0.0",
)

# Uploaded images are stored locally in backend/uploads.
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEPARTMENTS = {
    "Infrastructure": "Maintenance Department",
    "Wi-Fi": "IT Department",
    "Cleanliness": "Housekeeping Department",
    "Transport": "Transport Department",
}

ALLOWED_STATUSES = {
    "Submitted",
    "In Progress",
    "Resolved",
    "Rejected",
}


# --------------------------------------------------
# AUTHENTICATION HELPERS
# --------------------------------------------------

def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired login token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )
        user_id = int(payload["sub"])
    except (
        jwt.InvalidTokenError,
        KeyError,
        TypeError,
        ValueError,
    ):
        raise unauthorized

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise unauthorized

    return user


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return current_user


# --------------------------------------------------
# GENERAL ENDPOINTS
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Welcome to SmartCampus Complaint Management API"
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    user = User(
        name=user_data.name.strip(),
        email=str(user_data.email).lower(),
        hashed_password=password_hash.hash(user_data.password),
        role="student",
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create your account.",
        )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.post(
    "/api/auth/login",
    response_model=TokenResponse,
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    email = str(login_data.email).lower()

    user = db.query(User).filter(User.email == email).first()

    if (
        user is None
        or not password_hash.verify(
            login_data.password,
            user.hashed_password,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": create_access_token(user),
        "token_type": "bearer",
        "user": user,
    }


# --------------------------------------------------
# CURRENT USER PROFILE
# --------------------------------------------------

@app.get(
    "/api/auth/me",
    response_model=UserResponse,
)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


# --------------------------------------------------
# CREATE COMPLAINT
# --------------------------------------------------

@app.post(
    "/api/complaints",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_complaint(
    complaint_data: ComplaintCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = complaint_data.category.strip()

    if category not in DEPARTMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid complaint category.",
        )

    complaint = Complaint(
        ticket_id="PENDING",
        title=complaint_data.title.strip(),
        description=complaint_data.description.strip(),
        category=category,
        department=DEPARTMENTS[category],
        status="Submitted",
        user_id=current_user.id,
    )

    try:
        db.add(complaint)
        db.flush()

        complaint.ticket_id = (
            f"CMP-{datetime.now().year}-{complaint.id:03d}"
        )

        db.commit()
        db.refresh(complaint)

        return complaint

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create complaint.",
        )


# --------------------------------------------------
# LIST COMPLAINTS
# Students see their own. Admins can see all.
# --------------------------------------------------

@app.get(
    "/api/complaints",
    response_model=list[ComplaintResponse],
)
def list_complaints(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    if current_user.role != "admin":
        query = query.filter(
            Complaint.user_id == current_user.id
        )

    return query.order_by(Complaint.id.desc()).all()


# --------------------------------------------------
# VIEW A SINGLE COMPLAINT
# --------------------------------------------------

@app.get(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse,
)
def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint).filter(
        Complaint.id == complaint_id
    )

    if current_user.role != "admin":
        query = query.filter(
            Complaint.user_id == current_user.id
        )

    complaint = query.first()

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    return complaint


# --------------------------------------------------
# UPDATE COMPLAINT STATUS
# Only admins can update status.
# --------------------------------------------------

@app.patch("/api/complaints/{complaint_id}/status")
def update_complaint_status(
    complaint_id: int,
    update_data: ComplaintStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if update_data.status not in ALLOWED_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid status. Choose Submitted, In Progress, "
                "Resolved, or Rejected."
            ),
        )

    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    complaint.status = update_data.status

    try:
        db.commit()
        db.refresh(complaint)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update complaint status.",
        )

    return {
        "message": "Complaint status updated successfully.",
        "ticket_id": complaint.ticket_id,
        "status": complaint.status,
    }


# --------------------------------------------------
# UPLOAD COMPLAINT IMAGE
# Complaint owner or administrator only.
# --------------------------------------------------

@app.post("/api/complaints/{complaint_id}/image")
async def upload_complaint_image(
    complaint_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = db.query(Complaint).filter(
        Complaint.id == complaint_id
    ).first()

    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complaint not found.",
        )

    if current_user.role != "admin" and complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only upload images to your own complaints.",
        )

    extension = ALLOWED_IMAGE_TYPES.get(file.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image type. Upload a JPG, PNG, or WEBP image.",
        )

    contents = await file.read(MAX_IMAGE_SIZE + 1)
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be 5 MB or smaller.",
        )

    # Check the file signature rather than trusting only the browser MIME type.
    valid_signature = (
        (extension == ".jpg" and contents.startswith(bytes.fromhex("FFD8FF")))
        or (extension == ".png" and contents.startswith(bytes.fromhex("89504E470D0A1A0A")))
        or (extension == ".webp" and len(contents) >= 12
            and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP")
    )
    if not valid_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The file contents do not match a supported image type.",
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_DIR / filename

    try:
        destination.write_bytes(contents)

        # Remove the old uploaded image after the new one has been saved.
        old_image_url = complaint.image_url
        complaint.image_url = f"/uploads/{filename}"
        db.commit()
        db.refresh(complaint)

        if old_image_url and old_image_url.startswith("/uploads/"):
            old_path = UPLOAD_DIR / Path(old_image_url).name
            if old_path.is_file() and old_path.name != filename:
                old_path.unlink(missing_ok=True)

        return {
            "message": "Image uploaded successfully.",
            "ticket_id": complaint.ticket_id,
            "image_url": complaint.image_url,
        }

    except HTTPException:
        raise
    except Exception:
        db.rollback()
        if destination.exists():
            destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the complaint image.",
        )
    finally:
        await file.close()
