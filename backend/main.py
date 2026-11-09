
from dotenv import load_dotenv

load_dotenv()

import os
import uuid
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from threading import Lock

import jwt
import cloudinary
import cloudinary.uploader

from pwdlib import PasswordHash
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Complaint, User, StatusHistory, AuditLog
from schemas import (
    ComplaintCreate,
    ComplaintResponse,
    ComplaintStatusUpdate,
    StatusHistoryResponse,
    UserRegister,
    UserLogin,
    UserResponse,
    AdminUserResponse,
    UserRoleUpdate,
    TokenResponse,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackAnalytics,
    AuditLogResponse,
)


# --------------------------------------------------
# STRUCTURED LOGGING
# --------------------------------------------------

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        optional_fields = [
            "event",
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "user_id",
            "complaint_id",
            "old_status",
            "new_status",
            "rating",
            "action",
            "target_user_id",
            "old_role",
            "new_role",
        ]

        for field in optional_fields:
            value = getattr(record, field, None)
            if value is not None:
                log_entry[field] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(log_entry)


logger = logging.getLogger("smartcampus")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
logger.propagate = False

if not logger.handlers:
    log_handler = logging.StreamHandler()
    log_handler.setFormatter(JSONFormatter())
    logger.addHandler(log_handler)


# --------------------------------------------------
# SECURITY CONFIGURATION
# --------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing. Check backend/.env.")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_MINUTES = 60

password_hash = PasswordHash.recommended()

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description=(
        "Enter the access token returned by POST /api/auth/login. "
        "Enter the token only, without adding the Bearer prefix."
    ),
)

Base.metadata.create_all(bind=engine)


# --------------------------------------------------
# CLOUDINARY CONFIGURATION
# --------------------------------------------------

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

CLOUDINARY_ENABLED = all([
    CLOUDINARY_CLOUD_NAME,
    CLOUDINARY_API_KEY,
    CLOUDINARY_API_SECRET,
])

if CLOUDINARY_ENABLED:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )

    logger.info(
        "Cloudinary image storage configured",
        extra={"event": "cloudinary_configured"},
    )
else:
    logger.warning(
        "Cloudinary credentials are not configured. "
        "Using local image storage.",
        extra={"event": "local_image_storage_enabled"},
    )


# --------------------------------------------------
# API DOCUMENTATION CONFIGURATION
# --------------------------------------------------

API_TAGS = [
    {
        "name": "General",
        "description": "API availability and health-check endpoints.",
    },
    {
        "name": "Authentication",
        "description": "Registration, login, JWT authentication, and profiles.",
    },
    {
        "name": "Complaints",
        "description": "Create, search, filter, paginate, and view complaints.",
    },
    {
        "name": "Complaint Management",
        "description": "Administrator operations for complaint status.",
    },
    {
        "name": "Status History",
        "description": "Chronological history of complaint status changes.",
    },
    {
        "name": "Image Uploads",
        "description": "Upload supporting JPG, PNG, or WEBP images.",
    },
    {
        "name": "Student Feedback",
        "description": "Submit feedback and ratings after resolution.",
    },
    {
        "name": "Admin Feedback",
        "description": "Administrator access to student feedback.",
    },
    {
        "name": "Admin Analytics",
        "description": "Administrator feedback analytics.",
    },
    {
        "name": "Admin Audit Logs",
        "description": "Administrator-only records of system actions.",
    },
    {
        "name": "Admin User Management",
        "description": "Administrator-only user listing and role management.",
    },
]

app = FastAPI(
    title="SmartCampus Complaint Management System",
    summary="Campus complaint and grievance management API",
    description="""
# SmartCampus API

SmartCampus allows students to report campus issues and administrators
to manage and resolve complaints.

## Main capabilities

- Student registration and JWT authentication
- Complaint creation and tracking
- Automatic department assignment
- Complaint search, filtering, and pagination
- Supporting image uploads
- Administrator complaint status management
- Complaint status history
- Student feedback and ratings
- Administrator feedback analytics
- Administrative audit logs
- Role-based user management
- Request tracking and rate limiting

## Authentication

1. Register using `POST /api/auth/register`.
2. Log in using `POST /api/auth/login`.
3. Copy the `access_token` from the response.
4. Select Authorize and enter the token.
5. Use the protected endpoints.

## User roles

**Student**
- Create complaints.
- View their own complaints.
- Upload images to their own complaints.
- View their complaint history.
- Submit feedback after resolution.

**Administrator**
- View all complaints.
- Update complaint statuses.
- View complaint history.
- Access student feedback.
- View analytics.
- View administrative audit logs.
- List users and manage user roles.

## Complaint categories

| Category | Assigned department |
|---|---|
| Infrastructure | Maintenance Department |
| Wi-Fi | IT Department |
| Cleanliness | Housekeeping Department |
| Transport | Transport Department |

## Complaint statuses

- Submitted
- In Progress
- Resolved
- Rejected
""",
    version="4.5.0",
    openapi_tags=API_TAGS,
    contact={"name": "SmartCampus API Support"},
)


