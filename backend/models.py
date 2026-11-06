
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


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

    # Student feedback after complaint resolution
    feedback = Column(Text, nullable=True)

    # Path or URL of the uploaded complaint image
    image_url = Column(String(500), nullable=True)

    # Complaint owner
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
