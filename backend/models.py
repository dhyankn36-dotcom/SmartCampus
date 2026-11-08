
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


# --------------------------------------------------
# COMPLAINT MODEL
# --------------------------------------------------

class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)

    ticket_id = Column(
        String(30),
        unique=True,
        index=True,
        nullable=False
    )

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    department = Column(String(100), nullable=False)

    status = Column(
        String(30),
        nullable=False,
        default="Submitted",
        server_default="Submitted"
    )

    submitted_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    feedback = Column(Text, nullable=True)
    feedback_rating = Column(Integer, nullable=True)
    feedback_submitted_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    image_url = Column(String(500), nullable=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", name="fk_complaints_user"),
        nullable=True,
        index=True
    )

    owner = relationship(
        "User",
        back_populates="complaints"
    )

    status_history = relationship(
        "StatusHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="StatusHistory.changed_at"
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="complaint"
    )


# --------------------------------------------------
# USER MODEL
# --------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password = Column(String(255), nullable=False)

    role = Column(
        String(20),
        nullable=False,
        default="student",
        server_default="student"
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    complaints = relationship(
        "Complaint",
        back_populates="owner"
    )

    status_changes = relationship(
        "StatusHistory",
        back_populates="changed_by",
        foreign_keys="StatusHistory.changed_by_user_id"
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_user_id"
    )


# --------------------------------------------------
# COMPLAINT STATUS HISTORY MODEL
# --------------------------------------------------

class StatusHistory(Base):
    __tablename__ = "status_history"

    id = Column(Integer, primary_key=True, index=True)

    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    old_status = Column(
        String(30),
        nullable=True
    )

    new_status = Column(
        String(30),
        nullable=False
    )

    changed_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    changed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    complaint = relationship(
        "Complaint",
        back_populates="status_history"
    )

    changed_by = relationship(
        "User",
        back_populates="status_changes",
        foreign_keys=[changed_by_user_id]
    )


# --------------------------------------------------
# ADMIN AUDIT LOG MODEL
# --------------------------------------------------

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    actor_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Snapshot retained even if the admin account is deleted.
    actor_name = Column(
        String(100),
        nullable=False
    )

    complaint_id = Column(
        Integer,
        ForeignKey("complaints.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    action = Column(
        String(100),
        nullable=False,
        index=True
    )

    old_value = Column(
        Text,
        nullable=True
    )

    new_value = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True
    )

    actor = relationship(
        "User",
        back_populates="audit_logs",
        foreign_keys=[actor_user_id]
    )

    complaint = relationship(
        "Complaint",
        back_populates="audit_logs"
    )

    __table_args__ = (
        Index(
            "ix_audit_logs_complaint_action",
            "complaint_id",
            "action"
        ),
    )
