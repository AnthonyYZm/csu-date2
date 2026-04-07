"""ORM 模型。建表在应用启动时由 main 中 Base.metadata.create_all(bind=engine) 执行。"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_verified = Column(Boolean, default=False)

    name = Column(String, default="")
    campus = Column(String, default="")
    grade = Column(String, default="")
    major = Column(String, default="")
    quiz_completed = Column(Boolean, default=False)
    paused = Column(Boolean, default=False)
    wechat = Column(String, default="")
    created_at = Column(DateTime, nullable=True)

    bio = Column(String, default="")
    values_json = Column(JSON, nullable=True)

    # 教育邮箱验证（非edu邮箱注册用户需在3天内绑定）
    edu_email = Column(String, nullable=True)
    edu_email_verified_at = Column(DateTime, nullable=True)

    profile = relationship("Profile", back_populates="user", uselist=False)
    sent_crushes = relationship("Crush", back_populates="sender")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    gender = Column(String, nullable=True)
    sexuality = Column(String, nullable=True)
    campus = Column(String, nullable=True)
    cross_campus_ok = Column(Boolean, nullable=True)
    raw_quiz_data = Column(JSON, nullable=True)
    vectorized_data = Column(JSON, nullable=True)

    user = relationship("User", back_populates="profile")


class Crush(Base):
    __tablename__ = "crushes"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    target_email = Column(String, index=True, nullable=False)
    message = Column(String, default="")
    is_mutual = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", back_populates="sent_crushes")


class PageView(Base):
    __tablename__ = "page_views"

    id = Column(Integer, primary_key=True, index=True)
    path = Column(String, nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    user2_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_number = Column(Integer, nullable=False, index=True)
    score = Column(Float, nullable=True)
    report_data = Column(JSON, nullable=True)

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", "week_number", name="uq_match_pair_week"),
    )