# --------------------------------------------------
# FILE STORAGE
# --------------------------------------------------

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_IMAGE_SIZE = 5 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads",
)


# --------------------------------------------------
# RATE LIMITING
# --------------------------------------------------

RATE_LIMITS = {
    "register": (3, 60 * 60),
    "login": (5, 60),
    "create_complaint": (10, 60),
    "upload_image": (5, 60),
    "submit_feedback": (3, 60 * 60),
}

rate_limit_buckets = {}
rate_limit_lock = Lock()


def get_rate_limit_group(method: str, path: str):
    if method != "POST":
        return None

    if path == "/api/auth/register":
        return "register"

    if path == "/api/auth/login":
        return "login"

    if path == "/api/complaints":
        return "create_complaint"

    parts = path.strip("/").split("/")

    if (
        len(parts) == 4
        and parts[0] == "api"
        and parts[1] == "complaints"
        and parts[2].isdigit()
        and parts[3] == "image"
    ):
        return "upload_image"

    if (
        len(parts) == 4
        and parts[0] == "api"
        and parts[1] == "complaints"
        and parts[2].isdigit()
        and parts[3] == "feedback"
    ):
        return "submit_feedback"

    return None


def check_rate_limit(group: str, client_ip: str):
    limit, window = RATE_LIMITS[group]
    now = time.monotonic()
    key = (group, client_ip)

    with rate_limit_lock:
        window_start, request_count = rate_limit_buckets.get(
            key, (now, 0)
        )

        if now - window_start >= window:
            window_start = now
            request_count = 0

        if request_count >= limit:
            retry_after = max(
                1,
                int(window - (now - window_start)) + 1,
            )
            return False, retry_after

        rate_limit_buckets[key] = (
            window_start,
            request_count + 1,
        )

    return True, 0


# --------------------------------------------------
# REQUEST LOGGING AND RATE LIMITING MIDDLEWARE
# --------------------------------------------------

@app.middleware("http")
async def request_logging_and_rate_limit_middleware(
    request: Request,
    call_next,
):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    method = request.method
    path = request.url.path

    request.state.request_id = request_id

    group = get_rate_limit_group(method, path)

    if group is not None:
        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        allowed, retry_after = check_rate_limit(
            group,
            client_ip,
        )

        if not allowed:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )

            logger.warning(
                "Request rejected by rate limiter",
                extra={
                    "event": "rate_limit_exceeded",
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": 429,
                    "duration_ms": duration_ms,
                },
            )

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-Request-ID": request_id,
                },
            )

    try:
        response = await call_next(request)

        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        log_data = {
            "event": "http_request",
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }

        if response.status_code >= 500:
            logger.error(
                "Request completed with server error",
                extra=log_data,
            )
        elif response.status_code >= 400:
            logger.warning(
                "Request completed with client error",
                extra=log_data,
            )
        else:
            logger.info(
                "Request completed successfully",
                extra=log_data,
            )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception:
        duration_ms = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )

        logger.exception(
            "Unhandled exception while processing request",
            extra={
                "event": "unhandled_request_exception",
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
        )
        raise


# --------------------------------------------------
# CORS CONFIGURATION
# --------------------------------------------------

FRONTEND_URL = os.getenv(
    "FRONTEND_URL", ""
).strip().rstrip("/")

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://127.0.0.1:5175",
]

if FRONTEND_URL and FRONTEND_URL not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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

