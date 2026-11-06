
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
from sqlalchemy import func
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
    FeedbackCreate,
    FeedbackResponse,
    FeedbackAnalytics,
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

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SmartCampus Complaint Management System",
    description="API for campus complaints, grievances and student feedback",
    version="3.0.0",
)

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
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

    valid_signature = (
        (extension == ".jpg" and contents.startswith(bytes.fromhex("FFD8FF")))
        or (extension == ".png" and contents.startswith(bytes.fromhex("89504E470D0A1A0A")))
        or (
            extension == ".webp"
            and len(contents) >= 12
            and contents[:4] == b"RIFF"
            and contents[8:12] == b"WEBP"
        )
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


# --------------------------------------------------
# STUDENT FEEDBACK
# Students can submit feedback once after resolution.
# --------------------------------------------------

@app.post("/api/complaints/{complaint_id}/feedback")
def submit_feedback(
    complaint_id: int,
    feedback_data: FeedbackCreate,
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

    if complaint.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only review your own complaints.",
        )

    if complaint.status != "Resolved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted after resolution.",
        )

    if complaint.feedback is not None or complaint.feedback_rating is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted.",
        )

    feedback_text = feedback_data.feedback.strip()

    if not feedback_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback cannot be empty.",
        )

    complaint.feedback = feedback_text
    complaint.feedback_rating = feedback_data.rating
    complaint.feedback_submitted_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(complaint)

        return {
            "message": "Feedback submitted successfully.",
            "ticket_id": complaint.ticket_id,
            "feedback": complaint.feedback,
            "rating": complaint.feedback_rating,
        }

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit feedback.",
        )


# --------------------------------------------------
# ADMIN: VIEW ALL STUDENT FEEDBACK
# --------------------------------------------------

@app.get(
    "/api/admin/feedback",
    response_model=list[FeedbackResponse],
)
def get_all_feedback(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    complaints = (
        db.query(Complaint)
        .filter(
            Complaint.feedback.isnot(None),
            Complaint.feedback_rating.isnot(None),
            Complaint.feedback_submitted_at.isnot(None),
        )
        .order_by(Complaint.feedback_submitted_at.desc())
        .all()
    )

    return [
        {
            "complaint_id": complaint.id,
            "ticket_id": complaint.ticket_id,
            "title": complaint.title,
            "feedback": complaint.feedback,
            "rating": complaint.feedback_rating,
            "feedback_submitted_at": complaint.feedback_submitted_at,
            "student_name": (
                complaint.owner.name
                if complaint.owner else "Unknown"
            ),
        }
        for complaint in complaints
    ]


# --------------------------------------------------
# ADMIN: FEEDBACK ANALYTICS
# --------------------------------------------------

@app.get(
    "/api/admin/feedback/analytics",
    response_model=FeedbackAnalytics,
)
def get_feedback_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    total_feedback, average_rating = (
        db.query(
            func.count(Complaint.id),
            func.avg(Complaint.feedback_rating),
        )
        .filter(Complaint.feedback_rating.isnot(None))
        .first()
    )

    rating_rows = (
        db.query(
            Complaint.feedback_rating,
            func.count(Complaint.id),
        )
        .filter(Complaint.feedback_rating.isnot(None))
        .group_by(Complaint.feedback_rating)
        .all()
    )

    distribution = {
        rating: 0 for rating in range(1, 6)
    }

    for rating, count in rating_rows:
        distribution[rating] = count

    return {
        "total_feedback": total_feedback or 0,
        "average_rating": round(float(average_rating or 0), 2),
        "rating_distribution": distribution,
    }