ALLOWED_ROLES = {"student", "admin"}


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
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired login token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        payload = jwt.decode(
            credentials.credentials,
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

@app.get("/", tags=["General"], summary="API welcome message")
def home():
    return {
        "message": "Welcome to SmartCampus Complaint Management API"
    }


@app.get("/api/health", tags=["General"], summary="Check API health")
def health_check():
    return {"status": "healthy"}


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
    summary="Register a student account",
    description="Creates a new student account. New registrations receive the student role.",
    responses={
        409: {"description": "An account with this email already exists."},
        429: {"description": "Registration rate limit exceeded."},
    },
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

        logger.info(
            "Student account registered",
            extra={
                "event": "user_registered",
                "user_id": user.id,
            },
        )
        return user

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    except Exception:
        db.rollback()
        logger.exception(
            "Account registration failed",
            extra={"event": "registration_failed"},
        )
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
    tags=["Authentication"],
    summary="Log in and receive an access token",
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
        logger.warning(
            "Authentication attempt failed",
            extra={"event": "login_failed"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        "User authenticated successfully",
        extra={
            "event": "login_success",
            "user_id": user.id,
        },
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
    tags=["Authentication"],
    summary="Get the current user's profile",
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
    tags=["Complaints"],
    summary="Create a campus complaint",
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

        db.add(
            StatusHistory(
                complaint_id=complaint.id,
                old_status=None,
                new_status="Submitted",
                changed_by_user_id=current_user.id,
            )
        )

        db.commit()
        db.refresh(complaint)

        logger.info(
            "Complaint created",
            extra={
                "event": "complaint_created",
                "user_id": current_user.id,
                "complaint_id": complaint.id,
            },
        )
        return complaint

    except Exception:
        db.rollback()
        logger.exception(
            "Complaint creation failed",
            extra={
                "event": "complaint_creation_failed",
                "user_id": current_user.id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create complaint.",
        )


# --------------------------------------------------
# LIST, SEARCH, FILTER, AND PAGINATE COMPLAINTS
# --------------------------------------------------

@app.get(
    "/api/complaints",
    response_model=list[ComplaintResponse],
    tags=["Complaints"],
    summary="List and search complaints",
)
def list_complaints(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search by ticket ID, title, or description.",
        examples=["broken fan"],
    ),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by complaint status.",
    ),
    category: str | None = Query(
        default=None,
        max_length=50,
        description="Filter by complaint category.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)

    if current_user.role != "admin":
        query = query.filter(
            Complaint.user_id == current_user.id
        )

    if search:
        search_value = (
            search.strip()
            .replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        search_term = f"%{search_value}%"
        query = query.filter(
            (Complaint.ticket_id.ilike(search_term, escape="\\"))
            | (Complaint.title.ilike(search_term, escape="\\"))
            | (Complaint.description.ilike(search_term, escape="\\"))
        )

    if status_filter:
        if status_filter not in ALLOWED_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter.",
            )
        query = query.filter(Complaint.status == status_filter)

    if category:
        if category not in DEPARTMENTS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid category filter.",
            )
        query = query.filter(Complaint.category == category)

    return (
        query.order_by(Complaint.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


# --------------------------------------------------
# VIEW A SINGLE COMPLAINT
# --------------------------------------------------

@app.get(
    "/api/complaints/{complaint_id}",
    response_model=ComplaintResponse,
    tags=["Complaints"],
    summary="Get a complaint by ID",
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
# UPDATE COMPLAINT STATUS + CREATE AUDIT LOG
# --------------------------------------------------

@app.patch(
    "/api/complaints/{complaint_id}/status",
    tags=["Complaint Management"],
    summary="Update complaint status",
    description=(
        "Administrator-only endpoint. Updates complaint status, "
        "records status history, and creates an audit log in the "
        "same database transaction."
    ),
    responses={
        403: {"description": "Administrator access required."},
        404: {"description": "Complaint not found."},
    },
)
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

    old_status = complaint.status

    if old_status == update_data.status:
        return {
            "message": "Complaint already has this status.",
            "ticket_id": complaint.ticket_id,
            "status": complaint.status,
        }

    try:
        complaint.status = update_data.status

        db.add(
            StatusHistory(
                complaint_id=complaint.id,
                old_status=old_status,
                new_status=update_data.status,
                changed_by_user_id=current_user.id,
            )
        )

        db.add(
            AuditLog(
                actor_user_id=current_user.id,
                actor_name=current_user.name,
                complaint_id=complaint.id,
                action="complaint_status_updated",
                old_value=old_status,
                new_value=update_data.status,
            )
        )

        db.commit()
        db.refresh(complaint)

        logger.info(
            "Complaint status changed and audit log created",
            extra={
                "event": "complaint_status_changed",
                "user_id": current_user.id,
                "complaint_id": complaint.id,
                "old_status": old_status,
                "new_status": complaint.status,
                "action": "complaint_status_updated",
            },
        )

    except Exception:
        db.rollback()
        logger.exception(
            "Complaint status update failed",
            extra={
                "event": "complaint_status_update_failed",
                "complaint_id": complaint_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update complaint status.",
        )

    return {
        "message": "Complaint status updated successfully.",
        "ticket_id": complaint.ticket_id,
        "old_status": old_status,
        "status": complaint.status,
    }


# --------------------------------------------------
# VIEW COMPLAINT STATUS HISTORY
# --------------------------------------------------

@app.get(
    "/api/complaints/{complaint_id}/history",
    response_model=list[StatusHistoryResponse],
    tags=["Status History"],
    summary="Get complaint status history",
)
def get_complaint_history(
    complaint_id: int,
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

    if (
        current_user.role != "admin"
        and complaint.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view the history of your own complaints.",
        )

    entries = (
        db.query(StatusHistory)
        .filter(StatusHistory.complaint_id == complaint_id)
        .order_by(
            StatusHistory.changed_at.asc(),
            StatusHistory.id.asc(),
        )
        .all()
    )

    return [
        {
            "id": entry.id,
            "complaint_id": entry.complaint_id,
            "old_status": entry.old_status,
            "new_status": entry.new_status,
            "changed_by_user_id": entry.changed_by_user_id,
            "changed_by_name": (
                entry.changed_by.name
                if entry.changed_by
                else "System"
            ),
            "changed_at": entry.changed_at,
        }
        for entry in entries
    ]


# --------------------------------------------------
# ADMIN: VIEW AUDIT LOGS
# --------------------------------------------------

@app.get(
    "/api/admin/audit-logs",
    response_model=list[AuditLogResponse],
    tags=["Admin Audit Logs"],
    summary="View administrative audit logs",
    description=(
        "Administrator-only endpoint. Returns recorded administrative "
        "actions, newest first. Supports complaint and action filters "
        "and pagination."
    ),
    responses={
        200: {"description": "Audit logs returned successfully."},
        401: {"description": "Authentication required."},
        403: {"description": "Administrator access required."},
    },
)
def get_audit_logs(
    complaint_id: int | None = Query(
        default=None,
        ge=1,
        description="Optionally filter logs by complaint ID.",
    ),
    action: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Optionally filter by action name.",
        examples=["complaint_status_updated"],
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(AuditLog)

    if complaint_id is not None:
        query = query.filter(
            AuditLog.complaint_id == complaint_id
        )

    if action:
        query = query.filter(
            AuditLog.action == action.strip()
        )

    return (
        query.order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


# --------------------------------------------------
# ADMIN: LIST, SEARCH, AND FILTER USERS
# --------------------------------------------------

@app.get(
    "/api/admin/users",
    response_model=list[AdminUserResponse],
    tags=["Admin User Management"],
    summary="List and search users",
    description=(
        "Administrator-only endpoint. Supports searching by name or "
        "email, filtering by role, and pagination. Password hashes "
        "are never returned."
    ),
)
def get_admin_users(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search users by name or email.",
    ),
    role: str | None = Query(
        default=None,
        description="Filter users by student or admin role.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if role:
        role = role.strip().lower()

        if role not in ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role filter must be student or admin.",
            )

        query = query.filter(User.role == role)

    if search:
        search_term = f"%{search.strip()}%"

        query = query.filter(
            (User.name.ilike(search_term))
            | (User.email.ilike(search_term))
        )

    return (
        query.order_by(
            User.created_at.desc(),
            User.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


# --------------------------------------------------
# ADMIN: UPDATE USER ROLE
# --------------------------------------------------

@app.patch(
    "/api/admin/users/{user_id}/role",
    tags=["Admin User Management"],
    summary="Promote or demote a user",
    description=(
        "Administrator-only endpoint. Changes a user's role to "
        "student or admin and records the change in the audit log."
    ),
    responses={
        200: {"description": "User role updated successfully."},
        403: {"description": "Administrator access required."},
        404: {"description": "User not found."},
        409: {"description": "Role change is not permitted."},
        422: {"description": "Invalid role."},
    },
)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    new_role = role_data.role.strip().lower()

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Role must be either student or admin.",
        )

    target_user = db.query(User).filter(
        User.id == user_id
    ).first()

    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    old_role = target_user.role

    if old_role == new_role:
        return {
            "message": "User already has this role.",
            "user": {
                "id": target_user.id,
                "name": target_user.name,
                "email": target_user.email,
                "role": target_user.role,
                "created_at": target_user.created_at,
            },
        }

    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You cannot change your own administrator role.",
        )

    if old_role == "admin" and new_role == "student":
        admin_count = (
            db.query(func.count(User.id))
            .filter(User.role == "admin")
            .scalar()
        )

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The last administrator cannot be demoted.",
            )

    try:
        target_user.role = new_role

        db.add(
            AuditLog(
                actor_user_id=current_user.id,
                actor_name=current_user.name,
                complaint_id=None,
                action="user_role_updated",
                old_value=old_role,
                new_value=new_role,
            )
        )

        db.commit()
        db.refresh(target_user)

        logger.info(
            "User role updated",
            extra={
                "event": "user_role_updated",
                "user_id": current_user.id,
                "target_user_id": target_user.id,
                "old_role": old_role,
                "new_role": new_role,
                "action": "user_role_updated",
            },
        )

        return {
            "message": "User role updated successfully.",
            "user": {
                "id": target_user.id,
                "name": target_user.name,
                "email": target_user.email,
                "role": target_user.role,
                "created_at": target_user.created_at,
            },
        }

    except Exception:
        db.rollback()

        logger.exception(
            "User role update failed",
            extra={
                "event": "user_role_update_failed",
                "target_user_id": user_id,
                "user_id": current_user.id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update user role.",
        )


# --------------------------------------------------
# UPLOAD COMPLAINT IMAGE
# --------------------------------------------------

@app.post(
    "/api/complaints/{complaint_id}/image",
    tags=["Image Uploads"],
    summary="Upload a complaint image",
)
async def upload_complaint_image(
    complaint_id: int,
    file: UploadFile = File(
        ...,
        description="JPG, PNG, or WEBP image. Maximum size: 5 MB.",
    ),
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

    if (
        current_user.role != "admin"
        and complaint.user_id != current_user.id
    ):
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
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image must be 5 MB or smaller.",
        )

    valid_signature = (
        (
            extension == ".jpg"
            and contents.startswith(bytes.fromhex("FFD8FF"))
        )
        or (
            extension == ".png"
            and contents.startswith(
                bytes.fromhex("89504E470D0A1A0A")
            )
        )
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
        if CLOUDINARY_ENABLED:
            upload_result = cloudinary.uploader.upload(
                contents,
                resource_type="image",
                folder="smartcampus/complaints",
                public_id=uuid.uuid4().hex,
                overwrite=False,
                allowed_formats=["jpg", "jpeg", "png", "webp"],
            )

            image_url = upload_result.get("secure_url")

            if not image_url:
                raise RuntimeError(
                    "Cloudinary did not return a secure image URL."
                )

        else:
            destination.write_bytes(contents)
            image_url = f"/uploads/{filename}"

        complaint.image_url = image_url

        db.commit()
        db.refresh(complaint)

        logger.info(
            "Complaint image uploaded",
            extra={
                "event": "complaint_image_uploaded",
                "user_id": current_user.id,
                "complaint_id": complaint.id,
            },
        )

        return {
            "message": "Image uploaded successfully.",
            "ticket_id": complaint.ticket_id,
            "image_url": complaint.image_url,
        }

    except Exception:
        db.rollback()

        if destination.exists():
            destination.unlink(missing_ok=True)

        logger.exception(
            "Complaint image upload failed",
            extra={
                "event": "complaint_image_upload_failed",
                "complaint_id": complaint_id,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the complaint image.",
        )

    finally:
        await file.close()


# --------------------------------------------------
# STUDENT FEEDBACK
# --------------------------------------------------

@app.post(
    "/api/complaints/{complaint_id}/feedback",
    tags=["Student Feedback"],
    summary="Submit complaint feedback",
)
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

    if (
        complaint.feedback is not None
        or complaint.feedback_rating is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback has already been submitted.",
        )

    complaint.feedback = feedback_data.feedback
    complaint.feedback_rating = feedback_data.rating
    complaint.feedback_submitted_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(complaint)

        logger.info(
            "Student feedback submitted",
            extra={
                "event": "feedback_submitted",
                "user_id": current_user.id,
                "complaint_id": complaint.id,
                "rating": complaint.feedback_rating,
            },
        )

        return {
            "message": "Feedback submitted successfully.",
            "ticket_id": complaint.ticket_id,
            "feedback": complaint.feedback,
            "rating": complaint.feedback_rating,
        }

    except Exception:
        db.rollback()
        logger.exception(
            "Feedback submission failed",
            extra={
                "event": "feedback_submission_failed",
                "complaint_id": complaint_id,
            },
        )
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
    tags=["Admin Feedback"],
    summary="View all submitted student feedback",
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
    tags=["Admin Analytics"],
    summary="Get student feedback analytics",
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
